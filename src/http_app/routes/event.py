from decimal import Decimal
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, computed_field

from domains.balance import BalanceEventServiceInterface, get_balance_service

router = APIRouter(prefix="/event", tags=["event"])


def is_string(value: Any) -> str:
    if isinstance(value, str):
        return value
    else:
        raise ValueError(f"{value} is not a string")


class EventRequest(BaseModel):
    # Make sure to implement the relevant code in the `ingest_event` function\
    # when adding new operation types!!!!!!
    type: Literal["deposit", "withdraw"]
    # Theoretically Decimal can handle both string and number input, however the requirements
    # seem to suggest only string values should be accepted, therefore I added specific validation on input type.
    amount: Annotated[Decimal, BeforeValidator(is_string), Field(decimal_places=2, gt=0)]
    user_id: Annotated[int, Field(gt=0)]
    t: Annotated[int, Field(gt=0)]

    model_config = ConfigDict(
        json_schema_extra={"example": {"type": "deposit", "amount": "42.00", "user_id": 1, "t": 10}}
    )


class EventResponse(BaseModel):
    alert_codes: list[int]
    user_id: int

    @computed_field  # type: ignore[misc]
    @property
    def alert(self) -> bool:
        return bool(self.alert_codes)

    model_config = ConfigDict(json_schema_extra={"example": {"alert": True, "alert_codes": [30, 123], "user_id": 1}})


@router.post("/")
async def ingest_event(
    event: EventRequest,
    balance_service: Annotated[BalanceEventServiceInterface, Depends(get_balance_service)],
) -> EventResponse:
    alerts = await balance_service.ingest_event(event.type, event.user_id, event.amount, event.t)

    return EventResponse(
        alert_codes=alerts,
        user_id=event.user_id,
    )
