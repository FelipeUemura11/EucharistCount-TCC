import { useMemo, useState } from 'react';
import HistoryFilters from '../components/history/HistoryFilters';
import HistoryRecordsTable from '../components/history/HistoryRecordsTable';
import PageHeader from '../components/layout/PageHeader';
import { useHistoryData } from '../hooks/useHistoryData';
import type { HistoryRecord } from '../types/history';

interface HistoryFilterState {
  searchTerm: string;
  periodInDays: number;
}

function parseDateFromHistory(dateString: string) {
  const [day, month, year] = dateString.split('/').map(Number);

  return new Date(year, month - 1, day);
}

function isWithinPeriod(recordDate: Date, referenceDate: Date, periodInDays: number) {
  const millisecondsInDay = 24 * 60 * 60 * 1000;
  const diffInDays = Math.floor((referenceDate.getTime() - recordDate.getTime()) / millisecondsInDay);

  return diffInDays >= 0 && diffInDays <= periodInDays;
}

function getLatestRecordDate(records: HistoryRecord[]) {
  return records.reduce((latestDate, record) => {
    const recordDate = parseDateFromHistory(record.date);
    return recordDate > latestDate ? recordDate : latestDate;
  }, parseDateFromHistory(records[0].date));
}

export default function History() {
  const { records, isLoading } = useHistoryData();
  const [draftSearchTerm, setDraftSearchTerm] = useState('');
  const [draftPeriodInDays, setDraftPeriodInDays] = useState(30);
  const [appliedFilters, setAppliedFilters] = useState<HistoryFilterState>({
    searchTerm: '',
    periodInDays: 30,
  });

  const filteredRecords = useMemo(() => {
    if (records.length === 0) {
      return [];
    }

    const referenceDate = getLatestRecordDate(records);

    const normalizedSearchTerm = appliedFilters.searchTerm.trim().toLowerCase();

    return records.filter((record) => {
      const searchableText = `${record.celebration} ${record.weekday} ${record.date}`.toLowerCase();
      const matchesSearchTerm = normalizedSearchTerm.length === 0 || searchableText.includes(normalizedSearchTerm);
      const matchesPeriod = isWithinPeriod(parseDateFromHistory(record.date), referenceDate, appliedFilters.periodInDays);

      return matchesSearchTerm && matchesPeriod;
    });
  }, [appliedFilters, records]);

  const applyFilters = () => {
    setAppliedFilters({
      searchTerm: draftSearchTerm,
      periodInDays: draftPeriodInDays,
    });
  };

  const handleExportRecords = () => {
    console.log('Exportando registros de histórico...');
  };

  return (
    <div>
      <PageHeader title={isLoading ? 'Carregando histórico...' : 'Histórico'} isActive={false} />

      <main className="min-w-0 flex-1 overflow-x-hidden px-8 pt-7 pb-10 max-[640px]:px-4">
        <HistoryFilters
          searchTerm={draftSearchTerm}
          periodInDays={draftPeriodInDays}
          onSearchTermChange={setDraftSearchTerm}
          onPeriodInDaysChange={setDraftPeriodInDays}
          onApplyFilters={applyFilters}
        />

        <HistoryRecordsTable records={filteredRecords} onExport={handleExportRecords} />
      </main>
    </div>
  );
}
