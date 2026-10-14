#!/usr/bin/env python3
"""Mirror Pi's configured resources and package sources into this collection."""

from pathlib import Path
from urllib.parse import urlsplit
import json
import os
import re
import shutil
import sys
import tempfile

RESOURCE_TYPES = ("skills", "extensions", "prompts", "themes")
SAFE_SETTING_KEYS = (
    "defaultProvider",
    "defaultModel",
    "defaultThinkingLevel",
    "hideThinkingBlock",
    "theme",
    "compaction",
    "retry",
)
EXCLUDED_NAMES = {
    ".DS_Store", ".git", "node_modules", "__pycache__", "secrets",
    "auth.json", "credentials.json", ".npmrc", ".pypirc", ".netrc",
    ".nono-trust.bundle", "trust.json",
}
SECRET_PATTERNS = (
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("credential URL", re.compile(r"https?://[^/\s:@]+:[^/\s@]+@")),
    ("AWS key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("API token", re.compile(r"\bsk-[A-Za-z0-9_-]{24,}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    (
        "credential assignment",
        re.compile(
            r'''(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)\b'''
            r'''\s*[:=]\s*["'][^"'<>\s]{16,}["']'''
        ),
    ),
)


def ignored(directory: str, names: list[str]) -> list[str]:
    result = []
    for name in names:
        path = Path(directory) / name
        if (
            path.is_symlink()
            or name in EXCLUDED_NAMES
            or name.startswith(".env")
            or name.endswith((".pem", ".key"))
        ):
            result.append(name)
    return result


def source_files(root: Path):
    for current, dirs, files in os.walk(root, followlinks=False):
        base = Path(current)
        dirs[:] = [name for name in dirs if name not in ignored(current, dirs)]
        for name in files:
            path = base / name
            if name not in ignored(current, [name]) and not path.is_symlink():
                yield path


def read_json(path: Path, default=None):
    if not path.exists():
        return {} if default is None else default
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        raise ValueError(f"Invalid JSON in {path.name}") from None


def configured_paths(settings: dict, agent_dir: Path, kind: str) -> list[Path]:
    paths = []
    for raw in settings.get(kind, []):
        if not isinstance(raw, str) or raw.startswith(("!", "-")):
            continue
        raw = raw.removeprefix("+")
        candidate = Path(raw).expanduser()
        if not candidate.is_absolute():
            candidate = agent_dir / candidate
        if any(char in str(candidate) for char in "*?["):
            paths.extend(Path(p).resolve() for p in candidate.parent.glob(candidate.name))
        else:
            paths.append(candidate.resolve())
    return list(dict.fromkeys(paths))


def npm_name(source: str) -> str:
    spec = source.removeprefix("npm:")
    if spec.startswith("@"):
        scope, _, rest = spec.partition("/")
        return f"{scope}/{rest.split('@', 1)[0]}"
    return spec.split("@", 1)[0]


def resolve_package(source: str, agent_dir: Path) -> Path:
    if source.startswith("npm:"):
        return agent_dir / "npm" / "node_modules" / npm_name(source)
    if source.startswith("git:"):
        raw = source.removeprefix("git:").removeprefix("git+")
        if "://" not in raw:
            raw = "https://" + raw
        parsed = urlsplit(raw)
        host = parsed.hostname or parsed.netloc.rsplit("@", 1)[-1]
        segments = parsed.path.strip("/").split("/")
        if segments:
            segments[-1] = segments[-1].split("@", 1)[0].removesuffix(".git")
        return agent_dir / "git" / host / Path(*segments)
    candidate = Path(source).expanduser()
    if not candidate.is_absolute():
        candidate = agent_dir / candidate
    return candidate.resolve()


def safe_source_label(source: str) -> str:
    if source.startswith("/") or source.startswith("~"):
        path = Path(source).expanduser()
        try:
            return "~/" + path.resolve().relative_to(Path.home().resolve()).as_posix()
        except ValueError:
            return "local package path (not portable)"
    source = re.sub(r"(https?://)[^/@]+:[^/@]+@", r"\1", source)
    return source.split("?", 1)[0]


def package_slug(name: str) -> str:
    slug = name.lstrip("@").replace("/", "--")
    return re.sub(r"[^A-Za-z0-9._-]", "-", slug)


def copy_tree(source: Path, target: Path) -> None:
    shutil.copytree(source, target, dirs_exist_ok=True, ignore=ignored, symlinks=False)


def copy_configured_path(source: Path, target_root: Path, kind: str) -> None:
    if not source.exists():
        raise ValueError(f"A configured {kind} resource is missing")
    if source.is_dir():
        if (source / "SKILL.md").is_file():
            copy_tree(source, target_root / source.name)
        elif any((source / name).is_file() for name in ("index.ts", "index.js")) and kind == "extensions":
            copy_tree(source, target_root / source.name)
        else:
            copy_tree(source, target_root)
    elif source.is_file():
        if kind == "skills" and source.name == "SKILL.md":
            copy_tree(source.parent, target_root / source.parent.name)
        else:
            target_root.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target_root / source.name)


