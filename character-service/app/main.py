from fastapi import FastAPI
from app.characters.router import router as character_router
from app.database import Base, engine

app = FastAPI()

app.include_router(character_router)


def create_db_tables():
    Base.metadata.create_all(bind=engine)

create_db_tables()

@app.get("/")
def root():
    return {"message": "Hello World"}
