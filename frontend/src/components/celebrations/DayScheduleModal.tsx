import { Clock3, Pencil, Plus, Save, Trash2 } from 'lucide-react';
import { useState } from 'react';
import type {
  CelebrationDayInfo,
  CelebrationMassSchedule,
  CelebrationMassScheduleChanges,
} from '../../types/celebrations';

interface DayScheduleModalProps {
  dayInfo: CelebrationDayInfo;
  schedules: CelebrationMassSchedule[];
  onAddSchedule: () => void;
  onClose: () => void;
  onRemoveSchedule: (scheduleId: string) => void;
  onSave: () => void;
  onUpdateSchedule: (scheduleId: string, changes: CelebrationMassScheduleChanges) => void;
}

const timeInputClassName = 'w-full rounded-lg border border-border bg-white px-3 py-2 text-sm font-bold text-text-dark outline-none [&::-webkit-calendar-picker-indicator]:cursor-pointer';

export default function DayScheduleModal({
  dayInfo,
  schedules,
  onAddSchedule,
  onClose,
  onRemoveSchedule,
  onSave,
  onUpdateSchedule,
}: DayScheduleModalProps) {
  const [editingScheduleId, setEditingScheduleId] = useState<string | null>(null);

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 px-4 py-6">
      <section className="max-h-full w-full max-w-4xl overflow-y-auto rounded-lg bg-white shadow-sm">
        <div className="border-b border-border p-6">
          <div>
            <p className="m-0 text-sm font-semibold uppercase text-text-muted">Configuração do dia</p>
            <h3 className="m-0 mt-1 text-2xl font-extrabold text-text-dark">{dayInfo.dateLabel}</h3>
            <p className="m-0 mt-1 text-sm text-text-muted">
              Os horários abaixo partem da configuração global e podem ser ajustados para esta data.
            </p>
          </div>
        </div>

        <div className="p-6">
          <div className="mb-5 flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="flex size-11 items-center justify-center rounded-lg bg-secondary/10 text-secondary">
                <Clock3 size={22} />
              </div>
              <div>
                <h4 className="m-0 text-base font-bold text-text-dark">Horários da data</h4>
                <p className="m-0 text-sm text-text-muted">
                  {schedules.length === 0 ? 'Nenhuma missa configurada' : `${schedules.length} horário(s) configurado(s)`}
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={onAddSchedule}
              className="flex items-center gap-2 rounded-lg bg-secondary px-4 py-2.5 text-sm font-bold text-white shadow-sm transition hover:bg-secondary/90"
            >
              <Plus size={18} />
              Adicionar horário
            </button>
          </div>

          {schedules.length === 0 ? (
            <p className="m-0 rounded-lg border border-dashed border-border bg-app-bg p-4 text-sm font-semibold text-text-muted">
              A configuração global deste dia não possui missas. Adicione um horário para criar uma celebração especial nesta data.
            </p>
          ) : (
            <div className="flex flex-col gap-3">
              {schedules.map((schedule) => {
                const isEditing = editingScheduleId === schedule.id;

                return (
                  <article key={schedule.id} className="rounded-lg border border-border bg-app-bg p-4">
                    <div className="mb-4 flex items-start justify-between gap-3">
                      <div>
                        <span className="rounded-full bg-white px-3 py-1 text-xs font-bold text-text-muted">
                          {schedule.source === 'global' ? 'Configuração global' : 'Alteração desta data'}
                        </span>
                      </div>

                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => setEditingScheduleId(isEditing ? null : schedule.id)}
                          className="flex items-center gap-2 rounded-lg border border-border bg-white px-3 py-2 text-sm font-bold text-text-dark hover:bg-border-light"
                        >
                          <Pencil size={16} />
                          {isEditing ? 'Concluir' : 'Alterar'}
                        </button>
                        <button
                          type="button"
                          onClick={() => onRemoveSchedule(schedule.id)}
                          className="flex items-center gap-2 rounded-lg border border-red-100 bg-white px-3 py-2 text-sm font-bold text-red-600 hover:bg-red-50"
                        >
                          <Trash2 size={16} />
                          Remover
                        </button>
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-3">
                      <label className="flex flex-col gap-2">
                        <span className="text-xs font-bold uppercase text-text-muted">Horário da missa</span>
                        <input
                          type="time"
                          value={schedule.startTime}
                          disabled={!isEditing}
                          onChange={(event) => onUpdateSchedule(schedule.id, { startTime: event.target.value })}
                          className={`${timeInputClassName} ${isEditing ? '' : 'bg-border-light text-text-muted'}`}
                        />
                      </label>

                      <label className="flex flex-col gap-2">
                        <span className="text-xs font-bold uppercase text-text-muted">Início da gravação</span>
                        <input
                          type="time"
                          value={schedule.recordingStartTime}
                          disabled={!isEditing}
                          onChange={(event) => onUpdateSchedule(schedule.id, { recordingStartTime: event.target.value })}
                          className={`${timeInputClassName} ${isEditing ? '' : 'bg-border-light text-text-muted'}`}
                        />
                      </label>

                      <label className="flex flex-col gap-2">
                        <span className="text-xs font-bold uppercase text-text-muted">Fim da gravação</span>
                        <input
                          type="time"
                          value={schedule.recordingEndTime}
                          disabled={!isEditing}
                          onChange={(event) => onUpdateSchedule(schedule.id, { recordingEndTime: event.target.value })}
                          className={`${timeInputClassName} ${isEditing ? '' : 'bg-border-light text-text-muted'}`}
                        />
                      </label>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </div>

        <div className="flex justify-end gap-3 border-t border-border p-6">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-border px-4 py-2.5 text-sm font-bold text-text-dark transition hover:bg-app-bg"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={onSave}
            className="flex items-center gap-2 rounded-lg bg-secondary px-4 py-2.5 text-sm font-bold text-white shadow-sm transition hover:bg-secondary/90"
          >
            <Save size={18} />
            Salvar alterações
          </button>
        </div>
      </section>
    </div>
  );
}
