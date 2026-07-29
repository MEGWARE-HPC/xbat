#! /usr/bin/env -S uv run

import importlib
import os
import shutil
import sys
from pathlib import Path


def main():
    uv_path = shutil.which("uv")
    if uv_path is None:
        print('Error: "uv" command not found.', file=sys.stderr)
        sys.exit(1)

    project_root = Path(__file__).parent.absolute()
    expected_prefix = project_root / ".venv"
    # Fix uv project context
    if Path(sys.prefix) != expected_prefix:
        print(
            f"Changing working directory to project root: {project_root}",
            file=sys.stderr,
        )
        os.chdir(project_root)
        args = ["uv", "run", Path(__file__).name] + sys.argv[1:]
        os.execvp(args[0], args)

    status = os.system("uv sync")
    if status != os.EX_OK:
        return os.exit(status)

    toml = importlib.import_module("tomllib")
    pyproject_path = project_root / "pyproject.toml"
    script_path = pyproject_path.parent
    with open(pyproject_path, "rb") as f:
        pyproject = toml.load(f)
        try:
            package_dir = pyproject["tool"]["setuptools"]["package-dir"]
            assert len(package_dir) == 1
            script_path /= Path(list(package_dir.values())[0])
        except Exception:
            print(
                f'Could not parse "package-dir" (setuptools) from {pyproject_path}.',
                file=sys.stderr,
            )
            sys.exit(1)
        try:
            script = pyproject["project"]["scripts"]["xbat"]
            for s in script.split(":")[0].split("."):
                script_path /= s
            script_path = script_path.with_suffix(".py")
            assert script_path.exists()
        except Exception:
            print(
                f'Could not parse Python source path for script "xbat" from {pyproject_path}.',
                file=sys.stderr,
            )
            sys.exit(1)

    cmd = [
        sys.executable,
        "-m",
        "nuitka",
        "--onefile",
        "--follow-imports",
        f"--output-dir={project_root / 'dist'}",
        "--python-flag=-m",
        script_path.parent,
    ]

    os.execvp(cmd[0], cmd)


if __name__ == "__main__":
    main()
