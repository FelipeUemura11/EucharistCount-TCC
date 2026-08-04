# Eucharist Count

Sistema de contagem de pessoas em tempo real utilizando **visão computacional**, desenvolvido para auxiliar igrejas católicas no monitoramento de ocupação durante celebrações litúrgicas.

O objetivo é fornecer uma estimativa automatizada e confiável do número de fiéis presentes, apoiando a equipe litúrgica no dimensionamento de hóstias a serem consagradas e reduzindo o desperdício ou a escassez causados por estimativas puramente visuais.

> Trabalho de Conclusão de Curso — Bacharelado em Ciência da Computação, Universidade Positivo, Curitiba, 2026. A especificação completa está em [`EucharistCountDocument.pdf`](./EucharistCountDocument.pdf).

---

## Visão geral

A contagem de pessoas em ambientes fechados é uma necessidade recorrente em locais com fluxo variável de público — igrejas, auditórios, centros de convenções, cinemas, terminais de transporte. Este projeto usa como estudo de caso uma **igreja católica de Curitiba/PR**, onde a contagem de fiéis subsidia a estimativa de hóstias consagradas por celebração.

O sistema opera inteiramente **local** (Edge Computing), sem GPU e sem envio de imagens para a nuvem — nenhuma imagem ou vídeo é armazenado em disco, apenas contagens agregadas. Essa arquitetura é o que garante conformidade com a LGPD: sem retenção de dado biométrico ou identificável, não há tratamento de dado pessoal nos termos da lei.

---

## Objetivo geral

Desenvolver e validar um sistema automatizado de visão computacional para contagem de fluxo humano e gestão de ocupação a partir de câmeras fixas, utilizando o monitoramento de celebrações litúrgicas em igrejas católicas como estudo de caso prático.

## Objetivos específicos

a) Implementar um módulo de detecção de pessoas baseado em visão computacional, operando a partir de câmeras fixas em posição diagonal em ambientes fechados;
b) Integrar um módulo de rastreamento de múltiplos indivíduos, garantindo identificadores únicos e eliminando duplicidade na contagem;
c) Implementar a lógica de contagem por cruzamento de linha virtual, distinguindo entrada e saída, limitada ao intervalo de cada celebração;
d) Registrar e persistir os dados de ocupação, possibilitando acompanhamento histórico da lotação antes e durante as celebrações;
e) Validar o sistema em uma igreja católica de Curitiba/PR, avaliando acurácia da contagem e usabilidade do painel junto às equipes litúrgicas.

---

## Arquitetura

```
Máquina Local da Igreja
┌─────────────────────────────────────────┐
│  Frontend (React + TypeScript)           │
│              ↕ HTTP localhost            │
│  API (FastAPI)                           │
│              ↕ registra jobs             │
│  Automação (APScheduler)                 │
│              ↕ aciona/finaliza           │
│  Motor IA (OpenCV + YOLO + ByteTrack)    │
│              ↕ grava contagem            │
│  Base de Dados (SQLite)                  │
└─────────────────────────────────────────┘
        ↑
   Câmera IP / NVR — stream RTSP
```

Tudo roda num único executável local (empacotado com PyInstaller), sem conectividade externa. A câmera fornece o stream via RTSP; o motor de IA processa os frames em memória, sem gravar nada em disco; a API expõe os dados agregados ao dashboard via `localhost`.

---

## Stack tecnológica

Conforme especificado no documento do TCC:

| Camada | Tecnologia | Papel |
|---|---|---|
| Linguagem / matemática | **Python + NumPy** | Base do backend e manipulação matricial de frames |
| Visão computacional | **OpenCV** | Captura, redimensionamento e desenho sobre os frames |
| Detecção | **Ultralytics YOLO** | Detecção de pessoas (classe `person`), restrita à ROI dos acessos |
| Rastreamento | **ByteTrack** | Identificadores únicos e persistentes por indivíduo |
| API | **FastAPI + Uvicorn** | Rotas HTTP assíncronas, comunicação local |
| Validação de dados | **Pydantic** | Tipagem e validação dos schemas trafegados |
| Persistência | **SQLite** | Celebrações, contagens, snapshots — em arquivo único, local |
| Agendamento | **APScheduler** | Início/fim automático do monitoramento por celebração |
| Frontend | **React + TypeScript + Vite** | Dashboard, Celebrações, Histórico, Configurações |
| Gráficos | **Recharts** | Evolução da ocupação ao longo da celebração |
| HTTP client | **Axios** | Comunicação do frontend com a API local |
| Empacotamento | **PyInstaller** | Executável autônomo para a máquina da paróquia |

---

## Estado atual do projeto

Este é um TCC em duas etapas. **O que está implementado até aqui** é a fundação de visão computacional; API, banco de dados e frontend fazem parte da próxima etapa (TCC II).

