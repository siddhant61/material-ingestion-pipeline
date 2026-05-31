import pytest
from fastapi import HTTPException, status
from src.api.dependencies import authenticate_user

# Mock the Depends function for testing
class MockRequest:
    def __init__(self, headers: dict):
        self._headers = headers

    @property
    def headers(self):
        return self._headers

@pytest.mark.asyncio
async def test_authenticate_user_valid_token():
    mock_request = MockRequest(headers={"Authorization": "Bearer valid-token"})
    user = await authenticate_user(authorization=mock_request.headers.get("Authorization"))
    assert user == "authenticated_user"

@pytest.mark.asyncio
async def test_authenticate_user_no_token():
    mock_request = MockRequest(headers={})
    with pytest.raises(HTTPException) as exc_info:
        await authenticate_user(authorization=mock_request.headers.get("Authorization"))
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Not authenticated"
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}

@pytest.mark.asyncio
async def test_authenticate_user_invalid_scheme():
    mock_request = MockRequest(headers={"Authorization": "Basic some-token"})
    with pytest.raises(HTTPException) as exc_info:
        await authenticate_user(authorization=mock_request.headers.get("Authorization"))
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Not authenticated"

@pytest.mark.asyncio
async def test_authenticate_user_empty_bearer_token():
    mock_request = MockRequest(headers={"Authorization": "Bearer "})
    with pytest.raises(HTTPException) as exc_info:
        await authenticate_user(authorization=mock_request.headers.get("Authorization"))
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Not authenticated"

@pytest.mark.asyncio
async def test_authenticate_user_invalid_token_value():
    mock_request = MockRequest(headers={"Authorization": "Bearer wrong-token"})
    with pytest.raises(HTTPException) as exc_info:
        await authenticate_user(authorization=mock_request.headers.get("Authorization"))
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Not authenticated"

@pytest.mark.asyncio
async def test_authenticate_user_malformed_header():
    mock_request = MockRequest(headers={"Authorization": "malformed-token-without-bearer"})
    with pytest.raises(HTTPException) as exc_info:
        await authenticate_user(authorization=mock_request.headers.get("Authorization"))
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Not authenticated"
