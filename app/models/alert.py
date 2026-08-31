import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from app.database import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    symbol = Column(String(30), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, default="1m")
    condition_type = Column(String(50), nullable=False)
    params = Column(JSON, nullable=False, default=dict)
    trigger_frequency = Column(String(30), nullable=False, default="only_once")
    cooldown_minutes = Column(Integer, default=5)
    channels = Column(JSON, nullable=False, default=lambda: ["push", "in_app"])
    target_email = Column(String(255), nullable=True)
    webhook_url = Column(String(500), nullable=True)
    message = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_triggered_at = Column(DateTime, nullable=True)
    trigger_count = Column(Integer, default=0)
    last_evaluated_bar_time = Column(Integer, nullable=True)
