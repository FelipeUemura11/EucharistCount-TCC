import { useState } from 'react'
import type { ReactElement } from 'react'
import './App.css'
import { Sidebar } from './components/Sidebar/Sidebar'
import { Dashboard } from './pages/Dashboard/Dashboard'
import { Celebrations } from './pages/Celebrations/Celebrations'
import { History } from './pages/History/History'
import { Settings } from './pages/Settings/Settings'

const pages: Record<string, ReactElement> = {
  dashboard: <Dashboard />,
  celebrations: <Celebrations />,
  history: <History />,
  settings: <Settings />
}

function App() {
  const [activePage, setActivePage] = useState('dashboard')

  return (
    <div className="app">
      <Sidebar active={activePage} onNavigate={setActivePage} />
      <div className="main-content">
          {pages[activePage]}
      </div>
    </div>
  )
}

export default App
