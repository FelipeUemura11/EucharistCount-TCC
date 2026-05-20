import { ClockCheck } from 'lucide-react'

interface HeaderProps {
    title: string
    isActive: boolean
    lastUpdate: string
}

export function Header({ title, isActive, lastUpdate }: HeaderProps){   
    return (
        <header>
            <div>
                <h1>{title}</h1>
            </div>

            <div>
                <div className={`${isActive ? 'active' : 'inactive'}`}></div>
                <span></span>
                <span>
                    {isActive ? 'Contagem ativa' : 'Contagem inativa'}
                </span>
            </div>

            <div>
                <span> <ClockCheck size={16}/></span>
                <span>Última atualização: {lastUpdate}</span>
            </div>
        </header>
    )
}

export default Header