import {
  CalendarDays,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Plus,
  Users,
  Video,
} from 'lucide-react';
import PageHeader from '../components/layout/PageHeader';
import { weekDays, calendarDays, selectedDayCelebrations, nextCelebrations, statusStyle, statusLabel } from '../data/celebrationsMock';

export default function Celebrations() {
  return (
    <div>
      <PageHeader title="Celebrações" isActive={false} />

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
                  className={`relative flex aspect-square min-h-0 items-center justify-center rounded-lg border text-sm font-bold transition ${
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
