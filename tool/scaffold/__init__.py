from tool.scaffold.post_init import post_init
from tool.scaffold.springboot import create_springboot
from tool.scaffold.vue_vite import create_vue_vite

SUPPORTED_TYPES = {
    "vue3+vite": create_vue_vite,
    "vue": create_vue_vite,
    "springboot": create_springboot,
}


def create_project(project_name: str, project_type: str) -> dict:
    normalized = project_type.lower().strip()
    if normalized not in SUPPORTED_TYPES:
        supported = ", ".join(sorted(set(SUPPORTED_TYPES.keys())))
        raise ValueError(f"Unsupported project type '{project_type}'. Supported: {supported}")
    return SUPPORTED_TYPES[normalized](project_name)

__all__ = ["create_project", "post_init", "SUPPORTED_TYPES"]