| Componente | Status |
|---|---|
| Captura de vídeo (arquivo / webcam / RTSP, com reconexão) | ✅ Implementado |
| Detecção de pessoas (YOLO, otimizado para CPU via ONNX) | ✅ Implementado |
| Rastreamento com ID persistente (ByteTrack) | ✅ Implementado |
| Recorte de Região de Interesse (ROI) | ✅ Implementado |
| Contagem por cruzamento de linha virtual (entrada/saída) | ✅ Implementado |
| Painel de monitoramento em tempo real (janela local) | ✅ Implementado |
| API (FastAPI) | ⏳ Planejado — TCC II |
| Persistência (SQLite) | ⏳ Planejado — TCC II |
| Agendamento automático (APScheduler) | ⏳ Planejado — TCC II |
| Estimativa de comunhão e hóstias sugeridas | ⏳ Planejado — TCC II |
| Dashboard web (React) | ⏳ Planejado — TCC II |
| Empacotamento (PyInstaller) | ⏳ Planejado — TCC II |

Detalhes de uso, configuração e arquitetura interna do módulo de visão computacional estão em [`backend/README.md`](./backend/README.md).

---

## Estrutura do repositório

```
EucharistCount-TCC/
├── EucharistCountDocument.pdf   # especificação oficial do TCC
├── README.md                    # este arquivo
│
├── backend/
│   ├── main.py                  # ponto de entrada do monitoramento
│   ├── config.json              # parâmetros ajustáveis (câmera, modelo, contagem)
│   ├── requirements.txt
│   ├── README.md                # documentação detalhada do backend
│   │
│   ├── eucharist/                # módulo de visão computacional
│   │   ├── config.py            # carrega/salva config.json
│   │   ├── camera.py            # captura: arquivo, webcam ou RTSP
│   │   ├── detector.py          # YOLO + ByteTrack + ROI → lista de Pessoa
│   │   ├── contador.py          # contagem por cruzamento de linha virtual
│   │   ├── visual.py            # desenho (janela de monitoramento)
│   │   └── monitor.py           # orquestra o ciclo completo
│   │
│   ├── scripts/
│   │   ├── preparar_modelo.py   # exporta o modelo YOLO para ONNX
│   │   └── calibrar.py          # testa combinações de modelo/resolução/confiança
│   │
│   ├── modelos/                 # modelos .onnx (fora do Git)
│   └── videos/                  # vídeos de teste (fora do Git)
│
└── frontend/                    # scaffold React + TypeScript + Vite (TCC II)
```

---

## Como executar (etapa atual: visão computacional)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows

pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

python -m scripts.preparar_modelo --modelo yolo11n --imgsz 640
python main.py
```

Instruções completas — calibração de modelo, ajuste de linha de contagem, ROI, parâmetros de `config.json` — estão em [`backend/README.md`](./backend/README.md).

O frontend (`frontend/`) é um scaffold Vite + React + TypeScript ainda não integrado à API, reservado para a próxima etapa do TCC.

---

## Estratégia de contagem

A contagem usa uma **linha virtual** posicionada sobre o portão de acesso, definida por dois pontos (podendo ter qualquer inclinação, o que acomoda câmeras em posição diagonal conforme exigido no objetivo específico *a*). Cada pessoa rastreada é avaliada pelo lado da linha em que se encontra, quadro a quadro:

- Cruzamento no sentido de entrada → incrementa a ocupação.
- Cruzamento no sentido de saída → decrementa a ocupação.
- Pessoa detectada repetidamente sem cruzar a linha → não altera a contagem.

Essa abordagem, combinada ao rastreamento por ID único do ByteTrack, evita que a mera presença de uma pessoa em múltiplos frames gere contagem duplicada — o problema citado na justificativa do TCC como recorrente em sistemas baseados apenas em detecção quadro a quadro.

---

## Privacidade e proteção de dados (LGPD)

O sistema **não possui, em nenhum ponto do código, capacidade de salvar imagem ou vídeo em disco**. Os frames capturados existem somente em memória (RAM) durante o processamento e são descartados assim que o próximo frame chega. Ao final, permanecem apenas números agregados (quantidade de pessoas, entradas, saídas) — nunca a imagem em si.

É essa ausência estrutural de armazenamento de imagem, e não uma configuração desligável, que fundamenta a conformidade com a LGPD descrita no TCC: sem retenção de dado biométrico ou identificável, não há tratamento de dado pessoal.

Vídeos de teste com fiéis reais não são versionados no Git — o `.gitignore` do projeto bloqueia isso.

---

## Validação planejada

Conforme o objetivo específico *e*, a validação do sistema em campo (igreja católica de Curitiba/PR) deverá avaliar:

- Acurácia da contagem frente à contagem manual de referência;
- Capacidade de distinguir corretamente entradas e saídas;
- Robustez a oclusão parcial (bancos, aglomeração nos acessos);
- Desempenho em CPU, sem GPU, na máquina real da paróquia;
- Desempenho com câmera em posição diagonal;
- Usabilidade do painel pela equipe litúrgica.

---

## Referências técnicas

A fundamentação bibliográfica completa (YOLO, ByteTrack, crowd counting, SQLite, FastAPI, React, entre outras) está no capítulo de Referências do [`EucharistCountDocument.pdf`](./EucharistCountDocument.pdf).

---

## Autores

- Felipe Yukiya Soares Uemura
- Yasmin Faraj
- Yuji Chikara Kiyota
- Eduardo Cornehl Wozniak

**Orientadora:** Prof. Malgarete Rodrigues Da Costa

## Instituição

**Universidade Positivo**
Bacharelado em Ciência da Computação
Curitiba — 2026

## Licença

Projeto desenvolvido como Trabalho de Conclusão de Curso. A licença de uso será definida pelos autores.
