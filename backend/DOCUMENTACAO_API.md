# Documentação Técnica — API e Integração

## Eucharist Count — Backend

Este documento explica **como as peças do backend foram ligadas**: o servidor FastAPI que alimenta o dashboard, a ponte que leva os números do motor de visão até o banco, e o caminho que uma pessoa cruzando o portão percorre até aparecer na tela.

| Documento | Cobre |
|---|---|
| [`DOCUMENTACAO_MOTOR.md`](./DOCUMENTACAO_MOTOR.md) | Motor de visão computacional: câmera, detecção, rastreio e contagem |
| [`DOCUMENTACAO_BANCO.md`](./DOCUMENTACAO_BANCO.md) | Modelo de dados, camada de acesso e estimativa de comunhão |
| **`DOCUMENTACAO_API.md`** (este) | Servidor FastAPI, ligação motor → banco e dashboard ao vivo |

---

## 1. Onde está cada coisa

O código deste documento está dividido por responsabilidade: cada arquivo resolve um problema, e o `main.py` só liga as peças na ordem certa.

```
backend/
├── main.py                 # orquestra: argumentos → banco → API → motor
├── cli.py                  # argumentos de linha de comando → Config
├── integracao/             # ponte motor ↔ banco (não é API nem motor)
│   ├── sessao.py           # GravadorSessao, abrir/fechar sessão, sessões presas
│   └── estimativa.py       # estimativa de comunhão e hóstias
└── api/                    # servidor web
    ├── app.py              # criar_app(): monta o FastAPI
    ├── servidor.py         # sobe o uvicorn numa thread
    ├── dependencias.py     # obter_db: uma conexão por requisição
    ├── schemas.py          # modelos Pydantic (contrato com o frontend)
    ├── formatacao.py       # datas, hora local, dia da semana, status
    ├── frontend.py         # serve o React compilado (catch-all)
    └── rotas/              # uma rota por tela do frontend
        ├── status.py
        ├── dashboard.py
        ├── celebracoes.py
        └── historico.py
```

| Pasta | Responsabilidade | Depende de |
|---|---|---|
| `api/` | Responder requisições HTTP | `db/`, `integracao/estimativa.py`. **Não importa o `motor`**: a API inteira roda sem a `ultralytics` instalada |
| `integracao/` | Transformar o que o motor vê em linhas no banco | `db/`, `motor/` |
| `motor/` | Visão computacional | Nada do resto: não sabe que banco e API existem (`DOCUMENTACAO_MOTOR.md`, seção 13) |
| `db/` | Acesso ao SQLite | Nada do resto |

**Por que `integracao/` fica fora de `api/`:** o `GravadorSessao` não responde requisições; ele liga o motor ao banco. Separado, ele continua útil mesmo sem servidor web, que é o caso do agendamento automático previsto (seção 9), contando sem dashboard aberto.

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
| 2 | Lê o `config.json` e aplica os argumentos | `cli.py` | O `config.json` define o padrão; os argumentos sobrescrevem só naquela execução |
| 3 | `inicializar_banco()` | `db/database.py` | Cria as tabelas que ainda não existirem (`DOCUMENTACAO_BANCO.md`, seção 6.1) |
| 4 | `fechar_sessoes_presas()` | `integracao/sessao.py` | Fecha como `interrompida` sessões de execuções anteriores que não terminaram (seção 6.6) |
| 5 | `iniciar_em_background(criar_app())` | `api/` | O dashboard fica no ar antes do motor começar |
| 6 | `Monitor(config, RAIZ)` | `motor/` | Carrega o modelo YOLO. **Vem antes de abrir a sessão** (seção 6.5) |
| 7 | `with sessao_de_monitoramento(...)` + `monitor.executar(...)` | `integracao/sessao.py` | Abre a sessão, conta até o vídeo acabar e fecha a sessão, aconteça o que acontecer |
| 8 | Imprime o resumo | `main.py` | Entradas, saídas, dentro e FPS médio no terminal, quando o vídeo acaba |
| 9 | `while True: time.sleep(1)` | `main.py` | Mantém o dashboard no ar até o Ctrl+C (seção 2.1) |

Se o modelo não existir (`FileNotFoundError`) ou a fonte de vídeo não abrir (`RuntimeError`), o programa imprime o erro e sai com código 1. O Ctrl+C, a qualquer momento, encerra com código 0.

### 3.1 Argumentos de linha de comando (`cli.py`)

