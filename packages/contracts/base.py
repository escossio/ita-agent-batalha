from datetime import date, datetime
from typing import Annotated, Literal
from pydantic import AfterValidator, BaseModel, ConfigDict, Field

def calendar_date(value: str) -> str:
    date.fromisoformat(value)
    return value


def utc_timestamp(value: str) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset().total_seconds() != 0:
        raise ValueError("UTC timestamp required")
    return value


Identifier = Annotated[str, Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$")]
CorrelationID = Annotated[str, Field(pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")]
Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Day = Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$"), AfterValidator(calendar_date)]
Timestamp = Annotated[str, Field(max_length=32), AfterValidator(utc_timestamp)]
Money = Annotated[int, Field(ge=-10**12, le=10**12)]
Amount = Annotated[int, Field(ge=0, le=10**12)]
class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, validate_default=True)


class Contract(Record):
    schema_version: Literal["1.0"]
