import { Download } from 'lucide-react';
import type { RegistroHistorico } from '../../types/history';

interface TabelaHistoricoProps {
  registros: RegistroHistorico[];
  onExport: () => void;
}

export default function TabelaHistorico({ registros, onExport }: TabelaHistoricoProps) {
  return (
    <section className="min-w-0">
      <div className="min-w-0 rounded-lg border border-border bg-white p-6 shadow-sm">
        <div className="mb-5 flex items-center justify-between gap-4 max-[640px]:items-start max-[640px]:flex-col">
          <div className="min-w-0">
            <h3 className="m-0 text-base font-bold text-text-dark">Registros de celebrações</h3>
            <p className="m-0 mt-1 text-sm text-text-muted">Dados consolidados após o encerramento da contagem</p>
          </div>

          <button
            type="button"
            onClick={onExport}
            className="flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm font-bold text-text-dark hover:bg-app-bg"
          >
            <Download size={17} />
            Exportar
          </button>
        </div>

        <div className="max-w-full overflow-x-auto rounded-xl">
          <table className="w-full min-w-245 table-fixed border-collapse">
            <colgroup>
              <col className="w-[13%]" />
              <col className="w-[25%]" />
              <col className="w-[13%]" />
              <col className="w-[17%]" />
              <col className="w-[14%]" />
              <col className="w-[9%]" />
              <col className="w-[9%]" />
            </colgroup>
            <thead>
              <tr className="bg-primary/10 border-b border-border-light text-xs uppercase text-text-muted">
                <th scope="col" className="px-4 py-3 text-left font-bold">Data</th>
                <th scope="col" className="px-4 py-3 text-left font-bold">Celebração</th>
                <th scope="col" className="px-4 py-3 text-right font-bold">Total de pessoas</th>
                <th scope="col" className="px-4 py-3 text-right font-bold">Estimativa para comunhão</th>
                <th scope="col" className="px-4 py-3 text-right font-bold">Hóstias sugeridas</th>
                <th scope="col" className="px-4 py-3 text-right font-bold">Entradas</th>
                <th scope="col" className="px-4 py-3 text-right font-bold">Saídas</th>
              </tr>
            </thead>
            <tbody>
              {registros.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-sm font-semibold text-text-muted">
                    Nenhum registro encontrado para os filtros aplicados.
                  </td>
                </tr>
              ) : (
                registros.map((registro) => (
                  <tr
                    key={registro.id}
                    className="border-b border-border-light transition last:border-0 hover:bg-app-bg"
                  >
                    <td className="px-4 py-4 text-left text-sm font-semibold text-text-dark">{registro.data}</td>
                    <td className="px-4 py-4 text-left">
                      <p className="m-0 text-sm font-bold text-text-dark">{registro.celebracao}</p>
                      <p className="m-0 mt-0.5 text-xs text-text-muted">{registro.diaSemana}, {registro.horarioMissa}</p>
                    </td>
                    <td className="px-4 py-4 text-right text-sm font-semibold text-text-dark">{registro.totalPessoas}</td>
                    <td className="px-4 py-4 text-right text-sm font-semibold text-secondary">{registro.estimativaComunhao}</td>
                    <td className="px-4 py-4 text-right text-sm font-semibold text-primary">{registro.hostiasSugeridas}</td>
                    <td className="px-4 py-4 text-right text-sm text-text-dark">{registro.entradas}</td>
                    <td className="px-4 py-4 text-right text-sm text-text-dark">{registro.saidas}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
