import { useState } from 'react'
import type { ReactElement } from 'react'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Celebrations from './pages/Celebrations'
import History from './pages/History'
import Settings from './pages/Settings'

const pages: Record<string, ReactElement> = {
  dashboard: <Dashboard />,
  celebrations: <Celebrations />,
  history: <History />,
  settings: <Settings />
}

function App() {
  const [activePage, setActivePage] = useState('dashboard')

  return (
    <div className="flex min-h-screen bg-app-bg">
      <Sidebar active={activePage} onNavigate={setActivePage} />
      <div className="flex-1 ml-70 flex flex-col min-h-screen lg:ml-70">
          {pages[activePage]}
      </div>
    </div>
  )
}

export default App
