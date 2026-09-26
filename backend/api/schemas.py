"""
Formato das respostas da API.

Cada modelo espelha, campo a campo e com os mesmos nomes, uma interface
TypeScript de frontend/src/types/. Mudou um lado, mude o outro.
"""

from pydantic import BaseModel


class OccupancyDataPoint(BaseModel):
    time: str
    value: int


class CelebrationSummaryItem(BaseModel):
    icon: str
    label: str
    value: str


class DashboardMetrics(BaseModel):
    currentOccupancy: int
    estimatedCommunicants: int
    entries: int
    exits: int
    isCountingActive: bool


class DashboardOverview(BaseModel):
    metrics: DashboardMetrics
    occupancyData: list[OccupancyDataPoint]
    celebrationSummary: list[CelebrationSummaryItem]


class Celebration(BaseModel):
    id: int
    title: str
    day: int
    weekday: str
    startTime: str
    monitorStart: str
    monitorEnd: str
    expectedPeople: int
    capacity: int
    status: str


class HistoryRecord(BaseModel):
    id: int
    date: str
    weekday: str
    celebration: str
    startTime: str
    totalPeople: int
    estimatedCommunicants: int
    suggestedHosts: int
    entries: int
    exits: int
