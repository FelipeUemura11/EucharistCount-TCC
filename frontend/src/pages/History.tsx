import {
  Download,
  Filter,
  Search,
} from 'lucide-react';
import PageHeader from '../components/layout/PageHeader';

interface HistoryDataPoint {
  time: string;
  value: number;
}

interface HistoryRecord {
  id: number;
  date: string;
  weekday: string;
  celebration: string;
  startTime: string;
  duration: string;
  entries: number;
  exits: number;
  peak: number;
  finalOccupancy: number;
  occupancyData: HistoryDataPoint[];
}

const historyRecords: HistoryRecord[] = [
  {
    id: 1,
    date: '24/05/2026',
    weekday: 'Domingo',
    celebration: 'Missa das 19h',
    startTime: '19:00',
    duration: '52 min',
    entries: 207,
    exits: 23,
    peak: 192,
    finalOccupancy: 184,
    occupancyData: [
      { time: '18:30', value: 45 },
      { time: '18:45', value: 96 },
      { time: '18:50', value: 132 },
      { time: '18:55', value: 170 },
      { time: '19:00', value: 184 },
      { time: '19:10', value: 192 },
    ],
  },
  {
    id: 2,
    date: '24/05/2026',
    weekday: 'Domingo',
    celebration: 'Missa principal',
    startTime: '10:00',
    duration: '48 min',
    entries: 188,
    exits: 16,
    peak: 181,
    finalOccupancy: 172,
    occupancyData: [
      { time: '09:30', value: 38 },
      { time: '09:45', value: 88 },
      { time: '09:50', value: 129 },
      { time: '09:55', value: 164 },
      { time: '10:00', value: 172 },
      { time: '10:10', value: 181 },
    ],
  },
  {
    id: 3,
    date: '21/05/2026',
    weekday: 'Quinta-feira',
    celebration: 'Missa de quinta-feira',
    startTime: '19:30',
    duration: '43 min',
    entries: 96,
    exits: 11,
    peak: 91,
    finalOccupancy: 85,
    occupancyData: [
      { time: '19:00', value: 18 },
      { time: '19:10', value: 34 },
      { time: '19:20', value: 67 },
      { time: '19:30', value: 85 },
      { time: '19:40', value: 91 },
    ],
  },
  {
    id: 4,
    date: '17/05/2026',
    weekday: 'Domingo',
    celebration: 'Missa das 19h',
    startTime: '19:00',
    duration: '50 min',
    entries: 198,
    exits: 31,
    peak: 181,
    finalOccupancy: 167,
    occupancyData: [
      { time: '18:30', value: 41 },
      { time: '18:45', value: 92 },
      { time: '18:50', value: 124 },
      { time: '18:55', value: 158 },
      { time: '19:00', value: 167 },
      { time: '19:10', value: 181 },
    ],
  },
];


export default function History() {

  return (
    <div>
      <PageHeader title="Histórico" isActive={false} lastUpdate="--:--" showStatus={false} />

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
                <option>Últimos 30 dias</option>
                <option>Últimos 7 dias</option>
                <option>Este mês</option>
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
                    <th className="p-4 font-bold">Entradas</th>
                    <th className="p-4 font-bold">Saídas</th>
                    <th className="p-4 font-bold">Pico</th>
                    <th className="p-4 font-bold">Final</th>
                    <th className="p-4 font-bold">Duração</th>
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
                      <td className="p-4 text-sm text-text-dark">{record.entries}</td>
                      <td className="p-4 text-sm text-text-dark">{record.exits}</td>
                      <td className="p-4 text-sm font-semibold text-secondary">{record.peak}</td>
                      <td className="p-4 text-sm font-semibold text-text-dark">{record.finalOccupancy}</td>
                      <td className="p-4 text-sm text-text-muted">{record.duration}</td>
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
