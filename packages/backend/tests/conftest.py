from collections.abc import Generator

import pytest

from researchlens.shared.config import reset_settings_cache


@pytest.fixture(autouse=True)
def reset_settings() -> Generator[None, None, None]:
    reset_settings_cache()
    yield
    reset_settings_cache()
