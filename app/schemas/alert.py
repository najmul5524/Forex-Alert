from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class AlertBase(BaseModel):
    symbol: str
    timeframe: str = "1m"
    condition_type: str
    params: Dict[str, Any] = Field(default_factory=dict)
    trigger_frequency: str = "only_once"
    cooldown_minutes: int = 5
    channels: List[str] = Field(default_factory=lambda: ["push", "in_app"])
    target_email: Optional[str] = None
    webhook_url: Optional[str] = None
    message: Optional[str] = None
    is_active: bool = True

class AlertCreate(AlertBase):
    pass

class AlertUpdate(BaseModel):
    symbol: Optional[str] = None
    timeframe: Optional[str] = None
    condition_type: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    trigger_frequency: Optional[str] = None
    cooldown_minutes: Optional[int] = None
    channels: Optional[List[str]] = None
    target_email: Optional[str] = None
    webhook_url: Optional[str] = None
    message: Optional[str] = None
    is_active: Optional[bool] = None

class AlertResponse(AlertBase):
    id: int
    created_at: datetime
    last_triggered_at: Optional[datetime] = None
    trigger_count: int = 0

    model_config = ConfigDict(from_attributes=True)
