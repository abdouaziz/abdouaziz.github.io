from __future__ import annotations

import threading
from pathlib import Path
from typing import BinaryIO, List, Union

import httpx

from .exceptions import APIError, AuthenticationError
from .models import (
    AudioToText,
    CreditInfo,
    GetPost,
    Post,
    PostVocalized,
    Statistic,
    Token,
    TokenRefresh,
)

_BASE_URL = "https://ttsapi.lafricamobile.com"


class Lamia:
    """Client for the LAM TTS API.

    Authenticate with an API key::

        client = Lamia(api_key="ae_live_...")

    Or with username and password::

        client = Lamia(username="user@example.com", password="secret")
    """

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        *,
        api_key: str | None = None,
        base_url: str = _BASE_URL,
        timeout: float = 30.0,
    ) -> None:
        if api_key is None and (username is None or password is None):
            raise ValueError("Provide either api_key or both username and password.")
        self._username = username
        self._password = password
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._access_token: str | None = api_key
        self._refresh_token: str | None = None
        self._api_key = api_key
        self._lock = threading.Lock()
        self._http = httpx.Client(timeout=timeout)

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def login(self) -> Token:
        """Authenticate and store tokens. Called automatically on first request."""
        response = self._http.post(
            f"{self._base_url}/login",
            data={
                "username": self._username,
                "password": self._password,
                "grant_type": "password",
            },
        )
        if response.status_code != 200:
            raise AuthenticationError(f"Login failed ({response.status_code}): {response.text}")
        token = Token.model_validate(response.json())
        self._access_token = token.access_token
        self._refresh_token = token.refresh_token
        return token

    def refresh(self) -> TokenRefresh:
        """Exchange the refresh token for a new access token."""
        if not self._refresh_token:
            raise AuthenticationError("No refresh token available — call login() first.")
        response = self._http.post(
            f"{self._base_url}/refresh",
            json={"refresh_token": self._refresh_token},
        )
        if response.status_code != 200:
            raise AuthenticationError(f"Token refresh failed ({response.status_code}): {response.text}")
        refreshed = TokenRefresh.model_validate(response.json())
        self._access_token = refreshed.access_token
        return refreshed

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_authenticated(self) -> None:
        with self._lock:
            if self._access_token is None:
                self.login()  # only reached in username/password mode

    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._access_token}"}

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        self._ensure_authenticated()
        response = self._http.request(
            method,
            f"{self._base_url}{path}",
            headers=self._auth_headers(),
            **kwargs,
        )
        if response.status_code == 401:
            if self._api_key:
                raise AuthenticationError("Invalid or expired API key.")
            try:
                self.refresh()
            except AuthenticationError:
                self.login()
            response = self._http.request(
                method,
                f"{self._base_url}{path}",
                headers=self._auth_headers(),
                **kwargs,
            )
        if response.status_code >= 400:
            raise APIError(response.status_code, response.json())
        return response

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    def get_credits(self) -> CreditInfo:
        """Return the authenticated user's remaining credit balance (in minutes)."""
        resp = self._request("GET", "/users/me/credits")
        return CreditInfo.model_validate(resp.json())

    # ------------------------------------------------------------------
    # Text-to-Speech
    # ------------------------------------------------------------------

    def get_languages(self) -> List[str]:
        """Return the list of supported TTS languages."""
        resp = self._request("GET", "/tts/languages")
        return resp.json()

    def get_tts_requests(self) -> List[GetPost]:
        """Return all previous TTS requests for the authenticated user."""
        resp = self._request("GET", "/tts/")
        return [GetPost.model_validate(item) for item in resp.json()]

    def synthesize(
        self,
        text: str,
        to_lang: str,
        *,
        pitch: float = 0,
        speed: float = 1,
    ) -> PostVocalized:
        """Translate *text* and vocalize it in *to_lang*.

        Returns a :class:`PostVocalized` containing the audio file path.
        """
        resp = self._request(
            "POST",
            "/tts/",
            json={"text": text, "to_lang": to_lang, "pitch": pitch, "speed": speed},
        )
        return PostVocalized.model_validate(resp.json())

    def translate(self, text: str, to_lang: str) -> Post:
        """Translate *text* into *to_lang* without generating audio."""
        resp = self._request(
            "POST",
            "/tts/translate",
            json={"text": text, "to_lang": to_lang},
        )
        return Post.model_validate(resp.json())

    def vocalize(
        self,
        text: str,
        to_lang: str,
        *,
        pitch: float = 0,
        speed: float = 1,
    ) -> PostVocalized:
        """Synthesize *text* to speech in *to_lang* without translation."""
        resp = self._request(
            "POST",
            "/tts/vocalize",
            json={"text": text, "to_lang": to_lang, "pitch": pitch, "speed": speed},
        )
        return PostVocalized.model_validate(resp.json())

    # ------------------------------------------------------------------
    # TTS-to-Voice call
    # ------------------------------------------------------------------

    def push_tts(
        self,
        text: str,
        to_lang: str,
        contacts_list: List[str],
        *,
        pitch: float = 0,
        speed: float = 1,
    ) -> dict:
        """Generate a TTS audio clip and initiate a voice call to *contacts_list*.

        Requires admin privileges on the LAM platform.
        """
        resp = self._request(
            "POST",
            "/push_tts",
            json={
                "text": text,
                "to_lang": to_lang,
                "pitch": pitch,
                "speed": speed,
                "login": self._username,
                "password": self._password,
                "contacts_list": contacts_list,
            },
        )
        return resp.json()

    # ------------------------------------------------------------------
    # Speech-to-Text
    # ------------------------------------------------------------------

    def get_stt_requests(self) -> List[AudioToText]:
        """Return all previous STT requests for the authenticated user."""
        resp = self._request("GET", "/stt/")
        return [AudioToText.model_validate(item) for item in resp.json()]

    def transcribe(
        self,
        audio: Union[bytes, BinaryIO, Path, str],
        to_lang: str,
    ) -> AudioToText:
        """Transcribe an audio file to text in *to_lang*.

        *audio* may be raw bytes, a file-like object, or a path (str/Path).
        """
        if isinstance(audio, (str, Path)):
            audio = Path(audio).read_bytes()
        if isinstance(audio, bytes):
            files = {"audio": ("audio.wav", audio, "audio/wav")}
        else:
            files = {"audio": audio}

        self._ensure_authenticated()
        response = self._http.post(
            f"{self._base_url}/stt/",
            headers=self._auth_headers(),
            files=files,
            data={"to_lang": to_lang},
        )
        if response.status_code == 401:
            if self._api_key:
                raise AuthenticationError("Invalid or expired API key.")
            try:
                self.refresh()
            except AuthenticationError:
                self.login()
            response = self._http.post(
                f"{self._base_url}/stt/",
                headers=self._auth_headers(),
                files=files,
                data={"to_lang": to_lang},
            )
        if response.status_code >= 400:
            raise APIError(response.status_code, response.json())
        return AudioToText.model_validate(response.json())

    def get_stt_request(self, post_id: int) -> AudioToText:
        """Retrieve a single STT request by its ID."""
        resp = self._request("GET", f"/stt/{post_id}")
        return AudioToText.model_validate(resp.json())

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def get_statistics(self) -> List[Statistic]:
        """Return all historical usage statistics."""
        resp = self._request("GET", "/stats/")
        return [Statistic.model_validate(item) for item in resp.json()]

    def get_current_statistics(self) -> Statistic:
        """Return the current period's usage statistics."""
        resp = self._request("GET", "/stats/current")
        return Statistic.model_validate(resp.json())

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "Lamia":
        return self

    def __exit__(self, *_) -> None:
        self.close()
