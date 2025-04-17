from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from src.domains.balance._service import BalanceService
from src.domains.balance.exceptions import OperationError
from src.domains.balance.models import BalanceOperation


@pytest.fixture
def mock_balance_repository():
    """Returns a mock balance repository for testing."""
    repository = AsyncMock()
    repository.save_operation = AsyncMock()
    repository.get_last_n_operations = AsyncMock()
    repository.get_last_operations_by_time = AsyncMock()
    return repository


@pytest.fixture
def balance_service(mock_balance_repository):
    """Returns a BalanceService with a mocked repository."""
    return BalanceService(mock_balance_repository)


async def test_deposit_success(balance_service, mock_balance_repository):
    # Arrange
    user_id = 1
    amount = Decimal("100.00")
    t = 1000
    mock_balance_repository.save_operation.return_value = None

    # Mock the _check_for_alerts method to avoid testing its implementation here
    with patch.object(balance_service, "_check_for_alerts", return_value=[]) as mock_check_alerts:
        # Act
        result = await balance_service.deposit(user_id, amount, t)

        # Assert
        mock_balance_repository.save_operation.assert_called_once()
        operation = mock_balance_repository.save_operation.call_args[0][0]
        assert isinstance(operation, BalanceOperation)
        assert operation.user_id == user_id
        assert operation.amount == amount
        assert operation.t == t
        assert operation.type == "deposit"

        mock_check_alerts.assert_called_once_with(operation)
        assert result == []


async def test_deposit_raises_operation_error(balance_service, mock_balance_repository):
    # Arrange
    user_id = 1
    amount = Decimal("100.00")
    t = 1000
    mock_balance_repository.save_operation.side_effect = Exception("Database error")

    # Act & Assert
    with pytest.raises(OperationError) as exc_info:
        await balance_service.deposit(user_id, amount, t)

    assert "The deposit operation failed" in str(exc_info.value)
    mock_balance_repository.save_operation.assert_called_once()


async def test_withdraw_success(balance_service, mock_balance_repository):
    # Arrange
    user_id = 1
    amount = Decimal("100.00")
    t = 1000
    mock_balance_repository.save_operation.return_value = None

    # Mock the _check_for_alerts method to avoid testing its implementation here
    with patch.object(balance_service, "_check_for_alerts", return_value=[30]) as mock_check_alerts:
        # Act
        result = await balance_service.withdraw(user_id, amount, t)

        # Assert
        mock_balance_repository.save_operation.assert_called_once()
        operation = mock_balance_repository.save_operation.call_args[0][0]
        assert isinstance(operation, BalanceOperation)
        assert operation.user_id == user_id
        assert operation.amount == amount
        assert operation.t == t
        assert operation.type == "withdraw"

        mock_check_alerts.assert_called_once_with(operation)
        assert result == [30]


async def test_withdraw_raises_operation_error(balance_service, mock_balance_repository):
    # Arrange
    user_id = 1
    amount = Decimal("100.00")
    t = 1000
    mock_balance_repository.save_operation.side_effect = Exception("Database error")

    # Act & Assert
    with pytest.raises(OperationError) as exc_info:
        await balance_service.withdraw(user_id, amount, t)

    assert "The withdraw operation failed" in str(exc_info.value)
    mock_balance_repository.save_operation.assert_called_once()


async def test_check_for_alerts(balance_service, mock_balance_repository):
    # Arrange
    operation = BalanceOperation(user_id=1, amount=Decimal("100.00"), t=1000, type="deposit")

    # Mock all check methods
    with (
        patch.object(balance_service, "_high_withdraw_check", return_value=True) as mock_high_withdraw,
        patch.object(balance_service, "_consecutive_withdraws_check", return_value=False) as mock_consecutive_withdraws,
        patch.object(
            balance_service, "_consecutive_growing_deposits_check", return_value=True
        ) as mock_growing_deposits,
        patch.object(balance_service, "_high_deposits_over_short_time_check", return_value=False) as mock_high_deposits,
    ):
        # Act
        result = await balance_service._check_for_alerts(operation)

        # Assert
        mock_high_withdraw.assert_called_once_with(operation.user_id)
        mock_consecutive_withdraws.assert_called_once_with(operation.user_id)
        mock_growing_deposits.assert_called_once_with(operation.user_id)
        mock_high_deposits.assert_called_once_with(operation.user_id, operation.t)

        # Check that only the alert codes from methods that returned True are in the result
        assert 1100 in result  # high_withdraw_check returned True
        assert 30 not in result  # consecutive_withdraws_check returned False
        assert 300 in result  # consecutive_growing_deposits_check returned True
        assert 123 not in result  # high_deposits_over_short_time_check returned False


