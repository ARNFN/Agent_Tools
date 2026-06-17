import subprocess
from pathlib import Path

from tool.scaffold.subprocess_util import resolve_command

ROOT = Path(__file__).resolve().parents[2]
PROJECTS_DIR = ROOT / "projects"


def post_init(project_name: str, project_type: str) -> dict:
    target = PROJECTS_DIR / project_name
    if not target.exists():
        raise FileNotFoundError(f"Project '{project_name}' not found at {target}")

    results = []

    git_dir = target / ".git"
    if not git_dir.exists():
        subprocess.run(
            ["git", "init"],
            cwd=str(target),
            check=True,
            shell=False,
        )
        results.append("git init")

    if project_type in ("vue3+vite", "vue"):
        npm = resolve_command("npm")
        subprocess.run(
            [npm, "install"],
            cwd=str(target),
            check=True,
            shell=False,
        )
        results.append("npm install")
    elif project_type == "springboot":
        mvnw = target / "mvnw.cmd"
        if mvnw.exists():
            subprocess.run(
                [str(mvnw), "-q", "dependency:resolve"],
                cwd=str(target),
                check=True,
                shell=False,
            )
            results.append("mvnw.cmd dependency:resolve")

    return {
        "project_name": project_name,
        "type": project_type,
        "path": str(target.resolve()),
        "steps": results,
    }
