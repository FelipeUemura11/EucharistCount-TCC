"""
Varredura de configuracoes contra uma contagem manual de referencia.

POR QUE NAO BASTA O calibrar.py

O `calibrar.py` responde "que configuracao detecta mais caixas e roda
rapido". Nao e essa a pergunta do TCC. A pergunta e "que configuracao
acerta quantas pessoas entraram e sairam". Detectar mais caixas costuma
significar mais falsos positivos — ou seja, contagem pior. Alem disso o
`calibrar.py` nao exercita rastreio nem contagem, que sao justamente as
etapas onde o erro de contagem nasce.

Este script mede o que importa: o erro contra a contagem manual.

COMO E RAPIDO

A inferencia ja foi feita uma vez por modelo e esta em cache
(`scripts/extrair_deteccoes.py`). Aqui so se reexecuta o que e barato:
ByteTrack sobre as caixas e a contagem por linha. A parte cara do
pipeline nao e repetida.

O caminho reproduz fielmente o de producao:

    conf -> max_det -> ByteTrack -> filtro geometrico -> ContadorLinha

na mesma ordem de `detector.py` e `monitor.py`, inclusive usando o tempo
do VIDEO (indice / fps de origem), como faz `camera.tempo_atual`.

DUAS ETAPAS

1. `deteccao` — varre modelo, confianca, fps e parametros do ByteTrack,
   avaliando cada um com uma triagem curta de geometrias de linha.
2. `contagem` — pega as melhores da etapa 1 e varre a fundo a geometria
   da linha, o cooldown e a janela.

Separar as duas evita o produto cartesiano completo, que levaria horas.

PRIVACIDADE (LGPD)

Opera exclusivamente sobre coordenadas numericas em cache. Nenhum quadro
de video e lido, exibido ou gravado.

Uso:
    python -m scripts.varrer --entradas 26 --saidas 3
    python -m scripts.varrer --entradas 26 --saidas 3 --etapa deteccao
    python -m scripts.varrer --entradas 26 --saidas 3 --topo 25
"""

import argparse
import itertools
import json
import sys
import time
from dataclasses import replace
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from eucharist.config import ConfigContagem, ConfigFiltro  # noqa: E402
from eucharist.contador import ContadorLinha  # noqa: E402
from eucharist.detector import Pessoa  # noqa: E402

PASTA_CACHE = RAIZ / "cache_deteccoes"
PASTA_RESULTADOS = RAIZ / "resultados_varredura"


# =============================================================== grades

# Confianca do detector (o mesmo `deteccao.confianca` do config.json).
GRADE_CONF = [0.15, 0.20, 0.25, 0.30, 0.35]

# Quadros por segundo analisados. O valor efetivo e sempre
# fps_origem / round(fps_origem / alvo) — ver camera._calcular_passo.
GRADE_FPS = [5.0, 7.5, 15.0]

# ByteTrack: quantos quadros um rastro sobrevive sem deteccao.
# Ate 90 quadros (3 s a 30 fps nominais) ajuda quando alguem some atras
# de uma coluna ou de outra pessoa.
GRADE_BUFFER = [30, 60, 90]

# Limiar da primeira associacao / criacao de rastro novo.
GRADE_ALTO = [0.25, 0.35]

# Linhas candidatas: x1,y1,x2,y2 em fracoes do quadro, do topo para a
# base. Todas ficam sobre o trecho final do caminho de acesso; variam o
# quanto se afastam da borda direita do quadro.
#
# Perto demais da borda, o rastro morre antes de cruzar (a pessoa sai do
# enquadramento). Longe demais, quem so passa em frente a igreja e
# contado como se tivesse entrado.
GRADE_LINHA = [
    (0.99, 0.20, 0.92, 0.99),   # a do config.json atual
    (0.98, 0.15, 0.90, 1.00),
    (0.96, 0.15, 0.88, 1.00),
    (0.94, 0.15, 0.86, 1.00),
    (0.97, 0.10, 0.93, 1.00),
    (0.95, 0.10, 0.90, 1.00),
    (0.93, 0.10, 0.88, 1.00),
    (0.99, 0.10, 0.99, 1.00),   # vertical pura, colada na borda
    (0.95, 0.10, 0.95, 1.00),   # vertical pura, mais interna
    (0.92, 0.10, 0.92, 1.00),
    (0.90, 0.10, 0.90, 1.00),
    (0.99, 0.25, 0.88, 1.00),   # mais inclinada
]

