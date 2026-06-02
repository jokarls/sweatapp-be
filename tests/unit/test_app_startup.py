from app.main import app


def test_app_imports_and_instantiates() -> None:
    """
    Test that the FastAPI application can be imported and instantiated without errors.
    """
    assert app is not None
    assert app.title == "SweatCheck API"
