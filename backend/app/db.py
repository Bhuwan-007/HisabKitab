from sqlmodel import create_engine, Session

sqlite_file_name = "data/itc_shield.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=False)

def get_session():
    with Session(engine) as session:
        yield session