# Subconjunto usado na triagem da etapa 1 (barata).
GRADE_LINHA_TRIAGEM = [
    (0.99, 0.20, 0.92, 0.99),
    (0.96, 0.15, 0.88, 1.00),
    (0.95, 0.10, 0.95, 1.00),
]

# (numero_linhas, linhas_necessarias, espacamento)
GRADE_N_LINHAS = [
    (1, 1, 0.045),
    (2, 2, 0.045),
    (3, 2, 0.035),
    (3, 3, 0.030),
]
GRADE_N_LINHAS_TRIAGEM = [(1, 1, 0.045), (3, 2, 0.035)]

GRADE_COOLDOWN = [2.0, 3.0, 5.0]
GRADE_JANELA = [4.0, 6.0, 10.0]

# O sentido e determinado pela geometria (ver contador._lado_da_linha):
# com a linha escrita do topo para a base na borda direita, quem anda
# para a direita cai no lado -1. Varre-se assim mesmo, para confirmar.
GRADE_LADO = [-1, 1]


# ================================================================ cache


class Cache:
    """Deteccoes de um video, indexadas por quadro."""

    def __init__(self, caminho: Path):
        d = np.load(caminho, allow_pickle=False)
        self.arr = d["deteccoes"]
        self.largura = int(d["largura"])
        self.altura = int(d["altura"])
        self.fps = float(d["fps"])
        self.total = int(d["total_quadros"])
        self.roi_px = tuple(int(v) for v in d["roi_px"])
        self.modelo = str(d["modelo"])
        self.imgsz = int(d["imgsz"])
        self.nome = caminho.stem
        self.ms_por_quadro = float(d["ms_por_quadro"])

        # Agrupa por quadro uma unica vez: a varredura consulta isso
        # dezenas de milhares de vezes.
        self.por_quadro: dict[int, np.ndarray] = {}
        if len(self.arr):
            ordem = np.argsort(self.arr[:, 0], kind="stable")
            a = self.arr[ordem]
            cortes = np.searchsorted(a[:, 0], np.arange(1, self.total + 2))
            for i in range(self.total):
                ini, fim = cortes[i], cortes[i + 1]
                if fim > ini:
                    self.por_quadro[i + 1] = a[ini:fim, 1:]

    @property
    def area_recorte(self) -> float:
        x1, y1, x2, y2 = self.roi_px
        return float((x2 - x1) * (y2 - y1))

    @property
    def usa_roi(self) -> bool:
        x1, y1, x2, y2 = self.roi_px
        return (x2 - x1) < self.largura or (y2 - y1) < self.altura


# ===================================================== rastreio offline


class _Deteccoes:
    """Formato minimo esperado por BYTETracker.update()."""

    def __init__(self, xyxy: np.ndarray, conf: np.ndarray):
        self.conf = conf
        self.cls = np.zeros(len(conf), dtype=np.float32)
        if len(xyxy):
            cx = (xyxy[:, 0] + xyxy[:, 2]) / 2
            cy = (xyxy[:, 1] + xyxy[:, 3]) / 2
            self.xywh = np.stack(
                [cx, cy, xyxy[:, 2] - xyxy[:, 0], xyxy[:, 3] - xyxy[:, 1]],
                axis=1,
            )
        else:
            self.xywh = np.zeros((0, 4), np.float32)


def _args_tracker(alto: float, baixo: float, novo: float,
                  buffer: int, match: float, fuse: bool):
    from types import SimpleNamespace

    return SimpleNamespace(
        tracker_type="bytetrack",
        track_high_thresh=alto,
        track_low_thresh=baixo,
        new_track_thresh=novo,
        track_buffer=buffer,
        match_thresh=match,
        fuse_score=fuse,
    )