def package_resource_paths(package_root: Path, manifest: dict, kind: str) -> list[str]:
    pi = manifest.get("pi", {})
    if kind in pi:
        values = pi[kind]
        if isinstance(values, str):
            return [values]
        return values if isinstance(values, list) else []
    conventional = package_root / kind
    return [f"./{kind}"] if conventional.is_dir() else []


def prefix_package_path(slug: str, value: str) -> str:
    exclude = value.startswith("!")
    path = value[1:] if exclude else value
    path = path.removeprefix("./")
    result = f"./vendor/{slug}/{path}"
    return "!" + result if exclude else result


def credential_label(text: str):
    return next((label for label, pattern in SECRET_PATTERNS if pattern.search(text)), None)


def scan_for_credentials(roots: list[Path]) -> None:
    seen = set()
    for root in roots:
        for path in source_files(root):
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            try:
                with path.open("rb") as file:
                    sample = file.read(8192)
                if b"\0" in sample:
                    continue  # shortcut: binary payloads evade text heuristics; add format-specific scanners if needed.
                text = path.read_text(errors="ignore")
            except OSError:
                raise ValueError("Could not inspect a configured resource; no files copied") from None
            label = credential_label(text)
            if label:
                raise ValueError(
                    f"Likely credential ({label}) in {path.name}; value suppressed, no files copied"
                )


def copy_package(source: str, source_root: Path, stage: Path, packages: list[dict]) -> None:
    manifest_path = source_root / "package.json"
    if not manifest_path.is_file():
        raise ValueError(f"Configured package has no package.json: {safe_source_label(source)}")
    manifest = read_json(manifest_path)
    name = manifest.get("name")
    if not name:
        raise ValueError(f"Configured package manifest has no name: {safe_source_label(source)}")
    slug = package_slug(name)
    if any(package["slug"] == slug for package in packages):
        raise ValueError(f"Two configured packages map to the same vendor folder: {slug}")
    target = stage / "vendor" / slug
    copy_tree(source_root, target)
    resources = {}
    for kind in RESOURCE_TYPES:
        resources[kind] = package_resource_paths(source_root, manifest, kind)
    packages.append({
        "name": name,
        "slug": slug,
        "source": safe_source_label(source),
        "repository": manifest.get("repository", ""),
        "resources": resources,
    })


def resource_workspace_dirs(skills_root: Path) -> list[str]:
    workspaces = []
    repo_root = skills_root.parent
    for package_json in skills_root.rglob("package.json"):
        if any(part in EXCLUDED_NAMES for part in package_json.parts):
            continue
        if package_json.parent != skills_root:
            workspaces.append(package_json.parent.relative_to(repo_root).as_posix())
    return workspaces


