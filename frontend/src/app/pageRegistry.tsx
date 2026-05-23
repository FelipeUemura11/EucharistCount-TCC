import type { ReactElement } from 'react';
import Celebrations from '../pages/Celebrations';
import Dashboard from '../pages/Dashboard';
import History from '../pages/History';
import Settings from '../pages/Settings';
import type { PageId } from '../types/navigation';

export const pageRegistry: Record<PageId, ReactElement> = {
  dashboard: <Dashboard />,
  celebrations: <Celebrations />,
  history: <History />,
  settings: <Settings />,
};
