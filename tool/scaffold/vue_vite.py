import subprocess
from pathlib import Path

from tool.scaffold.subprocess_util import resolve_command

ROOT = Path(__file__).resolve().parents[2]
PROJECTS_DIR = ROOT / "projects"


def create_vue_vite(project_name: str) -> dict:
    target = PROJECTS_DIR / project_name
    if target.exists():
        raise FileExistsError(
            f"Directory '{project_name}' already exists. "
            f"Please choose a different project name."
        )

    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

    npm = resolve_command("npm")
    subprocess.run(
        [npm, "create", "vite@latest", project_name, "--", "--template", "vue"],
        cwd=str(PROJECTS_DIR),
        check=True,
        shell=False,
    )

    return {
        "project_name": project_name,
        "type": "vue3+vite",
        "path": str(target.resolve()),
    }
