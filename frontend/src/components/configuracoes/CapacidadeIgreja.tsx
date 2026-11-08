import { useState } from "react";
import { Users } from "lucide-react";
import { salvarCapacidade } from "../../services/configuracoes";

interface CapacidadeIgrejaProps {
    inicial: number;
}

// Capacidade da igreja: e a linha de referencia do grafico do Dashboard.
export default function CapacidadeIgreja({ inicial }: CapacidadeIgrejaProps) {
    const [valor, setValor] = useState(String(inicial));
    const [mensagem, setMensagem] = useState<{ texto: string; erro: boolean } | null>(null);

    const numero = Number(valor);
    const valido = Number.isInteger(numero) && numero >= 1 && numero <= 5000;

    const salvar = async () => {
        try {
            await salvarCapacidade(numero);
            setMensagem({ texto: "Capacidade salva.", erro: false });
        } catch (error) {
            setMensagem({ texto: error instanceof Error ? error.message : "Erro ao salvar.", erro: true });
        }
    };

    return (
        <div className="rounded-xl bg-white p-6 shadow-sm border border-border">
            <div className="flex items-center gap-2 mb-4 border-b border-border pb-3">
                <Users className="text-text-muted" size={20} />
                <h3 className="m-0 text-lg font-bold text-text-dark">Capacidade da igreja</h3>
            </div>
            <label htmlFor="capacidade" className="block text-sm text-text-muted mb-2">
                Quantas pessoas cabem na igreja. Aparece como limite no gráfico do Dashboard.
            </label>
            <div className="flex items-center gap-2">
                <input
                    id="capacidade"
                    type="number"
                    min={1}
                    max={5000}
                    value={valor}
                    onChange={(e) => { setValor(e.target.value); setMensagem(null); }}
                    className="w-28 rounded-md border border-border bg-white px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                />
                <button
                    onClick={salvar}
                    disabled={!valido}
                    className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90 transition-colors disabled:opacity-60"
                >
                    Salvar
                </button>
            </div>
            {mensagem && (
                <p className={`mt-2 mb-0 text-sm ${mensagem.erro ? "text-red-600" : "text-emerald-700"}`}>{mensagem.texto}</p>
            )}
        </div>
    );
}
