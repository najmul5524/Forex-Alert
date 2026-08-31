import datetime
from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base

class DeviceToken(Base):
    __tablename__ = "device_tokens"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    token = Column(String(500), unique=True, nullable=False, index=True)
    device_name = Column(String(100), nullable=True, default="Android Device")
    platform = Column(String(20), default="android")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_active_at = Column(DateTime, default=datetime.datetime.utcnow)
