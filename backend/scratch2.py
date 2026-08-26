import os
from sqlalchemy import create_engine, text

engine = create_engine("postgresql://postgres:postgres@localhost:5432/codeguardian_db")
with engine.connect() as conn:
    res = conn.execute(text("SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = 'patches_status_check';"))
    for row in res:
        print(row)
