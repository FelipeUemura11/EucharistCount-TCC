# Documentação Técnica — API e Integração

## Eucharist Count — Backend

Este documento explica **como as peças do backend foram ligadas**: o servidor FastAPI que alimenta o dashboard, a ponte que leva os números do motor de visão até o banco, e o caminho que uma pessoa cruzando o portão percorre até aparecer na tela.

| Documento | Cobre |
|---|---|
| [`DOCUMENTACAO_MOTOR.md`](./DOCUMENTACAO_MOTOR.md) | Motor de visão computacional: câmera, detecção, rastreio e contagem |
| [`DOCUMENTACAO_BANCO.md`](./DOCUMENTACAO_BANCO.md) | Modelo de dados, camada de acesso e estimativa de comunhão |
| **`DOCUMENTACAO_API.md`** (este) | Servidor FastAPI, ligação motor → banco e dashboard ao vivo |
| [`DOCUMENTACAO_DISTRIBUICAO.md`](./DOCUMENTACAO_DISTRIBUICAO.md) | Empacotamento em `.exe`, caminhos e início com o Windows |

---

## 1. Onde está cada coisa

O código deste documento está dividido por responsabilidade: cada arquivo resolve um problema, e o `main.py` só liga as peças na ordem certa.

```
backend/
├── main.py                 # orquestra: argumentos → banco → API → motor (agora ou pela agenda)
├── cli.py                  # argumentos de linha de comando → Config
├── integracao/             # ponte motor ↔ banco (não é API nem motor)
│   ├── sessao.py           # GravadorSessao, abrir/fechar sessão, sessões presas
│   ├── estimativa.py       # estimativa de comunhão e hóstias
│   └── agendador.py        # APScheduler: liga e desliga a contagem nos horários da agenda
└── api/                    # servidor web
    ├── app.py              # criar_app(): monta o FastAPI
    ├── servidor.py         # sobe o uvicorn numa thread
    ├── dependencias.py     # obter_db: uma conexão por requisição
    ├── schemas.py          # modelos Pydantic (contrato com o frontend)
    ├── formatacao.py       # datas, hora local, dia da semana
    ├── frontend.py         # serve o React compilado (catch-all)
    └── rotas/              # uma rota por tela do frontend
        ├── status.py
        ├── dashboard.py
        ├── celebracoes.py
        ├── historico.py
        └── configuracoes.py
```

| Pasta | Responsabilidade | Depende de |
|---|---|---|
| `api/` | Responder requisições HTTP | `db/`, `integracao/estimativa.py`, `motor/config.py` (para ler `config.json` em `/api/configuracoes`). **Não carrega o detector/YOLO** |
| `integracao/` | Transformar o que o motor vê em linhas no banco | `db/`, `motor/` |
| `motor/` | Visão computacional | Nada do resto: não sabe que banco e API existem (`DOCUMENTACAO_MOTOR.md`, seção 13) |
| `db/` | Acesso ao SQLite | Nada do resto |

**Por que `integracao/` fica fora de `api/`:** o `GravadorSessao` não responde requisições; ele liga o motor ao banco. Separado, ele continua útil mesmo sem servidor web, que é o caso do agendamento automático (seção 9): o agendador abre a sessão e roda o motor sozinho, no horário da missa.

---

## 2. Visão geral: um processo, duas threads

```mermaid
flowchart LR
    subgraph P["Processo único — python main.py"]
        direction TB
        subgraph T1["Thread principal"]
            MON["Monitor.executar()<br/>motor de visão"] -->|"ao_atualizar()<br/>a cada frame"| GRV["GravadorSessao<br/>integracao/sessao.py"]
        end
        subgraph T2["Thread daemon"]
            UV["uvicorn :8000<br/>api/servidor.py"] --> APP["FastAPI<br/>api/app.py"]
        end
    end
    GRV -->|"INSERT / UPDATE<br/>+ commit"| DB[("eucharist_count.db")]
    APP -->|"SELECT via crud"| DB
    NAV["Navegador<br/>Dashboard React"] -->|"GET /api/dashboard<br/>a cada 2 s"| APP
```

Um único comando, `python main.py`, sobe tudo: o motor que conta, o banco que guarda e o servidor que mostra. Na máquina da paróquia, ninguém deveria precisar abrir três terminais, e o empacotamento futuro com PyInstaller gera **um único executável**.

As duas partes precisam de threads separadas porque **as duas ficam presas num laço**: o `Monitor` lendo frames, o uvicorn esperando requisições. Numa thread só, uma bloquearia a outra.

O diagrama mostra o modo manual. No modo agendado (seção 9), o motor roda numa thread do APScheduler, e a thread principal só espera o `Ctrl+C`.

Elas **não compartilham memória** para trocar dados: o motor escreve no banco e a API lê do banco. O banco é a única interface entre as duas. Isso mantém a porta aberta para rodar motor e API em processos, ou até máquinas, diferentes, sem mudar nenhum dos dois lados.

### 2.1 Por que a API é daemon, e o que isso exige da thread principal

O Python encerra o programa quando a **última thread não-daemon** termina. As threads daemon não seguram o programa aberto: morrem junto com ele. A API é daemon de propósito:

- se não fosse, o programa nunca terminaria, porque o uvicorn seguraria o processo aberto para sempre;
- o Ctrl+C também não resolveria, porque o uvicorn só trata o Ctrl+C quando roda na thread principal.

A consequência é que **quem decide quando o programa termina é a thread principal**. Por isso, quando o vídeo acaba, ela não retorna: imprime o resumo e fica num laço `while True: time.sleep(1)`, mantendo o dashboard no ar até o usuário apertar Ctrl+C. Sem esse laço, o fim do vídeo derrubaria o dashboard justamente no momento em que os números finais existem.

O laço usa `time.sleep(1)`, e não `threading.Event().wait()`, porque no Windows uma espera sem tempo limite pode não ser interrompida pelo Ctrl+C, e o programa ficaria impossível de fechar pelo terminal.

---

## 3. A inicialização, passo a passo

O que `main()` faz, em ordem:

| # | Passo | Onde | Por quê |
|---|---|---|---|
| 1 | `multiprocessing.freeze_support()` | `main.py` | Exigência do PyInstaller no Windows: sem isso, o executável pode abrir cópias de si mesmo em loop |
| 2 | Lê o `config.json` + `.env` e aplica os argumentos | `cli.py` | O `config.json` e o `.env` definem o padrão; os argumentos sobrescrevem só naquela execução |
| 3 | `inicializar_banco()` | `db/database.py` | Cria as tabelas que ainda não existirem (`DOCUMENTACAO_BANCO.md`, seção 6.1) |
| 4 | `fechar_sessoes_presas()` | `integracao/sessao.py` | Fecha como `interrompida` sessões de execuções anteriores que não terminaram (seção 6.6) |
| 5 | `iniciar_em_background(criar_app())` | `api/` | O dashboard fica no ar antes do motor começar |
| 6 | `modo_manual(args)` | `cli.py` | Com `--agora` ou `--fonte`, conta agora; sem eles, segue a agenda (seção 9) |
| 7 | **Manual:** `executar_manual(config)` | `main.py` | `Monitor(config, RAIZ)` valida a fonte e carrega o YOLO **antes de abrir a sessão** (seção 6.5); depois `with sessao_de_monitoramento(...)` + `monitor.executar(...)` e o resumo no terminal |
| 7 | **Agendado:** `iniciar_agendado(config)` | `main.py` | Carrega o `Monitor` uma vez, sem janela, liga o `Agendador` e mostra as próximas contagens (seção 9) |
| 8 | `while True: time.sleep(1)` | `main.py` | Mantém o dashboard (e o agendador) no ar até o Ctrl+C (seção 2.1) |

