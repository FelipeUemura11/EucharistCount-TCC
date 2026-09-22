# Frontend — Eucharist Count

Dashboard web do sistema de contagem. React + TypeScript + Vite.

Ainda **não integrado à API** — as telas consomem os mocks de
`src/data/` através dos hooks em `src/hooks/`. A troca por chamadas HTTP
reais acontece dentro de `src/services/`, sem alterar as páginas.

## Rodar

```bash
cd frontend
npm install
npm run dev
```

## Estrutura

```
src/
├── pages/        # Dashboard, Celebrações, Histórico, Configurações
├── components/   # componentes por área (dashboard/, history/, layout/...)
├── hooks/        # busca de dados das páginas
├── services/     # ponto de troca mock -> API
├── data/         # mocks enquanto a API não existe
└── types/        # contratos de dados compartilhados
```

O backend de visão computacional fica em [`../backend`](../backend).
