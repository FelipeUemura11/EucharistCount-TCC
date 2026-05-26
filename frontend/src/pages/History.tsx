import {
  Download,
  Filter,
  Search,
} from 'lucide-react';
import PageHeader from '../components/layout/PageHeader';

interface HistoryRecord {
  id: number;
  date: string;
  weekday: string;
  celebration: string;
  startTime: string;
  totalPeople: number;
  estimatedCommunicants: number;
  suggestedHosts: number;
  entries: number;
  exits: number;
}

const historyRecords: HistoryRecord[] = [
  {
    id: 1,
    date: '24/05/2026',
    weekday: 'Domingo',
    celebration: 'Missa das 19h',
    startTime: '19:00',
    totalPeople: 184,
    estimatedCommunicants: 178,
    suggestedHosts: 196,
    entries: 207,
    exits: 23,
  },
  {
    id: 2,
    date: '24/05/2026',
    weekday: 'Domingo',
    celebration: 'Missa principal',
    startTime: '10:00',
    totalPeople: 172,
    estimatedCommunicants: 165,
    suggestedHosts: 182,
    entries: 188,
    exits: 16,
  },
  {
    id: 3,
    date: '21/05/2026',
    weekday: 'Quinta-feira',
    celebration: 'Missa de quinta-feira',
    startTime: '19:30',
    totalPeople: 85,
    estimatedCommunicants: 80,
    suggestedHosts: 88,
    entries: 96,
    exits: 11,
  },
  {
    id: 4,
    date: '17/05/2026',
    weekday: 'Domingo',
    celebration: 'Missa das 19h',
    startTime: '19:00',
    totalPeople: 167,
    estimatedCommunicants: 159,
    suggestedHosts: 175,
    entries: 198,
    exits: 31,
  },
];


export default function History() {

  return (
    <div>
      <PageHeader title="Histórico" isActive={false} />

      <main className="min-w-0 flex-1 overflow-x-hidden px-8 pt-7 pb-10 max-[640px]:px-4">
        <section className="mb-6 rounded-lg border border-border bg-white p-5 shadow-sm">
          <div className="grid grid-cols-[minmax(0,1fr)_180px_180px_auto] items-end gap-4 max-[1100px]:grid-cols-2 max-[640px]:grid-cols-1">
            <label className="flex min-w-0 flex-col gap-2">
              <span className="text-xs font-bold uppercase text-text-muted">Buscar celebração</span>
              <div className="flex min-w-0 items-center gap-2 rounded-lg border border-border bg-white px-3 py-2.5">
                <Search size={18} className="text-text-muted" />
                <input
                  className="min-w-0 w-full border-0 bg-transparent text-sm text-text-dark outline-none"
                  placeholder="Missa das 19h"
                />
              </div>
            </label>

            <label className="flex min-w-0 flex-col gap-2">
              <span className="text-xs font-bold uppercase text-text-muted">Período</span>
              <select className="rounded-lg border border-border bg-white px-3 py-2.5 text-sm font-semibold text-text-dark outline-none">
                <option>Últimos 7 dias</option>
                <option>Últimos 30 dias</option>
                <option>Últimos 90 dias</option>
              </select>
            </label>

            <button
              type="button"
              className="flex items-center justify-center gap-2 rounded-lg bg-secondary px-4 py-2.5 text-sm font-bold text-white shadow-sm transition hover:bg-secondary/90"
            >
              <Filter size={18} />
              Filtrar
            </button>
          </div>
        </section>

        <section className="min-w-0">
          <div className="min-w-0 rounded-lg border border-border bg-white p-6 shadow-sm">
            <div className="mb-5 flex items-center justify-between gap-4 max-[640px]:items-start max-[640px]:flex-col">
              <div className="min-w-0">
                <h3 className="m-0 text-base font-bold text-text-dark">Registros de celebrações</h3>
                <p className="m-0 mt-1 text-sm text-text-muted">Dados consolidados após o encerramento da contagem</p>
              </div>

              <button type="button" className="flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm font-bold text-text-dark hover:bg-app-bg">
                <Download size={17} />
                Exportar
              </button>
            </div>

            <div className="max-w-full overflow-x-auto rounded-xl">
              <table className="w-full border-collapse text-left">
                <thead>
                  <tr className="bg-primary/10 border-b border-border-light text-xs uppercase text-text-muted">
                    <th className="p-4 font-bold">Data</th>
                    <th className="p-4 font-bold">Celebração</th>
                    <th className="p-4 font-bold">Total de pessoas</th>
                    <th className="p-4 font-bold">Estimativa para comunhão</th>
                    <th className="p-4 font-bold">Hóstias sugeridas</th>
                    <th className="p-4 font-bold">Entradas</th>
                    <th className="p-4 font-bold">Saídas</th>
                  </tr>
                </thead>
                <tbody>
                  {historyRecords.map((record) => (
                    <tr
                      key={record.id}
                      className="border-b border-border-light transition last:border-0 hover:bg-app-bg"
                    >
                      <td className="p-4 text-sm font-semibold text-text-dark">{record.date}</td>
                      <td className="p-4">
                        <p className="m-0 text-sm font-bold text-text-dark">{record.celebration}</p>
                        <p className="m-0 mt-0.5 text-xs text-text-muted">{record.weekday}, {record.startTime}</p>
                      </td>
                      <td className="p-4 text-sm font-semibold text-text-dark">{record.totalPeople}</td>
                      <td className="p-4 text-sm font-semibold text-secondary">{record.estimatedCommunicants}</td>
                      <td className="p-4 text-sm font-semibold text-primary">{record.suggestedHosts}</td>
                      <td className="p-4 text-sm text-text-dark">{record.entries}</td>
                      <td className="p-4 text-sm text-text-dark">{record.exits}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
