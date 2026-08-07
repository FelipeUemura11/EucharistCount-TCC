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
├── motor/                   # Motor de Visão Computacional (OpenCV + YOLO + ByteTrack)
│   ├── config.py            # carrega/salva config.json
│   ├── camera.py            # captura: arquivo, webcam ou RTSP
│   ├── detector.py          # YOLO + ByteTrack + ROI → lista de Pessoa
│   ├── contador.py          # contagem por cruzamento de linha virtual
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

Testa combinações de modelo/resolução/confiança nos frames do
`videos/cam.mp4` e mede a velocidade **nesta máquina**. Os frames de teste
ficam só em memória durante a execução — nada é salvo em disco.

O script recomenda uma configuração com base em quantidade de detecções
e velocidade.

### 2. Prepare o modelo escolhido

```bash
python -m scripts.preparar_modelo --modelo yolo11n --imgsz 640
```

Exporta para ONNX, que roda 2 a 4× mais rápido em CPU que o `.pt`.

### 3. Posicione a linha de contagem e a ROI, e rode

```bash
python main.py
```

Ajuste `contagem.linha_base` e `deteccao.roi` no `config.json` até a linha
e a área analisada (destacada em ciano na janela) ficarem sobre o portão.

---

## Uso

```bash
# vídeo de teste
python main.py --fonte videos/cam.mp4

# câmera IP da igreja
python main.py --fonte "rtsp://usuario:senha@192.168.1.50:554/stream1"

# ajustar a linha do portao (x1,y1,x2,y2 em fracoes do frame)
python main.py --linha 0.96,0.20,0.88,0.99

# ajustar a area analisada (ROI)
python main.py --roi 0.50,0.05,1.0,1.0

# se entrada/saida estiverem trocadas
python main.py --inverter-sentido

# maquina fraca: menor resolucao, menos threads, sem janela
python main.py --imgsz 480 --threads 2 --sem-janela
```

**Teclas:** `ESC`/`Q` sair · `ESPAÇO` pausar

A janela apenas exibe o vídeo na tela — nada do que é mostrado é gravado
ou salvo em arquivo.

---

## Como funciona a contagem

Uma **linha virtual** é posicionada sobre o portão de acesso, definida por
dois pontos (`linha_base`), podendo ter qualquer inclinação — o que
acomoda câmeras em posição diagonal. A partir dela, o sistema gera linhas
paralelas equidistantes (`numero_linhas`, `espacamento`); a pessoa só é
contada ao cruzar pelo menos `linhas_necessarias` delas no mesmo sentido,
o que evita contagem falsa por tremor da caixa delimitadora.

Antes da inferência, o frame é recortado pela **ROI** (`deteccao.roi`):
só a área próxima ao portão é analisada. Isso ignora quem está longe,
melhora a separação entre pessoas próximas (mais pixels por indivíduo) e
reduz o custo de CPU. A ROI precisa incluir espaço dos dois lados da
linha de contagem — senão o sistema não consegue observar a pessoa antes
e depois da travessia.

O rastreamento usa ByteTrack via Ultralytics, garantindo que cada pessoa
mantenha um ID único entre frames — sem isso, a mesma pessoa detectada
em vários quadros poderia ser contada mais de uma vez.

---

## Ajustando para máquina fraca

Em ordem de impacto:

| Parâmetro | Efeito |
|---|---|
| `fps_processamento` | maior ganho, menor perda. Pessoas não andam rápido o bastante para poucos fps ser insuficiente |
| `roi` | recortar a área analisada reduz proporcionalmente o custo de CPU |
| `imgsz: 480` | mais rápido que 640/960, mas perde pessoas ao fundo |
| `modelo: yolo11n.onnx` | o mais leve que ainda detecta bem |
| `threads` | limita o uso de CPU e mantém a máquina utilizável |
| `mostrar_janela: false` | desenhar e exibir consome CPU à toa em produção |

Se as pessoas do fundo não forem detectadas, o problema quase sempre é o
`imgsz` baixo demais — não o limiar de confiança.

---

## Parâmetros do `config.json`

**camera**
- `fonte` — arquivo, `"0"` para webcam, ou URL `rtsp://`
- `fps_processamento` — quadros por segundo a analisar
- `segundos_reconexao` — espera antes de retentar um stream caído

**deteccao**
- `modelo` — caminho do `.onnx` ou `.pt`
- `imgsz` — resolução de inferência, múltiplo de 32
- `confianca` — limiar (0–1); mais baixo detecta mais e erra mais
- `iou` — limiar do NMS; baixo demais funde pessoas próximas numa caixa só
- `threads` — limite de núcleos; `0` = automático
- `roi_ativo` / `roi` — região analisada, em frações do frame (x1,y1,x2,y2)

**filtro** — descarta caixas com geometria improvável para uma pessoa.
Os limites são permissivos de propósito: numa igreja há gente sentada,
de perfil e parcialmente oculta pelos bancos.

**contagem**
- `linha_base` — dois pontos (x1,y1,x2,y2) definindo a linha sobre o portão
- `numero_linhas` / `espacamento` — linhas paralelas geradas a partir da base
- `linhas_necessarias` — quantas precisam ser cruzadas para confirmar
- `lado_entrada` — `-1` ou `1`; define qual lado da linha é "entrada"
- `segundos_janela` / `segundos_cooldown` / `segundos_esquecer` — controle
  temporal da travessia, contado no tempo do vídeo (não da CPU)

---

## Privacidade

O sistema **não possui, em nenhum ponto do código, capacidade de salvar
imagem ou vídeo em disco.** Os frames capturados pela câmera existem
somente em memória (RAM) durante o processamento e são descartados
assim que o próximo frame chega. Isso vale para o monitoramento
(`main.py`) e para a calibração (`scripts/calibrar.py`).

Ao final do processamento, só permanecem números agregados (entradas,
saídas, ocupação) — nunca a imagem em si. Essa é a base técnica da
conformidade com a LGPD descrita no TCC: não há tratamento de dado
pessoal identificável, porque a imagem nunca é persistida.

Vídeos de teste com fiéis reais (como `videos/cam.mp4`) não devem ser
versionados no Git — o `.gitignore` do projeto já bloqueia isso.

---

## Próximas etapas (TCC II)

Ainda não implementados nesta fase:

- [ ] Persistência em SQLite
- [ ] API FastAPI
- [ ] Agendamento automático com APScheduler
- [ ] Estimativa de comunhão e hóstias sugeridas
- [ ] Dashboard web (React)
- [ ] Empacotamento com PyInstaller

A classe `Monitor` já foi desenhada para ser controlada externamente
(`executar`/`parar`), pronta para ser orquestrada pela API e pelo
APScheduler sem refatoração.
