import re

DANGEROUS_PATTERNS = [
    r"\brm\b",
    r"\bdel\b",
    r"\berase\b",
    r"\bformat\b",
    r"\bshutdown\b",
    r"\brestart-computer\b",
    r"\bremove-item\b.*-recurse",
    r"\breg\b\s+(add|delete)",
    r"\bnet\s+user\b",
    r">\s*[a-zA-Z]:\\",
    r"\bdiskpart\b",
    r"\bmkfs\b",
]

_COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in DANGEROUS_PATTERNS]


def is_potentially_dangerous(command: str) -> bool:
    return any(pattern.search(command) for pattern in _COMPILED_PATTERNS)