import click
import os
import subprocess
import sys

from .reporter import generate_report


@click.group()
def cli():
    """API Test CLI - A command-line interface for API testing."""
    pass


@cli.command()
@click.argument('path', default='tests/')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--allure-dir', '-r', default='allure-results', help='directory for Allure report')
@click.option('--tags', '-t', default='', help='Comma-separated list of tags to filter tests')
def run(path, verbose, allure_dir, tags):
    """Run API tests located in the specified PATH.

    PATH can be a directory or a specific test file.
    Use --tags to filter tests by marker (comma-separated).

    Example:
      lashtest run tests/ -v -r my-results -t smoke,regression
    """
    os.makedirs(allure_dir, exist_ok=True)

    cmd = [
        'pytest',
        path,
        f'--alluredir={allure_dir}',
        '--clean-alluredir',
        '-s',
    ]

    if verbose:
        cmd.append('-v')

    if tags:
        tags_filter = ' or '.join(tag.strip() for tag in tags.split(',') if tag.strip())
        cmd.extend(['-m', tags_filter])

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


@cli.command()
@click.argument('results-dir', default='allure-results')
@click.argument('output-dir', default='allure-report')
def report(results_dir, output_dir):
    """Generate an Allure HTML report from test results.

    RESULTS-DIR: directory containing Allure JSON results (default: allure-results).
    OUTPUT-DIR:  directory where the HTML report will be written (default: allure-report).
    """
    generate_report(results_dir, output_dir)
