import { useEffect, useState } from "react";
import { PlusCircle, Trash2, Camera } from "lucide-react";
import type { ConfiguracoesGlobais, AgendaDiaCriar } from "../types/configuracoes";
import { getConfiguracoesGlobais, criarAgendaPadrao, removerAgendaPadrao } from "../services/configuracoes";

const DIAS_SEMANA = [
    "Domingo",
    "Segunda-feira",
    "Terça-feira",
    "Quarta-feira",
    "Quinta-feira",
    "Sexta-feira",
    "Sábado"
];

export default function Configuracoes() {
    const [configuracoes, setConfiguracoes] = useState<ConfiguracoesGlobais | null>(null);
    const [loading, setLoading] = useState(true);
    const [erroAgenda, setErroAgenda] = useState<string | null>(null);

    // Estado para o formulário de nova agenda
    const [novaAgenda, setNovaAgenda] = useState<AgendaDiaCriar>({
        diaSemana: 0,
        horarioMissa: "08:00",
        inicioGravacao: "08:00",
        fimGravacao: "09:00"
    });

    // Recarga apos adicionar/remover: nao volta para "Carregando...".
    const carregarConfigs = async () => {
        setConfiguracoes(await getConfiguracoesGlobais());
    };

    useEffect(() => {
        let isMounted = true;

        async function carregarInicial() {
            try {
                const data = await getConfiguracoesGlobais();
                if (isMounted) setConfiguracoes(data);
            } catch (error) {
                console.error(error);
            } finally {
                if (isMounted) setLoading(false);
            }
        }

        void carregarInicial();

        return () => {
            isMounted = false;
        };
    }, []);

    const handleAdicionarAgenda = async () => {
        if (!novaAgenda.horarioMissa || !novaAgenda.inicioGravacao || !novaAgenda.fimGravacao) return;
        if (novaAgenda.fimGravacao <= novaAgenda.inicioGravacao) {
            setErroAgenda("O fim da gravação deve ser depois do início.");
            return;
        }

        try {
            await criarAgendaPadrao(novaAgenda);
            setErroAgenda(null);
            await carregarConfigs();
        } catch (error) {
            setErroAgenda(error instanceof Error ? error.message : "Erro ao salvar horário.");
        }
    };

    const handleRemoverAgenda = async (id: number) => {
        try {
            await removerAgendaPadrao(id);
            setErroAgenda(null);
            await carregarConfigs();
        } catch (error) {
            setErroAgenda(error instanceof Error ? error.message : "Erro ao remover horário.");
        }
    };

    if (loading) return <div className="p-8 text-center text-text-muted">Carregando configurações...</div>;
    if (!configuracoes) return <div className="p-8 text-center text-text-muted">Erro ao carregar configurações.</div>;

    return (
        <div className="mx-auto max-w-6xl space-y-8">
            <div className="mb-6">
                <p className="m-0 text-sm font-semibold uppercase text-text-muted">
                    Gestão do Sistema
                </p>
                <h2 className="m-0 mt-1 text-2xl font-extrabold text-text-dark">
                    Configurações Globais
                </h2>
                <p className="mt-2 text-text-muted">
                    Gerencie a agenda padrão de missas semanais e consulte as configurações da câmera.
                </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Coluna Principal: Agenda Padrão */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="rounded-xl bg-white p-6 shadow-sm border border-border">
                        <h3 className="m-0 mb-4 text-xl font-bold text-text-dark border-b border-border pb-3">
                            Agenda Semanal Padrão
                        </h3>
                        <p className="text-sm text-text-muted mb-6">
                            Cadastre os horários fixos das missas e o período de gravação de cada uma. O agendamento automático do monitoramento a partir desta agenda ainda está em desenvolvimento. Celebrações especiais podem ser ajustadas na aba "Celebrações".
                        </p>

                        {/* Formulário de Adição */}
                        <div className="bg-gray-50 p-4 rounded-lg border border-border mb-6 flex flex-wrap gap-4 items-end">
                            <div className="flex-1 min-w-37.5">
                                <label className="block text-sm font-medium text-text-dark mb-1">Dia da Semana</label>
                                <select 
                                    className="w-full rounded-md border border-border bg-white px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                                    value={novaAgenda.diaSemana}
                                    onChange={(e) => setNovaAgenda({...novaAgenda, diaSemana: Number(e.target.value)})}
                                >
                                    {DIAS_SEMANA.map((dia, idx) => (
                                        <option key={idx} value={idx}>{dia}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="flex-1 min-w-30">
                                <label className="block text-sm font-medium text-text-dark mb-1">Início (Missa)</label>
                                <input 
                                    type="time" 
                                    className="w-full rounded-md border border-border bg-white px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                                    value={novaAgenda.horarioMissa}
                                    onChange={(e) => setNovaAgenda({...novaAgenda, horarioMissa: e.target.value})}
                                />
                            </div>
                            <div className="flex-1 min-w-30">
                                <label className="block text-sm font-medium text-text-dark mb-1">Início Gravação</label>
                                <input 
                                    type="time" 
                                    className="w-full rounded-md border border-border bg-white px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                                    value={novaAgenda.inicioGravacao}
                                    onChange={(e) => setNovaAgenda({...novaAgenda, inicioGravacao: e.target.value})}
                                />
                            </div>
                            <div className="flex-1 min-w-30">
                                <label className="block text-sm font-medium text-text-dark mb-1">Fim Gravação</label>
                                <input 
                                    type="time" 
                                    className="w-full rounded-md border border-border bg-white px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                                    value={novaAgenda.fimGravacao}
                                    onChange={(e) => setNovaAgenda({...novaAgenda, fimGravacao: e.target.value})}
                                />
                            </div>
                            <div>
                                <button 
                                    onClick={handleAdicionarAgenda}
                                    className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90 transition-colors"
                                >
                                    <PlusCircle size={16} />
                                    Adicionar
                                </button>
                            </div>
                        </div>

                        {erroAgenda && (
                            <p className="-mt-3 mb-6 text-sm text-red-600">{erroAgenda}</p>
                        )}

                        {/* Lista Agrupada */}
                        <div className="space-y-4">
                            {DIAS_SEMANA.map((diaNome, diaIdx) => {
                                const agendasDoDia = configuracoes.agendaPadrao.filter(a => a.diaSemana === diaIdx);
                                if (agendasDoDia.length === 0) return null;

                                return (
                                    <div key={diaIdx} className="border border-border rounded-lg overflow-hidden">
                                        <div className="bg-gray-100 px-4 py-2 font-semibold text-text-dark text-sm border-b border-border">
                                            {diaNome}
                                        </div>
                                        <div className="divide-y divide-border">
                                            {agendasDoDia.map(agenda => (
                                                <div key={agenda.id} className="flex items-center justify-between px-4 py-3 bg-white">
                                                    <div className="flex items-center gap-6">
                                                        <div className="text-sm">
                                                            <span className="text-text-muted text-xs block">Missa</span>
                                                            <strong className="text-text-dark">{agenda.horarioMissa}</strong>
                                                        </div>
                                                        <div className="text-sm">
                                                            <span className="text-text-muted text-xs block">Gravação</span>
                                                            <span className="text-text-dark">{agenda.inicioGravacao} - {agenda.fimGravacao}</span>
                                                        </div>
                                                    </div>
                                                    <button 
                                                        onClick={() => handleRemoverAgenda(agenda.id)}
                                                        className="p-1.5 text-text-muted hover:text-red-500 hover:bg-red-50 rounded transition-colors"
                                                        title="Remover horário"
                                                    >
                                                        <Trash2 size={16} />
                                                    </button>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                );
                            })}
                            
                            {configuracoes.agendaPadrao.length === 0 && (
                                <p className="text-center text-text-muted py-8 bg-gray-50 rounded-lg border border-dashed border-border">
                                    Nenhum horário padrão configurado ainda.
                                </p>
                            )}
                        </div>
                    </div>
                </div>

                {/* Coluna Lateral: Informações da Câmera */}
                <div className="space-y-6">
                    {/* Informações da Câmera */}
                    <div className="rounded-xl bg-white p-6 shadow-sm border border-border">
                        <div className="flex items-center gap-2 mb-4 border-b border-border pb-3">
                            <Camera className="text-text-muted" size={20} />
                            <h3 className="m-0 text-lg font-bold text-text-dark">Info. da Câmera</h3>
                        </div>
                        <ul className="space-y-3 text-sm">
                            <li className="flex flex-col">
                                <span className="text-text-muted text-xs uppercase font-semibold">Fonte de Vídeo</span>
                                <span className="text-text-dark truncate mt-0.5">{configuracoes.infoCamera.fonte}</span>
                            </li>
                            <li className="flex flex-col">
                                <span className="text-text-muted text-xs uppercase font-semibold">Resolução Proc.</span>
                                <span className="text-text-dark mt-0.5">{configuracoes.infoCamera.resolucao}</span>
                            </li>
                            <li className="flex flex-col">
                                <span className="text-text-muted text-xs uppercase font-semibold">FPS Processado</span>
                                <span className="text-text-dark mt-0.5">{configuracoes.infoCamera.fpsProcessado} fps</span>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    );
}