| Argumento | Sobrescreve | Exemplo |
|---|---|---|
| `--fonte` | `camera.fonte` | `--fonte videos/20-09-teste.mp4` |
| `--modelo` | `deteccao.modelo` | `--modelo modelos/yolo11s_dyn.onnx` |
| `--imgsz` | `deteccao.imgsz` | `--imgsz 640` |
| `--conf` | `deteccao.confianca` | `--conf 0.25` |
| `--fps` | `camera.fps_processamento` | `--fps 5` |
| `--threads` | `deteccao.threads` | `--threads 2` |
| `--linha` | `contagem.linha` | `--linha 0.25,0.0,0.25,1.0` |
| `--sem-janela` | `visual.mostrar_janela = false` | produção, sem interface gráfica |

Os argumentos numéricos são testados com `is not None`, e não com `if valor:`. Isso porque em Python `0` é falso: o teste antigo ignorava um `--threads 0` digitado de propósito. O `argparse` usa `None` para "não informado", e é exatamente isso que o teste verifica.

A configuração efetiva, já com os argumentos aplicados, fica gravada em `sessao_monitoramento.parametros_contagem`.

---

## 4. Os endpoints

| Método e rota | Arquivo | Devolve | Usado por |
|---|---|---|---|
| `GET /api/status` | `rotas/status.py` | Se há contagem ativa | Selo "Contagem ativa" no topo das páginas (a cada 5 s) |
| `GET /api/dashboard` | `rotas/dashboard.py` | Métricas, gráfico e resumo da missa atual ou da última | Página Dashboard (a cada 2 s) |
| `GET /api/celebracoes` | `rotas/celebracoes.py` | Celebrações do mês corrente | Ainda não usado (a página Celebrações usa dados fixos) |
| `GET /api/historico` | `rotas/historico.py` | Missas encerradas, com os resultados | Página Histórico |
| `GET /api/configuracoes` | `rotas/configuracoes.py` | Agenda padrão, dados da câmera e saúde dos serviços | Página Configurações |
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
    app.add_middleware(CORSMiddleware, ...)

    for rotas in (status, dashboard, celebracoes, historico, configuracoes):
        app.include_router(rotas.router, prefix="/api")

    # POR ULTIMO: o catch-all aceita qualquer caminho.
    app.include_router(frontend.router)
    return app
