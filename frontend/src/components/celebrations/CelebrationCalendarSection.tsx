import { CalendarDays, ChevronLeft, ChevronRight } from 'lucide-react';
import type { CalendarDay } from '../../types/celebrations';

interface CelebrationCalendarSectionProps {
  calendarDays: CalendarDay[];
  monthLabel: string;
  selectedDay: number | null;
  weekDays: string[];
  onSelectDay: (day: number) => void;
}

export default function CelebrationCalendarSection({
  calendarDays,
  monthLabel,
  selectedDay,
  weekDays,
  onSelectDay,
}: CelebrationCalendarSectionProps) {
  return (
    <section className="rounded-lg border border-border bg-white p-6 shadow-sm">
      <div className="mb-5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex size-11 items-center justify-center rounded-lg bg-secondary/10 text-secondary">
            <CalendarDays size={24} />
          </div>
          <div>
            <h3 className="m-0 text-base font-bold text-text-dark">Calendário</h3>
            <p className="m-0 text-sm text-text-muted">{monthLabel}</p>
          </div>
        </div>

        <div className="flex gap-2">
          <button type="button" className="flex size-9 items-center justify-center rounded-lg border border-border text-text-muted hover:bg-app-bg">
            <ChevronLeft size={18} />
          </button>
          <button type="button" className="flex size-9 items-center justify-center rounded-lg border border-border text-text-muted hover:bg-app-bg">
            <ChevronRight size={18} />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-7 gap-2">
        {weekDays.map((day) => (
          <div key={day} className="py-2 text-center text-xs font-bold uppercase text-text-muted">
            {day}
          </div>
        ))}

        {calendarDays.map((item) => (
          <button
            key={item.id}
            type="button"
            disabled={!item.day}
            onClick={() => item.day && onSelectDay(item.day)}
            className={`relative flex aspect-square min-h-0 items-center justify-center rounded-lg border text-sm font-bold transition ${
              !item.day
                ? 'cursor-default border-transparent bg-transparent'
                : selectedDay === item.day
                  ? 'border-secondary bg-secondary text-white shadow-sm'
                  : 'border-border bg-white text-text-dark hover:border-secondary/30 hover:bg-secondary/10'
            }`}
          >
            {item.day}
            {item.hasCelebration && (
              <span className={`absolute bottom-2 size-1.5 rounded-full ${selectedDay === item.day ? 'bg-white' : 'bg-secondary'}`} />
            )}
          </button>
        ))}
      </div>
    </section>
  );
}
