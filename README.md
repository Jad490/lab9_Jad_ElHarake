# Lab 9 — Profiling in Python

Jad El Harake · EECE 435L · Fall 2026–2027

This submission follows the supplied handout. Broken indentation, duplicated
fragments, and malformed `__main__` guards in the Word file were repaired so
that its code is executable. The original function logic, workload sizes,
three test methods, timing thresholds, and strict memory-increase assertion
are retained. No failing assertion is replaced or hidden.

The optimized files use the handout's exact example:

```python
def optimized_fast_function():
    return sum(i**2 for i in range(100))
```

All optimized scripts and tests call this function. `slow_function` still
sleeps for two seconds and sums 10,000 squares. The memory function still
sums 10,000,000 squares. The line-profiler and memory-profiler scripts contain
the same workload definitions as the main script, as in the handout.

## Files

- `before/`: original `profiler.py`, `profiler_lineprofiler.py`,
  `profiler_memoryprofiler.py`, and `test_profiler.py`.
- `after/`: the corresponding optimized four files.
- `lab9_Jad_ElHarake.docx`: one report with all before/after outputs,
  conventional screenshots of a live terminal, and analysis.
- `before/htmlcov/index.html`, `after/htmlcov/index.html`: complete coverage
  reports; keep all sibling CSS, JavaScript, and source-page assets.
- `reports/before/`, `reports/after/`: unedited command output and execution
  metadata, including actual failing test results if the supplied assertion fails.
- `reports/screenshots/`: native screenshots taken while the lab commands and
  results are displayed in a live browser-based PTY terminal.
- `reports/transcripts/`: original terminal bytes supporting the screenshots.
- `lab9_Jad_ElHarake_GitHub.txt`: the repository link requested by Moodle.

## Run the handout commands

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cd before
python -m cProfile -s time profiler.py
python profiler_lineprofiler.py
python -m memory_profiler profiler_memoryprofiler.py
python test_profiler.py
coverage run -m unittest discover
coverage report -m
coverage html
```

Repeat the same commands from `after/`. To run both sets automatically from
the repository root, use `python run_lab.py`. Each full line-by-line memory
profile can take several minutes. The tests and all reports use real results;
coverage is not increased by excluding statements or appending extra runs.

The handout requires final RSS to be strictly greater than initial RSS. A
streaming sum can reuse already allocated memory, so this supplied assertion
may fail. It is retained exactly, and any actual failure is explained in the
Word report. A failure is never represented as a pass. Likewise, the example
optimization is measured rather than assumed to be faster.

## Report and screenshot tools

```sh
python -m pip install -r requirements-report.txt
python tools/live_terminal.py
```

The helper binds only to `127.0.0.1:8769` and runs only fixed homework commands.
It shows a real, live PTY terminal in a separate browser page. Screenshots are
captured from that browser window using the computer-use screenshot API;
no screenshot is drawn from a transcript or produced with an image model.

After saving the required screenshots and measurements:

```sh
python benchmark.py
python tools/build_report.py
python tools/validate_submission.py
python tools/package_submission.py
```

## Submission requirements

The LMS requests a `.txt` file containing the GitHub repository URL, and
sharing the repository with `NourSN2004`, `HusseinMoukalled`, and `RanimTahmoush`.
The displayed deadline is 19 November 2026, 11:59 PM. Publication, access, and
Moodle submission are tracked separately from the measured code results.
