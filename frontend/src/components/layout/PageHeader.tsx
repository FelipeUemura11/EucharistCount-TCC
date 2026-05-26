interface HeaderProps {
    title: string
    isActive: boolean
    showStatus?: boolean
}

export default function PageHeader({ title, isActive, showStatus = true }: HeaderProps){   
    return (
        <header className="bg-white px-8 py-5 flex items-center justify-between border-b border-text-dark/10 sticky top-0 z-50">
            <div className="flex items-center gap-4">
                <h1 className="text-2xl font-bold text-text-dark m-0">{title}</h1>
            </div>
        
            {showStatus && (
                <div className="flex items-center gap-5">
                    <div className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold ${isActive ? 'bg-emerald-50 text-emerald-600' : 'bg-red-50 text-red-600'}`}>
                        <span className={`w-2 h-2 rounded-full animate-pulse ${isActive ? 'bg-emerald-500' : 'bg-red-500'}`}></span>
                        <span>
                            {isActive ? 'Contagem ativa' : 'Contagem inativa'}
                        </span>
                    </div>
                </div>
            )}
        </header>
    )
}
