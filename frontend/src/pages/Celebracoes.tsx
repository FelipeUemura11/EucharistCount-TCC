import { useMemo, useState } from "react";
import CalendarioCelebracoes from "../components/celebracoes/CalendarioCelebracoes";
import ModalHorariosDia from "../components/celebracoes/ModalHorariosDia";
import TabelaProximasCelebracoes from "../components/celebracoes/TabelaProximasCelebracoes";
import {
    calendarDays,
    celebrationMonth,
    createInitialDaySchedules,
    getDayInfo,
    nextCelebrations,
    weekDays,
} from "../data/celebrationsMock";
import type { CelebrationMassScheduleChanges } from "../types/celebrations";

export default function Celebracoes() {
    const [selectedDay, setSelectedDay] = useState<number | null>(null);
    const [daySchedules, setDaySchedules] = useState(createInitialDaySchedules);

    const selectedDayInfo = useMemo(
        () => (selectedDay ? getDayInfo(selectedDay) : null),
        [selectedDay],
    );

    const selectedDaySchedules = selectedDay
        ? (daySchedules[selectedDay] ?? [])
        : [];

    const addSchedule = () => {
        if (!selectedDay) {
            return;
        }

        setDaySchedules((currentSchedules) => ({
            ...currentSchedules,
            [selectedDay]: [
                ...(currentSchedules[selectedDay] ?? []),
                {
                    id: `day-${selectedDay}-custom-${Date.now()}`,
                    startTime: "18:00",
                    recordingStartTime: "18:00",
                    recordingEndTime: "19:00",
                    source: "custom",
                },
            ],
        }));
    };

    const updateSchedule = (
        scheduleId: string,
        changes: CelebrationMassScheduleChanges,
    ) => {
        if (!selectedDay) {
            return;
        }

        setDaySchedules((currentSchedules) => ({
            ...currentSchedules,
            [selectedDay]: (currentSchedules[selectedDay] ?? []).map(
                (schedule) =>
                    schedule.id === scheduleId
                        ? { ...schedule, ...changes, source: "custom" }
                        : schedule,
            ),
        }));
    };

    const removeSchedule = (scheduleId: string) => {
        if (!selectedDay) {
            return;
        }

        setDaySchedules((currentSchedules) => ({
            ...currentSchedules,
            [selectedDay]: (currentSchedules[selectedDay] ?? []).filter(
                (schedule) => schedule.id !== scheduleId,
            ),
        }));
    };

    return (
        <>
            <div className="mb-6">
                <div>
                    <p className="m-0 text-sm font-semibold uppercase text-text-muted">
                        Agenda litúrgica
                    </p>
                    <h2 className="m-0 mt-1 text-2xl font-extrabold text-text-dark">
                        {celebrationMonth.label}
                    </h2>
                </div>
            </div>

            <CalendarioCelebracoes
                calendarDays={calendarDays}
                monthLabel={celebrationMonth.label}
                selectedDay={selectedDay}
                weekDays={weekDays}
                onSelectDay={setSelectedDay}
            />

            <TabelaProximasCelebracoes celebracoes={nextCelebrations} />

            {selectedDayInfo && (
                <ModalHorariosDia
                    dayInfo={selectedDayInfo}
                    schedules={selectedDaySchedules}
                    onAddSchedule={addSchedule}
                    onClose={() => setSelectedDay(null)}
                    onRemoveSchedule={removeSchedule}
                    onSave={() => setSelectedDay(null)}
                    onUpdateSchedule={updateSchedule}
                />
            )}
        </>
    );
}
