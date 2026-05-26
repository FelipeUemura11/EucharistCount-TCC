import type { LucideIcon } from 'lucide-react';

export type StatCardColor = 'primary' | 'secondary' | 'green' | 'red';
export type StatCardType = 'simple' | 'progress';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  color?: StatCardColor;
  type?: StatCardType;
  progress?: number;
  maxValue?: number;
}

const iconBg: Record<StatCardColor, string> = {
  primary:  'bg-primary text-white',
  secondary: 'bg-secondary text-white',
  green: 'bg-emerald-50 text-emerald-500',
  red:   'bg-red-50 text-red-500',
};

const progressGradient: Record<StatCardColor, string> = {
  primary:  'from-primary to-tertiary',
  secondary: 'from-secondary to-tertiary',
  green: 'from-emerald-500 to-emerald-400',
  red:   'from-red-500 to-red-400',
};

export default function StatCard({
  title,
  value,
  icon: Icon,
  color = 'primary',
  type = 'simple',
  progress,
  maxValue
}: StatCardProps) {
  const progressPercent = progress !== undefined && maxValue
    ? Math.min(Math.max((progress / maxValue) * 100, 0), 100)
    : 0;

  return (
    <div className="bg-white rounded-lg p-7 flex items-start gap-4 shadow-sm border border-border transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md">
      <div className={`w-12 h-12 rounded-lg flex items-center justify-center shrink-0 ${iconBg[color]}`}>
        <Icon size={28} />
      </div>
      
      <div className="flex-1 min-w-0">
        <p className="text-[14px] font-semibold text-text-muted mb-1.5 uppercase">{title}</p>
        <p className="text-[28px] font-extrabold text-text-dark leading-none m-0">{value}</p>
        
        {type === 'progress' && progress !== undefined && maxValue !== undefined && (
          <div className="mt-3 flex items-center gap-2.5">
            <div className="flex-1 h-2 bg-app-bg rounded-full overflow-hidden">
              <div 
                className={`h-full rounded-full bg-linear-to-r transition-all duration-300 ${progressGradient[color]}`}
                style={{ width: `${progressPercent}%` }}
              />
            </div>
            <span className="text-[12px] font-semibold text-text-muted min-w-10 text-right">
              {Math.round(progressPercent)}%
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
