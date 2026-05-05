import os
import subprocess
import sys
from typing import Optional


def run_tests(path: str, results_dir: str, verbose: bool = False, tags: Optional[str] = None) -> int:
    """Run pytest on the given path and write Allure results.

    Args:
        path: Directory or file to pass to pytest.
        results_dir: Directory where Allure JSON results are written.
        verbose: Whether to pass -v to pytest.
        tags: Optional pytest marker expression for filtering tests.

    Returns:
        The pytest process return code.
    """
    os.makedirs(results_dir, exist_ok=True)

    cmd = [
        'pytest',
        path,
        f'--alluredir={results_dir}',
        '--clean-alluredir',
        '-s',
    ]

    if verbose:
        cmd.append('-v')

    if tags:
        cmd.extend(['-m', tags])

    result = subprocess.run(cmd)
    return result.returncode
