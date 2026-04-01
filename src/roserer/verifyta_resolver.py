import sys
import os
from pathlib import Path
import shutil

def _is_executable(path: Path) -> bool:
    return (
        path.is_file()
        and os.access(str(path), os.X_OK)
    )

def _resolve_candidate(path: Path) -> Path | None:
    if path.is_dir():
        exe = path / ("verifyta.exe" if sys.platform == "win32" or sys.platform == "linux" else "verifyta")
        
        return exe if _is_executable(exe) else None
    return path if _is_executable(path) else None

def _default_verifyta_paths() -> list[Path]:
    paths: list[Path] = []

    if sys.platform == "darwin":
        paths += [
            Path("/Applications/UPPAAL.app/Contents/Resources/uppaal/bin/verifyta"),
            Path("/Applications/UPPAAL-5.0.0.app/Contents/Resources/uppaal/bin/verifyta"),
        ]

    elif sys.platform == "linux":
        paths += [
            # Not tested
        ]

    elif sys.platform == "win32":
        paths += [
            Path(r"C:\Program Files\UPPAAL\bin\verifyta.exe"),
            Path(r"C:\Program Files\UPPAAL\uppaal\bin\verifyta.exe"),
            Path(r"C:\Program Files (x86)\UPPAAL\uppaal-5.0.0-win64\bin\verifyta.exe")
        ]

    return paths


def find_verifyta(uppaal_bin_path: str | os.PathLike | None = None) -> str:

    # 1. Explicit argument
    if uppaal_bin_path:
        p = Path(uppaal_bin_path).expanduser()
        resolved = _resolve_candidate(p)
        if resolved:
            return str(resolved)
        raise FileNotFoundError(f"Invalid verifyta path: {p}")

    # 2. Local ./verifyta
    cwd = Path.cwd()
    for name in ("verifyta", "verifyta.exe"):
        resolved = _resolve_candidate(cwd / name)
        if resolved:
            return str(resolved)

    # 3. Environment variable
    env_path = os.getenv("VERIFYTA_PATH")
    if env_path:
        resolved = _resolve_candidate(Path(env_path).expanduser())
        if resolved:
            if not resolved.is_absolute():
                resolved = Path.cwd() / resolved
            return str(resolved)
        raise FileNotFoundError(
            f"VERIFYTA_PATH is set but invalid: {env_path}"
        )

    # 4. PATH lookup
    which = shutil.which("verifyta")
    if which:
        return which

    # 5. Platform-specific defaults
    for path in _default_verifyta_paths():
        resolved = _resolve_candidate(path)
        if resolved:
            return str(resolved)

    raise FileNotFoundError(
        "Could not find verifyta executable.\n"
        "Set VERIFYTA_PATH, add verifyta to PATH, "
        "or provide an explicit path."
    )
