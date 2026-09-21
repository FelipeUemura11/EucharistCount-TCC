# Documentação Técnica — Motor de Visão Computacional

## Eucharist Count — Backend

Este documento explica **como e por que** cada parte do motor de visão computacional funciona, com a justificativa técnica de cada escolha e de cada fórmula matemática usada no código. O objetivo é que qualquer pessoa da equipe — ou a banca do TCC — consiga entender não apenas *o que* o sistema faz, mas *por que* foi construído dessa forma.

Os valores citados aqui refletem a configuração atual do projeto (`config.json`).

---

## 1. Visão geral: o caminho de um frame

Antes de entrar em cada detalhe, vale entender o percurso completo que um único quadro de vídeo percorre, do início ao fim:

```
Câmera/Arquivo
    │
    ▼
FonteVideo (camera.py)          → entrega o frame, no ritmo certo
    │
    ▼
DetectorPessoas (detector.py)   → roda YOLO + ByteTrack, filtra caixas
    │                              devolve uma lista de objetos Pessoa
    ▼
ContadorLinha (contador.py)     → verifica se alguma Pessoa trocou de lado
    │                              devolve Eventos (entrada/saída)
    ▼
Monitor (monitor.py)            → atualiza métricas, desenha na tela
```

Cada seta é uma fronteira de responsabilidade: o módulo de captura não sabe o que é uma pessoa; o detector não sabe o que é uma linha de contagem; o contador não sabe o que é OpenCV. Essa separação existe para que cada peça possa ser entendida, testada e ajustada isoladamente — e é o que vai permitir, na próxima etapa, plugar a API FastAPI e o APScheduler por cima sem reescrever nada disto.

---

## 2. O pipeline do modelo: de onde ele vem até como é usado

Antes de falar de formato de arquivo, vale situar de onde o modelo vem. Este projeto **não treina** a rede neural — treinar um detector do zero exigiria centenas de milhares de imagens anotadas e dias de GPU, incompatível com o escopo e o hardware disponíveis. O que o projeto usa é um modelo **já treinado pela própria Ultralytics** no dataset COCO (~330 mil imagens, 80 categorias de objetos, incluindo `person`) e disponibilizado publicamente. Esse treinamento é um processo externo, anterior e independente deste TCC — o trabalho aqui começa a partir do resultado dele.

A partir desse ponto, existem **dois pipelines distintos**, que rodam em momentos diferentes e resolvem problemas diferentes:

```
PIPELINE DE PREPARACAO — offline, executado UMA VEZ
(scripts/preparar_modelo.py)

  Rede ja treinada pela Ultralytics (COCO, fora deste projeto)
        │
        ▼
  Download automatico do checkpoint .pt
        │   formato de TREINO: flexivel, pesado, depende do PyTorch inteiro
        ▼
  modelo.export(format="onnx", imgsz=640, half=False, ...)
        │   conversao: "congela" a rede numa resolucao fixa,
        │   descarta tudo que so serve para treinar
        ▼
  arquivo .onnx salvo em modelos/
        │
        └── o .pt baixado e apagado — ja cumpriu sua funcao


PIPELINE DE EXECUCAO — repetido a cada frame, na missa inteira
(motor/detector.py, toda vez que main.py roda)

  DetectorPessoas carrega SOMENTE o .onnx (nunca mais toca o .pt)
        │
        ▼
  ONNX Runtime executa a inferencia (nao o motor do PyTorch)
        │
        ▼
  lista de objetos Pessoa
```

### Por que essa separação em dois momentos importa

O pipeline de preparação é **pesado e só precisa rodar uma vez**: ele baixa o checkpoint, aciona toda a maquinaria de exportação do PyTorch, e pode inclusive ser executado numa máquina mais potente do que a da igreja — o resultado (o `.onnx`) é só copiado depois para `modelos/`. Nada disso acontece durante uma celebração.

O pipeline de execução, em contraste, **roda continuamente durante toda a missa**, quadro a quadro, na máquina fraca da paróquia. É por isso que ele foi deliberadamente reduzido ao mínimo: a partir do momento em que o `.onnx` existe, `DetectorPessoas` nunca mais carrega um `.pt` nem aciona a máquina de exportação — ele entrega o arquivo direto ao ONNX Runtime, que foi construído especificamente para executar esse tipo de grafo já congelado com o menor overhead possível.

