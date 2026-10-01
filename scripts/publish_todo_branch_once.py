"""Publish the current immutable branch once through the owner Risk 3 gateway."""
from __future__ import annotations

import subprocess


TARGET = "docs/powerbi-todo-20261001"


def main() -> int:
    branch = subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()
    if branch != TARGET:
        raise SystemExit(f"unexpected branch: {branch}")
    status = subprocess.check_output(["git", "status", "--porcelain"], text=True)
    if status:
        raise SystemExit("worktree must be clean")
    subprocess.run(["git", "push", "origin", f"HEAD:refs/heads/{TARGET}"], check=True)
    remote = subprocess.check_output(
        ["git", "ls-remote", "--heads", "origin", f"refs/heads/{TARGET}"], text=True
    ).split()[0]
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if remote != head:
        raise SystemExit(f"remote SHA mismatch: {remote} != {head}")
    print(f"PUBLISH_OK branch={TARGET} sha={head}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
