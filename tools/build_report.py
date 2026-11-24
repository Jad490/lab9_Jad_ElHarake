"""Build the requested Word report from real, saved profiling artifacts."""

import json
from pathlib import Path
import re
import sys

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
SHOTS = [
    ('01_before_cprofile.png', 'cProfile — before'),
    ('02_after_cprofile.png', 'cProfile — after'),
    ('03_before_line_profiler.png', 'line_profiler — before'),
    ('04_after_line_profiler.png', 'line_profiler — after'),
    ('05_before_tests.png', 'test_profiler.py — before'),
    ('06_after_tests.png', 'test_profiler.py — after'),
    ('07_before_coverage.png', 'coverage.py — before'),
    ('08_after_coverage.png', 'coverage.py — after'),
    ('09_before_memory_profiler.png', 'memory_profiler — before'),
    ('10_after_memory_profiler.png', 'memory_profiler — after'),
]


def read(stage, name):
    return (REPORTS / stage / (name + ".txt")).read_text()


def line_times(stage):
    text = read(stage, "line_profiler")
    return {name: float(seconds) for seconds, name in re.findall(
        r"Total time: ([\deE.+-]+) s\nFile: [^\n]+\nFunction: (\w+)", text)}


def cprofile_total(stage):
    return float(re.search(r"function calls in ([\d.]+) seconds", read(stage, "cprofile"))[1])


def rss_range(stage):
    # First MiB column is memory usage; the second is the cumulative increment.
    rows = re.findall(r"^\s*\d+\s+([\d.]+) MiB\s+([-\d.]+) MiB", read(stage, "memory_profiler"), re.M)
    values = [float(usage) for usage, _ in rows]
    if not values:
        raise ValueError(f"No memory_profiler rows for {stage}")
    return min(values), max(values)


def heading(doc, title, level=1, newpage=False):
    if newpage:
        doc.add_page_break()
    doc.add_heading(title, level)


def paragraph(doc, text):
    doc.add_paragraph(text)


def code(doc, text, size=9):
    text = "".join(ch if ord(ch) >= 32 or ch in "\t\n\r" else "\\x" + format(ord(ch), "02x") for ch in text)
    for line in text.strip("\n").splitlines():
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1
        run = p.add_run(line or " ")
        run.font.name = "Courier New"
        run.font.size = Pt(size)


def table(doc, headers, rows):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.autofit = False
    widths = {2: [3.1, 7.2], 3: [4.7, 2.8, 2.8], 5: [3.3, 1.0, 1.0, 1.4, 3.6]}[len(headers)]
    for column, width in zip(t.columns, widths):
        column.width = Inches(width)
    for cell, text in zip(t.rows[0].cells, headers):
        cell.text = str(text)
        shade = OxmlElement("w:shd")
        shade.set(qn("w:fill"), "80002F")
        cell._tc.get_or_add_tcPr().append(shade)
        for run in cell.paragraphs[0].runs:
            run.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)
    for row in rows:
        for cell, text in zip(t.add_row().cells, row):
            cell.text = str(text)
    for row in t.rows:
        for cell, width in zip(row.cells, widths):
            cell.width = Inches(width)
            for p in cell.paragraphs:
                p.paragraph_format.space_after = Pt(3)
                for r in p.runs:
                    r.font.size = Pt(10)
    doc.add_paragraph()


def metadata(stage,name):
    return json.loads((REPORTS/stage/(name+'.json')).read_text())


def test_result(stage,name='tests'):
    text=read(stage,name)
    match=re.search(r'Ran (\d+) tests in ([\d.]+)s',text)
    return f"{match[1]} tests; "+('PASS' if metadata(stage,name)['exit_code']==0 else 'FAIL (see actual output)')


