# backend/schemas/demand.py
from pydantic import BaseModel, ConfigDict
from datetime import datetime # <--- Importa el TIPO datetime
from typing import Optional, List

# --- Esquemas Base (campos comunes) ---
class DemandaHistoricoBase(BaseModel):
    # CAMBIAR AQUÍ: de 'datetime_col' a 'datetime'
    datetime: datetime
    kwh: Optional[float] = None
    mes: Optional[int] = None
    hour: Optional[int] = None
    season: Optional[int] = None
    dia_habil: Optional[int] = None

# (DemandaPrediccionBase no cambia)
class DemandaPrediccionBase(BaseModel):
    # ... (sin cambios) ...
    prediction_run_ts: datetime
    prediction_for_datetime: datetime
    predicted_kwh: float
    model_version: Optional[str] = None


# --- Esquemas para Lectura (usados en respuestas API) ---
class DemandaHistoricoRead(DemandaHistoricoBase):
    # Ya no necesita definir 'datetime' porque lo hereda de DemandaHistoricoBase
    # id: int # <-- Esto ya lo habíamos quitado
    model_config = ConfigDict(from_attributes=True)

class DemandaPrediccionRead(DemandaPrediccionBase):
    # id: int # <-- Esto ya lo habíamos quitado
    model_config = ConfigDict(from_attributes=True)

# --- Esquema para Respuesta Paginada de Históricos ---
class DemandaHistoricoPaginated(BaseModel):
    total: int
    results: List[DemandaHistoricoRead] # Usará la versión actualizada de DemandaHistoricoRead