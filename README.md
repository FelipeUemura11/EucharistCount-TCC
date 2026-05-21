
### Eucharist Count ###

Sistema de contagem de pessoas em tempo real utilizando **visão computacional**, desenvolvido para auxiliar igrejas católicas no monitoramento de ocupação durante celebrações litúrgicas.

O objetivo principal do projeto é fornecer uma estimativa automatizada e precisa do número de fiéis presentes, apoiando a equipe responsável no dimensionamento dos insumos eucarísticos e reduzindo falhas causadas por estimativas manuais.

---

## 📌 Visão Geral

A contagem de pessoas em ambientes fechados é uma necessidade recorrente em locais com fluxo variável de público, como igrejas, auditórios, centros de convenções, cinemas e terminais de transporte.

No contexto deste projeto, o estudo de caso será realizado em uma **igreja católica de Curitiba/PR**, onde a contagem de fiéis é essencial para estimar a quantidade adequada de hóstias a serem consagradas durante a celebração.

O sistema será executado localmente, sem envio de imagens para a nuvem, contribuindo para maior controle sobre privacidade e proteção de dados.

---

## 🎯 Objetivo Geral

Desenvolver um sistema de contagem de pessoas baseado em visão computacional, aplicado à gestão de ocupação em ambientes fechados com câmeras fixas em posição diagonal, fornecendo dados precisos e automatizados sobre a quantidade de pessoas presentes durante celebrações litúrgicas.

---

## ✅ Objetivos Específicos

- Implementar um módulo de detecção de pessoas utilizando visão computacional.
- Configurar o sistema para operar com câmeras fixas posicionadas em ângulo diagonal.
- Integrar rastreamento de múltiplos indivíduos com identificadores únicos.
- Evitar contagens duplicadas de uma mesma pessoa.
- Implementar lógica de contagem por cruzamento de linha virtual.
- Diferenciar fluxos de entrada e saída de pessoas.
- Limitar o período de contagem ao intervalo de cada celebração.
- Persistir dados de ocupação e instantâneos temporais.
- Disponibilizar um dashboard para acompanhamento em tempo real.
- Validar o sistema em uma igreja católica de Curitiba/PR.

---

## 🧠 Tecnologias Utilizadas

### Backend e Visão Computacional

- **Python**  
  Linguagem principal do sistema, escolhida pelo amplo ecossistema de inteligência artificial, visão computacional e integração com bibliotecas de processamento de vídeo.

- **YOLO — You Only Look Once**  
  Algoritmo de detecção de objetos utilizado para identificar pessoas nos quadros de vídeo em tempo quase real.

- **DeepSORT**  
  Algoritmo de rastreamento de múltiplos objetos responsável por manter a identidade de cada pessoa ao longo dos frames, reduzindo duplicidades na contagem.

- **OpenCV**  
  Biblioteca utilizada para captura, leitura e processamento dos frames de vídeo.

### Banco de Dados

- **MongoDB**  
  Banco de dados NoSQL utilizado para armazenar eventos de entrada, saída, timestamps e snapshots de ocupação.

### Frontend

- **React**  
  Biblioteca utilizada para construção da interface visual do sistema.

- **TypeScript**  
  Superset do JavaScript que adiciona tipagem estática, tornando o desenvolvimento mais seguro, organizado e fácil de manter.

- **Vite**  
  Ferramenta para criação e execução do projeto frontend com React e TypeScript de forma rápida e moderna.

---

## 🏗️ Arquitetura do Sistema

O sistema é dividido em três camadas principais:

```text
Câmera / Vídeo
      ↓
Módulo de Visão Computacional
YOLO + DeepSORT + Lógica de Contagem
      ↓
API / Persistência de Dados
Python + MongoDB
      ↓
Dashboard Web
React + TypeScript
```

### Fluxo de Funcionamento

1. A câmera captura o fluxo de pessoas na entrada da igreja.
2. O sistema processa os frames do vídeo.
3. O YOLO detecta pessoas presentes na imagem.
4. O DeepSORT atribui e mantém identificadores únicos para cada indivíduo.
5. A lógica de linha virtual identifica entradas e saídas.
6. O saldo de ocupação é atualizado em tempo real.
7. Os dados são armazenados no MongoDB.
8. O dashboard exibe a lotação atual e dados históricos para a equipe litúrgica.

---

## 📊 Estratégia de Contagem

A contagem será baseada no cruzamento de uma **linha virtual** definida na imagem da câmera.

O sistema deverá identificar a direção do movimento:

