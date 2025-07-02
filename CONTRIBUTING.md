# Contributing to PhysiCell Configuration Builder

Thank you for your interest in contributing to the PhysiCell Configuration Builder! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.7 or higher
- Basic knowledge of PhysiCell and XML
- Familiarity with Git and GitHub

### Development Setup

1. **Fork the repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/YOUR-USERNAME/physicell-config.git
   cd physicell-config
   ```

2. **Set up development environment**
   ```bash
   # Create virtual environment (recommended)
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install in development mode
   pip install -e .
   ```

3. **Run tests to ensure everything works**
   ```bash
   python physicell_config/test_config.py
   ```

## 🛠️ Development Workflow

### Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow existing code style and patterns
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**
   ```bash
   # Run the full test suite
   python physicell_config/test_config.py
   
   # Test specific functionality
   python -c "from physicell_config import PhysiCellConfig; print('Import successful')"
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add feature: descriptive commit message"
   ```

5. **Push and create pull request**
   ```bash
   git push origin feature/your-feature-name
   # Then create a Pull Request on GitHub
   ```

## 📝 Coding Standards

### Code Style

- **Follow PEP 8** for Python code style
- **Use type hints** where appropriate
- **Document functions** with clear docstrings
- **Keep functions focused** - single responsibility principle

### Example Good Code

```python
def add_substrate(self, name: str, diffusion_coefficient: float = 1000.0,
                 decay_rate: float = 0.1, initial_condition: float = 0.0,
                 units: str = "dimensionless") -> 'PhysiCellConfig':
    """
    Add a substrate to the microenvironment.
    
    Args:
        name: Substrate name
        diffusion_coefficient: Diffusion coefficient (micron^2/min)
        decay_rate: Decay rate (1/min)
        initial_condition: Initial concentration
        units: Concentration units
    
    Returns:
        Self for method chaining
    
    Raises:
        ValueError: If substrate name is empty or already exists
    """
    if not name:
        raise ValueError("Substrate name cannot be empty")
    
    if name in self.substrates:
        raise ValueError(f"Substrate '{name}' already exists")
    
    self.substrates[name] = {
        'diffusion_coefficient': float(diffusion_coefficient),
        'decay_rate': float(decay_rate),
        'initial_condition': float(initial_condition),
        'units': str(units)
    }
    return self
```

### Testing

- **Add tests** for all new functionality
- **Test edge cases** and error conditions
- **Ensure backward compatibility** when modifying existing features
- **Test with real PhysiCell configurations** when possible

## 🎯 Types of Contributions

### 🐛 Bug Fixes

- **Check existing issues** before creating new ones
- **Provide clear reproduction steps**
- **Include PhysiCell version and configuration details**
- **Test the fix thoroughly**

### ✨ New Features

Before implementing major features:

1. **Open an issue** to discuss the feature
2. **Get feedback** from maintainers and community
3. **Plan the implementation** - API design, testing strategy
4. **Consider backward compatibility**

### 📚 Documentation

- **Improve README examples**
- **Add API documentation**
- **Create tutorials** for complex features
- **Fix typos and clarify instructions**

### 🧪 Testing

- **Add test cases** for untested code
- **Improve test coverage**
- **Add integration tests** with PhysiCell examples
- **Performance testing** for large configurations

## 📋 Contribution Areas

### High Priority

- **More PhysiCell examples** - Reproduce published models
- **Additional cell cycle models** - Support more PhysiCell cycle types
- **ECM support** - Extracellular matrix configuration
- **Performance optimization** - For large configurations
- **Error handling improvements** - Better validation and error messages

### Medium Priority

- **Configuration templates** - Pre-built model templates
- **Parameter validation** - More sophisticated range checking
- **XML pretty-printing** - Better formatted output
- **Configuration comparison tools** - Diff between configs

### Nice to Have

- **GUI wrapper** - Simple interface for non-programmers
- **Jupyter notebook integration** - Interactive configuration
- **Configuration visualization** - Graphical representation
- **Migration tools** - Convert between PhysiCell versions

## 🚦 Pull Request Process

### Before Submitting

- [ ] Code follows project style guidelines
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Documentation updated (if applicable)
- [ ] No breaking changes (or clearly documented)

### Pull Request Checklist

- [ ] **Clear description** of changes and motivation
- [ ] **Link to related issues** (if applicable)
- [ ] **Test results** included or described
- [ ] **Screenshots/examples** for UI changes
- [ ] **Breaking changes** clearly documented

### Review Process

1. **Automated checks** must pass
2. **Code review** by maintainers
3. **Testing** with various PhysiCell configurations
4. **Approval** and merge by maintainers

## 🏷️ Issue Guidelines

### Bug Reports

```markdown
**Bug Description**
Clear description of the bug

**Reproduction Steps**
1. Step one
2. Step two
3. See error

**Expected Behavior**
What should happen

**Environment**
- Python version:
- PhysiCell version:
- Operating system:

**Code Example**
```python
# Minimal code to reproduce the issue
```

**Additional Context**
Any other relevant information
```

### Feature Requests

```markdown
**Feature Description**
Clear description of the proposed feature

**Use Case**
Why this feature would be useful

**Proposed API**
```python
# Example of how the feature might work
config.new_feature(param1="value", param2=123)
```

**Alternatives Considered**
Other ways to accomplish the same goal

**Additional Context**
Links to PhysiCell documentation, papers, etc.
```

## 🌟 Recognition

Contributors will be:

- **Listed in CONTRIBUTORS.md**
- **Credited in release notes** for significant contributions
- **Mentioned in documentation** for major features
- **Invited to co-author** papers using this tool (for substantial contributions)

## 📞 Getting Help

- **GitHub Discussions** - For questions and ideas
- **GitHub Issues** - For bugs and feature requests
- **Code review** - Maintainers will provide feedback on PRs

## 🙏 Thank You

Every contribution helps make this tool better for the PhysiCell community. Whether it's:

- 🐛 **Bug reports** - Help us find and fix issues
- 💡 **Feature ideas** - Help us understand user needs
- 📝 **Documentation** - Help others use the tool
- 🧪 **Testing** - Help ensure reliability
- 💻 **Code** - Help build new features

**All contributions are valued and appreciated!** 🎉

---

Ready to contribute? Check out our [good first issues](https://github.com/your-username/physicell-config/labels/good%20first%20issue) to get started!