Se o modelo não existir (`FileNotFoundError`) ou a fonte de vídeo não estiver configurada / não abrir (`RuntimeError`), o `main.py` captura a exceção, exibe um aviso no terminal e **mantém o dashboard ativo** no laço final para consultas ao histórico e configurações. O Ctrl+C, a qualquer momento, encerra com código 0. No modo agendado, antes de sair, ele chama `agendador.encerrar()`: uma contagem em andamento é fechada como `interrompida`.

### 3.1 Argumentos de linha de comando (`cli.py`)

| Argumento | Sobrescreve | Exemplo |
|---|---|---|
| `--fonte` | `camera.fonte` | `--fonte videos/20-09-teste.mp4` |
| `--modelo` | `deteccao.modelo` | `--modelo modelos/yolo11s_dyn.onnx` |
| `--imgsz` | `deteccao.imgsz` | `--imgsz 640` |
| `--conf` | `deteccao.confianca` | `--conf 0.25` |
| `--fps` | `camera.fps_processamento` | `--fps 5` |
| `--linha` | `contagem.linha` | `--linha 0.25,0.0,0.25,1.0` |
| `--sem-janela` | `visual.mostrar_janela = false` | produção, sem interface gráfica |
| `--agora` | — (escolhe o modo) | conta agora, sem esperar a agenda; `--fonte` também ativa o modo manual (seção 9.1) |
| `--boot` | não abre o navegador | usado pela entrada de início do Windows (`DOCUMENTACAO_DISTRIBUICAO.md`, seção 3.1) |

Os argumentos numéricos são testados com `is not None`, e não com `if valor:`. Isso porque em Python `0` é falso: o teste antigo ignorava um `--fps 0` (processar todos os frames) digitado de propósito. O `argparse` usa `None` para "não informado", e é exatamente isso que o teste verifica.

A configuração efetiva, já com os argumentos aplicados, fica gravada em `sessao_monitoramento.parametros_contagem`.

---

## 4. Os endpoints

| Método e rota | Arquivo | Devolve | Usado por |
|---|---|---|---|
| `GET /api/status` | `rotas/status.py` | Se há contagem ativa | Selo "Contagem ativa" no topo das páginas (a cada 5 s) |
| `GET /api/dashboard` | `rotas/dashboard.py` | Métricas, gráfico e resumo da missa atual ou da última | Página Dashboard (a cada 2 s) |
| `GET /api/celebracoes` | `rotas/celebracoes.py` | Celebrações do mês corrente | Ainda não usado (a página Celebrações usa dados fixos) |
| `GET /api/historico` | `rotas/historico.py` | Missas encerradas, com os resultados | Página Histórico (a cada 10 s) |
| `GET /api/configuracoes` | `rotas/configuracoes.py` | Agenda padrão e dados da câmera (`infoCamera`) | Página Configurações |
| `POST /api/configuracoes/agenda` | `rotas/configuracoes.py` | O horário criado, com `id` | Página Configurações (botão "Adicionar") |
| `DELETE /api/configuracoes/agenda/{id}` | `rotas/configuracoes.py` | `{ "sucesso": true }`, ou **404** | Página Configurações (lixeira) |
| `GET /api/<inexistente>` | `frontend.py` | **404** | — |
| `GET /{qualquer outro caminho}` | `frontend.py` | O frontend compilado | O navegador |
| `GET /docs` | automático | Documentação interativa (Swagger) | Desenvolvimento |

### 4.1 Como as rotas são montadas

Cada arquivo em `api/rotas/` cria um `APIRouter()`: um "mini-app" com as rotas daquela tela. As rotas declaram só o final do caminho (`"/status"`, `"/dashboard"`), e o prefixo `/api` é aplicado uma vez só, em `api/app.py`:

```python
def criar_app() -> FastAPI:
    app = FastAPI(title="Eucharist Count")

    for rotas in (status, dashboard, celebracoes, historico, configuracoes):
        app.include_router(rotas.router, prefix="/api")

    # POR ULTIMO: o catch-all aceita qualquer caminho.
    app.include_router(frontend.router)
    return app
```

- **Um arquivo por tela.** A divisão espelha as páginas do React: se o Histórico mostrar algo errado, a rota está em `historico.py` e em mais nenhum lugar.
- **A ordem importa.** O FastAPI testa as rotas na ordem em que foram registradas, e a rota do frontend aceita qualquer caminho. Se ela viesse antes, capturaria também as chamadas da API.
- **`criar_app()` é uma *app factory*.** Em vez de uma variável global `app`, é uma função que monta um app novo a cada chamada. Um teste pode criar o seu app sem importar o `main.py`, o que evita carregar o YOLO e subir o motor.

As respostas são descritas pelos **modelos Pydantic** de `api/schemas.py` (`DadosDashboard`, `Celebracao`, `RegistroHistorico`, `ConfiguracoesGlobais`…). Eles espelham, campo a campo e com os mesmos nomes em português e *camelCase*, as interfaces TypeScript de `frontend/src/types/`. O FastAPI usa esses modelos para validar a saída: um campo com o tipo errado dá erro no servidor, e não vira um bug silencioso na tela.

As conversões de formato ficam em `api/formatacao.py`, como **funções puras** (recebem um valor e devolvem outro, sem tocar em banco nem rede). As rotas só as chamam:

| Função | Converte |
|---|---|
| `formatar_data_br()` | `2026-09-21` → `21/09/2026` |
| `formatar_dia_semana()` | `2026-09-21` → `Segunda-feira` |
| `dia_do_mes()` | `2026-09-21` → `21` |
| `hora_de_timestamp()` | `2026-09-26T21:00:00` (UTC) → `18:00` (hora local) |

O status das celebrações não precisa de conversão: a API devolve o mesmo valor do banco (`agendada`, `em_andamento`, `finalizada`, `cancelada`).

### 4.2 `GET /api/status`

```json
{ "contagemAtiva": true }
```

`true` se existir alguma sessão com `status = 'em_andamento'` (`crud.obter_sessao_ativa`). Reflete **só** a contagem ativa: quando o vídeo acaba, o selo desliga, mesmo que o dashboard continue mostrando os números da missa que terminou.

### 4.3 `GET /api/dashboard`

A rota mostra **a contagem em andamento** ou, se não houver, **a última missa encerrada**:

```python
sessao = crud.obter_sessao_ativa(db) or crud.obter_ultima_sessao_concluida(db)
```

Se `obter_sessao_ativa` devolve `None`, o `or` passa para a segunda consulta. O motivo é que é logo depois do vídeo que a equipe quer ver o resultado final. Antes, a tela zerava nesse momento; pior, se houvesse uma sessão presa de outra execução, mostrava a dela.