def main():
    missing=[name for name,_ in SHOTS if not (REPORTS/'screenshots'/name).exists()]
    if missing:raise SystemExit('Native terminal screenshots still required: '+', '.join(missing))
    captures=json.loads((REPORTS/'screenshots/capture_manifest.json').read_text())
    assert len(captures)==len(SHOTS) and all(x['method']=='native_screenshot_live_terminal' for x in captures)
    env=json.loads((REPORTS/'environment.json').read_text())
    bench=json.loads((REPORTS/'benchmark.json').read_text())
    cov={stage:json.loads((REPORTS/stage/'coverage.json').read_text()) for stage in ('before','after')}
    doc=Document();sec=doc.sections[0]
    sec.orientation=WD_ORIENT.LANDSCAPE;sec.page_width=Inches(11.69);sec.page_height=Inches(8.27)
    sec.top_margin=sec.bottom_margin=Inches(.55);sec.left_margin=sec.right_margin=Inches(.65)
    normal=doc.styles['Normal'];normal.font.name='Arial';normal.font.size=Pt(11);normal.paragraph_format.space_after=Pt(6)
    for name in ('Title','Heading 1','Heading 2'):
        doc.styles[name].font.name='Arial';doc.styles[name].font.color.rgb=RGBColor.from_string('80002F')
    doc.core_properties.title='Lab 9 — Profiling in Python';doc.core_properties.author='Jad El Harake'
    footer=sec.footer.paragraphs[0];footer.add_run('EECE 435L | Lab 9 | Jad El Harake                                      Page ')
    field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
    doc.add_heading('Lab 9 — Profiling in Python',0)
    paragraph(doc,'Jad El Harake | EECE 435L — Software Tools Lab | Fall 2026–2027 | 23 November 2026')
    paragraph(doc,'Project: lab9_Jad_ElHarake. This report contains the original and optimized profiling results, supplied test results, coverage analysis, and conventional screenshots of the actual commands and output in a live terminal.')
    heading(doc,'Fidelity to the handout',2)
    paragraph(doc,'The Word handout contains duplicated fragments, broken indentation, and malformed __main__ guards. Only those formatting/syntax defects were repaired. The original workloads, all three supplied test methods, time.time timing, duration thresholds, and strict RSS-after > RSS-before assertion are retained. The after files use the exact example optimized_fast_function: return sum(i**2 for i in range(100)). All optimized callers and profiler registrations use that function.')
    paragraph(doc,'No artificial memory allocation was added to force a test to pass. No failed assertion was replaced. Test outcomes and performance changes are reported as observed, including failures or a lack of speedup.')
    table(doc,['Environment','Recorded value'],[('Python',env['python'].splitlines()[0]),('Platform',env['platform']),('Packages','; '.join(k+' '+v for k,v in env['packages'].items())),('Unchanged workloads','2-second sleep; 10,000 slow-loop squares; 100 fast-loop squares; 10,000,000 memory-loop squares')])
    heading(doc,'Measured overview',2)
    table(doc,['Metric','Before','After'],[
        ('cProfile total elapsed time (s)',f"{cprofile_total('before'):.3f}",f"{cprofile_total('after'):.3f}"),
        ('Fast function median, unprofiled (µs/call)',f"{bench['functions']['baseline_loop']['median_seconds']*1e6:.3f}",f"{bench['functions']['handout_generator']['median_seconds']*1e6:.3f}"),
        ('Supplied test_profiler.py',test_result('before'),test_result('after')),
        ('Coverage run test outcome',test_result('before','coverage_run'),test_result('after','coverage_run')),
        ('profiler.py statement coverage',cov['before']['files']['profiler.py']['summary']['percent_covered_display']+'%',cov['after']['files']['profiler.py']['summary']['percent_covered_display']+'%'),
    ])
    heading(doc,'1. Performance profiling',newpage=True)
    heading(doc,'cProfile',2)
    paragraph(doc,'Command: python -m cProfile -s time profiler.py. tottime is internal time excluding called functions; cumtime includes callees. time.sleep consumes about two seconds of elapsed waiting. slow_function therefore has a large cumulative time despite little arithmetic work. The 10-million-square loop is the main computational bottleneck. The fast function is a very small portion of the complete program.')
    paragraph(doc,f"The original run took {cprofile_total('before'):.3f} seconds and the optimized run took {cprofile_total('after'):.3f} seconds under cProfile. These are individual instrumented runs, so small differences cannot establish a whole-program improvement. The optimized generator produces additional generator calls and a sum call in cProfile; that instrumentation can alter its relative timing. The repeated unprofiled comparison below is the more suitable measure of the tiny fast function.")
    heading(doc,'line_profiler',2)
    times={stage:line_times(stage) for stage in ('before','after')}
    table(doc,['Function','Before instrumented time (s)','After instrumented time (s)'],[
        ('slow_function',times['before']['slow_function'],times['after']['slow_function']),
        ('fast_function / optimized_fast_function',times['before']['fast_function'],times['after']['optimized_fast_function']),
        ('memory_intensive_function',times['before']['memory_intensive_function'],times['after']['memory_intensive_function']),
    ])
    paragraph(doc,'The sleep line dominates slow_function. The original fast loop executes its square-and-add line 100 times and its loop header 101 times. The large loop executes its arithmetic 10,000,000 times, with 10,000,001 loop-header hits. The after fast function is the single sum(generator) return expression. Line reports identify exactly which lines incur cost, but timer resolution and tracing overhead limit conclusions from a single tiny function call. The complete reports are reproduced below.')
    heading(doc,'2. Memory profiling',newpage=True)
    paragraph(doc,'Command: python -m memory_profiler profiler_memoryprofiler.py. Mem usage is observed process RSS in MiB, Increment is the attributed memory change, and Occurrences is the number of executions of a line. The interpreter and profiling library contribute to RSS; these values are not just local-variable sizes. All ten million iterations are retained in both runs.')
    memory={stage:rss_range(stage) for stage in ('before','after')}
    table(doc,['Observation','Before','After'],[
        ('Line-reported RSS range (MiB)',f"{memory['before'][0]:.3f}–{memory['before'][1]:.3f}",f"{memory['after'][0]:.3f}–{memory['after'][1]:.3f}"),
        ('Full command wall time (s)',f"{metadata('before','memory_profiler')['wall_seconds']:.3f}",f"{metadata('after','memory_profiler')['wall_seconds']:.3f}"),
    ])
    paragraph(doc,'The two full memory-tracing runs used separate processes concurrently. Their command durations reflect tracing overhead and shared machine load; these durations are not used to claim a runtime speedup. RSS is measured for each individual profiled process.')
    paragraph(doc,'Despite its name, memory_intensive_function uses range and one running total, rather than storing a collection of ten million squares. It keeps a constant number of Python objects; integer storage changes with the number of bits required. Python can reuse already allocated memory, so RSS need not increase after the function. The generator also avoids materializing a list, but the original loop already avoided one. Consequently, this example does not establish a reduction in retained memory.')
    paragraph(doc,'On repeated loop lines, memory_profiler may show very large negative accumulated Increment values while Mem usage stays small. Repeated attributed differences can accumulate over millions of hits as RSS changes. That total is not a simultaneous allocation, a peak measurement, or proof that gigabytes were freed. The observed Mem usage column is the relevant scale for process memory. The long traced run is not an ordinary runtime benchmark.')
    heading(doc,'3. Supplied tests — unchanged logic',newpage=True)
    paragraph(doc,'Command: python test_profiler.py. All three test methods follow the handout: slow_function must take more than two seconds; the fast function must take less than one second; memory_intensive_function must take less than five seconds and its final RSS must be strictly greater than its initial RSS. The original before/after memory snapshots, time.time helper, and assertions are retained. In the after file, the fast-function call is replaced with optimized_fast_function as requested.')
    table(doc,['Execution','Before','After'],[('Direct test script',test_result('before'),test_result('after')),('Under coverage.py',test_result('before','coverage_run'),test_result('after','coverage_run'))])
    failures=[]
    for stage in ('before','after'):
        for name in ('tests','coverage_run'):
            if metadata(stage,name)['exit_code']:failures.append(stage+'/'+name)
    if failures:
        paragraph(doc,'Observed failing executions: '+', '.join(failures)+'. Their complete tracebacks are included in the raw-output pages and screenshots. An unchanged RSS fails the supplied strict-increase assertion even though a streaming sum can correctly return its result without growing process RSS. This limitation is documented; the assertion has not been weakened or replaced.')
    else:
        paragraph(doc,'The supplied tests passed in the recorded executions. The RSS-increase assertion is nevertheless environment-dependent: a streaming accumulator may reuse existing memory. A pass here does not make strict RSS growth a reliable correctness requirement on every machine.')
    paragraph(doc,'The tests print two-decimal timings exactly as supplied, so the tiny fast function can print 0.00 seconds in both versions. A separate timeit comparison measures that function more precisely. Its numerical return value is also checked to equal 328350 before timing.')
    heading(doc,'4. Code coverage and missing lines',newpage=True)
    paragraph(doc,'The exact requested commands were used: coverage run -m unittest discover; coverage report -m; coverage html. Default coverage includes profiler.py and test_profiler.py. No source filter, exclusion, custom test, or appended CLI run was used to inflate the result. Coverage data can be generated even when a supplied assertion fails; execution coverage and test success are different properties.')
    rows=[]
    for stage in ('before','after'):
        for filename,info in cov[stage]['files'].items():
            s=info['summary'];rows.append((stage+'/'+filename,str(s['num_statements']),str(s['missing_lines']),s['percent_covered_display']+'%',', '.join(map(str,info['missing_lines'])) or 'None'))
    table(doc,['Version/file','Statements','Missing count','Coverage','Missing line numbers'],rows)
    for stage in ('before','after'):
        heading(doc,stage.capitalize()+': unexecuted statements',2)
        for filename,info in cov[stage]['files'].items():
            source=(ROOT/stage/filename).read_text().splitlines()
            for line in info['missing_lines']:
                paragraph(doc,f'{filename}:{line}: {source[line-1].strip()}')
    paragraph(doc,'Unittest discovery imports profiler.py and calls the three computational functions directly. It does not call the program main() or its __main__ entry point. Likewise, the test script main()/__main__ path is not entered when unittest imports it for discovery. These unexecuted startup statements explain the reported gaps. The complete HTML directories are before/htmlcov/ and after/htmlcov/; each includes index.html, source pages, stylesheets, and JavaScript.')
    heading(doc,'5. Exact example optimization and comparison',newpage=True)
    code(doc,'def optimized_fast_function():\n    return sum(i**2 for i in range(100))')
    paragraph(doc,'The after version uses the exact example from Part 6 in profiler.py, profiler_lineprofiler.py, and profiler_memoryprofiler.py, and calls it from test_profiler.py. It replaces the explicit total-update loop with sum over a generator. Both implementations perform 100 squarings and have linear iteration work in the range size. The original and generator versions both stream values without retaining a list.')
    table(doc,['Implementation','Median (µs/call)','Range of seven batch averages (µs/call)'],[
        (name,f"{v['median_seconds']*1e6:.3f}",f"{v['min_seconds']*1e6:.3f}–{v['max_seconds']*1e6:.3f}") for name,v in bench['functions'].items()
    ])
    ratio=bench['median_speedup_ratio']
    paragraph(doc,f"The repeated measurement uses seven batches of 20,000 calls per implementation, divided by the call count. Baseline median / generator median = {ratio:.3f}. A ratio above one means the generator was faster in this measurement; a ratio below one means it was slower. The actual measured ratio, rather than the name optimized_fast_function, determines the observed effect. A shorter generator expression is not guaranteed to run faster because it adds generator machinery.")
    paragraph(doc,'The full program remains dominated by the two-second sleep and ten-million-item calculation. The fast-function call is only a tiny share of its elapsed time, so even a small function-level improvement would have negligible whole-program impact. Memory is already streamed in both versions. Coverage differences reflect the changed number of statements while the same startup paths remain unexecuted. No improvement is claimed where the measurements do not establish one.')
    heading(doc,'Reproduce the measurements',2)
    code(doc,'python3 -m venv .venv\nsource .venv/bin/activate\npython -m pip install -r requirements.txt\npython run_lab.py\npython benchmark.py')
    paragraph(doc,'The Word appendix displays any nonprinting terminal-control bytes as visible hexadecimal escapes; the raw text and .tty files retain the original bytes.')
    paragraph(doc,'Native screenshots were taken of a live, isolated browser-based PTY terminal. The page displays an actual shell executing the fixed lab commands; it is not a generated screenshot, static transcript image, or image-model output. The project name, stage, command, returning shell prompt, and results are visible. The raw terminal bytes and command metadata are retained for review.')
    heading(doc,'Sources',2)
    for text in ['Provided lab9 -Profiling in python.docx and LMS screenshot','Python profiling documentation: https://docs.python.org/3.9/library/profile.html','line_profiler documentation: https://kernprof.readthedocs.io/en/latest/','memory_profiler documentation: https://github.com/pythonprofilers/memory_profiler','coverage.py documentation: https://coverage.readthedocs.io/en/latest/commands/cmd_run.html']:
        paragraph(doc,text)
    from PIL import Image
    for filename,title in SHOTS:
        heading(doc,'Terminal screenshot: '+title,newpage=True)
        p=doc.add_paragraph();p.paragraph_format.space_after=Pt(0)
        with Image.open(REPORTS/'screenshots'/filename) as img:w,h=img.size
        p.add_run().add_picture(str(REPORTS/'screenshots'/filename),width=Inches(min(9.55,5.9*w/h)))
        paragraph(doc,'Native screenshot of the live lab terminal: reports/screenshots/'+filename)
    for stage in ('before','after'):
        for name in ('cprofile','line_profiler','memory_profiler','tests','coverage_run','coverage_report','coverage_html'):
            heading(doc,'Raw output — '+stage+': '+name,newpage=True)
            m=metadata(stage,name);paragraph(doc,m['cwd']+' $ '+m['command']+' | exit '+str(m['exit_code'])+' | '+m['timestamp_utc'])
            code(doc,read(stage,name),size=8)
    path=ROOT/'lab9_Jad_ElHarake.docx';doc.save(path)
    print('Created',path.name,'with',len(doc.inline_shapes),'native screenshots.')


if __name__=='__main__':main()
