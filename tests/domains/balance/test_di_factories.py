from unittest.mock import MagicMock, patch

from domains.balance import get_balance_repository, get_balance_service
from domains.balance._service import BalanceService
from domains.balance.interfaces import BalanceRepositoryInterface, BalanceServiceInterface
from gateways.balance_repository import BalanceRepository


@patch("gateways.balance_repository.BalanceRepository")
def test_get_balance_repository(mock_balance_repository):
    """Test that get_balance_repository returns the correct repository instance."""
    # Setup
    mock_instance = MagicMock(spec=BalanceRepositoryInterface)
    mock_balance_repository.return_value = mock_instance

    # Execute
    repo = get_balance_repository()

    # Assert
    assert repo is mock_instance
    mock_balance_repository.assert_called_once()


@patch("domains.balance._service.BalanceService")
def test_get_balance_service(mock_balance_service):
    """Test that get_balance_service returns a service with the correct repository."""
    # Setup
    mock_repo = MagicMock(spec=BalanceRepositoryInterface)
    mock_instance = MagicMock(spec=BalanceServiceInterface)
    mock_balance_service.return_value = mock_instance

    # Execute
    service = get_balance_service(mock_repo)

    # Assert
    assert service is mock_instance
    mock_balance_service.assert_called_once_with(balance_repository=mock_repo)


def test_integration_of_dependencies():
    """Test that the dependencies chain works correctly together."""
    # Execute
    repo = get_balance_repository()
    service = get_balance_service(repo)

    # Assert
    assert isinstance(repo, BalanceRepository)
    assert isinstance(service, BalanceService)

    # Check that the service has the repository correctly set
    if hasattr(service, "_balance_repository"):
        assert service._balance_repository is repo