`obter_ultima_sessao_concluida` só considera contagens da câmera (`origem_contagem = 'visao_computacional'`). As sessões manuais, importadas da planilha, não têm gráfico nem entradas e saídas.

Exemplo, com uma contagem manual em andamento (no modo agendado, o título é o da agenda, como "Missa das 10:00", e `inicioMonitoramento`/`fimMonitoramento` vêm preenchidos):

```json
{
  "metricas": {
    "ocupacaoAtual": 42,
    "estimativaComunhao": 32,
    "hostiasSugeridas": 36,
    "entradas": 50,
    "saidas": 8,
    "contagemAtiva": true
  },
  "graficoOcupacao": [
    { "hora": "18:30", "ocupacao": 12 },
    { "hora": "18:30", "ocupacao": 25 },
    { "hora": "18:31", "ocupacao": 42 }
  ],
  "resumoCelebracao": {
    "titulo": "Missa (monitoramento automatico)",
    "inicioMonitoramento": "",
    "fimMonitoramento": ""
  }
}
```

De onde vem cada campo:

| Campo | Origem | Atualizado |
|---|---|---|
| `ocupacaoAtual` | `sessao_monitoramento.ocupacao_final` | A cada passagem pela linha |
| `entradas` / `saidas` | `sessao_monitoramento.total_entradas` / `total_saidas` | A cada passagem pela linha |
| `estimativaComunhao` | `calcular_estimativa(db, ocupação, celebracao=celebracao).comungantes` (seção 8) | Junto com a ocupação |
| `hostiasSugeridas` | `calcular_estimativa(db, ocupação, celebracao=celebracao).hostias` (com `margem_hostias` do banco) | Junto com a ocupação |
| `margemHostias` | `calcular_estimativa(...).margem`: a folga já incluída em `hostiasSugeridas` (`0.15` = 15%). A tela a mostra ao lado das hóstias | Junto com a ocupação |
| `contagemHabitual` | `contagem_abaixo_do_habitual()`: a mediana do histórico do mesmo dia e horário quando a contagem está abaixo de 70% dela; `null` no resto. A tela mostra o aviso "contagem abaixo do habitual" (`DOCUMENTACAO_BANCO.md`, seção 9.4) | Junto com a ocupação |
| `contagemAtiva` | `sessao["status"] == "em_andamento"` | `false` quando mostra a última missa encerrada |
| `graficoOcupacao[]` | `instantaneo_ocupacao`: `hora` = `hora_de_timestamp(registrado_em)`, `ocupacao` = `ocupacao_atual` | A cada 5 s de vídeo |
| `resumoCelebracao` | Título e janela de monitoramento da celebração | — |

Três detalhes:

- **A ocupação atual vem da sessão, e não do último ponto do gráfico.** A sessão é atualizada no instante em que alguém cruza a linha; o gráfico, só a cada 5 segundos de vídeo. Ler do gráfico deixaria o número principal até 5 segundos atrasado em relação aos cartões de entradas e saídas.
- **A API manda só os valores do resumo.** Ícones e rótulos ficam fixos em `ResumoDaCelebracao.tsx`. O rótulo da primeira linha muda com `contagemAtiva` ("Missa atual" durante a contagem, "Última missa" depois), e a linha "Pessoas presentes" usa `metricas.ocupacaoAtual`.
- **Celebração inexistente não derruba a rota.** Se a sessão apontar para uma celebração removida, título e horários saem como "Desconhecido" e vazios, em vez de lançar `TypeError`.

Sem nenhuma sessão (nem ativa, nem encerrada), a rota devolve o mesmo formato, zerado, com o gráfico vazio e `resumoCelebracao: null`. O frontend mostra "Nenhuma missa registrada ainda." no lugar do resumo.

### 4.4 `/api/celebracoes`

Tela Celebrações. A agenda semanal fica em `/api/configuracoes` (seção 4.6); aqui entram as missas **fora da rotina** (Natal, Páscoa, casamento, exéquias, missa de última hora) e o calendário do mês.

| Rota | Comportamento |
|---|---|
| `GET /api/celebracoes?ano=&mes=` | Celebrações do mês pedido (`crud.listar_celebracoes_do_mes`, que filtra por `data LIKE 'AAAA-MM%'`). Sem `ano` e `mes`, vale o mês atual. `mes` fora de 1 a 12 responde **422** |
| `POST /api/celebracoes` | Cria uma celebração **agendada** e responde **201** com o registro criado |
| `DELETE /api/celebracoes/{id}` | Cancela (`status = 'cancelada'`). **404** se não existir; **409** se já estiver `em_andamento` ou `finalizada` |

Campos devolvidos pelo `GET` e pelo `POST`:

| Campo | Origem |
|---|---|
| `id`, `titulo`, `tipo` | `celebracao.id`, `titulo`, `tipo` |
| `dia`, `diaSemana` | Derivados de `celebracao.data` (`dia_do_mes`, `formatar_dia_semana`) |
| `horarioMissa`, `inicioMonitoramento`, `fimMonitoramento` | `horario_missa`, `horario_inicio/fim_monitoramento` |
| `pessoasEsperadas`, `capacidade` | `pessoas_esperadas`, `capacidade` (`0` se vazios) |
| `status` | `celebracao.status`, sem conversão: `agendada`, `em_andamento`, `finalizada` ou `cancelada` |

**Corpo do `POST`** (`CelebracaoCriar`): `titulo`, `tipo` (`comum`, `especial`, `natal`, `pascoa`, `casamento` ou `exequias`), `data` (`AAAA-MM-DD`), `horarioMissa`, `inicioGravacao`, `fimGravacao` (`HH:MM`) e `repetirSemanalmente`.

**Validações**, as mesmas da agenda mais as da data:

| Situação | Resposta |
|---|---|
| Hora fora do formato `HH:MM`, fim da gravação não depois do início, data impossível ou no passado, tipo fora da lista, título vazio | **422** |
| Data de hoje com o fim da gravação já passado | **422** (não haveria o que contar) |
| Já existe celebração naquela data e horário | **409** (`UNIQUE (data, horario_missa)`) |
| A janela de gravação se sobrepõe a outra celebração do dia ou a uma missa da agenda daquele dia da semana | **409** (a contagem é uma por vez) |

Uma celebração **cancelada** no mesmo dia e horário não bloqueia: ela é apagada para dar lugar à nova (só se nunca foi contada).

**`repetirSemanalmente`:** além da celebração, grava um horário em `horario_padrao` (mesmo dia da semana e horário da missa), de modo que a missa passa a se repetir toda semana pela agenda existente, sem tabela nova. Se a agenda já tem esse dia e horário, ele é reaproveitado, sem duplicar. A celebração criada fica ligada a esse horário (`horario_padrao_id`), então o disparo semanal a reaproveita, com o título e o tipo escolhidos (seção 9.6).

Depois de salvar ou cancelar, a rota chama `recarregar_agenda()`, e a mudança vale na hora, sem reiniciar o programa.

### 4.5 `GET /api/historico`