Essa é a razão de existir dois arquivos e duas etapas em vez de usar sempre o `.pt`: colocar todo o custo de conversão **antes** do dia da missa, para que o que roda **durante** a missa seja o mínimo necessário.

### O que muda de um formato para o outro

**`.pt`** é o formato nativo do PyTorch, otimizado para flexibilidade de treino: junto aos pesos da rede, carrega metadados que permitem continuar treinando, trocar camadas, inspecionar tensores intermediários. Essa flexibilidade é justamente o que o pipeline de execução não precisa e não pode pagar.

**`.onnx`** descreve a mesma rede como um grafo fixo de operações matemáticas, sem nada relacionado a treino. O ONNX Runtime aplica otimizações específicas de CPU sobre esse grafo — fusão de operações, melhor uso de cache, paralelização — que o PyTorch genérico não aplica por padrão quando usado fora do fluxo de treinamento.

No código, a conversão é:

```python
modelo = YOLO(f"{args.modelo}.pt")          # baixa o checkpoint treinado
caminho_onnx = modelo.export(               # converte para ONNX
    format="onnx",
    imgsz=args.imgsz,
    half=False,
    simplify=True,
    opset=12,
    device="cpu",
)
```

Um detalhe que decorre diretamente da natureza "congelada" do `.onnx`: ele fixa a resolução de entrada (`imgsz`) no momento da exportação. Mudar de `imgsz=640` para `imgsz=960` exige reexportar — o `.onnx` não aceita variar isso em tempo de execução como o `.pt` aceitaria. É o preço da rigidez que o torna mais rápido.

### Por que os parâmetros de exportação são esses

- **`half=False`** — `half` ativaria FP16 (números de 16 bits em vez de 32). Isso acelera bastante em GPU, mas em **CPU comum não traz ganho de velocidade** e ainda reduz a precisão numérica. Como a máquina da paróquia não tem GPU, manter FP32 (`half=False`) é a escolha correta.
- **`simplify=True`** — remove operações redundantes do grafo (nós que não afetam o resultado final), deixando o modelo mais enxuto e um pouco mais rápido de carregar e executar.
- **`opset=12`** — é a "versão da linguagem" do formato ONNX. Um opset mais antigo garante compatibilidade ampla com diferentes versões do ONNX Runtime; um valor muito recente poderia falhar em ambientes mais conservadores, como pode ser o caso de um computador de igreja com Windows desatualizado.

### Por que isso importa na prática

O ganho medido de ONNX sobre `.pt` em CPU é tipicamente de **2 a 4 vezes** em velocidade de inferência, sem perda de precisão perceptível. Combinado com o fato de que esse custo de conversão é pago uma única vez, fora do horário de missa, o resultado é que a máquina da igreja nunca precisa arcar com o lado mais pesado do pipeline — só com a parte que já foi otimizada para ela.

---

## 3. YOLO: detecção de pessoas

O YOLO (You Only Look Once) é um detector de objetos *de estágio único* — ele olha a imagem inteira uma única vez e devolve, simultaneamente, todas as caixas delimitadoras e suas classificações, em vez de primeiro propor regiões de interesse e depois classificá-las separadamente (como fazem detectores de dois estágios). Essa arquitetura é o que viabiliza velocidade suficiente para tempo real em CPU.

No código (`detector.py`), a chamada relevante é:

```python
resultado = self.modelo.track(
    entrada,
    imgsz=self.config.imgsz,
    conf=self.config.confianca,
    iou=self.config.iou,
    classes=[CLASSE_PESSOA],   # = 0
    ...
)
```

`classes=[0]` restringe a saída à classe `person` do dataset COCO (no qual o modelo foi originalmente treinado) — o modelo é capaz de reconhecer dezenas de categorias de objetos, mas o sistema descarta tudo que não seja pessoa antes mesmo de o resultado chegar ao resto do código. Isso não só é necessário funcionalmente, como também reduz o processamento de pós-detecção (NMS) a apenas uma classe.

O modelo usado é o **YOLO11n** (variante "nano" da 11ª geração da arquitetura) — a menor e mais rápida disponível, mantendo precisão suficiente para o cenário. Modelos maiores (`s`, `m`, `l`, `x`) trocam velocidade por uma capacidade de detecção maior, principalmente em objetos pequenos e distantes; numa máquina sem GPU, a variante "nano" é o único ponto de operação que ainda permite processamento em tempo aproximado ao real.

