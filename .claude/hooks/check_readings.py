#!/usr/bin/env python3
"""Claude Code hook (PreToolUse, Bash): before a git commit, every text that a
student reads among the files committed must have been read once by the subagent
student-reader before the commit, with an answer to every point.

The texts that a student reads are the .md and .ipynb files of cases/ and every
README.md. For each one, the hook looks in .claude/readings/ for the record of the
file (its path with "/" replaced by "__", plus ".json") and takes its last reading.
The reading must be later than the last commit that changed the file, so that a
reading made before an earlier commit does not count for a new change; a file not yet in any
commit takes any reading. Every point of that reading must have a response. The
version committed may differ from the version read: the corrections made after the
reading do not need another one. If a text is missing any of that, the commit is
blocked and the hook says what is missing.

The hook reads the JSON that Claude Code sends on stdin and exits with 2 to block
the command, writing the reason on stderr; with 0 the command runs.
"""

import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime

READINGS = os.path.join(".claude", "readings")


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)


def repository(command, cwd):
    """The folder in which the commit runs: the one of "git -C <dir>", or of a
    "cd <dir>" before it, or the working folder of the session."""
    folder = cwd
    move = re.search(r"\bcd\s+(\"[^\"]+\"|'[^']+'|\S+)\s*(&&|;)", command)
    if move:
        folder = os.path.join(folder, os.path.expanduser(shlex.split(move.group(1))[0]))
    option = re.search(r"\bgit\s+-C\s+(\"[^\"]+\"|'[^']+'|\S+)", command)
    if option:
        folder = os.path.join(folder, os.path.expanduser(shlex.split(option.group(1))[0]))
    top = git(folder, "rev-parse", "--show-toplevel")
    return top.stdout.strip() if top.returncode == 0 else None


def read_by_students(path):
    name = os.path.basename(path)
    return name == "README.md" or (path.startswith("cases/") and path.endswith((".md", ".ipynb")))


def last_change(repo, path):
    """The date of the last commit that changed the file, or None if no commit has it."""
    date = git(repo, "log", "-1", "--format=%cI", "--", path).stdout.strip()
    return datetime.fromisoformat(date) if date else None


def committed(repo, command):
    """The texts that a student reads among the files of the commit. With -a or
    --all, the tracked files changed in the working tree enter the commit as well
    as the staged ones."""
    all_changes = re.search(r"\bcommit\b.*(\s--all\b|\s-[A-Za-z]*a[A-Za-z]*\b)", command)
    names = git(repo, "diff", "--cached", "--name-only", "--diff-filter=ACMR").stdout.split()
    if all_changes:
        names += git(repo, "diff", "--name-only", "--diff-filter=ACMR").stdout.split()
    return [path for path in dict.fromkeys(names) if read_by_students(path)]


def missing(repo, path):
    """What the record of a file lacks for the commit, or None."""
    record = os.path.join(repo, READINGS, path.replace("/", "__") + ".json")
    if not os.path.exists(record):
        return f"{path}: no reading by student-reader (no record {os.path.relpath(record, repo)})"
    try:
        with open(record, encoding="utf-8") as handle:
            readings = json.load(handle).get("readings", [])
    except (json.JSONDecodeError, OSError) as error:
        return f"{path}: the record cannot be read ({error})"
    if not readings:
        return f"{path}: the record has no reading"
    reading = readings[-1]
    changed = last_change(repo, path)
    if changed and not (reading.get("date") and datetime.fromisoformat(reading["date"]) > changed):
        return (f"{path}: no reading after the last commit that changed the file "
                f"({changed.isoformat()}); the new change needs one")
    unanswered = [str(p.get("id", "?")) for p in reading.get("points", []) if not str(p.get("response", "")).strip()]
    if unanswered:
        return f"{path}: points without a response in the reading of {reading.get('date', 'no date')}: {', '.join(unanswered)}"
    return None


def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Bash":
        return 0
    command = data.get("tool_input", {}).get("command", "")
    if not re.search(r"\bgit\b[^;&|]*\bcommit\b", command):
        return 0
    repo = repository(command, data.get("cwd") or os.getcwd())
    if not repo or not os.path.exists(os.path.join(repo, ".claude", "hooks", "check_readings.py")):
        return 0
    problems = [m for path in committed(repo, command) if (m := missing(repo, path))]
    if problems:
        print("Commit blocked: every text that a student reads must be read once by the subagent "
              "student-reader before each commit that changes it, with a response to every point.\n- "
              + "\n- ".join(problems), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
