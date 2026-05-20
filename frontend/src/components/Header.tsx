import { ClockCheck } from 'lucide-react'

interface HeaderProps {
    title: string
    isActive: boolean
    lastUpdate: string
}

export function Header({ title, isActive, lastUpdate }: HeaderProps){   
    return (
        <header className="bg-white px-8 py-5 flex items-center justify-between border-b border-text-dark/10 sticky top-0 z-50">
            <div className="flex items-center gap-4">
                <h1 className="text-xl font-bold text-text-dark m-0">{title}</h1>
            </div>

            <div className="flex items-center gap-5 max-[768px]:w-full max-[768px]:justify-between max-[768px]:flex-wrap max-[768px]:gap-3 max-[480px]:flex-col max-[480px]:items-start">
                <div className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold max-[768px]:px-3 max-[768px]:py-1.5 max-[768px]:text-xs ${isActive ? 'bg-emerald-50 text-emerald-600' : 'bg-red-50 text-red-600'}`}>
                    <span className={`w-2 h-2 rounded-full animate-pulse ${isActive ? 'bg-emerald-500' : 'bg-red-500'}`}></span>
                    <span>
                        {isActive ? 'Contagem ativa' : 'Contagem inativa'}
                    </span>
                </div>
                
                <div className="flex items-center gap-1.5 text-sm text-text-muted max-[768px]:text-xs">
                    <ClockCheck size={16} />
                    <span className="font-medium">Última atualização: {lastUpdate}</span>
                </div>
            </div>
        </header>
    )
}

export default Header