def rastrear(cache: Cache, conf: float, passo: int, max_det: int,
             tracker_args) -> list[tuple[int, np.ndarray]]:
    """
    Reexecuta o ByteTrack sobre as caixas em cache.

    Devolve [(indice_do_quadro, array Nx6 [x1,y1,x2,y2,id,conf])].

    `passo` reproduz o descarte de quadros de `camera.py`: para arquivo,
    so os indices multiplos do passo chegam ao detector.
    """
    from ultralytics.trackers.byte_tracker import BYTETracker

    # frame_rate=30 e o que a Ultralytics usa internamente; manter aqui
    # garante que track_buffer signifique o mesmo em producao.
    tracker = BYTETracker(tracker_args, frame_rate=30)

    vazio = np.zeros((0, 6), np.float32)
    saida = []

    for indice in range(passo, cache.total + 1, passo):
        caixas = cache.por_quadro.get(indice)

        if caixas is None:
            xyxy = np.zeros((0, 4), np.float32)
            confs = np.zeros(0, np.float32)
        else:
            m = caixas[:, 4] >= conf
            xyxy = caixas[m, :4]
            confs = caixas[m, 4]
            if len(confs) > max_det:
                topo = np.argsort(-confs)[:max_det]
                xyxy, confs = xyxy[topo], confs[topo]

        res = tracker.update(_Deteccoes(xyxy, confs))
        # res: [x1,y1,x2,y2,id,score,cls,idx]
        saida.append(
            (indice, res[:, :6].astype(np.float32) if len(res) else vazio)
        )

    return saida


# ============================================================= contagem


def _plausivel(x1, y1, x2, y2, area_recorte: float, f: ConfigFiltro) -> bool:
    """Mesma regra de detector._plausivel, medida contra a area do recorte."""
    if not f.ativo:
        return True
    largura = x2 - x1
    altura = y2 - y1
    if largura <= 0 or altura <= 0:
        return False
    if not (f.area_min <= (largura * altura) / area_recorte <= f.area_max):
        return False
    aspecto = largura / altura
    return f.aspecto_min <= aspecto <= f.aspecto_max


def contar(trilhas, cache: Cache, filtro: ConfigFiltro,
           contagem: ConfigContagem) -> tuple[int, int]:
    """Reproduz o laco do Monitor sobre trilhas ja rastreadas."""
    contador = ContadorLinha(contagem, cache.largura, cache.altura)
    area = cache.area_recorte
    fps = max(cache.fps, 1e-6)

    for indice, linhas in trilhas:
        pessoas = [
            Pessoa(int(pid), int(x1), int(y1), int(x2), int(y2), float(cf))
            for x1, y1, x2, y2, pid, cf in linhas
            if _plausivel(x1, y1, x2, y2, area, filtro)
        ]
        # Tempo do video, igual a camera.tempo_atual para arquivo.
        contador.atualizar(pessoas, indice / fps)

    return contador.entradas, contador.saidas


# ============================================================ varredura


def _combinacoes_contagem(linhas, n_linhas, cooldowns, janelas, lados):
    return [
        (linha, lado, n, nec, esp, cd, jn)
        for linha in linhas
        for lado in lados
        for (n, nec, esp) in n_linhas
        for cd in cooldowns
        for jn in janelas
    ]


def _config_contagem(base, combo) -> ConfigContagem:
    linha, lado, n, nec, esp, cd, jn = combo
    return replace(
        base,
        linha_base=linha, lado_entrada=lado,
        numero_linhas=n, linhas_necessarias=nec, espacamento=esp,
        segundos_cooldown=cd, segundos_janela=jn,
    )


def avaliar(trilhas, cache, filtro, base, combos, ref_ent, ref_sai) -> list[dict]:
    """Aplica todas as geometrias de contagem sobre um mesmo rastreio."""
    fora = []
    for combo in combos:
        entradas, saidas = contar(
            trilhas, cache, filtro, _config_contagem(base, combo)
        )
        ee, es = abs(entradas - ref_ent), abs(saidas - ref_sai)
        linha, lado, n, nec, esp, cd, jn = combo
        fora.append({
            "entradas": entradas, "saidas": saidas,
            "dentro": entradas - saidas,
            "erro": ee + es, "erro_entradas": ee, "erro_saidas": es,
            "linha": list(linha), "lado_entrada": lado,
            "numero_linhas": n, "linhas_necessarias": nec,
            "espacamento": esp,
            "segundos_cooldown": cd, "segundos_janela": jn,
        })
    return fora


