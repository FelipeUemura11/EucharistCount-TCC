# backend/db — camada de persistência

Banco (SQLite) do Eucharist Count. Nenhuma imagem/vídeo é
armazenado aqui — só números (contagens, horários, estimativas), conforme
exigido pela LGPD no TCC.

## Arquivos

| Arquivo | Para quê |
|---|---|
| `schema.sql` | Cria todas as tabelas, índices, trigger e a view. Fonte da verdade da estrutura. |
| `database.py` | `inicializar_banco()` roda o schema; `obter_conexao()` abre uma conexão (com FKs ligadas). |
| `crud.py` | **Use isto na API.** Uma função por operação (criar celebração, iniciar sessão, registrar instantâneo, etc.). Não escreva SQL novo nas rotas — se faltar uma operação, adicione a função aqui. |
| `import_csv.py` | Importa o `counting_people.csv` (contagem manual, contagem da câmera e comungantes) para o schema normalizado. Formato na seção "O arquivo `counting_people.csv`". |
| `calcular_coeficiente_inicial.py` | Calcula a média `comungantes_reais / contagem_sistema` (a contagem da câmera, a mesma que a estimativa recebe em produção) dos dados já importados e grava em `configuracao_estimativa` (modo `coeficiente_fixo`, margem de hóstias de 15%). Descarta os dias em que a câmera contou menos de 75% da contagem manual. Rodar de novo sempre que importar dado novo. |
| `preparar_dataset.py` | Monta o dataset de treino (ocupação, dia da semana, horário, tipo → comungantes reais) a partir do banco. Usado pelo script de treino, mas também roda sozinho pra inspecionar o dataset (`python3 preparar_dataset.py`). |
| `treinar_regressao.py` | Treina a regressão (modo `regressao`), valida com leave-one-out, salva o modelo em `modelos_estimativa/*.joblib` (na mesma pasta onde vive o banco, `CAMINHO_BANCO.parent`) e registra a versão em `configuracao_estimativa`. **Só treina com 15+ celebrações no banco** — com menos que isso, ele avisa e não faz nada (ver seção "Estimativa de comunhão" abaixo). |
| `requirements.txt` | Dependências só deste módulo (`pandas`, `scikit-learn`, `joblib`), nas mesmas versões do `backend/requirements.txt`, que já as inclui. Serve para quem quer rodar só os scripts do banco sem instalar o motor de visão. |

## Como a API usa este módulo

O `main.py` chama `inicializar_banco()` uma vez, na inicialização. As rotas
em `backend/api/rotas/` recebem uma conexão por requisição pela dependência
`obter_db` (`backend/api/dependencias.py`) e só chamam funções do `crud`:

```python
# backend/api/rotas/historico.py (resumido)
@router.get("/historico", response_model=list[RegistroHistorico])
def get_historico(db: sqlite3.Connection = Depends(obter_db)):
    return [RegistroHistorico(...) for r in crud.obter_historico(db)]
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
  energia, travamento), e porque a contagem manual importada da planilha
  e a contagem da câmera escrevem na mesma tabela, separadas só por
  `origem_contagem`.
- **`estimativa_comunhao`** guarda três fontes de valor lado a lado, de
  propósito:
  - `comungantes_reais` / `hostias_reais` — o número real, informado
    pela equipe (coluna `communed` do `counting_people.csv`, importada pelo
    `import_csv.py`).
  - `estimativa_calculada` / `hostias_calculadas` — o que o sistema
    prevê (coeficiente fixo ou regressão). Gravado automaticamente quando
    uma contagem da câmera termina como `concluida`
    (`integracao/sessao.py`), e completado no início do programa para as
    sessões concluídas que ficaram sem (`main.py`).
  - `estimativa_ajustada` / `hostias_ajustadas` — correção humana em
    cima do valor calculado (fluxo *human-in-the-loop* do TCC).
- **`vw_historico`** já entrega as colunas prontas para a tela Histórico
  do frontend (`data`, `celebracao`, `total_pessoas`, `estimativa_comunhao`,
  `hostias_sugeridas`, `entradas`, `saidas`) — não precisa fazer join nenhum
  na API, só `SELECT * FROM vw_historico` (via `crud.obter_historico`).

## Estimativa de comunhão: coeficiente fixo → regressão

O sistema opera em duas fases, sem precisar trocar de schema entre elas
(`configuracao_estimativa.metodo`):

1. **`coeficiente_fixo`** (fase inicial) — `calcular_coeficiente_inicial.py`
   calcula a média real observada e grava. É esse valor que a API lê
   (`crud.obter_configuracao_estimativa_vigente`) pra sugerir comungantes/
   hóstias enquanto não há modelo de regressão treinado.
2. **`regressao`** — assim que houver **15+ celebrações** com
   `comungantes_reais` preenchido no banco, `treinar_regressao.py` treina
   um modelo (contagem da câmera + dia da semana + horário + tipo → comungantes) e
   grava o caminho do artefato em `configuracao_estimativa.modelo_path`
   (salvo em `CAMINHO_BANCO.parent / "modelos_estimativa"`, ou seja, sempre
   ao lado do banco). Hoje o banco fica em `backend/db/`; o `database.py` já
   traz comentadas as linhas que o movem para `%APPDATA%\EucharistCount` no
   executável, e aí o modelo vai junto, fora da pasta temporária do
   PyInstaller.

Rotina recomendada: sempre que importar um lote novo de dados
(`import_csv.py`), rodar os dois scripts de novo, nessa ordem:

```bash
python3 calcular_coeficiente_inicial.py   # sempre atualiza o fallback
python3 treinar_regressao.py              # só re-treina se ja tiver dado suficiente
```

A estimativa usada pelo sistema é centralizada em
`backend/integracao/estimativa.py` (`calcular_estimativa`):
- Se `metodo == 'regressao'` e o arquivo `.joblib` existir, carrega o modelo
  (com cache em memória) e prevê os comungantes usando `ocupacao_final`,
  `minutos_missa`, `dia_semana` e `tipo` da celebração.
- Caso contrário (modo `coeficiente_fixo`, tabela vazia ou falha ao carregar o
  modelo), multiplica a ocupação pelo `coeficiente_comunhao` (ou pelo padrão
  `0.89` se o banco estiver vazio).

Assim, tanto o dashboard ao vivo quanto o histórico usam exatamente a mesma
regra e transicionam automaticamente do coeficiente fixo para a regressão
assim que o modelo é treinado.

## Ligação com o motor de visão

O motor já grava no banco durante a missa. Todo o ciclo da sessão fica em
`backend/integracao/sessao.py`, e o `main.py` (modo manual) e o agendador
(`integracao/agendador.py`, modo agendado) só o usam:

```python
fechar_sessoes_presas()            # no inicio: sessoes de execucoes anteriores -> 'interrompida'
preencher_estimativas_atrasadas()  # no inicio: estimativa das concluidas que ficaram sem

