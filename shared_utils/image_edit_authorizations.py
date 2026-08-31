import os
import secrets
import threading
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class ImageEditAuthorization:
    file_path: str
    owner: str
    model: str | None
    size: str | None
    quality: str | None
    output_format: str | None
    expires_at: float


class ImageEditAuthorizationStore:
    """Bind browser-safe edit tokens to server-validated image metadata."""

    def __init__(self, ttl_seconds=3600, max_entries=2048):
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._entries = {}
        self._lock = threading.Lock()

    def issue(
        self,
        *,
        owner,
        file_path,
        output_root,
        model=None,
        size=None,
        quality=None,
        output_format=None,
    ):
        """Issue a token after confirming the image belongs to the output root."""
        resolved_file = self._resolve_owned_file(file_path, output_root)
        token = secrets.token_urlsafe(32)
        authorization = ImageEditAuthorization(
            file_path=resolved_file,
            owner=str(owner),
            model=model,
            size=size,
            quality=quality,
            output_format=output_format,
            expires_at=time.monotonic() + self.ttl_seconds,
        )
        with self._lock:
            self._remove_expired_locked()
            if len(self._entries) >= self.max_entries:
                oldest_token = min(
                    self._entries,
                    key=lambda item: self._entries[item].expires_at,
                )
                self._entries.pop(oldest_token, None)
            self._entries[token] = authorization
        return token

    def resolve(self, token, *, owner, output_root):
        """Resolve a token only for its original owner and output directory."""
        if not isinstance(token, str) or not token:
            return None
        with self._lock:
            self._remove_expired_locked()
            authorization = self._entries.get(token)
        if authorization is None or authorization.owner != str(owner):
            return None
        try:
            resolved_file = self._resolve_owned_file(
                authorization.file_path,
                output_root,
            )
        except ValueError:
            return None
        if resolved_file != authorization.file_path:
            return None
        return authorization

    def _remove_expired_locked(self):
        now = time.monotonic()
        expired = [
            token
            for token, authorization in self._entries.items()
            if authorization.expires_at <= now
        ]
        for token in expired:
            self._entries.pop(token, None)

    @staticmethod
    def _resolve_owned_file(file_path, output_root):
        root = os.path.realpath(os.path.abspath(output_root))
        candidate = os.path.realpath(os.path.abspath(file_path))
        try:
            is_owned = os.path.commonpath([root, candidate]) == root
        except ValueError:
            is_owned = False
        if not is_owned or not os.path.isfile(candidate):
            raise ValueError("Image file is outside the authorized output directory")
        return candidate


image_edit_authorizations = ImageEditAuthorizationStore()
