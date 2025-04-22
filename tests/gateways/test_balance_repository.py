from decimal import Decimal

import pytest

from domains.balance.models import BalanceOperationEvent
from src.gateways.balance_event_repository import BalanceEventRepository, _balance_events_storage


@pytest.fixture
def balance_repository():
    """Return a fresh instance of BalanceRepository for testing."""
    # Clear the storage before each test
    _balance_events_storage.clear()
    return BalanceEventRepository()


@pytest.fixture
def sample_operations():
    """Return a list of sample operations for testing."""
    return [
        BalanceOperationEvent(type="deposit", amount=Decimal("100.00"), user_id=1, t=1000),
        BalanceOperationEvent(type="withdraw", amount=Decimal("50.00"), user_id=1, t=1100),
        BalanceOperationEvent(type="deposit", amount=Decimal("25.00"), user_id=1, t=1200),
        BalanceOperationEvent(type="deposit", amount=Decimal("200.00"), user_id=2, t=1050),
    ]


async def test_save_operation(balance_repository):
    """Test that operations are saved correctly."""
    operation = BalanceOperationEvent(type="deposit", amount=Decimal("100.00"), user_id=1, t=1000)

    await balance_repository.save_operation(operation)

    assert len(_balance_events_storage) == 1
    assert _balance_events_storage[1][0] == operation


async def test_save_multiple_operations_sorts_by_time(balance_repository):
    """Test that operations are sorted by time after saving."""
    operation1 = BalanceOperationEvent(type="deposit", amount=Decimal("100.00"), user_id=1, t=1200)

    operation2 = BalanceOperationEvent(type="withdraw", amount=Decimal("50.00"), user_id=1, t=1100)

    await balance_repository.save_operation(operation1)
    await balance_repository.save_operation(operation2)

    assert len(_balance_events_storage[1]) == 2
    assert _balance_events_storage[1][0] == operation2  # operation2 has earlier timestamp
    assert _balance_events_storage[1][1] == operation1


async def test_get_last_n_operations_by_time(balance_repository, sample_operations):
    """Test retrieving operations after a specific time."""
    for operation in sample_operations:
        await balance_repository.save_operation(operation)

    # Get operations after timestamp 1100
    result = await balance_repository.get_last_operations_by_time(user_id=1, min_t=1100)

    assert len(result) == 2
    assert result[0].t == 1100
    assert result[1].t == 1200


async def test_get_last_n_operations_by_time_empty_result(balance_repository, sample_operations):
    """Test retrieving operations with no matching results."""
    for operation in sample_operations:
        await balance_repository.save_operation(operation)

    # Get operations after timestamp 1300 (none exist)
    result = await balance_repository.get_last_operations_by_time(user_id=1, min_t=1300)

    assert len(result) == 0


async def test_get_last_n_operations_by_time_nonexistent_user(balance_repository, sample_operations):
    """Test retrieving operations for a user that doesn't exist."""
    for operation in sample_operations:
        await balance_repository.save_operation(operation)

    # Get operations for user_id=3 (doesn't exist)
    result = await balance_repository.get_last_operations_by_time(user_id=3, min_t=1000)

    assert len(result) == 0


async def test_get_last_n_operations_by_time_filtered_by_deposit(balance_repository, sample_operations):
    """Test retrieving operations after a specific time, filtered by deposit type."""
    for operation in sample_operations:
        await balance_repository.save_operation(operation)

    # Get deposit operations after timestamp 1000
    result = await balance_repository.get_last_operations_by_time(user_id=1, min_t=1000, op_type="deposit")

    assert len(result) == 2
    assert all(op.type == "deposit" for op in result)
    assert result[0].t == 1000
    assert result[1].t == 1200


async def test_get_last_n_operations_by_time_filtered_by_withdraw(balance_repository, sample_operations):
    """Test retrieving operations after a specific time, filtered by withdraw type."""
    for operation in sample_operations:
        await balance_repository.save_operation(operation)

    # Get withdraw operations after timestamp 1000
    result = await balance_repository.get_last_operations_by_time(user_id=1, min_t=1000, op_type="withdraw")

    assert len(result) == 1
    assert result[0].type == "withdraw"
    assert result[0].t == 1100


