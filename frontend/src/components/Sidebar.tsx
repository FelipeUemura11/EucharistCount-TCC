import logo from '../assets/logo.png'
import logoEucharistCount from '../assets/LogoEucaristCount.png'
import { CalendarDays, History, Settings, LayoutDashboard, type LucideIcon } from 'lucide-react'

const navItems: { icon: LucideIcon; label: string; id: string }[] = [
  { icon: LayoutDashboard, label: 'Dashboard', id: 'dashboard' },
  { icon: CalendarDays, label: 'Celebrações', id: 'celebrations' },
  { icon: History, label: 'Histórico', id: 'history' },
  { icon: Settings, label: 'Configurações', id: 'settings' },
]

interface SidebarProps {
  active: string;
  onNavigate: (id: string) => void;
}

export default function Sidebar({ active, onNavigate }: SidebarProps) {
  return (
    <aside className="bg-linear-to-b from-tertiary to-primary text-white flex w-70 flex-col fixed top-0 left-0 bottom-0 z-100 border-r border-white/10 shadow-[0_0_10px_rgba(0,0,0,0.5)] overflow-y-auto">
      <div className="px-5 py-6 flex items-center gap-3.5 border-b border-white/10">
        <div className="w-30 rounded-xl flex items-center justify-center overflow-hidden">
          <img src={logo} alt="Logo"/>
        </div>

        <div>
          <h2 className="text-base font-bold text-white leading-snug mb-0.5">Paróquia Santo Agostinho</h2>
          <span className="font-semibold text-[15px] text-white/90">& Santa Mônica</span>
        </div>
      </div>

      <nav className="flex-1 py-4">
        {navItems.map(item => (
          <button
            key={item.id}
            className={`flex items-center gap-3 w-[calc(100%-24px)] mx-3 my-1 px-4 py-3 border-0 rounded-lg text-sm font-medium text-left cursor-pointer transition-all duration-300 ease-out hover:-translate-y-1 ${
              active === item.id
                ? 'bg-transparent text-white hover:bg-white/10 hover:text-white'
                : 'bg-transparent text-white/70 hover:bg-white/10 hover:text-white'
            }`}
            onClick={() => onNavigate(item.id)}
          >
            <span className="text-lg w-6 text-center shrink-0">
              <item.icon size={24} />
            </span>
            <span className="flex-1">{item.label}</span>
          </button>
        ))}
      </nav>
      <div className="p-5 border-t border-white/10">
        <div className="flex items-center gap-2.5 px-3.5 py-3 bg-white/8 rounded-lg">
          <img src={logoEucharistCount} alt="EucharistCount Logo" className="w-15 h-15"/>
          <span className="font-semibold text-sm text-white">EucharistCount</span>
        </div>
      </div>
    </aside>
  )
}