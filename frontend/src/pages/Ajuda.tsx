import { HelpCircle, PlusCircle, Settings, PlayCircle, ChevronDown, X } from "lucide-react";
import { useState } from "react";

import printDashboard from "../assets/faq/Dashboard.png";
import printCelebracoes from "../assets/faq/Celebracoes.png";
import printCelebracaoModal from "../assets/faq/CelebracaoModal.png";
import printHistorico from "../assets/faq/Historico.png";
import printConfiguracoes from "../assets/faq/Configuracoes.png";

interface FaqItem {
    id: string;
    icon: React.ReactNode;
    title: string;
    content: React.ReactNode;
    colorClass: string;
}

// Fora do componente da pagina: definido dentro, seria um componente novo a
// cada render e o React remontaria as imagens.
function ExpandableImage({ src, alt, onZoom }: { src: string; alt: string; onZoom: (src: string) => void }) {
    return (
        <div
            className="relative overflow-hidden rounded-lg border border-border shadow-sm cursor-zoom-in group"
            onClick={() => onZoom(src)}
        >
            <img src={src} alt={alt} className="w-full h-auto object-cover group-hover:opacity-90 transition-opacity" />

            {/* Overlay com texto "Clique para ampliar" */}
            <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity bg-black/5">
                <span className="bg-black/75 text-white px-4 py-2 rounded-full text-sm font-medium backdrop-blur-md">
                    Clique para ampliar
                </span>
            </div>
        </div>
    );
}

