# This is an example storage implementation, not thread safe and not efficient.
# We should use a proper database here
from typing import Literal

from domains.balance.models import BalanceOperation

_balance_storage: dict[int, list[BalanceOperation]] = {}
"""
Structure of the storage:
{
    # user_id: list of BalanceOperations
    1: [
        BalanceOperation(...),
        BalanceOperation(...),
        BalanceOperation(...)
    ]
}
"""


class BalanceRepository:
    async def save_operation(self, operation: BalanceOperation) -> None:
        if not _balance_storage.get(operation.user_id):
            _balance_storage[operation.user_id] = []

        _balance_storage[operation.user_id].append(operation)
        _balance_storage[operation.user_id].sort(key=lambda x: x.t)

    async def get_last_n_operations_by_time(
        self, user_id: int, min_t: int, op_type: None | Literal["deposit", "withdraw"] = None
    ) -> list[BalanceOperation]:
        if op_type:
            operations = [x for x in _balance_storage.get(user_id, []) if (x.type == op_type and x.t >= min_t)]
        else:
            operations = [x for x in _balance_storage.get(user_id, []) if x.t >= min_t]
        return operations

    async def get_last_n_operations(
        self, user_id: int, num_operations: int, op_type: None | Literal["deposit", "withdraw"] = None
    ) -> list[BalanceOperation]:
        if op_type:
            operations = [x for x in _balance_storage.get(user_id, []) if x.type == op_type]
        else:
            operations = [*_balance_storage.get(user_id, [])]

        return operations[-num_operations:]