def write_package_manifest(collection: Path, stage: Path, packages: list[dict]) -> None:
    manifest = read_json(collection / "package.json", default={})
    manifest.setdefault("name", "pi-agent-collection")
    manifest.setdefault("version", "0.1.0")
    manifest["private"] = True
    manifest.setdefault("keywords", ["pi-package"])
    dependencies = {}
    pi = {kind: [f"./{kind}"] for kind in RESOURCE_TYPES}
    workspaces = ["vendor/*"]
    for package in packages:
        dependencies[package["name"]] = f"file:vendor/{package['slug']}"
        for kind, paths in package["resources"].items():
            pi[kind].extend(prefix_package_path(package["slug"], value) for value in paths)
    workspaces.extend(resource_workspace_dirs(stage / "skills"))
    manifest["workspaces"] = sorted(set(workspaces))
    manifest["dependencies"] = dependencies
    manifest["pi"] = pi
    (stage / "package.json").write_text(json.dumps(manifest, indent=2) + "\n")


def listed_files(stage: Path, paths: list[str], predicate) -> set[Path]:
    included, excluded = set(), set()
    for value in paths:
        is_exclusion = value.startswith("!")
        pattern = value[1:] if is_exclusion else value
        pattern = pattern.removeprefix("./")
        matches = list(stage.glob(pattern)) if any(char in pattern for char in "*?[") else [stage / pattern]
        files = set()
        for match in matches:
            if match.is_file() and predicate(match):
                files.add(match)
            elif match.is_dir():
                files.update(path for path in match.rglob("*") if path.is_file() and predicate(path))
        (excluded if is_exclusion else included).update(files)
    return included - excluded


def write_sources(stage: Path, direct_paths: dict, packages: list[dict], safe_settings: dict) -> None:
    pi = read_json(stage / "package.json")["pi"]
    counts = {
        "skills": len(listed_files(stage, pi["skills"], lambda path: path.name == "SKILL.md")),
        "prompts": len(listed_files(stage, pi["prompts"], lambda path: path.suffix == ".md")),
        "extension paths": len(pi["extensions"]),
        "themes": len(listed_files(stage, pi["themes"], lambda path: path.suffix == ".json")),
    }
    lines = [
        "# Resource sources",
        "",
        "Generated by `./update.py` from the configured Pi resources and package manifests.",
        "",
        "## Startup inventory",
        "",
        f"- Skills: {counts['skills']}",
        f"- Prompt files: {counts['prompts']}",
        f"- Extension resource paths: {counts['extension paths']}",
        f"- Theme files: {counts['themes']}",
        "",
        "## Direct resources",
        "",
        "| Type | Source |",
        "|---|---|",
    ]
    for kind, paths in direct_paths.items():
        for source in paths:
            try:
                display = "~/" + source.relative_to(Path.home()).as_posix()
            except ValueError:
                display = "external configured path (source path not embedded)"
            lines.append(f"| `{kind}` | `{display}` |")
    lines += ["", "## Configured Pi packages", "", "| Package | Repository | Pi resources | Installed source |", "|---|---|---|---|"]
    for package in packages:
        repo = package["repository"]
        if isinstance(repo, dict):
            repo = repo.get("url", "")
        repo = safe_source_label(str(repo)) if repo else package["source"]
        resources = ", ".join(kind for kind, paths in package["resources"].items() if paths) or "none declared"
        lines.append(
            f"| `{package['name']}` | `{repo}` | {resources} | `vendor/{package['slug']}` (from `{package['source']}`) |"
        )
    lines += [
        "",
        "## Portable configuration",
        "",
        f"Shared non-secret settings keys: {', '.join(f'`{key}`' for key in safe_settings) or 'none'}.",
        "Credentials and machine-specific provider/MCP files are not copied. Authenticate separately on each machine.",
        "",
    ]
    (stage / "SOURCES.md").write_text("\n".join(lines))


