import researchlens
import researchlens_api
import researchlens_worker


def test_installed_package_imports() -> None:
    assert researchlens.__doc__ == "ResearchLens installed backend package."
    assert researchlens_api.__doc__ == "ResearchLens API application package."
    assert researchlens_worker.__doc__ == "ResearchLens worker package."
