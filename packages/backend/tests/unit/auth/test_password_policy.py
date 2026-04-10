import pytest

from researchlens.modules.auth.domain import PasswordPolicy
from researchlens.modules.auth.domain.user import normalize_email, normalize_username
from researchlens.shared.errors import ValidationError


@pytest.mark.parametrize(
    "password",
    [
        "Short1!",
        "a" * 129 + "A1!",
        "lowercase1!",
        "UPPERCASE1!",
        "NoDigits!",
        "NoSpecial1",
        "Has Space1!",
        "casey",
        "casey@example.com",
        "CaseyStrong1!",
        "Password123!",
    ],
)
def test_password_policy_rejects_invalid_passwords(password: str) -> None:
    policy = PasswordPolicy()

    with pytest.raises(ValidationError):
        policy.validate(password=password, username="casey", email="casey@example.com")


def test_password_policy_accepts_strong_password() -> None:
    PasswordPolicy().validate(
        password="CorrectHorse1!",
        username="casey",
        email="casey@example.com",
    )


def test_username_and_email_normalization() -> None:
    assert normalize_username(" Casey.User ") == "casey.user"
    assert normalize_email(" Casey@Example.COM ") == "casey@example.com"
