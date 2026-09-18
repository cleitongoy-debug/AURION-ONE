from typing import Literal

from pydantic import BaseModel, Field


class DeviceState(BaseModel):
    device_id: str = Field(min_length=2, max_length=80)
    source: Literal["poco", "helmet", "band", "panel", "pc"]
    moving: bool = False
    battery_percent: int | None = Field(default=None, ge=0, le=100)


class PromptRequest(BaseModel):
    text: str = Field(min_length=1, max_length=8000)
    device_id: str = Field(min_length=2, max_length=80)
    moving: bool = False


class PromptResponse(BaseModel):
    status: Literal["completed", "blocked", "disabled"]
    answer: str

