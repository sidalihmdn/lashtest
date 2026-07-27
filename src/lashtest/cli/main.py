import click
import os
import subprocess
import sys
from typing import Optional

from .reporter import generate_report
from .env_profile import load_env_profile


@click.group()
def cli():
    """API Test CLI - A command-line interface for API testing."""
    pass


@cli.command()
@click.argument('path', default='tests/')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--allure-dir', '-r', default='allure-results', help='Directory for Allure results')
@click.option('--tags', '-t', default='', help='Comma-separated list of tags to filter tests')
@click.option(
    '--parallel', '-p', default=None, type=int,
    help='Run tests in parallel using N workers (requires pytest-xdist). '
         'Pass -p auto to use all available CPUs.',
)
@click.option(
    '--junit-xml', default=None,
    help='Write a JUnit XML report to the given path.',
)
@click.option(
    '--env', default=None,
    help='Load environment variables from a named profile file '
         '(e.g. "staging" loads lashtest.staging.env or .env.staging).',
)
def run(path, verbose, allure_dir, tags, parallel, junit_xml, env):
    """Run API tests located in the specified PATH.

    PATH can be a directory or a specific test file.

    \b
    Examples:
      lashtest run                          # run all tests in tests/
      lashtest run tests/ -v                # verbose
      lashtest run -t smoke,regression      # filter by tags
      lashtest run -p 4                     # 4 parallel workers
      lashtest run --junit-xml report.xml   # JUnit XML output
      lashtest run --env staging            # load staging env profile
    """
    if env:
        loaded = load_env_profile(env)
        if loaded:
            click.echo(f"Loaded environment profile: {loaded}")
        else:
            click.echo(
                f"Warning: no env file found for profile '{env}'. "
                "Looked for lashtest.{env}.env and .env.{env}.",
                err=True,
            )

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

    if parallel is not None:
        cmd.extend(['-n', str(parallel)])

    if junit_xml:
        cmd.extend([f'--junit-xml={junit_xml}'])

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


@cli.command()
@click.argument('results-dir', default='allure-results')
@click.argument('output-dir', default='allure-report')
def report(results_dir, output_dir):
    """Generate an Allure HTML report from test results.

    RESULTS-DIR: directory containing Allure JSON result files (default: allure-results).
    OUTPUT-DIR:  directory where the HTML report will be written (default: allure-report).
    """
    generate_report(results_dir, output_dir)
