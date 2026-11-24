# Exact handout review

Source: the supplied `lab9 -Profiling in python.docx` and LMS screenshot.
Only duplicated/broken formatting and malformed Python guards are repaired.

| Requirement | Evidence |
| --- | --- |
| Install all required libraries | `requirements.txt`; `reports/environment.json` |
| Original workload code | `before/profiler.py`; unchanged 2-second sleep and all loop bounds |
| Line-by-line performance script | `before/profiler_lineprofiler.py`; same function definitions |
| Decorated memory script | `before/profiler_memoryprofiler.py`; same full workloads |
| Provided test suite | `before/test_profiler.py`; all three methods, time.time, thresholds, strict RSS-increase assertion |
| Exact example optimization | `after/`: sum(i**2 for i in range(100)); optimized name called in all files |
| Both original and optimized four-file sets | `before/` and `after/` |
| Run cProfile, line_profiler, memory_profiler before/after | `reports/before/`, `reports/after/` |
| Run test_profiler before/after | Real direct test logs and native terminal screenshots |
| Run coverage commands | Exact coverage run -m unittest discover; coverage report -m; coverage html |
| Identify every missing line | Word report; raw coverage output and JSON |
| Full HTML reports and assets | `before/htmlcov/`, `after/htmlcov/` |
| Conventional terminal snapshots showing project name | Ten native screenshots of the live lab terminal; `capture_manifest.json` |
| All outputs and analysis in one named Word document | `lab9_Jad_ElHarake.docx` |
| Compare performance, memory, coverage | Measured before/after tables; no assumed speedup |
| Preserve genuine supplied-test failures | Original assertions retained; results and tracebacks reported truthfully |
| Solo submission | One student's files; no other student's solution used |
| GitHub repository | https://github.com/Jad490/lab9_Jad_ElHarake |
| Share repository with required accounts | NourSN2004, HusseinMoukalled, RanimTahmoush; verify actual access/invitation status |
| Moodle link file | `lab9_Jad_ElHarake_GitHub.txt`; upload after publication |

A supplied assertion may fail because a streaming sum need not increase RSS.
The assertion is retained exactly; a failure is not concealed or labeled as a pass.
External publication and Moodle completion must be verified separately.
