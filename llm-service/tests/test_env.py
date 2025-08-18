"""
Configuración de entorno para tests.
Define qué tipo de tests ejecutar basado en variables de entorno.
"""
import os
import pytest

def pytest_configure(config):
    """Configurar pytest con marcadores personalizados."""
    config.addinivalue_line(
        "markers", "real_llm: tests que requieren conexión real con LM Studio"
    )
    config.addinivalue_line(
        "markers", "mock_llm: tests que usan mocks (no requieren LM Studio real)"
    )
    config.addinivalue_line(
        "markers", "performance: tests de rendimiento"
    )

def pytest_collection_modifyitems(config, items):
    """Modificar colección de tests basado en variables de entorno."""
    
    # Si SKIP_REAL_LLM_TESTS está configurado, saltar tests reales
    if os.getenv("SKIP_REAL_LLM_TESTS", "false").lower() == "true":
        skip_real_llm = pytest.mark.skip(reason="Tests de LLM real deshabilitados")
        for item in items:
            if "real_llm" in item.keywords:
                item.add_marker(skip_real_llm)
    
    # Si ONLY_REAL_LLM_TESTS está configurado, solo ejecutar tests reales
    if os.getenv("ONLY_REAL_LLM_TESTS", "false").lower() == "true":
        skip_mock_tests = pytest.mark.skip(reason="Solo ejecutando tests de LLM real")
        for item in items:
            if "real_llm" not in item.keywords:
                item.add_marker(skip_mock_tests)
    
    # Si SKIP_PERFORMANCE_TESTS está configurado, saltar tests de rendimiento
    if os.getenv("SKIP_PERFORMANCE_TESTS", "false").lower() == "true":
        skip_performance = pytest.mark.skip(reason="Tests de rendimiento deshabilitados")
        for item in items:
            if "performance" in item.keywords:
                item.add_marker(skip_performance)

# Fixture para detectar si LM Studio está disponible
@pytest.fixture(scope="session")
def lm_studio_available():
    """Verificar si LM Studio está disponible para tests."""
    import httpx
    from app.config import settings
    
    try:
        response = httpx.get(
            f"http://{settings.lm_studio_host}:{settings.lm_studio_port}/v1/models",
            timeout=5
        )
        return response.status_code == 200
    except Exception:
        return False

@pytest.fixture(scope="session")
def test_environment():
    """Información sobre el entorno de test actual."""
    return {
        "skip_real_llm": os.getenv("SKIP_REAL_LLM_TESTS", "false").lower() == "true",
        "only_real_llm": os.getenv("ONLY_REAL_LLM_TESTS", "false").lower() == "true",
        "skip_performance": os.getenv("SKIP_PERFORMANCE_TESTS", "false").lower() == "true",
        "test_timeout": int(os.getenv("TEST_TIMEOUT", "30")),
        "verbose": os.getenv("VERBOSE_TESTS", "false").lower() == "true"
    }