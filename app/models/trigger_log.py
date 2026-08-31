import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from app.database import Base

class TriggerLog(Base):
    __tablename__ = "trigger_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    alert_id = Column(Integer, ForeignKey("alerts.id", ondelete="CASCADE"), nullable=True)
    symbol = Column(String(30), nullable=False, index=True)
    condition_summary = Column(String(255), nullable=False)
    trigger_price = Column(Float, nullable=False)
    timeframe = Column(String(10), nullable=False)
    channels_sent = Column(JSON, nullable=False, default=list)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
