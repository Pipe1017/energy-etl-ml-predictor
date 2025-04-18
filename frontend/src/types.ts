// src/types.ts (o similar)

export interface HistoricalDemandPoint {
  // Nombres deben coincidir con tu esquema Pydantic 'DemandaHistoricoRead'
  datetime: string; // Asumiendo que FastAPI lo serializa como string ISO
  kwh: number | null;
  // otros campos si los necesitas... mes, hour, etc.
}

export interface PredictedDemandPoint {
  // Nombres deben coincidir con tu esquema Pydantic 'DemandaPrediccionRead'
  prediction_run_ts: string; // Asumiendo string ISO
  prediction_for_datetime: string; // Asumiendo string ISO
  predicted_kwh: number | null;
  model_version: string | null;
}

// Estructura combinada para el gráfico
export interface CombinedDemandPoint {
  x: number; // Timestamp en milisegundos para Chart.js
  y_hist: number | null; // Valor histórico para este timestamp
  y_pred: number | null; // Valor predicho para este timestamp
}