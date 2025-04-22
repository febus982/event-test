from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class BalanceOperationEvent(BaseModel):
    type: Literal["deposit", "withdraw"]
    amount: Annotated[Decimal, Field(decimal_places=2, gt=0)]
    user_id: Annotated[int, Field(gt=0)]
    t: Annotated[int, Field(gt=0)]
