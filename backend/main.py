# backend/main.py
import logging
from fastapi import FastAPI
# Importa el router desde la ubicación correcta
from api.v1.endpoints.demand import router as demand_router
from core.database import engine, Base # Importar engine y Base para crear tablas (opcional)

# --- Configuración de Logging (Opcional pero recomendado) ---
# Puedes configurar esto de forma más avanzada si lo necesitas
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Creación de Tablas (Opcional - Solo para desarrollo/primera ejecución) ---
# Descomenta la siguiente línea si quieres que FastAPI cree las tablas
# definidas en tus modelos SQLAlchemy al iniciar (si no existen).
# ¡Cuidado en producción! Es mejor usar herramientas de migración como Alembic.
# try:
#    logger.info("Intentando crear tablas de base de datos si no existen...")
#    Base.metadata.create_all(bind=engine)
#    logger.info("Tablas verificadas/creadas.")
# except Exception as e:
#    logger.error(f"Error al crear las tablas de la base de datos: {e}")

# --- Creación de la Aplicación FastAPI ---
app = FastAPI(
    title="API de Demanda Energética",
    description="API para consultar datos históricos y predicciones de demanda energética.",
    version="1.0.0"
)

# --- Inclusión de Routers ---
# Incluye las rutas definidas en api/v1/endpoints/demand.py
# con el prefijo /api/v1
app.include_router(demand_router, prefix="/api/v1")

# --- Endpoint Raíz (Opcional) ---
@app.get("/")
def read_root():
    logger.info("Acceso al endpoint raíz '/'")
    return {"message": "Bienvenido a la API de Demanda Energética. Accede a la documentación en /docs"}

# --- Instrucciones para Ejecutar (Comentado) ---
# Para ejecutar localmente en desarrollo:
# uvicorn main:app --host 0.0.0.0 --port 8000 --reload

logger.info("Aplicación FastAPI inicializada.")