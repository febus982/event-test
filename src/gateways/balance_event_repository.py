# This is an example storage implementation, not thread safe and not efficient.
# We should use a proper storage implementation, either permanent or temporary,
# based on the lifecycle we want for events and their use cases.
from typing import Literal

from domains.balance.models import BalanceOperationEvent

_balance_events_storage: dict[int, list[BalanceOperationEvent]] = {}
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


class BalanceEventRepository:
    async def save_operation(self, operation: BalanceOperationEvent) -> None:
        """
        Save a balance operation for a user in the storage. This method stores the operation
        in memory and ensures it gets appended to the list of operations for the given user.
        Operations are sorted by their timestamp (`t`) value to maintain order.

        Parameters:
            operation (BalanceOperationEvent): The balance operation object to be stored. It
            contains user-related and operation-specific data.

        Returns:
            None
        """
        if not _balance_events_storage.get(operation.user_id):
            _balance_events_storage[operation.user_id] = []

        _balance_events_storage[operation.user_id].append(operation)
        _balance_events_storage[operation.user_id].sort(key=lambda x: x.t)

    async def get_last_operations_by_time(
        self, user_id: int, min_t: int, op_type: None | Literal["deposit", "withdraw"] = None
    ) -> list[BalanceOperationEvent]:
        """
        Retrieve the last operations of a specific type performed by a user after a given time.

        This asynchronous function fetches a list of balance operations carried out by the provided
        user after the specified minimum Unix timestamp. If an operation type is supplied, only
        operations of that type are included. The function accesses a storage structure to retrieve
        the filtered balance operations.

        Parameters:
            user_id: int
                Unique identifier of the user whose operations are to be retrieved.
            min_t: int
                Minimum Unix timestamp. Only operations performed after this time will be included.
            op_type: None | Literal["deposit", "withdraw"], optional
                Type of operations to be retrieved. If None, operations of all types are included.

        Returns:
            list[BalanceOperation]
                A list of BalanceOperation objects filtered by the specified criteria.
        """
        if op_type:
            operations = [x for x in _balance_events_storage.get(user_id, []) if (x.type == op_type and x.t >= min_t)]
        else:
            operations = [x for x in _balance_events_storage.get(user_id, []) if x.t >= min_t]
        return operations

    async def get_last_n_operations(
        self, user_id: int, num_operations: int, op_type: None | Literal["deposit", "withdraw"] = None
    ) -> list[BalanceOperationEvent]:
        """
        Retrieve the last 'n' balance operations for a specific user, optionally filtered by operation type.

        This method fetches a list of the most recent balance operations for a specified user, with an
        optional parameter to filter operations by their type. The filter allows either "deposit" or
        "withdraw" as valid types. If no filter is provided, all types of operations are considered. The
        resulting list is capped to the 'n' most recent operations as specified.

        Parameters:
            user_id (int): The ID of the user whose balance operations are queried.
            num_operations (int): The number of most recent operations to be retrieved.
            op_type (None or Literal["deposit", "withdraw"]): The type of operation to filter by. Defaults
                to None, which implies no filtering.

        Returns:
            list[BalanceOperationEvent]: A list of the most recent balance operations matching the criteria.
        """
        if op_type:
            operations = [x for x in _balance_events_storage.get(user_id, []) if x.type == op_type]
        else:
            operations = [*_balance_events_storage.get(user_id, [])]

        return operations[-num_operations:]
