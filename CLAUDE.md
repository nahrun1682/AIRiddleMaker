# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python project optimized for modern Python development. The project uses industry-standard tools and follows best practices for scalable application development.

## Development Commands

### Environment Management
- `uv venv` - Create virtual environment (`.venv`)
- `source .venv/bin/activate` (Linux/Mac) or `.venv\Scripts\activate` (Windows) - Activate virtual environment
- `deactivate` - Deactivate virtual environment
- `uv sync` - Install dependencies from `pyproject.toml`/`uv.lock`
- `uv sync --extra dev` - Install development dependencies

### Package Management
- `uv add <package>` - Add a production dependency
- `uv add --dev <package>` - Add a development dependency
- `uv remove <package>` - Remove a dependency
- `uv lock` - Regenerate lockfile

### Testing Commands
- `uv run pytest` - Run all tests
- `uv run pytest -v` - Run tests with verbose output
- `uv run pytest --cov` - Run tests with coverage report
- `uv run pytest --cov-report=html` - Generate HTML coverage report
- `uv run pytest -x` - Stop on first failure
- `uv run pytest -k "test_name"` - Run specific test by name
- `uv run python -m unittest` - Run tests with unittest

### Code Quality Commands
- `uv run black .` - Format code with Black
- `uv run black --check .` - Check code formatting without changes
- `uv run isort .` - Sort imports
- `uv run isort --check-only .` - Check import sorting
- `uv run flake8` - Run linting with Flake8
- `uv run pylint src/` - Run linting with Pylint
- `uv run mypy src/` - Run type checking with MyPy

### Development Tools
- `uv lock --upgrade` - Upgrade dependencies and refresh lockfile
- `uv run python -c "import sys; print(sys.version)"` - Check Python version
- `uv run python -m site` - Show Python site information
- `uv run python -m pdb script.py` - Debug with pdb

## Technology Stack

### Core Technologies
- **Python** - Primary programming language (3.13+)
- **uv** - Package/dependency and virtual environment management

### Common Frameworks
- **Django** - High-level web framework
- **Flask** - Micro web framework
- **FastAPI** - Modern API framework with automatic documentation
- **SQLAlchemy** - SQL toolkit and ORM
- **Pydantic** - Data validation using Python type hints

### Data Science & ML
- **NumPy** - Numerical computing
- **Pandas** - Data manipulation and analysis
- **Matplotlib/Seaborn** - Data visualization
- **Scikit-learn** - Machine learning library
- **TensorFlow/PyTorch** - Deep learning frameworks

### Testing Frameworks
- **pytest** - Testing framework
- **unittest** - Built-in testing framework
- **pytest-cov** - Coverage plugin for pytest
- **factory-boy** - Test fixtures
- **responses** - Mock HTTP requests

### Code Quality Tools
- **Black** - Code formatter
- **isort** - Import sorter
- **flake8** - Style guide enforcement
- **pylint** - Code analysis
- **mypy** - Static type checker
- **pre-commit** - Git hooks framework

## Project Structure Guidelines

### File Organization
```
src/
├── package_name/
│   ├── __init__.py
│   ├── main.py          # Application entry point
│   ├── models/          # Data models
│   ├── views/           # Web views (Django/Flask)
│   ├── api/             # API endpoints
│   ├── services/        # Business logic
│   ├── utils/           # Utility functions
│   └── config/          # Configuration files
tests/
├── __init__.py
├── conftest.py          # pytest configuration
├── test_models.py
├── test_views.py
└── test_utils.py
pyproject.toml          # Project metadata and dependencies
uv.lock                 # Resolved dependency lockfile
```

### Naming Conventions
- **Files/Modules**: Use snake_case (`user_profile.py`)
- **Classes**: Use PascalCase (`UserProfile`)
- **Functions/Variables**: Use snake_case (`get_user_data`)
- **Constants**: Use UPPER_SNAKE_CASE (`API_BASE_URL`)
- **Private methods**: Prefix with underscore (`_private_method`)