Lê a view `vw_historico` (`DOCUMENTACAO_BANCO.md`, seção 3.8): uma linha por celebração `finalizada`, com a sessão `concluida` mais recente (se o monitoramento foi reiniciado, as tentativas anteriores não aparecem), da data mais recente para a mais antiga.

| Campo | Origem |
|---|---|
| `id` | `sessao_id` |
| `data` | `data` convertida para `dd/mm/aaaa` |
| `diaSemana` | Dia da semana por extenso |
| `celebracao`, `horarioMissa` | Título e horário da missa |
| `totalPessoas` | `ocupacao_final` |
| `estimativaComunhao`, `hostiasSugeridas` | Já priorizados pela view: ajustado → calculado → real. Para contagens da câmera, dependem de a estimativa ter sido gravada em `estimativa_comunhao` (seção 8); sem ela, saem `0` |
| `entradas`, `saidas` | `total_entradas`, `total_saidas` |

### 4.6 `/api/configuracoes`

A agenda semanal padrão fica na tabela `horario_padrao` (`DOCUMENTACAO_BANCO.md`, seção 3.1), lida e escrita pelas funções de `crud.py`.

| Rota | Comportamento |
|---|---|
| `GET /api/configuracoes` | `agendaPadrao`: horários ativos, por dia e hora. `infoCamera`: fonte (do `.env`), `imgsz` e FPS (do `config.json`) lidos por `Config.carregar()`, resolvidos pela raiz do backend. Sem `CAMERA_FONTE`, a fonte aparece como "Não definida (CAMERA_FONTE no .env)". A senha de uma URL RTSP sai mascarada (`mascarar_senha`: `rtsp://usuario:***@...`) |
| `POST /api/configuracoes/agenda` | Recebe `diaSemana` (0 = domingo a 6), `horarioMissa`, `inicioGravacao` e `fimGravacao` (`HH:MM`). Fora do formato, ou com o fim antes do início, responde **422** |
| `DELETE /api/configuracoes/agenda/{id}` | *Soft delete* (`ativo = 0`): celebrações geradas pelo horário mantêm a referência. **404** se não houver horário ativo com o `id` |

Depois de criar ou remover um horário, as duas rotas chamam `recarregar_agenda()` (`integracao/agendador.py`): a mudança vale na hora, sem reiniciar o programa (seção 9.4). Sem agendador ligado (modo manual), a chamada não faz nada.

### 4.7 Uma conexão por requisição (`api/dependencias.py`)

```python
def obter_db():
    conexao = obter_conexao()
    try:
        yield conexao
    finally:
        conexao.close()

@router.get("/status")
def get_status(db: sqlite3.Connection = Depends(obter_db)):
    ...
```

`Depends(obter_db)` é a **injeção de dependência** do FastAPI: antes de cada requisição, ele executa `obter_db()` até o `yield` e entrega a conexão para a rota; depois da resposta, executa o `finally` e fecha a conexão. Cada requisição tem sua própria conexão, e nenhuma fica aberta esquecida, mesmo se a rota lançar exceção.

As rotas são funções comuns (`def`), não `async def`. O FastAPI roda funções comuns num pool de threads, que é o certo aqui: o `sqlite3` é bloqueante, e uma consulta dentro de `async def` travaria o servidor inteiro enquanto esperasse o disco.

---

## 5. Servindo o frontend (`api/frontend.py`)

A mesma porta 8000 serve a API **e** o dashboard compilado. Não é preciso um servidor web separado para o React.

A rota `/{catchall:path}` segue esta regra, na ordem:

1. Se o caminho começa com `api/`, devolve **404**. Nenhuma tela do React começa com `/api/`, então o que chegou até aqui é uma rota da API que não existe.
2. Se o caminho é um arquivo que existe **dentro de** `frontend/dist/` (um `.js`, `.css`, imagem), devolve o arquivo. O caminho passa por `resolve()`, que desfaz os `..`, e só é servido se `is_relative_to(dist)`.
3. Se `frontend/dist/index.html` não existe, devolve um aviso pedindo `npm run build`.
4. Senão, devolve o `index.html`.

- **O passo 1 existe por causa de um bug real.** Antes dele, uma rota da API inexistente devolvia o `index.html` com status 200. O frontend recebia HTML onde esperava JSON, o erro era engolido, e a tela ficava vazia sem nenhum aviso. Foi assim que a rota do histórico (na época `/api/history`), quebrada na reorganização por um `@` que faltava, passou despercebida.
- **A checagem do passo 2 fecha um *path traversal*.** Antes, o caminho era só `dist / catchall`. O uvicorn decodifica `%2e%2e` para `..`, então `GET /%2e%2e/%2e%2e/backend/config.json` devolvia o `config.json`, e o mesmo valia para o banco e o `.env`. Na época o servidor escutava em `0.0.0.0`, então qualquer máquina da rede da paróquia conseguia baixar esses arquivos. Agora esse caminho cai no passo 4, e o servidor só escuta em `127.0.0.1` (ver *Acesso só local* abaixo).
- **O passo 4 faz as rotas do React funcionarem ao recarregar a página.** `/historico` não é um arquivo, e sim uma tela que o React desenha no navegador; sem essa regra, apertar F5 em `/historico` daria 404.

**O frontend precisa estar compilado.** O servidor entrega a pasta `dist/`, e não o código-fonte React. Mudanças no frontend só aparecem em `:8000` depois de `npm run build` na pasta `frontend`. Durante o desenvolvimento, `npm run dev` serve o frontend com recarga automática na porta 5173, e o *proxy* do Vite (`frontend/vite.config.ts`) repassa as chamadas `/api` para `:8000`. O `main.py` precisa estar rodando.

**Onde fica `dist/`:**
- **em desenvolvimento:** em `frontend/dist`, calculado como `RAIZ.parent / "frontend" / "dist"`. O `RAIZ` vem de `motor/config.py` e aponta para `backend/`. O caminho não depende de onde o `frontend.py` está: um `Path(__file__).parent.parent` mudaria de significado se o arquivo trocasse de pasta, que foi exatamente o que aconteceu na reorganização;
- **no executável do PyInstaller:** os arquivos são extraídos numa pasta temporária indicada por `sys._MEIPASS`, e o `getattr(sys, "frozen", False)` escolhe entre os dois casos.

**Acesso só local.** O sistema é usado só no PC onde está instalado, e o dashboard não tem login. Por isso:

- **O servidor escuta em `127.0.0.1`** (`api/servidor.py`), não em `0.0.0.0`. Outra máquina da rede não alcança o dashboard nem a API.
- **O frontend usa endereços relativos** (`/api/dashboard`, `/api/status`...). Servido pelo `main.py`, a página e a API estão na mesma origem (`:8000`). Em desenvolvimento, o *proxy* do Vite faz o mesmo papel.
- **Não há CORS.** Como tudo vem da mesma origem, o `CORSMiddleware` saiu. Antes ele liberava `allow_origins=["*"]`, e qualquer site aberto no navegador do PC podia chamar a API, inclusive para apagar horários da agenda.

Para voltar a abrir o dashboard de outra máquina, seria preciso trocar o `host` para `0.0.0.0`, e antes disso colocar autenticação.