---

## 4. `confianca`, `iou`, e a dupla NMS/IoU

### Confiança (limiar de detecção)

Todo objeto que o YOLO acredita ser uma pessoa recebe uma pontuação de 0 a 1. O parâmetro `confianca` (atualmente **0.15**) é o piso: qualquer detecção abaixo disso é descartada antes mesmo de chegar ao filtro geométrico ou ao contador.

O valor está deliberadamente baixo. A justificativa é o cenário de uso: no acesso da igreja há oclusão parcial constante (pessoas passando perto umas das outras, roupas escuras, contraluz), o que reduz artificialmente a confiança do modelo mesmo quando a detecção está correta. Um limiar baixo aceita essas detecções "menos certas" — e o risco de falso positivo que isso traz é compensado por duas outras camadas do sistema: o filtro geométrico (seção 6) e a exigência de atravessar a zona morta inteira para confirmar uma contagem (seção 8.4).

### IoU (Intersection over Union) e NMS (Non-Maximum Suppression)

**IoU** é uma métrica de sobreposição entre duas caixas:

```
IoU = área da interseção / área da união das duas caixas
```

Varia de 0 (caixas totalmente separadas) a 1 (caixas idênticas). É a régua usada para responder: "essas duas caixas detectadas são a mesma pessoa vista duas vezes, ou são duas pessoas diferentes muito próximas?"

**NMS** é o algoritmo que usa essa régua para limpar duplicatas: dentre caixas sobrepostas, mantém a de maior confiança e descarta as demais cujo IoU com ela ultrapasse o limiar configurado.

O parâmetro `iou` no `config.json` está em **0.7** — um valor alto para o padrão da área (o comum é algo entre 0.4 e 0.5). Essa escolha resolve um problema específico observado durante os testes: **duas pessoas andando lado a lado geram caixas naturalmente sobrepostas**, e com um limiar baixo o NMS as tratava como duplicata da mesma pessoa, descartando uma delas — o sistema contava duas pessoas juntas como se fosse uma só. Subir o `iou` para 0.7 torna o NMS mais tolerante a sobreposição legítima entre indivíduos distintos, só descartando caixas que se sobrepõem quase inteiramente (o caso real de detecção duplicada da mesma pessoa).

---

## 5. ByteTrack: manter a identidade de cada pessoa

Detecção sozinha não é suficiente para contar pessoas: o YOLO analisa cada frame de forma independente, sem nenhuma noção de "essa caixa no frame 50 é a mesma pessoa da caixa no frame 49". Sem rastreamento, uma pessoa parada por vários frames poderia ser contada várias vezes.

O **ByteTrack**, configurado via `tracker: "bytetrack.yaml"` e acionado com `modelo.track(..., persist=True)`, resolve isso associando detecções entre frames consecutivos e atribuindo um **ID numérico estável** a cada pessoa. `persist=True` é o que garante que esse histórico de IDs continue entre uma chamada e outra — sem isso, o rastreador reiniciaria a contagem de IDs a cada frame.

A vantagem específica do ByteTrack sobre alternativas mais pesadas (como o DeepSORT, usado nas versões iniciais deste projeto) é a forma como ele trata detecções de baixa confiança: em vez de descartá-las, ele tenta associá-las a rastros já existentes antes de decidir que são ruído. Isso confere resiliência a oclusão parcial — exatamente o cenário de bancos de igreja e aglomeração no portão — sem o custo computacional de um extrator de aparência visual (rede neural adicional que o DeepSORT usa para "reconhecer" a pessoa por sua aparência, cara demais para uma CPU sem GPU).

O ID atribuído pelo ByteTrack é o que permite ao `ContadorLinha` (seção 8) saber que a mesma pessoa cruzou a linha, e não duas pessoas diferentes.

---

## 6. Filtro geométrico: descartando caixas implausíveis

Depois que o YOLO e o NMS já filtraram por confiança e sobreposição, uma segunda camada de segurança — puramente geométrica, sem nenhuma rede neural envolvida — rejeita caixas cuja forma não faz sentido para uma pessoa:

```python
fracao_area = (largura * altura) / (largura_frame * altura_frame)
if not (area_min <= fracao_area <= area_max):
    return False

aspecto = largura / altura
return aspecto_min <= aspecto <= aspecto_max
```