def etapa_deteccao(caches, filtro, base, ref_ent, ref_sai) -> list[dict]:
    """Varre modelo/confianca/fps/ByteTrack com triagem curta de linhas."""
    combos = _combinacoes_contagem(
        GRADE_LINHA_TRIAGEM, GRADE_N_LINHAS_TRIAGEM, [3.0], [6.0], [-1]
    )
    total = (len(caches) * len(GRADE_CONF) * len(GRADE_FPS)
             * len(GRADE_BUFFER) * len(GRADE_ALTO))

    print(f"ETAPA 1 — deteccao e rastreio: {total} rastreios "
          f"x {len(combos)} linhas de triagem")

    resultados, feito, inicio = [], 0, time.perf_counter()

    for cache in caches:
        for conf, fps, buffer, alto in itertools.product(
            GRADE_CONF, GRADE_FPS, GRADE_BUFFER, GRADE_ALTO
        ):
            passo = max(1, int(round(cache.fps / fps)))
            trilhas = rastrear(
                cache, conf, passo, 300,
                _args_tracker(alto, 0.1, alto, buffer, 0.8, True),
            )
            melhor = min(
                avaliar(trilhas, cache, filtro, base, combos, ref_ent, ref_sai),
                key=lambda r: (r["erro"], r["erro_entradas"]),
            )
            resultados.append({
                "cache": cache.nome, "modelo": cache.modelo,
                "imgsz": cache.imgsz, "roi": cache.usa_roi,
                "conf": conf, "fps": fps,
                "fps_efetivo": round(cache.fps / passo, 2),
                "buffer": buffer, "alto": alto,
                **melhor,
            })

            feito += 1
            if feito % 10 == 0 or feito == total:
                dec = time.perf_counter() - inicio
                print(f"  {feito}/{total}  ({dec / feito:.1f} s/rastreio, "
                      f"faltam ~{(total - feito) * dec / feito / 60:.1f} min)",
                      flush=True)

    return resultados


def etapa_contagem(caches, filtro, base, ref_ent, ref_sai,
                   candidatos: list[dict]) -> list[dict]:
    """Varre a fundo a geometria da linha sobre os melhores rastreios."""
    combos = _combinacoes_contagem(
        GRADE_LINHA, GRADE_N_LINHAS, GRADE_COOLDOWN, GRADE_JANELA, GRADE_LADO
    )
    por_nome = {c.nome: c for c in caches}

    print(f"\nETAPA 2 — contagem: {len(candidatos)} rastreios "
          f"x {len(combos)} geometrias")

    resultados = []
    for i, cand in enumerate(candidatos, 1):
        cache = por_nome[cand["cache"]]
        passo = max(1, int(round(cache.fps / cand["fps"])))
        trilhas = rastrear(
            cache, cand["conf"], passo, 300,
            _args_tracker(cand["alto"], 0.1, cand["alto"],
                          cand["buffer"], 0.8, True),
        )
        for r in avaliar(trilhas, cache, filtro, base, combos,
                         ref_ent, ref_sai):
            resultados.append({
                "cache": cache.nome, "modelo": cache.modelo,
                "imgsz": cache.imgsz, "roi": cache.usa_roi,
                "conf": cand["conf"], "fps": cand["fps"],
                "fps_efetivo": round(cache.fps / passo, 2),
                "buffer": cand["buffer"], "alto": cand["alto"],
                **r,
            })
        print(f"  {i}/{len(candidatos)}", flush=True)

    return resultados


# =============================================================== saida


CABECALHO = (f"{'MODELO':<10}{'CONF':>6}{'FPS':>6}{'BUF':>5}{'ALTO':>6}"
             f"{'LINHA':>27}{'NL':>6}{'CD':>5}{'JAN':>5}"
             f"{'ENT':>5}{'SAI':>5}{'DENTRO':>8}{'ERRO':>6}")


def formatar(r: dict) -> str:
    linha = ",".join(f"{v:.2f}" for v in r["linha"])
    modelo = r["modelo"].replace(".onnx", "")[:9]
    marca = "*" if not r["roi"] else " "
    n_linhas = f"{r['numero_linhas']}/{r['linhas_necessarias']}"
    return (f"{modelo:<9}{marca}{r['conf']:>6.2f}{r['fps']:>6.1f}"
            f"{r['buffer']:>5}{r['alto']:>6.2f}{linha:>27}{n_linhas:>6}"
            f"{r['segundos_cooldown']:>5.0f}{r['segundos_janela']:>5.0f}"
            f"{r['entradas']:>5}{r['saidas']:>5}{r['dentro']:>8}"
            f"{r['erro']:>6}")


def imprimir_tabela(resultados: list[dict], topo: int, titulo: str) -> None:
    print("\n" + "=" * len(CABECALHO))
    print(f"  {titulo}")
    print("=" * len(CABECALHO))
    print(CABECALHO)
    print("-" * len(CABECALHO))
    for r in resultados[:topo]:
        print(formatar(r))
    print("=" * len(CABECALHO))


