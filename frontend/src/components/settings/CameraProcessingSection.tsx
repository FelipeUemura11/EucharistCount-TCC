import { Video } from 'lucide-react';

const cameraSettings = [
  { label: 'Fonte da câmera', value: 'Entrada principal' },
  { label: 'Resolução', value: '1280 x 720' },
  { label: 'FPS processado', value: '30 FPS' },
];

export default function CameraProcessingSection() {
  return (
    <section className="mb-6 rounded-lg border border-border bg-white p-6 shadow-sm">
      <div className="mb-5 flex items-center gap-3">
        <div className="flex size-11 items-center justify-center rounded-lg bg-secondary/10 text-secondary">
          <Video size={24} />
        </div>
        <div>
          <h3 className="m-0 text-base font-bold text-text-dark">Câmera e processamento</h3>
          <p className="m-0 text-sm text-text-muted">Configuração atual da entrada monitorada</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 max-[900px]:grid-cols-1">
        {cameraSettings.map((setting) => (
          <div key={setting.label} className="rounded-lg border border-border bg-app-bg p-4">
            <span className="text-xs font-bold uppercase text-text-muted">{setting.label}</span>
            <p className="m-0 mt-2 text-sm font-bold text-text-dark">{setting.value}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
