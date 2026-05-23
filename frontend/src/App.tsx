import { useState } from 'react'
import { pageRegistry } from './app/pageRegistry'
import AppLayout from './components/layout/AppLayout'
import type { PageId } from './types/navigation'

function App() {
  const [activePage, setActivePage] = useState<PageId>('dashboard')

  return (
    <AppLayout activePage={activePage} onNavigate={setActivePage}>
      {pageRegistry[activePage]}
    </AppLayout>
  )
}

export default App
