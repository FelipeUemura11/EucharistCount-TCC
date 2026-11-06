import { Save } from 'lucide-react';
import { useState, type FormEvent } from 'react';
import type { CelebracaoCriar, TipoCelebracao } from '../../types/celebrations';

interface ModalNovaCelebracaoProps {
  dataInicial: string; // "YYYY-MM-DD"
  hoje: string; // "YYYY-MM-DD", limite minimo do campo de data
  onClose: () => void;
  // Rejeita com Error(mensagem) quando o backend recusa; a mensagem aparece no formulário.
  onSalvar: (corpo: CelebracaoCriar) => Promise<void>;
}

const tipos: { value: TipoCelebracao; label: string }[] = [
  { value: 'comum', label: 'Comum' },
  { value: 'especial', label: 'Especial' },
  { value: 'natal', label: 'Natal' },
  { value: 'pascoa', label: 'Páscoa' },
  { value: 'casamento', label: 'Casamento' },
  { value: 'exequias', label: 'Exéquias' },
];

const inputClassName = 'w-full rounded-lg border border-border bg-white px-3 py-2 text-sm font-semibold text-text-dark outline-none focus:border-secondary';

export default function ModalNovaCelebracao({ dataInicial, hoje, onClose, onSalvar }: ModalNovaCelebracaoProps) {
  const [corpo, setCorpo] = useState<CelebracaoCriar>({
    titulo: '',
    tipo: 'comum',
    data: dataInicial,
    horarioMissa: '19:00',
    inicioGravacao: '18:30',
    fimGravacao: '20:00',
    repetirSemanalmente: false,
  });
  const [erro, setErro] = useState<string | null>(null);
  const [salvando, setSalvando] = useState(false);

  const alterar = (campos: Partial<CelebracaoCriar>) => setCorpo((atual) => ({ ...atual, ...campos }));

  const enviar = async (evento: FormEvent) => {
    evento.preventDefault();

    // Mesmas regras do backend, checadas antes para responder sem ir à rede.
    if (!corpo.titulo.trim()) {
      setErro('Informe o título da celebração.');
      return;
    }
    if (corpo.fimGravacao <= corpo.inicioGravacao) {
      setErro('O fim da gravação deve ser depois do início.');
      return;
    }

    setSalvando(true);
    try {
      await onSalvar({ ...corpo, titulo: corpo.titulo.trim() });
    } catch (error) {
      setErro(error instanceof Error ? error.message : 'Erro ao salvar a celebração.');
      setSalvando(false);
    }
  };

  return (
    <div className="fixed inset-0 z-100 flex items-center justify-center bg-black/40 px-4 py-6">
      <form onSubmit={enviar} className="max-h-full w-full max-w-2xl overflow-y-auto rounded-lg bg-white shadow-sm">
        <div className="border-b border-border p-6">
          <p className="m-0 text-sm font-semibold uppercase text-text-muted">Fora da agenda semanal</p>
          <h3 className="m-0 mt-1 text-2xl font-extrabold text-text-dark">Nova celebração</h3>
          <p className="m-0 mt-1 text-sm text-text-muted">
            A contagem liga e desliga sozinha na janela de gravação, com o programa aberto.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4 p-6 max-[640px]:grid-cols-1">
          <label className="col-span-2 flex flex-col gap-2 max-[640px]:col-span-1">
            <span className="text-xs font-bold uppercase text-text-muted">Título</span>
            <input
              value={corpo.titulo}
              maxLength={120}
              placeholder="Missa de Natal"
              onChange={(e) => alterar({ titulo: e.target.value })}
              className={inputClassName}
            />
          </label>

          <label className="flex flex-col gap-2">
            <span className="text-xs font-bold uppercase text-text-muted">Tipo</span>
            <select
              value={corpo.tipo}
              onChange={(e) => alterar({ tipo: e.target.value as TipoCelebracao })}
              className={inputClassName}
            >
              {tipos.map((tipo) => (
                <option key={tipo.value} value={tipo.value}>{tipo.label}</option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-2">
            <span className="text-xs font-bold uppercase text-text-muted">Data</span>
            <input
              type="date"
              value={corpo.data}
              min={hoje}
              onChange={(e) => alterar({ data: e.target.value })}
              className={inputClassName}
            />
          </label>

          <label className="flex flex-col gap-2">
            <span className="text-xs font-bold uppercase text-text-muted">Horário da missa</span>
            <input
              type="time"
              value={corpo.horarioMissa}
              onChange={(e) => alterar({ horarioMissa: e.target.value })}
              className={inputClassName}
            />
          </label>

          <div className="grid grid-cols-2 gap-4">
            <label className="flex flex-col gap-2">
              <span className="text-xs font-bold uppercase text-text-muted">Início da gravação</span>
              <input
                type="time"
                value={corpo.inicioGravacao}
                onChange={(e) => alterar({ inicioGravacao: e.target.value })}
                className={inputClassName}
              />
            </label>
            <label className="flex flex-col gap-2">
              <span className="text-xs font-bold uppercase text-text-muted">Fim da gravação</span>
              <input
                type="time"
                value={corpo.fimGravacao}
                onChange={(e) => alterar({ fimGravacao: e.target.value })}
                className={inputClassName}
              />
            </label>
          </div>

          <label className="col-span-2 flex items-start gap-3 rounded-lg border border-border bg-app-bg p-4 max-[640px]:col-span-1">
            <input
              type="checkbox"
              checked={corpo.repetirSemanalmente}
              onChange={(e) => alterar({ repetirSemanalmente: e.target.checked })}
              className="mt-0.5 size-4 accent-secondary"
            />
            <span>
              <span className="block text-sm font-bold text-text-dark">Repetir toda semana neste dia</span>
              <span className="block text-sm text-text-muted">
                Também entra na agenda semanal (Configurações), no mesmo dia da semana e horário. Sem marcar, vale só para esta data.
              </span>
            </span>
          </label>

          {erro && <p className="col-span-2 m-0 text-sm font-semibold text-red-600 max-[640px]:col-span-1">{erro}</p>}
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
            type="submit"
            disabled={salvando}
            className="flex items-center gap-2 rounded-lg bg-secondary px-4 py-2.5 text-sm font-bold text-white shadow-sm transition hover:bg-secondary/90 disabled:opacity-60"
          >
            <Save size={18} />
            {salvando ? 'Salvando...' : 'Salvar celebração'}
          </button>
        </div>
      </form>
    </div>
  );
}