Os valores atuais são:

| Parâmetro | Valor | O que rejeita |
|---|---|---|
| `area_min` | 0.0001 | Manchas microscópicas de falso positivo (ruído, reflexo) |
| `area_max` | 0.35 | Uma "pessoa" absurdamente grande — provavelmente a câmera ficou muito perto de algo, ou é um erro do modelo |
| `aspecto_min` | 0.10 | Caixas anormalmente largas e baixas — não é o formato de uma pessoa em pé |
| `aspecto_max` | 3.2 | Caixas anormalmente altas e finas |

Esses limites são propositalmente **permissivos**, não restritivos. A razão é o próprio ambiente do estudo de caso: numa igreja há gente sentada, de perfil, parcialmente cortada pela borda do quadro perto do portão, ou parcialmente oculta por outra pessoa — situações que produzem proporções de caixa bem diferentes de uma pessoa "de pé, de frente, isolada". Limites apertados demais rejeitariam detecções corretas justamente nos casos mais difíceis, que é onde mais importa não perder a contagem.

---

## 7. Enquadramento da câmera e o que ele já resolve

Uma versão anterior deste sistema recortava digitalmente o frame antes da
inferência (técnica conhecida como ROI — Região de Interesse), para
analisar apenas a área próxima ao portão.

Essa etapa foi **removida** após o reposicionamento físico da câmera. Com
a câmera apontada diretamente para a entrada, todo o enquadramento já
corresponde à área de interesse — recortar digitalmente passou a ser
redundante e só adicionaria complexidade ao código (conversão de
coordenadas, risco de cortar a linha de contagem, mais um parâmetro a
calibrar).

### 7.1 A troca de câmera e o que ela mudou no software

A câmera originalmente usada no estudo de caso apresentou problemas em
campo e foi substituída pela câmera já instalada **do outro lado da
igreja** (identificada como `CAM 2` na gravação). O enquadramento mudou
por completo:

| | Câmera antiga | Câmera atual (`CAM 2`) |
|---|---|---|
| Posição do portão no frame | região central | **canto esquerdo** |
| Quem está entrando se desloca | para a direita | **da direita para a esquerda** |
| Quem está saindo se desloca | para a esquerda | **da esquerda para a direita** |

A consequência prática é que a matemática não mudou: só a posição da
linha, que passou de uma vertical no meio do frame
(`[0.50, 0.0, 0.50, 1.00]`) para uma vertical **na porção esquerda**
(`[0.25, 0.0, 0.25, 1.00]`), perto do portão.

Essa câmera é **fixa** — não haverá nova troca. Por isso o sentido da
entrada (direita → esquerda) deixou de ser configuração e passou a ser
uma regra do código, descrita na seção 8.6.

### 7.2 Por que a linha não fica colada no portão

A primeira tentativa colocou a linha em `x = 0.20`, praticamente em cima
do batente. O raciocínio parecia correto: o modelo detecta pés até
`x ≈ 0.06` da largura do frame, então haveria folga de sobra dos dois
lados.

**Esse raciocínio estava errado**, e a medição mostrou por quê. O que a
contagem exige não é que *exista detecção* do outro lado da linha — é
que o **rastro sobreviva** até lá, com o mesmo ID. E é exatamente na
boca do portão que o rastreio morre: a pessoa entra na sombra do vão,
passa atrás da grade e do arbusto do primeiro plano, e some no meio de
quem já está parado ali esperando.

Medindo, num trecho de 40 s de chegada de fiéis, onde termina o rastro
de cada pessoa que caminhava para a esquerda:

| Onde o rastro terminou (`x`) | Quantos |
|---|---|
| 0.00 – 0.10 | 2 |
| 0.10 – 0.16 | 7 |
| **0.16 – 0.20** | **9** |
| 0.20 – 0.24 | 1 |
| 0.24 – 0.30 | 4 |
| 0.30 – 1.00 | 7 |

Com a linha em `0.20` e `margem = 0.035`, a pessoa só é confirmada do
lado de dentro ao ser vista antes de `x = 0.165`. O maior grupo de
rastros — os 9 que terminam entre `0.16` e `0.20` — morre poucos pixels
antes desse limiar. Resultado: **apenas 8 das 9 a 19 entradas plausíveis
daquele trecho eram contadas.**

