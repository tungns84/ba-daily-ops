"""ba-tools mermaid-render — extract ```mermaid fence → .mmd → invoke mmdc → emit image.

Subcommand:
    mermaid-render --slug <slug> --artifact <diagram.md> [--format svg|png] [--mermaid-cli <path>]

    1. Reads the diagram .md at --artifact.
    2. Extracts the first ```mermaid fenced block → writes .ba-ops/mermaid/<slug>/diagram.mmd
       (FileLock-guarded, T-03-05).
    3. Resolves mmdc via the locked 4-step chain: --mermaid-cli → $MERMAID_CLI → PATH mmdc →
       npx -p @mermaid-js/mermaid-cli mmdc (D-05cmd; CLAUDE.md verified).
    4. Invokes mmdc via subprocess.run list-form (never shell=True, T-03-04).
    5. Emits diagram.<format> under the same slug directory.

Security:
    T-03-01: --slug derived out_dir guarded under root via is_within_root; PATH_TRAVERSAL exit 2.
    T-03-04: fence body reaches mmdc only via .mmd file path in list-form argv — never shell-expanded.
    T-03-05: diagram.mmd write is FileLock(timeout=10) guarded; LOCK_TIMEOUT exit 2 on contention.

Determinism boundary (D-05 / DESIGN §5):
    NO import of openai, anthropic, or any model client.
    This module does only file-I/O + command/hash-provable work.
"""

import os
import re
import shutil
import subprocess
from pathlib import Path

from filelock import FileLock, Timeout

from ba_tools.errors import BaToolsError
from ba_tools.output import ok_json
from ba_tools.repo import is_within_root, resolve_repo_root

# Lock timeout — matches STATE.md convention (D-02 / DESIGN §8, render_cmd.py line 34)
_LOCK_TIMEOUT = 10

# Inline Mermaid fence regex (Pattern 1, RESEARCH.md / 03-PATTERNS.md).
# Matches opening: up to 3 spaces indent, 3+ backticks, info-string "mermaid" (case-sensitive,
#   no suffix like "mermaidjs"), then the body, then a closing fence with same indent+fence length.
# re.MULTILINE so ^ anchors to line-starts; re.DOTALL so body . matches newlines.
# CRLF: normalize \r\n→\n before searching (see extract_mermaid_fence).
_FENCE_RE = re.compile(
    r"^(?P<indent>\s{0,3})(?P<fence>`{3,})[ \t]*mermaid[ \t]*\r?\n"
    r"(?P<body>.*?)"
    r"^(?P=indent)(?P=fence)[ \t]*(?:\r?\n|$)",
    re.MULTILINE | re.DOTALL,
)


def extract_mermaid_fence(md_text: str) -> str:
    """Return the body of the first ```mermaid fenced block in md_text.

    Normalizes CRLF line endings before searching so Windows-authored artifacts
    are handled correctly.

    Args:
        md_text: raw text of the diagram .md artifact.

    Returns:
        The diagram body string (everything between the opening and closing fence lines).

    Raises:
        BaToolsError: code NO_MERMAID_FENCE when no ```mermaid block is found.
    """
    normalized = md_text.replace("\r\n", "\n")
    m = _FENCE_RE.search(normalized)
    if not m:
        raise BaToolsError([{
            "code": "NO_MERMAID_FENCE",
            "message": "No ```mermaid fenced block found in artifact.",
        }])
    return m.group("body")


def resolve_mmdc(cli_flag: str | None) -> list[str]:
    """Return the argv prefix to invoke mmdc, or raise BaToolsError NO_MERMAID_CLI.

    Resolution order (D-05cmd, CLAUDE.md verified):
      1. --mermaid-cli flag value (cli_flag)
      2. $MERMAID_CLI environment variable
      3. PATH mmdc (via shutil.which)
      4. npx -p @mermaid-js/mermaid-cli mmdc (the -p flag is MANDATORY because the
         package name differs from the binary name — see CLAUDE.md + DESIGN §5)

    Args:
        cli_flag: value of the --mermaid-cli argument, or None.

    Returns:
        A non-empty list[str] ready to prepend as argv before ["-i", mmd, "-o", out].

    Raises:
        BaToolsError: code NO_MERMAID_CLI when no resolution step succeeds.
    """
    # Step 1: explicit --mermaid-cli flag
    if cli_flag:
        return [cli_flag]

    # Step 2: $MERMAID_CLI environment variable
    env_cli = os.environ.get("MERMAID_CLI")
    if env_cli:
        return [env_cli]

    # Step 3: PATH mmdc
    path_mmdc = shutil.which("mmdc")
    if path_mmdc:
        return [path_mmdc]

    # Step 4: npx fallback — -p flag REQUIRED (package name != binary name, CLAUDE.md)
    npx = shutil.which("npx")
    if npx:
        return [npx, "-p", "@mermaid-js/mermaid-cli", "mmdc"]

    raise BaToolsError([{
        "code": "NO_MERMAID_CLI",
        "message": (
            "No mmdc CLI found. Tried: --mermaid-cli flag, $MERMAID_CLI env, "
            "PATH mmdc, npx -p @mermaid-js/mermaid-cli mmdc. "
            "Install with: npm install -g @mermaid-js/mermaid-cli"
        ),
    }])


