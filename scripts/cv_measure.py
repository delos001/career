#!/usr/bin/env python3
"""
cv_measure.py - measure a targeted CV's real page length in Word

The cv-targeted length check (cv_qc.py L1) estimates rendered length from
character counts, and the estimate runs short: CVs that passed it rendered
4 to 9 lines over the page ceiling (APP-014, APP-023, APP-027), and on APP-007
the writer cut a vetted bullet for an estimated 2-line overage. Only Word knows
how the text wraps and paginates, so this script asks it.

It renders cv_content.md to a throwaway .docx with the same builder cv-render
uses (cv_to_docx.build_cv), opens it read-only in a separate, invisible Word
instance, and reads the page count and the number of lines that spill past the
level's page ceiling. cv-targeted trims only on this measurement; the L1
estimate is advisory.

When Word cannot be reached (no Word, no pywin32, automation error) the result
is 'measured: false' with the reason, and the caller cuts nothing.

Output: one JSON object on stdout:
  {"measured": bool, "pages": int|null, "ceiling": int, "fits": bool|null,
   "lines_over": int|null, "detail": str}

Author    : Jason Delosh
Created   : 2026-11-05
Project   : career
Usage     : python scripts/cv_measure.py --cv-file <cv_content.md> --level <ic|leadership>
                --scratch-dir <dir>
Depends   : python-docx (via cv_to_docx), pywin32 and Microsoft Word for the measurement
"""

import argparse
import contextlib
import json
import os
import sys

import cv_qc
import cv_to_docx

# Word ComputeStatistics / GoTo constants (Word object model).
WD_STATISTIC_LINES = 1
WD_STATISTIC_PAGES = 2
WD_GOTO_PAGE = 1
WD_GOTO_ABSOLUTE = 1


# ---------------------------------------------------------------------------
# Assessment
# Pure decision on a measurement, kept separate from Word so it is testable on
# any machine.
# ---------------------------------------------------------------------------

def assess(pages, lines_beyond, ceiling):
    """Return the result dict for a measured (pages, lines_beyond) at a ceiling.

    lines_beyond is the number of rendered lines on the pages after the
    ceiling page (0 when the CV fits).
    """
    fits = pages <= ceiling
    detail = (f'{pages} page(s), within the {ceiling}-page ceiling' if fits
              else f'{pages} pages, {lines_beyond} line(s) past the {ceiling}-page ceiling')
    return {'measured': True, 'pages': pages, 'ceiling': ceiling, 'fits': fits,
            'lines_over': 0 if fits else lines_beyond, 'detail': detail}


def unmeasured(ceiling, reason):
    """Return the result dict when Word could not measure the CV."""
    return {'measured': False, 'pages': None, 'ceiling': ceiling, 'fits': None,
            'lines_over': None, 'detail': f'not measured: {reason}'}


# ---------------------------------------------------------------------------
# Word measurement
# DispatchEx starts a private Word instance, so a document the user has open
# in their own Word session is never touched. The file opens read-only and the
# instance quits in all cases.
# ---------------------------------------------------------------------------

def measure_docx(docx_path, ceiling):
    """Open docx_path in Word and return (pages, lines past the ceiling page)."""
    import pythoncom
    import win32com.client

    pythoncom.CoInitialize()
    word = None
    try:
        word = win32com.client.DispatchEx('Word.Application')
        word.Visible = False
        word.DisplayAlerts = 0
        doc = word.Documents.Open(os.path.abspath(docx_path), False, True)  # ConfirmConversions, ReadOnly
        try:
            pages = doc.ComputeStatistics(WD_STATISTIC_PAGES)
            lines_beyond = 0
            if pages > ceiling:
                start = doc.GoTo(WD_GOTO_PAGE, WD_GOTO_ABSOLUTE, ceiling + 1).Start
                lines_beyond = doc.Range(start, doc.Content.End).ComputeStatistics(WD_STATISTIC_LINES)
            return pages, lines_beyond
        finally:
            doc.Close(False)
    finally:
        if word is not None:
            word.Quit()
        pythoncom.CoUninitialize()


def measure(cv_file, level, scratch_dir):
    """Render cv_file to a scratch .docx and return the result dict."""
    ceiling = cv_qc.PAGE_CEILING[level]
    os.makedirs(scratch_dir, exist_ok=True)
    docx_path = os.path.join(scratch_dir, 'cv_measure.docx')
    # build_cv prints a 'Saved:' line; keep stdout for the JSON result only.
    with contextlib.redirect_stdout(sys.stderr):
        cv_to_docx.build_cv(cv_file, docx_path)
    try:
        pages, lines_beyond = measure_docx(docx_path, ceiling)
    except ImportError:
        return unmeasured(ceiling, 'pywin32 is not installed')
    except Exception as e:  # any Word automation failure: report, never cut
        return unmeasured(ceiling, f'Word automation failed ({type(e).__name__}: {e})')
    return assess(pages, lines_beyond, ceiling)


def main():
    parser = argparse.ArgumentParser(description="Measure a CV's real page length in Word.")
    parser.add_argument('--cv-file', required=True, help='path to cv_content.md')
    parser.add_argument('--level', required=True, choices=sorted(cv_qc.PAGE_CEILING))
    parser.add_argument('--scratch-dir', required=True,
                        help='folder for the throwaway .docx (the application scratch folder)')
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(measure(args.cv_file, args.level, args.scratch_dir)))


if __name__ == '__main__':
    main()
