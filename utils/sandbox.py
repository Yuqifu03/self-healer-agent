"""Path-level sandbox security helpers.

Every file-system tool in this project resolves and validates paths through
this module so the agent can only ever read or write inside the configured
sandbox root. The checks defend against the common escape vectors:

* absolute paths (``/etc/passwd``)
* parent-directory traversal (``../../``)
* sibling-directory prefix spoofing (``sandbox_evil`` when root is ``sandbox``)
* symlinks that point outside the sandbox

The canonical root is resolved once with ``realpath`` so ``~``, symlinked
workspaces, and trailing slashes cannot bypass the boundary check.
"""

import os


def resolve_sandbox_root(project_root: str) -> str:
    """Resolve the canonical, symlink-free absolute path of the sandbox root."""
    if not project_root:
        raise PermissionError("Sandbox root is not configured.")
    return os.path.realpath(os.path.abspath(os.path.expanduser(project_root)))


def check_path(sandbox_root: str, relative_path: str) -> str:
    """Resolve ``relative_path`` inside ``sandbox_root`` and enforce containment.

    Args:
        sandbox_root: Canonical absolute path of the sandbox (see
            :func:`resolve_sandbox_root`).
        relative_path: Path as supplied by the agent, relative to the sandbox
            root. Absolute paths are treated as escape attempts.

    Returns:
        The canonical absolute path inside the sandbox.

    Raises:
        PermissionError: If the resolved path escapes the sandbox root.
    """
    if relative_path is None or relative_path == "":
        raise PermissionError("Empty or missing path is not allowed.")

    joined_path = os.path.join(sandbox_root, relative_path)
    resolved_path = os.path.realpath(os.path.abspath(joined_path))

    if resolved_path != sandbox_root and not resolved_path.startswith(
        sandbox_root + os.sep
    ):
        raise PermissionError(
            f"Access denied: '{relative_path}' resolves outside the "
            f"allowed sandbox: {sandbox_root}"
        )

    return resolved_path
