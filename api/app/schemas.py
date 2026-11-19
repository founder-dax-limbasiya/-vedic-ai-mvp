from __future__ import annotations

from datetime import date, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


AyanamsaName = Literal["lahiri", "raman", "kp", "true_chitrapaksha"]


class ChartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    birth_date: date
    birth_time: time
    timezone: str = Field(min_length=3, max_length=64, examples=["Asia/Kolkata"])
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    ayanamsa: AyanamsaName = "lahiri"
    fold: Literal[0, 1] | None = None

    @field_validator("timezone")
    @classmethod
    def trim_timezone(cls, value: str) -> str:
        return value.strip()
