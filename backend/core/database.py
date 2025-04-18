# backend/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings # Importa la configuración

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# echo=True imprime las sentencias SQL, útil para debug
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True, pool_pre_ping=True)

# Cada instancia de SessionLocal será una sesión de base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base para nuestros modelos ORM (SQLAlchemy)
Base = declarative_base()

# Dependencia de FastAPI para obtener una sesión de BD en los endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db # Proporciona la sesión al endpoint
    finally:
        db.close() # Cierra la sesión al finalizar

print("SQLAlchemy Engine y SessionLocal creados.")