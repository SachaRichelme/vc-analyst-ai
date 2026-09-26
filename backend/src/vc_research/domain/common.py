from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, Field

def nonblank(value: str) -> str:
    if not value.strip():
        raise ValueError("blank text is not a value")
    return value


Text = Annotated[str, Field(strict=True, min_length=1), AfterValidator(nonblank)]


def utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must include timezone")
    return value.astimezone(timezone.utc)


Timestamp = Annotated[datetime, AfterValidator(utc)]


def exact_decimal(value):
    if isinstance(value, (float, bool)):
        raise ValueError("use a decimal string or Decimal, not float/bool")
    return value


Number = Annotated[Decimal, BeforeValidator(exact_decimal), Field(allow_inf_nan=False)]
Nonnegative = Annotated[Number, Field(ge=0)]
Count = Annotated[int, Field(strict=True, ge=0)]
PositiveCount = Annotated[int, Field(strict=True, gt=0)]
Mode = Literal["demo", "live"]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)
    schema_version: Literal["1.0"] = "1.0"


class Record(Contract):
    id: UUID
    mode: Mode


class Versions(Contract):
    prompt: Text
    model: Text
    model_revision: Text | None = None
    extractor: Text
    policy: Text
    # Unknown model revision remains unknown, not a reproducibility claim.