Deslocar a linha para `x = 0.25` move o limiar de confirmação para
`x = 0.215`, antes da zona de oclusão, e recupera esses rastros. Numa
varredura das duas coisas que se pode ajustar — posição da linha e
largura da zona morta — medida em dois trechos independentes do vídeo:

| `linha` | `margem` | Trecho A (9–19 plausíveis) | Trecho B (5–10 plausíveis) |
|---|---|---|---|
| 0.20 | 0.035 | 8 ✗ | 6 |
| 0.20 | 0.020 | 16 | 8 |
| **0.25** | **0.035** | **17 ✓** | **9 ✓** |
| 0.30 | 0.035 | 16 ✓ | 10 ✓ |
| 0.35 | 0.035 | 16 ✓ | 10 ✓ |
| 0.40 | 0.035 | 13 ✓ | 11 ✗ |

O número plausível de entradas de cada trecho foi estimado **sem usar o
contador**, para não julgar o parâmetro com a própria ferramenta que ele
configura: o piso são os rastros inequívocos, que vão de `x > 0.55` até
`x < 0.22` num único ID; o teto acrescenta os rastros parciais que se
deslocaram para a esquerda e podem ser pedaços de travessias reais.

`0.25 / 0.035` é o único ajuste que cai dentro da faixa plausível nos
dois trechos, e tem a vantagem de não mexer na `margem` — mantendo
intacta a proteção contra tremor descrita na seção 8.4. Empurrar a linha
para `0.40` começa a contar gente demais: naquela altura do quadro ela
cruza o caminho de quem apenas circula pelo pátio sem entrar.



---

## 8. A contagem por linha virtual

Esta é a parte central do sistema: transformar "uma pessoa detectada em algum lugar do frame" em "uma pessoa que entrou ou saiu pela porta".

### 8.1 Por que uma linha, e não uma área

Uma linha virtual modela naturalmente o ato de "atravessar um limiar físico" — o portão da igreja. Ao contrário de uma zona (região poligonal), que exigiria decidir arbitrariamente quando alguém "está dentro" versus "está passando", uma linha reduz o problema a uma pergunta binária e bem definida a cada frame: a pessoa está de que lado?

### 8.2 A fórmula: distância com sinal

Dada uma linha entre os pontos A e B, e um ponto P (a posição da pessoa), o sistema calcula:

```python
produto = (bx - ax) * (py - ay) - (by - ay) * (px - ax)
distancia = produto / comprimento_da_linha
```

O numerador é a componente z do **produto vetorial** entre o vetor da linha (`B - A`) e o vetor do ponto até o início da linha (`P - A`). Dividido pelo comprimento da linha, o resultado é a **distância com sinal** entre o ponto e a reta:

- **O sinal** diz de que lado o ponto está (positivo de um lado, negativo do outro, zero exatamente sobre a reta).
- **O módulo** diz a distância em pixels até a reta.

Uma única fórmula responde às duas perguntas de que o contador precisa — de que lado, e a que distância. É por isso que o módulo não tem nenhuma outra função geométrica.

A vantagem decisiva dessa formulação é que ela funciona **para qualquer inclinação da linha**, sem nenhum caso especial. Uma comparação simples como "a pessoa está à esquerda ou à direita de um valor de x fixo" só funcionaria para linhas perfeitamente verticais; o produto vetorial generaliza isso para qualquer ângulo. Isso é o que permite a linha de contagem acompanhar a geometria real da câmera — que, no objetivo específico do TCC, é posicionada **em ângulo diagonal**, não perpendicular ao chão.

### 8.3 O ponto de referência da pessoa: os pés, não o centro

O sistema usa `pessoa.base` — o ponto médio da base da caixa delimitadora (os pés) — como posição da pessoa para o cálculo do lado, em vez do centro geométrico da caixa:

```python
@property
def base(self) -> tuple[int, int]:
    return (self.x1 + self.x2) // 2, self.y2
```

A razão é a estabilidade sob oclusão parcial. Quando o torso de uma pessoa é parcialmente encoberto por outra pessoa ou por um obstáculo, a caixa delimitadora "encolhe" de forma inconsistente pelo topo, deslocando o centro geométrico de forma imprevisível. Os pés, apoiados no chão, são a parte da caixa que menos varia nessas situações — e é justamente a posição no chão que corresponde fisicamente a "de que lado da porta a pessoa está".

### 8.4 A zona morta: por que não basta trocar de sinal

