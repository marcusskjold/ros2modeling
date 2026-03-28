from pathlib import Path
from unittest.mock import patch
import roserer.verifyta_resolver as vr

def test_is_executable_true(tmp_path):
    file = tmp_path / "verifyta"
    file.write_text("test")

    with patch("os.access", return_value=True):
        assert vr._is_executable(file) is True

def test_is_executable_false(tmp_path):
    file = tmp_path / "verifyta"
    file.write_text("test")

    with patch("os.access", return_value=False):
        assert vr._is_executable(file) is False