---

## 6. A ligação motor → banco (`integracao/sessao.py`)

### 6.1 O problema

Os números nascem dentro do loop do `Monitor`, frame a frame. Eles precisam chegar ao banco **enquanto a missa acontece**, para o dashboard mostrar a contagem ao vivo. O jeito mais direto seria chamar o `crud` dentro do `monitor.py`, mas isso quebraria o princípio central do motor (`DOCUMENTACAO_MOTOR.md`, seção 11): cada módulo não sabe nada dos outros. O motor passaria a depender do banco, e deixaria de ser testável sem um.

### 6.2 A solução: um callback

O `Monitor` tem um único parâmetro opcional:

```python
def executar(self, ao_atualizar: Callable[[Metricas, float], None] | None = None) -> Metricas:
    ...
    self._atualizar_metricas(pessoas, ultimo_instante)
    if ao_atualizar is not None:
        ao_atualizar(self.metricas, fonte.tempo_atual)
```

A cada frame processado, o motor chama a função recebida com as métricas atuais e o instante do frame **no tempo do vídeo**. O motor não sabe quem está ouvindo nem o que será feito com isso, e continua sem importar nada de `db/`.

### 6.3 O `GravadorSessao`

Quem escuta é o `GravadorSessao`. É uma classe com o método especial `__call__`, o que permite passar o objeto onde se espera uma função. A vantagem sobre uma função comum é que o objeto **guarda estado entre uma chamada e outra**:

| Atributo | Guarda |
|---|---|
| `_ultimo` | O instante do último instantâneo gravado. Começa em `-math.inf`, para o primeiro frame sempre gravar |
| `_totais` | O par `(entradas, saídas)` da última gravação dos totais |
| `pico` | A maior ocupação já vista, conferida em **todo** frame |

```python
def __call__(self, metricas, instante):
    self.pico = max(self.pico, metricas.dentro)

    totais = (metricas.entradas, metricas.saidas)
    if totais != self._totais:                    # alguém cruzou a linha
        self._totais = totais
        crud.atualizar_totais_sessao(...)          # grava na hora

    if instante - self._ultimo < self.intervalo:  # ainda não deu 5 s
        return
    self._ultimo = instante
    crud.registrar_instantaneo(...)                # um ponto no gráfico
```

### 6.4 Dois ritmos de escrita

O gravador faz duas escritas diferentes, em ritmos diferentes, porque elas servem a leitores diferentes:

| Escrita | Ritmo | Serve a | Por quê |
|---|---|---|---|
| Totais da sessão | **No frame em que alguém cruza a linha** | Cartões de ocupação, entradas e saídas | Quem olha o painel espera ver o número mudar quando a pessoa passa |
| Instantâneo | **A cada 5 segundos de vídeo** | Gráfico "Evolução da ocupação" | Uma curva precisa de pontos regulares, não de um ponto por frame |

**Por que os totais não saem caros:** o motor chama o gravador 7,5 vezes por segundo, mas pessoas cruzando a linha são raras em comparação. Na imensa maioria dos frames, `(entradas, saídas)` não mudou e o gravador nem toca no banco.

**Por que 5 segundos para o gráfico:** gravar a cada frame daria ~27.000 linhas por hora de missa, com um `commit()` em disco a cada uma, disputando CPU com a detecção e travando por instantes as leituras da API. Com 5 segundos, são 720 linhas por hora, o suficiente para desenhar a curva com folga. O valor começou em 10 segundos e foi reduzido para 5 para o gráfico parecer mais "ao vivo". A justificativa completa está em `DOCUMENTACAO_BANCO.md`, seção 7.3. Para mudar, basta um argumento: `GravadorSessao(conexao, sessao_id, intervalo=5.0)`.

**Por que segundos de vídeo:** o intervalo é medido com `fonte.tempo_atual`, e não com o relógio da máquina, pelo mesmo motivo do cooldown da contagem (`DOCUMENTACAO_MOTOR.md`, seção 8.8): o mesmo vídeo de teste gera sempre os mesmos pontos, qualquer que seja a velocidade do computador. Numa câmera ao vivo, os dois relógios coincidem.

### 6.5 Abrindo e fechando a sessão: um context manager

Todo o ciclo de vida da sessão fica numa função com `@contextmanager`, usada no `main.py` como um bloco `with`:

```python
monitor = Monitor(config, RAIZ)                      # 1. carrega o modelo

with sessao_de_monitoramento(monitor, config) as gravador:
    metricas = monitor.executar(ao_atualizar=gravador)
```

Por dentro, simplificado:

```python
@contextmanager
def sessao_de_monitoramento(monitor, config):
    conexao = obter_conexao()
    celebracao_id = crud.obter_ou_criar_celebracao(...)
    sessao_id = crud.iniciar_sessao(...)             # 2. abre a sessão
    gravador = GravadorSessao(conexao, sessao_id)

    status = "concluida"
    try:
        yield gravador                               # 3. o bloco "with" roda aqui
    except BaseException:
        status = "interrompida"                      # 4. terminou com erro
        raise
    finally:
        crud.finalizar_sessao(..., status=status)    # 5. fecha, aconteça o que acontecer
        conexao.close()
```

- **Como o `@contextmanager` funciona.** Tudo antes do `yield` roda na entrada do `with`; o `yield` entrega o gravador para o bloco; o `finally` roda na saída, **mesmo se houver erro**. Quem lê `with sessao_de_monitoramento(...)` entende o que acontece sem ver os detalhes.
- **O `Monitor` é criado antes de abrir a sessão.** Se o modelo não existir, o erro acontece antes de qualquer escrita, e não fica uma sessão vazia no banco.
- **Concluída ou interrompida.** Se o bloco termina normalmente (fim do vídeo, ESC), a sessão fecha como `concluida`. Se termina por exceção (a fonte não abriu, um erro no motor, Ctrl+C), o `except` anota `interrompida` e relança a exceção, para o `main.py` ainda mostrar a mensagem. O `BaseException` é necessário porque o `KeyboardInterrupt` do Ctrl+C não herda de `Exception`. Só sessões `concluida` entram no Histórico, então uma contagem que falhou não aparece lá como resultado válido com zeros. O mesmo vale para uma contagem que terminou normal, mas é impossível (mais saídas que entradas) ou menor que `contagem.minimo_pessoas`: a sessão é gravada como `interrompida`, com o motivo em `observacoes` (`DOCUMENTACAO_BANCO.md`, seção 5.2).
- **Uma conexão para a missa inteira.** O gravador usa a mesma conexão durante toda a sessão, ao contrário da API, que abre uma por requisição (`DOCUMENTACAO_BANCO.md`, seção 7.5).

**Qual celebração é usada:** no modo agendado, o agendador passa `celebracao_id` com a celebração da agenda, por exemplo "Missa das 10:00", ligada ao `horario_padrao` e com início e fim de monitoramento (seção 9). No modo manual, sem `celebracao_id`, a celebração é criada na hora, com a data e o horário em que a contagem começou e o título "Missa (monitoramento automatico)". Reiniciar no mesmo minuto reaproveita a celebração (`obter_ou_criar_celebracao`) e cria uma segunda sessão nela.

