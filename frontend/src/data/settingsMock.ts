import { Camera, Database, Gauge, Server } from 'lucide-react';
import type { HealthItem, HealthStatus, WeeklyScheduleDay } from '../types/settings';

export const healthItems: HealthItem[] = [
  { label: 'API local', detail: 'http://localhost:8000', status: 'online', icon: Server },
  { label: 'Banco SQLite', detail: 'eucharist_count.db', status: 'online', icon: Database },
  { label: 'Câmera', detail: 'Entrada principal', status: 'online', icon: Camera },
  { label: 'Modelo YOLO', detail: 'Detectando pessoas', status: 'warning', icon: Gauge },
];

export const healthStyle: Record<HealthStatus, string> = {
  online: 'bg-emerald-50 text-emerald-600 border-emerald-100',
  warning: 'bg-amber-50 text-amber-600 border-amber-100',
  offline: 'bg-red-50 text-red-600 border-red-100',
};

export const healthLabel: Record<HealthStatus, string> = {
  online: 'Conectado',
  warning: 'Atenção',
  offline: 'Offline',
};

const defaultWeeklySchedule: WeeklyScheduleDay[] = [
  {
    id: 'saturday',
    label: 'Sábado',
    helper: 'Missa única com gravação de 1h',
    masses: [
      {
        id: 'saturday-evening',
        startTime: '18:00',
        recordingStartTime: '18:00',
        recordingEndTime: '19:00',
      },
    ],
  },
  {
    id: 'sunday',
    label: 'Domingo',
    helper: 'Três missas fixas',
    masses: [
      {
        id: 'sunday-morning-8',
        startTime: '08:00',
        recordingStartTime: '08:00',
        recordingEndTime: '09:00',
      },
      {
        id: 'sunday-morning-10',
        startTime: '10:00',
        recordingStartTime: '10:00',
        recordingEndTime: '11:00',
      },
      {
        id: 'sunday-evening',
        startTime: '18:00',
        recordingStartTime: '18:00',
        recordingEndTime: '19:00',
      },
    ],
  },
  {
    id: 'monday',
    label: 'Segunda-feira',
    helper: 'Sem missa fixa',
    masses: [],
  },
  {
    id: 'tuesday',
    label: 'Terça-feira',
    helper: 'Missa única no fim da tarde',
    masses: [
      {
        id: 'tuesday-evening',
        startTime: '18:00',
        recordingStartTime: '18:00',
        recordingEndTime: '18:35',
      },
    ],
  },
  {
    id: 'wednesday',
    label: 'Quarta-feira',
    helper: 'Missa única no fim da tarde',
    masses: [
      {
        id: 'wednesday-evening',
        startTime: '18:00',
        recordingStartTime: '18:00',
        recordingEndTime: '18:35',
      },
    ],
  },
  {
    id: 'thursday',
    label: 'Quinta-feira',
    helper: 'Missa única no fim da tarde',
    masses: [
      {
        id: 'thursday-evening',
        startTime: '18:00',
        recordingStartTime: '18:00',
        recordingEndTime: '18:35',
      },
    ],
  },
  {
    id: 'friday',
    label: 'Sexta-feira',
    helper: 'Missa única no fim da tarde',
    masses: [
      {
        id: 'friday-evening',
        startTime: '18:00',
        recordingStartTime: '18:00',
        recordingEndTime: '18:35',
      },
    ],
  },
];

export function createDefaultWeeklySchedule() {
  return defaultWeeklySchedule.map((day) => ({
    ...day,
    masses: day.masses.map((mass) => ({ ...mass })),
  }));
}