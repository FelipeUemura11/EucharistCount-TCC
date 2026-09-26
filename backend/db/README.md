# backend/db — camada de persistência

Esqueleto do banco (SQLite) do Eucharist Count. Nenhuma imagem/vídeo é
armazenado aqui — só números (contagens, horários, estimativas), conforme
exigido pela LGPD no TCC.

## Arquivos

| Arquivo | Para quê |
|---|---|
| `schema.sql` | Cria todas as tabelas, índices, trigger e a view. Fonte da verdade da estrutura. |
| `database.py` | `inicializar_banco()` roda o schema; `obter_conexao()` abre uma conexão (com FKs ligadas). |
| `crud.py` | **Use isto na API.** Uma função por operação (criar celebração, iniciar sessão, registrar instantâneo, etc.). Não escreva SQL novo nas rotas — se faltar uma operação, adicione a função aqui. |
| `import_csv.py` | Importa o `counting_people.csv` (contagem manual) para o schema normalizado. |
| `calcular_coeficiente_inicial.py` | Calcula a média `comungantes_reais / ocupacao_final` dos dados já importados e grava em `configuracao_estimativa` (modo `coeficiente_fixo`). Rodar de novo sempre que importar dado novo. |
| `preparar_dataset.py` | Monta o dataset de treino (ocupação, dia da semana, horário, tipo → comungantes reais) a partir do banco. Usado pelo script de treino, mas também roda sozinho pra inspecionar o dataset (`python3 preparar_dataset.py`). |
| `treinar_regressao.py` | Treina a regressão (modo `regressao`), valida com leave-one-out, salva o modelo em `modelos_estimativa/*.joblib` e registra a versão em `configuracao_estimativa`. **Só treina com 15+ celebrações no banco** — com menos que isso, ele avisa e não faz nada (ver seção "Estimativa de comunhão" abaixo). |
| `requirements.txt` | Dependências só deste módulo (`pandas`, `scikit-learn`, `joblib`) — não é o `requirements.txt` do motor de visão, são libs separadas. |

## Como a API usa este módulo

O `main.py` chama `inicializar_banco()` uma vez, na inicialização. As rotas
em `backend/api/rotas/` recebem uma conexão por requisição pela dependência
`obter_db` (`backend/api/dependencias.py`) e só chamam funções do `crud`:

```python
# backend/api/rotas/historico.py (resumido)
@router.get("/history", response_model=list[HistoryRecord])
def get_history(db: sqlite3.Connection = Depends(obter_db)):
    return [HistoryRecord(...) for r in crud.obter_historico(db)]
```

Para uma rota nova, siga o mesmo padrão: se faltar uma operação, crie a
função aqui no `crud.py`, e não SQL na rota. A organização completa da API
está em [`../DOCUMENTACAO_API.md`](../DOCUMENTACAO_API.md).

## Modelo de dados (visão geral)

```
horario_padrao (agenda semanal fixa)
      │ opcional
      ▼
celebracao (uma data concreta com missa)
      │ 1
      ▼ N
sessao_monitoramento (uma execução real da contagem)
      │ 1                              │ 1
      ▼ N                              ▼ 1
instantaneo_ocupacao            estimativa_comunhao
(série temporal p/ gráfico)     (comungantes/hóstias: real, calculado, ajustado)
```

- **`celebracao`** é o *planejado* (agenda). **`sessao_monitoramento`** é o
  *executado* (o que de fato rolou naquele dia) — são tabelas separadas
  porque uma celebração pode ter o monitoramento reiniciado (queda de
  energia, travamento), e porque hoje (modo manual) e amanhã (câmera)
  escrevem na mesma tabela sem precisar mudar nada.
- **`estimativa_comunhao`** guarda três fontes de valor lado a lado, de
  propósito:
  - `comungantes_reais` / `hostias_reais` — contagem manual real (o que
    está na planilha do colega, coluna `communed`). É o único valor que
    existe hoje.
  - `estimativa_calculada` / `hostias_calculadas` — o que o sistema
    prevê (coeficiente fixo hoje, regressão depois). `NULL` até esse
    módulo existir.
  - `estimativa_ajustada` / `hostias_ajustadas` — correção humana em
    cima do valor calculado (fluxo *human-in-the-loop* do TCC).
- **`vw_historico`** já entrega as colunas prontas para a tela Histórico
  do frontend (`data`, `celebracao`, `total_pessoas`, `estimativa_comunhao`,
  `hostias_sugeridas`, `entradas`, `saidas`) — não precisa fazer join nenhum
  na API, só `SELECT * FROM vw_historico` (via `crud.obter_historico`).

## Estimativa de comunhão: coeficiente fixo → regressão

O sistema opera em duas fases, sem precisar trocar de schema entre elas
(`configuracao_estimativa.metodo`):