Se o contador registrasse toda troca de sinal da distância, o sistema geraria contagens falsas o tempo todo. O motivo é que **o YOLO nunca desenha a caixa exatamente no mesmo pixel dois frames seguidos**, mesmo para uma pessoa completamente parada. Alguém aguardando em pé em cima da linha "entraria e sairia" repetidamente sem ter saído do lugar.

A solução é uma **zona morta** em torno da linha, de largura `margem` para cada lado:

```python
if abs(distancia) < self.margem:
    return None          # lado indefinido: nada muda neste frame

lado = 1 if distancia > 0 else -1
```

O lado da pessoa só é atualizado quando ela está a mais de `margem` pixels da linha. Entre `-margem` e `+margem` nenhuma decisão é tomada. O tremor de poucos pixels da caixa delimitadora acontece inteiro dentro dessa faixa e nunca chega a mudar o lado registrado; só um deslocamento real atravessa a faixa inteira, de um lado ao outro.

O valor atual é `margem: 0.035` (fração da largura do frame), ou seja, uma faixa total de 7% da largura. Num frame de 1024 px isso são ±36 px em torno da linha.

Um ponto que costuma gerar dúvida: a travessia **não precisa acontecer em um único frame**. A pessoa pode levar quantos frames quiser atravessando a faixa — o contador apenas registra o novo lado quando ela sai dela. Isso torna o parâmetro tolerante a pessoas andando devagar, paradas no meio do caminho, ou momentaneamente perdidas pelo rastreador.

### 8.5 Uma nota histórica: de três linhas para uma faixa

Uma versão anterior deste contador gerava **três linhas paralelas** e só confirmava a travessia quando a pessoa cruzasse pelo menos duas delas no mesmo sentido, dentro de uma janela de tempo. O objetivo era exatamente o mesmo da zona morta: exigir deslocamento real, e não tremor.

A zona morta substitui esse mecanismo porque entrega a mesma garantia com bem menos peças móveis. O esquema antigo exigia quatro parâmetros (`numero_linhas`, `espacamento`, `linhas_necessarias`, `segundos_janela`) e mantinha, para cada pessoa, um dicionário de lados por linha mais uma lista de cruzamentos com carimbo de tempo. O esquema atual exige um parâmetro (`margem`) e guarda **um único inteiro por pessoa**: o último lado confirmado.

Além de mais simples, a faixa é conceitualmente mais direta: o que se quer exigir é *deslocamento mínimo em pixels*, e a margem expressa isso literalmente, enquanto "duas de três linhas espaçadas de 0.035" expressava a mesma distância de forma indireta.

### 8.6 O sentido da entrada

O sinal da distância separa os dois lados da linha, mas nada na matemática diz qual lado é "dentro" e qual é "fora" — isso depende da posição física da câmera. Na instalação atual (`CAM 2`, seção 7.1) o portão está no canto esquerdo do frame: **quem passa da direita para a esquerda entra; quem vai da esquerda para a direita sai.** Como a câmera é fixa, essa regra está no código, e não no `config.json`.

O lado positivo é sempre o lado apontado pelo vetor perpendicular `(-dy, dx)`. Para uma linha percorrida **de cima para baixo**, esse vetor aponta para a **esquerda do frame**. Para que isso valha sempre, o contador normaliza a linha nessa ordem ao convertê-la para pixels:

```python
return (a, b) if a[1] <= b[1] else (b, a)
```

Assim, inverter a ordem dos pontos no `config.json` não troca entrada com saída silenciosamente.

Com a esquerda sendo o lado positivo, o lado para onde a pessoa foi **é** o sentido da travessia. Os valores do enum `Sentido` foram escolhidos para coincidir com os lados (`ENTRADA = +1`, `SAIDA = -1`), e a conversão vira uma linha:

```python
sentido = Sentido(lado)   # foi para a esquerda = entrou
```

A seta verde "ENTRA" desenhada na janela de monitoramento aponta sempre para a esquerda, e a vermelha "SAI" para a direita, para conferir visualmente a linha antes de confiar nos números.

Vale registrar o histórico: a versão anterior tinha um parâmetro `entrada_para_esquerda` (e, antes dele, `lado_entrada: ±1`) para acomodar uma eventual troca de câmera. Com a câmera definitiva, esse parâmetro só acrescentava um caminho de código e um valor de configuração que nunca mais mudariam — e que, se editado por engano, inverteria silenciosamente todas as contagens.

