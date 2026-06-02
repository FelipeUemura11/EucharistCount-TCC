import { Camera, Database, Gauge, Server } from 'lucide-react';
import type { HealthItem, HealthStatus } from '../types/settings';

export const healthItems: HealthItem[] = [
  { label: 'API local',    detail: 'http://localhost:8000', status: 'online',  icon: Server },
  { label: 'Banco SQLite', detail: 'eucharist_count.db',   status: 'online',  icon: Database },
  { label: 'Câmera',       detail: 'Entrada principal',    status: 'online',  icon: Camera },
  { label: 'Modelo YOLO',  detail: 'GPU habilitada',       status: 'warning', icon: Gauge },
];

export const healthStyle: Record<HealthStatus, string> = {
  online:  'bg-emerald-50 text-emerald-600 border-emerald-100',
  warning: 'bg-amber-50 text-amber-600 border-amber-100',
  offline: 'bg-red-50 text-red-600 border-red-100',
};

export const healthLabel: Record<HealthStatus, string> = {
  online:  'Conectado',
  warning: 'Atenção',
  offline: 'Offline',
};
