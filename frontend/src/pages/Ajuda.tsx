import {
    Calculator,
    CalendarClock,
    CalendarDays,
    ChevronDown,
    History,
    PlayCircle,
    ShieldCheck,
    Timer,
    Wrench,
    X,
} from "lucide-react";
import { useState } from "react";

import printDashboard from "../assets/faq/Dashboard.png";
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

// O index.css zera o list-style de todo <ul> (fora das camadas do Tailwind),
// entao a classe list-disc nao vence: o marcador vai inline. "outside" + pl-5
// faz a linha quebrada alinhar com o texto, e nao com a bolinha.
const MARCADOR = { listStyle: "disc outside" } as const;

// Destaque de termos da interface (nomes de abas, botoes, cartoes).
function Termo({ children }: { children: React.ReactNode }) {
    return <strong className="text-text-dark">{children}</strong>;
}

export default function Ajuda() {
    const [openId, setOpenId] = useState<string | null>("funciona");
    const [zoomedImage, setZoomedImage] = useState<string | null>(null);

    const toggleAccordion = (id: string) => {
        setOpenId(openId === id ? null : id);
    };

    // O texto descreve o comportamento atual do sistema (agendador, estimativa,
    // historico). Mudou o comportamento, atualize aqui tambem.
    const faqs: FaqItem[] = [
        {
            id: "funciona",
            icon: <PlayCircle size={24} />,
            title: "Como funciona o sistema?",
            colorClass: "bg-blue-50 text-blue-600",
            content: (
                <>
                    <p>
                        O EucharistCount conta quantas pessoas estão na igreja durante a missa, usando a câmera da
                        entrada. O sistema reconhece pessoas na imagem, sem identificar quem é cada uma, e conta quem
                        cruza a linha da porta: quem entra soma, quem sai subtrai. Com esse número, ele sugere quantas
                        hóstias consagrar.
                    </p>
                    <p>
                        O <Termo>Dashboard</Termo> mostra a missa em tempo real e se atualiza sozinho a cada 2 segundos:
                    </p>
                    <ul style={MARCADOR} className="space-y-1.5 pl-5">
                        <li><Termo>Pessoas presentes</Termo>: entradas menos saídas, ou seja, quem está dentro agora.</li>
                        <li><Termo>Entradas</Termo> e <Termo>Saídas</Termo>: quantas pessoas cruzaram a porta em cada sentido.</li>
                        <li><Termo>Evolução da ocupação</Termo>: o gráfico de pessoas presentes ao longo da missa.</li>
                        <li><Termo>Resumo da celebração</Termo>: a missa e o horário de início e fim da contagem.</li>
                        <li><Termo>Estimativa para comunhão</Termo>, <Termo>Hóstias sugeridas</Termo> e <Termo>Porcentagem que irá comungar</Termo>: a sugestão de hóstias.</li>
                    </ul>
                    <p>
                        O selo no topo da tela indica <Termo>Contagem ativa</Termo> enquanto a câmera está contando.
                        Sem contagem, o Dashboard continua mostrando o resultado da última missa.
                    </p>
                    <div>
                        <ExpandableImage src={printDashboard} alt="Dashboard durante uma contagem" onZoom={setZoomedImage} />
                    </div>
                </>
            )
        },
        {
            id: "agenda",
            icon: <CalendarClock size={24} />,
            title: "Como cadastro os horários das missas?",
            colorClass: "bg-green-50 text-green-600",
            content: (
                <>
                    <p>
                        Os horários ficam na <Termo>agenda semanal</Termo>, e são eles que ligam e desligam a contagem:
                    </p>
                    <ol className="list-decimal space-y-1.5 pl-5">
                        <li>Acesse a aba <Termo>Configurações</Termo> no menu lateral.</li>
                        <li>Em <Termo>Agenda Semanal Padrão</Termo>, escolha o <Termo>Dia da Semana</Termo>.</li>
                        <li>Preencha o horário da missa (<Termo>Início (Missa)</Termo>) e o período em que a câmera deve contar (<Termo>Início Gravação</Termo> e <Termo>Fim Gravação</Termo>).</li>
                        <li>Clique em <Termo>Adicionar</Termo>.</li>
                    </ol>
                    <ul style={MARCADOR} className="space-y-1.5 pl-5">
                        <li>O horário vale para <Termo>todas as semanas</Termo>, até ser removido.</li>
                        <li>Para remover um horário, clique na lixeira ao lado dele.</li>
                        <li>As mudanças valem na hora, sem precisar reiniciar o programa.</li>
                        <li>O fim da gravação precisa ser depois do início, no mesmo dia (o período não pode passar da meia-noite).</li>
                        <li>Comece a gravação antes de os fiéis chegarem: quem entra antes do início da gravação não é contado.</li>
                    </ul>
                    <div>
                        <ExpandableImage src={printConfiguracoes} alt="Agenda semanal na tela Configurações" onZoom={setZoomedImage} />
                    </div>
                </>
            )
        },
        {
            id: "contagem",
            icon: <Timer size={24} />,
            title: "Como a contagem começa e termina?",
            colorClass: "bg-teal-50 text-teal-600",
            content: (
                <ul style={MARCADOR} className="space-y-1.5 pl-5">
                    <li>
                        Com o programa EucharistCount aberto no computador da igreja, a contagem <Termo>liga sozinha</Termo> no
                        início da gravação e <Termo>desliga sozinha</Termo> no fim. Não é preciso apertar nada.
                    </li>
                    <li>Durante a contagem, o selo no topo da tela mostra <Termo>Contagem ativa</Termo>.</li>
                    <li>Se o programa for aberto com a missa já em andamento, dentro do período de gravação, a contagem começa na hora.</li>
                    <li>Se o programa estiver fechado ou o computador desligado no horário, a missa não é contada.</li>
                    <li>Ao terminar, a missa vai para o <Termo>Histórico</Termo>, já com a sugestão de hóstias.</li>
                    <li>Se o programa for fechado no meio da contagem, aquela contagem é descartada e não aparece no Histórico.</li>
                </ul>
            )
        },
        {
            id: "hostias",
            icon: <Calculator size={24} />,
            title: "Como é calculada a sugestão de hóstias?",
            colorClass: "bg-amber-50 text-amber-600",
            content: (
                <>
                    <ul style={MARCADOR} className="space-y-1.5 pl-5">
                        <li>
                            <Termo>Estimativa para comunhão</Termo>: as pessoas presentes multiplicadas pela proporção de
                            pessoas que costumam comungar, calculada a partir das missas já registradas (78% enquanto não
                            houver dados). Com mais missas registradas, o sistema passa a considerar também o dia, o horário e
                            o tipo da celebração.
                        </li>
                        <li>
                            <Termo>Hóstias sugeridas</Termo>: a estimativa mais uma margem de segurança (hoje, 10%),
                            arredondada para cima.
                        </li>
                        <li>
                            <Termo>Porcentagem que irá comungar</Termo>: a estimativa dividida pelas pessoas presentes.
                        </li>
                    </ul>
                    <p>
                        Exemplo: com 149 pessoas presentes e 78%, a estimativa é de 116 pessoas, e a sugestão é de
                        128 hóstias (116 + 10%, arredondado para cima).
                    </p>
                    <p>
                        É uma sugestão: a decisão final é sempre da equipe litúrgica. A conta depende de a câmera ver
                        todas as pessoas que entram, por isso o posicionamento dela e o horário da gravação fazem diferença.
                    </p>
                </>
            )
        },
        {
            id: "historico",
            icon: <History size={24} />,
            title: "Onde vejo os dados de missas anteriores?",
            colorClass: "bg-purple-50 text-purple-600",
            content: (
                <>
                    <p>
                        Na aba <Termo>Histórico</Termo>. Cada linha é uma missa encerrada, com a data, o total de pessoas,
                        a estimativa para comunhão, as hóstias sugeridas e as entradas e saídas.
                    </p>
                    <ul style={MARCADOR} className="space-y-1.5 pl-5">
                        <li>Em <Termo>Buscar celebração</Termo>, procure pelo nome da missa, pelo dia da semana ou pela data.</li>
                        <li>Em <Termo>Período</Termo>, escolha <Termo>Mostrar tudo</Termo> ou os últimos 7, 30 ou 90 dias (contados a partir da missa mais recente) e clique em <Termo>Filtrar</Termo>.</li>
                        <li>A lista mostra 8 missas por página. Use as setas no rodapé da tabela para passar de página.</li>
                        <li>O botão <Termo>Exportar</Termo> baixa um arquivo <Termo>.csv</Termo>, que abre no Excel, com as missas do filtro atual.</li>
                        <li>Só aparecem contagens que terminaram normalmente. Uma contagem interrompida não entra no Histórico.</li>
                    </ul>
                    <div>
                        <ExpandableImage src={printHistorico} alt="Tela de Histórico" onZoom={setZoomedImage} />
                    </div>
                </>
            )
        },
        {
            id: "celebracoes",
            icon: <CalendarDays size={24} />,
            title: "E a aba Celebrações?",
            colorClass: "bg-rose-50 text-rose-600",
            content: (
                <p>
                    A aba <Termo>Celebrações</Termo> ainda está em desenvolvimento: o calendário mostra dados de exemplo,
                    e as alterações feitas nele não são salvas nem ligam a câmera. Para que uma missa seja contada,
                    cadastre o horário em <Termo>Configurações</Termo>. Missas fora da agenda semanal, como uma missa de
                    última hora, ainda não podem ser agendadas pelo sistema.
                </p>
            )
        },
        {
            id: "privacidade",
            icon: <ShieldCheck size={24} />,
            title: "As imagens das pessoas ficam gravadas?",
            colorClass: "bg-sky-50 text-sky-600",
            content: (
                <p>
                    Não. As imagens da câmera são analisadas na memória do computador e descartadas em seguida: nenhuma
                    foto ou vídeo é salvo. O sistema guarda apenas números (quantas pessoas entraram, saíram e estavam
                    presentes) e não identifica ninguém. Tudo roda no computador da igreja, sem enviar nada para a internet.
                </p>
            )
        },
        {
            id: "problemas",
            icon: <Wrench size={24} />,
            title: "A contagem não começou. O que verificar?",
            colorClass: "bg-orange-50 text-orange-600",
            content: (
                <ol className="list-decimal space-y-1.5 pl-5">
                    <li>O programa EucharistCount está aberto no computador da igreja?</li>
                    <li>
                        Em <Termo>Configurações</Termo>, o horário está cadastrado para o dia da semana certo, e o horário
                        atual está dentro do período de gravação?
                    </li>
                    <li>
                        Em <Termo>Configurações</Termo> → <Termo>Info. da Câmera</Termo>, a fonte de vídeo aparece? Se estiver
                        "Não definida", a câmera não foi configurada.
                    </li>
                    <li>O computador não pode entrar em suspensão durante a missa.</li>
                    <li>Se mesmo assim não funcionar, avise o responsável técnico.</li>
                </ol>
            )
        }
    ];

    return (
        <>
            <div className="mx-auto max-w-4xl space-y-8">
                <div>
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

                <div className="space-y-3">
                    {faqs.map((faq) => {
                        const isOpen = openId === faq.id;
                        return (
                            <div key={faq.id} className="rounded-xl bg-white shadow-sm border border-border overflow-hidden">
                                <button
                                    type="button"
                                    onClick={() => toggleAccordion(faq.id)}
                                    className={`w-full flex items-center justify-between gap-4 px-5 py-4 md:px-6 md:py-5 text-left cursor-pointer transition-colors ${
                                        isOpen ? "bg-gray-50/60" : "hover:bg-gray-50/50"
                                    }`}
                                >
                                    <div className="flex items-center gap-4">
                                        <div className={`shrink-0 p-2 rounded-lg ${faq.colorClass}`}>
                                            {faq.icon}
                                        </div>
                                        <h3 className="m-0 text-[1.15rem] font-bold text-text-dark">{faq.title}</h3>
                                    </div>
                                    <div className={`shrink-0 p-1.5 rounded-full transition-transform duration-300 ${isOpen ? "rotate-180 bg-gray-100" : ""}`}>
                                        <ChevronDown className="text-text-muted" size={20} />
                                    </div>
                                </button>
                                
                                <div 
                                    className={`grid transition-[grid-template-rows] duration-300 ease-in-out ${
                                        isOpen ? "grid-rows-[1fr]" : "grid-rows-[0fr]"
                                    }`}
                                >
                                    <div className="overflow-hidden">
                                        <div className="space-y-4 border-t border-border px-5 pt-5 pb-6 md:px-6 text-text-muted leading-relaxed">
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
