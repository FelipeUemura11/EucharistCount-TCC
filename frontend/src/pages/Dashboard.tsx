import CelebrationSummary from '../components/dashboard/CelebrationSummary'
import DashboardStats from '../components/dashboard/DashboardStats'
import OccupancyChart from '../components/dashboard/OccupancyChart'
import PageHeader from '../components/layout/PageHeader'
import { useDashboardData } from '../hooks/useDashboardData'

export default function Dashboard() {
    const { data, isLoading } = useDashboardData()
    const { metrics, occupancyData, celebrationSummary } = data

    const handleStartCount = () => {
        console.log('Iniciando contagem...');
    };

    const handleEndCount = () => {
        console.log('Encerrando contagem...');
    };

    return (
        <div>
            <PageHeader
                title={isLoading ? 'Carregando dashboard...' : 'Dashboard de Ocupação'}
                isActive={metrics.isCountingActive}
                lastUpdate={metrics.lastUpdate}
            />
            <main className="flex-1 px-8 pt-7 pb-10 flex flex-col gap-6 max-[640px]:px-4">
                <DashboardStats metrics={metrics} />
                <section>
                <div className="grid grid-cols-[1fr_380px] gap-6 max-[1400px]:grid-cols-[1fr_340px] max-[1024px]:grid-cols-1">
                    <div className="min-w-0">
                    <OccupancyChart 
                        data={occupancyData}
                        maxCapacity={metrics.maxCapacity}
                        currentValue={metrics.currentOccupancy}
                    />
                    </div>
                    <div className="min-w-0">
                    <CelebrationSummary 
                        items={celebrationSummary}
                        onStartCount={handleStartCount}
                        onEndCount={handleEndCount}
                    />
                    </div>
                </div>
                </section>
            </main>
            
        </div>
    )
}
