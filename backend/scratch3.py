import os
from sqlalchemy import create_engine, text

engine = create_engine("postgresql://postgres:postgres@localhost:5432/codeguardian_db")
with engine.connect() as conn:
    conn.execute(text("UPDATE repositories SET owner = 'sunilkumarb2007' WHERE name = 'CodeGuardian';"))
    conn.commit()
    print("Repository owner updated to sunilkumarb2007")