- Pessoa cruza a linha no sentido de entrada → incrementa a ocupação.
- Pessoa cruza a linha no sentido de saída → decrementa a ocupação.
- Pessoa detectada repetidamente sem cruzar a linha → não altera a contagem.

Essa estratégia evita que a simples presença de uma pessoa em vários frames gere contagens duplicadas.

---

## 💾 Persistência de Dados

O MongoDB será utilizado para armazenar documentos em formato semelhante a JSON, contendo informações como:

```json
{
  "timestamp": "2026-05-16T18:30:00Z",
  "entradas": 120,
  "saidas": 15,
  "ocupacaoAtual": 105,
  "celebracaoId": "missa-domingo-18h"
}
```

Além dos eventos de entrada e saída, o sistema poderá armazenar snapshots temporais da ocupação, por exemplo:

- 30 minutos antes da celebração;
- 15 minutos antes da celebração;
- 10 minutos antes da celebração;
- 5 minutos antes da celebração;
- durante a celebração.

---

## 🖥️ Dashboard

O dashboard será desenvolvido com React e TypeScript, permitindo que os responsáveis acompanhem a ocupação em tempo real por meio de computadores ou dispositivos móveis conectados à rede local.

### Funcionalidades previstas

- Exibição da ocupação atual.
- Quantidade de entradas e saídas.
- Histórico de ocupação por celebração.
- Visualização de snapshots temporais.
- Interface responsiva para celular, tablet e desktop.
- Atualização automática dos dados sem recarregar a página.

---

## 🔐 Privacidade e Proteção de Dados

O projeto prevê execução local, sem necessidade de envio de imagens para serviços externos em nuvem.

Essa abordagem reduz riscos relacionados à exposição de dados sensíveis e se alinha a princípios de privacidade e proteção de dados, especialmente considerando que imagens de pessoas podem ser tratadas como dados pessoais.

---

## 📁 Estrutura Sugerida do Projeto

```text
eucharist-count/
├── backend/
│   ├── app/
│   │   ├── detection/
│   │   │   ├── yolo_detector.py
│   │   │   └── tracker.py
│   │   ├── counting/
│   │   │   └── line_counter.py
│   │   ├── database/
│   │   │   └── mongo_client.py
│   │   ├── api/
│   │   │   └── routes.py
│   │   └── main.py
│   ├── requirements.txt
│   └── README.md
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── types/
│   │   └── App.tsx
│   ├── package.json
│   └── README.md
│
├── docs/
│   └── architecture.md
│
├── docker-compose.yml
└── README.md
```

---

## 🚀 Como Executar o Projeto

> Os comandos abaixo representam uma estrutura inicial sugerida para desenvolvimento.

### 1. Clonar o repositório

```bash
git clone <url-do-repositorio>
cd eucharist-count
```

### 2. Configurar o Backend

```bash
cd backend
python -m venv venv
```

Ativar o ambiente virtual:

```bash
# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

Instalar dependências:

```bash
pip install -r requirements.txt
```

Executar o backend:

```bash
python app/mainCPU.py
```

### 3. Configurar o Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## ⚙️ Variáveis de Ambiente

Exemplo de arquivo `.env` para o backend:

```env
MONGO_URI=mongodb://localhost:27017
DATABASE_NAME=eucharist_count
CAMERA_SOURCE=0
API_PORT=8000
```

Exemplo de arquivo `.env` para o frontend:

```env
VITE_API_URL=http://localhost:8000
```

---

## 🧪 Validação

A validação do sistema deverá considerar:

- Acurácia da contagem de pessoas.
- Capacidade de distinguir entradas e saídas.
- Funcionamento em ambiente fechado.
- Desempenho com câmeras em posição diagonal.
- Robustez em situações de oclusão parcial.
- Usabilidade do dashboard pela equipe litúrgica.

---

## 📚 Referências Técnicas

Este projeto é fundamentado em estudos sobre:

- Detecção de objetos com YOLO.
- Rastreamento de múltiplos objetos com DeepSORT.
- Contagem de pessoas em ambientes internos.
- Sistemas de monitoramento em tempo real.
- Interfaces web baseadas em React.
- Persistência de dados temporais com bancos NoSQL.

---

## 👥 Autores

- Felipe Yukiya Soares Uemura
- Yasmin Faraj
- Yuji Chikara Kiyota
- Eduardo Cornehl Wozniak

---

## 🎓 Instituição

**Universidade Positivo**  
Bacharelado em Ciência da Computação  
Curitiba — 2026

---

## 📄 Licença

Este projeto foi desenvolvido como proposta de Trabalho de Conclusão de Curso. A licença de uso deverá ser definida pelos autores do projeto.
