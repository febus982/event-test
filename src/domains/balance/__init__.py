from typing import Annotated

from fastapi import Depends

from .interfaces import BalanceRepositoryInterface, BalanceServiceInterface


def get_balance_repository() -> BalanceRepositoryInterface:
    from gateways.balance_repository import BalanceRepository

    # If we were following strictly the Clean Architecture principles we
    # should not have imported directly the BalanceRepository class here,
    # and we should not have used a dependency injection system that is
    # dependent on the HTTP framework. Something to improve when the
    # application grows.
    return BalanceRepository()


def get_balance_service(
    balance_repository: Annotated[BalanceRepositoryInterface, Depends(get_balance_repository)],
) -> BalanceServiceInterface:
    """
    Retrieves an instance of the BalanceServiceInterface.

    This function creates and returns an instance of BalanceService, using the
    BalanceRepository as its dependency. It ensures that the balance service
    has a repository instance to interact with for its operations.

    Returns:
        BalanceServiceInterface: An instance of the BalanceServiceInterface
        implemented by BalanceService.
    """
    from ._service import BalanceService

    return BalanceService(balance_repository=balance_repository)
