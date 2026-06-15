# 🤝 Contributing to Windows Computer Use

Thank you for your interest in contributing to Windows Computer Use! This document provides guidelines and information for contributors.

## 📋 Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)
- [Community](#community)

## 🤟 Code of Conduct

This project follows a code of conduct to ensure a welcoming environment for all contributors. By participating, you agree to:

- Be respectful and inclusive
- Focus on constructive feedback
- Accept responsibility for mistakes
- Show empathy towards other community members

## 🚀 Getting Started

### Prerequisites
- Windows 10/11
- Python 3.10 or higher
- Git
- Basic knowledge of Windows UI automation concepts

### Quick Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/windows-computer-use-mcp.git
cd windows-computer-use-mcp

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/
```

## 🛠️ Development Setup

### Environment Setup
```bash
# Install all development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Install Tesseract OCR (for OCR features)
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

### Project Structure
```
windows-computer-use-mcp/
├── src/windows_computer_use_mcp/     # Main package
│   ├── tools/            # MCP tools
│   ├── api/              # REST API endpoints
│   ├── core/             # Core functionality
│   └── services/         # Background services
├── tests/                # Test suite
├── docs/                 # Documentation
├── dxt/                  # DXT packaging
└── examples/             # Usage examples
```

## 🔄 Development Workflow

### 1. Choose an Issue
- Check [GitHub Issues](https://github.com/yourusername/windows-computer-use-mcp/issues) for open tasks
- Look for issues labeled `good first issue` or `help wanted`
- Comment on the issue to indicate you're working on it

### 2. Create a Branch
```bash
# Create and switch to a new branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

### 3. Make Changes
- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass

### 4. Test Your Changes
```bash
# Run the full test suite
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=windows_computer_use_mcp

# Run specific test file
pytest tests/test_specific_feature.py
```

### 5. Commit Your Changes
```bash
# Stage your changes
git add .

# Commit with a descriptive message
git commit -m "feat: add new automation tool

- Add new tool for window management
- Include comprehensive error handling
- Add unit tests

Closes #123"
```

## 🧪 Testing

### Test Structure
- **Unit tests**: Test individual functions and classes
- **Integration tests**: Test tool registration and MCP protocol
- **End-to-end tests**: Test complete automation workflows

### Running Tests
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_face_recognition.py::test_add_face

# Run tests with coverage
pytest --cov=windows_computer_use_mcp --cov-report=html
```

### Writing Tests
```python
import pytest
from windows_computer_use_mcp.tools.window import get_window_title

def test_get_window_title():
    """Test getting window title."""
    # Arrange
    window_handle = 12345

    # Act
    title = get_window_title(window_handle)

    # Assert
    assert isinstance(title, str)
    assert len(title) > 0
```

## 📚 Documentation

### Documentation Types
- **README.md**: Project overview and quick start
- **API Documentation**: Tool and function documentation
- **Examples**: Usage examples and tutorials
- **Changelog**: Version history and changes

### Updating Documentation
```bash
# Update README.md for new features
# Update docstrings in code
# Add examples for new functionality
```

## 📤 Submitting Changes

### Pull Request Process
1. **Create a Pull Request**
   - Use a descriptive title
   - Reference related issues
   - Provide a clear description of changes

2. **Pull Request Template**
   - [ ] Tests pass
   - [ ] Documentation updated
   - [ ] Code follows style guidelines
   - [ ] Commit messages are clear

3. **Review Process**
   - Address review feedback
   - Make requested changes
   - Ensure CI passes

### Commit Message Guidelines
```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance

**Examples:**
```
feat: add OCR text extraction tool
fix: resolve window handle validation issue
docs: update installation instructions
```

## 🌐 Community

### Communication Channels
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General discussion and questions
- **Pull Requests**: Code contributions

### Getting Help
- Check existing issues and documentation first
- Create a new issue for bugs or feature requests
- Use clear, descriptive titles and provide context

## 🙏 Recognition

Contributors will be recognized in:
- GitHub repository contributors list
- CHANGELOG.md for significant contributions
- Release notes for major features

---

Thank you for contributing to Windows Computer Use! Your efforts help make Windows automation more accessible and powerful for everyone. 🚀
