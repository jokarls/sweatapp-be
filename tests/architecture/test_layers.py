from pathlib import Path


def test_domain_layer_isolation():
    """
    Ensure the domain layer does not import from api or infrastructure.
    """
    domain_path = Path(__file__).parent.parent.parent / "app" / "domain"
    for file in domain_path.glob("*.py"):
        content = file.read_text()
        assert "app.api" not in content, f"Domain file {file.name} imports from api"
        assert (
            "app.infrastructure" not in content
        ), f"Domain file {file.name} imports from infrastructure"


def test_api_layer_isolation():
    """
    Ensure the api layer does not import from infrastructure.
    It should only depend on domain.
    """
    api_path = Path(__file__).parent.parent.parent / "app" / "api"
    for file in api_path.glob("**/*.py"):
        content = file.read_text()
        assert (
            "app.infrastructure" not in content
        ), f"API file {file.name} imports from infrastructure"


def test_infrastructure_layer_dependency():
    """
    Infrastructure should depend on domain but not api.
    """
    infra_path = Path(__file__).parent.parent.parent / "app" / "infrastructure"
    for file in infra_path.glob("**/*.py"):
        content = file.read_text()
        assert "app.api" not in content, f"Infrastructure file {file.name} imports from api"
