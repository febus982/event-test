from unittest.mock import MagicMock, patch

from domains.balance import get_balance_repository, get_balance_service
from domains.balance._service import BalanceEventService
from domains.balance.interfaces import BalanceEventRepositoryInterface, BalanceEventServiceInterface
from gateways.balance_event_repository import BalanceEventRepository


@patch("gateways.balance_event_repository.BalanceEventRepository")
def test_get_balance_repository(mock_balance_repository):
    """Test that get_balance_repository returns the correct repository instance."""
    # Setup
    mock_instance = MagicMock(spec=BalanceEventRepositoryInterface)
    mock_balance_repository.return_value = mock_instance

    # Execute
    repo = get_balance_repository()

    # Assert
    assert repo is mock_instance
    mock_balance_repository.assert_called_once()


@patch("domains.balance._service.BalanceEventService")
def test_get_balance_service(mock_balance_service):
    """Test that get_balance_service returns a service with the correct repository."""
    # Setup
    mock_repo = MagicMock(spec=BalanceEventRepositoryInterface)
    mock_instance = MagicMock(spec=BalanceEventServiceInterface)
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
    assert isinstance(repo, BalanceEventRepository)
    assert isinstance(service, BalanceEventService)

    # Check that the service has the repository correctly set
    if hasattr(service, "_balance_repository"):
        assert service._balance_repository is repo
