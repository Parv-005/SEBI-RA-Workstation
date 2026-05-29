# SEBI RA Automation Software

Trade automation software for SEBI Registered Advisers. Create, manage, and broadcast trades via Telegram, track them in Google Sheets, and generate trade images — all from a desktop GUI.

## Prerequisites

- Python 3.10 or higher (for development)
- A Telegram account with API credentials
- An AngelOne trading account (for CMP fetch)
- A Google Cloud service account with Sheets API access

## Quick Start (Development)

### 1. Clone the repository

```bash
git clone https://github.com/Parv-005/SEBI-RA-Workstation.git
cd SEBI_RA_Automation_Software
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
.venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -e .
```

Or using requirements.txt:

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
python main.py
```

Or after `pip install -e .`:

```bash
sebi-ra
```

`config.json` is **auto-created** from `config_example.json` on first launch. Go to **Settings** in the app to fill in your credentials through the GUI — no manual JSON editing needed.

## Features

- **Trade Entry** — Create new trades with entry price, target, stop loss, and zone
- **Live CMP Fetch** — Fetch current market price from AngelOne SmartAPI
- **Risk/Reward Calculator** — Automatic risk:reward computation
- **Telegram Broadcast** — Send trade signals to configured Telegram groups
- **Google Sheets Logging** — Auto-log trades to Google Sheets
- **Trade Image Generation** — Generate styled trade broadcast images
- **Trade Management** — Track active/closed trades with status updates
- **Auto-Updater** — Checks for new releases on startup, downloads and installs updates automatically

## Configuration

All credentials are configured through the **Settings** page in the app:

- **Telegram** — API ID, API Hash, Phone, group management, authenticate button
- **AngelOne** — SmartAPI credentials for live CMP fetch
- **Google Sheets** — Service account JSON, spreadsheet ID
- **Broadcast** — Image generation toggle
- **Updates** — Enable/disable automatic update checks, manual "Check Now" button
- **Message Formatting** — Customize Telegram broadcast templates

The `config_example.json` file serves as a template. It is auto-copied to `config.json` on first launch if the file doesn't exist.

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New Trade |
| `Ctrl+R` | Active Trades |
| `Ctrl+S` | Settings |
| `Escape` | Back to Active Trades |

## Auto-Updater

The app checks for updates on startup by querying the GitHub Releases API. When a newer version is available, a dialog shows the release notes and lets you download and install the update with one click.

### How it works (end user)

1. App starts → checks GitHub Releases for latest version
2. If update available → dialog appears with version diff and release notes
3. Click **Download & Install** → downloads the ZIP with a progress bar
4. Click **Close** → app quits, updater replaces files, app relaunches
5. You're now on the latest version — no manual download or extraction needed

You can disable automatic checks or trigger a manual check from **Settings → Updates**.

### How it works (developer — releasing updates)

1. Bump the version in `core/version.py` (e.g. `"1.0.0"` → `"1.0.1"`)
2. Make your code changes
3. Build on each target platform (see [Building](#building))
4. Create a GitHub Release with tag `v1.0.1`
5. Upload the three platform ZIPs as release assets:
   - `SEBI_RA_Automation_v1.0.1_Windows.zip`
   - `SEBI_RA_Automation_v1.0.1_macOS.zip`
   - `SEBI_RA_Automation_v1.0.1_Linux.zip`
6. Publish the release — users get the update automatically on next launch

The update check uses `GET /repos/.../releases/latest` on the GitHub API. Each platform picks its matching ZIP by name. No config needed by end users.

### Private repo

When the repository is private, set `_GITHUB_TOKEN` in `services/update_service.py` to a **fine-grained** GitHub PAT (Contents: Read-only, scoped to this repo only). The token is baked into the built binary so users don't need to configure anything. Rebuild and re-release after setting the token.

## Building

Build standalone executables that run without Python installed on the target machine.

### Windows

```bat
build.bat
```

Or manually:

```bat
pip install pyinstaller>=6.0
pyinstaller sebi_ra.spec --clean --noconfirm
```

### macOS / Linux

```bash
./build.sh
```

Or manually:

```bash
pip install "pyinstaller>=6.0"
pyinstaller sebi_ra.spec --clean --noconfirm
```

### Output

Each build produces:

```
dist/
├── SEBI_RA_Automation/          # Application directory (onedir mode)
│   ├── SEBI_RA_Automation       # Main executable (GUI, no console)
│   ├── updater                  # Updater binary (console, standalone)
│   ├── _internal/               # Python runtime + bundled dependencies
│   └── config_example.json      # Auto-copied to config.json on first run
├── updater                      # Standalone updater binary (onefile mode)
└── SEBI_RA_Automation_vX.X.X_<platform>.zip   # Release package
```

The build script automatically:
- Copies the updater binary into the app directory
- Creates a versioned ZIP package with platform suffix

### Distribution

1. Users download the ZIP for their platform from GitHub Releases
2. Extract anywhere — no installer, no admin rights needed
3. Run `SEBI_RA_Automation` (or `SEBI_RA_Automation.exe` on Windows)
4. `config.json` is auto-created on first launch
5. Fill in credentials in Settings → Save
6. Future updates arrive automatically via the updater

The app is fully portable — delete the folder to uninstall.

## Project Structure

```
SEBI_RA_Automation_Software/
├── main.py                  # Application entry point
├── updater.py               # Standalone update installer (stdlib only)
├── config_example.json      # Config template (auto-copied to config.json)
├── pyproject.toml           # Project metadata and dependencies
├── requirements.txt         # Pinned dependencies
├── build.bat                # Windows build script
├── build.sh                 # macOS / Linux build script
├── sebi_ra.spec             # PyInstaller spec (dual EXE target)
├── core/
│   ├── __init__.py          # Package exports
│   ├── version.py           # Single source of truth for version
│   ├── config.py            # Config loading, auto-create, caching
│   └── paths.py             # Platform-aware path resolution
├── gui/
│   ├── main.py              # QApplication setup, update check on startup
│   ├── app.py               # Main window and navigation
│   ├── theme.py             # Dark theme and styling
│   ├── signals.py           # Qt signal bus
│   ├── workers.py           # QThreadPool worker abstraction
│   ├── controllers/         # Business logic controllers
│   ├── views/               # UI pages (trade form, list, settings)
│   ├── widgets/             # Reusable components (sidebar, toast, dialogs)
│   └── models/              # Data models (table models)
├── services/
│   ├── telegram_service.py  # Telethon-based Telegram client
│   ├── google_sheets_service.py  # Google Sheets integration
│   ├── angelone_service.py  # AngelOne SmartAPI client
│   ├── image_generator.py   # Trade image generation
│   ├── trade_service.py     # Trade logic and R:R calculations
│   └── update_service.py    # GitHub Releases API, download, updater launch
├── database/                # Data storage layer (XLSX-based)
├── utils/                   # Constants, logging, helpers, validators
└── controllers/             # Trade controller
```

## License

Private — All rights reserved.