async def test_high_withdraw_check_true(balance_service, mock_balance_repository):
    # Arrange
    user_id = 1
    mock_balance_repository.get_last_n_operations.return_value = [
        BalanceOperation(user_id=user_id, amount=Decimal("150.00"), t=1000, type="withdraw")
    ]

    # Act
    result = await balance_service._high_withdraw_check(user_id)

    # Assert
    assert result is True
    mock_balance_repository.get_last_n_operations.assert_called_once_with(user_id=user_id, num_operations=1)


async def test_high_withdraw_check_false_no_operations(balance_service, mock_balance_repository):
    # Arrange
    user_id = 1
    mock_balance_repository.get_last_n_operations.return_value = []

    # Act
    result = await balance_service._high_withdraw_check(user_id)

    # Assert
    assert result is False
    mock_balance_repository.get_last_n_operations.assert_called_once_with(user_id=user_id, num_operations=1)


async def test_high_withdraw_check_false_deposit(balance_service, mock_balance_repository):
    # Arrange
    user_id = 1
    mock_balance_repository.get_last_n_operations.return_value = [
        BalanceOperation(user_id=user_id, amount=Decimal("150.00"), t=1000, type="deposit")
    ]

    # Act
    result = await balance_service._high_withdraw_check(user_id)

    # Assert
    assert result is False
    mock_balance_repository.get_last_n_operations.assert_called_once_with(user_id=user_id, num_operations=1)


async def test_high_withdraw_check_false_low_amount(balance_service, mock_balance_repository):
    # Arrange
    user_id = 1
    mock_balance_repository.get_last_n_operations.return_value = [
        BalanceOperation(user_id=user_id, amount=Decimal("50.00"), t=1000, type="withdraw")
    ]

    # Act
    result = await balance_service._high_withdraw_check(user_id)

    # Assert
    assert result is False
    mock_balance_repository.get_last_n_operations.assert_called_once_with(user_id=user_id, num_operations=1)


async def test_consecutive_withdraws_check_true(balance_service, mock_balance_repository):
    # Arrange
    user_id = 1
    mock_balance_repository.get_last_n_operations.return_value = [
        BalanceOperation(user_id=user_id, amount=Decimal("50.00"), t=1000, type="withdraw"),
        BalanceOperation(user_id=user_id, amount=Decimal("60.00"), t=1001, type="withdraw"),
        BalanceOperation(user_id=user_id, amount=Decimal("70.00"), t=1002, type="withdraw"),
    ]

    # Act
    result = await balance_service._consecutive_withdraws_check(user_id)

    # Assert
    assert result is True
    mock_balance_repository.get_last_n_operations.assert_called_once_with(user_id=user_id, num_operations=3)


async def test_consecutive_withdraws_check_false_deposit(balance_service, mock_balance_repository):
    # Arrange
    user_id = 1
    mock_balance_repository.get_last_n_operations.return_value = [
        BalanceOperation(user_id=user_id, amount=Decimal("50.00"), t=1000, type="withdraw"),
        BalanceOperation(user_id=user_id, amount=Decimal("60.00"), t=1001, type="deposit"),
        BalanceOperation(user_id=user_id, amount=Decimal("70.00"), t=1002, type="withdraw"),
    ]

    # Act
    result = await balance_service._consecutive_withdraws_check(user_id)

    # Assert
    assert result is False
    mock_balance_repository.get_last_n_operations.assert_called_once_with(user_id=user_id, num_operations=3)


async def test_consecutive_withdraws_check_false_not_enough_operations(balance_service, mock_balance_repository):
    # Arrange
    user_id = 1
    mock_balance_repository.get_last_n_operations.return_value = [
        BalanceOperation(user_id=user_id, amount=Decimal("50.00"), t=1000, type="withdraw"),
        BalanceOperation(user_id=user_id, amount=Decimal("60.00"), t=1001, type="withdraw"),
    ]

    # Act
    result = await balance_service._consecutive_withdraws_check(user_id)

    # Assert
    assert result is False
    mock_balance_repository.get_last_n_operations.assert_called_once_with(user_id=user_id, num_operations=3)


