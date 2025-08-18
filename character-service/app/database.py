from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine

# Cambiado de PostgreSQL a SQLite
#SQLALCHEMY_DATABASE_URL = "sqlite:///./characters.db"
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:secret@localhost:5431/chatbot"

# Para SQLite, connect_args es necesario para permitir múltiples hilos
engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():  # Cambiado de async def a def
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() # Cambiado de await db.close() a db.close()
