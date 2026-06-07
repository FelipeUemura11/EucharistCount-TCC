import { RefreshCw } from 'lucide-react';
import { healthItems, healthLabel, healthStyle } from '../../data/settingsMock';

export default function SystemHealthSection() {
  return (
    <section className="mb-6 rounded-lg border border-border bg-white p-6 shadow-sm">
      <div className="mb-5 flex items-center justify-between gap-4">
        <div>
          <p className="m-0 text-sm font-semibold uppercase text-text-muted">Saúde do sistema</p>
          <h2 className="m-0 mt-1 text-2xl font-extrabold text-text-dark">Integrações locais</h2>
        </div>

        <button
          type="button"
          className="flex items-center gap-2 rounded-lg border border-border px-4 py-2.5 text-sm font-bold text-text-dark transition hover:bg-app-bg"
        >
          <RefreshCw size={18} />
          Testar conexões
        </button>
      </div>

      <div className="grid grid-cols-4 gap-4">
        {healthItems.map((item) => (
          <article key={item.label} className={`rounded-lg border p-5 ${healthStyle[item.status]}`}>
            <div className="mb-4 flex items-start justify-between gap-3">
              <div className="flex size-11 items-center justify-center rounded-lg bg-white/70">
                <item.icon size={24} />
              </div>
              <span className="rounded-full bg-white/70 px-3 py-1 text-xs font-bold">
                {healthLabel[item.status]}
              </span>
            </div>
            <h3 className="m-0 text-base font-bold">{item.label}</h3>
            <p className="m-0 mt-1 text-sm opacity-80">{item.detail}</p>
          </article>
        ))}
      </div>
    </section>
  );
}