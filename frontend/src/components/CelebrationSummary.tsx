import type { ElementType } from 'react'
import { Play, CirclePause } from 'lucide-react'

interface SummaryItem {
  icon: ElementType;
  label: string;
  value: string;
}

interface CelebrationSummaryProps {
  items: SummaryItem[];
  onStartCount?: () => void;
  onEndCount?: () => void;
}

export default function CelebrationSummary({
  items,
  onStartCount,
  onEndCount
}: CelebrationSummaryProps) {
  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-text-muted flex flex-col h-full">
      <div className="mb-5">
        <h3 className="text-base font-bold text-text-dark m-0">Resumo da celebração</h3>
      </div>
      
      <div className="flex-1">
        <ul className="flex flex-col gap-4 list-none m-0 p-0">
          {items.map((item, index) => (
            <li key={index} className="flex items-center gap-3.5 px-4 py-3.5 bg-app-bg rounded-xl transition-colors duration-150 hover:bg-text-light">
              <span className="text-xl w-8 h-8 flex items-center justify-center shrink-0"><item.icon /></span>
              <div className="flex flex-col gap-0.5 flex-1 min-w-0">
                <span className="text-xs font-medium text-text-muted uppercase tracking-[0.3px]">{item.label}</span>
                <span className="text-sm font-semibold text-text-dark">{item.value}</span>
              </div>
            </li>
          ))}
        </ul>
      </div>
      
      <div className="flex flex-col gap-2.5 mt-5 pt-5 border-t border-app-bg">
        <button 
          className="flex items-center justify-center gap-2 px-5 py-3 rounded-lg text-sm font-semibold cursor-pointer transition-all duration-150 border-2 bg-linear-to-br from-blue-500 to-blue-600 text-white border-blue-500 hover:from-blue-600 hover:to-blue-700 hover:-translate-y-px hover:shadow-[0_4px_12px_rgba(59,130,246,0.3)]"
          onClick={onStartCount}
        >
          <span className="text-xs"><Play /></span>
          Iniciar contagem
        </button>
        <button 
          className="flex items-center justify-center gap-2 px-5 py-3 rounded-lg text-sm font-semibold cursor-pointer transition-all duration-150 border-2 bg-white text-text-dark border-border hover:bg-app-bg hover:border-text-muted"
          onClick={onEndCount}
        >
          <span className="text-xs"><CirclePause /></span>
          Encerrar contagem
        </button>
      </div>
    </div>
  );
}