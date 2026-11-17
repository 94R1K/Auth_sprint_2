from core.exceptions import InvalidCredentialsError
from core.services import OAuthProviderABC
from schemas import OAuthUserCreate

from services.token import YandexTokenService


class YandexOAuthProvider(OAuthProviderABC):
    name = "yandex"
    def __init__(self, client_id: str, secret: str, code_url: str, token_url: str, user_info_url: str):
        self._client_id = client_id
        self._secret = secret
        self._code_url = code_url
        self._token_url = token_url
        self._user_info_url = user_info_url
        self._oauth_token_service = YandexTokenService()

    async def get_user_info(self, code) -> OAuthUserCreate:
        tokens = await self._oauth_token_service.get_tokens(code)
        if tokens.get("error"):
            raise InvalidCredentialsError(tokens.get("error_description"))

        if not tokens.get("access_token"):
            raise InvalidCredentialsError("empty token")

        return await self._oauth_token_service.get_user_info(tokens.get("access_token"))

    def get_login_url(self, state: str) -> str:
        return f"{self._code_url}?response_type=code&client_id={self._client_id}&state={state}"
