import { useEffect, useState } from 'react';
import { getHistoryRecords } from '../services/historyService';
import type { HistoryRecord } from '../types/history';

export function useHistoryData() {
  const [records, setRecords] = useState<HistoryRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    async function loadHistory() {
      const loadedRecords = await getHistoryRecords();
      if (isMounted) {
        setRecords(loadedRecords);
        setIsLoading(false);
      }
    }

    void loadHistory();

    return () => {
      isMounted = false;
    };
  }, []);

  return { records, isLoading };
}
