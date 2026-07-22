from __future__ import annotations

import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
TEXT_EXTENSIONS = {
    ".md", ".json", ".toml", ".yml", ".yaml", ".cff", ".txt", ".csv", ".py", ".ps1", ".sh", ".svg"
}
EXCLUDED_DIRECTORIES = {".git", ".venv", "__pycache__", ".pytest_cache", ".matplotlib"}
FORBIDDEN_FILES = {".env", "credentials.json", "secrets.json"}
SENSITIVE_PATTERNS = {
    "windows_absolute_path": re.compile(r"[A-Za-z]:\\(?:Users|Claude AI|Documents|Desktop|Downloads)\\", re.IGNORECASE),
    "unix_home_path": re.compile(r"/(?:home|Users)/[^/\s]+/"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "api_secret_assignment": re.compile(r"(?:api[_-]?secret|secret[_-]?key|private[_-]?key)\s*[:=]\s*['\"][^'\"]+", re.IGNORECASE),
}


def iter_public_files():
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_DIRECTORIES for part in path.parts):
            continue
        yield path


def main() -> int:
    problems: list[str] = []

    for path in iter_public_files():
        relative = path.relative_to(ROOT).as_posix()
        if path.name in FORBIDDEN_FILES or path.suffix.lower() in {".pem", ".key"}:
            problems.append(f"Forbidden sensitive file: {relative}")
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        if path.stat().st_size > 15_000_000:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in SENSITIVE_PATTERNS.items():
            if pattern.search(text):
                problems.append(f"{label}: {relative}")

    required = [
        "REPLICATION_MANIFEST.json",
        "REPLICATION_CHECKSUMS.sha256",
        "data/raw/sol_usdt_4h.csv",
        "data/raw/btc_usdt_4h.csv",
        "data/processed/model_features.csv",
        "data/processed/fold_assignments.csv",
        "outputs/research_report.md",
        "outputs/stage_2_oos_predictions.csv",
        "outputs/figures/figure_01_market_signal_anatomy.svg",
    ]
    for relative in required:
        if not (ROOT / relative).exists():
            problems.append(f"Required public replication artifact missing: {relative}")

    report = {
        "status": "FAIL" if problems else "PASS",
        "problems": problems,
        "checked_root": ".",
    }
    (ROOT / "PUBLIC_RELEASE_AUDIT.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
