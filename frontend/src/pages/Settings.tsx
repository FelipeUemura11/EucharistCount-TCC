import PageHeader from '../components/layout/PageHeader';
import { useSystemStatus } from "../hooks/useSystemStatus";

export default function Settings() {
  const isActiveGlobal = useSystemStatus();

  return (
    <div>
      <PageHeader title="Configurações" isActive={isActiveGlobal} />

      <main className="min-w-0 flex-1 overflow-x-hidden px-8 pt-7 pb-10 max-[640px]:px-4">
        <div className="grid gap-6">
          {/* Pode colocar os formulários de configuração aqui futuramente */}
          <p className="text-gray-500">
             O painel de configurações estará disponível em breve pela equipe de desenvolvimento.
          </p>
        </div>
      </main>
    </div>
  );
}