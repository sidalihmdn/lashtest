import subprocess
import sys


def generate_report(results_dir: str, output_dir: str) -> None:
    """Call the Allure CLI to generate an HTML report.

    Args:
        results_dir: Directory containing Allure JSON result files.
        output_dir: Directory where the HTML report will be written.

    Raises:
        SystemExit: If the allure command is not found or returns a non-zero exit code.
    """
    cmd = ['allure', 'generate', results_dir, '-o', output_dir, '--clean']
    try:
        result = subprocess.run(cmd)
    except FileNotFoundError:
        print(
            "Error: 'allure' command not found. "
            "Install the Allure CLI: https://docs.qameta.io/allure/#_installing_a_commandline",
            file=sys.stderr,
        )
        sys.exit(1)

    if result.returncode != 0:
        sys.exit(result.returncode)

    print(f"Report generated in: {output_dir}")
