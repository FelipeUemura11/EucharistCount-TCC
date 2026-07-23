# Backend — Eucharist Count

Módulo de visão computacional para contagem de pessoas em celebrações litúrgicas.

Projetado para rodar **na máquina da paróquia**: CPU comum, sem placa de vídeo,
sem conexão com a nuvem. Nenhuma imagem é armazenada.

---

## Estrutura

```
backend/
├── main.py                  # ponto de entrada do monitoramento
├── config.json              # parâmetros ajustáveis (editável)
├── requirements.txt
│
├── eucharist/               # o módulo em si
│   ├── config.py            # carrega/salva config.json
│   ├── camera.py            # captura: arquivo, webcam ou RTSP
│   ├── detector.py          # YOLO + ByteTrack → lista de Pessoa
│   ├── visual.py            # desenho (só para monitoramento)
│   └── monitor.py           # orquestra o ciclo completo
│
├── scripts/
│   ├── preparar_modelo.py   # baixa e exporta o modelo para ONNX
│   └── calibrar.py          # descobre a melhor configuração pro seu vídeo
│
├── modelos/                 # modelos .onnx (fora do Git)
└── videos/                  # vídeos de teste (fora do Git)
```

Cada módulo tem uma responsabilidade só. `detector.py` não sabe o que é uma
janela; `camera.py` não sabe o que é uma pessoa. Isso mantém o código simples
de entender e permite testar as partes isoladamente.

Nenhum módulo grava imagem ou vídeo em disco. Os frames existem apenas em
memória, durante o processamento, e somem quando o programa termina.

---

## Instalação

Requer **Python 3.11**.

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac

pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu
```

O `--extra-index-url` é importante: sem ele o pip baixa a versão CUDA do
PyTorch (~2.5 GB) que não serve para nada numa máquina sem GPU.

---

## Primeira execução

### 1. Descubra a melhor configuração para o seu vídeo

```bash
python -m scripts.calibrar
```

Testa 27 combinações de modelo/resolução/confiança nos frames do
`videos/cam.mp4` e mede a velocidade **nesta máquina**. Os frames de teste
ficam só em memória durante a execução — nada é salvo em disco.

O script recomenda uma configuração com base em quantidade de detecções
e velocidade.

### 2. Prepare o modelo escolhido

```bash
python -m scripts.preparar_modelo --modelo yolo11n --imgsz 640
```

Exporta para ONNX, que roda 2 a 4× mais rápido em CPU que o `.pt`.

### 3. Ajuste o `config.json` e rode

```bash
python main.py
```

---

## Uso

```bash
# vídeo de teste
python main.py --fonte videos/cam.mp4

# webcam
python main.py --fonte 0

# câmera IP da igreja
python main.py --fonte "rtsp://usuario:senha@192.168.1.50:554/stream1"

# máquina fraca: menor resolução, menos threads, sem janela
python main.py --imgsz 480 --threads 2 --sem-janela
```

**Teclas:** `ESC`/`Q` sair · `ESPAÇO` pausar

A janela apenas exibe o vídeo na tela — nada do que é mostrado é gravado
ou salvo em arquivo.

---

## Ajustando para máquina fraca

Em ordem de impacto:

| Parâmetro | Efeito |
|---|---|
| `fps_processamento: 4.0` | maior ganho, menor perda. Pessoas não andam rápido o bastante para 4 fps ser insuficiente |
| `imgsz: 480` | ~2× mais rápido que 640, mas perde pessoas ao fundo |
| `modelo: yolo11n.onnx` | o mais leve que ainda detecta bem |
| `threads: 2` | limita o uso de CPU e mantém a máquina utilizável |
| `mostrar_janela: false` | desenhar e exibir consome CPU à toa em produção |

Se as pessoas do fundo não forem detectadas, o problema quase sempre é o
`imgsz` baixo demais — não o limiar de confiança.

---

## Parâmetros do `config.json`

**camera**
- `fonte` — arquivo, `"0"` para webcam, ou URL `rtsp://`
- `fps_processamento` — quadros por segundo a analisar (4–8 é suficiente)
- `segundos_reconexao` — espera antes de retentar um stream caído

**deteccao**
- `modelo` — caminho do `.onnx` ou `.pt`
- `imgsz` — resolução de inferência, múltiplo de 32
- `confianca` — limiar (0–1); mais baixo detecta mais e erra mais
- `iou` — remoção de caixas sobrepostas
- `threads` — limite de núcleos; `0` = automático

**filtro** — descarta caixas com geometria improvável para uma pessoa.
Os limites são permissivos de propósito: numa igreja há gente sentada,
de perfil e parcialmente oculta pelos bancos.

---

## Privacidade

O sistema **não possui, em nenhum ponto do código, capacidade de salvar
imagem ou vídeo em disco.** Os frames capturados pela câmera existem
somente em memória (RAM) durante o processamento e são descartados
assim que o próximo frame chega. Isso vale para o monitoramento
(`main.py`) e para a calibração (`scripts/calibrar.py`).

Ao final do processamento, só permanecem números agregados (quantidade
de pessoas, IDs de rastreio) — nunca a imagem em si. Essa é a base técnica
da conformidade com a LGPD descrita no TCC: não há tratamento de dado
pessoal identificável, porque a imagem nunca é persistida.

Vídeos de teste com fiéis reais (como `videos/cam.mp4`) não devem ser
versionados no Git — o `.gitignore` do projeto já bloqueia isso.

---

## Próximas etapas

Ainda não implementados nesta fase:

- [ ] Contagem por cruzamento de linha virtual (entradas/saídas)
- [ ] Persistência em SQLite
- [ ] API FastAPI
- [ ] Agendamento automático com APScheduler
- [ ] Estimativa de comunhão e hóstias
- [ ] Empacotamento com PyInstaller

A classe `Monitor` já foi desenhada para ser controlada externamente
(`iniciar`/`parar`), e `DetectorPessoas` já devolve objetos `Pessoa` com o
ponto `base` (pés) — que será a referência do cruzamento de linha.
