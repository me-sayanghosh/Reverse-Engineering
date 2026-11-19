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
    r"""import\.meta\.env\.([A-Za-z0-9_]+)""",
    r"""import\.meta\.env\[['"]([A-Za-z0-9_]+)['"]\]""",
    r"""os\.environ\[['"]([A-Za-z0-9_]+)['"]\]""",
    r"""os\.environ\.get\(['"]([A-Za-z0-9_]+)['"]""",
    r"""os\.getenv\(['"]([A-Za-z0-9_]+)['"]""",
    r"""System\.getenv\(['"]([A-Za-z0-9_]+)['"]""",
    r"""os\.Getenv\(['"]([A-Za-z0-9_]+)['"]""",
    r"""os\.LookupEnv\(['"]([A-Za-z0-9_]+)['"]""",
    r"""std::env::var\(['"]([A-Za-z0-9_]+)['"]""",
    r"""std::env::var_os\(['"]([A-Za-z0-9_]+)['"]""",
    r"""ENV\[['"]([A-Za-z0-9_]+)['"]\]""",
    r"""ENV\.fetch\(['"]([A-Za-z0-9_]+)['"]""",
    r"""Environment\.GetEnvironmentVariable\(['"]([A-Za-z0-9_]+)['"]""",
    r"""getenv\(['"]([A-Za-z0-9_]+)['"]""",
    r"""\$_ENV\['([A-Za-z0-9_]+)'\]""",
    r"""\$_ENV\["([A-Za-z0-9_]+)"\]""",
    r"""System\.getProperty\(['"]([A-Za-z0-9_]+)['"]""",
    r"""os\.environ\.setdefault\(['"]([A-Za-z0-9_]+)['"]""",
    r"""os\.getenvb\(['"]([A-Za-z0-9_]+)['"]""",
    r"""c\.env\.([A-Za-z0-9_]+)""",
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
        ext = file_path.suffix.lower()

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
                                    env_vars[var_name] = {
                                        "name": var_name,
                                        "category": categorize_env_var(var_name),
                                        "occurrences": [],
                                    }
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
                                env_vars[var_name] = {
                                    "name": var_name,
                                    "category": categorize_env_var(var_name),
                                    "occurrences": [],
                                }
                            citation = f"{rel}:{idx}"
                            if citation not in env_vars[var_name]["occurrences"]:
                                env_vars[var_name]["occurrences"].append(citation)
        except Exception:
            pass

    return list(env_vars.values())


def categorize_env_var(name: str) -> str:
    """Categorize an environment variable name into db, auth, third-party, feature-flag, infra, or other."""
    u = name.upper()

    # Database
    if any(k in u for k in ["DB", "DATABASE", "POSTGRES", "MYSQL", "MONGO", "REDIS", "SQLITE"]):
        return "db"

    # Auth
    if any(k in u for k in ["AUTH", "JWT", "TOKEN", "SECRET", "PASSWORD", "PASSWD", "SESSION", "OAUTH", "CREDENTIAL"]):
        return "auth"

    # Third-party services
    if any(
        k in u
        for k in [
            "STRIPE",
            "AWS",
            "S3",
            "SLACK",
            "GITHUB",
            "SENDGRID",
            "TWILIO",
            "MAIL",
            "OPENAI",
            "SENTRY",
            "DATADOG",
        ]
    ):
        return "third-party"

    # Feature flags
    if any(k in u for k in ["ENABLE", "DISABLE", "FEATURE", "FLAG", "TOGGLE"]) or u.startswith("IS_"):
        return "feature-flag"

    # Infrastructure / networking
    if any(k in u for k in ["PORT", "HOST", "URL", "DOMAIN", "REGION", "ENV", "STAGE", "CORS", "LOG", "TIMEOUT"]):
        return "infra"

    return "other"


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
        ext = file_path.suffix.lower()

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

        elif ext == ".toml" and ("config" in name or "setting" in name or name in ("wrangler.toml", "netlify.toml")):
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for idx, line in enumerate(f, start=1):
                        m_toml = re.match(r"^([a-zA-Z0-9_\-]+)\s*=", line.strip())
                        if m_toml and not line.strip().startswith("#"):
                            config_keys.append({"key": m_toml.group(1), "file": f"{rel}:{idx}"})
            except Exception:
                pass

    return config_keys


