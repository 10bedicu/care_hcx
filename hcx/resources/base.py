from datetime import datetime

from pydantic import BaseModel, model_validator


class PeriodSpec(BaseModel):
    start: datetime | None = None
    end: datetime | None = None

    @model_validator(mode="after")
    def validate_period(self):
        if (self.start and self.end) and (self.start > self.end):
            raise ValueError("Start date cannot be greater than end date")
        return self
