import { useState } from 'react';
import { HandHeart } from 'lucide-react';
import { confirmarComungantes } from '../../services/dashboard';

interface ConfirmarComunhaoProps {
  sessaoId: number;
  estimativa: number;
}

export default function ConfirmarComunhao({ sessaoId, estimativa }: ConfirmarComunhaoProps) {
  const [corrigindo, setCorrigindo] = useState(false);
  const [valor, setValor] = useState(String(estimativa));
  const [salvo, setSalvo] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const salvar = async (comungantes: number) => {
    try {
      await confirmarComungantes(sessaoId, comungantes);
      setSalvo(true);
      setErro(null);
    } catch (error) {
      setErro(error instanceof Error ? error.message : 'Não foi possível salvar.');
    }
  };

  // Enquanto o Dashboard nao recarrega, fica so o agradecimento.
  if (salvo) {
    return (
      <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-5 py-3 text-sm font-semibold text-emerald-700">
        Obrigado! Registrado.
      </div>
    );
  }

  const numero = Number(valor);
  const valido = valor.trim() !== '' && Number.isInteger(numero) && numero >= 0;

  return (
    <section className="flex flex-wrap items-center gap-4 rounded-lg border border-secondary/30 bg-white px-5 py-4 shadow-sm">
      <div className="flex size-11 items-center justify-center rounded-lg bg-secondary/10 text-secondary">
        <HandHeart size={22} />
      </div>
      <div className="min-w-0 flex-1">
        <p className="m-0 text-sm font-bold text-text-dark">A missa terminou. Quantas pessoas comungaram?</p>
        <p className="m-0 mt-0.5 text-sm text-text-muted">O sistema estimou {estimativa}.</p>
      </div>

      {corrigindo ? (
        <div className="flex items-center gap-2">
          <input
            type="number"
            min={0}
            value={valor}
            onChange={(e) => setValor(e.target.value)}
            className="w-28 rounded-lg border border-border px-3 py-2 text-sm font-semibold text-text-dark outline-none focus:border-secondary"
          />
          <button
            type="button"
            disabled={!valido}
            onClick={() => salvar(numero)}
            className="rounded-lg bg-secondary px-4 py-2 text-sm font-bold text-white hover:bg-secondary/90 disabled:opacity-60"
          >
            Salvar
          </button>
        </div>
      ) : (
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => salvar(estimativa)}
            className="rounded-lg bg-secondary px-4 py-2 text-sm font-bold text-white hover:bg-secondary/90"
          >
            Está certo
          </button>
          <button
            type="button"
            onClick={() => setCorrigindo(true)}
            className="rounded-lg border border-border px-4 py-2 text-sm font-bold text-text-dark hover:bg-app-bg"
          >
            Corrigir
          </button>
        </div>
      )}

      {erro && <p className="m-0 w-full text-sm font-semibold text-red-600">{erro}</p>}
    </section>
  );
}
