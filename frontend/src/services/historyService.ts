import { historyRecords } from '../data/historyMock';
import type { HistoryRecord } from '../types/history';

export async function getHistoryRecords(): Promise<HistoryRecord[]> {
  // Substituir por chamada de API real quando o endpoint de histórico estiver disponível.
  return historyRecords;
}
