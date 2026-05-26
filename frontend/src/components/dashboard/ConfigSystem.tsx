import { Database, Server, Cctv } from "lucide-react";
import { CheckCircle2, XCircle } from "lucide-react";
import type { ElementType } from "react";

interface SystemStatus {
    label: string;
    isOnline: boolean;
    icon: ElementType;
}

interface ConfigSystemProps {
  statuses?: SystemStatus[];
}

const defaultStatuses: SystemStatus[] = [
    { label: 'Câmeras', isOnline: true, icon: Cctv },
    { label: 'API Local', isOnline: true, icon: Server },
    { label: 'Banco de dados', isOnline: true, icon: Database },
]

export default function ConfigSystem({statuses = defaultStatuses}: ConfigSystemProps) {
    return (
        <div className="bg-white rounded-xl p-4 shadow-sm border border-border h-full">
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
                                className="flex flex-col items-center justify-center gap-4 border-r border-border-light last:border-r-0"
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
    )
}