def replace_generated(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_dir():
        shutil.rmtree(target)
    elif target.exists():
        target.unlink()
    os.replace(source, target)


def main() -> int:
    agent_dir = Path(os.environ.get("PI_CODING_AGENT_DIR", Path.home() / ".pi/agent")).expanduser().resolve()
    collection = Path(os.environ.get("PI_AGENT_COLLECTION_DIR", Path(__file__).resolve().parent)).expanduser().resolve()
    try:
        settings = read_json(agent_dir / "settings.json")
        package_entries = settings.get("packages", [])
        package_roots = []
        for entry in package_entries:
            source = entry if isinstance(entry, str) else entry.get("source", "")
            if not source:
                continue
            root = resolve_package(source, agent_dir)
            package_roots.append((source, root))
        direct_paths = {
            kind: list(dict.fromkeys([
                *([agent_dir / kind] if (agent_dir / kind).is_dir() else []),
                *configured_paths(settings, agent_dir, kind),
            ]))
            for kind in RESOURCE_TYPES
        }
        resolved_package_roots = []
        for source, root in package_roots:
            if not root.is_dir():
                raise ValueError(f"Configured package is not installed: {safe_source_label(source)}")
            resolved_package_roots.append((source, root))
        source_roots = [root for paths in direct_paths.values() for root in paths]
        source_roots += [root for _, root in resolved_package_roots]
        targets = [collection / kind for kind in RESOURCE_TYPES] + [collection / "vendor"]
        if any(
            source == target or source in target.parents or target in source.parents
            for source in source_roots
            for target in targets
        ):
            raise ValueError("Refusing to copy between overlapping source and destination folders")
        scan_for_credentials(source_roots)
        safe_settings = {key: settings[key] for key in SAFE_SETTING_KEYS if key in settings}
        if credential_label(json.dumps(safe_settings)):
            raise ValueError("A shared preference looks like a credential; no files copied")
    except (ValueError, TypeError, AttributeError) as error:
        print(str(error), file=sys.stderr)
        return 1

    collection.mkdir(parents=True, exist_ok=True)
    packages = []
    try:
        with tempfile.TemporaryDirectory(prefix=".pi-sync-", dir=collection) as temporary:
            stage = Path(temporary)
            for kind in RESOURCE_TYPES:
                (stage / kind).mkdir()
            (stage / "vendor").mkdir()
            (stage / "config").mkdir()

            # Pi discovers default user resources before explicit settings paths.
            for kind, paths in direct_paths.items():
                default_root = (agent_dir / kind).resolve()
                for source in paths:
                    if source != default_root:
                        copy_configured_path(source, stage / kind, kind)
                if default_root in paths:
                    copy_tree(default_root, stage / kind)

            for source, root in resolved_package_roots:
                copy_package(source, root, stage, packages)

            for package in packages:
                for kind, paths in package["resources"].items():
                    for resource_path in paths:
                        local_path = stage / "vendor" / package["slug"] / resource_path.removeprefix("./")
                        if not local_path.exists() and not any(ch in resource_path for ch in "*?["):
                            raise ValueError(
                                f"Package resource is missing: {package['name']} ({kind})"
                            )

            (stage / "config" / "settings.json").write_text(
                json.dumps(safe_settings, indent=2) + "\n"
            )
            write_package_manifest(collection, stage, packages)
            write_sources(stage, direct_paths, packages, safe_settings)

            for name in (*RESOURCE_TYPES, "vendor"):
                replace_generated(stage / name, collection / name)
            replace_generated(stage / "config" / "settings.json", collection / "config" / "settings.json")
            replace_generated(stage / "package.json", collection / "package.json")
            replace_generated(stage / "SOURCES.md", collection / "SOURCES.md")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(str(error), file=sys.stderr)
        return 1

    print(f"Synced configured Pi resources and {len(packages)} packages; credentials were excluded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