### 6.6 Sessões presas: `fechar_sessoes_presas()`

O `finally` cobre ESC, erro e Ctrl+C, mas não cobre o processo **morto de fora**: queda de energia, terminal fechado no X, o Gerenciador de Tarefas. Nesses casos nenhum código Python chega a rodar, e a sessão fica `em_andamento` para sempre. O efeito aparecia no dashboard: ao terminar uma contagem real, a tela passava a mostrar a sessão presa como se fosse a missa em andamento.

A correção roda **na próxima inicialização**, logo depois de `inicializar_banco()`:

```python
presas = fechar_sessoes_presas()   # crud.interromper_sessoes_orfas()
```

Toda sessão ainda `em_andamento` é marcada como `interrompida`, com `finalizado_em`, e a celebração dela como `finalizada`. O programa avisa no terminal quantas fechou.

É seguro porque **só um processo roda o motor**. No instante em que o programa está começando, nenhuma contagem pode estar legitimamente em andamento: qualquer sessão nesse estado é de uma execução anterior que não terminou.

---

## 7. O dashboard ao vivo e depois do vídeo

### 7.1 O caminho de uma pessoa até a tela

```mermaid
sequenceDiagram
    participant C as Contador (motor)
    participant G as GravadorSessao
    participant DB as SQLite
    participant F as Dashboard (React)
    participant API as FastAPI

    C->>C: pessoa sai da zona morta do outro lado → entradas + 1
    C->>G: ao_atualizar() no mesmo frame
    G->>DB: atualizar_totais_sessao() + commit
    Note over F: até 2 s depois...
    F->>API: GET /api/dashboard
    API->>DB: obter_sessao_ativa()
    DB-->>API: total_entradas atualizado
    API-->>F: JSON
    F->>F: React redesenha os cartões
```

O atraso entre a pessoa ser contada e o número mudar na tela é de **no máximo cerca de 2 segundos**. A gravação acontece no mesmo frame da contagem; o atraso restante é o intervalo de consulta do navegador.

### 7.2 Depois do vídeo

```mermaid
stateDiagram-v2
    [*] --> Zerado : nenhuma sessão no banco
    Zerado --> AoVivo : uma contagem começa (--agora ou agenda)
    AoVivo --> AoVivo : alguém cruza a linha / a cada 5 s de vídeo
    AoVivo --> UltimaMissa : fim do vídeo ou ESC (concluida)
    UltimaMissa --> AoVivo : nova contagem começa
    UltimaMissa --> [*] : Ctrl+C encerra o programa
```

| Estado | O dashboard mostra | Selo "Contagem ativa" |
|---|---|---|
| Ao vivo | A sessão `em_andamento`, atualizando a cada 2 s | Ligado |
| Última missa | Os números finais da última sessão `concluida`, com o rótulo "Última missa" | Desligado |
| Zerado | Tudo 0 (só se não houver nenhuma sessão da câmera no banco) | Desligado |

### 7.3 Consulta repetida (*polling*)

O frontend busca `/api/dashboard` a cada 2 segundos (`frontend/src/hooks/useDashboard.ts`, constante `INTERVALO_ATUALIZACAO_MS`). O selo de status no topo das páginas faz o mesmo com `/api/status` a cada 5 segundos (`useStatusContagem.ts`), e a tela Histórico consulta `/api/historico` a cada 10 segundos (`useHistorico.ts`).

A alternativa seria o servidor **empurrar** os dados para o navegador, por WebSocket ou *Server-Sent Events*. A consulta repetida foi escolhida porque, neste cenário, as vantagens do *push* não compensam a complexidade:

- **A carga é irrelevante.** Há um navegador, na mesma máquina, fazendo uma consulta leve a cada 2 segundos.
- **Recuperação automática.** Se a API cair e voltar, a próxima consulta simplesmente funciona. Com WebSocket, seria preciso programar a detecção da queda e a reconexão.
- **2 segundos já parece instantâneo** para um painel de ocupação. Se for preciso mais rápido, basta mudar a constante.
- **O banco continua sendo a única interface.** Com *push*, a API teria que ser avisada pelo motor de cada mudança, o que acoplaria as duas threads.

Se a API não responder, o hook **mantém na tela os últimos dados recebidos** e tenta de novo no ciclo seguinte. Antes da primeira resposta, o Dashboard mostra tudo zerado e o Histórico, uma lista vazia. Os estados iniciais dos dois hooks (`useDashboard`, `useHistorico`) foram trocados de dados de demonstração para valores vazios justamente para que números fictícios nunca apareçam como se fossem uma contagem real.

---

## 8. A estimativa de comunhão (`integracao/estimativa.py`)

A estimativa é calculada **num lugar só**. O arquivo tem três funções públicas:

| Função | O que faz | Quem chama hoje |
|---|---|---|
| `calcular_estimativa(conexao, ocupacao, celebracao=None)` | Calcula comungantes e hóstias (via regressão ou coeficiente fixo) | `api/rotas/dashboard.py`, a cada consulta |
| `registrar_estimativa_da_sessao(conexao, sessao_id, ocupacao)` | Calcula e **grava** em `estimativa_comunhao`, de onde o Histórico lê | `integracao/sessao.py`, ao fechar uma sessão concluída (e `preencher_estimativas_pendentes`) |
| `preencher_estimativas_pendentes(conexao)` | Grava a estimativa de toda sessão concluída que ainda não tem uma | `main.py`, ao iniciar (e manualmente, comando abaixo) |

Se o dashboard e o histórico tivessem cada um a sua cópia da conta, bastaria alguém mudar uma delas para os dois mostrarem números diferentes. Com uma função só, os dois sempre concordam.

A regra opera em duas fases conforme a linha vigente de `configuracao_estimativa` (`DOCUMENTACAO_BANCO.md`, seções 9.1 e 9.2):

1. **Modo `regressao`:** quando `metodo == 'regressao'` e `modelo_path` aponta para um artefato `.joblib` válido (salvo na pasta do banco, `CAMINHO_BANCO.parent / "modelos_estimativa"`), o pipeline scikit-learn é carregado com cache em memória (`_CACHE_MODELO`) e prevê a quantidade de comungantes a partir de `ocupacao_final`, `minutos_missa`, `dia_semana` e `tipo` da celebração (só não pode ser negativa: a contagem da câmera é um piso do total presente, não um teto).
2. **Modo `coeficiente_fixo` (ou fallback):** enquanto não há modelo de regressão (ou caso o arquivo `.joblib` não possa ser carregado), aplica a proporção direta:

```python
comungantes = int(max(ocupacao, 0) * coeficiente)
hostias     = math.ceil(comungantes * (1 + margem))
```

