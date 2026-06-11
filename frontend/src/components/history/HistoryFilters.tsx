import { Filter, Search } from 'lucide-react';

interface HistoryFiltersProps {
  searchTerm: string;
  periodInDays: number;
  onSearchTermChange: (value: string) => void;
  onPeriodInDaysChange: (value: number) => void;
  onApplyFilters: () => void;
}

const periodOptions = [
  { label: 'Últimos 7 dias', value: 7 },
  { label: 'Últimos 30 dias', value: 30 },
  { label: 'Últimos 90 dias', value: 90 },
];

export default function HistoryFilters({
  searchTerm,
  periodInDays,
  onSearchTermChange,
  onPeriodInDaysChange,
  onApplyFilters,
}: HistoryFiltersProps) {
  return (
    <section className="mb-6 rounded-lg border border-border bg-white p-5 shadow-sm">
      <div className="grid grid-cols-[minmax(0,1fr)_180px_180px_auto] items-end gap-4 max-[1100px]:grid-cols-2 max-[640px]:grid-cols-1">
        <label className="flex min-w-0 flex-col gap-2">
          <span className="text-xs font-bold uppercase text-text-muted">Buscar celebração</span>
          <div className="flex min-w-0 items-center gap-2 rounded-lg border border-border bg-white px-3 py-2.5">
            <Search size={18} className="text-text-muted" />
            <input
              value={searchTerm}
              onChange={(event) => onSearchTermChange(event.target.value)}
              className="min-w-0 w-full border-0 bg-transparent text-sm text-text-dark outline-none"
              placeholder="Missa das 19h"
            />
          </div>
        </label>

        <label className="flex min-w-0 flex-col gap-2">
          <span className="text-xs font-bold uppercase text-text-muted">Período</span>
          <select
            value={periodInDays}
            onChange={(event) => onPeriodInDaysChange(Number(event.target.value))}
            className="rounded-lg border border-border bg-white px-3 py-2.5 text-sm font-semibold text-text-dark outline-none"
          >
            {periodOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <button
          type="button"
          onClick={onApplyFilters}
          className="flex items-center justify-center gap-2 rounded-lg bg-secondary px-4 py-2.5 text-sm font-bold text-white shadow-sm transition hover:bg-secondary/90"
        >
          <Filter size={18} />
          Filtrar
        </button>
      </div>
    </section>
  );
}
