"""Environment profile loader for the lashtest CLI.

Profile files are simple ``KEY=VALUE`` dotenv-style files.  Two naming
conventions are supported:

* ``lashtest.{profile}.env``  (e.g. ``lashtest.staging.env``)
* ``.env.{profile}``          (e.g. ``.env.staging``)

Both files are looked up in the current working directory.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def load_env_profile(profile: str) -> Optional[str]:
    """Load environment variables from the profile file matching *profile*.

    Args:
        profile: The profile name, e.g. ``"staging"`` or ``"prod"``.

    Returns:
        The path of the loaded file as a string, or ``None`` if no
        matching file was found.
    """
    candidates = [
        Path(f"lashtest.{profile}.env"),
        Path(f".env.{profile}"),
    ]

    for candidate in candidates:
        if candidate.is_file():
            _parse_env_file(candidate)
            return str(candidate)

    return None


def _parse_env_file(path: Path) -> None:
    """Parse a dotenv-style file and inject variables into ``os.environ``."""
    for lineno, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        # Skip blanks and comments
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        # Strip optional surrounding quotes
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        if key:
            os.environ.setdefault(key, value)
