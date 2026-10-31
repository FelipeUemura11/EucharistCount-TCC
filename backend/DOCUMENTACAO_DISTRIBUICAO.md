# Documentação Técnica — Distribuição (.exe)

## Eucharist Count — Backend

Este documento explica **como o sistema vira um único `EucharistCount.exe`** para o computador da paróquia, e por que cada decisão foi tomada. O objetivo: o padre recebe um arquivo, clica, e o dashboard abre — sem instalar Python, sem rodar scripts e sem configurar modelo ou contagem.

| Documento | Cobre |
|---|---|
| [`DOCUMENTACAO_MOTOR.md`](./DOCUMENTACAO_MOTOR.md) | Motor de visão computacional |
| [`DOCUMENTACAO_BANCO.md`](./DOCUMENTACAO_BANCO.md) | Modelo de dados e estimativa de comunhão |
| [`DOCUMENTACAO_API.md`](./DOCUMENTACAO_API.md) | Servidor FastAPI e dashboard ao vivo |
| **`DOCUMENTACAO_DISTRIBUICAO.md`** (este) | Empacotamento em `.exe`, caminhos, início com o Windows |

---

## 1. O que vai dentro do `.exe`

O PyInstaller (`--onefile`) embute o interpretador Python e tudo o que o código **importa**. Arquivos que o código apenas **lê do disco** não são detectados e precisam ser declarados em [`eucharist_count.spec`](./eucharist_count.spec):

| Item | Por que precisa ser declarado | Onde o código o procura |
|---|---|---|
| `frontend/dist` | O React compilado é lido por caminho | `api/frontend.py` (`_MEIPASS/frontend/dist`) |
| `modelos/yolo11n.onnx` | O modelo é aberto pelo caminho do `config.json` | `motor/detector.py` (`RAIZ/modelos`) |
| `config.json` | Padrão de fábrica da contagem e da linha | `motor/config.py` |
| `bytetrack_ajustado.yaml` | Configuração do rastreador | `motor/detector.py` |
| `db/schema.sql` | Criação das tabelas na primeira execução | `db/database.py` |
| Arquivos do Ultralytics | YAMLs internos de configuração e trackers | `collect_data_files("ultralytics")` |

Com o modelo e o `config.json` já calibrados dentro do `.exe`, **o cliente não roda `preparar_modelo.py` nem ajusta a linha**. O `preparar_modelo.py` roda uma vez, na máquina de build.

---

## 2. Onde cada coisa fica em tempo de execução

No modo `--onefile`, o `.exe` se descompacta numa pasta temporária (`_MEI...`) a cada abertura, e ela é apagada ao fechar. Por isso há duas áreas:

| Área | Caminho | Conteúdo | Sobrevive ao fechar? |
|---|---|---|---|
| Recursos (somente leitura) | pasta temporária `_MEI...` (`RAIZ`) | modelo, frontend, `schema.sql`, `config.json` de fábrica | não, é recriada a cada abertura |
| Dados | `%APPDATA%\EucharistCount` (`PASTA_DADOS`) | banco `eucharist_count.db`, `eucharist_count.log`, `config.json` alterado | **sim** |
| Segredos | pasta do `.exe` | `.env` com `CAMERA_FONTE` | sim |

- **Banco:** `db/database.py` passa a usar `%APPDATA%` quando empacotado. Em desenvolvimento nada muda (`backend/db/eucharist_count.db`).
- **Configuração:** o `config.json` embutido é o padrão. Se existir um `config.json` em `%APPDATA%\EucharistCount`, ele tem prioridade — permite ajustar a linha ou a confiança no computador da paróquia sem gerar um novo `.exe`.
- **Câmera:** o `.env` fica ao lado do `.exe` (comportamento que já existia). A URL RTSP leva usuário e senha; usa-se um perfil de **somente leitura**, configurado localmente, e a senha **não é embutida** no `.exe` (um executável pode ser descompactado).

---

## 3. Comportamento sem terminal (`inicializacao.py`)

O build usa `console=False`. Sem terminal, quatro coisas que o `python main.py` dava de graça precisam ser feitas explicitamente. O `main.py` só as aciona quando `EMPACOTADO` (`getattr(sys, "frozen", False)`); em desenvolvimento o comportamento é o de sempre.

| Função | O que resolve | Por quê |
|---|---|---|
| `preparar_saida()` | `print()` e erros vão para `eucharist_count.log` | Sem console, `sys.stdout` é `None` e o `uvicorn` quebra ao configurar o log. O log (limitado a 5 MB, com um arquivo `.antigo` de reserva) também permite diagnosticar problemas na paróquia |
| `adquirir_instancia_unica()` | Impede um segundo programa | Duas instâncias disputariam a porta 8000 e a câmera. A trava é uma porta local (`47653`): o sistema a libera sozinho se o processo morrer, sem arquivo de *lock* para limpar |
| `registrar_inicio_com_windows()` | O programa abre ao ligar o PC | Grava a chave `HKCU\...\Run` com `"<exe>" --boot`. Não exige administrador e é regravada a cada execução, então se o `.exe` mudar de pasta o caminho se corrige |
| `abrir_dashboard()` | Mostra o dashboard sem clique | Espera a porta 8000 responder e chama `webbrowser.open`. Roda em thread, para não atrasar a inicialização |

