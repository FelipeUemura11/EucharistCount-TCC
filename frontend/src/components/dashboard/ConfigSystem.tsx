import { Clock1, Clock2, Clock3, Clock4 } from "lucide-react";
import { Database, Server, Cctv } from "lucide-react";
import { CheckCircle2, XCircle } from "lucide-react";


interface Snapshot {
    time: string;
    label: string;
    count: number;
}

interface SystemStatus {
    label: string;
    isOnline: boolean;
    icon: React.ElementType;
}

interface ConfigSystemProps {
  snapshots?: Snapshot[];
  statuses?: SystemStatus[];
}

const defaultSnapshots: Snapshot[] = [
  { time: '18:30', label: '30 min antes', count: 45 },
  { time: '18:45', label: '15 min antes', count: 96 },
  { time: '18:50', label: '10 min antes', count: 132 },
  { time: '18:55', label: '5 min antes', count: 170 },
];

const defaultStatuses: SystemStatus[] = [
    { label: 'Câmeras', isOnline: true, icon: Cctv },
    { label: 'API Local', isOnline: true, icon: Server },
    { label: 'Banco de dados', isOnline: true, icon: Database },
]

export default function ConfigSystem({snapshots = defaultSnapshots, statuses = defaultStatuses}: ConfigSystemProps) {
    return (
        <div className="grid grid-cols-[1fr_380px] p-2 gap-6 max-[1400px]:grid-cols-[1fr_340px] max-[1200px]:grid-cols-1">
            <div className="min-w-0">
                <div className="w-full shadow-sm border border-border rounded-xl bg-white">
                    <div className="grid grid-cols-4 gap-px bg-border-light rounded-xl overflow-hidden max-[1200px]:grid-cols-2">
                    {snapshots.map((snapshot, index) => (
                        <div key={index} className="flex flex-col items-center gap-3 px-4 py-5 bg-white text-center transition-colors duration-150 hover:bg-app-bg">
                        <div className="w-11 h-11 rounded-full bg-secondary/10 text-secondary flex items-center justify-center text-xl">
                            {index === 0 && <Clock1 />}
                            {index === 1 && <Clock2 />}
                            {index === 2 && <Clock3 />}
                            {index === 3 && <Clock4 />}
                        </div>
                        <div className="flex flex-col gap-1">
                            <span className="text-xs font-semibold text-text-muted uppercase tracking-[0.3px]">
                                {snapshot.label}
                            </span>
                            <span className="text-2xl font-extrabold text-secondary leading-none">
                                {snapshot.count} 
                                <small className="text-xs font-medium text-text-muted block mt-1">
                                    pessoas
                                </small>
                            </span>
                        </div>
                        </div>
                    ))}
                    </div>
                </div>
            </div>
            <div className="min-w-0">
                <div className="bg-white rounded-xl p-4 shadow-sm border border-border">
                    <div className="mb-5">
                        <h3 className="text-base font-bold text-text-dark m-0 mb-1 pb-2">
                            Status do sistema
                        </h3>
                        <div className="grid grid-cols-3 gap-4">
                            {statuses.map((status) => {
                                const Icon = status.icon;
                                return (
                                    <div
                                        key={status.label}
                                        className="flex flex-col items-center justify-center gap-3 border-r border-border-light last:border-r-0"
                                    >
                                    <div
                                        className={`relative w-14 h-10 rounded-full flex items-center justify-center ${
                                        status.isOnline
                                            ? 'bg-emerald-50 text-emerald-600'
                                            : 'bg-red-50 text-red-600'
                                        }`}
                                    >
                                        <Icon size={28} />

                                        <span className="absolute -right-1 -bottom-1 bg-white rounded-full">
                                        {status.isOnline ? (
                                            <CheckCircle2 size={18} className="text-emerald-500" />
                                        ) : (
                                            <XCircle size={18} className="text-red-500" />
                                        )}
                                        </span>
                                    </div>

                                    <span
                                        className={`text-sm font-semibold text-center ${
                                        status.isOnline ? 'text-emerald-600' : 'text-red-600'
                                        }`}
                                    >
                                        {status.label}
                                    </span>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </div>  
            </div>
        </div>
    )
}
