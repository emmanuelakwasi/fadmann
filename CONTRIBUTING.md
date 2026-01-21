# Contributing to FadMann

Thanks for your interest in contributing! This project is built by students, for students, and we welcome contributions of all kinds.

## How to Contribute

### Reporting Bugs

Found a bug? Please open an issue using the [bug report template](https://github.com/yourusername/fadmann/issues/new?template=bug_report.md). Include as much detail as possible:
- What happened
- What you expected to happen
- Steps to reproduce
- Your environment (OS, Python version, etc.)

### Suggesting Features

Have an idea for a new feature? Use the [feature request template](https://github.com/yourusername/fadmann/issues/new?template=feature_request.md). Tell us:
- What problem it would solve
- How you envision it working
- Any alternatives you've considered

### Code Contributions

1. **Fork the repository** and clone it locally
2. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```
3. **Set up your development environment**:
   - Create a virtual environment: `python -m venv venv`
   - Activate it: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (macOS/Linux)
   - Install dependencies: `pip install -r requirements.txt`
4. **Make your changes** and test them locally
5. **Commit your changes** with clear, descriptive messages:
   ```bash
   git commit -m "Add feature: description of what you did"
   ```
6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Open a Pull Request** on GitHub

## Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add comments for complex logic
- Keep functions focused and small
- Test your changes before submitting

### Optional: Pre-commit Hooks

We have a pre-commit configuration (`.pre-commit-config.yaml`) that automatically formats code. To use it:

```bash
pip install pre-commit
pre-commit install
```

This will run Black formatter and other checks before each commit. It's optional but recommended!

## Project Structure

- `backend/` - FastAPI backend code
- `frontend/` - Static HTML/CSS/JavaScript files
- `data/` - SQLite database (gitignored, auto-created)
- `scripts/` - Helper scripts

## Questions?

Feel free to open an issue with the "question" label if you're unsure about anything. We're all learning here!

Thanks for helping make FadMann better!
