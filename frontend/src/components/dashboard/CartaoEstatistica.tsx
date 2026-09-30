import type { LucideIcon } from 'lucide-react';

type CartaoEstatisticaColor = 'primary' | 'secondary' | 'green' | 'red';

interface CartaoEstatisticaProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  color?: CartaoEstatisticaColor;
}

const iconBg: Record<CartaoEstatisticaColor, string> = {
  primary:  'bg-primary text-white',
  secondary: 'bg-secondary text-white',
  green: 'bg-emerald-50 text-emerald-500',
  red:   'bg-red-50 text-red-500',
};

export default function CartaoEstatistica({
  title,
  value,
  icon: Icon,
  color = 'primary'
}: CartaoEstatisticaProps) {
  return (
    <div className="bg-white rounded-lg p-7 flex items-start gap-4 shadow-sm border border-border transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md">
      <div className={`w-12 h-12 rounded-lg flex items-center justify-center shrink-0 ${iconBg[color]}`}>
        <Icon size={28} />
      </div>

      <div className="flex-1 min-w-0">
        <p className="text-[14px] font-semibold text-text-muted mb-1.5 uppercase">{title}</p>
        <p className="text-[28px] font-extrabold text-text-dark leading-none m-0">{value}</p>
      </div>
    </div>
  );
}
