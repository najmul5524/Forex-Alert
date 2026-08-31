from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class DeviceTokenRegister(BaseModel):
    token: str
    device_name: Optional[str] = "Android Smartphone"
    platform: Optional[str] = "android"

class DeviceTokenResponse(BaseModel):
    id: int
    token: str
    device_name: Optional[str]
    platform: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
