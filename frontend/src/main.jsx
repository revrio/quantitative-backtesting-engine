import React, { useState } from 'react'
import ReactDOM from 'react-dom/client'
import { Activity, TestTube2 } from 'lucide-react'
import Screener from './pages/Screener'
import Backtester from './pages/Backtester'
import ErrorBoundary from './components/ErrorBoundary'
import './styles.css'
function App() {
  const [activeTab, setActiveTab] = useState('screener')
  return (
    <div className="flex h-screen w-full bg-bg-app text-text-primary overflow-hidden">
      {}
      <aside className="w-[220px] flex-shrink-0 border-r border-border-subtle bg-bg-app flex flex-col">
        <div className="p-6 flex items-center gap-3 border-b border-border-subtle">
          <div className="w-8 h-8 rounded-full bg-accent-cyanDim flex items-center justify-center">
            <Activity className="w-5 h-5 text-accent-cyan" />
          </div>
          <span className="font-semibold tracking-tight text-lg">StockPulse</span>
        </div>
        <nav className="flex-1 p-4 flex flex-col gap-2">
          <button 
            onClick={() => setActiveTab('screener')}
            className={`flex items-center gap-3 px-4 py-3 rounded-md transition-all duration-200 w-full text-left ${activeTab === 'screener' ? 'bg-bg-elevated border-l-2 border-accent-cyan text-accent-cyan' : 'text-text-secondary hover:bg-bg-hover hover:text-text-primary'}`}
          >
            <Activity className="w-5 h-5" />
            <span className="font-medium">Screener</span>
          </button>
          <button 
            onClick={() => setActiveTab('backtester')}
            className={`flex items-center gap-3 px-4 py-3 rounded-md transition-all duration-200 w-full text-left ${activeTab === 'backtester' ? 'bg-bg-elevated border-l-2 border-accent-cyan text-accent-cyan' : 'text-text-secondary hover:bg-bg-hover hover:text-text-primary'}`}
          >
            <TestTube2 className="w-5 h-5" />
            <span className="font-medium">Backtester</span>
          </button>
        </nav>
        <div className="p-6 text-xs text-text-muted border-t border-border-subtle">
          Platform v2.0
        </div>
      </aside>
      {}
      <main className="flex-1 overflow-auto bg-bg-app">
        <div className="max-w-[1400px] mx-auto p-6 h-full">
          <div className={`h-full ${activeTab === 'screener' ? 'block' : 'hidden'}`}>
            <Screener />
          </div>
          <div className={`h-full ${activeTab === 'backtester' ? 'block' : 'hidden'}`}>
            <Backtester />
          </div>
        </div>
      </main>
    </div>
  )
}
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
)