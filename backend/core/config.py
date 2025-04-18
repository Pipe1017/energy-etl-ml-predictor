# backend/core/config.py
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Carga el archivo .env desde el directorio raíz del proyecto
# Asume que este archivo está dos niveles arriba de core/
DOTENV_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path=DOTENV_PATH)
print(f"Intentando cargar .env desde: {DOTENV_PATH}") # Log para verificar path

class Settings(BaseSettings):
    # Lee las variables del .env (o del entorno del sistema)
    POSTGRES_APP_USER: str = "default_user"
    POSTGRES_APP_PASSWORD: str = "default_password"
    POSTGRES_APP_DB: str = "default_db"
    POSTGRES_APP_HOST: str = "localhost" # Usará 'app-db' en Docker
    POSTGRES_APP_PORT: str = "5432"

    # Construye la URL de la base de datos
    # Usa property para asegurar que use los valores cargados
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_APP_USER}:{self.POSTGRES_APP_PASSWORD}@"
            f"{self.POSTGRES_APP_HOST}:{self.POSTGRES_APP_PORT}/{self.POSTGRES_APP_DB}"
        )

    # Configuración para pydantic-settings V2
    model_config = SettingsConfigDict(
        env_file=DOTENV_PATH, # Indica dónde buscar el archivo .env
        env_file_encoding='utf-8',
        case_sensitive=True, # Distingue mayúsculas/minúsculas en variables de entorno
        extra='ignore' # Ignora variables extra en .env que no estén definidas aquí
    )

# Crea una instancia global de la configuración
settings = Settings()

# Log para verificar que la URL se construye correctamente
print(f"Database URL construida: postgresql+psycopg2://{settings.POSTGRES_APP_USER}:***@{settings.POSTGRES_APP_HOST}:{settings.POSTGRES_APP_PORT}/{settings.POSTGRES_APP_DB}")