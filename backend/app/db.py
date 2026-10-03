from sqlmodel import create_engine, Session, SQLModel
from . import models

sqlite_file_name = "data/itc_shield.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=False)

def init_db():
    import os
    os.makedirs(os.path.dirname(sqlite_file_name), exist_ok=True)
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
