"""Execute a local recovery notebook with an explicitly selected Python.

Only local notebook outputs are updated. The temporary kernel registration and
runtime directories are removed when execution finishes.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import time

import nbformat
from nbclient import NotebookClient


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("notebook", type=Path)
    parser.add_argument("--cwd", type=Path)
    parser.add_argument("--python", default=sys.executable,
                        help="Python environment used by the notebook (default: this interpreter)")
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--original-workflow", action="store_true",
                        help="For CONCH/ESMFold2, execute acquisition, processing, model scoring and curves; requires the documented model environment and resources")
    args = parser.parse_args()
    notebook_path = args.notebook.resolve()
    cwd = (args.cwd or notebook_path.parent).resolve()
    notebook = nbformat.read(notebook_path, as_version=4)
    if args.original_workflow and not any(
        "RUN_ORIGINAL_WORKFLOW" in cell.get("source", "")
        for cell in notebook.cells if cell.cell_type == "code"
    ):
        parser.error("This notebook has no full-workflow switch. Use its documented historical replay without --original-workflow.")
    started = time.time()
    with tempfile.TemporaryDirectory(prefix="spectra-notebook-") as temp:
        temp = Path(temp)
        kernel = temp / "kernels" / "spectra-recovery"
        kernel.mkdir(parents=True)
        runtime = temp / "runtime"
        runtime.mkdir()
        kernel_env = {
            "MPLCONFIGDIR": str(temp / "matplotlib"),
            "IPYTHONDIR": str(temp / "ipython"),
            "JUPYTER_RUNTIME_DIR": str(runtime),
            "SPECTRA_RUN_ORIGINAL_WORKFLOW": "1" if args.original_workflow else "0",
        }
        (kernel / "kernel.json").write_text(json.dumps({
            "argv": [args.python, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
            "display_name": "SPECTRA recovery", "language": "python", "env": kernel_env,
        }))
        os.environ["JUPYTER_PATH"] = str(temp)
        os.environ["JUPYTER_RUNTIME_DIR"] = str(runtime)
        notebook.metadata.kernelspec = {
            "name": "spectra-recovery", "display_name": "SPECTRA recovery", "language": "python"
        }
        client = NotebookClient(notebook, timeout=args.timeout,
                                kernel_name="spectra-recovery",
                                resources={"metadata": {"path": str(cwd)}},
                                allow_errors=False)
        error = None
        try:
            client.execute()
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        notebook.metadata["recovery_execution"] = {
            "python": args.python, "working_directory": str(cwd),
            "elapsed_seconds": round(time.time() - started, 3),
            "completed": error is None, "error": error,
            "original_workflow_requested": args.original_workflow,
        }
        notebook.metadata.kernelspec = {
            "name": "python3", "display_name": "Python 3", "language": "python"
        }
        nbformat.write(notebook, notebook_path)
        print(json.dumps({"notebook": str(notebook_path),
                          **notebook.metadata["recovery_execution"]}, indent=2), flush=True)
        if error:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
