import { Clock3, Pencil, Plus, Trash2 } from 'lucide-react';
import type { Celebracao, StatusCelebracao } from '../../types/celebrations';

interface ModalHorariosDiaProps {
  dateLabel: string;
  celebracoes: Celebracao[];
  onClose: () => void;
  onNovaCelebracao: () => void;
  onCancelar: (celebracao: Celebracao) => void;
  onEditar: (celebracao: Celebracao) => void;
}

const statusLabel: Record<StatusCelebracao, string> = {
  agendada: 'Agendada',
  em_andamento: 'Em andamento',
  finalizada: 'Finalizada',
  cancelada: 'Cancelada',
};

const statusStyle: Record<StatusCelebracao, string> = {
  agendada: 'bg-secondary/10 text-secondary',
  em_andamento: 'bg-emerald-50 text-emerald-600',
  finalizada: 'bg-border-light text-text-muted',
  cancelada: 'bg-red-50 text-red-600',
};

export default function ModalHorariosDia({
  dateLabel,
  celebracoes,
  onClose,
  onNovaCelebracao,
  onCancelar,
  onEditar,
}: ModalHorariosDiaProps) {
  return (
    <div className="fixed inset-0 z-100 flex items-center justify-center bg-black/40 px-4 py-6">
      <section className="max-h-full w-full max-w-3xl overflow-y-auto rounded-lg bg-white shadow-sm">
        <div className="border-b border-border p-6">
          <p className="m-0 text-sm font-semibold uppercase text-text-muted">Celebrações do dia</p>
          <h3 className="m-0 mt-1 text-2xl font-extrabold text-text-dark">{dateLabel}</h3>
        </div>

        <div className="p-6">
          <div className="mb-5 flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="flex size-11 items-center justify-center rounded-lg bg-secondary/10 text-secondary">
                <Clock3 size={22} />
              </div>
              <p className="m-0 text-sm text-text-muted">
                {celebracoes.length === 0
                  ? 'Nenhuma celebração cadastrada neste dia'
                  : `${celebracoes.length} celebração(ões) neste dia`}
              </p>
            </div>

            <button
              type="button"
              onClick={onNovaCelebracao}
              className="flex items-center gap-2 rounded-lg bg-secondary px-4 py-2.5 text-sm font-bold text-white shadow-sm transition hover:bg-secondary/90"
            >
              <Plus size={18} />
              Nova celebração
            </button>
          </div>

          {celebracoes.length === 0 ? (
            <p className="m-0 rounded-lg border border-dashed border-border bg-app-bg p-4 text-sm font-semibold text-text-muted">
              Nenhuma missa neste dia. Use "Nova celebração" para cadastrar uma missa fora da rotina.
            </p>
          ) : (
            <div className="flex flex-col gap-3">
              {celebracoes.map((celebracao) => (
                <article key={`${celebracao.data}-${celebracao.horarioMissa}`} className="rounded-lg border border-border bg-app-bg p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <h4 className="m-0 truncate text-base font-bold text-text-dark">{celebracao.titulo}</h4>
                      {celebracao.horarioPadraoId !== null && (
                        <p className="m-0 text-xs font-semibold uppercase text-text-muted">Rotina semanal</p>
                      )}
                      <p className="m-0 mt-1 text-sm text-text-muted">
                        Missa às {celebracao.horarioMissa} · gravação {celebracao.inicioMonitoramento || '—'} às {celebracao.fimMonitoramento || '—'}
                      </p>
                    </div>

                    <div className="flex shrink-0 flex-wrap items-center justify-end gap-2">
                      <span className={`rounded-full px-3 py-1 text-xs font-bold ${statusStyle[celebracao.status]}`}>
                        {statusLabel[celebracao.status]}
                      </span>
                      {/* Só a agendada muda: em andamento e finalizada já têm contagem. Na rotina, vale só para este dia. */}
                      {celebracao.status === 'agendada' && (
                        <>
                          <button
                            type="button"
                            onClick={() => onEditar(celebracao)}
                            className="flex items-center gap-2 rounded-lg border border-border bg-white px-3 py-2 text-sm font-bold text-text-dark hover:bg-border-light"
                          >
                            <Pencil size={16} />
                            {celebracao.horarioPadraoId !== null ? 'Alterar neste dia' : 'Editar'}
                          </button>
                          <button
                            type="button"
                            onClick={() => onCancelar(celebracao)}
                            className="flex items-center gap-2 rounded-lg border border-red-100 bg-white px-3 py-2 text-sm font-bold text-red-600 hover:bg-red-50"
                          >
                            <Trash2 size={16} />
                            {celebracao.horarioPadraoId !== null ? 'Cancelar neste dia' : 'Cancelar'}
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>

        <div className="flex justify-end border-t border-border p-6">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-border px-4 py-2.5 text-sm font-bold text-text-dark transition hover:bg-app-bg"
          >
            Fechar
          </button>
        </div>
      </section>
    </div>
  );
}
