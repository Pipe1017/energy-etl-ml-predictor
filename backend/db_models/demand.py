# backend/db_models/demand.py
from sqlalchemy import Column, Integer, Float, DateTime, String, Index
from sqlalchemy.sql import func
from core.database import Base # Importa la Base declarativa

class DemandaHistorico(Base):
    __tablename__ = "demanda_historico" # Nombre de la tabla en la BD

    # CAMBIAR AQUÍ: de 'datetime_col' a 'datetime'
    datetime = Column(DateTime(timezone=True), index=True, nullable=False, primary_key=True)
    kwh = Column(Float, nullable=True)
    mes = Column(Integer, nullable=True)
    hour = Column(Integer, nullable=True)
    season = Column(Integer, nullable=True)
    dia_habil = Column(Integer, nullable=True)

    # Mantenemos el índice, pero podríamos ajustar su nombre si quisiéramos (opcional)
    __table_args__ = (Index('ix_demanda_historico_datetime', 'datetime'),) # Actualizar nombre de columna aquí también

# La clase DemandaPrediccion no necesita cambios aquí (asumiendo que sus nombres de columna SÍ coinciden)
class DemandaPrediccion(Base):
    __tablename__ = "demanda_prediccion"
    # ... (sin cambios respecto a la versión anterior que funcionaba al arrancar) ...
    prediction_run_ts = Column(DateTime(timezone=True), default=func.now(), index=True)
    prediction_for_datetime = Column(DateTime(timezone=True), index=True, primary_key=True)
    predicted_kwh = Column(Float)
    model_version = Column(String, nullable=True)
    __table_args__ = (Index('ix_demanda_prediccion_run_for', 'prediction_run_ts', 'prediction_for_datetime'),)