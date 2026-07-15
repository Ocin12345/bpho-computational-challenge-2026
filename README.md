# BPhO Computational Challenge 2026

Project workspace for the British Physics Olympiad Computational Challenge.

## Project goals

- Implement the challenge models in Python.
- Keep code, calculations, figures, and explanations together.
- Record enough working to support the final three-minute screencast.

## Suggested workflow

1. Work on one task at a time.
2. Save reusable code in the relevant `taskXX_*` folder.
3. Save exploratory notebooks in `notebooks/`.
4. Save generated graphs in `figures/`.
5. Pull before working and commit/push before switching computers.

## Environment

The intended environment uses Python with NumPy, Matplotlib, SciPy, and Jupyter.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The virtual environment is intentionally excluded from Git.

## Competition reminder

The final entry is a maximum three-minute unlisted YouTube screencast showing the
models, code or spreadsheets, graphs, results, and explanation of the working.
