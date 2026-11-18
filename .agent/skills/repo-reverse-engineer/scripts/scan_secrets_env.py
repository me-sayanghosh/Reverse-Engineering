#!/usr/bin/env python3
"""Scan environment variables, configuration keys, and detect potential secret leaks with strict redaction."""

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import _common


import re

ENV_PATTERNS = [
    r"""process\.env\.([A-Za-z0-9_]+)""",
    r"""process\.env\[['"]([A-Za-z0-9_]+)['"]\]""",
    r"""os\.environ\[['"]([A-Za-z0-9_]+)['"]\]""",
    r"""os\.environ\.get\(['"]([A-Za-z0-9_]+)['"]""",
    r"""os\.getenv\(['"]([A-Za-z0-9_]+)['"]""",
    r"""System\.getenv\(['"]([A-Za-z0-9_]+)['"]""",
    r"""os\.Getenv\(['"]([A-Za-z0-9_]+)['"]""",
    r"""std::env::var\(['"]([A-Za-z0-9_]+)['"]""",
    r"""ENV\[['"]([A-Za-z0-9_]+)['"]\]""",
]


def find_env_vars(root_path: Path):
    """Scan source code and .env.example files for environment variable names only (values strictly excluded)."""
    root_path = root_path.resolve()
    env_vars = {}

    for file_path in _common.walk_repo(root_path):
        if _common.is_binary(file_path):
            continue
        rel = str(file_path.relative_to(root_path))
        name = file_path.name.lower()

        # Check .env.example / sample templates
        if name in (".env.example", ".env.sample", ".env.template", ".env.dist"):
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for idx, line in enumerate(f, start=1):
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            var_name = line.split("=", 1)[0].strip()
                            if var_name:
                                if var_name not in env_vars:
                                    env_vars[var_name] = {"name": var_name, "occurrences": []}
                                env_vars[var_name]["occurrences"].append(f"{rel}:{idx}")
            except Exception:
                pass

        # Check source code invocations
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for idx, line in enumerate(f, start=1):
                    for pat in ENV_PATTERNS:
                        for m in re.finditer(pat, line):
                            var_name = m.group(1)
                            # Ignore common non-env props like process.env.NODE_ENV handled cleanly
                            if var_name not in env_vars:
                                env_vars[var_name] = {"name": var_name, "occurrences": []}
                            citation = f"{rel}:{idx}"
                            if citation not in env_vars[var_name]["occurrences"]:
                                env_vars[var_name]["occurrences"].append(citation)
        except Exception:
            pass

    return list(env_vars.values())


def find_config_keys(root_path: Path):
    """List configuration keys from config files and settings.py constants (names only)."""
    root_path = root_path.resolve()
    config_keys = []
    import json

    for file_path in _common.walk_repo(root_path):
        if _common.is_binary(file_path):
            continue
        rel = str(file_path.relative_to(root_path))
        name = file_path.name.lower()

        # 1. settings.py constants
        if name == "settings.py":
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for idx, line in enumerate(f, start=1):
                        m_const = re.match(r"^([A-Z0-9_]{3,})\s*=", line.strip())
                        if m_const:
                            config_keys.append({"key": m_const.group(1), "file": f"{rel}:{idx}"})
            except Exception:
                pass

        # 2. application.properties / application.yml / config.json / config.yaml
        elif name in ("application.properties", "config.properties"):
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for idx, line in enumerate(f, start=1):
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            prop_key = line.split("=", 1)[0].strip()
                            config_keys.append({"key": prop_key, "file": f"{rel}:{idx}"})
            except Exception:
                pass

        elif name in ("config.json", "default.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    doc = json.load(f)
                    if isinstance(doc, dict):
                        for k in doc.keys():
                            config_keys.append({"key": k, "file": rel})
            except Exception:
                pass

        elif name in ("application.yml", "application.yaml", "config.yml", "config.yaml"):
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for idx, line in enumerate(f, start=1):
                        m_yaml = re.match(r"^\s*([a-zA-Z0-9_.-]+):\s*", line)
                        if m_yaml and not line.strip().startswith("#"):
                            config_keys.append({"key": m_yaml.group(1), "file": f"{rel}:{idx}"})
            except Exception:
                pass

    return config_keys


SECRET_PATTERNS = [
    (r"\b(AKIA[0-9A-Z]{16})\b", "AWS Access Key ID", 4),
    (r"\b(gh[pousr]_[a-zA-Z0-9_]{36,})\b", "GitHub Personal Access Token", 4),
    (r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----", "Private Key Header", 11),
    (r"\b(xox[baprs]-[0-9a-zA-Z]{10,48})\b", "Slack Token", 5),
    (r"\b(sk_live_[0-9a-zA-Z]{24,})\b", "Stripe Live Secret Key", 8),
    (
        r"""(?i)(?:api_key|apikey|secret|password|auth_token)\s*[:=]\s*['"]([a-zA-Z0-9_\-.~!@#$%^&*+=]{12,})['"]""",
        "Committed Secret / Token",
        4,
    ),
]


def mask_secret(secret_str: str, prefix_len: int = 4) -> str:
    """Return strictly redacted/masked string (e.g. AKIA****). Never leaks middle or suffix bytes."""
    prefix = secret_str[:prefix_len] if len(secret_str) >= prefix_len else secret_str[:2]
    return f"{prefix}****"


def detect_potential_secrets(root_path: Path):
    """Scan committed files for hardcoded secrets, returning findings with masked samples only."""
    root_path = root_path.resolve()
    findings = []

    for file_path in _common.walk_repo(root_path):
        if _common.is_binary(file_path):
            continue
        rel = str(file_path.relative_to(root_path))
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for idx, line in enumerate(f, start=1):
                    for pat, desc, pfx_len in SECRET_PATTERNS:
                        m = re.search(pat, line)
                        if m:
                            raw_val = m.group(1) if m.groups() else m.group(0)
                            # Ignore obvious placeholder templates
                            if any(
                                ph in raw_val.lower()
                                for ph in ["your_", "insert_", "<token>", "<secret>", "replace_me"]
                            ):
                                continue
                            masked = mask_secret(raw_val, pfx_len)
                            findings.append(
                                {
                                    "file": f"{rel}:{idx}",
                                    "type": desc,
                                    "masked_sample": masked,
                                }
                            )
                            break
        except Exception:
            pass

    return findings


def parse_args():
    parser = argparse.ArgumentParser(
        description="Scan repository environment variable usage, config keys, and audit potential secret leaks."
    )
    parser.add_argument("root", help="Path to repository root directory")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    return parser.parse_args()


def main():
    args = parse_args()
    root_path = Path(args.root).resolve()
    if not root_path.exists():
        _common.die(f"Repository root does not exist: {root_path}")

    env_vars = find_env_vars(root_path)
    config_keys = find_config_keys(root_path)
    secret_findings = detect_potential_secrets(root_path)

    data = {
        "root": str(root_path),
        "env_vars": env_vars,
        "config_keys": config_keys,
        "secret_findings": secret_findings,
    }

    if args.json:
        _common.output_json(data)
    else:
        print(f"Secret and Env Scanner for: {root_path}")


if __name__ == "__main__":
    main()