async def test_consecutive_growing_deposits_check_true(balance_service, mock_balance_repository):
    # Arrange
    user_id = 1
    mock_balance_repository.get_last_n_operations.return_value = [
        BalanceOperation(user_id=user_id, amount=Decimal("50.00"), t=1000, type="deposit"),
        BalanceOperation(user_id=user_id, amount=Decimal("60.00"), t=1001, type="deposit"),
        BalanceOperation(user_id=user_id, amount=Decimal("70.00"), t=1002, type="deposit"),
    ]

    # Act
    result = await balance_service._consecutive_growing_deposits_check(user_id)

    # Assert
    assert result is True
    mock_balance_repository.get_last_n_operations.assert_called_once_with(
        user_id=user_id, num_operations=3, op_type="deposit"
    )


async def test_consecutive_growing_deposits_check_false_not_growing(balance_service, mock_balance_repository):
    # Arrange
    user_id = 1
    mock_balance_repository.get_last_n_operations.return_value = [
        BalanceOperation(user_id=user_id, amount=Decimal("50.00"), t=1000, type="deposit"),
        BalanceOperation(user_id=user_id, amount=Decimal("70.00"), t=1001, type="deposit"),
        BalanceOperation(user_id=user_id, amount=Decimal("60.00"), t=1002, type="deposit"),
    ]

    # Act
    result = await balance_service._consecutive_growing_deposits_check(user_id)

    # Assert
    assert result is False
    mock_balance_repository.get_last_n_operations.assert_called_once_with(
        user_id=user_id, num_operations=3, op_type="deposit"
    )


async def test_consecutive_growing_deposits_check_false_not_enough_operations(balance_service, mock_balance_repository):
    # Arrange
    user_id = 1
    mock_balance_repository.get_last_n_operations.return_value = [
        BalanceOperation(user_id=user_id, amount=Decimal("50.00"), t=1000, type="deposit"),
        BalanceOperation(user_id=user_id, amount=Decimal("60.00"), t=1001, type="deposit"),
    ]

    # Act
    result = await balance_service._consecutive_growing_deposits_check(user_id)

    # Assert
    assert result is False
    mock_balance_repository.get_last_n_operations.assert_called_once_with(
        user_id=user_id, num_operations=3, op_type="deposit"
    )


async def test_high_deposits_over_short_time_check_true(balance_service, mock_balance_repository):
    # Arrange
    user_id = 1
    last_t = 1000
    mock_balance_repository.get_last_operations_by_time.return_value = [
        BalanceOperation(user_id=user_id, amount=Decimal("100.00"), t=980, type="deposit"),
        BalanceOperation(user_id=user_id, amount=Decimal("110.00"), t=990, type="deposit"),
    ]

    # Act
    result = await balance_service._high_deposits_over_short_time_check(user_id, last_t)

    # Assert
    assert result is True
    mock_balance_repository.get_last_operations_by_time.assert_called_once_with(
        user_id=user_id, min_t=last_t - 30, op_type="deposit"
    )


async def test_high_deposits_over_short_time_check_false_below_threshold(balance_service, mock_balance_repository):
    # Arrange
    user_id = 1
    last_t = 1000
    mock_balance_repository.get_last_operations_by_time.return_value = [
        BalanceOperation(user_id=user_id, amount=Decimal("100.00"), t=980, type="deposit"),
        BalanceOperation(user_id=user_id, amount=Decimal("50.00"), t=990, type="deposit"),
    ]

    # Act
    result = await balance_service._high_deposits_over_short_time_check(user_id, last_t)

    # Assert
    assert result is False
    mock_balance_repository.get_last_operations_by_time.assert_called_once_with(
        user_id=user_id, min_t=last_t - 30, op_type="deposit"
    )


async def test_high_deposits_over_short_time_check_false_no_operations(balance_service, mock_balance_repository):
    # Arrange
    user_id = 1
    last_t = 1000
    mock_balance_repository.get_last_operations_by_time.return_value = []

    # Act
    result = await balance_service._high_deposits_over_short_time_check(user_id, last_t)

    # Assert
    assert result is False
    mock_balance_repository.get_last_operations_by_time.assert_called_once_with(
        user_id=user_id, min_t=last_t - 30, op_type="deposit"
    )
