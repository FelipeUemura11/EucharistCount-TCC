import type { LucideIcon } from 'lucide-react';

export type PageId = 'dashboard' | 'celebrations' | 'history' | 'settings';

export interface NavigationItem {
  id: PageId;
  label: string;
  icon: LucideIcon;
}
