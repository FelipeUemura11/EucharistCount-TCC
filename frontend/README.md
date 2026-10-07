# Frontend — Eucharist Count

Dashboard web do sistema de contagem. React + TypeScript + Vite.

As telas já estão conectadas à API e se comunicam em tempo real com o motor de visão através dos arquivos em `src/services/`.

## Rodar (Modo Desenvolvimento)

```bash
cd frontend
npm install
npm run dev
```

O `npm run dev` precisa do backend rodando (`python main.py`): as telas chamam a API por endereço relativo (`/api/...`), e o *proxy* do `vite.config.ts` repassa essas chamadas para `http://127.0.0.1:8000`.

> **Nota:** Em produção/demonstração on-premise, rode `npm run build`. O arquivo principal do motor (`main.py` no backend) já serve essa pasta `dist` empacotada automaticamente na porta 8000.

## Estrutura

```
src/
├── pages/        # Dashboard, Celebrações, Histórico, Configurações e Ajuda (FAQ)
├── components/   # componentes por área (dashboard/, history/, layout/...)
├── hooks/        # busca de dados e estados (ex. status do motor)
├── services/     # integração com a API FastAPI (chamadas HTTP)
├── data/         # mocks e dados fixos utilizados na estrutura visual
├── assets/       # imagens, logos e prints do sistema (faq)
└── types/        # contratos de dados compartilhados com o backend
```

O backend de visão computacional fica em [`../backend`](../backend).