async def test_get_last_n_operations_by_time_filtered_by_type_no_results(balance_repository, sample_operations):
    """Test retrieving operations after a specific time with type filter that returns no results."""
    for operation in sample_operations:
        await balance_repository.save_operation(operation)

    # Get withdraw operations after timestamp 1200 (none exist)
    result = await balance_repository.get_last_operations_by_time(user_id=1, min_t=1200, op_type="withdraw")

    assert len(result) == 0


async def test_get_last_n_operations_by_time_filtered_by_type_different_user(balance_repository, sample_operations):
    """Test retrieving operations for a different user with type filter."""
    for operation in sample_operations:
        await balance_repository.save_operation(operation)

    # Get deposit operations after timestamp 1000 for user_id=2
    result = await balance_repository.get_last_operations_by_time(user_id=2, min_t=1000, op_type="deposit")

    assert len(result) == 1
    assert result[0].type == "deposit"
    assert result[0].user_id == 2
    assert result[0].t == 1050


async def test_get_last_n_operations_by_time_boundary_condition(balance_repository, sample_operations):
    """Test retrieving operations with timestamp exactly matching the min_t parameter."""
    for operation in sample_operations:
        await balance_repository.save_operation(operation)

    # Get operations with timestamp exactly 1100
    result = await balance_repository.get_last_operations_by_time(user_id=1, min_t=1100, op_type="withdraw")

    assert len(result) == 1
    assert result[0].t == 1100
    assert result[0].type == "withdraw"


async def test_get_last_n_operations_by_time_combined_filters(balance_repository):
    """Test retrieving operations with both time and type filters on multiple operations."""
    # Create operations with varied timestamps
    operations = [
        BalanceOperationEvent(type="deposit", amount=Decimal("10.00"), user_id=1, t=1000),
        BalanceOperationEvent(type="deposit", amount=Decimal("20.00"), user_id=1, t=1100),
        BalanceOperationEvent(type="withdraw", amount=Decimal("5.00"), user_id=1, t=1200),
        BalanceOperationEvent(type="deposit", amount=Decimal("30.00"), user_id=1, t=1300),
        BalanceOperationEvent(type="withdraw", amount=Decimal("15.00"), user_id=1, t=1400),
    ]

    for operation in operations:
        await balance_repository.save_operation(operation)

    # Get deposit operations after timestamp 1100
    result = await balance_repository.get_last_operations_by_time(user_id=1, min_t=1100, op_type="deposit")

    assert len(result) == 2
    assert all(op.type == "deposit" for op in result)
    assert all(op.t >= 1100 for op in result)
    assert result[0].t == 1100
    assert result[1].t == 1300


async def test_get_last_n_operations_all_types(balance_repository, sample_operations):
    """Test retrieving the last N operations regardless of type."""
    for operation in sample_operations:
        await balance_repository.save_operation(operation)

    # Get last 2 operations for user_id=1
    result = await balance_repository.get_last_n_operations(user_id=1, num_operations=2)

    assert len(result) == 2
    assert result[0].t == 1100
    assert result[1].t == 1200


async def test_get_last_n_operations_filtered_by_type(balance_repository, sample_operations):
    """Test retrieving the last N operations of a specific type."""
    for operation in sample_operations:
        await balance_repository.save_operation(operation)

    # Get last 2 deposit operations for user_id=1
    result = await balance_repository.get_last_n_operations(user_id=1, num_operations=2, op_type="deposit")

    assert len(result) == 2
    assert all(op.type == "deposit" for op in result)
    assert result[0].t == 1000
    assert result[1].t == 1200


async def test_get_last_n_operations_fewer_than_requested(balance_repository, sample_operations):
    """Test requesting more operations than exist."""
    for operation in sample_operations:
        await balance_repository.save_operation(operation)

    # Request 5 operations when only 3 exist
    result = await balance_repository.get_last_n_operations(user_id=1, num_operations=5)

    assert len(result) == 3


async def test_get_last_n_operations_nonexistent_user(balance_repository, sample_operations):
    """Test retrieving operations for a user that doesn't exist."""
    for operation in sample_operations:
        await balance_repository.save_operation(operation)

    # Get operations for user_id=3 (doesn't exist)
    result = await balance_repository.get_last_n_operations(user_id=3, num_operations=2)

    assert len(result) == 0
