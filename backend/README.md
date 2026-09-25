# Backend — Eucharist Count

Módulo de visão computacional para contagem de pessoas em celebrações litúrgicas.

Projetado para rodar **na máquina da paróquia**: CPU comum, sem placa de vídeo,
sem conexão com a nuvem. Nenhuma imagem é armazenada.

---

## Estrutura

```
backend/
├── main.py                  # ponto de entrada: motor + API + dashboard
├── gerar_dados.py           # popula o banco com dados de demonstração
├── config.json              # parâmetros ajustáveis (editável)
├── bytetrack_ajustado.yaml  # tracker ajustado para esta cena
├── counting_people.csv      # contagem manual de referência (validação)
├── requirements.txt
│
├── DOCUMENTACAO_MOTOR.md    # o porquê de cada decisão do motor
├── DOCUMENTACAO_BANCO.md    # modelo de dados, com diagramas das tabelas
├── DOCUMENTACAO_API.md      # API, ligação motor → banco, dashboard ao vivo
│
├── motor/                   # Motor de Visão Computacional (OpenCV + YOLO + ByteTrack)
│   ├── config.py            # carrega o config.json
│   ├── camera.py            # captura: arquivo, webcam ou RTSP
│   ├── detector.py          # YOLO + ByteTrack → lista de Pessoa
│   ├── contador.py          # contagem por cruzamento de linha virtual
│   ├── visual.py            # desenho (só para monitoramento)
│   └── monitor.py           # orquestra o ciclo completo
│
├── db/                      # persistência SQLite — ver db/README.md
│
├── scripts/
│   ├── preparar_modelo.py   # baixa e exporta o modelo para ONNX
│   ├── calibrar.py          # descobre a melhor configuração pro seu vídeo
│   └── calibrar_linha.py    # marca a linha de contagem por clique
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
`videos/20-09-teste.mp4` e mede a velocidade **nesta máquina**. Os frames de teste
ficam só em memória durante a execução — nada é salvo em disco.

O script recomenda uma configuração com base em quantidade de detecções
e velocidade.

### 2. Prepare o modelo escolhido

```bash
python -m scripts.preparar_modelo --modelo yolo11n --imgsz 640
```

Exporta para ONNX, que roda 2 a 4× mais rápido em CPU que o `.pt`.

### 3. Posicione a linha de contagem e rode

```bash
python -m scripts.calibrar_linha     # opcional: clique os 2 pontos da linha
python main.py
```

Ajuste `contagem.linha` no `config.json` até a linha amarela ficar sobre
o portão. A seta verde **ENTRA** aponta para a esquerda e a vermelha
**SAI** para a direita. As duas linhas cinzas ao redor delimitam a zona
morta (`margem`): quem fica entre elas ainda não foi contado.

O `scripts.calibrar_linha` evita editar as coordenadas no escuro: ele
pausa o vídeo, você clica os dois pontos sobre o portão e ele imprime a
tupla pronta para colar no `config.json`.

---

## Uso

```bash
# vídeo de teste
python main.py --fonte videos/20-09-teste.mp4

# câmera IP da igreja
python main.py --fonte "rtsp://usuario:senha@192.168.1.50:554/stream1"

# ajustar a linha do portao (x1,y1,x2,y2 em fracoes do frame)
python main.py --linha 0.25,0.0,0.25,1.0