- **`COEFICIENTE_PADRAO = 0.89`** é a média de `comungantes ÷ contagem da câmera` nas missas boas do `counting_people.csv` (`DOCUMENTACAO_BANCO.md`, seção 9.1). Ele só vale enquanto não houver uma linha em `configuracao_estimativa`, e vale de verdade no `.exe`, que começa com o banco vazio. A margem de hóstias padrão é de 15% (`MARGEM_HOSTIAS_PADRAO`). Rodar `db/calcular_coeficiente_inicial.py` grava os valores calculados no banco.
- **`max(ocupacao, 0)`** protege o começo de um vídeo, quando `dentro` pode ficar negativo (uma saída antes de qualquer entrada).
- O resultado é um objeto `Estimativa` (`comungantes`, `hostias`, `coeficiente`, `configuracao_id`, `margem`), para quem usa escrever `est.hostias` em vez de `resultado[1]`.

**Por que a estimativa precisa ser gravada:** o Histórico lê as colunas de `estimativa_comunhao` pela `vw_historico`. Uma estimativa que só é calculada na hora de exibir o dashboard nunca chega ao banco, e o Histórico mostra estimativa e hóstias zeradas. `registrar_estimativa_da_sessao()` grava `estimativa_calculada`, `hostias_calculadas`, `coeficiente_utilizado` e `configuracao_estimativa_id` para a sessão.

**Gravando as sessões já encerradas:** `preencher_estimativas_pendentes(conexao)` só pega as sessões sem estimativa, então é seguro rodar quantas vezes quiser:

```bash
cd backend
python -c "from db.database import obter_conexao; from integracao.estimativa import preencher_estimativas_pendentes as p; k=obter_conexao(); print(p(k), 'sessoes atualizadas'); k.close()"
```

**Por que em `integracao/`:** é regra de negócio usada pelos dois lados, API e gravação. O arquivo não importa o `motor`, então a API continua rodando sem a `ultralytics`.

---

## 9. Agendamento automático (`integracao/agendador.py`)

Sem `--agora` nem `--fonte`, o `python main.py` não conta na hora: ele sobe o dashboard e **espera os horários da agenda** (`horario_padrao`, tela Configurações). Em cada horário, liga a contagem sozinho e desliga no fim da janela de gravação. É o modo de uso na igreja: ninguém precisa abrir nem fechar nada no dia da missa.

### 9.1 Os dois modos

| Comando | Modo | O que faz |
|---|---|---|
| `python main.py` | **Agendado** | Carrega o `Monitor` uma vez (sem janela), liga o `Agendador` e espera. Mostra no terminal as próximas contagens |
| `python main.py --agora` | **Manual** | Conta imediatamente, com a janela, como antes do agendador (testes e demonstração) |
| `python main.py --fonte videos/x.mp4` | **Manual** | Idem, com outra fonte. Quem aponta um vídeo quer contá-lo agora |

A regra fica numa função só, `cli.modo_manual(args)`: `args.agora or args.fonte is not None`. Assim, os comandos que já existiam (`--fonte ...`) continuam funcionando do mesmo jeito.

No modo agendado, a contagem roda numa thread do APScheduler, e não na thread principal (seção 2). Por isso o `main.py` desliga a janela do OpenCV (`visual.mostrar_janela = False`): no Windows, a janela não funciona direito fora da thread principal. O acompanhamento é pelo dashboard.

### 9.2 Do horário cadastrado até o Histórico

```mermaid
sequenceDiagram
    participant S as APScheduler
    participant A as Agendador
    participant DB as SQLite
    participant V as Vigia (thread)
    participant M as Monitor

    S->>A: domingo 09:45 → _executar_janela(horario_id)
    A->>DB: obter_ou_criar_celebracao("Missa das 10:00", horario_padrao_id, 09:45–11:15)
    A->>DB: sessao_de_monitoramento(..., celebracao_id) abre a sessão
    A->>V: inicia o vigia
    A->>M: executar(ao_atualizar=gravador)
    loop a cada 1 s
        V->>V: já são 11:15?
    end
    V->>M: parar()
    M-->>A: devolve as métricas
    A->>DB: sessão concluída + estimativa gravada (seção 8)
```

1. **Registro.** Ao iniciar (`Agendador.iniciar()`), o `recarregar()` lê os horários ativos e cria, para cada um, uma tarefa semanal no APScheduler (`CronTrigger`), com o id `agenda-{id do horário}`: "todo domingo às 09:45".
2. **Disparo.** No horário de início, o APScheduler chama `_executar_janela(horario_id)`, que confere se a contagem deve mesmo acontecer (seção 9.3) e cria (ou reaproveita) a celebração do dia: título "Missa das 10:00", ligada ao horário pelo `horario_padrao_id` e com o início e o fim de monitoramento. É isso que preenche "Início do monitor" e "Fim do monitor" no Dashboard.
3. **Contagem.** `_contar()` usa exatamente o mesmo `with sessao_de_monitoramento(...)` + `monitor.executar(...)` do modo manual (seção 6), passando o `celebracao_id`. O agendador não reimplementa a contagem: ele só decide **quando** ligar e desligar.
4. **Fim.** Uma segunda thread, o **vigia** (`_parar_no_fim`), confere o relógio a cada segundo e chama `monitor.parar()` no horário de fim. O `executar()` retorna normalmente, a sessão fecha como `concluida` e a estimativa é gravada (seção 8). Se o vídeo acabar antes, a contagem termina antes e o vigia é dispensado.

O `Monitor` é criado **uma vez só**, no `main.py`, e reaproveitado em todas as missas: carregar o modelo YOLO a cada missa seria lento à toa. O `executar()` zera as métricas e o rastreio a cada chamada (`DOCUMENTACAO_MOTOR.md`, seção 14).

### 9.3 Regras que evitam contagem errada

| Situação | O que acontece | Como |
|---|---|---|
| Dia da semana | A missa de domingo dispara no domingo | O banco usa 0 = domingo; o APScheduler, 0 = segunda. O agendador passa o **nome** do dia (`DIAS_CRON = ("sun", "mon", ...)`), e nunca o número |
| Programa ligado **no meio** de uma janela | Começa a contar na hora, atrasado | O cron só dispararia na semana seguinte; o `recarregar()` agenda uma execução imediata (`agora-{id}`) |
| Computador em suspensão no horário de início | Conta ao acordar, se ainda estiver dentro da janela | `misfire_grace_time` igual à duração da janela; o `_executar_janela` confere o fim de novo antes de abrir a câmera |
| Programa ligado **depois** do fim | Não conta | Conferência `inicio <= agora < fim` |
| Janelas sobrepostas | Só a primeira conta; a segunda é ignorada com aviso no terminal | Trava `_ocupado` (`threading.Lock`), tentada com `acquire(blocking=False)` |
| Mesma janela disparada duas vezes no dia (agenda recarregada no meio) | Conta uma vez só | Conjunto `_feitas` de trios `(origem, id, dia)` |
| Celebração marcada como `cancelada` | Não liga a câmera | Conferido antes de contar |
| Erro no motor ou câmera que não volta | Sessão `interrompida`; as próximas missas continuam funcionando | O erro é capturado em `_contar()` e a trava é sempre solta num `finally` |
| `Ctrl+C` no meio da contagem | Sessão `interrompida` (não entra no Histórico) | `encerrar()` marca `_encerrando`, para o motor e espera a sessão ser gravada (`shutdown(wait=True)`); `_contar()` lança `_Encerrado` dentro do `with` |