### 8.7 As duas janelas de tempo

Dois parâmetros temporais governam o ciclo de vida de cada rastro:

**`segundos_cooldown` (3.0s)** — depois de confirmar uma contagem para uma pessoa, o sistema ignora novos eventos dela por esse período. Isso evita contar a mesma pessoa duas vezes caso ela volte a atravessar a faixa logo após ser contada — alguém que para na porta, hesita e volta, por exemplo.

**`segundos_esquecer` (10.0s)** — pessoas que somem do enquadramento (ou que o rastreador simplesmente perde) têm seu rastro apagado após esse tempo:

```python
limite = self.config.segundos_esquecer
for pid in [pid for pid, r in self._rastros.items()
            if agora - r.visto_em > limite]:
    del self._rastros[pid]
```

Sem essa limpeza, o dicionário de rastros cresceria indefinidamente ao longo de uma missa inteira, consumindo memória sem necessidade numa máquina já limitada.

A `segundos_janela` da versão anterior deixou de existir junto com a lista de cruzamentos: não havendo mais eventos parciais acumulados, não há o que expirar.

### 8.8 Um detalhe crítico: tempo do vídeo, não da máquina

O tempo usado em todos os cálculos acima (`agora`) não vem do relógio da CPU (`time.perf_counter()`), e sim do **tempo do próprio vídeo**, calculado em `camera.py`:

```python
@property
def tempo_atual(self) -> float:
    if self._ao_vivo:
        return time.perf_counter()
    return self.indice_atual / max(self.fps_original, 1e-6)
```

Para um arquivo de vídeo, o tempo é `número do frame ÷ fps original do arquivo` — um valor que depende só do conteúdo do vídeo, nunca de quão rápido a máquina processa. Isso é essencial para a reprodutibilidade dos testes de validação do TCC: rodar o mesmo arquivo numa máquina mais lenta ou mais rápida produz **exatamente a mesma contagem**, porque os limiares de tempo (cooldown, esquecer) sempre se referem ao tempo que se passou *dentro do vídeo*, não ao tempo que o computador levou para processá-lo. Sem esse cuidado, o mesmo vídeo poderia gerar contagens diferentes dependendo do hardware — o que inviabilizaria comparar resultados de forma confiável.

Um cuidado que decorre disso: o campo `contado_em` de cada rastro nasce em `-infinito`, e não em zero. Como o tempo do vídeo começa em zero, um valor inicial zero colocaria todo mundo em cooldown durante os primeiros 3 segundos de gravação — ninguém que cruzasse a linha nesse intervalo seria contado.

---

## 9. Captura de vídeo: ritmo e resiliência

### 9.1 Por que limitar o FPS processado

`fps_processamento: 7.5` significa que o sistema analisa 7,5 quadros por segundo, não os 25–30 que um vídeo tipicamente contém. Para arquivos, isso é implementado como um pulo determinístico de frames:

```python
passo = round(fps_original / fps_alvo)
if passo > 1 and indice % passo != 0:
    continue
```

A justificativa é dupla. Primeiro, uma pessoa caminhando não se desloca o suficiente entre dois trigésimos de segundo para que analisar cada quadro individual traga informação nova relevante — o custo computacional de processar 30 fps não se traduz em contagem mais precisa. Segundo, e mais importante para este projeto: **cada frame processado custa CPU**, e numa máquina sem GPU, reduzir a taxa de processamento é o ajuste de maior impacto disponível para manter o sistema fluido.

Para streams ao vivo (RTSP/webcam), o mesmo objetivo é alcançado de forma diferente — por tempo decorrido, não por índice de frame, já que não existe um "índice total" conhecido de antemão numa transmissão contínua:

```python
if agora - ultimo_envio < intervalo_minimo:
    continue
```

### 9.2 Reconexão automática

Se um stream RTSP cair no meio de uma celebração, o sistema não encerra — ele espera `segundos_reconexao` (3.0s) e tenta reabrir a conexão automaticamente, indefinidamente, até conseguir. Isso é essencial num cenário de uso real: uma queda momentânea de rede Wi-Fi não pode exigir intervenção manual de alguém da equipe litúrgica no meio da missa.

---

## 10. Limitação de threads de CPU

```python
for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ[var] = str(n)
```