# maquina fraca: menor resolucao, menos threads, sem janela
python main.py --imgsz 480 --threads 2 --sem-janela
```

**Teclas:** `ESC`/`Q` sair · `ESPAÇO` pausar

A janela apenas exibe o vídeo na tela — nada do que é mostrado é gravado
ou salvo em arquivo.

---

## Como funciona a contagem

Uma **linha virtual** é posicionada sobre o portão de acesso, definida
por dois pontos (`linha`), podendo ter qualquer inclinação — o que
acomoda câmeras em posição diagonal.

A cada frame o sistema calcula a **distância com sinal** entre os pés de
cada pessoa e essa linha: o sinal diz de que lado ela está, o módulo diz
a quantos pixels. Quando o lado muda, conta-se uma entrada ou uma saída.

Em volta da linha existe uma **zona morta** de `margem` pixels para cada
lado, onde nenhum lado é decidido. É ela que impede o tremor natural da
caixa delimitadora — o YOLO nunca desenha a caixa no mesmo pixel dois
frames seguidos — de virar entrada e saída falsas para alguém parado em
cima da linha. A travessia da faixa não precisa acontecer num único
frame: a pessoa pode levar o tempo que for.

O sentido é fixo: a câmera é definitiva e o portão fica no canto esquerdo
do quadro, então quem passa da **direita para a esquerda entra** e quem
vai da **esquerda para a direita sai**.

O rastreamento usa ByteTrack via Ultralytics, garantindo que cada pessoa
mantenha um ID único entre frames — sem isso, a mesma pessoa detectada
em vários quadros poderia ser contada mais de uma vez.

### Se estiver contando de menos

O erro mais comum não é a linha estar no lugar errado — é ela estar
**perto demais da porta**.

Para uma travessia ser contada, não basta a pessoa ser detectada do
outro lado: o rastro dela precisa **chegar vivo até lá, com o mesmo
ID**. Em cima da porta há sombra, grade, e gente parada esperando — o
rastreador perde a pessoa exatamente ali, e a travessia nunca se
confirma. Foi o que aconteceu com `linha: 0.20` nesta instalação: só 8
das 9 a 19 entradas de um trecho eram contadas. Movendo para `0.25`,
foram 17.

Na prática, se os números parecem baixos:

1. Afaste a linha da porta, em direção à área aberta por onde as
   pessoas chegam (em passos de 0.05).
2. Só depois disso mexa na `margem` — reduzi-la também ajuda, mas
   enfraquece a proteção contra tremor.
3. Confira na janela se a pessoa continua sendo detectada, com a mesma
   cor de caixa, depois de passar a linha. Se a caixa some ou muda de
   cor ali, a linha está dentro da zona de oclusão.

---

## Ajustando para máquina fraca

Em ordem de impacto:

| Parâmetro | Efeito |
|---|---|
| `fps_processamento` | maior ganho, menor perda. Pessoas não andam rápido o bastante para poucos fps ser insuficiente |
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

**rastreio**
- `algoritmo` — arquivo do tracker. O padrão é o
  `bytetrack_ajustado.yaml` do projeto, com limiares mais tolerantes que
  o `bytetrack.yaml` da Ultralytics porque a nossa `confianca: 0.15` e
  `fps_processamento: 7.5` produzem detecções mais fracas e com saltos
  maiores entre frames — o que fazia a mesma pessoa ganhar um ID novo
  perto do portão. Cada valor está comentado dentro do arquivo. Para
  voltar ao padrão da biblioteca, use `"bytetrack.yaml"`

**filtro** — descarta caixas com geometria improvável para uma pessoa.
Os limites são permissivos de propósito: numa igreja há gente sentada,
de perfil e parcialmente oculta pelos bancos.

**contagem**
- `linha` — dois pontos (x1,y1,x2,y2), em frações do frame, definindo a
  linha sobre o portão. Os pontos são ordenados de cima para baixo pelo
  próprio contador, então a ordem em que você os escreve não troca
  entrada com saída
- `margem` — meia-largura da zona morta, em fração da largura do frame.
  Maior = mais resistente a tremor, porém exige que a pessoa se afaste
  mais da linha para ser contada
- `segundos_cooldown` / `segundos_esquecer` — tempo mínimo entre duas
  contagens da mesma pessoa e tempo até esquecer quem sumiu do
  enquadramento, contados no tempo do vídeo (não da CPU)

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

Vídeos de teste com fiéis reais (como os de `videos/`) não devem ser
versionados no Git — o `.gitignore` do projeto já bloqueia isso.

---

## Próximas etapas (TCC II)

- [x] API FastAPI servindo o dashboard — ver [`DOCUMENTACAO_API.md`](./DOCUMENTACAO_API.md)
- [x] Motor gravando no banco durante a missa, com dashboard ao vivo
- [ ] Agendamento automático com APScheduler
- [ ] Empacotamento com PyInstaller

`python main.py` já sobe tudo junto: o motor conta, grava no SQLite, e o
dashboard em `http://127.0.0.1:8000` acompanha a contagem ao vivo. Ver
[`DOCUMENTACAO_BANCO.md`](./DOCUMENTACAO_BANCO.md) para o modelo de dados
e [`../frontend/README.md`](../frontend/README.md) para o dashboard.

A classe `Monitor` é controlada de fora por `executar(ao_atualizar=...)`
e `parar()`, a mesma interface que o APScheduler vai usar para iniciar e
encerrar o monitoramento no horário de cada missa.
