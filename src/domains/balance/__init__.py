from typing import Annotated

from fastapi import Depends

from .interfaces import BalanceEventRepositoryInterface, BalanceEventServiceInterface


def get_balance_repository() -> BalanceEventRepositoryInterface:
    """
    Provides a function for initialising and retrieving the repository to manage balance events.

    This module contains the `get_balance_repository` function responsible for
    returning an instance of a BalanceEventRepositoryInterface. The current implementation
    directly imports and utilises the BalanceEventRepository class, which could be
    refactored to adhere more strictly to Clean Architecture principles in the
    future.

    Raises:
        ImportError: If the BalanceEventRepository module or class cannot be imported.

    Returns:
        BalanceEventRepositoryInterface: An instance of the repository interface to handle
        balance events.
    """
    from gateways.balance_event_repository import BalanceEventRepository

    return BalanceEventRepository()


def get_balance_service(
    balance_repository: Annotated[BalanceEventRepositoryInterface, Depends(get_balance_repository)],
) -> BalanceEventServiceInterface:
    """
    Retrieves an instance of the BalanceServiceInterface.

    This function creates and returns an instance of BalanceService, using the
    BalanceRepository as its dependency. It ensures that the balance service
    has a repository instance to interact with for its operations.

    Returns:
        BalanceEventServiceInterface: An instance of the BalanceServiceInterface
        implemented by BalanceService.
    """
    from ._service import BalanceEventService

    return BalanceEventService(balance_repository=balance_repository)
