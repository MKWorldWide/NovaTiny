# Contributing to NovaTiny

We're thrilled you're interested in contributing to NovaTiny! This guide will help you get started with contributing to our project.

## 🌟 First Time Contributors

If you're new to open source or contributing to NovaTiny, we recommend starting with issues labeled `good first issue` or `help wanted`. These are typically smaller, well-defined tasks that are great for getting familiar with the codebase.

## 🛠 Development Setup

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
   ```bash
   git clone https://github.com/your-username/novatiny.git
   cd novatiny
   ```
3. **Set up the development environment**
   ```bash
   # Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install development dependencies
   pip install -r requirements-dev.txt
   
   # Install pre-commit hooks
   pre-commit install
   ```
4. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 🔧 Development Workflow

1. **Code Style**
   - Python: Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
   - JavaScript: Follow [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
   - Use type hints for all Python code
   - Document all public functions and classes with docstrings

2. **Testing**
   - Write tests for new features and bug fixes
   - Ensure all tests pass before submitting a PR
   - Run the test suite:
     ```bash
     pytest
     ```

3. **Linting and Formatting**
   - Run the following before committing:
     ```bash
     black .
     isort .
     flake8
     mypy .
     ```

## 📝 Submitting Changes

1. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   ```
   
   Use [conventional commit messages](https://www.conventionalcommits.org/):
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation changes
   - `style:` for formatting changes
   - `refactor:` for code changes that neither fix bugs nor add features
   - `test:` for adding or modifying tests
   - `chore:` for maintenance tasks

2. **Push your changes**
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Open a Pull Request**
   - Go to the [NovaTiny repository](https://github.com/your-username/novatiny)
   - Click "New Pull Request"
   - Fill in the PR template with details about your changes
   - Reference any related issues
   - Request reviews from maintainers

## 🐛 Reporting Bugs

Found a bug? Please open an issue with:
- A clear, descriptive title
- Steps to reproduce the issue
- Expected vs. actual behavior
- Environment details (OS, Python/Node.js versions, etc.)
- Any relevant error messages or logs

## 💡 Feature Requests

Have an idea for a new feature? Open an issue with:
- A clear description of the feature
- The problem it solves
- Any alternative solutions you've considered
- Additional context or examples

## 📜 Code of Conduct

Please note that this project is released with a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.

## 🙏 Thank You!

Your contributions make NovaTiny better for everyone. Thank you for your time and effort in improving this project!
