from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config

engine = create_engine()
SessionLocal = sessionmaker(bind=engine)