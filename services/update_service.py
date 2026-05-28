import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import requests

from core.version import __version__
from core.config import Config
from utils.logger import setup_logger

logger = setup_logger("UpdateService")

GITHUB_REPO = "Parv-005/SEBI-RA-Workstation"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
INSTRUCTION_FILE = "update_instruction.json"

# Only needed when the repo goes private.
# Use a FINE-GRAINED Personal Access Token (NOT a classic token):
#   1. https://github.com/settings/tokens → "Fine-grained tokens"
#   2. Resource owner: your account
#   3. Repository access: "Only select repositories" → this repo
#   4. Permissions → Contents: Read-only
# This ensures the token can only download releases — no write access,
# even if someone extracts it from the built app binary.
_GITHUB_TOKEN = ""


def _parse_version(version_str: str) -> tuple[int, ...]:
    cleaned = version_str.lstrip("v").strip()
    parts = cleaned.split(".")
    try:
        return tuple(int(p) for p in parts)
    except (ValueError, AttributeError):
        logger.warning(f"Cannot parse version string: {version_str!r}")
        return (0, 0, 0)


def check_for_update(current_version: str | None = None, github_token: str | None = None):
    """
    Check GitHub Releases for a newer version.

    Returns:
        (has_update, latest_version, release_notes, download_url) on success,
        or None on any error (network, rate-limit, invalid response).
    """
    if current_version is None:
        current_version = __version__

    if github_token is None:
        github_token = Config.get_value("updates", "github_token", None) or _GITHUB_TOKEN

    headers = {"Accept": "application/vnd.github+json"}
    if github_token:
        headers["Authorization"] = f"token {github_token}"

    try:
        logger.info("Checking for updates...")
        resp = requests.get(GITHUB_API_URL, headers=headers, timeout=10)
    except requests.RequestException as e:
        logger.warning(f"Update check network error: {e}")
        return None

    if resp.status_code == 403:
        logger.warning("Update check rate-limited by GitHub API")
        return None

    if resp.status_code == 401:
        logger.warning("Update check: unauthorized (bad token?)")
        return None

    if resp.status_code != 200:
        logger.warning(f"Update check: unexpected status {resp.status_code}")
        return None

    try:
        data = resp.json()
    except (ValueError, requests.exceptions.JSONDecodeError):
        logger.warning("Update check: invalid JSON response")
        return None

    tag_name = data.get("tag_name", "")
    latest_version = tag_name.lstrip("v") if tag_name else ""
    if not latest_version:
        logger.warning("Update check: release has no tag_name")
        return None

    release_notes = data.get("body", "") or ""
    download_url = None
    platform_tags = {
        "win32": "Windows",
        "darwin": "macOS",
        "linux": "Linux",
    }
    target_platform = platform_tags.get(sys.platform, "")
    for asset in data.get("assets", []):
        name = asset.get("name", "")
        if not name.endswith(".zip"):
            continue
        url = asset.get("browser_download_url")
        if not url:
            continue
        if target_platform and target_platform in name:
            download_url = url
            break
        if download_url is None:
            download_url = url

    current_tuple = _parse_version(current_version)
    latest_tuple = _parse_version(latest_version)
    has_update = latest_tuple > current_tuple

    if has_update:
        logger.info(f"Update available: {current_version} -> {latest_version}")
    else:
        logger.info(f"App is up to date ({current_version})")

    return (has_update, latest_version, release_notes, download_url)


def download_release(url: str, dest_path: Path | None = None, progress_callback=None):
    """
    Download a release asset to dest_path.

    Args:
        url: Direct download URL for the .zip asset.
        dest_path: Destination file path. If None, creates a temp file.
        progress_callback: Called with (bytes_downloaded, total_bytes) periodically.

    Returns:
        Path to the downloaded file, or None on error.
    """
    github_token = Config.get_value("updates", "github_token", None) or _GITHUB_TOKEN
    headers = {"Accept": "application/octet-stream"}
    if github_token:
        headers["Authorization"] = f"token {github_token}"

    tmp_dir = None
    if dest_path is None:
        tmp_dir = tempfile.mkdtemp(prefix="sebi_ra_update_")
        dest_path = Path(tmp_dir) / "update.zip"

    try:
        logger.info(f"Downloading update from {url}")
        with requests.get(url, headers=headers, stream=True, timeout=60) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("content-length", 0))
            downloaded = 0
            with open(dest_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        try:
                            progress_callback(downloaded, total)
                        except Exception:
                            pass
        logger.info(f"Update downloaded to {dest_path}")
        return dest_path
    except requests.RequestException as e:
        logger.error(f"Update download failed: {e}", exc_info=True)
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        return None


def get_updater_exe_path() -> Path | None:
    """Return the path to the updater binary next to the main executable, or None."""
    if getattr(sys, 'frozen', False):
        base = Path(sys.executable).resolve().parent
        if os.name == 'nt':
            updater = base / "updater.exe"
        else:
            updater = base / "updater"
        if updater.exists():
            return updater
    return None


def launch_updater(zip_path: str | Path) -> bool:
    """
    Write instruction file and launch the updater binary.

    The calling application should exit immediately after this returns True.

    Returns:
        True if the updater was launched successfully, False otherwise.
    """
    zip_path = str(zip_path)
    if not os.path.exists(zip_path):
        logger.error(f"Update ZIP not found: {zip_path}")
        return False

    updater_exe = get_updater_exe_path()
    if updater_exe is None:
        logger.warning("updater binary not found — update ZIP downloaded but auto-install unavailable")
        return False

    app_exe = str(Path(sys.executable).resolve())
    app_pid = os.getpid()

    instruction = {
        "zip_path": zip_path,
        "app_exe": app_exe,
        "app_pid": app_pid,
    }

    inst_path = Path(updater_exe).parent / INSTRUCTION_FILE
    try:
        with open(inst_path, "w", encoding="utf-8") as f:
            json.dump(instruction, f, indent=2)
    except OSError as e:
        logger.error(f"Failed to write update instruction file: {e}", exc_info=True)
        return False

    try:
        popen_kwargs = {
            "cwd": str(updater_exe.parent),
            "close_fds": True,
        }
        if os.name == "nt":
            popen_kwargs["creationflags"] = subprocess.DETACHED_PROCESS
        else:
            popen_kwargs["start_new_session"] = True
        subprocess.Popen([str(updater_exe)], **popen_kwargs)
        logger.info(f"Updater launched: {updater_exe}")
        return True
    except Exception as e:
        logger.error(f"Failed to launch updater: {e}", exc_info=True)
        return False