from sqlalchemy import text
from app.db.database import SessionLocal
db = SessionLocal()
res = db.execute(text("SELECT conname, pg_get_constraintdef(c.oid) FROM pg_constraint c JOIN pg_class t ON c.conrelid = t.oid;")).fetchall()
for r in res:
    print(r[0], r[1])
