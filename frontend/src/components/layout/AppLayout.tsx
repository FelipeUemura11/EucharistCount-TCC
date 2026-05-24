import type { ReactNode } from 'react';
import Sidebar from './Sidebar';
import type { PageId } from '../../types/navigation';

interface AppLayoutProps {
  activePage: PageId;
  onNavigate: (id: PageId) => void;
  children: ReactNode;
}

export default function AppLayout({ activePage, onNavigate, children }: AppLayoutProps) {
  return (
    <div className="flex min-h-screen bg-app-bg">
      <Sidebar active={activePage} onNavigate={onNavigate} />
      <div className="ml-70 flex min-h-screen min-w-0 flex-1 flex-col lg:ml-70">
        {children}
      </div>
    </div>
  );
}
