from asyncio import TaskGroup
from decimal import Decimal
from typing import Literal

from .exceptions import OperationError
from .interfaces import BalanceEventRepositoryInterface
from .models import BalanceOperationEvent


class BalanceEventService:
    def __init__(self, balance_repository: BalanceEventRepositoryInterface) -> None:
        self._balance_repository = balance_repository

    async def ingest_event(
        self, type_: Literal["deposit", "withdraw"], user_id: int, amount: Decimal, t: int
    ) -> list[int]:
        """
        Ingests a financial event of a specific type for a user.

        This coroutine processes a financial event such as a deposit or withdrawal. It records
        the event, updates user-specific data accordingly, and returns a list of or identifiers
        that correspond to alerts to be handled by the event submitter.

        Args:
            type_: A string literal specifying the type of event. Must be one of "deposit" or
                  "withdraw".
            user_id: An integer representing the ID of the user associated with the
                     financial event.
            amount: A Decimal value representing the amount of the transaction.
            t: An integer representing the timestamp associated with the financial event.

        Returns:
            A list of integers representing the IDs of the alerts produced by
            the processed event.
        """
        try:
            op = BalanceOperationEvent(user_id=user_id, amount=amount, t=t, type=type_)
            await self._balance_repository.save_operation(op)
            return await self._check_for_alerts(op)
        except Exception as e:
            raise OperationError("Failed event ingestion") from e

    async def _check_for_alerts(self, last_operation: BalanceOperationEvent) -> list[int]:
        """
        Checks for balance alerts for a specific user.

        This method evaluates balance conditions for a user and identifies alerts that
        match the conditions by invoking the associated functions. The process includes
        retrieving the user's balance information and applying pre-defined alert
        conditions to determine which alerts are triggered.

        Args:
            last_operation (BalanceOperationEvent): The last operation performed by the user.

        Returns:
            list[int]: A list of alert identifiers that are triggered based on the
            user's last operations.
        """

        # This is an improvement area. We should probably have a centralised error/alert
        # handling mechanism, supporting more than error codes (i.e. description, log behaviour, etc.).
        # Without more information on the wider use cases of the application this seem
        # to be a good place to start. We at least ensure the uniqueness of the error codes using a dictionary.
        # Another improvement would be making all the hardcoded values configurable
        # (number of checked operations, thresholds, etc.)

        async with TaskGroup() as tg:
            tasks = {
                1100: tg.create_task(self._high_withdraw_check(last_operation.user_id)),
                30: tg.create_task(self._consecutive_withdraws_check(last_operation.user_id)),
                300: tg.create_task(self._consecutive_growing_deposits_check(last_operation.user_id)),
                123: tg.create_task(
                    self._high_deposits_over_short_time_check(last_operation.user_id, last_operation.t)
                ),
            }

        return [k for k, v in tasks.items() if v.result() is True]

    async def _high_withdraw_check(self, user_id: int) -> bool:
        """
        Checks if the last operation for the given user is a high-value withdrawal.

        This asynchronous function retrieves the last operation for a given user
        and determines if it is a withdrawal operation with an amount greater
        than 100. If no operations exist for the user, it returns False.

        Args:
            user_id (int): The unique identifier of the user.

        Returns:
            bool: True if the last operation is a withdrawal with an amount
            greater than 100, False otherwise.
        """
        ops = await self._balance_repository.get_last_n_operations(user_id=user_id, num_operations=1)
        if not ops:
            return False
        else:
            return ops[0].type == "withdraw" and ops[0].amount > 100

    async def _consecutive_withdraws_check(self, user_id: int) -> bool:
        """
        Checks if the given user has made three consecutive withdrawal operations.

        The method retrieves the last three operations performed by the user and evaluates
        whether they all are of type 'withdrawal'. If there are fewer than three operations,
        it will indicate that the condition is not met.

        Args:
            user_id (int): The unique identifier of the user whose operations are to be checked.

        Returns:
            bool: True if the user has exactly three consecutive withdrawals, False otherwise.
        """
        ops = await self._balance_repository.get_last_n_operations(user_id=user_id, num_operations=3)
        if not len(ops) == 3:
            return False
        else:
            return not [x for x in ops if x.type == "deposit"]

    async def _consecutive_growing_deposits_check(self, user_id: int) -> bool:
        """
        Determine if a user has made three consecutive growing deposit operations.

        This asynchronous function checks if the last three deposit operations by the user
        show a consecutive increase in their amounts. If the user does not have at least
        three deposit operations, it will return False.

        Args:
            user_id (int): The unique identifier of the user whose deposit
                operations are to be checked.

        Returns:
            bool: True if the last three deposit operations display consecutive
                growth in their amounts, False otherwise.
        """
        ops = await self._balance_repository.get_last_n_operations(user_id=user_id, num_operations=3, op_type="deposit")
        if not len(ops) == 3:
            return False
        else:
            return ops[0].amount < ops[1].amount < ops[2].amount

    async def _high_deposits_over_short_time_check(self, user_id: int, last_t: int) -> bool:
        """
        Checks if a user has made high deposit amounts over a short period of time.

        This method verifies whether a user has made deposit operations within
        the last 30 seconds that collectively reach or exceed a specified
        threshold amount. The operations are queried from a balance repository.

        Args:
            user_id: The ID of the user to check the deposits for.
            last_t: The latest timestamp (in seconds) considered
                for the deposit operations check.

        Returns:
            A boolean indicating whether the total deposit amount meets or exceeds
            the threshold in the given timeframe.
        """
        ops = await self._balance_repository.get_last_operations_by_time(
            user_id=user_id, min_t=last_t - 30, op_type="deposit"
        )
        if not ops:
            return False
        else:
            return sum(x.amount for x in ops) >= 200
