# The Holy Maiden's Quill

Windows desktop overlay translator for games and visual novels.

## Languages / ภาษา

- [English Version](#english-version)
- [ภาษาไทย](#ภาษาไทย)

---

## English Version

Windows desktop overlay translator for games and visual novels. Select an area of the screen, let Google Cloud Vision OCR read the text, then translate it with your selected translation engine and show the result as draggable overlay bubbles.

### Features

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

### Requirements

- Windows
- Python 3.10 or newer
- Google Cloud service account credential with Cloud Vision API access
- Optional API key for 9arm or Gemini if you use those engines

### Installation

Clone or download the project, then open PowerShell in the project folder.

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\pip install -r requirements.txt
```

### Google Cloud Credential

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

### Running

```powershell
.\venv\Scripts\python.exe main.py
```

Or run:

```powershell
.\run_translator.bat
```

On first launch, the app shows a readiness checklist explaining what is required before translation can work.

### Usage

1. Choose the translation engine.
2. Select the source language, or use `AUTO`.
3. Select the target language.
4. Enter the API key if your selected engine needs one.
5. Press `F9` and drag over the game text.
6. Read the translated overlay.
7. Press `Esc` to hide overlays.

For games with mixed UI languages, choose a specific source language such as `JP`, `EN`, `KR`, `CH`, or `TH` instead of `AUTO`.

### User Data Layout

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

### Translation Cache

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

### Build

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

### Troubleshooting

#### `Default credentials were not found`

Place `google_credentials.json` in:

```txt
user_data/credentials/
```

Or set `GOOGLE_APPLICATION_CREDENTIALS`.

#### `FAILED_PRECONDITION` or `Regional Access Boundary`

This is a Google Cloud project or service-account policy problem. Check that:

- Cloud Vision API is enabled
- billing is enabled
- the service account has permission to call Cloud Vision
- organization policies allow the service account to use Cloud Vision

#### `pyqtdarktheme` cannot be installed

The app has a built-in fallback dark theme. On newer Python versions, `pyqtdarktheme` may be skipped automatically.

### Security Notes

- Never commit `user_data/`
- Never commit `google_credentials.json`
- Never commit `config.json` if it contains API keys
- Rotate any API key that was shared in screenshots, logs, or chat

---

## ภาษาไทย

โปรแกรมแปลข้อความแบบ Overlay สำหรับ Windows ใช้กับเกมและ Visual Novel ได้ โดยเลือกพื้นที่บนหน้าจอให้ Google Cloud Vision อ่านข้อความด้วย OCR จากนั้นโปรแกรมจะแปลด้วยระบบแปลที่เลือกไว้ และแสดงผลเป็นกล่องแปลที่ลากย้ายหรือปรับขนาดได้

### ความสามารถ

- อ่านข้อความจากพื้นที่ที่เลือกบนหน้าจอด้วย Google Cloud Vision
- แสดงคำแปลเป็นกล่อง Overlay ที่ย้ายตำแหน่งและปรับขนาดได้
- ปุ่มลัดใช้งานได้ทั่วระบบ:
  - `F9`: เลือกพื้นที่เพื่ออ่าน OCR และแปล
  - `Esc`: ซ่อนกล่องคำแปล
- รองรับระบบแปล:
  - Google Translate
  - 9arm API Qwen
  - 9arm API Gemma
  - Gemini API
  - Local API Gateway
- เลือกภาษาต้นทางได้ เพื่อลดปัญหาแปลผิดภาษา
- มีโหมดต่อเนื่องสำหรับดูพื้นที่เดิมซ้ำ ๆ
- มีแคชคำแปล เพื่อลดการแปลข้อความเดิมซ้ำ
- มีรายการตรวจสอบตอนเปิดครั้งแรกสำหรับ credentials, API keys, ภาษา, และ cache
- แยกข้อมูลผู้ใช้ออกจากไฟล์โปรแกรม

### สิ่งที่ต้องมี

- Windows
- Python 3.10 หรือใหม่กว่า
- Google Cloud service account credential ที่มีสิทธิ์ใช้งาน Cloud Vision API
- API key ของ 9arm หรือ Gemini ถ้าเลือกใช้ระบบแปลเหล่านั้น

### การติดตั้ง

Clone หรือดาวน์โหลดโปรเจกต์ จากนั้นเปิด PowerShell ในโฟลเดอร์โปรเจกต์

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\pip install -r requirements.txt
```

### Google Cloud Credential

Google Cloud Vision จำเป็นสำหรับ OCR แม้ว่าจะใช้ 9arm, Gemini, หรือระบบอื่นสำหรับแปลก็ตาม

ให้นำไฟล์ credential ของ Google ไปวางไว้ที่:

```txt
user_data/credentials/google_credentials.json
```

โปรแกรมยังรองรับไฟล์ credential ที่มีชื่อรูปแบบนี้ด้วย:

```txt
user_data/credentials/translate-*.json
```

หรือจะตั้งค่า environment variable เองก็ได้:

```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="D:\path\to\google_credentials.json"
```

ห้ามอัปโหลด credentials หรือ API keys จริงขึ้น GitHub

### การรันโปรแกรม

```powershell
.\venv\Scripts\python.exe main.py
```

หรือรันไฟล์นี้:

```powershell
.\run_translator.bat
```

เมื่อเปิดครั้งแรก โปรแกรมจะแสดงรายการตรวจสอบว่าต้องตั้งค่าอะไรบ้างก่อนใช้งานแปลได้

### วิธีใช้งาน

1. เลือกระบบแปลที่ต้องการใช้
2. เลือกภาษาต้นทาง หรือใช้ `AUTO`
3. เลือกภาษาปลายทาง
4. ใส่ API key ถ้าระบบแปลที่เลือกจำเป็นต้องใช้
5. กด `F9` แล้วลากครอบข้อความในเกม
6. อ่านคำแปลจากกล่อง Overlay
7. กด `Esc` เพื่อซ่อนกล่องคำแปล

ถ้าเกมมีหลายภาษาปนกันใน UI แนะนำให้เลือกภาษาต้นทางแบบเจาะจง เช่น `JP`, `EN`, `KR`, `CH`, หรือ `TH` แทนการใช้ `AUTO`

### โครงสร้างข้อมูลผู้ใช้

ไฟล์โปรแกรมจะอยู่ในโฟลเดอร์หลักของโปรเจกต์:

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

ไฟล์เฉพาะของผู้ใช้จะอยู่ใน `user_data/`:

```txt
user_data/config.json
user_data/translation_cache.json
user_data/translator.log
user_data/onboarding_state.json
user_data/credentials/google_credentials.json
```

`user_data/` ถูกตั้งค่าให้ Git ไม่ติดตาม เพราะมีข้อมูลตั้งค่าในเครื่อง, logs, cache, API keys, และ credentials

### แคชคำแปล

โปรแกรมจะเก็บคำแปลที่เคยแปลแล้วไว้ที่:

```txt
user_data/translation_cache.json
```

ข้อมูลแคชจะแยกตาม:

- ระบบแปล
- ภาษาต้นทาง
- ภาษาปลายทาง
- ข้อความต้นฉบับ

เมื่อเจอข้อความเดิมอีกครั้ง โปรแกรมจะอ่านจากแคชแทนการเรียก API ใหม่ ช่วยลดการใช้ token และค่าใช้จ่าย API

ถ้าต้องการล้างแคช ให้ปิดโปรแกรมแล้วลบไฟล์นี้:

```txt
user_data/translation_cache.json
```

### การ Build

ติดตั้งเครื่องมือสำหรับ build:

```powershell
.\venv\Scripts\pip install cx-Freeze pyinstaller
```

Build ด้วย cx_Freeze:

```powershell
.\venv\Scripts\python.exe setup.py build
```

Build ด้วย PyInstaller:

```powershell
.\venv\Scripts\pyinstaller main.spec
```

หลังจาก build ด้วย cx_Freeze แล้ว สามารถใช้ `setup.iss` กับ Inno Setup เพื่อสร้างตัวติดตั้ง Windows ได้

Credentials จะไม่ถูกใส่ไปในไฟล์ build ผู้ใช้ต้องนำไฟล์ credential ของตัวเองไปวางไว้ใน `user_data/credentials/`

### การแก้ปัญหาเบื้องต้น

#### `Default credentials were not found`

ให้วางไฟล์ `google_credentials.json` ไว้ใน:

```txt
user_data/credentials/
```

หรือตั้งค่า `GOOGLE_APPLICATION_CREDENTIALS`

#### `FAILED_PRECONDITION` หรือ `Regional Access Boundary`

ปัญหานี้มักเกี่ยวกับ Google Cloud project หรือ service account policy ให้ตรวจสอบว่า:

- เปิดใช้งาน Cloud Vision API แล้ว
- เปิด billing แล้ว
- service account มีสิทธิ์เรียกใช้ Cloud Vision
- organization policies อนุญาตให้ service account ใช้ Cloud Vision

#### ติดตั้ง `pyqtdarktheme` ไม่ได้

โปรแกรมมีธีมมืดสำรองในตัวเอง ถ้าใช้ Python รุ่นใหม่ บางครั้ง `pyqtdarktheme` อาจถูกข้ามอัตโนมัติ

### หมายเหตุด้านความปลอดภัย

- ห้าม commit โฟลเดอร์ `user_data/`
- ห้าม commit ไฟล์ `google_credentials.json`
- ห้าม commit ไฟล์ `config.json` ถ้าในไฟล์มี API keys
- ถ้า API key เคยถูกแชร์ในรูปภาพ, logs, หรือแชต ให้เปลี่ยน key ใหม่ทันที
