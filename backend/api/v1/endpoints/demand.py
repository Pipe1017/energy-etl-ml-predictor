# backend/api/v1/endpoints/demand.py
import logging
from typing import Optional, List
from datetime import datetime
import pendulum # Para manejo robusto de fechas y zonas horarias

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func # Importar func para count

from core.database import get_db
from db_models.demand import DemandaHistorico as DBDemandaHistorico
from db_models.demand import DemandaPrediccion as DBDemandaPrediccion
from schemas.demand import DemandaHistoricoRead, DemandaHistoricoPaginated, DemandaPrediccionRead # Asegúrate que DemandaHistoricoRead esté importado

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/demand", tags=["demand"])

@router.get("/historical", response_model=DemandaHistoricoPaginated)
def read_historical_demand(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    try:
        # Construir consulta base
        query = db.query(DBDemandaHistorico).order_by(DBDemandaHistorico.datetime.asc())
        
        # Aplicar filtros de fecha
        if start_date:
            query = query.filter(DBDemandaHistorico.datetime >= start_date)
        if end_date:
            query = query.filter(DBDemandaHistorico.datetime <= end_date)
        
        # Obtener resultados
        results = query.all()
        total = query.count()
        
        return {"total": total, "results": results}
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )


# --- Endpoint de Predicciones (Revisar también sus límites) ---
@router.get(
    "/predictions",
    response_model=List[DemandaPrediccionRead],
    summary="Obtener predicciones de demanda",
    description="Recupera las predicciones de demanda más recientes, ordenadas por fecha de ejecución y luego por fecha de predicción."
)
def read_predicted_demand(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    # ACTUALIZADO: Revisar si este límite también debe eliminarse o aumentarse
    limit: Optional[int] = Query(100, ge=1, description="Número máximo de registros a devolver (opcional, default 100)"), # le=2000 eliminado
    db: Session = Depends(get_db)
):
    logger.info(f"GET /demand/predictions?skip={skip}&limit={limit}")
    try:
        query = db.query(DBDemandaPrediccion)

        query = query.order_by(
            DBDemandaPrediccion.prediction_run_ts.desc(),
            DBDemandaPrediccion.prediction_for_datetime.asc()
        )

        query = query.offset(skip)

        # Aplicar límite si se proporciona
        if limit is not None:
             query = query.limit(limit)
             logger.info(f"Aplicando limit={limit} a predicciones")
        else:
             logger.warning("No se especificó límite para predicciones. Se devolverán todos.")


        results = query.all()

        logger.info(f"Devolviendo {len(results)} registros de predicciones.")
        return results

    except Exception as e:
        logger.error(f"Error al consultar predicciones de demanda: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error interno al consultar las predicciones."
        )