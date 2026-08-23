"""Basic configuration sanity checks."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config  # noqa: E402


def test_config_has_iteration_cap():
    assert Config.MAX_ITERATIONS > 0


def test_config_has_positive_execution_timeout():
    assert Config.EXEC_TIMEOUT > 0


def test_config_resolves_project_root_to_absolute_path():
    assert os.path.isabs(Config.PROJECT_ROOT)