export default function Ajuda() {
    const [openId, setOpenId] = useState<string | null>("nova-missa");
    const [zoomedImage, setZoomedImage] = useState<string | null>(null);

    const toggleAccordion = (id: string) => {
        setOpenId(openId === id ? null : id);
    };

    const faqs: FaqItem[] = [
        {
            id: "funciona",
            icon: <PlayCircle size={24} />,
            title: "Como funciona o sistema?",
            colorClass: "bg-blue-50 text-blue-600",
            content: (
                <>
                    <p className="mb-4">
                        O EucharistCount é um sistema de contagem automatizada de fiéis usando visão computacional.
                        Ele utiliza câmeras instaladas na igreja para identificar e contar as pessoas presentes durante
                        as celebrações, auxiliando no planejamento logístico e na distribuição da Eucaristia. 
                        O dashboard principal exibe as contagens em tempo real.
                    </p>
                    <div className="mt-4">
                        <ExpandableImage src={printDashboard} alt="Dashboard do Sistema" onZoom={setZoomedImage} />
                    </div>
                </>
            )
        },
        {
            id: "nova-missa",
            icon: <PlusCircle size={24} />,
            title: "Como adiciono uma nova missa ou celebração?",
            colorClass: "bg-green-50 text-green-600",
            content: (
                <>
                    <p className="mb-4">Para adicionar uma nova missa:</p>
                    <ol className="space-y-2 list-decimal list-inside ml-2 mb-4">
                        <li>Acesse a aba <strong className="text-text-dark">Celebrações</strong> no menu lateral.</li>
                        <li>No calendário, clique no dia desejado.</li>
                        <li>No modal que se abrirá, clique em <strong className="text-text-dark">"Adicionar Horário"</strong>.</li>
                        <li>Preencha o horário de início da missa e ajuste os horários de gravação (início e fim) para a câmera.</li>
                        <li>Clique em <strong className="text-text-dark">"Salvar Alterações"</strong> para registrar o horário da celebração.</li>
                    </ol>
                    <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                        <ExpandableImage 
                            src={printCelebracoes} 
                            alt="Tela de Celebrações"
                            onZoom={setZoomedImage}
                        />
                        <ExpandableImage 
                            src={printCelebracaoModal} 
                            alt="Modal de Adicionar Horário"
                            onZoom={setZoomedImage}
                        />
                    </div>
                </>
            )
        },
        {
            id: "historico",
            icon: <HelpCircle size={24} />,
            title: "Onde vejo os dados de missas anteriores?",
            colorClass: "bg-purple-50 text-purple-600",
            content: (
                <>
                    <p className="mb-4">
                        Todo o registro de contagens passadas fica armazenado na aba <strong className="text-text-dark">Histórico</strong>. 
                        Lá você pode filtrar por período e ver, para cada missa, a presença estimada, as entradas e saídas e a sugestão de hóstias.
                    </p>
                    <div className="mt-4">
                        <ExpandableImage src={printHistorico} alt="Tela de Histórico" onZoom={setZoomedImage} />
                    </div>
                </>
            )
        },
        {
            id: "configuracoes",
            icon: <Settings size={24} />,
            title: "Como configuro a agenda e as câmeras?",
            colorClass: "bg-orange-50 text-orange-600",
            content: (
                <>
                    <p className="mb-4">
                        A aba <strong className="text-text-dark">Configurações</strong> concentra a gestão global da igreja.
                        Nela, você pode definir a agenda padrão semanal, cadastrando o dia, o horário da missa e o período de gravação.
                        Também é possível consultar as configurações de vídeo usadas no processamento.
                    </p>
                    <div className="mt-4">
                        <ExpandableImage src={printConfiguracoes} alt="Tela de Configurações" onZoom={setZoomedImage} />
                    </div>
                </>
            )
        }
    ];

    return (
        <>
            <div className="mx-auto max-w-4xl space-y-8">
                <div className="mb-6">
                    <p className="m-0 text-sm font-semibold uppercase text-text-muted">
                        Central de Ajuda
                    </p>
                    <h2 className="m-0 mt-1 text-2xl font-extrabold text-text-dark">
                        Perguntas Frequentes (FAQ)
                    </h2>
                    <p className="mt-2 text-text-muted">
                        Tire suas dúvidas sobre como usar o sistema EucharistCount.
                    </p>
                </div>

                <div className="space-y-4">
                    {faqs.map((faq) => {
                        const isOpen = openId === faq.id;
                        return (
                            <div key={faq.id} className="rounded-xl bg-white shadow-sm border border-border overflow-hidden">
                                <button
                                    type="button"
                                    onClick={() => toggleAccordion(faq.id)}
                                    className="w-full flex items-center justify-between p-6 text-left cursor-pointer hover:bg-gray-50/50 transition-colors"
                                >
                                    <div className="flex items-center gap-4">
                                        <div className={`p-2 rounded-lg ${faq.colorClass}`}>
                                            {faq.icon}
                                        </div>
                                        <h3 className="m-0 text-[1.15rem] font-bold text-text-dark">{faq.title}</h3>
                                    </div>
                                    <div className={`p-1.5 rounded-full transition-transform duration-300 ${isOpen ? "rotate-180 bg-gray-100" : ""}`}>
                                        <ChevronDown className="text-text-muted" size={20} />
                                    </div>
                                </button>
                                
                                <div 
                                    className={`grid transition-[grid-template-rows] duration-300 ease-in-out ${
                                        isOpen ? "grid-rows-[1fr]" : "grid-rows-[0fr]"
                                    }`}
                                >
                                    <div className="overflow-hidden">
                                        <div className="p-6 pt-0 text-text-muted leading-relaxed border-t border-border mt-2">
                                            {faq.content}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Lightbox / Modal para visualizar imagem em tela cheia */}
            {zoomedImage && (
                <div 
                    className="fixed inset-0 z-9999 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 md:p-10"
                    onClick={() => setZoomedImage(null)}
                >
                    <button 
                        className="absolute top-4 right-4 md:top-6 md:right-6 text-white bg-white/20 hover:bg-white/40 rounded-full p-2 backdrop-blur-md transition-colors"
                        onClick={() => setZoomedImage(null)}
                        aria-label="Fechar"
                    >
                        <X size={28} />
                    </button>
                    <img 
                        src={zoomedImage} 
                        alt="Imagem Ampliada" 
                        className="max-w-full max-h-full rounded-lg shadow-2xl object-contain border border-white/10"
                        onClick={(e) => e.stopPropagation()} // Impede que o clique na imagem feche o modal
                    />
                </div>
            )}
        </>
    );
}
