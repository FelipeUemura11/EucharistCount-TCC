import { useEffect, useState } from 'react';
import { historyRecords } from '../data/historyMock';
import { getHistoryRecords } from '../services/historyService';
import type { HistoryRecord } from '../types/history';

export function useHistoryData() {
  const [records, setRecords] = useState<HistoryRecord[]>(historyRecords);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    let isMounted = true;

    async function loadHistory() {
      setIsLoading(true);
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

  return {
    records,
    isLoading,
  };
}
