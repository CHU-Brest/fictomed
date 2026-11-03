from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


BUILTIN_PROMPT_SETS_DIR = Path(__file__).resolve().parent / "templates"


@dataclass(frozen=True)
class PromptSet:
    name: str
    version: str
    root: Path
    source: str
    content_hash: str
    workflows: dict[str, bool]
    external: bool = False

    def supports(self, workflow: str) -> bool:
        return bool(self.workflows.get(workflow, False))


def _content_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _load_manifest(root: Path) -> dict[str, Any]:
    manifest_path = root / "manifest.yaml"
    if not manifest_path.is_file():
        raise FileNotFoundError(
            f"Le manifeste du jeu de prompts est introuvable : {manifest_path}"
        )
    with manifest_path.open("r", encoding="utf-8") as file:
        manifest = yaml.safe_load(file) or {}
    if not isinstance(manifest, dict):
        raise ValueError(f"Manifeste de prompts invalide : {manifest_path}")
    return manifest


def resolve_prompt_set(
    *,
    prompt_set: str = "default",
    prompt_dir: str | Path | None = None,
    workflow: str = "one_stage",
) -> PromptSet:
    if prompt_dir is not None and prompt_set != "default":
        raise ValueError("prompt_set et prompt_dir ne peuvent pas être fournis ensemble")

    external = prompt_dir is not None
    root = (
        Path(prompt_dir).expanduser().resolve()
        if external
        else BUILTIN_PROMPT_SETS_DIR / prompt_set
    )
    if not root.is_dir():
        raise FileNotFoundError(f"Jeu de prompts introuvable : {root}")

    manifest = _load_manifest(root)
    name = str(manifest.get("name") or root.name)
    version = str(manifest.get("version") or "")
    workflows = manifest.get("workflows") or {}
    if not isinstance(workflows, dict):
        raise ValueError(f"Champ workflows invalide dans {root / 'manifest.yaml'}")

    resolved = PromptSet(
        name=name,
        version=version,
        root=root,
        source=f"external:{root}" if external else f"builtin:{prompt_set}",
        content_hash=_content_hash(root),
        workflows={str(key): bool(value) for key, value in workflows.items()},
        external=external,
    )
    if not resolved.supports(workflow):
        raise ValueError(
            f"Le jeu de prompts '{resolved.name}' ne prend pas en charge "
            f"le workflow '{workflow}'"
        )
    return resolved


def template_path(prompt_set: PromptSet, template_name: str, stage: str) -> Path:
    filename = Path(str(template_name)).name
    if filename != str(template_name):
        raise ValueError(f"Nom de template invalide : {template_name}")
    if not filename.endswith(".txt"):
        filename = f"{filename}.txt"
    path = prompt_set.root / stage / filename
    if not path.is_file():
        raise FileNotFoundError(f"Template introuvable : {path}")
    return path


def snapshot_external_prompt_set(prompt_set: PromptSet, output_dir: Path) -> Path | None:
    if not prompt_set.external:
        return None
    snapshot_dir = (
        output_dir
        / "prompts_snapshot"
        / f"{prompt_set.name}-{prompt_set.version}-{prompt_set.content_hash[:12]}"
    )
    if not snapshot_dir.exists():
        snapshot_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(prompt_set.root, snapshot_dir)
    return snapshot_dir
