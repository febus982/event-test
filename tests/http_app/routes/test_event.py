from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.domains.balance import BalanceEventServiceInterface
from src.http_app.routes.event import get_balance_service


# Setup test client and mock dependencies
@pytest.fixture
def mock_balance_service():
    service = MagicMock(spec=BalanceEventServiceInterface)
    # Make deposit and withdraw async methods
    service.deposit = AsyncMock()
    service.withdraw = AsyncMock()
    return service


@pytest.fixture
def client(mock_balance_service, testapp):
    # Override dependency
    def override_get_balance_service():
        return mock_balance_service

    testapp.dependency_overrides = {get_balance_service: override_get_balance_service}
    yield TestClient(testapp)
    testapp.dependency_overrides = {}


# Test cases


async def test_deposit_event_success(client, mock_balance_service):
    # Arrange
    mock_balance_service.ingest_event.return_value = [30, 123]
    payload = {"type": "deposit", "amount": "100.00", "user_id": 1, "t": 10}

    # Act
    response = client.post("/event/", json=payload)

    # Assert
    mock_balance_service.ingest_event.assert_called_once_with("deposit", 1, Decimal("100.00"), 10)
    assert response.status_code == 200
    assert response.json() == {"alert": True, "alert_codes": [30, 123], "user_id": 1}


async def test_withdraw_event_success(client, mock_balance_service):
    # Arrange
    mock_balance_service.ingest_event.return_value = []
    payload = {"type": "withdraw", "amount": "50.00", "user_id": 1, "t": 15}

    # Act
    response = client.post("/event/", json=payload)

    # Assert
    assert response.status_code == 200
    assert response.json() == {"alert": False, "alert_codes": [], "user_id": 1}
    mock_balance_service.ingest_event.assert_called_once_with("withdraw", 1, Decimal("50.00"), 15)


@pytest.mark.parametrize(
    "invalid_payload",
    [
        # Invalid type
        {"type": "invalid_type", "amount": "100.00", "user_id": 1, "t": 10},
        # Invalid amount format (number instead of string)
        {"type": "deposit", "amount": 100.00, "user_id": 1, "t": 10},
        # Negative amount
        {"type": "deposit", "amount": "-100.00", "user_id": 1, "t": 10},
        # Invalid user_id
        {"type": "deposit", "amount": "100.00", "user_id": -1, "t": 10},
        # Invalid timestamp
        {"type": "deposit", "amount": "100.00", "user_id": 1, "t": -10},
    ],
)
def test_invalid_request_validation(client, mock_balance_service, invalid_payload):
    # Act
    response = client.post("/event/", json=invalid_payload)

    # Assert
    assert response.status_code == 422
    mock_balance_service.deposit.assert_not_called()
    mock_balance_service.withdraw.assert_not_called()


def test_missing_fields(client, mock_balance_service):
    # Arrange
    payload = {
        "type": "deposit",
        "amount": "100.00",
        # Missing user_id and t
    }

    # Act
    response = client.post("/event/", json=payload)

    # Assert
    assert response.status_code == 422
    mock_balance_service.deposit.assert_not_called()
