# Accessibility Evaluator

## Setup Instructions

1. Clone the repository or download this folder.
2. Navigate to the folder in your terminal.
3. Set up a virtual environment (optional but recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

4. Install Python dependencies:

```bash
pip install -r requirements.txt
```

5. Install Playwright dependencies:

```bash
playwright install
```

6. Install axe-core JavaScript library:

```bash
npm install axe-core
```

(You need Node.js and npm installed for this step)

## Running the Tool

```bash
python main.py https://example.com
```

This will generate a `report.json` with the accessibility audit results.

## Notes

- Ensure you have Node.js installed for axe-core.
- You can expand this tool with additional modules to check specific metrics like alt text coverage, keyboard navigation, etc.
