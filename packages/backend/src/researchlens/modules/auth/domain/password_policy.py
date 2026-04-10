import re

from researchlens.modules.auth.domain.user import normalize_email, normalize_username
from researchlens.shared.errors import ValidationError

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
COMMON_WEAK_PASSWORDS = {
    "password",
    "password1",
    "password123",
    "password123!",
    "qwerty123",
    "letmein123",
    "admin123",
    "welcome1",
}


class PasswordPolicy:
    def validate(self, *, password: str, username: str, email: str) -> None:
        normalized_username = normalize_username(username)
        normalized_email = normalize_email(email)
        lowered_password = password.lower()

        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValidationError("Password must be at least 8 characters.")
        if len(password) > MAX_PASSWORD_LENGTH:
            raise ValidationError("Password must be 128 characters or fewer.")
        if any(character.isspace() for character in password):
            raise ValidationError("Password must not contain spaces.")
        if not re.search(r"[A-Z]", password):
            raise ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", password):
            raise ValidationError("Password must contain at least one lowercase letter.")
        if not re.search(r"\d", password):
            raise ValidationError("Password must contain at least one digit.")
        if not re.search(r"[^A-Za-z0-9\s]", password):
            raise ValidationError("Password must contain at least one special character.")
        if lowered_password == normalized_username:
            raise ValidationError("Password must not equal the username.")
        if lowered_password == normalized_email:
            raise ValidationError("Password must not equal the email.")
        if normalized_username in lowered_password:
            raise ValidationError("Password must not contain the username.")
        if lowered_password in COMMON_WEAK_PASSWORDS:
            raise ValidationError("Password is too common.")
