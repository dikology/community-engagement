from app.core.oauth import create_oauth_flow


def test_create_oauth_flow():
    """Test creating OAuth flow with correct parameters."""
    telegram_user_id = "123456789"

    flow, state = create_oauth_flow(telegram_user_id)

    assert flow is not None
    assert state.startswith(telegram_user_id)
    assert ":" in state
    assert len(state.split(":")[1]) > 0  # Check that we have a random part


def test_create_oauth_flow_different_users():
    """Test that different users get different state values."""
    user1_id = "123456789"
    user2_id = "987654321"

    _, state1 = create_oauth_flow(user1_id)
    _, state2 = create_oauth_flow(user2_id)

    assert state1 != state2
    assert state1.startswith(user1_id)
    assert state2.startswith(user2_id)
