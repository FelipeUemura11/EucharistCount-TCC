import { RotateCcw, Save } from 'lucide-react';

interface SettingsActionsProps {
  onReset: () => void;
}

export default function SettingsActions({ onReset }: SettingsActionsProps) {
  return (
    <section className="flex justify-end gap-3">
      <button
        type="button"
        onClick={onReset}
        className="flex items-center justify-center gap-2 rounded-lg border border-border px-4 py-2.5 text-sm font-bold text-text-dark transition hover:bg-app-bg"
      >
        <RotateCcw size={18} />
        Restaurar padrão
      </button>
      <button
        type="button"
        className="flex items-center justify-center gap-2 rounded-lg bg-secondary px-4 py-2.5 text-sm font-bold text-white shadow-sm transition hover:bg-secondary/90"
      >
        <Save size={18} />
        Salvar alterações
      </button>
    </section>
  );
}