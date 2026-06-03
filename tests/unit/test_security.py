from datetime import timedelta
from uuid import uuid4

from app.core.security import create_access_token, decode_access_token


def test_create_and_decode_access_token() -> None:
    user_id = uuid4()
    token = create_access_token(user_id)

    assert isinstance(token, str)
    assert len(token) > 0

    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == str(user_id)


def test_decode_invalid_token() -> None:
    payload = decode_access_token("invalid.token.here")
    assert payload is None


def test_decode_expired_token() -> None:
    user_id = uuid4()
    # Create a token that expired 5 minutes ago
    token = create_access_token(user_id, expires_delta=timedelta(minutes=-5))

    payload = decode_access_token(token)
    assert payload is None