**Por que o vigia chama `parar()` repetidas vezes.** O `Monitor.executar()` zera o pedido de parada ao começar (`DOCUMENTACAO_MOTOR.md`, seção 14): um `parar()` chamado um instante antes se perderia, e a contagem não pararia mais. Com câmera RTSP fora do ar, o motor fica tentando reconectar e só desiste quando `parar()` é chamado. Repetindo a chamada a cada segundo até a contagem terminar, os dois casos ficam cobertos.

**Por que a trava é solta num lugar só.** Se alguma saída de `_executar_janela` esquecesse de soltar `_ocupado`, nenhuma outra missa seria contada até reiniciar o programa. Depois que a trava é pega, todo caminho (celebração cancelada, contagem normal, erro) passa por um único `finally`.

### 9.4 Agenda alterada pela tela

O `main.py` registra o agendador ligado com `agendador.registrar(...)`. As rotas `POST` e `DELETE /api/configuracoes/agenda` chamam `recarregar_agenda()` depois de gravar no banco (seção 4.6): o `recarregar()` remove as tarefas `agenda-*` e cria de novo a partir da tabela. Um horário cadastrado para agora começa a contar na hora, sem reiniciar o programa.

- **Sem agendador** (modo manual), `recarregar_agenda()` não faz nada.
- **Uma contagem em andamento não é interrompida**: a mudança vale para as próximas.
- **Falhar ao recarregar não vira erro 500**: o horário já foi salvo, e a falha só aparece no terminal.

O `agendador.py` não importa o motor no topo do arquivo: a rota de Configurações importa `recarregar_agenda`, e carregar OpenCV e YOLO só para isso deixaria a API mais pesada. O `sessao_de_monitoramento` é importado dentro de `_contar()`, quando uma contagem de fato começa.

### 9.5 Como foi testado

Com um motor falso (que "conta" sozinho), um relógio falso (para simular "domingo 10:05" a qualquer hora) e um banco temporário, foram verificados: dia da semana certo; ligar no meio da janela, contar e parar sozinho no fim, com a missa no Histórico e a estimativa gravada; a mesma janela não rodar duas vezes; acordar depois do fim; janelas sobrepostas; celebração cancelada; câmera sem nenhum frame; erro no motor; `Ctrl+C` no meio; recarga da agenda; e o modo manual sem mudanças.

Com o vídeo de teste e o programa real: uma janela cadastrada com início já passado começou a contar ao abrir o programa, parou sozinha no horário de fim e entrou no Histórico como "Missa das …" com a estimativa; e um horário cadastrado pela tela, com o programa aberto, começou a contar sem reiniciar.

### 9.6 Celebrações avulsas

Além da agenda semanal, o agendador conta as celebrações cadastradas na tela Celebrações (Natal, Páscoa, casamento, missa de última hora). Antes, uma missa fora da rotina só era contada com `python main.py --agora`, entrando como "Missa (monitoramento automatico)".

| Fonte | Disparo | Quando existe |
|---|---|---|
| Agenda semanal (`horario_padrao`) | `CronTrigger` semanal no horário de início da gravação | Um por horário ativo |
| Celebração avulsa (`celebracao` com `horario_padrao_id` nulo e `status = 'agendada'`) | `DateTrigger` de data única no início da gravação | Uma por celebração, de hoje em diante |

O `recarregar()` lê as duas fontes, e as rotas `/api/celebracoes` e `/api/configuracoes` o chamam depois de cada mudança. A contagem (`_contar`) e a trava de uma contagem por vez são as mesmas. A diferença está em `_executar_celebracao`, que lê a janela da própria celebração, e em `_reservar()`, que marca a janela como feita com a chave `(origem, id, dia)`: a origem (`"agenda"` ou `"celebracao"`) evita colisão entre ids de tabelas diferentes. Se o computador ligar no meio da janela, o disparo já venceu, mas o `misfire_grace_time` é a duração da janela, então ele roda na hora.

**`repetirSemanalmente`:** a celebração criada fica ligada ao horário da agenda (`horario_padrao_id`). Por isso o agendador **não** cria um disparo avulso para ela: quem a conta é o disparo semanal, que encontra a celebração pela chave `(data, horario_missa)` e a reaproveita (`obter_ou_criar_celebracao`), preservando título e tipo.

**Limpeza (`limpar_celebracoes_vencidas`).** Avulsa que passou e **nunca foi contada** é apagada 24 horas depois do fim da gravação, na inicialização (`main.py`) e todo dia às 03:00 no próprio agendador, porque o computador pode ficar ligado por dias.

| Regra | Motivo |
|---|---|
| Só `origem = 'personalizada'` e sem `horario_padrao_id` | As ligadas à agenda semanal não são avulsas |
| Só `agendada` ou `cancelada` | Em andamento e finalizada têm contagem |
| Só sem nenhuma sessão | `sessao_monitoramento` tem `ON DELETE CASCADE`: apagar a celebração apagaria a contagem, e o Histórico lê a celebração |

Missa contada **nunca** é apagada: fica como `finalizada` e alimenta o Histórico.

---

## 10. Limitações conhecidas

| Onde | Limitação | Efeito |
|---|---|---|
| `integracao/agendador.py` | Janela de gravação que passa da meia-noite não é suportada | A tela já recusa: o fim precisa ser depois do início no mesmo dia |
| `integracao/agendador.py` | O agendador só funciona com o programa aberto | O `.exe` se registra para iniciar com o Windows (`DOCUMENTACAO_DISTRIBUICAO.md`), mas com o computador desligado na hora da missa ela não é contada |
| `integracao/agendador.py` | O controle de "uma vez por dia" fica em memória | Reiniciar o programa dentro de uma janela que já foi contada (vídeo que acabou antes do fim) conta de novo, numa segunda sessão da mesma celebração. O Histórico mostra a mais recente |
| `Celebracoes.tsx` | O calendário lista só o que está na tabela `celebracao` | As missas da agenda semanal aparecem ali quando a contagem delas começa (é nesse momento que a celebração é criada); as futuras ainda não são mostradas. Celebrações avulsas aparecem desde o cadastro |

Corrigido: `EstimativaComunhao.tsx` antes calculava as hóstias sugeridas no próprio frontend multiplicando por `1.1` fixo. Agora `GET /api/dashboard` devolve `hostiasSugeridas` diretamente de `calcular_estimativa(db, ocupacao, celebracao).hostias`, garantindo que o Dashboard e o Histórico usem sempre a mesma `margem_hostias` configurada no banco.

---

## 11. Próximos passos previstos

- **Empacotamento (PyInstaller + Inno Setup).** O `.exe` único, o banco em `%APPDATA%`, o início com o Windows e a abertura automática do dashboard já estão no código e estão descritos em [`DOCUMENTACAO_DISTRIBUICAO.md`](./DOCUMENTACAO_DISTRIBUICAO.md). Falta validar o build numa máquina Windows e criar o instalador (Inno Setup).
- **Controle manual da contagem.** Hoje não há botões no dashboard nem rotas na API para iniciar ou encerrar o motor: ele começa pelo `main.py` (na hora, com `--agora`, ou pela agenda) e termina no fim do vídeo ou da janela, por ESC/Q na janela ou por Ctrl+C.
