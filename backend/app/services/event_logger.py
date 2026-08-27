from datetime import timezone
import logging
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
from app.db.models import RunEvent

logger = logging.getLogger(__name__)

class BackendEventLogger:
    def __init__(self, db: Session, run_id: str):
        self.db = db
        self.run_id = run_id
        self.sequence = 0

    def emit(self, event_type: str, title: str, description: str = None, command: str = None, output: str = None, status: str = "completed"):
        self.sequence += 1
        ev = RunEvent(
            run_id=self.run_id,
            sequence=self.sequence,
            timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            title=title,
            description=description,
            command=command,
            output=output,
            status=status,
            related_entity_type="run",
            related_entity_id=self.run_id
        )
        self.db.add(ev)
        self.db.commit()

