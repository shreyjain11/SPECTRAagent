"""Rescore retained Kimi r2 coordinates without running model inference.

Usage: python reproduction/review_20261115/verify_esmfold_coordinates.py \
    --inputs /path/to/assets/kimi-r2/audit --output /tmp/coordinate-check.json

Requires the notebook's CPU analysis dependencies, including tmtools and Biopython.
The selected notebook cells verify split membership, score stored coordinates,
aggregate curves and calculate the reported endpoint and sensitivity results.
"""
import argparse
import io
import json
import os
from pathlib import Path

os.environ.setdefault('MPLBACKEND', 'Agg')
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
from IPython.display import Image
from Bio.SeqUtils import seq1
from tmtools import tm_align

def display(*args):
    pass

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    notebook = Path(__file__).resolve().parents[1] / 'inline/esmfold2/esmfold2-kimi-r2/test-01.ipynb'
    book = json.loads(notebook.read_text())
    namespace = dict(globals(), P=args.inputs.resolve())
    for index in [4, 6, 8, 10, 11, 13]:
        exec(compile(''.join(book['cells'][index]['source']), f'{notebook}:cell-{index}', 'exec'), namespace)
    namespace['control_results'].to_json(args.output, orient='records', indent=2)
    print(namespace['control_results'].to_string(index=False))

if __name__ == '__main__':
    main()
