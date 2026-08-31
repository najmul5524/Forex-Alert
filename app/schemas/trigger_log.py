from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class TriggerLogResponse(BaseModel):
    id: int
    alert_id: Optional[int] = None
    symbol: str
    condition_summary: str
    trigger_price: float
    timeframe: str
    channels_sent: List[str]
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
