import sys
sys.path.insert(0, ".")
from app.db.session import SessionLocal
from app.db.models import EvidenceEvent
db = SessionLocal()
evidence = db.query(EvidenceEvent).order_by(EvidenceEvent.created_at.desc()).first()
print('Stack trace:', evidence.stack_trace if evidence else 'None')
