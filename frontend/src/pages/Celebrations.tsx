import {
  CalendarDays,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  DoorOpen,
  Plus,
  Users,
  Video,
} from 'lucide-react';
import PageHeader from '../components/layout/PageHeader';

type CelebrationStatus = 'scheduled' | 'active' | 'finished';

interface Celebration {
  id: number;
  title: string;
  day: number;
  weekday: string;
  startTime: string;
  monitorStart: string;
  monitorEnd: string;
  door: string;
  expectedPeople: number;
  capacity: number;
  status: CelebrationStatus;
}

interface CalendarDay {
  day?: number;
  hasCelebration?: boolean;
  isSelected?: boolean;
  isToday?: boolean;
}

const weekDays = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];

const calendarDays: CalendarDay[] = [
  {}, {}, {}, {}, {}, { day: 1 }, { day: 2 },
  { day: 3 }, { day: 4 }, { day: 5 }, { day: 6 }, { day: 7 }, { day: 8 }, { day: 9 },
  { day: 10 }, { day: 11 }, { day: 12 }, { day: 13 }, { day: 14 }, { day: 15 }, { day: 16 },
  { day: 17 }, { day: 18 }, { day: 19, hasCelebration: true }, { day: 20 }, { day: 21, hasCelebration: true }, { day: 22 }, { day: 23 },
  { day: 24, hasCelebration: true, isSelected: true, isToday: true }, { day: 25 }, { day: 26 }, { day: 27, hasCelebration: true }, { day: 28 }, { day: 29 }, { day: 30 },
  { day: 31, hasCelebration: true },
];

const selectedDayCelebrations: Celebration[] = [
  {
    id: 1,
    title: 'Missa da manhã',
    day: 24,
    weekday: 'Domingo',
    startTime: '08:00',
    monitorStart: '07:30',
    monitorEnd: '08:20',
    door: 'Entrada principal',
    expectedPeople: 120,
    capacity: 300,
    status: 'finished',
  },
  {
    id: 2,
    title: 'Missa principal',
    day: 24,
    weekday: 'Domingo',
    startTime: '10:00',
    monitorStart: '09:30',
    monitorEnd: '10:20',
    door: 'Entrada principal',
    expectedPeople: 210,
    capacity: 300,
    status: 'finished',
  },
  {
    id: 3,
    title: 'Missa das 19h',
    day: 24,
    weekday: 'Domingo',
    startTime: '19:00',
    monitorStart: '18:30',
    monitorEnd: '19:20',
    door: 'Entrada principal',
    expectedPeople: 240,
    capacity: 300,
    status: 'scheduled',
  },
];

const nextCelebrations: Celebration[] = [
  selectedDayCelebrations[2],
  {
    id: 4,
    title: 'Missa de quarta-feira',
    day: 27,
    weekday: 'Quarta-feira',
    startTime: '19:30',
    monitorStart: '19:00',
    monitorEnd: '19:50',
    door: 'Entrada lateral',
    expectedPeople: 90,
    capacity: 180,
    status: 'scheduled',
  },
  {
    id: 5,
    title: 'Missa de domingo',
    day: 31,
    weekday: 'Domingo',
    startTime: '10:00',
    monitorStart: '09:30',
    monitorEnd: '10:20',
    door: 'Entrada principal',
    expectedPeople: 230,
    capacity: 300,
    status: 'scheduled',
  },
];

const statusStyle: Record<CelebrationStatus, string> = {
  scheduled: 'bg-secondary/10 text-secondary',
  active: 'bg-emerald-50 text-emerald-600',
  finished: 'bg-slate-100 text-slate-600',
};

const statusLabel: Record<CelebrationStatus, string> = {
  scheduled: 'Agendada',
  active: 'Em andamento',
  finished: 'Finalizada',
};

