# SEBI RA Automation Software

Trade automation software for SEBI Registered Advisers. Create, manage, and broadcast trades via Telegram, track them in Google Sheets, and generate trade images — all from a desktop GUI.

## Prerequisites

- Python 3.10 or higher
- A Telegram account with API credentials
- An AngelOne trading account (for CMP fetch)
- A Google Cloud service account with Sheets API access

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/SEBI_RA_Automation_Software.git
cd SEBI_RA_Automation_Software
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows
```

### 3. Install dependencies

```bash
pip install -e .
```

Or using requirements.txt:

```bash
pip install -r requirements.txt
```

### 4. Configure credentials

Copy the example config and fill in your credentials:

```bash
cp config_example.json config.json
```

Edit `config.json` and provide:

- **Telegram**: API ID, API Hash, Phone number, and group IDs
- **AngelOne**: API Key, Client ID, Password, TOTP Secret
- **Google Sheets**: Service account JSON path, Spreadsheet ID

### 5. Run the application

```bash
python main.py
```

Or after `pip install -e .`:

```bash
sebi-ra
```

## Configuration

All credentials are stored in `config.json` (git-ignored). The settings page in the app provides a UI to configure:

- Telegram API credentials and group management
- AngelOne (SmartAPI) credentials for live CMP fetch
- Google Sheets integration for trade logging
- Message templates for trade broadcasts

## Features

- **Trade Entry**: Create new trades with entry price, target, stop loss, and zone
- **Live CMP Fetch**: Fetch current market price from AngelOne SmartAPI
- **Risk/Reward Calculator**: Automatic risk:reward computation
- **Telegram Broadcast**: Send trade signals to configured Telegram groups
- **Google Sheets Logging**: Auto-log trades to Google Sheets
- **Trade Image Generation**: Generate styled trade broadcast images
- **Trade Management**: Track active/closed trades with status updates

## Project Structure

```
SEBI_RA_Automation_Software/
├── main.py                  # Application entry point
├── config_example.json      # Example configuration template
├── pyproject.toml           # Project metadata and dependencies
├── requirements.txt         # Pinned dependencies
├── gui/
│   ├── main.py              # QApplication setup
│   ├── app.py               # Main window and navigation
│   ├── theme.py             # Dark theme and styling
│   ├── signals.py           # Qt signal bus
│   ├── controllers/         # Business logic controllers
│   ├── views/               # UI pages (trade form, list, settings)
│   ├── widgets/             # Reusable UI components
│   └── models/              # Data models (table models)
├── services/
│   ├── telegram_service.py  # Telethon-based Telegram client
│   ├── google_sheets_service.py  # Google Sheets integration
│   ├── angelone_service.py  # AngelOne SmartAPI client
│   ├── image_generator.py   # Trade image generation
│   └── trade_service.py     # Trade logic and R:R calculations
├── database/                # Data storage layer (XLSX-based)
├── core/                    # Config management
├── utils/                   # Constants, logging, helpers
└── controllers/             # Additional controllers
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New Trade |
| `Ctrl+R` | Active Trades |
| `Ctrl+S` | Settings |
| `Escape` | Back to Active Trades |

## License

Private — All rights reserved.
