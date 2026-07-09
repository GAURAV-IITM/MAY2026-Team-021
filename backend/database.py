from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base,sessionmaker

DATABASE_URL = "sqlite:///library.db"

engine = create_engine(
    DATABASE_URL, 
    connect_args={'check_same_thread':False} 
)

SessionLocal = sessionmaker(
    autocommit = False, #wont save directly, will wait for the instructions 
    autoflush = False,  #this will wait till the coder decides to commit changes
    bind=engine
)

Base = declarative_base()