SECRET_PATTERNS = [
    (r"\b(AKIA[0-9A-Z]{16})\b", "AWS Access Key ID", 4),
    (r"\b(gh[pousr]_[a-zA-Z0-9_]{36,})\b", "GitHub Personal Access Token", 4),
    (r"\b(github_pat_[a-zA-Z0-9_]{60,})\b", "GitHub Fine-Grained PAT", 11),
    (r"\b(sk-(?:proj-|live-|test-)?[a-zA-Z0-9_-]{32,})\b", "OpenAI / AI Secret Key", 5),
    (r"\b(hf_[a-zA-Z0-9]{34,})\b", "Hugging Face Token", 5),
    (r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----", "Private Key Header", 11),
    (r"\b(xox[baprs]-[0-9a-zA-Z]{10,48})\b", "Slack Token", 5),
    (r"\b(sk_(?:live|test)_[0-9a-zA-Z]{24,})\b", "Stripe Secret Key", 8),
    (r"\b(glpat-[a-zA-Z0-9_\-]{20,})\b", "GitLab Personal Access Token", 6),
    (r"\b(npm_[a-zA-Z0-9]{32,})\b", "npm Access Token", 4),
    (r"\b(pypi-AgEIcHlwaS5vcmc[a-zA-Z0-9_\-]{50,})\b", "PyPI API Token", 9),
    (
        r"""(?i)(?:postgres|postgresql|mysql|mongodb|redis)://[a-zA-Z0-9_.-]+:([a-zA-Z0-9_\-.~!@#$%^&*+=]{4,})@""",
        "Database Connection URI Password",
        2,
    ),
    (
        r"""(?i)(?:api_key|apikey|secret|token|password|auth_token)[a-z0-9_]*\s*[:=]\s*['"]?([a-zA-Z0-9_\-.~!@#$%^&*+=]{12,})['"]?""",
        "Committed Secret / Token",
        4,
    ),
]


def mask_secret(secret_str: str, prefix_len: int = 4) -> str:
    """Return strictly redacted/masked string (e.g. AKIA****). Never leaks middle or suffix bytes."""
    if not secret_str:
        return "****"
    if len(secret_str) <= 2:
        prefix = ""
    elif len(secret_str) <= 4:
        prefix = secret_str[:1]
    else:
        # Cap prefix to at most prefix_len or one-third of secret length
        actual_len = min(prefix_len, max(1, len(secret_str) // 3))
        prefix = secret_str[:actual_len]
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
                                for ph in [
                                    "your_",
                                    "insert_",
                                    "<token>",
                                    "<secret>",
                                    "replace_me",
                                    "changeme",
                                    "dummy",
                                    "placeholder",
                                    "sample_key",
                                    "sample_token",
                                    "test_secret",
                                ]
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


def redact_all_secrets_filter(data):
    """Recursively traverse data structures and redact any string matching secret patterns."""
    if isinstance(data, str):
        cleaned = data
        for pat, _, pfx_len in SECRET_PATTERNS:
            # Replace any unmasked secrets with masked representation
            def repl(match):
                if match.groups() and match.group(1):
                    raw = match.group(1)
                    full = match.group(0)
                    start, end = match.span(1)
                    m_start, _ = match.span(0)
                    rel_start = start - m_start
                    rel_end = end - m_start
                    return full[:rel_start] + mask_secret(raw, pfx_len) + full[rel_end:]
                return mask_secret(match.group(0), pfx_len)

            cleaned = re.sub(pat, repl, cleaned)
        return cleaned
    elif isinstance(data, dict):
        return {redact_all_secrets_filter(k): redact_all_secrets_filter(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [redact_all_secrets_filter(item) for item in data]
    return data


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

    # Final guarantee redaction pass
    sanitized_data = redact_all_secrets_filter(data)

    if args.json:
        _common.output_json(sanitized_data)
    else:
        print(f"Secret and Env Scanner for: {root_path}")
        print(f"Environment variables discovered: {len(sanitized_data['env_vars'])}")
        for ev in sanitized_data["env_vars"][:10]:
            print(f"  - {ev['name']} (cited in {len(ev['occurrences'])} locations)")
        print(f"\nConfiguration keys discovered: {len(sanitized_data['config_keys'])}")
        for ck in sanitized_data["config_keys"][:10]:
            print(f"  - {ck['key']} ({ck['file']})")
        if sanitized_data["secret_findings"]:
            print(f"\nSECURITY ALERT: Potential secrets detected ({len(sanitized_data['secret_findings'])}):")
            for sf in sanitized_data["secret_findings"]:
                print(f"  [{sf['type']}] {sf['file']} -> {sf['masked_sample']}")
        else:
            print("\nPotential secrets: None detected")


if __name__ == "__main__":
    main()
