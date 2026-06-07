import { CalendarDays } from 'lucide-react';
import type { MassScheduleChanges, WeekdayId, WeeklyScheduleDay } from '../../types/settings';

interface WeeklyMassScheduleSectionProps {
  weeklySchedule: WeeklyScheduleDay[];
  onMassChange: (dayId: WeekdayId, massId: string, changes: MassScheduleChanges) => void;
}

const timeInputClassName = 'w-full rounded-lg border border-border bg-white px-3 py-2 text-sm font-bold text-text-dark outline-none [&::-webkit-calendar-picker-indicator]:cursor-pointer';

function getMassCountLabel(count: number) {
  if (count === 0) {
    return 'Sem missa';
  }

  return count === 1 ? '1 missa' : `${count} missas`;
}

export default function WeeklyMassScheduleSection({
  weeklySchedule,
  onMassChange,
}: WeeklyMassScheduleSectionProps) {
  return (
    <section className="mb-6 rounded-lg border border-border bg-white p-6 shadow-sm">
      <div className="mb-5 flex items-center gap-3">
        <div className="flex size-11 items-center justify-center rounded-lg bg-secondary/10 text-secondary">
          <CalendarDays size={24} />
        </div>
        <div>
          <h3 className="m-0 text-base font-bold text-text-dark">Agenda semanal de missas</h3>
          <p className="m-0 text-sm text-text-muted">Horário da missa e período de gravação por dia da semana</p>
        </div>
      </div>

      <div className="flex flex-col gap-4">
        {weeklySchedule.map((day) => (
          <article key={day.id} className="rounded-lg border border-border bg-app-bg p-4">
            <div className="mb-4 flex items-start justify-between gap-3">
              <div className="min-w-0">
                <h4 className="m-0 text-sm font-bold text-text-dark">{day.label}</h4>
                <p className="m-0 mt-1 text-xs text-text-muted">{day.helper}</p>
              </div>
              <span
                className={`shrink-0 rounded-full px-3 py-1 text-xs font-bold ${
                  day.masses.length > 0
                    ? 'bg-secondary/10 text-secondary'
                    : 'bg-slate-100 text-slate-500'
                }`}
              >
                {getMassCountLabel(day.masses.length)}
              </span>
            </div>

            {day.masses.length === 0 ? (
              <p className="m-0 rounded-lg border border-dashed border-border bg-white p-4 text-sm font-semibold text-text-muted">
                Nenhuma missa fixa cadastrada para este dia.
              </p>
            ) : (
              <div className="flex flex-col gap-3">
                {day.masses.map((mass) => (
                  <div
                    key={mass.id}
                    className="grid grid-cols-3 items-end gap-3"
                  >
                    <label className="flex min-w-0 flex-col gap-2">
                      <span className="text-xs font-bold uppercase text-text-muted">Horário da missa</span>
                      <input
                        type="time"
                        value={mass.startTime}
                        onChange={(event) =>
                          onMassChange(day.id, mass.id, { startTime: event.target.value })
                        }
                        className={timeInputClassName}
                      />
                    </label>

                    <label className="flex min-w-0 flex-col gap-2">
                      <span className="text-xs font-bold uppercase text-text-muted">Início da gravação</span>
                      <input
                        type="time"
                        value={mass.recordingStartTime}
                        onChange={(event) =>
                          onMassChange(day.id, mass.id, { recordingStartTime: event.target.value })
                        }
                        className={timeInputClassName}
                      />
                    </label>

                    <label className="flex min-w-0 flex-col gap-2">
                      <span className="text-xs font-bold uppercase text-text-muted">Fim da gravação</span>
                      <input
                        type="time"
                        value={mass.recordingEndTime}
                        onChange={(event) =>
                          onMassChange(day.id, mass.id, { recordingEndTime: event.target.value })
                        }
                        className={timeInputClassName}
                      />
                    </label>
                  </div>
                ))}
              </div>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}