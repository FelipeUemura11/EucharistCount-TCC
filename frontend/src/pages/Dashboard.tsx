import Header from '../components/Header'
import StatCard from '../components/StatCard'
import OccupancyChart from '../components/OccupancyChart'
import CelebrationSummary from '../components/CelebrationSummary'
import { Users, Building2, LogIn, LogOut, Church, Clock2, ChartNoAxesCombined, DoorOpen } from 'lucide-react'

const occupancyData = [
  { time: '18:00', value: 35 },
  { time: '18:10', value: 75 },
  { time: '18:20', value: 115 },
  { time: '18:30', value: 140 },
  { time: '18:40', value: 165 },
  { time: '18:50', value: 184 },
];

const celebrationSummary = [
  { icon: Church, label: 'Celebração', value: 'Missa das 19h' },
  { icon: Clock2, label: 'Início do monitoramento', value: '18:00' },
  { icon: ChartNoAxesCombined, label: 'Pico de ocupação', value: '192 pessoas' },
  { icon: DoorOpen, label: 'Porta monitorada', value: 'Entrada principal' },
];

export default function Dashboard() {
    const handleStartCount = () => {
        console.log('Iniciando contagem...');
    };

    const handleEndCount = () => {
        console.log('Encerrando contagem...');
    };
    return (
        <div>
            <Header
                title="Dashboard de Ocupação"
                isActive={true}
                lastUpdate="08:16"
            />
            <main className="flex-1 px-8 pt-7 pb-10 flex flex-col gap-6">
                <section>
                    <div className="mx-auto grid grid-cols-4 gap-5">
                        <StatCard
                            title="Pessoas presentes"
                            value={184}
                            icon={Users}
                            color="secondary"
                            type="simple"
                        />
                        <StatCard
                            title="Capacidade"
                            value="184 / 300"
                            icon={Building2}
                            color="secondary"
                            type="progress"
                            progress={184}
                            maxValue={300}
                        />
                        <StatCard
                            title="Entradas"
                            value={207}
                            icon={LogIn}
                            color="secondary"
                            type="simple"
                        />
                        <StatCard
                            title="Saídas"
                            value={23}
                            icon={LogOut}
                            color="secondary"
                            type="simple"
                        />
                    </div>
                </section>
                <section>
                <div className="grid grid-cols-[1fr_380px] gap-6 max-[1400px]:grid-cols-[1fr_340px]">
                    <div className="min-w-0">
                    <OccupancyChart 
                        data={occupancyData}
                        maxCapacity={300}
                        currentValue={184}
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
