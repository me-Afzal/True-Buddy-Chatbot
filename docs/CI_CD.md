# ⚙️ CI/CD Pipeline Documentation

This document explains the **Continuous Integration (CI)** pipeline for **True-Buddy Chatbot**.

---

## 🚀 Workflow Overview

The CI/CD workflow is defined in [`.github/workflows/ci-cd.yml`](../.github/workflows/ci-cd.yml).  
It runs automatically on every push to the `main` branch.

### Jobs
- **Build & Test**  
  - Sets up Python environment (3.9).  
  - Installs project dependencies.  
  - Runs **pylint** on `app.py`.  
  - Ensures the code maintains a quality score ≥ **8.0/10**.  
  - If the score falls below 8, the workflow fails.

---

## 📝 Workflow File

```yaml
name: True-Buddy Chatbot CI/CD Workflow

on:
  push:
    branches: [ main ]

jobs:
  build_and_test:
    name: Code standard analysing
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.9

      - name: Install dependencies
        run: |
          pip install pylint
          pip install -r requirements.txt
          sudo apt-get update && sudo apt-get install -y bc

      - name: Code linting with pylint on Streamlit app
        run: |
          SCORE=$(pylint app.py --exit-zero | grep -oP 'rated at \K[0-9]+\.[0-9]+')
          echo "Pylint score: $SCORE"
          if (( $(echo "$SCORE < 8" | bc -l) )); then
            echo "Pylint score is less than 8. Failing the workflow."
            exit 1
          fi
