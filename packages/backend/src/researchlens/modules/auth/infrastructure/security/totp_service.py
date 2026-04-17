from datetime import datetime

import pyotp


class PyotpTotpService:
    def __init__(
        self,
        *,
        issuer: str,
        period_seconds: int,
        digits: int,
    ) -> None:
        self._issuer = issuer
        self._period_seconds = period_seconds
        self._digits = digits

    def generate_secret(self) -> str:
        return pyotp.random_base32()

    def provisioning_uri(self, *, secret: str, account_name: str) -> str:
        return pyotp.TOTP(
            secret,
            interval=self._period_seconds,
            digits=self._digits,
        ).provisioning_uri(name=account_name, issuer_name=self._issuer)

    def verify_code(self, *, secret: str, code: str, verified_at: datetime) -> bool:
        return bool(
            pyotp.TOTP(
                secret,
                interval=self._period_seconds,
                digits=self._digits,
            ).verify(code, for_time=verified_at, valid_window=0)
        )
