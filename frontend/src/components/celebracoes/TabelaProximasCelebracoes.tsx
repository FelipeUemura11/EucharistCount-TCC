import { CheckCircle2 } from 'lucide-react';
import type { Celebracao } from '../../types/celebrations';

interface TabelaProximasCelebracoesProps {
  celebracoes: Celebracao[];
}

export default function TabelaProximasCelebracoes({ celebracoes }: TabelaProximasCelebracoesProps) {
  return (
    <section className="mt-6 rounded-lg border border-border bg-white p-6 shadow-sm">
      <div className="mb-5 flex items-center justify-between gap-4">
        <div>
          <h3 className="m-0 text-base font-bold text-text-dark">Próximas celebrações</h3>
          <p className="m-0 mt-1 text-sm text-text-muted">Monitoramento configurado automaticamente</p>
        </div>
        <CheckCircle2 className="text-emerald-500" size={22} />
      </div>

      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-left">
          <thead>
            <tr className="border-b border-border text-xs uppercase text-text-muted">
              <th className="py-3 pr-4 font-bold">Celebração</th>
              <th className="py-3 pr-4 font-bold">Dia</th>
              <th className="py-3 pr-4 font-bold">Horário</th>
              <th className="py-3 pr-4 font-bold">Monitoramento</th>
              <th className="py-3 font-bold">Capacidade</th>
            </tr>
          </thead>
          <tbody>
            {celebracoes.map((celebracao) => (
              <tr key={celebracao.id} className="border-b border-border-light last:border-0">
                <td className="py-4 pr-4 text-sm font-bold text-text-dark">{celebracao.titulo}</td>
                <td className="py-4 pr-4 text-sm text-text-muted">{celebracao.diaSemana}, {celebracao.dia}/05</td>
                <td className="py-4 pr-4 text-sm text-text-dark">{celebracao.horarioMissa}</td>
                <td className="py-4 pr-4 text-sm text-text-muted">{celebracao.inicioMonitoramento} - {celebracao.fimMonitoramento}</td>
                <td className="py-4 text-sm font-semibold text-text-dark">{celebracao.capacidade}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