## Python Guidelines

### Type Hints
- Use type hints for function parameters and return values
- Import types from `typing` module when needed
- Use `Optional` for nullable values
- Use `Union` for multiple possible types
- Document complex types with comments

### Code Style
- Follow PEP 8 style guide
- Use meaningful variable and function names
- Keep functions focused and single-purpose
- Use docstrings for modules, classes, and functions
- Limit line length to 88 characters (Black default)

### Best Practices
- Use list comprehensions for simple transformations
- Prefer `pathlib` over `os.path` for file operations
- Use context managers (`with` statements) for resource management
- Handle exceptions appropriately with try/except blocks
- Use `logging` module instead of print statements

## Testing Standards

### Test Structure
- Organize tests to mirror source code structure
- Use descriptive test names that explain the behavior
- Follow AAA pattern (Arrange, Act, Assert)
- Use fixtures for common test data
- Group related tests in classes

### Coverage Goals
- Aim for 90%+ test coverage
- Write unit tests for business logic
- Use integration tests for external dependencies
- Mock external services in tests
- Test error conditions and edge cases

### pytest Configuration
```python
# pytest.ini or pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "--cov=src --cov-report=term-missing"
```

## UV Environment Setup

### Creation and Activation
```bash
# Create virtual environment
uv venv

# Activate (Linux/Mac)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
uv sync
uv sync --extra dev
```

### Requirements Management
- Use `pyproject.toml` as the source of truth for dependencies
- Use `uv.lock` for reproducible builds
- Add dependencies with `uv add` / `uv add --dev`
- Refresh lockfile with `uv lock`

## Django-Specific Guidelines

### Project Structure
```
project_name/
├── manage.py
├── project_name/
│   ├── __init__.py
│   ├── settings/
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── users/
│   ├── products/
│   └── orders/
├── pyproject.toml
└── uv.lock
```

### Common Commands
- `uv run python manage.py runserver` - Start development server
- `uv run python manage.py migrate` - Apply database migrations
- `uv run python manage.py makemigrations` - Create new migrations
- `uv run python manage.py createsuperuser` - Create admin user
- `uv run python manage.py collectstatic` - Collect static files
- `uv run python manage.py test` - Run Django tests

## FastAPI-Specific Guidelines

### Project Structure
```
src/
├── main.py              # FastAPI application
├── api/
│   ├── __init__.py
│   ├── dependencies.py  # Dependency injection
│   └── v1/
│       ├── __init__.py
│       └── endpoints/
├── core/
│   ├── __init__.py
│   ├── config.py       # Settings
│   └── security.py    # Authentication
├── models/
├── schemas/            # Pydantic models
└── services/
```

### Common Commands
- `uv run uvicorn main:app --reload` - Start development server
- `uv run uvicorn main:app --host 0.0.0.0 --port 8000` - Start production server

## Security Guidelines

### Dependencies
- Regularly update dependencies with `uv lock --upgrade`
- Use `uvx pip-audit` to check for known vulnerabilities
- Pin dependency versions in `uv.lock`
- Use virtual environments to isolate dependencies

### Code Security
- Validate input data with Pydantic or similar
- Use environment variables for sensitive configuration
- Implement proper authentication and authorization
- Sanitize data before database operations
- Use HTTPS for production deployments

## Development Workflow

### Before Starting
1. Check Python version compatibility
2. Create and activate virtual environment
3. Install dependencies from `pyproject.toml` with `uv sync`
4. Run type checking with `uv run mypy`

### During Development
1. Use type hints for better code documentation
2. Run tests frequently to catch issues early
3. Use meaningful commit messages
4. Format code with Black before committing

### Before Committing
1. Run full test suite: `uv run pytest`
2. Check code formatting: `uv run black --check .`
3. Sort imports: `uv run isort --check-only .`
4. Run linting: `uv run flake8`
5. Run type checking: `uv run mypy src/`