with sessao_de_monitoramento(monitor, config, celebracao_id=...) as gravador:
    metricas = monitor.executar(ao_atualizar=gravador)
# ao sair do "with": finalizar_sessao() com 'concluida' ou, se houve erro, 'interrompida';
# se 'concluida', grava a estimativa (registrar_estimativa_da_sessao)
```

`celebracao_id` vem do agendador (a celebração da agenda, ex.: "Missa das
10:00"). No modo manual ele não é passado, e a sessão cria a celebração
"Missa (monitoramento automatico)" com a data e a hora de agora.

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
  (`.py`, `.sql`, `.md`) é versionado. O `.gitignore` da raiz já cobre os
  dois (`*.db` e `backend/db/modelos_estimativa/`).

## O arquivo `counting_people.csv`

Os dados de campo: uma linha por missa, com **exatamente 9 colunas**
(uma vírgula a mais desloca o `notes` para uma coluna sem nome, e ele não é
importado).

| Coluna | Obrigatória | Conteúdo | Vai para |
|---|---|---|---|
| `id` | — | Número da linha (não é usado na importação) | — |
| `date` | sim | Data da missa, `AAAA-MM-DD` | `celebracao.data` |
| `time` | sim | Horário da missa, `HH:MM` | `celebracao.horario_missa` |
| `celebration_type` | — | Tipo (`common`, ...); vazio vira `comum` | `celebracao.tipo` |
| `people` | sim | Pessoas contadas manualmente | `sessao_monitoramento.ocupacao_final` |
| `communed` | — | Comungantes reais | `estimativa_comunhao.comungantes_reais` |
| `system_count` | — | Pessoas contadas pela câmera | `sessao_monitoramento.contagem_sistema` |
| `hosts_consecrated` | — | Hóstias consagradas | `estimativa_comunhao.hostias_reais` |
| `notes` | — | Observação livre (ex.: `camera_mal_posicionada`) | `sessao_monitoramento.observacoes` |

Linhas sem `date`, `time` ou `people` são ignoradas com aviso. Só as linhas
com `communed` entram no cálculo do coeficiente e no treino da regressão.
Reimportar o CSV (por exemplo, depois de corrigir uma linha) atualiza a
sessão e os comungantes da missa já importada (mesma data e horário), sem
duplicar.

## Testar

```bash
pip install -r requirements.txt               # pandas, scikit-learn, joblib

python database.py                            # cria o banco
python import_csv.py ../counting_people.csv   # importa os dados de campo
python calcular_coeficiente_inicial.py        # calcula e grava o coeficiente
python treinar_regressao.py                   # tenta treinar (avisa se faltar dado)
```

Para inspecionar: `sqlite3 eucharist_count.db` (ou DB Browser for SQLite),
ou em Python:

```python
from database import obter_conexao
con = obter_conexao()
for row in con.execute("SELECT * FROM vw_historico"):
    print(dict(row))
```
