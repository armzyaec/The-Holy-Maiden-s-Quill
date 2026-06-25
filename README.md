# The Holy Maiden's Quill

Windows desktop overlay translator for games and visual novels. Select an area of the screen, let Google Cloud Vision OCR read the text, then translate it with your selected translation engine and show the result as draggable overlay bubbles.

## Features

- Screen-region OCR with Google Cloud Vision
- Translation overlay bubbles that can be moved and resized
- Global hotkeys:
  - `F9`: select an area to OCR and translate
  - `Esc`: hide translation overlays
- Translation engines:
  - Google Translate
  - 9arm API Qwen
  - 9arm API Gemma
  - Gemini API
  - Local API Gateway
- Source-language selection to reduce wrong-language translations
- Continuous mode for repeatedly watching the selected area
- Persistent translation cache to avoid translating the same text again
- First-run readiness checklist for credentials, API keys, language settings, and cache
- User data separated from program files

## Requirements

- Windows
- Python 3.10 or newer
- Google Cloud service account credential with Cloud Vision API access
- Optional API key for 9arm or Gemini if you use those engines

## Installation

Clone or download the project, then open PowerShell in the project folder.

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\pip install -r requirements.txt
```

## Google Cloud Credential

Google Cloud Vision is required for OCR even when you use 9arm, Gemini, or another engine for translation.

Place your Google credential file here:

```txt
user_data/credentials/google_credentials.json
```

The app also accepts credential files matching:

```txt
user_data/credentials/translate-*.json
```

Alternatively, set the environment variable manually:

```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="D:\path\to\google_credentials.json"
```

Do not commit real credentials or API keys to GitHub.

## Running

```powershell
.\venv\Scripts\python.exe main.py
```

Or run:

```powershell
.\run_translator.bat
```

On first launch, the app shows a readiness checklist explaining what is required before translation can work.

## Usage

1. Choose the translation engine.
2. Select the source language, or use `AUTO`.
3. Select the target language.
4. Enter the API key if your selected engine needs one.
5. Press `F9` and drag over the game text.
6. Read the translated overlay.
7. Press `Esc` to hide overlays.

For games with mixed UI languages, choose a specific source language such as `JP`, `EN`, `KR`, `CH`, or `TH` instead of `AUTO`.

## User Data Layout

Program files stay in the project root:

```txt
main.py
requirements.txt
run_translator.bat
main.spec
setup.py
setup.iss
icon.ico
README.md
```

User-specific files stay under `user_data/`:

```txt
user_data/config.json
user_data/translation_cache.json
user_data/translator.log
user_data/onboarding_state.json
user_data/credentials/google_credentials.json
```

`user_data/` is ignored by Git because it contains local settings, logs, cache, API keys, and credentials.

## Translation Cache

The app stores previous translations in:

```txt
user_data/translation_cache.json
```

Cache entries are separated by:

- translation engine
- source language
- target language
- original text

When the same text appears again, the app reads from the cache instead of calling the translation API again. This helps reduce token usage and API cost.

To clear the cache, close the app and delete:

```txt
user_data/translation_cache.json
```

## Build

Install build tools:

```powershell
.\venv\Scripts\pip install cx-Freeze pyinstaller
```

Build with cx_Freeze:

```powershell
.\venv\Scripts\python.exe setup.py build
```

Build with PyInstaller:

```powershell
.\venv\Scripts\pyinstaller main.spec
```

After building with cx_Freeze, you can use `setup.iss` with Inno Setup to create a Windows installer.

Credentials are not bundled into builds. Users should place their own credential file under `user_data/credentials/`.

## Troubleshooting

### `Default credentials were not found`

Place `google_credentials.json` in:

```txt
user_data/credentials/
```

Or set `GOOGLE_APPLICATION_CREDENTIALS`.

### `FAILED_PRECONDITION` or `Regional Access Boundary`

This is a Google Cloud project or service-account policy problem. Check that:

- Cloud Vision API is enabled
- billing is enabled
- the service account has permission to call Cloud Vision
- organization policies allow the service account to use Cloud Vision

### `pyqtdarktheme` cannot be installed

The app has a built-in fallback dark theme. On newer Python versions, `pyqtdarktheme` may be skipped automatically.

## Security Notes

- Never commit `user_data/`
- Never commit `google_credentials.json`
- Never commit `config.json` if it contains API keys
- Rotate any API key that was shared in screenshots, logs, or chat

