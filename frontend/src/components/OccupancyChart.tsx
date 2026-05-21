import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';

interface OccupancyDataPoint {
  time: string;
  value: number;
}

interface OccupancyChartProps {
  data: OccupancyDataPoint[];
  maxCapacity?: number;
  currentValue?: number;
}

const defaultData: OccupancyDataPoint[] = [
  { time: '18:00', value: 35 },
  { time: '18:10', value: 75 },
  { time: '18:20', value: 115 },
  { time: '18:30', value: 140 },
  { time: '18:40', value: 165 },
  { time: '18:50', value: 184 },
];

export default function OccupancyChart({
  data = defaultData,
  maxCapacity = 300,
  currentValue = 184
}: OccupancyChartProps) {
  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-border">
      <div className="flex justify-between items-start mb-5">
        <div>
          <h3 className="text-base font-bold text-text-dark m-0 mb-1">Evolução da ocupação</h3>
          <p className="text-[13px] text-text-muted m-0">Monitoramento em tempo real</p>
        </div>
        <div className="flex items-baseline gap-1 bg-primary/20 px-4 py-2 rounded-xl">
          <span className="text-xs font-medium text-text-muted">Atual:</span>
          <span className="text-2xl font-extrabold text-primary">{currentValue}</span>
          <span className="text-sm font-semibold text-text-muted">/ {maxCapacity}</span>
        </div>
      </div>
      
      <div className="w-full">
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart
            data={data}
            margin={{ top: 20, right: 30, left: 0, bottom: 0 }}
          >
            <defs>
              <linearGradient id="colorOccupancy" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
            </defs>
            
            <CartesianGrid 
              strokeDasharray="3 3" 
              stroke="#e5e7eb" 
              vertical={false} 
            />
            
            <XAxis 
              dataKey="time" 
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#9ca3af', fontSize: 12 }}
              dy={10}
            />
            
            <YAxis 
              domain={[0, maxCapacity]}
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#9ca3af', fontSize: 12 }}
              dx={-10}
              ticks={[0, 75, 150, 225, 300]}
            />
            
            <Tooltip 
              contentStyle={{
                background: '#ffffff',
                border: '1px solid #e5e7eb',
                borderRadius: '12px',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
                padding: '12px 16px'
              }}
              labelStyle={{ color: '#374151', fontWeight: 600, marginBottom: 4 }}
              formatter={(value) => [`${value} pessoas`, 'Ocupação']}
            />
            
            <ReferenceLine 
              y={maxCapacity} 
              stroke="#ef4444" 
              strokeDasharray="5 5"
              label={{ 
                value: 'Capacidade máxima', 
                position: 'right',
                fill: '#ef4444',
                fontSize: 11
              }}
            />
            
            <Area
              type="monotone"
              dataKey="value"
              stroke="#3b82f6"
              strokeWidth={3}
              fill="url(#colorOccupancy)"
              dot={{ fill: '#3b82f6', strokeWidth: 2, stroke: '#ffffff', r: 4 }}
              activeDot={{ r: 6, stroke: '#3b82f6', strokeWidth: 2 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

