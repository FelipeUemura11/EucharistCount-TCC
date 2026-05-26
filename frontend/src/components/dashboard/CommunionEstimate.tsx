import { HandHeart, Percent, HandPlatter } from "lucide-react";
import type { DashboardMetrics } from "../../types/dashboard";

interface CommunionEstimateProps {
    metrics: DashboardMetrics;
}

export default function CommunionEstimate({ metrics }: CommunionEstimateProps) {
    const communionPercent = metrics.currentOccupancy > 0
        ? Math.round((metrics.estimatedCommunicants / metrics.currentOccupancy) * 100)
        : 0;
    const suggestedHosts = Math.ceil(metrics.estimatedCommunicants * 1.1);

    const communionStats = [
        {
            label: 'Estimativa para comunhão',
            value: metrics.estimatedCommunicants,
            suffix: 'pessoas',
            icon: HandHeart,
        },
        {
            label: 'Hóstias sugeridas',
            value: suggestedHosts,
            suffix: 'unidades',
            icon: HandPlatter,
        },
        {
            label: 'Porcentagem que irá comungar',
            value: communionPercent,
            suffix: '% dos presentes',
            icon: Percent,
        },
    ];

    return (
        <div className="w-full shadow-sm border border-border rounded-xl bg-white">
            <div className="grid grid-cols-3 gap-px bg-border-light rounded-xl overflow-hidden max-[900px]:grid-cols-1">
                {communionStats.map((stat) => {
                    const Icon = stat.icon;
                    return (
                        <div key={stat.label} className="flex items-center gap-4 px-5 py-10 bg-white transition-colors duration-150 hover:bg-app-bg">
                            <div className="w-12 h-12 rounded-full bg-primary/10 text-primary flex items-center justify-center shrink-0">
                                <Icon size={26} />
                            </div>
                            <div className="flex flex-col gap-1 min-w-0">
                                <span className="text-xs font-semibold text-text-muted uppercase tracking-[0.3px]">
                                    {stat.label}
                                </span>
                                <span className="text-2xl font-extrabold text-primary leading-none">
                                    {stat.value}
                                    <small className="text-sm font-medium text-text-muted block mt-1">
                                        {stat.suffix}
                                    </small>
                                </span>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
