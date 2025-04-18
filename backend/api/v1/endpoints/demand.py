# backend/api/v1/endpoints/demand.py
import logging
from typing import Optional, List # Importar List
from datetime import datetime
import pendulum # Para manejo robusto de fechas y zonas horarias

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.database import get_db # Dependencia para la sesión de BD
# Importar modelos SQLAlchemy (usar alias para claridad)
from db_models.demand import DemandaHistorico as DBDemandaHistorico
from db_models.demand import DemandaPrediccion as DBDemandaPrediccion
# Importar esquemas Pydantic (usar alias si hay conflicto, aunque aquí no)
from schemas.demand import DemandaHistoricoPaginated, DemandaPrediccionRead

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/demand", # Prefijo para todas las rutas en este router
    tags=["demand"],  # Etiqueta para la documentación Swagger/OpenAPI
)

@router.get(
    "/historical",
    response_model=DemandaHistoricoPaginated, # Usa el schema paginado!
    summary="Obtener demanda histórica",
    description="Recupera datos históricos de demanda con paginación y filtro opcional por rango de fechas. El rango máximo por consulta es de 1 año. Si no se especifican fechas, devuelve el último año."
)
def read_historical_demand(
    skip: int = Query(0, ge=0, description="Número de registros a saltar (para paginación)"),
    limit: int = Query(1000, ge=1, le=8760, description="Número máximo de registros a devolver (máx 1 año ~ 8760 horas)"), # Limitar a 1 año aprox
    start_date: Optional[str] = Query(None, alias="start_date", description="Fecha de inicio (YYYY-MM-DD o formato ISO 8601)"),
    end_date: Optional[str] = Query(None, alias="end_date", description="Fecha de fin (YYYY-MM-DD o formato ISO 8601)"),
    db: Session = Depends(get_db) # Inyección de dependencia de la sesión de BD
):
    logger.info(f"GET /demand/historical?skip={skip}&limit={limit}&start_date={start_date}&end_date={end_date}")

    start_datetime: Optional[pendulum.DateTime] = None
    end_datetime: Optional[pendulum.DateTime] = None
    timezone = "America/Bogota" # O la zona horaria relevante

    # --- Parseo y Validación de Fechas ---
    try:
        if start_date:
            # pendulum es bueno parseando varios formatos e infiere timezone si está presente
            start_datetime = pendulum.parse(start_date)
            # Si no tiene timezone, asume el local de la API
            if not start_datetime.tzinfo:
                 start_datetime = pendulum.instance(start_datetime, tz=timezone)
        if end_date:
            end_datetime = pendulum.parse(end_date)
            # Si no tiene timezone, asume el local de la API
            if not end_datetime.tzinfo:
                 end_datetime = pendulum.instance(end_datetime, tz=timezone)
            # Para que la fecha final incluya todo el día, ir hasta el final del día
            # end_datetime = end_datetime.end_of('day') # O ajustar según necesidad

    except Exception as e:
        logger.error(f"Error parseando fechas: start='{start_date}', end='{end_date}'. Error: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Formato de fecha inválido para start_date o end_date. Usa YYYY-MM-DD o ISO 8601. Error: {e}"
        )

    # --- Lógica de Fechas por Defecto y Validación de Rango ---
    if not start_datetime and not end_datetime:
        # Por defecto, el último año desde ahora
        end_datetime = pendulum.now(tz=timezone)
        start_datetime = end_datetime.subtract(years=1)
        logger.info(f"No se proporcionaron fechas. Usando rango por defecto: {start_datetime} a {end_datetime}")
    elif not start_datetime:
         # Si solo se da end_date, calcula un año hacia atrás desde end_date
         start_datetime = end_datetime.subtract(years=1)
    elif not end_datetime:
         # Si solo se da start_date, calcula un año hacia adelante desde start_date
         end_datetime = start_datetime.add(years=1)

    # Validar que el rango no supere ~1 año (366 días)
    if (end_datetime - start_datetime).days > 366:
        logger.warning(f"Rango de fechas solicitado ({start_datetime} a {end_datetime}) excede 1 año.")
        raise HTTPException(
            status_code=400,
            detail="El rango de fechas solicitado excede el máximo permitido de 1 año (366 días)."
        )

    # --- Consulta a la Base de Datos ---
    try:
        query = db.query(DBDemandaHistorico)

        # Aplicar filtros de fecha (asegúrate que datetime_col en BD tenga timezone o compara consistentemente)
        if start_datetime:
            query = query.filter(DBDemandaHistorico.datetime >= start_datetime)
        if end_datetime:
            # Usar '<=' para incluir la fecha final
            query = query.filter(DBDemandaHistorico.datetime <= end_datetime)

        # Obtener el total de registros que coinciden con el filtro *antes* de aplicar skip/limit
        total = query.count()
        logger.info(f"Total de registros encontrados para el filtro: {total}")

        # Aplicar orden, paginación (offset/skip) y límite
        records = (
            query.order_by(DBDemandaHistorico.datetime.asc()) # O .desc() si prefieres los más recientes primero
            .offset(skip)
            .limit(limit)
            .all() # Ejecutar la consulta y obtener todos los resultados para esta página
        )
        logger.info(f"Devolviendo {len(records)} registros para la página actual (skip={skip}, limit={limit}).")

        # Devolver en el formato esperado por DemandaHistoricoPaginated
        return {
            "total": total,
            "results": records # FastAPI/Pydantic convertirán los objetos ORM a dicts según DemandaHistoricoRead
        }

    except Exception as e:
        logger.error(f"Error al consultar demanda histórica: {e}", exc_info=True) # exc_info=True para loggear el traceback
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error interno al consultar los datos históricos."
        )

@router.get(
    "/predictions",
    response_model=List[DemandaPrediccionRead], # La respuesta es una lista del schema de lectura
    summary="Obtener predicciones de demanda",
    description="Recupera las predicciones de demanda más recientes, ordenadas por fecha de ejecución y luego por fecha de predicción."
)
def read_predicted_demand(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=2000, description="Número máximo de registros a devolver"),
    db: Session = Depends(get_db)
):
    logger.info(f"GET /demand/predictions?skip={skip}&limit={limit}")
    try:
        # Obtener las predicciones, ordenando primero por la ejecución más reciente,
        # y luego por la fecha para la que se hizo la predicción.
        results = (
            db.query(DBDemandaPrediccion)
            .order_by(
                DBDemandaPrediccion.prediction_run_ts.desc(), # Más recientes primero
                DBDemandaPrediccion.prediction_for_datetime.asc() # Dentro de una ejecución, ordenar cronológicamente
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
        logger.info(f"Devolviendo {len(results)} registros de predicciones.")
        return results # FastAPI/Pydantic convertirán la lista de objetos ORM

    except Exception as e:
        logger.error(f"Error al consultar predicciones de demanda: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error interno al consultar las predicciones."
        )