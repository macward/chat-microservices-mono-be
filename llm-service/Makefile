# Makefile for LLM Service

.PHONY: help install install-dev test test-unit test-integration test-cov test-real test-mock test-connection test-api lint format clean run run-dev

# Default target
help:
	@echo "LLM Service - Comandos disponibles:"
	@echo ""
	@echo "Instalación:"
	@echo "  install     - Instalar dependencias de producción"
	@echo "  install-dev - Instalar dependencias de desarrollo"
	@echo ""
	@echo "Testing:"
	@echo "  test        - Ejecutar todos los tests (mock)"
	@echo "  test-unit   - Ejecutar solo tests unitarios"
	@echo "  test-integration - Ejecutar tests de integración"
	@echo "  test-cov    - Ejecutar tests con reporte de cobertura"
	@echo "  test-real   - Ejecutar tests con LM Studio real"
	@echo "  test-mock   - Ejecutar solo tests con mocks"
	@echo "  test-connection - Verificar conexión con LM Studio"
	@echo "  test-api    - Probar API manualmente (requiere servicio corriendo)"
	@echo ""
	@echo "Calidad de código:"
	@echo "  lint        - Verificar estilo de código"
	@echo "  format      - Formatear código automáticamente"
	@echo ""
	@echo "Ejecución:"
	@echo "  run         - Ejecutar aplicación en modo producción"
	@echo "  run-dev     - Ejecutar aplicación en modo desarrollo"
	@echo ""
	@echo "Utilidades:"
	@echo "  clean       - Limpiar archivos temporales"

# Instalación
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

# Testing
test:
	SKIP_REAL_LLM_TESTS=true pytest

test-unit:
	SKIP_REAL_LLM_TESTS=true pytest tests/ -m "not integration and not slow and not real_llm"

test-integration:
	SKIP_REAL_LLM_TESTS=true pytest tests/ -m "integration and not real_llm"

test-cov:
	SKIP_REAL_LLM_TESTS=true pytest --cov=app --cov-report=term-missing --cov-report=html

test-real:
	@echo "🚀 Ejecutando tests con LM Studio real..."
	@echo "💡 Asegúrate de que LM Studio esté corriendo con un modelo cargado"
	SKIP_REAL_LLM_TESTS=false pytest tests/test_real_llm_connection.py -v

test-mock:
	SKIP_REAL_LLM_TESTS=true pytest tests/ -m "not real_llm" -v

test-connection:
	@echo "🔍 Verificando conexión con LM Studio..."
	python scripts/test_llm_connection.py

test-api:
	@echo "🌐 Probando API HTTP..."
	@echo "💡 Asegúrate de que el servicio esté corriendo: make run-dev"
	python scripts/test_api_manual.py

# Calidad de código
lint:
	flake8 app tests
	mypy app
	black --check app tests
	isort --check-only app tests

format:
	black app tests
	isort app tests

# Ejecución
run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

run-dev:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Utilidades
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf dist/
	rm -rf build/