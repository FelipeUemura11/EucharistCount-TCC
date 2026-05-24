import { useState } from 'react';
import type { LucideIcon } from 'lucide-react';
import {
  Bell,
  Camera,
  Clock3,
  Database,
  EyeOff,
  Gauge,
  RefreshCw,
  RotateCcw,
  Save,
  Server,
  ShieldCheck,
  Video,
  Wifi,
} from 'lucide-react';
import PageHeader from '../components/layout/PageHeader';

type HealthStatus = 'online' | 'warning' | 'offline';

interface HealthItem {
  label: string;
  detail: string;
  status: HealthStatus;
  icon: LucideIcon;
}

const healthItems: HealthItem[] = [
  { label: 'API local', detail: 'http://localhost:8000', status: 'online', icon: Server },
  { label: 'Banco SQLite', detail: 'eucharist_count.db', status: 'online', icon: Database },
  { label: 'Câmera', detail: 'Entrada principal', status: 'online', icon: Camera },
  { label: 'Modelo YOLO', detail: 'GPU habilitada', status: 'warning', icon: Gauge },
];

const healthStyle: Record<HealthStatus, string> = {
  online: 'bg-emerald-50 text-emerald-600 border-emerald-100',
  warning: 'bg-amber-50 text-amber-600 border-amber-100',
  offline: 'bg-red-50 text-red-600 border-red-100',
};

const healthLabel: Record<HealthStatus, string> = {
  online: 'Conectado',
  warning: 'Atenção',
  offline: 'Offline',
};