### 3.1 O argumento `--boot`

Quem inicia o programa define se o navegador abre:

| Como foi aberto | Navegador | Contagem |
|---|---|---|
| O Windows ligou (`--boot`) | **não abre**, ninguém está na frente do PC | segue a agenda sozinha |
| O padre clicou no `.exe` | abre o dashboard | segue a agenda |
| O padre clicou com o programa **já aberto** | abre o dashboard e o segundo processo encerra | não é afetada |

O último caso é a instância única em ação: clicar de novo funciona como "abrir o dashboard".

---

## 4. Como gerar o `.exe`

Na máquina de build (Windows), usando **sempre o mesmo venv**, para manter a versão do Python consistente:

```bash
cd frontend && npm run build && cd ../backend     # 1. dashboard compilado
python -m scripts.preparar_modelo --modelo yolo11n --imgsz 640   # 2. modelo ONNX
pip install pyinstaller
pyinstaller eucharist_count.spec                  # 3. dist/EucharistCount.exe
```

O `modelos/*.onnx` e o `frontend/dist` não estão no Git (são regenerados), então os passos 1 e 2 são obrigatórios antes do 3.

---

## 5. Decisões e justificativas

| Decisão | Justificativa |
|---|---|
| `--onefile` | Um arquivo só para entregar. O custo é descompactar a cada abertura, por isso dados persistentes ficam em `%APPDATA%` |
| `lap==0.5.13` no `requirements.txt` | O ByteTrack do Ultralytics precisa do `lap`. Sem ele, o Ultralytics tenta instalá-lo em tempo de execução, o que não funciona dentro do `.exe` |
| `copy_metadata` no `.spec` | O Ultralytics confere versões de pacotes pelos metadados e, se não os acha, tenta `pip install`. O APScheduler também localiza seus componentes pelos metadados |
| Regressão fora do `.exe` | `sklearn` não é importado pelo `main.py`, então não entra no build. O cliente começa com o coeficiente fixo padrão (0,78) e a estimativa funciona; a regressão depende de treino com dados reais (ver `DOCUMENTACAO_BANCO.md`) |
| Início com o Windows pela chave `Run` | Simples, sem administrador. Alguns antivírus desconfiam de programas que se registram sozinhos; o instalador (Inno Setup) é o caminho mais limpo e fica como evolução |
| Trava por porta, não por arquivo | Libera sozinha em queda de energia e funciona nos dois sistemas |

---

## 6. Limitações conhecidas e validação pendente

- **Não validado em Windows.** O `.spec`, o registro do início automático e o log sem console foram escritos e revisados, mas a primeira geração do `.exe` deve ser testada numa máquina Windows limpa (sem Python).
- **Sem terminal não há `Ctrl+C`.** O programa é encerrado pelo Gerenciador de Tarefas. Uma sessão aberta nesse momento é fechada como `interrompida` na próxima abertura (`fechar_sessoes_presas`). Um ícone na bandeja com a opção "Sair" resolveria.
- **Tamanho.** O Ultralytics importa o `torch` (cerca de 700 MB instalado), o que deixa o `.exe` grande e a abertura mais lenta.
- **Apenas CPU.** A inferência usa o `onnxruntime` comum, o que atende a máquina da paróquia (só processador).

## 7. Trabalhos futuros

- **Instalador (Inno Setup).** Cria o atalho de inicialização de forma mais limpa que a chave `Run` e é o caminho para distribuição ampla. Com build único, não precisa de seleção CPU/GPU.
- **Hardware amplo (AMD, NVIDIA, Intel).** Trocar para `onnxruntime-directml` com `providers=["DmlExecutionProvider", "CPUExecutionProvider"]`. O Ultralytics monta os providers sozinho (só CPU/CUDA) e não aceita o DirectML; seria preciso rodar `onnxruntime.InferenceSession` direto no `DetectorPessoas`. Os pacotes `onnxruntime`, `onnxruntime-gpu` e `onnxruntime-directml` conflitam no mesmo venv, e o desempenho do DirectML deve ser medido em placas NVIDIA, AMD e no fallback para CPU.
- **Nuitka.** Alternativa ao PyInstaller (gera executável nativo, costuma causar menos alertas de antivírus); avaliar junto do instalador.
- **Acesso remoto seguro.** Login e senha, ou hospedagem na nuvem. Hoje a API escuta só em `127.0.0.1`, sem autenticação — expor a porta exige autenticação antes.