Por padrão, bibliotecas de computação numérica (como as usadas internamente pelo ONNX Runtime) tentam usar **todos os núcleos disponíveis** da CPU. Numa máquina dedicada de servidor isso é desejável; numa máquina de igreja que também precisa rodar outras coisas (o próprio sistema operacional, talvez outros programas), monopolizar todos os núcleos deixaria a máquina praticamente travada para qualquer outro uso. O parâmetro `threads` (atualmente `0`, ou seja, sem limite explícito) existe para poder restringir esse consumo quando necessário — por exemplo, `threads: 2` numa máquina de poucos núcleos.

---

## 11. Por que o código é dividido em módulos pequenos

A estrutura do pacote `motor/` — `camera.py`, `detector.py`, `contador.py`, `visual.py`, `monitor.py` — segue o princípio de responsabilidade única: cada arquivo resolve exatamente um problema e não sabe nada sobre os outros além do necessário para trocar dados.

Essa separação não é só estética. Ela tem três consequências práticas diretas para este projeto:

1. **Testabilidade.** `ContadorLinha`, por exemplo, recebe objetos `Pessoa` (dataclasses simples) e devolve `Evento`s — nada de OpenCV, nada de YOLO. É possível escrever um teste automatizado que simula uma "pessoa" andando por posições específicas e verificar se a contagem funciona corretamente, sem precisar rodar um vídeo real. Isso será importante na fase de validação de acurácia do TCC II.
2. **Substituibilidade.** Se um dia o projeto trocar o algoritmo de rastreamento, ou adicionar suporte a múltiplas câmeras, as mudanças ficam isoladas em `detector.py`/`camera.py` sem tocar na lógica de contagem.
3. **Integração futura.** A classe `Monitor` já expõe `executar()`/`parar()` como uma interface pronta para ser controlada externamente — é exatamente o formato que o APScheduler vai precisar para iniciar e encerrar o monitoramento automaticamente no horário de cada celebração, sem que essa integração exija reescrever o motor de visão computacional.

---

## 12. Por que nada é salvo em disco

Esta não é uma configuração que pode ser ligada ou desligada — é uma ausência estrutural. Em nenhum lugar do código existe uma chamada a `cv2.imwrite()` ou `cv2.VideoWriter()`. Os frames chegam da câmera, são processados inteiramente em memória (RAM), e são descartados assim que o frame seguinte chega. Ao final de todo o processamento, o que sobrevive são apenas números agregados — quantas entradas, quantas saídas, qual a ocupação — nunca a imagem em si.

Essa é a base técnica direta da conformidade com a LGPD que o TCC declara: sem retenção de imagem, não existe dado biométrico ou identificável sendo armazenado, e portanto não há tratamento de dado pessoal nos termos da lei.

---

## Resumo das decisões-chave

| Decisão | Valor atual | Motivo central |
|---|---|---|
| Formato de inferência | ONNX (a partir de `.pt`) | 2–4× mais rápido em CPU, sem GPU disponível |
| `half` na exportação | `False` | FP16 não acelera em CPU e perde precisão |
| Modelo | YOLO11n | Menor variante viável para tempo real sem GPU |
| `confianca` | 0.15 | Ambiente com oclusão parcial exige limiar permissivo |
| `iou` (NMS) | 0.7 | Evita fundir pessoas próximas numa única detecção |
| Rastreador | ByteTrack | Resiliente a oclusão, sem custo de extrator de aparência |
| Ponto de referência | Pés (base da caixa) | Mais estável que o centro sob oclusão parcial |
| Cálculo de lado da linha | Distância com sinal (produto vetorial) | Uma fórmula dá lado e distância, em qualquer ângulo |
| Posição da linha | Vertical em `x = 0.25` | Perto do portão, mas fora da zona onde o rastreio morre |
| Sentido da entrada | Direita → esquerda | Lado da igreja de onde a câmera atual enquadra o portão |
| Anti-tremor | Zona morta de ±3,5% da largura | Mesma garantia das 3 linhas antigas, com 1 parâmetro |
| Enquadramento | Câmera apontada para a entrada | Resolve fisicamente o que a ROI compensava em software |
| Base de tempo da contagem | Tempo do vídeo, não da CPU | Reprodutibilidade entre execuções e hardwares |
| Armazenamento de imagem | Inexistente no código | Conformidade estrutural com a LGPD |
