# SPDX-FileCopyrightText: 2026 RadiaSight
# SPDX-License-Identifier: GPL-3.0-or-later
"""Native file selection for Linux desktops without a Qt Python dependency."""

import shutil
import subprocess
from pathlib import Path


def open_linux_file(title: str, pattern: str, label: str) -> str:
    """Return a selected path, an empty string on cancel, or raise OSError."""
    if executable := shutil.which("kdialog"):
        command = [
            executable, "--title", title, "--getopenfilename",
            str(Path.home()), f"{pattern}|{label}\n*|All files",
        ]
    elif executable := shutil.which("zenity"):
        command = [
            executable, "--file-selection", f"--title={title}",
            f"--file-filter={label} | {pattern}", "--file-filter=All files | *",
        ]
    else:
        raise OSError("No file picker found. Install kdialog or zenity and try again.")

    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode == 1:
        return ""  # User cancelled.
    if result.returncode != 0:
        raise OSError(result.stderr.strip() or "Could not open the file picker.")
    return result.stdout.strip()