def config_final(r: dict, cache: Cache) -> dict:
    """Monta o bloco pronto para colar no config.json."""
    return {
        "camera": {"fps_processamento": r["fps"]},
        "deteccao": {
            "modelo": f"modelos/{r['modelo']}",
            "imgsz": r["imgsz"],
            "confianca": r["conf"],
            "roi_ativo": bool(r["roi"]),
        },
        "contagem": {
            "linha_base": r["linha"],
            "numero_linhas": r["numero_linhas"],
            "linhas_necessarias": r["linhas_necessarias"],
            "espacamento": r["espacamento"],
            "lado_entrada": r["lado_entrada"],
            "segundos_cooldown": r["segundos_cooldown"],
            "segundos_janela": r["segundos_janela"],
        },
        "_bytetrack": {
            "track_high_thresh": r["alto"],
            "new_track_thresh": r["alto"],
            "track_buffer": r["buffer"],
        },
        "_custo": f"{cache.ms_por_quadro:.0f} ms/quadro nesta maquina",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--entradas", type=int, required=True,
                    help="contagem manual de referencia: quantos entraram")
    ap.add_argument("--saidas", type=int, required=True,
                    help="contagem manual de referencia: quantos sairam")
    ap.add_argument("--etapa", choices=["deteccao", "tudo"], default="tudo")
    ap.add_argument("--cache", nargs="*", default=None)
    ap.add_argument("--candidatos", type=int, default=8,
                    help="quantos rastreios seguem para a etapa 2")
    ap.add_argument("--topo", type=int, default=20)
    args = ap.parse_args()

    caminhos = ([Path(c) for c in args.cache] if args.cache
                else sorted(PASTA_CACHE.glob("*.npz")))
    if not caminhos:
        print("[ERRO] Nenhum cache. Rode antes:")
        print("  python -m scripts.extrair_deteccoes --modelo modelos/yolo11n.onnx")
        return 1

    caches = [Cache(p) for p in caminhos]

    print("=" * len(CABECALHO))
    print("  VARREDURA DE CONFIGURACOES")
    print("=" * len(CABECALHO))
    print(f"Referencia: {args.entradas} entradas, {args.saidas} saidas, "
          f"{args.entradas - args.saidas} dentro\n")
    for c in caches:
        print(f"  {c.nome:<22} {len(c.arr):>6} caixas  {c.total} quadros  "
              f"{'ROI' if c.usa_roi else 'quadro inteiro'}  "
              f"{c.ms_por_quadro:.0f} ms/quadro")
    print()

    # O filtro geometrico vem do config.json em uso; nao e varrido aqui
    # porque os limites ja sao permissivos de proposito.
    filtro = ConfigFiltro(True, 0.0001, 0.35, 0.10, 3.2)
    base = ConfigContagem()

    r1 = etapa_deteccao(caches, filtro, base, args.entradas, args.saidas)
    r1.sort(key=lambda r: (r["erro"], r["erro_entradas"], -r["fps"]))
    imprimir_tabela(r1, args.topo, "ETAPA 1 — melhores rastreios (triagem)")

    PASTA_RESULTADOS.mkdir(parents=True, exist_ok=True)
    (PASTA_RESULTADOS / "etapa1.json").write_text(
        json.dumps(r1, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    finais = r1
    if args.etapa == "tudo":
        # Diversifica: no maximo 3 candidatos por modelo, para a etapa 2
        # nao ficar presa a um unico detector.
        vistos: dict[str, int] = {}
        candidatos = []
        for r in r1:
            chave = r["cache"]
            if vistos.get(chave, 0) >= 3:
                continue
            vistos[chave] = vistos.get(chave, 0) + 1
            candidatos.append(r)
            if len(candidatos) >= args.candidatos:
                break

        r2 = etapa_contagem(caches, filtro, base, args.entradas, args.saidas,
                            candidatos)
        r2.sort(key=lambda r: (r["erro"], r["erro_entradas"], -r["fps"]))
        imprimir_tabela(r2, args.topo, "ETAPA 2 — melhores configuracoes")
        (PASTA_RESULTADOS / "etapa2.json").write_text(
            json.dumps(r2, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        finais = r2

    if finais:
        melhor = finais[0]
        cache = {c.nome: c for c in caches}[melhor["cache"]]
        print("\nMELHOR CONFIGURACAO (cole em config.json)")
        print(json.dumps(config_final(melhor, cache), indent=2,
                         ensure_ascii=False))
        print("\n* na coluna MODELO = cache sem ROI (quadro inteiro)")

    print(f"\nResultados completos em {PASTA_RESULTADOS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
