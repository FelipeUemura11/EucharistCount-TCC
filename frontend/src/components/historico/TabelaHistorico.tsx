import { useState } from 'react';
import { ChevronLeft, ChevronRight, Download } from 'lucide-react';
import type { RegistroHistorico } from '../../types/history';

// Quantos registros cabem em cada pagina do "carrossel".
const REGISTROS_POR_PAGINA = 8;

interface TabelaHistoricoProps {
  registros: RegistroHistorico[];
  onExport: () => void;
}

export default function TabelaHistorico({ registros, onExport }: TabelaHistoricoProps) {
  const [pagina, setPagina] = useState(1);

  const totalPaginas = Math.max(1, Math.ceil(registros.length / REGISTROS_POR_PAGINA));
  // Se a lista encolher (novo filtro), nao deixa a pagina apontar para alem do fim.
  const paginaAtual = Math.min(pagina, totalPaginas);

  const inicio = (paginaAtual - 1) * REGISTROS_POR_PAGINA;
  const registrosDaPagina = registros.slice(inicio, inicio + REGISTROS_POR_PAGINA);
  // Linhas vazias completam a ultima pagina para a tabela manter a mesma altura.
  const linhasVazias = registros.length === 0 ? 0 : REGISTROS_POR_PAGINA - registrosDaPagina.length;

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
                registrosDaPagina.map((registro) => (
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
              {Array.from({ length: linhasVazias }, (_, i) => (
                // Mesma estrutura (duas linhas de texto + py-4) de uma linha real, mas invisivel.
                <tr key={`vazia-${i}`} aria-hidden="true">
                  <td colSpan={7} className="px-4 py-4">
                    <p className="m-0 text-sm">&nbsp;</p>
                    <p className="m-0 mt-0.5 text-xs">&nbsp;</p>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {registros.length > 0 && (
          <div className="mt-4 flex items-center justify-between gap-4 max-[640px]:flex-col">
            <p className="m-0 text-sm text-text-muted">
              Mostrando {inicio + 1}–{inicio + registrosDaPagina.length} de {registros.length} registros
            </p>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setPagina(paginaAtual - 1)}
                disabled={paginaAtual === 1}
                aria-label="Página anterior"
                className="flex items-center justify-center rounded-lg border border-border p-2 text-text-dark hover:bg-app-bg disabled:cursor-not-allowed disabled:opacity-40"
              >
                <ChevronLeft size={18} />
              </button>

              <span className="min-w-28 text-center text-sm font-semibold text-text-dark">
                Página {paginaAtual} de {totalPaginas}
              </span>

              <button
                type="button"
                onClick={() => setPagina(paginaAtual + 1)}
                disabled={paginaAtual === totalPaginas}
                aria-label="Próxima página"
                className="flex items-center justify-center rounded-lg border border-border p-2 text-text-dark hover:bg-app-bg disabled:cursor-not-allowed disabled:opacity-40"
              >
                <ChevronRight size={18} />
              </button>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
