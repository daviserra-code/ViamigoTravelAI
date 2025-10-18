# Contributing to Viamigo Travel AI

Thank you for your interest in contributing to Viamigo Travel AI! This document provides guidelines for contributing to the project.

## Getting Started

1. **Read the documentation**:
   - [SETUP.md](SETUP.md) - Set up your development environment
   - [SETUP_CHECKLIST.md](SETUP_CHECKLIST.md) - Verify your setup
   - [Instructions.md](Instructions.md) - Understand the architecture

2. **Set up your development environment**:
   ```bash
   git clone https://github.com/daviserra-code/ViamigoTravelAI.git
   cd ViamigoTravelAI
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   npm install
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run the application**:
   ```bash
   python3 run.py
   ```

## Development Workflow

### Making Changes

1. **Create a new branch** for your feature or fix:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make your changes** following the code style of the project

3. **Test your changes** thoroughly:
   - Run the application and test manually
   - Check for console errors
   - Test with different inputs and edge cases

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Clear description of your changes"
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request** on GitHub

## Code Style Guidelines

### Python
- Follow PEP 8 style guide
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused on a single task

### JavaScript
- Use ES6+ syntax where appropriate
- Keep functions small and focused
- Add comments for complex logic
- Use consistent indentation (2 or 4 spaces)

### General
- Write clear commit messages
- Keep commits focused on a single change
- Update documentation when adding features
- Remove debug code before committing

## Project Structure

```
ViamigoTravelAI/
├── app/                    # Application modules
│   ├── routes/            # Route handlers
│   ├── services/          # Business logic
│   └── utils/             # Utility functions
├── static/                # Frontend assets
│   ├── css/              # Stylesheets
│   ├── js/               # JavaScript files
│   └── images/           # Images
├── *_routes.py           # Route blueprints
├── models.py             # Database models
├── flask_app.py         # Flask application setup
└── run.py               # Application entry point
```

## Adding Features

When adding new features:

1. **Plan your implementation**:
   - Consider the impact on existing code
   - Think about edge cases
   - Document your approach

2. **Update documentation**:
   - Update relevant .md files
   - Add code comments
   - Update SETUP.md if setup changes

3. **Add tests** (if applicable):
   - Create test files following existing patterns
   - Test both success and failure cases

4. **Consider performance**:
   - Avoid blocking operations
   - Use caching where appropriate
   - Minimize API calls

## Bug Reports

When reporting bugs, please include:

1. **Description**: Clear description of the issue
2. **Steps to reproduce**: Detailed steps to reproduce the bug
3. **Expected behavior**: What should happen
4. **Actual behavior**: What actually happens
5. **Environment**:
   - OS and version
   - Python version
   - Browser (if frontend issue)
6. **Logs**: Relevant console output or error messages
7. **Screenshots**: If applicable

## Feature Requests

When requesting features, please include:

1. **Use case**: Why is this feature needed?
2. **Proposed solution**: How should it work?
3. **Alternatives**: Other approaches you've considered
4. **Additional context**: Any other relevant information

## API Keys and Secrets

**⚠️ Important**: Never commit API keys or secrets to the repository!

- Use `.env` file for configuration (already in .gitignore)
- Use `.env.example` as a template without real values
- Document required API keys in SETUP.md

## Database Changes

When modifying database models:

1. Update `models.py`
2. Document the change
3. Consider migration strategy
4. Test with both PostgreSQL and SQLite (if applicable)

## Testing

### Manual Testing
- Test on different browsers (Chrome, Firefox, Safari)
- Test with different screen sizes
- Test with sample data
- Test error conditions

### Automated Testing
- Run existing test files: `python3 test_*.py`
- Add new tests for new features
- Ensure tests pass before submitting PR

## Pull Request Guidelines

### Before Submitting
- [ ] Code follows the style guidelines
- [ ] Self-review of your own code
- [ ] Comments added where needed
- [ ] Documentation updated
- [ ] No API keys or secrets committed
- [ ] Tested manually
- [ ] No breaking changes (or clearly documented)

### PR Description
Include in your PR:
- Clear title describing the change
- Description of what changed and why
- Related issue numbers (if any)
- Screenshots (for UI changes)
- Breaking changes (if any)

### Review Process
- Maintainers will review your PR
- Address feedback in new commits
- Once approved, maintainer will merge

## Questions?

If you have questions:
- Check [SETUP.md](SETUP.md) for setup issues
- Check [Instructions.md](Instructions.md) for architecture
- Open an issue for general questions
- Tag maintainers in your PR for specific questions

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards others

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to Viamigo Travel AI! 🇮🇹✈️