export default function Celebrations() {
  return (
    <div>
      <PageHeader title="Celebrações" isActive={false} lastUpdate="--:--" showStatus={false} />

      <main className="flex-1 px-8 pt-7 pb-10">
        <div className="mb-6 flex items-center justify-between gap-4">
          <div>
            <p className="m-0 text-sm font-semibold uppercase text-text-muted">Agenda litúrgica</p>
            <h2 className="m-0 mt-1 text-2xl font-extrabold text-text-dark">Maio de 2026</h2>
          </div>

          <button
            type="button"
            className="flex items-center gap-2 rounded-lg bg-secondary px-4 py-2.5 text-sm font-bold text-white shadow-sm transition hover:bg-secondary/90"
          >
            <Plus size={18} />
            Nova celebração
          </button>
        </div>

        <section className="grid grid-cols-[1fr_390px] gap-6 max-[1180px]:grid-cols-1">
          <div className="rounded-lg border border-border bg-white p-6 shadow-sm">
            <div className="mb-5 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-secondary/10 text-secondary">
                  <CalendarDays size={24} />
                </div>
                <div>
                  <h3 className="m-0 text-base font-bold text-text-dark">Calendário</h3>
                  <p className="m-0 text-sm text-text-muted">Dias com celebrações destacadas</p>
                </div>
              </div>

              <div className="flex gap-2">
                <button type="button" className="flex h-9 w-9 items-center justify-center rounded-lg border border-border text-text-muted hover:bg-app-bg">
                  <ChevronLeft size={18} />
                </button>
                <button type="button" className="flex h-9 w-9 items-center justify-center rounded-lg border border-border text-text-muted hover:bg-app-bg">
                  <ChevronRight size={18} />
                </button>
              </div>
            </div>

            <div className="grid grid-cols-7 gap-2">
              {weekDays.map((day) => (
                <div key={day} className="py-2 text-center text-xs font-bold uppercase text-text-muted">
                  {day}
                </div>
              ))}

              {calendarDays.map((item, index) => (
                <button
                  key={`${item.day ?? 'blank'}-${index}`}
                  type="button"
                  disabled={!item.day}
                  className={`relative flex aspect-square min-h-14 items-center justify-center rounded-lg border text-sm font-bold transition ${
                    !item.day
                      ? 'cursor-default border-transparent bg-transparent'
                      : item.isSelected
                        ? 'border-secondary bg-secondary text-white shadow-sm'
                        : 'border-border bg-white text-text-dark hover:border-secondary/30 hover:bg-secondary/10'
                  }`}
                >
                  {item.day}
                  {item.hasCelebration && (
                    <span className={`absolute bottom-2 h-1.5 w-1.5 rounded-full ${item.isSelected ? 'bg-white' : 'bg-secondary'}`} />
                  )}
                </button>
              ))}
            </div>
          </div>

          <aside className="rounded-lg border border-border bg-white p-6 shadow-sm">
            <div className="mb-5">
              <h3 className="m-0 text-base font-bold text-text-dark">Domingo, 24 maio</h3>
              <p className="m-0 mt-1 text-sm text-text-muted">3 celebrações agendadas</p>
            </div>

            <div className="flex flex-col gap-3">
              {selectedDayCelebrations.map((celebration) => (
                <article key={celebration.id} className="rounded-lg border border-border bg-app-bg p-4">
                  <div className="mb-3 flex items-start justify-between gap-3">
                    <div>
                      <h4 className="m-0 text-sm font-bold text-text-dark">{celebration.title}</h4>
                      <p className="m-0 mt-1 text-sm text-text-muted">{celebration.startTime}</p>
                    </div>
                    <span className={`rounded-full px-3 py-1 text-xs font-bold ${statusStyle[celebration.status]}`}>
                      {statusLabel[celebration.status]}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-sm text-text-muted">
                    <span className="flex items-center gap-2">
                      <Video size={16} />
                      {celebration.monitorStart} - {celebration.monitorEnd}
                    </span>
                    <span className="flex items-center gap-2">
                      <Users size={16} />
                      {celebration.expectedPeople}/{celebration.capacity}
                    </span>
                    <span className="col-span-2 flex items-center gap-2">
                      <DoorOpen size={16} />
                      {celebration.door}
                    </span>
                  </div>
                </article>
              ))}
            </div>
          </aside>
        </section>

        <section className="mt-6 rounded-lg border border-border bg-white p-6 shadow-sm">
          <div className="mb-5 flex items-center justify-between gap-4">
            <div>
              <h3 className="m-0 text-base font-bold text-text-dark">Próximas celebrações</h3>
              <p className="m-0 mt-1 text-sm text-text-muted">Monitoramento configurado automaticamente</p>
            </div>
            <CheckCircle2 className="text-emerald-500" size={22} />
          </div>

          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-left">
              <thead>
                <tr className="border-b border-border text-xs uppercase text-text-muted">
                  <th className="py-3 pr-4 font-bold">Celebração</th>
                  <th className="py-3 pr-4 font-bold">Dia</th>
                  <th className="py-3 pr-4 font-bold">Horário</th>
                  <th className="py-3 pr-4 font-bold">Monitoramento</th>
                  <th className="py-3 pr-4 font-bold">Entrada</th>
                  <th className="py-3 font-bold">Capacidade</th>
                </tr>
              </thead>
              <tbody>
                {nextCelebrations.map((celebration) => (
                  <tr key={celebration.id} className="border-b border-border-light last:border-0">
                    <td className="py-4 pr-4 text-sm font-bold text-text-dark">{celebration.title}</td>
                    <td className="py-4 pr-4 text-sm text-text-muted">{celebration.weekday}, {celebration.day}/05</td>
                    <td className="py-4 pr-4 text-sm text-text-dark">{celebration.startTime}</td>
                    <td className="py-4 pr-4 text-sm text-text-muted">{celebration.monitorStart} - {celebration.monitorEnd}</td>
                    <td className="py-4 pr-4 text-sm text-text-muted">{celebration.door}</td>
                    <td className="py-4 text-sm font-semibold text-text-dark">{celebration.capacity}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  );
}