export default function Settings() {
  const [startOffset, setStartOffset] = useState(30);
  const [endOffset, setEndOffset] = useState(10);

  return (
    <div>
      <PageHeader title="Configurações" isActive={false} lastUpdate="--:--" showStatus={false} />

      <main className="flex-1 px-8 pt-7 pb-10 max-[640px]:px-4">
        <section className="mb-6 rounded-lg border border-border bg-white p-6 shadow-sm">
          <div className="mb-5 flex items-center justify-between gap-4 max-[760px]:items-start max-[760px]:flex-col">
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

          <div className="grid grid-cols-4 gap-4 max-[1180px]:grid-cols-2 max-[640px]:grid-cols-1">
            {healthItems.map((item) => (
              <article key={item.label} className={`rounded-lg border p-5 ${healthStyle[item.status]}`}>
                <div className="mb-4 flex items-start justify-between gap-3">
                  <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-white/70">
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

        <section className="grid grid-cols-[1fr_380px] gap-6 max-[1180px]:grid-cols-1">
          <div className="flex flex-col gap-6">
            <article className="rounded-lg border border-border bg-white p-6 shadow-sm">
              <div className="mb-5 flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-secondary/10 text-secondary">
                  <Clock3 size={24} />
                </div>
                <div>
                  <h3 className="m-0 text-base font-bold text-text-dark">Horários globais</h3>
                  <p className="m-0 text-sm text-text-muted">Aplicados às celebrações cadastradas</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 max-[840px]:grid-cols-1">
                <label className="flex flex-col gap-2">
                  <span className="text-xs font-bold uppercase text-text-muted">Iniciar antes</span>
                  <div className="flex items-center rounded-lg border border-border px-3 py-2.5">
                    <input
                      type="number"
                      min={0}
                      value={startOffset}
                      onChange={(event) => setStartOffset(Number(event.target.value))}
                      className="w-full border-0 bg-transparent text-sm font-bold text-text-dark outline-none"
                    />
                    <span className="text-sm text-text-muted">min</span>
                  </div>
                </label>

                <label className="flex flex-col gap-2">
                  <span className="text-xs font-bold uppercase text-text-muted">Encerrar após</span>
                  <div className="flex items-center rounded-lg border border-border px-3 py-2.5">
                    <input
                      type="number"
                      min={0}
                      value={endOffset}
                      onChange={(event) => setEndOffset(Number(event.target.value))}
                      className="w-full border-0 bg-transparent text-sm font-bold text-text-dark outline-none"
                    />
                    <span className="text-sm text-text-muted">min</span>
                  </div>
                </label>
              </div>
            </article>

            <article className="rounded-lg border border-border bg-white p-6 shadow-sm">
              <div className="mb-5 flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-secondary/10 text-secondary">
                  <Video size={24} />
                </div>
                <div>
                  <h3 className="m-0 text-base font-bold text-text-dark">Câmera e processamento</h3>
                  <p className="m-0 text-sm text-text-muted">Parâmetros da entrada monitorada</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 max-[760px]:grid-cols-1">
                <label className="flex flex-col gap-2">
                  <span className="text-xs font-bold uppercase text-text-muted">Fonte da câmera</span>
                  <select className="rounded-lg border border-border bg-white px-3 py-2.5 text-sm font-semibold text-text-dark outline-none">
                    <option>Entrada principal</option>
                    <option>Entrada lateral</option>
                    <option>Webcam local</option>
                  </select>
                </label>

                <label className="flex flex-col gap-2">
                  <span className="text-xs font-bold uppercase text-text-muted">Resolução</span>
                  <select className="rounded-lg border border-border bg-white px-3 py-2.5 text-sm font-semibold text-text-dark outline-none">
                    <option>1280 x 720</option>
                    <option>960 x 540</option>
                    <option>640 x 360</option>
                  </select>
                </label>

                <label className="flex flex-col gap-2">
                  <span className="text-xs font-bold uppercase text-text-muted">FPS processado</span>
                  <select className="rounded-lg border border-border bg-white px-3 py-2.5 text-sm font-semibold text-text-dark outline-none">
                    <option>10 FPS</option>
                    <option>15 FPS</option>
                    <option>30 FPS</option>
                  </select>
                </label>

                <label className="flex flex-col gap-2">
                  <span className="text-xs font-bold uppercase text-text-muted">Tracker</span>
                  <select className="rounded-lg border border-border bg-white px-3 py-2.5 text-sm font-semibold text-text-dark outline-none">
                    <option>BoT-SORT</option>
                    <option>ByteTrack</option>
                  </select>
                </label>
              </div>
            </article>
          </div>

          <aside className="flex flex-col gap-6">
            <article className="rounded-lg border border-border bg-white p-6 shadow-sm">
              <div className="mb-5 flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600">
                  <ShieldCheck size={24} />
                </div>
                <div>
                  <h3 className="m-0 text-base font-bold text-text-dark">Privacidade</h3>
                  <p className="m-0 text-sm text-text-muted">Operação local sem identificação pessoal</p>
                </div>
              </div>

              <div className="flex flex-col gap-3 text-sm">
                <div className="flex items-center gap-3 rounded-lg bg-app-bg p-4">
                  <EyeOff size={20} className="text-emerald-600" />
                  <span className="font-semibold text-text-dark">Não armazenar vídeo por padrão</span>
                </div>
                <div className="flex items-center gap-3 rounded-lg bg-app-bg p-4">
                  <Wifi size={20} className="text-emerald-600" />
                  <span className="font-semibold text-text-dark">Execução na rede local</span>
                </div>
                <div className="flex items-center gap-3 rounded-lg bg-app-bg p-4">
                  <Bell size={20} className="text-emerald-600" />
                  <span className="font-semibold text-text-dark">Alertas de câmera offline</span>
                </div>
              </div>
            </article>
          <div className="mt-2 flex justify-center gap-3">
            <button
              type="button"
              className="flex items-center gap-2 rounded-lg border border-border px-4 py-2.5 text-sm font-bold text-text-dark transition hover:bg-app-bg"
            >
              <RotateCcw size={18} />
              Restaurar padrão
            </button>
            <button
              type="button"
              className="flex items-center gap-2 rounded-lg bg-secondary px-4 py-2.5 text-sm font-bold text-white shadow-sm transition hover:bg-secondary/90"
            >
              <Save size={18} />
              Salvar alterações
            </button>
          </div>
          </aside>
        </section>

      </main>
    </div>
  );
}
