import { useState } from 'react';
import CameraProcessingSection from '../components/settings/CameraProcessingSection';
import SettingsActions from '../components/settings/SettingsActions';
import SystemHealthSection from '../components/settings/SystemHealthSection';
import WeeklyMassScheduleSection from '../components/settings/WeeklyMassScheduleSection';
import PageHeader from '../components/layout/PageHeader';
import { createDefaultWeeklySchedule } from '../data/settingsMock';
import type { MassScheduleChanges, WeekdayId } from '../types/settings';

export default function Settings() {
  const [weeklySchedule, setWeeklySchedule] = useState(createDefaultWeeklySchedule);

  const updateMassSchedule = (
    dayId: WeekdayId,
    massId: string,
    changes: MassScheduleChanges
  ) => {
    setWeeklySchedule((currentSchedule) =>
      currentSchedule.map((day) => {
        if (day.id !== dayId) {
          return day;
        }

        return {
          ...day,
          masses: day.masses.map((mass) =>
            mass.id === massId ? { ...mass, ...changes } : mass
          ),
        };
      })
    );
  };

  const resetSettings = () => {
    setWeeklySchedule(createDefaultWeeklySchedule());
  };

  return (
    <div>
      <PageHeader title="Configurações" isActive={false} />

      <main className="flex-1 px-8 pt-7 pb-10">
        <WeeklyMassScheduleSection
          weeklySchedule={weeklySchedule}
          onMassChange={updateMassSchedule}
        />
        <CameraProcessingSection />
        <SystemHealthSection />
        <SettingsActions onReset={resetSettings} />
      </main>
    </div>
  );
}
