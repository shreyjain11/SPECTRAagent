"""Create a dedicated original-CONCH model environment; never edit an existing env."""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--venv', type=Path, default=ROOT / '.venv-inference')
    parser.add_argument('--device', choices=['cu124', 'cpu'], default='cu124')
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 11):
        parser.error('Run this setup with Python 3.11, matching the original environment.')
    if args.venv.exists():
        parser.error('Destination exists. Reuse it via CONCH_INFERENCE_PYTHON or choose a new --venv.')
    subprocess.run([sys.executable, '-m', 'venv', str(args.venv)], check=True)
    python = str(args.venv / 'bin/python')
    subprocess.run([python, '-m', 'pip', 'install', 'pip==25.0.1'], check=True)
    subprocess.run([python, '-m', 'pip', 'install', 'torch==2.5.0', 'torchvision==0.20.0',
                    '--index-url', 'https://download.pytorch.org/whl/' + args.device], check=True)
    subprocess.run([python, '-m', 'pip', 'install', '-r', str(ROOT / 'requirements_inference.txt')], check=True)
    subprocess.run([python, '-m', 'pip', 'check'], check=True)
    print('Model environment ready:', python)


if __name__ == '__main__':
    main()
