"""
Standalone updater script for SEBI RA Automation.

This script is built as a separate update updater binary alongside the main app.
When the main app downloads an update ZIP, it writes an instruction file
and launches this updater.  The updater then:

1. Waits for the main app process to exit.
2. Extracts the ZIP into the app's install directory, replacing
   ``_internal/`` and the main binary while preserving user data
   (config.json, data/, sessions, etc.).
3. Re-launches the main app.
4. Cleans up the temp files and exits.

The instruction file is a simple JSON written by the main app::

    {
        "zip_path": "/tmp/sebi_ra_update_xxxxx/update.zip",
        "app_exe": "C:/Users/.../SEBI_RA_Automation.exe",
        "app_pid": 12345
    }
"""

import json
import os
import shutil
import stat
import subprocess
import sys
import time
import zipfile
from pathlib import Path

INSTRUCTION_FILE = "update_instruction.json"
MAX_WAIT_SECONDS = 60
POLL_INTERVAL = 0.5


def _pid_exists(pid: int) -> bool:
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.windll.kernel32
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        STILL_ACTIVE = 259

        kernel32.OpenProcess.restype = ctypes.c_void_p
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.GetExitCodeProcess.restype = wintypes.BOOL
        kernel32.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD)]
        kernel32.CloseHandle.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [ctypes.c_void_p]

        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return False
        exit_code = wintypes.DWORD()
        result = kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
        kernel32.CloseHandle(handle)
        if not result:
            return False
        return exit_code.value == STILL_ACTIVE
    else:
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except OSError:
            return True


def _wait_for_process(pid: int, timeout: float = MAX_WAIT_SECONDS) -> bool:
    waited = 0.0
    while waited < timeout:
        if not _pid_exists(pid):
            return True
        time.sleep(POLL_INTERVAL)
        waited += POLL_INTERVAL
    return False


def _strip_top_dir(zip_path: str) -> str | None:
    """If every entry in the zip is under a single top-level directory, return its name; else None."""
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            if not names:
                return None
            prefixes = set()
            for n in names:
                if "/" in n:
                    prefixes.add(n.split("/", 1)[0])
            if len(prefixes) == 1:
                candidate = prefixes.pop()
                if all(n.startswith(candidate + "/") or n == candidate + "/" for n in names):
                    return candidate
    except Exception:
        pass
    return None


def _extract_update(zip_path: str, install_dir: Path) -> bool:
    try:
        top_dir = _strip_top_dir(zip_path)
        with zipfile.ZipFile(zip_path, "r") as zf:
            if top_dir is not None:
                for member in zf.namelist():
                    if member == top_dir + "/":
                        os.makedirs(install_dir / member, exist_ok=True)
                        continue
                    if not member.startswith(top_dir + "/"):
                        continue
                    relative = member[len(top_dir) + 1:]
                    if not relative:
                        continue
                    target = install_dir / relative
                    if member.endswith("/"):
                        os.makedirs(target, exist_ok=True)
                    else:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(member) as src, open(target, "wb") as dst:
                            shutil.copyfileobj(src, dst)
            else:
                zf.extractall(install_dir)

        _make_executables(install_dir)
        return True
    except Exception as e:
        print(f"UPDATE ERROR: Failed to extract update: {e}", file=sys.stderr)
        return False


def _make_executables(install_dir: Path):
    if os.name == "nt":
        return
    exe_name = "SEBI_RA_Automation"
    for candidate in [install_dir / exe_name, install_dir / "updater"]:
        try:
            if candidate.exists():
                candidate.chmod(candidate.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        except OSError:
            pass


def _relaunch_app(app_path: Path):
    if os.name != "nt":
        try:
            app_path.chmod(app_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        except OSError:
            pass

    if sys.platform == "darwin":
        bundle_dir = app_path
        for _ in range(10):
            if bundle_dir.suffix == ".app":
                subprocess.Popen(["open", str(bundle_dir)])
                return
            parent = bundle_dir.parent
            if parent == bundle_dir:
                break
            bundle_dir = parent

    subprocess.Popen([str(app_path)], cwd=str(app_path.parent))


def _cleanup(zip_path: str, inst_path: Path):
    try:
        zip_file = Path(zip_path)
        if zip_file.exists():
            parent_dir = zip_file.parent
            shutil.rmtree(parent_dir, ignore_errors=True)
    except Exception:
        pass

    try:
        if inst_path.exists():
            inst_path.unlink()
    except Exception:
        pass


def _prompt_continue():
    try:
        if sys.stdin.isatty():
            input("Press Enter to close...")
    except Exception:
        time.sleep(3)


def run_updater():
    inst_path = Path(sys.executable).resolve().parent / INSTRUCTION_FILE

    if not inst_path.exists():
        print("UPDATE ERROR: No update instruction file found.", file=sys.stderr)
        _prompt_continue()
        sys.exit(1)

    instruction = _load_instruction(inst_path)
    zip_path = instruction.get("zip_path", "")
    app_exe = instruction.get("app_exe", "")
    app_pid = instruction.get("app_pid", 0)

    if not zip_path or not app_exe:
        print("UPDATE ERROR: Invalid update instruction.", file=sys.stderr)
        _prompt_continue()
        sys.exit(1)

    app_path = Path(app_exe)
    install_dir = app_path.parent

    print(f"Waiting for application (PID {app_pid}) to exit...")
    exited = _wait_for_process(app_pid) if app_pid else True

    if not exited:
        print("UPDATE ERROR: Application did not exit in time.", file=sys.stderr)
        _cleanup(zip_path, inst_path)
        _prompt_continue()
        sys.exit(1)

    print("Application exited. Applying update...")
    time.sleep(1)

    success = _extract_update(zip_path, install_dir)

    _cleanup(zip_path, inst_path)

    if success:
        print("Update applied successfully!")
        if app_path.exists():
            print(f"Relaunching {app_exe}...")
            try:
                _relaunch_app(app_path)
            except Exception as e:
                print(f"UPDATE WARNING: Could not relaunch app: {e}", file=sys.stderr)
        sys.exit(0)
    else:
        print("UPDATE ERROR: Extraction failed.", file=sys.stderr)
        _prompt_continue()
        sys.exit(1)


def _load_instruction(inst_path: Path) -> dict:
    with open(inst_path, "r", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    run_updater()