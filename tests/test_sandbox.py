"""Security tests for the path-level sandbox containment helpers."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.sandbox import check_path, resolve_sandbox_root  # noqa: E402


@pytest.fixture
def sandbox_root(tmp_path):
    root = tmp_path / "sandbox"
    root.mkdir()
    return str(root)


def test_resolves_sandbox_root_to_canonical_path(tmp_path):
    root = resolve_sandbox_root(str(tmp_path / "sandbox"))
    assert root == os.path.realpath(os.path.abspath(str(tmp_path / "sandbox")))


def test_rejects_empty_root():
    with pytest.raises(PermissionError):
        resolve_sandbox_root("")


def test_allows_files_inside_sandbox(sandbox_root):
    resolved = check_path(sandbox_root, "example/main.py")
    assert resolved == os.path.join(sandbox_root, "example", "main.py")


def test_allows_sandbox_root_itself(sandbox_root):
    resolved = check_path(sandbox_root, ".")
    assert resolved == sandbox_root


def test_blocks_absolute_path_escape(sandbox_root):
    with pytest.raises(PermissionError):
        check_path(sandbox_root, "/etc/passwd")


def test_blocks_parent_directory_traversal(sandbox_root):
    with pytest.raises(PermissionError):
        check_path(sandbox_root, "../secret.txt")


def test_blocks_nested_parent_traversal(sandbox_root):
    os.makedirs(os.path.join(sandbox_root, "a", "b"))
    with pytest.raises(PermissionError):
        check_path(sandbox_root, "a/../../secret.txt")


def test_blocks_sibling_prefix_spoofing(sandbox_root):
    sibling = os.path.join(os.path.dirname(sandbox_root), "sandbox_evil")
    with pytest.raises(PermissionError):
        check_path(sandbox_root, os.path.join("../sandbox_evil", "file.py"))


def test_blocks_symlink_escape(sandbox_root, tmp_path):
    outside = tmp_path / "outside_secret.txt"
    outside.write_text("secret")

    link = os.path.join(sandbox_root, "escape_link")
    os.symlink(str(outside), link)

    with pytest.raises(PermissionError):
        check_path(sandbox_root, "escape_link")


def test_rejects_empty_path(sandbox_root):
    with pytest.raises(PermissionError):
        check_path(sandbox_root, "")