def invoke_mmdc(mmdc_argv: list[str], mmd_path: str, out_path: str) -> dict:
    """Invoke mmdc and return {argv, exit_code} on success.

    Uses list-form subprocess.run (never shell=True) so fence-body metacharacters
    in the .mmd file path cannot be shell-expanded (T-03-04).

    Args:
        mmdc_argv: the resolved mmdc argv prefix from resolve_mmdc().
        mmd_path:  absolute path string to the .mmd input file.
        out_path:  absolute path string to the image output file.

    Returns:
        dict with keys "argv" (list[str]) and "exit_code" (int, always 0 here).

    Raises:
        BaToolsError: code MMDC_FAILED when mmdc exits non-zero.
    """
    argv = mmdc_argv + ["-i", mmd_path, "-o", out_path]
    result = subprocess.run(argv, capture_output=True)  # noqa: S603 (list-form, no shell)
    if result.returncode != 0:
        raise BaToolsError([{
            "code": "MMDC_FAILED",
            "argv": argv,
            "exit_code": result.returncode,
            "stderr": result.stderr.decode("utf-8", errors="replace")[:500],
            "message": f"mmdc exited {result.returncode}.",
        }])
    return {"argv": argv, "exit_code": result.returncode}


def _guarded_write(file_path: Path, content: str, lock_name: str) -> None:
    """Write content to file_path under a FileLock(timeout=10).

    Ensures parent directory exists before writing (T-03-05).

    Raises:
        BaToolsError: code LOCK_TIMEOUT if the lock is not acquired within 10 seconds.
    """
    lock_path = file_path.parent / lock_name
    file_path.parent.mkdir(parents=True, exist_ok=True)
    lock = FileLock(str(lock_path), timeout=_LOCK_TIMEOUT)
    try:
        with lock:
            file_path.write_text(content, encoding="utf-8")
    except Timeout:
        raise BaToolsError([{
            "code": "LOCK_TIMEOUT",
            "lock": str(lock_path),
            "message": (
                f"{lock_name} held for >{_LOCK_TIMEOUT}s; another writer may be active. "
                "No write was performed."
            ),
        }])


def register(subparsers) -> None:
    """Register the mermaid-render subcommand."""
    p = subparsers.add_parser(
        "mermaid-render",
        help=(
            "Extract ```mermaid fence from a diagram .md → write .mmd → invoke mmdc → emit image"
        ),
    )
    p.add_argument(
        "--slug",
        required=True,
        help="Mermaid slug (subdirectory under .ba-ops/mermaid/)",
    )
    p.add_argument(
        "--artifact",
        required=True,
        help="Path to the diagram .md containing the ```mermaid block",
    )
    p.add_argument(
        "--format",
        default="svg",
        choices=["svg", "png"],
        help="Output format (default: svg)",
    )
    p.add_argument(
        "--mermaid-cli",
        default=None,
        dest="mermaid_cli",
        help="Explicit path to mmdc binary (overrides $MERMAID_CLI and PATH)",
    )
    p.set_defaults(func=run)


def run(args) -> None:
    """Execute the mermaid-render command.

    Steps:
      1. Resolve repo root; guard slug-derived out_dir under root (PATH_TRAVERSAL).
      2. Read artifact text from --artifact.
      3. extract_mermaid_fence → raises NO_MERMAID_FENCE if absent.
      4. FileLock-write diagram.mmd (LOCK_TIMEOUT on contention).
      5. resolve_mmdc → raises NO_MERMAID_CLI if none found (no image written).
      6. invoke_mmdc → raises MMDC_FAILED on non-zero exit.
      7. Emit ok_json with slug, mmd, image, argv.

    Critical ordering: resolve_mmdc is called AFTER fence extraction + .mmd write.
    If resolve_mmdc raises NO_MERMAID_CLI, .mmd may already be on disk but NO image
    is written — this is the correct DESIGN §11 / criterion-3 behaviour (hard-fail,
    no synthetic image).

    Args:
        args: parsed argparse.Namespace with repo_root, slug, artifact, format, mermaid_cli.
    """
    root = resolve_repo_root(getattr(args, "repo_root", None))
    slug = args.slug

    # T-03-01: slug-derived output directory must resolve within repo root
    out_dir = (root / ".ba-ops" / "mermaid" / slug).resolve()
    if not is_within_root(out_dir, root):
        raise BaToolsError([{
            "code": "PATH_TRAVERSAL",
            "slug": slug,
            "message": (
                f"--slug '{slug}' resolves outside repo root. "
                "Slugs must not contain path traversal sequences."
            ),
        }])

    # Read artifact
    artifact_path = Path(args.artifact)
    if not artifact_path.is_absolute():
        artifact_path = (root / artifact_path).resolve()
    if not artifact_path.exists():
        raise BaToolsError([{
            "code": "FILE_NOT_FOUND",
            "path": str(artifact_path),
            "message": f"--artifact '{args.artifact}' not found: {artifact_path}",
        }])
    md_text = artifact_path.read_text(encoding="utf-8")

    # Extract fence (raises NO_MERMAID_FENCE if absent)
    fence_body = extract_mermaid_fence(md_text)

    # Write diagram.mmd (FileLock-guarded; T-03-05)
    mmd_path = out_dir / "diagram.mmd"
    _guarded_write(mmd_path, fence_body, "diagram.mmd.lock")

    # Resolve mmdc (raises NO_MERMAID_CLI if none found; no image written on failure)
    mmdc_argv = resolve_mmdc(getattr(args, "mermaid_cli", None))

    # Determine output image path
    fmt = getattr(args, "format", "svg")
    image_path = out_dir / f"diagram.{fmt}"

    # Invoke mmdc (raises MMDC_FAILED on non-zero exit; T-03-04 list-form)
    invocation = invoke_mmdc(mmdc_argv, str(mmd_path), str(image_path))

    ok_json(
        slug=slug,
        mmd=str(mmd_path),
        image=str(image_path),
        argv=invocation["argv"],
    )
