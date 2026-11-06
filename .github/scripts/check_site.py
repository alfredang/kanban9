#!/usr/bin/env python3
"""Check the v2 page's security policy and project rules. CI runs this on every push.

    python .github/scripts/check_site.py          check, and exit 1 on any problem
    python .github/scripts/check_site.py --write  update the policy's hashes, then check

v2's Content-Security-Policy allows its inline <style> and <script> by SHA-256 hash.
Any edit to either changes the hash, and a stale hash stops the page loading, so run
this with --write after editing them.
"""
import base64
import hashlib
import pathlib
import re
import sys

PAGE = pathlib.Path(__file__).resolve().parents[2] / "v2" / "index.html"

REQUIRED_DIRECTIVES = [
    "default-src 'none'",
    "connect-src https://formsubmit.co",
    "form-action 'none'",
    "base-uri 'none'",
    "require-trusted-types-for 'script'",
]

# (pattern, reason). Project rules and sinks the security policy depends on avoiding.
FORBIDDEN = [
    (r"\blocalStorage\b|\bsessionStorage\b|\bindexedDB\b|document\.cookie", "storage is not allowed"),
    (r"\balert\(|\bconfirm\(|\bprompt\(", "browser dialogs are not allowed"),
    (r"!important", "!important is not allowed"),
    (r"\beval\(|new Function\(", "dynamic code is not allowed"),
    (r"\son[a-z]+\s*=\s*[\"']", "inline event handlers are blocked by the policy"),
    (r"<[a-z][^<>]*\sstyle\s*=", "style attributes are blocked by the policy"),
    (r"\.innerHTML\s*=(?!\s*htmlPolicy)", "use setHtml(), the only allowed HTML sink"),
]

ALLOWED_URLS = ("https://formsubmit.co", "http://www.w3.org/2000/svg")


HIDDEN_CHARS = "[" + "".join(chr(code) for code in [
    *range(0x200B, 0x2010), 0x2028, 0x2029, *range(0x202A, 0x202F), 0x2060, *range(0x2066, 0x206A), 0xFEFF,
]) + "]"


def digest(text):
    raw = hashlib.sha256(text.encode("utf-8")).digest()
    return "sha256-" + base64.b64encode(raw).decode("ascii")


def only_block(html, tag):
    blocks = re.findall(rf"<{tag}>(.*?)</{tag}>", html, flags=re.DOTALL)
    if len(blocks) != 1:
        sys.exit(f"Expected exactly one <{tag}> block, found {len(blocks)}")
    if blocks[0].lstrip().startswith("<") or "-->" in blocks[0]:
        sys.exit(f"The <{tag}> match starts in a comment: don't name the tag in comments")
    return blocks[0]


def main():
    write = "--write" in sys.argv[1:]
    html = PAGE.read_bytes().decode("utf-8")
    if "\r" in html:
        sys.exit("v2/index.html must use LF line endings")
    # Raw invisible or direction characters can hide code from reviewers and break scripts.
    hidden = re.search(HIDDEN_CHARS, html)
    if hidden:
        sys.exit(f"v2/index.html has raw U+{ord(hidden.group(0)):04X}: use an escape instead")

    hashes = {
        "style-src": digest(only_block(html, "style")),
        "script-src": digest(only_block(html, "script")),
    }

    if write:
        for directive, value in hashes.items():
            html = re.sub(rf"{directive} 'sha256-[^']*'", f"{directive} '{value}'", html, count=1)
        PAGE.write_bytes(html.encode("utf-8"))

    problems = []
    for directive, value in hashes.items():
        if f"{directive} '{value}'" not in html:
            problems.append(f"{directive} hash is stale: run with --write")
    for directive in REQUIRED_DIRECTIVES:
        if directive not in html:
            problems.append(f"policy is missing: {directive}")

    # The hashed blocks and the markup are checked, with this page's own comments removed.
    code = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
    for pattern, reason in FORBIDDEN:
        for match in re.finditer(pattern, code):
            line = code.count("\n", 0, match.start()) + 1
            problems.append(f"{reason}: {match.group(0)!r} near stripped line {line}")
    for url in re.findall(r"https?://[^\s\"'`<>)]+", code):
        if not url.startswith(ALLOWED_URLS):
            problems.append(f"external URL is not allowed: {url}")

    if problems:
        print("\n".join(problems))
        sys.exit(1)
    print("v2/index.html passed: policy hashes current, project rules met")


if __name__ == "__main__":
    main()