1. **`coeficiente_fixo`** (fase atual) — `calcular_coeficiente_inicial.py`
   calcula a média real observada e grava. É esse valor que a API deve ler
   (`crud.obter_configuracao_estimativa_vigente`) pra sugerir comungantes/
   hóstias enquanto não há modelo.
2. **`regressao`** — assim que houver **15+ celebrações** com
   `comungantes_reais` preenchido no banco, `treinar_regressao.py` treina
   um modelo (ocupação + dia da semana + horário + tipo → comungantes) e
   grava o caminho do artefato em `configuracao_estimativa.modelo_path`.

Rotina recomendada: sempre que importar um lote novo de dados
(`import_csv.py`), rodar os dois scripts de novo, nessa ordem:

```bash
python3 calcular_coeficiente_inicial.py   # sempre atualiza o fallback
python3 treinar_regressao.py              # só re-treina se ja tiver dado suficiente
```

Hoje, a estimativa usada pelo sistema é calculada em
`backend/integracao/estimativa.py` (`calcular_estimativa`), sempre pelo
coeficiente: se `configuracao_estimativa` estiver vazia, usa o padrão 0.78
do próprio código. Para usar o modelo de regressão quando
`metodo = 'regressao'`, a função precisará aplicar este contrato:

```python
import joblib
config = crud.obter_configuracao_estimativa_vigente(conexao)

if config["metodo"] == "regressao" and config["modelo_path"]:
    modelo = joblib.load(RAIZ_DB / config["modelo_path"])
    entrada = pd.DataFrame([{
        "ocupacao_final": ocupacao_atual,
        "minutos_missa": minutos_desde_meia_noite,
        "dia_semana": dia_semana,
        "tipo": tipo_celebracao,
    }])
    estimativa = int(modelo.predict(entrada)[0])
else:
    estimativa = round(ocupacao_atual * config["coeficiente_comunhao"])

hostias = math.ceil(estimativa * (1 + config["margem_hostias"]))
```

Aqui fica documentado o contrato (o que ler de `configuracao_estimativa`
e como aplicar); a implementação vai em `calcular_estimativa`, para o
dashboard e o histórico continuarem usando uma única regra.

## Ligação com o motor de visão

O motor já grava no banco durante a missa. Todo o ciclo da sessão fica em
`backend/integracao/sessao.py`, e o `main.py` só o usa:

```python
fechar_sessoes_presas()        # no inicio: sessoes de execucoes anteriores -> 'interrompida'

with sessao_de_monitoramento(monitor, config) as gravador:
    metricas = monitor.executar(ao_atualizar=gravador)
# ao sair do "with": finalizar_sessao() com 'concluida' ou, se houve erro, 'interrompida'
```

O `GravadorSessao` grava os totais a cada passagem pela linha e um ponto do
gráfico a cada 5 segundos de vídeo.

O detalhamento (sequência completa, por que 5 segundos, o que vai em cada
coluna) está em [`../DOCUMENTACAO_BANCO.md`](../DOCUMENTACAO_BANCO.md),
seção 7, e o lado da API em [`../DOCUMENTACAO_API.md`](../DOCUMENTACAO_API.md).

## Convenções

- Datas/horas em texto ISO-8601 (`YYYY-MM-DD`, `HH:MM`, `YYYY-MM-DDTHH:MM:SS`).
- **Todo timestamp é UTC** — tanto os `DEFAULT` do `schema.sql`
  (`strftime('now')`) quanto os gerados em `crud.py` (`_agora()`). Se for
  gerar timestamp em outro lugar do backend, use
  `datetime.now(timezone.utc)`, nunca `datetime.now()` puro — já corrigimos
  um bug assim aqui (ver histórico do `crud.py`).
- `configuracao_estimativa` é *append-only* (histórico de coeficientes):
  para mudar o coeficiente, insira uma linha nova em vez de fazer UPDATE —
  assim dá pra saber qual coeficiente valia quando uma sessão antiga foi
  calculada.
- O arquivo `.db` gerado (`eucharist_count.db`) e a pasta `modelos_estimativa/`
  (artefatos `.joblib`) **não devem ir para o git** — são dados/artefatos
  gerados, regeneráveis a qualquer momento rodando os scripts. Só o código
  (`.py`, `.sql`, `.md`) é versionado. Confira se isso está no `.gitignore`
  da raiz do projeto:
  ```
  backend/db/*.db
  backend/db/modelos_estimativa/
  ```

## Testar

```bash
pip install -r requirements.txt               # pandas, scikit-learn, joblib

python3 database.py                           # cria o banco
python3 import_csv.py ../counting_people.csv  # importa dados reais existentes
python3 calcular_coeficiente_inicial.py       # calcula e grava o coeficiente
python3 treinar_regressao.py                  # tenta treinar (avisa se faltar dado)
```

Para inspecionar: `sqlite3 eucharist_count.db` (ou DB Browser for SQLite),
ou em Python:

```python
from database import obter_conexao
con = obter_conexao()
for row in con.execute("SELECT * FROM vw_historico"):
    print(dict(row))
```
