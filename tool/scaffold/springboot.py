import io
import zipfile
from pathlib import Path
from urllib.parse import urlencode

import httpx

from tool.scaffold.config import get_springboot_defaults

ROOT = Path(__file__).resolve().parents[2]
PROJECTS_DIR = ROOT / "projects"
SPRING_IO_URL = "https://start.spring.io/starter.zip"


def _normalize_boot_version(version: str) -> str:
    """Strip .RELEASE — Initializr accepts it but embeds it in pom.xml where Maven Central has no such artifact."""
    return version.removesuffix(".RELEASE")


def _safe_db_name(project_name: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in project_name).lower() or "app"


def _append_database_config(target: Path, project_name: str, db_cfg: dict) -> list[str]:
    props_path = target / "src" / "main" / "resources" / "application.properties"
    if not props_path.exists():
        return []

    db_name = _safe_db_name(project_name)
    url_template = db_cfg.get(
        "url_template",
        "jdbc:mysql://localhost:3306/{db_name}?useSSL=false&serverTimezone=Asia/Shanghai&characterEncoding=utf8",
    )
    jpa_cfg = db_cfg.get("jpa", {})

    lines = [
        "",
        "# --- database (from scaffold_defaults.yaml) ---",
        f"spring.datasource.url={url_template.format(db_name=db_name)}",
        f"spring.datasource.username={db_cfg.get('username', 'root')}",
        f"spring.datasource.password={db_cfg.get('password', '')}",
        f"spring.datasource.driver-class-name={db_cfg.get('driver_class_name', 'com.mysql.cj.jdbc.Driver')}",
        f"spring.jpa.hibernate.ddl-auto={jpa_cfg.get('hibernate_ddl_auto', 'update')}",
        f"spring.jpa.show-sql={str(jpa_cfg.get('show_sql', True)).lower()}",
    ]

    with open(props_path, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return lines


def create_springboot(project_name: str) -> dict:
    cfg = get_springboot_defaults()
    boot_version = _normalize_boot_version(cfg.get("boot_version", "3.5.15"))

    target = PROJECTS_DIR / project_name
    if target.exists():
        raise FileExistsError(
            f"Directory '{project_name}' already exists. "
            f"Please choose a different project name."
        )

    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

    group_id = cfg.get("group_id", "com.example")
    java_version = cfg.get("java_version", "17")
    dependencies = cfg.get("dependencies", ["web", "data-jpa", "mysql"])

    params = {
        "type": "maven-project",
        "language": "java",
        "bootVersion": boot_version,
        "baseDir": project_name,
        "groupId": group_id,
        "artifactId": project_name,
        "name": project_name,
        "packageName": f"{group_id}.{project_name.replace('-', '')}",
        "javaVersion": java_version,
        "dependencies": ",".join(dependencies),
    }

    url = f"{SPRING_IO_URL}?{urlencode(params)}"
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()
        zip_data = resp.content

    with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
        zf.extractall(PROJECTS_DIR)

    db_lines = _append_database_config(target, project_name, cfg.get("database", {}))

    return {
        "project_name": project_name,
        "type": "springboot",
        "path": str(target.resolve()),
        "boot_version": boot_version,
        "database_configured": bool(db_lines),
    }