```

- **Um arquivo por tela.** A divisão espelha as páginas do React: se o Histórico mostrar algo errado, a rota está em `historico.py` e em mais nenhum lugar.
- **A ordem importa.** O FastAPI testa as rotas na ordem em que foram registradas, e a rota do frontend aceita qualquer caminho. Se ela viesse antes, capturaria também as chamadas da API.
- **`criar_app()` é uma *app factory*.** Em vez de uma variável global `app`, é uma função que monta um app novo a cada chamada. Um teste pode criar o seu app sem importar o `main.py`, o que evita carregar o YOLO e subir o motor.

As respostas são descritas pelos **modelos Pydantic** de `api/schemas.py` (`DadosDashboard`, `Celebracao`, `RegistroHistorico`…). Eles espelham, campo a campo e com os mesmos nomes em português e *camelCase*, as interfaces TypeScript de `frontend/src/types/`. O FastAPI usa esses modelos para validar a saída: um campo com o tipo errado dá erro no servidor, e não vira um bug silencioso na tela.

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

Exemplo, com uma contagem em andamento:

```json
{
  "metricas": {
    "ocupacaoAtual": 42,
    "estimativaComunhao": 32,
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
| `estimativaComunhao` | `calcular_estimativa(db, ocupação).comungantes` (seção 8) | Junto com a ocupação |
| `contagemAtiva` | `sessao["status"] == "em_andamento"` | `false` quando mostra a última missa encerrada |
| `graficoOcupacao[]` | `instantaneo_ocupacao`: `hora` = `hora_de_timestamp(registrado_em)`, `ocupacao` = `ocupacao_atual` | A cada 5 s de vídeo |
| `resumoCelebracao` | Título e janela de monitoramento da celebração | — |

Três detalhes:

- **A ocupação atual vem da sessão, e não do último ponto do gráfico.** A sessão é atualizada no instante em que alguém cruza a linha; o gráfico, só a cada 5 segundos de vídeo. Ler do gráfico deixaria o número principal até 5 segundos atrasado em relação aos cartões de entradas e saídas.
- **A API manda só os valores do resumo.** Ícones e rótulos ficam fixos em `ResumoDaCelebracao.tsx`. O rótulo da primeira linha muda com `contagemAtiva` ("Missa atual" durante a contagem, "Última missa" depois), e a linha "Pessoas presentes" usa `metricas.ocupacaoAtual`.
- **Celebração inexistente não derruba a rota.** Se a sessão apontar para uma celebração removida, título e horários saem como "Desconhecido" e vazios, em vez de lançar `TypeError`.

Sem nenhuma sessão (nem ativa, nem encerrada), a rota devolve o mesmo formato, zerado, com o gráfico vazio e `resumoCelebracao: null`. O frontend mostra "Nenhuma missa registrada ainda." no lugar do resumo.

### 4.4 `GET /api/celebracoes`

Lista as celebrações do **mês atual** (`crud.listar_celebracoes_do_mes`, que filtra por `data LIKE 'AAAA-MM%'`).

| Campo | Origem |
|---|---|
| `id`, `titulo` | `celebracao.id`, `titulo` |
| `dia`, `diaSemana` | Derivados de `celebracao.data` (`dia_do_mes`, `formatar_dia_semana`) |
| `horarioMissa`, `inicioMonitoramento`, `fimMonitoramento` | `horario_missa`, `horario_inicio/fim_monitoramento` |
| `pessoasEsperadas`, `capacidade` | `pessoas_esperadas`, `capacidade` (`0` se vazios) |
| `status` | `celebracao.status`, sem conversão: `agendada`, `em_andamento`, `finalizada` ou `cancelada` |

### 4.5 `GET /api/historico`

Lê a view `vw_historico` (`DOCUMENTACAO_BANCO.md`, seção 3.8): só sessões `concluida`, de celebrações `finalizada`, da data mais recente para a mais antiga.

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
| `GET /api/configuracoes` | `agendaPadrao`: horários ativos, por dia e hora. `infoCamera`: fonte (do `.env`), `imgsz` e FPS (do `config.json`) lidos por `Config.carregar()`, resolvidos pela raiz do backend. Sem `CAMERA_FONTE`, a fonte aparece como "Não definida". A senha de uma URL RTSP sai mascarada (`mascarar_senha`: `rtsp://usuario:***@...`) |
| `POST /api/configuracoes/agenda` | Recebe `diaSemana` (0 = domingo a 6), `horarioMissa`, `inicioGravacao` e `fimGravacao` (`HH:MM`). Fora do formato, ou com o fim antes do início, responde **422** |
| `DELETE /api/configuracoes/agenda/{id}` | *Soft delete* (`ativo = 0`): celebrações geradas pelo horário mantêm a referência. **404** se não houver horário ativo com o `id` |

A agenda ainda **não dispara o monitoramento**: isso depende do APScheduler (seção 9).

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
- **A checagem do passo 2 fecha um *path traversal*.** Antes, o caminho era só `dist / catchall`. O uvicorn decodifica `%2e%2e` para `..`, então `GET /%2e%2e/%2e%2e/backend/config.json` devolvia o `config.json`, e o mesmo valia para o banco e o `.env`. Como o servidor escuta em `0.0.0.0`, qualquer máquina da rede da paróquia conseguia baixar esses arquivos. Agora esse caminho cai no passo 4.
- **O passo 4 faz as rotas do React funcionarem ao recarregar a página.** `/historico` não é um arquivo, e sim uma tela que o React desenha no navegador; sem essa regra, apertar F5 em `/historico` daria 404.

**O frontend precisa estar compilado.** O servidor entrega a pasta `dist/`, e não o código-fonte React. Mudanças no frontend só aparecem em `:8000` depois de `npm run build` na pasta `frontend`. Durante o desenvolvimento, `npm run dev` serve o frontend com recarga automática na porta 5173, consumindo a API em `:8000`.

**Onde fica `dist/`:**
- **em desenvolvimento:** em `frontend/dist`, calculado como `RAIZ.parent / "frontend" / "dist"`. O `RAIZ` vem de `motor/config.py` e aponta para `backend/`. O caminho não depende de onde o `frontend.py` está: um `Path(__file__).parent.parent` mudaria de significado se o arquivo trocasse de pasta, que foi exatamente o que aconteceu na reorganização;
- **no executável do PyInstaller:** os arquivos são extraídos numa pasta temporária indicada por `sys._MEIPASS`, e o `getattr(sys, "frozen", False)` escolhe entre os dois casos.

**CORS:** em desenvolvimento, o frontend (`:5173`) e a API (`:8000`) estão em portas diferentes, o que o navegador trata como origens diferentes e bloqueia por padrão. O `CORSMiddleware` com `allow_origins=["*"]` libera. Quando o dashboard é servido pela própria porta 8000, tudo vem da mesma origem e o CORS nem entra em jogo.

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
- **Concluída ou interrompida.** Se o bloco termina normalmente (fim do vídeo, ESC), a sessão fecha como `concluida`. Se termina por exceção (a fonte não abriu, um erro no motor, Ctrl+C), o `except` anota `interrompida` e relança a exceção, para o `main.py` ainda mostrar a mensagem. O `BaseException` é necessário porque o `KeyboardInterrupt` do Ctrl+C não herda de `Exception`. Só sessões `concluida` entram no Histórico, então uma contagem que falhou não aparece lá como resultado válido com zeros.
- **Uma conexão para a missa inteira.** O gravador usa a mesma conexão durante toda a sessão, ao contrário da API, que abre uma por requisição (`DOCUMENTACAO_BANCO.md`, seção 7.5).

**Qual celebração é usada:** enquanto o agendamento automático não existe (seção 9), a celebração é criada na hora, com a data e o horário em que o programa foi iniciado e o título "Missa (monitoramento automatico)". Reiniciar no mesmo minuto reaproveita a celebração (`obter_ou_criar_celebracao`) e cria uma segunda sessão nela.

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
    Zerado --> AoVivo : main.py abre a sessão
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

O frontend busca `/api/dashboard` a cada 2 segundos (`frontend/src/hooks/useDashboard.ts`, constante `INTERVALO_ATUALIZACAO_MS`). O selo de status no topo das páginas faz o mesmo com `/api/status`, a cada 5 segundos.

A alternativa seria o servidor **empurrar** os dados para o navegador, por WebSocket ou *Server-Sent Events*. A consulta repetida foi escolhida porque, neste cenário, as vantagens do *push* não compensam a complexidade:

- **A carga é irrelevante.** Há um navegador, na mesma máquina, fazendo uma consulta leve a cada 2 segundos.
- **Recuperação automática.** Se a API cair e voltar, a próxima consulta simplesmente funciona. Com WebSocket, seria preciso programar a detecção da queda e a reconexão.
- **2 segundos já parece instantâneo** para um painel de ocupação. Se for preciso mais rápido, basta mudar a constante.
- **O banco continua sendo a única interface.** Com *push*, a API teria que ser avisada pelo motor de cada mudança, o que acoplaria as duas threads.

Se a API não responder, o hook **mantém na tela os últimos dados recebidos** e tenta de novo no ciclo seguinte. Antes da primeira resposta, o Dashboard mostra tudo zerado e o Histórico, uma lista vazia. Os estados iniciais dos dois hooks (`useDashboard`, `useHistorico`) foram trocados de dados de demonstração para valores vazios justamente para que números fictícios nunca apareçam como se fossem uma contagem real.

---

## 8. A estimativa de comunhão (`integracao/estimativa.py`)

A estimativa é calculada **num lugar só**. O arquivo tem três funções:

| Função | O que faz | Quem chama hoje |
|---|---|---|
| `calcular_estimativa(conexao, ocupacao)` | Calcula comungantes e hóstias | `api/rotas/dashboard.py`, a cada consulta |
| `registrar_estimativa_da_sessao(conexao, sessao_id, ocupacao)` | Calcula e **grava** em `estimativa_comunhao`, de onde o Histórico lê | `preencher_estimativas_pendentes` |
| `preencher_estimativas_pendentes(conexao)` | Grava a estimativa de toda sessão concluída que ainda não tem uma | Rodada manualmente (comando abaixo) |

Se o dashboard e o histórico tivessem cada um a sua cópia da conta, bastaria alguém mudar uma delas para os dois mostrarem números diferentes. Com uma função só, os dois sempre concordam.

A regra (fórmula de `DOCUMENTACAO_BANCO.md`, seção 9.1):

```python
config = crud.obter_configuracao_estimativa_vigente(conexao)
coeficiente = config["coeficiente_comunhao"] if config else COEFICIENTE_PADRAO    # 0.78
margem      = config["margem_hostias"]       if config else MARGEM_HOSTIAS_PADRAO  # 0.10

comungantes = int(max(ocupacao, 0) * coeficiente)
hostias     = math.ceil(comungantes * (1 + margem))
```

- **`COEFICIENTE_PADRAO = 0.78`** é a média das 3 celebrações reais do `counting_people.csv` (17/22, 177/214, 250/340). Ele só vale enquanto não houver uma linha em `configuracao_estimativa`; na instalação, rodar `db/calcular_coeficiente_inicial.py` grava o valor real no banco. O padrão anterior era `0.4`, que estimava metade do observado: um número plausível e errado.
- **`max(ocupacao, 0)`** protege o começo de um vídeo, quando `dentro` pode ficar negativo (uma saída antes de qualquer entrada).
- O resultado é um objeto `Estimativa` (`comungantes`, `hostias`, `coeficiente`, `configuracao_id`), para quem usa escrever `est.hostias` em vez de `resultado[1]`.

**Por que a estimativa precisa ser gravada:** o Histórico lê as colunas de `estimativa_comunhao` pela `vw_historico`. Uma estimativa que só é calculada na hora de exibir o dashboard nunca chega ao banco, e o Histórico mostra estimativa e hóstias zeradas. `registrar_estimativa_da_sessao()` grava `estimativa_calculada`, `hostias_calculadas`, `coeficiente_utilizado` e `configuracao_estimativa_id` para a sessão.

**Gravando as sessões já encerradas:** `preencher_estimativas_pendentes(conexao)` só pega as sessões sem estimativa, então é seguro rodar quantas vezes quiser:

```bash
cd backend
python -c "from db.database import obter_conexao; from integracao.estimativa import preencher_estimativas_pendentes as p; k=obter_conexao(); print(p(k), 'sessoes atualizadas'); k.close()"
```

**Por que em `integracao/`:** é regra de negócio usada pelos dois lados, API e gravação. O arquivo não importa o `motor`, então a API continua rodando sem a `ultralytics`.

O modelo de regressão (`metodo = 'regressao'`, com o arquivo `.joblib`) ainda não é carregado aqui: a função sempre usa o coeficiente. Ver seção 10.

---

## 9. Próximos passos previstos

- **Agendamento automático (APScheduler).** Iniciar o monitoramento sozinho no horário de cada missa, sem janela (`--sem-janela`), usando o mesmo `with sessao_de_monitoramento(...)` + `monitor.executar(...)`. Com ele, a celebração deixaria de ser criada na hora (seção 6.5) e passaria a vir da agenda (`horario_padrao`). O `Monitor.parar()` já existe para encerrar a contagem no fim da janela.
- **Empacotamento (PyInstaller).** O código já prevê o executável: `freeze_support()` e a resolução de caminhos por `sys._MEIPASS`.
- **Botões de iniciar e encerrar contagem.** Existem no dashboard, mas hoje só escrevem no console do navegador. Não há rotas na API para controlar o motor.

---

## 10. Limitações conhecidas

| Onde | Limitação | Efeito |
|---|---|---|
| `integracao/sessao.py` | O fechamento da sessão não chama `registrar_estimativa_da_sessao` | **Toda contagem nova entra no Histórico com estimativa e hóstias 0**, até alguém rodar `preencher_estimativas_pendentes` (seção 8). Correção: no `finally` de `sessao_de_monitoramento`, depois do `finalizar_sessao`, chamar `registrar_estimativa_da_sessao(conexao, sessao_id, m.dentro)` quando `status == "concluida"` |
| `cli.py` | `aplicar_argumentos` não trata `--fonte` nem `--modelo`, e repete `--conf`/`--threads` com o teste antigo (`if valor:`) | **`--fonte` e `--modelo` são ignorados**: o programa usa o que está no `config.json`. Correção: `if args.fonte: config.camera.fonte = args.fonte` e `if args.modelo: config.deteccao.modelo = args.modelo`, e apagar as duas linhas repetidas |
| `crud.obter_historico` | Ordena só por `data DESC` | Missas do mesmo dia aparecem em ordem arbitrária no Histórico. Correção: `ORDER BY data DESC, horario_missa DESC` |
| `vw_historico` | Junta **todas** as sessões concluídas da celebração | Uma missa com monitoramento reiniciado aparece duas vezes no Histórico |
| `integracao/estimativa.py` | Sempre usa o coeficiente, mesmo com `metodo = 'regressao'` | O modelo treinado por `treinar_regressao.py` ainda não é usado |
| `EstimativaComunhao.tsx` | O frontend calcula as hóstias do dashboard com `× 1,1` fixo | Se a `margem_hostias` do banco mudar, o dashboard e o Histórico sugerem números diferentes. A rota do dashboard poderia enviar as hóstias já calculadas |
| `useHistorico.ts` | Busca o histórico uma vez só, ao abrir a página | Uma missa que termina com a página aberta só aparece ao recarregar |
| `api/servidor.py` | Escuta em `0.0.0.0` | O dashboard fica acessível para qualquer máquina da rede da paróquia, sem autenticação. Para uso só local, `host="127.0.0.1"` |
| Frontend | Os *services* chamam `http://127.0.0.1:8000` com endereço fixo | Abrir o dashboard de outra máquina da rede não funciona. Endereços relativos (`/api/...`) resolveriam |
