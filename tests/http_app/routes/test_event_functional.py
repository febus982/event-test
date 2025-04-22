import pytest
from fastapi.testclient import TestClient

from gateways.balance_event_repository import _balance_events_storage


@pytest.fixture
def client(testapp):
    return TestClient(testapp)


@pytest.mark.parametrize(
    ["payloads", "expected_alert_codes"],
    [
        pytest.param(
            [{"type": "withdraw", "amount": "101.00", "user_id": 1, "t": 10}], [1100], id="withdraw_over_hundred"
        ),
        pytest.param(
            [
                {"type": "withdraw", "amount": "10.00", "user_id": 1, "t": 10},
                {"type": "withdraw", "amount": "10.00", "user_id": 1, "t": 11},
            ],
            [],
            id="consecutive_withdraws_before_alert",
        ),
        pytest.param(
            [
                {"type": "withdraw", "amount": "10.00", "user_id": 1, "t": 10},
                {"type": "withdraw", "amount": "10.00", "user_id": 1, "t": 11},
                {"type": "withdraw", "amount": "10.00", "user_id": 1, "t": 12},
            ],
            [30],
            id="consecutive_withdraws",
        ),
        pytest.param(
            [
                {"type": "withdraw", "amount": "10.00", "user_id": 1, "t": 10},
                {"type": "withdraw", "amount": "10.00", "user_id": 2, "t": 11},
                {"type": "withdraw", "amount": "10.00", "user_id": 1, "t": 12},
            ],
            [],
            id="consecutive_withdraws_different_users",
        ),
        pytest.param(
            [
                {"type": "withdraw", "amount": "10.00", "user_id": 1, "t": 10},
                {"type": "withdraw", "amount": "10.00", "user_id": 1, "t": 11},
                {"type": "withdraw", "amount": "101.00", "user_id": 1, "t": 12},
            ],
            [30, 1100],
            id="consecutive_withdraws_and_over_hundred",
        ),
        pytest.param(
            [
                {"type": "withdraw", "amount": "10.00", "user_id": 1, "t": 10},
                {"type": "withdraw", "amount": "10.00", "user_id": 1, "t": 11},
                {"type": "deposit", "amount": "10.00", "user_id": 1, "t": 12},
                {"type": "withdraw", "amount": "10.00", "user_id": 1, "t": 13},
            ],
            [],
            id="consecutive_withdraws_interrupted_by_deposits",
        ),
        pytest.param(
            [
                {"type": "deposit", "amount": "10.00", "user_id": 1, "t": 10},
                {"type": "deposit", "amount": "11.00", "user_id": 1, "t": 11},
            ],
            [],
            id="a_few_consecutive_increasing_deposits",
        ),
        pytest.param(
            [
                {"type": "deposit", "amount": "10.00", "user_id": 1, "t": 10},
                {"type": "deposit", "amount": "11.00", "user_id": 1, "t": 11},
                {"type": "deposit", "amount": "12.00", "user_id": 1, "t": 12},
            ],
            [300],
            id="consecutive_increasing_deposits",
        ),
        pytest.param(
            [
                {"type": "deposit", "amount": "10.00", "user_id": 1, "t": 10},
                {"type": "deposit", "amount": "11.00", "user_id": 2, "t": 11},
                {"type": "deposit", "amount": "12.00", "user_id": 1, "t": 12},
            ],
            [],
            id="consecutive_increasing_deposits_different_users",
        ),
        pytest.param(
            [
                {"type": "deposit", "amount": "10.00", "user_id": 1, "t": 10},
                {"type": "deposit", "amount": "11.00", "user_id": 1, "t": 11},
                {"type": "withdraw", "amount": "10.00", "user_id": 1, "t": 12},
                {"type": "deposit", "amount": "12.00", "user_id": 1, "t": 13},
            ],
            [300],
            id="consecutive_increasing_deposits_interrupted_by_withdraw",
        ),
        pytest.param(
            [
                {"type": "deposit", "amount": "10.00", "user_id": 1, "t": 10},
                {"type": "deposit", "amount": "11.00", "user_id": 1, "t": 11},
                {"type": "withdraw", "amount": "10.00", "user_id": 1, "t": 12},
                {"type": "deposit", "amount": "212.00", "user_id": 1, "t": 13},
            ],
            [300, 123],
            id="consecutive_increasing_deposits_over_200_interrupted_by_withdraw_",
        ),
        pytest.param(
            [
                {"type": "deposit", "amount": "140.00", "user_id": 1, "t": 10},
                {"type": "deposit", "amount": "111.00", "user_id": 1, "t": 13},
            ],
            [123],
            id="total_deposits_over_200_less_than_30_seconds",
        ),
        pytest.param(
            [
                {"type": "deposit", "amount": "140.00", "user_id": 1, "t": 10},
                {"type": "deposit", "amount": "111.00", "user_id": 1, "t": 83},
            ],
            [],
            id="total_deposits_over_200_more_than_30_seconds",
        ),
    ],
)
async def test_scenarios(client, payloads: list[dict], expected_alert_codes: list[int]):
    _balance_events_storage.clear()

    # Act
    for payload in payloads:
        response = client.post("/event/", json=payload)

    # Assert
    assert response.status_code == 200
    assert set(response.json()["alert_codes"]) == set(expected_alert_codes)
    assert response.json()["alert"] == bool(expected_alert_codes)
