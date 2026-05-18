import logo from '../../assets/logo.png'
import './Sidebar.css'
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

export function Sidebar({ active, onNavigate }: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="logo">
        <div className="logo-image">
          <img src={logo} alt="Logo" />
        </div>

        <div className="logo-text">
          <h2>Paróquia Santo Agostinho</h2>
          <span>& Santa Mônica</span>
        </div>
      </div>

      <nav>
        {navItems.map(item => (
          <button
            key={item.id}
            className={`nav-item ${active === item.id ? 'active' : ''}`}
            onClick={() => onNavigate(item.id)}
          >
            <span className="nav-icon">
              <item.icon size={24} />
            </span>
            <span className="nav-label">{item.label}</span>
          </button>
        ))}
      </nav>
    </aside>
  )
}