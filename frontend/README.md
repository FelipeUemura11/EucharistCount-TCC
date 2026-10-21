# Frontend — Eucharist Count

Dashboard web do sistema de contagem. React + TypeScript + Vite + Tailwind CSS.

As telas **Dashboard**, **Histórico** e **Configurações** já estão conectadas à API FastAPI em tempo real através dos módulos em `src/services/` e `src/hooks/`. A tela **Celebrações** ainda utiliza dados fictícios locais (`src/data/celebrationsMock.ts`), e a tela **Ajuda** exibe o guia visual de uso (FAQ).

## Rodar (Modo Desenvolvimento)

```bash
cd frontend
npm install
npm run dev
```

O `npm run dev` precisa do backend rodando (`python main.py`): as telas chamam a API por endereço relativo (`/api/...`), e o *proxy* do `vite.config.ts` repassa essas chamadas para `http://127.0.0.1:8000`.

> **Nota:** Em produção/demonstração on-premise, rode `npm run build`. O arquivo principal do backend (`main.py`) já serve essa pasta `dist` empacotada automaticamente na porta 8000.

## Estrutura

```
src/
├── pages/        # Dashboard, Celebrações, Histórico, Configurações e Ajuda (FAQ)
├── components/   # componentes por área (dashboard/, historico/, celebracoes/) e ErrorBoundary
├── layout/       # estrutura fixa da aplicação (AppLayout, Sidebar, HeaderPage)
├── hooks/        # busca periódica de dados (useDashboard, useHistorico, useStatusContagem)
├── services/     # integração com a API FastAPI (dashboard, historico, configuracoes)
├── data/         # valores iniciais neutros do dashboard e mocks da tela Celebrações
├── assets/       # imagens, logos e prints do sistema (faq/)
└── types/        # contratos TypeScript espelhados com backend/api/schemas.py
```

O backend de visão computacional e a API ficam em [`../backend`](../backend).
