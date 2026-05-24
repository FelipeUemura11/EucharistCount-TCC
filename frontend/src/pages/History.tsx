import { useMemo, useState } from 'react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  Church,
  Clock3,
  Download,
  Filter,
  Search,
  TrendingUp,
  Users,
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
  door: string;
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
    door: 'Entrada principal',
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
    door: 'Entrada principal',
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
    door: 'Entrada lateral',
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
    door: 'Entrada principal',
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

const summaryCards = [
  { label: 'Missas registradas', value: '24', icon: Church },
  { label: 'Média de público', value: '176', icon: Users },
  { label: 'Maior pico', value: '241', icon: TrendingUp },
  { label: 'Duração média', value: '52 min', icon: Clock3 },
];

export default function History() {
  const [selectedRecordId, setSelectedRecordId] = useState(historyRecords[0].id);

  const selectedRecord = useMemo(
    () => historyRecords.find((record) => record.id === selectedRecordId) ?? historyRecords[0],
    [selectedRecordId],
  );

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

            <label className="flex min-w-0 flex-col gap-2">
              <span className="text-xs font-bold uppercase text-text-muted">Entrada</span>
              <select className="rounded-lg border border-border bg-white px-3 py-2.5 text-sm font-semibold text-text-dark outline-none">
                <option>Todas</option>
                <option>Entrada principal</option>
                <option>Entrada lateral</option>
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

        <section className="mb-6 grid grid-cols-4 gap-5 max-[1180px]:grid-cols-2 max-[640px]:grid-cols-1">
          {summaryCards.map((card) => (
            <article key={card.label} className="min-w-0 rounded-lg border border-border bg-white p-5 shadow-sm">
              <div className="flex flex-row items-start gap-2">
                <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-lg bg-secondary/10 text-secondary">
                  <card.icon size={24} />
                </div>
                <div className="flex flex-col items-start gap-1 pl-4">
                  <p className="m-0 text-xs font-bold uppercase text-text-muted">{card.label}</p>
                  <p className="m-0 mt-1 text-3xl font-extrabold text-text-dark">{card.value}</p>
                </div>
              </div>
            </article>
          ))}
        </section>

        <section className="grid min-w-0 grid-cols-[minmax(0,1fr)_minmax(320px,380px)] gap-6 max-[1450px]:grid-cols-1">
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

            <div className="max-w-full overflow-x-auto">
              <table className="w-full min-w-[760px] border-collapse text-left">
                <thead>
                  <tr className="border-b border-border text-xs uppercase text-text-muted">
                    <th className="py-3 pr-4 font-bold">Data</th>
                    <th className="py-3 pr-4 font-bold">Celebração</th>
                    <th className="py-3 pr-4 font-bold">Entradas</th>
                    <th className="py-3 pr-4 font-bold">Saídas</th>
                    <th className="py-3 pr-4 font-bold">Pico</th>
                    <th className="py-3 pr-4 font-bold">Final</th>
                    <th className="py-3 font-bold">Duração</th>
                  </tr>
                </thead>
                <tbody>
                  {historyRecords.map((record) => (
                    <tr
                      key={record.id}
                      className={`cursor-pointer border-b border-border-light transition last:border-0 ${
                        selectedRecordId === record.id ? 'bg-secondary/10' : 'hover:bg-app-bg'
                      }`}
                      onClick={() => setSelectedRecordId(record.id)}
                    >
                      <td className="py-4 pr-4 text-sm font-semibold text-text-dark">{record.date}</td>
                      <td className="py-4 pr-4">
                        <p className="m-0 text-sm font-bold text-text-dark">{record.celebration}</p>
                        <p className="m-0 mt-0.5 text-xs text-text-muted">{record.weekday}, {record.startTime}</p>
                      </td>
                      <td className="py-4 pr-4 text-sm text-text-dark">{record.entries}</td>
                      <td className="py-4 pr-4 text-sm text-text-dark">{record.exits}</td>
                      <td className="py-4 pr-4 text-sm font-semibold text-secondary">{record.peak}</td>
                      <td className="py-4 pr-4 text-sm font-semibold text-text-dark">{record.finalOccupancy}</td>
                      <td className="py-4 text-sm text-text-muted">{record.duration}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <aside className="min-w-0 rounded-lg border border-border bg-white p-6 shadow-sm">
            <div className="mb-5">
              <h3 className="m-0 text-base font-bold text-text-dark">Resumo selecionado</h3>
              <p className="m-0 mt-1 text-sm text-text-muted">{selectedRecord.date} - {selectedRecord.celebration}</p>
            </div>

            <div className="mb-5 h-56">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={selectedRecord.occupancyData} margin={{ top: 12, right: 12, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="historyOccupancy" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="var(--color-secondary)" stopOpacity={0.28} />
                      <stop offset="95%" stopColor="var(--color-secondary)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="#e5e7eb" strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{ fill: '#9ca3af', fontSize: 11 }} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fill: '#9ca3af', fontSize: 11 }} />
                  <Tooltip />
                  <Area type="monotone" dataKey="value" stroke="var(--color-secondary)" strokeWidth={3} fill="url(#historyOccupancy)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-lg bg-app-bg p-4">
                <p className="m-0 text-xs font-bold uppercase text-text-muted">Entrada</p>
                <p className="m-0 mt-1 text-sm font-bold text-text-dark">{selectedRecord.door}</p>
              </div>
              <div className="rounded-lg bg-app-bg p-4">
                <p className="m-0 text-xs font-bold uppercase text-text-muted">Pico</p>
                <p className="m-0 mt-1 text-sm font-bold text-text-dark">{selectedRecord.peak} pessoas</p>
              </div>
              <div className="rounded-lg bg-app-bg p-4">
                <p className="m-0 text-xs font-bold uppercase text-text-muted">Entradas</p>
                <p className="m-0 mt-1 text-sm font-bold text-text-dark">{selectedRecord.entries}</p>
              </div>
              <div className="rounded-lg bg-app-bg p-4">
                <p className="m-0 text-xs font-bold uppercase text-text-muted">Saídas</p>
                <p className="m-0 mt-1 text-sm font-bold text-text-dark">{selectedRecord.exits}</p>
              </div>
            </div>
          </aside>
        </section>
      </main>
    </div>
  );
}
