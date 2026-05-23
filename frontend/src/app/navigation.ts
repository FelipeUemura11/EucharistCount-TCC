import { CalendarDays, History, LayoutDashboard, Settings } from 'lucide-react';
import type { NavigationItem } from '../types/navigation';

export const navigationItems: NavigationItem[] = [
  { icon: LayoutDashboard, label: 'Dashboard', id: 'dashboard' },
  { icon: CalendarDays, label: 'Celebrações', id: 'celebrations' },
  { icon: History, label: 'Histórico', id: 'history' },
  { icon: Settings, label: 'Configurações', id: 'settings' },
];
