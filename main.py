import json
import logging
import os
import shutil
import sys
from collections import OrderedDict, deque
from dataclasses import dataclass, field
from html import escape, unescape
from html.parser import HTMLParser
from pathlib import Path
from threading import Thread
from typing import Optional
from unicodedata import category

try:
    from pythainlp.tokenize import word_tokenize
    HAS_PYTHAINLP = True
except Exception:
    HAS_PYTHAINLP = False

import mss
import mss.tools
try:
    import qdarktheme
except ImportError:
    qdarktheme = None
from pynput import keyboard
from PyQt5.QtCore import QObject, QRect, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QFontMetrics, QIcon, QPainter, QPen, QImage
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


APP_NAME = "The Holy Maiden's Quill"
GOOGLE_CREDENTIALS_ENV = "GOOGLE_APPLICATION_CREDENTIALS"
LOCAL_CREDENTIALS_NAME = "google_credentials.json"
LOCAL_CREDENTIALS_PATTERNS = (LOCAL_CREDENTIALS_NAME, "translate-*.json")
GOOGLE_SERVICE_ACCOUNTS_URL = "https://console.cloud.google.com/iam-admin/serviceaccounts"
DEFAULT_UI_LANGUAGE = "en"
USER_DATA_DIR_NAME = "user_data"
CREDENTIALS_DIR_NAME = "credentials"
OVERLAY_MARGIN = 8
OVERLAY_PADDING = 12
MIN_OVERLAY_WIDTH = 220
MAX_OVERLAY_WIDTH = 520
MIN_OVERLAY_HEIGHT = 64
MAX_OVERLAY_HEIGHT = 620
CONTINUOUS_INTERVAL_MS = 1500
SCENE_HISTORY_LIMIT = 20
TRANSLATION_CACHE_LIMIT = 100
TRANSLATION_TEXT_CACHE_LIMIT = 5000
TRANSLATION_CACHE_FILE = "translation_cache.json"
ONBOARDING_STATE_FILE = "onboarding_state.json"
 
LANG_MAP = {
    "AUTO": {"code": None, "name": "Auto detect"},
    "TH": {"code": "th", "name": "Thai"},
    "EN": {"code": "en", "name": "English"},
    "JP": {"code": "ja", "name": "Japanese"},
    "KR": {"code": "ko", "name": "Korean"},
    "CH": {"code": "zh", "name": "Chinese"},
}

UI_TEXT = {
    "en": {
        "ui_language": "UI language:",
        "first_run_title": "Readiness Check",
        "first_run_heading": "What the app needs before translating",
        "first_run_description": (
            "The app uses Google Cloud Vision for OCR screen reading and the selected "
            "translation engine for translating text."
        ),
        "skip_ready": "Do not show this again when required items are ready",
        "credentials_help_button": "How to get Google file",
        "select_area_hint": "Press F9 to select an area | Press Esc to hide translations",
        "select_area_button": "Select area to translate (F9)",
        "continuous_mode": "Continuous mode: watch the latest area",
        "engine_label": "Translation engine:",
        "source_label": "Source language:",
        "target_label": "Target language:",
        "api_key_placeholder": "Enter API key...",
        "show_key": "Show key",
        "font_size_label": "Translation text size:",
        "opacity_label": "Translation background opacity:",
        "latest_log": "Latest translations",
        "credential_ready": "Google credential: ready ({name})",
        "credential_missing": "Google credential: not set. Click Import google_credentials.json",
        "settings_saved": "Settings saved",
        "log_heading": "Full page translation [engine: {engine}]:",
        "log_original": "Original",
        "log_translation": "Translation",
        "check_credential_title": "Google Cloud Vision credential for OCR",
        "check_credential_ready": "Ready",
        "check_credential_missing": "Import google_credentials.json or place it in user_data/credentials",
        "check_engine_title": "Translation engine",
        "check_api_key_title": "Translation engine API key",
        "check_api_not_required": "Not required for this engine",
        "check_api_ready": "API key entered",
        "check_api_missing": "API key is missing",
        "check_gateway": "Start your API Gateway at http://localhost:3000",
        "check_language_title": "Source / target language",
        "check_cache_title": "Translation cache",
        "check_cache_detail": f"{TRANSLATION_CACHE_FILE} will be created automatically",
        "check_hotkeys_title": "Hotkeys",
        "check_hotkeys_detail": "F9 selects an area, Esc hides translations",
        "check_needs_setup": "Needs setup",
        "continuous_watching": "Continuous mode is watching the selected area",
        "continuous_needs_area": "Continuous mode needs a selected area",
        "continuous_stopped": "Continuous mode stopped",
        "new_area_queued": "New area queued",
        "reading_translating": "Reading and translating...",
        "no_text_found": "No text found",
        "translation_failed": "Translation failed",
        "translated_status": "Translated | scene history: {count}/{limit}",
    },
    "th": {
        "ui_language": "ภาษา UI:",
        "first_run_title": "ตรวจความพร้อมก่อนใช้งาน",
        "first_run_heading": "สิ่งที่โปรแกรมต้องการก่อนเริ่มแปล",
        "first_run_description": (
            "โปรแกรมต้องใช้ Google Cloud Vision สำหรับ OCR อ่านภาพหน้าจอ "
            "และใช้ engine ที่เลือกไว้สำหรับแปลข้อความ"
        ),
        "skip_ready": "ไม่ต้องแสดงหน้านี้อีก ถ้าของจำเป็นพร้อมแล้ว",
        "credentials_help_button": "วิธีเอาไฟล์ Google",
        "select_area_hint": "กด F9 เพื่อเลือกพื้นที่ | กด Esc เพื่อซ่อนคำแปล",
        "select_area_button": "เลือกพื้นที่เพื่อแปล (F9)",
        "continuous_mode": "Continuous mode: ดูพื้นที่ล่าสุดซ้ำ",
        "engine_label": "ระบบแปลภาษา:",
        "source_label": "ภาษาต้นทาง:",
        "target_label": "ภาษาปลายทาง:",
        "api_key_placeholder": "ใส่ API Key...",
        "show_key": "แสดงคีย์",
        "font_size_label": "ขนาดตัวอักษรคำแปล:",
        "opacity_label": "ความทึบพื้นหลังคำแปล:",
        "latest_log": "บันทึกคำแปลล่าสุด",
        "credential_ready": "Google credential: พร้อมใช้งาน ({name})",
        "credential_missing": "Google credential: ยังไม่ได้ตั้งค่า กด Import google_credentials.json",
        "settings_saved": "บันทึกการตั้งค่าแล้ว",
        "log_heading": "แปลทั้งหน้า [ใช้ระบบ: {engine}]:",
        "log_original": "ต้นฉบับ",
        "log_translation": "คำแปล",
        "check_credential_title": "Google Cloud Vision credential สำหรับ OCR",
        "check_credential_ready": "พร้อม",
        "check_credential_missing": "นำเข้า google_credentials.json หรือวางใน user_data/credentials",
        "check_engine_title": "Translation engine",
        "check_api_key_title": "API key ของ engine แปล",
        "check_api_not_required": "ไม่จำเป็นสำหรับ engine นี้",
        "check_api_ready": "ใส่ API key แล้ว",
        "check_api_missing": "ยังไม่ได้ใส่ API key",
        "check_gateway": "ต้องเปิด API Gateway ที่ http://localhost:3000",
        "check_language_title": "ภาษาต้นทาง / ภาษาปลายทาง",
        "check_cache_title": "Cache คำแปล",
        "check_cache_detail": f"จะสร้าง {TRANSLATION_CACHE_FILE} ให้อัตโนมัติ",
        "check_hotkeys_title": "ปุ่มลัด",
        "check_hotkeys_detail": "F9 เลือกพื้นที่, Esc ซ่อนคำแปล",
        "check_needs_setup": "ต้องตั้งค่า",
        "continuous_watching": "Continuous mode กำลังดูพื้นที่ที่เลือก",
        "continuous_needs_area": "Continuous mode ต้องเลือกพื้นที่ก่อน",
        "continuous_stopped": "หยุด Continuous mode แล้ว",
        "new_area_queued": "เพิ่มพื้นที่ใหม่เข้าคิวแล้ว",
        "reading_translating": "กำลังอ่านและแปล...",
        "no_text_found": "ไม่พบข้อความ",
        "translation_failed": "แปลไม่สำเร็จ",
        "translated_status": "แปลแล้ว | ประวัติฉาก: {count}/{limit}",
    },
}


def ui_text(language, key, **kwargs):
    text = UI_TEXT.get(language, UI_TEXT[DEFAULT_UI_LANGUAGE]).get(
        key,
        UI_TEXT[DEFAULT_UI_LANGUAGE].get(key, key),
    )
    return text.format(**kwargs) if kwargs else text


@dataclass
class TextRegion:
    original: str
    source_rect: QRect
    translated: str = ""
    overlay_rect: QRect = field(default_factory=QRect)


@dataclass(frozen=True)
class TranslationSettings:
    engine_index: int
    engine_name: str
    source_label: str
    source_code: Optional[str]
    source_name: str
    target_code: str
    target_name: str
    api_key: str = ""


@dataclass(frozen=True)
class OverlayStyle:
    font_size: int = 14
    background_opacity: int = 225


class TranslatedRegionParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.regions = {}
        self.current_region = None

    def handle_starttag(self, tag, attrs):
        if tag != "p":
            return

        attributes = dict(attrs)
        region_index = attributes.get("data-region")
        if region_index is not None:
            self.current_region = int(region_index)
            self.regions[self.current_region] = ""

    def handle_endtag(self, tag):
        if tag == "p":
            self.current_region = None

    def handle_data(self, data):
        if self.current_region is not None:
            self.regions[self.current_region] += data


def app_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def user_data_dir():
    path = app_dir() / USER_DATA_DIR_NAME
    path.mkdir(exist_ok=True)
    return path


def credentials_dir():
    path = user_data_dir() / CREDENTIALS_DIR_NAME
    path.mkdir(exist_ok=True)
    return path


def user_data_path(name):
    return user_data_dir() / name


def resource_path(name):
    base_path = Path(getattr(sys, "_MEIPASS", app_dir()))
    return base_path / name


def find_local_credentials():
    search_dirs = (credentials_dir(), user_data_dir(), app_dir())
    for directory in search_dirs:
        for pattern in LOCAL_CREDENTIALS_PATTERNS:
            matches = sorted(directory.glob(pattern))
            if matches:
                return matches[0]
    return None


def validate_google_credentials_file(path):
    data = load_json_file(path, default=None)
    if not isinstance(data, dict):
        raise ValueError("This file is not a valid JSON credential file.")

    required_fields = ("type", "project_id", "private_key", "client_email")
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        raise ValueError(
            "The credential file is missing required fields: " + ", ".join(missing_fields)
        )

    if data.get("type") != "service_account":
        raise ValueError("This file must be a Google service account JSON key.")


def import_google_credentials_file(source_path):
    source = Path(source_path)
    validate_google_credentials_file(source)
    target = credentials_dir() / LOCAL_CREDENTIALS_NAME
    shutil.copy2(source, target)
    os.environ[GOOGLE_CREDENTIALS_ENV] = str(target)
    logging.info("Imported Google credentials to %s", target)
    return target


def google_credentials_help_text(language=DEFAULT_UI_LANGUAGE):
    if language == "th":
        return (
            "วิธีเอา google_credentials.json:\n\n"
            "1. เข้า Google Cloud Console\n"
            "2. เลือกโปรเจกต์ที่เปิด Billing แล้ว\n"
            "3. เปิด Cloud Vision API ในโปรเจกต์นั้น\n"
            "4. ไปที่ IAM & Admin > Service Accounts\n"
            "5. สร้างหรือเลือก Service Account\n"
            "6. เข้าแท็บ Keys > Add key > Create new key\n"
            "7. เลือก JSON แล้วกด Create\n"
            "8. นำไฟล์ .json ที่ดาวน์โหลดมา Import ในโปรแกรม\n\n"
            f"หน้าที่ใช้สร้าง Service Account:\n{GOOGLE_SERVICE_ACCOUNTS_URL}\n\n"
            "หมายเหตุ: เก็บไฟล์นี้เป็นความลับ ห้ามอัปขึ้น GitHub หรือส่งให้คนอื่น"
        )

    return (
        "How to get google_credentials.json:\n\n"
        "1. Open Google Cloud Console\n"
        "2. Select a project with billing enabled\n"
        "3. Enable Cloud Vision API for that project\n"
        "4. Go to IAM & Admin > Service Accounts\n"
        "5. Create or select a service account\n"
        "6. Open Keys > Add key > Create new key\n"
        "7. Select JSON, then click Create\n"
        "8. Import the downloaded .json file in this app\n\n"
        f"Service Accounts page:\n{GOOGLE_SERVICE_ACCOUNTS_URL}\n\n"
        "Keep this file secret. Do not upload it to GitHub or share it with others."
    )


def show_google_credentials_help(parent=None, language=DEFAULT_UI_LANGUAGE):
    QMessageBox.information(
        parent,
        "วิธีเอา google_credentials.json" if language == "th" else "How to get google_credentials.json",
        google_credentials_help_text(language),
    )


def import_google_credentials_with_dialog(parent=None, language=DEFAULT_UI_LANGUAGE):
    source_path, _ = QFileDialog.getOpenFileName(
        parent,
        "เลือกไฟล์ Google service account JSON" if language == "th" else "Select Google service account JSON",
        str(Path.home() / "Downloads"),
        "JSON files (*.json);;All files (*.*)",
    )
    if not source_path:
        return False

    try:
        target = import_google_credentials_file(source_path)
    except Exception as exc:
        QMessageBox.critical(
            parent,
            "Import credential ไม่สำเร็จ" if language == "th" else "Credential import failed",
            f"{exc}\n\n{google_credentials_help_text(language)}",
        )
        return False

    QMessageBox.information(
        parent,
        "Import credential สำเร็จ" if language == "th" else "Credential imported",
        (
            f"นำเข้าไฟล์เรียบร้อยแล้ว:\n{target}\n\nโปรแกรมจะใช้ไฟล์นี้สำหรับ Google Cloud Vision OCR"
            if language == "th"
            else f"Imported successfully:\n{target}\n\nThe app will use this file for Google Cloud Vision OCR."
        ),
    )
    return True


logging.basicConfig(
    filename=user_data_path("translator.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


def show_error(title, message):
    logging.error("%s: %s", title, message)
    if QApplication.instance():
        QMessageBox.critical(None, title, message)
    else:
        print(f"{title}: {message}", file=sys.stderr)


def app_stylesheet():
    if qdarktheme:
        return qdarktheme.load_stylesheet("dark")

    return """
        QWidget { background-color: #202124; color: #f1f3f4; }
        QPushButton {
            background-color: #3c4043;
            border: 1px solid #5f6368;
            border-radius: 4px;
            padding: 8px;
        }
        QPushButton:hover { background-color: #4b4f52; }
        QLineEdit, QTextEdit, QComboBox {
            background-color: #171717;
            border: 1px solid #5f6368;
            border-radius: 4px;
            padding: 6px;
        }
        QCheckBox { spacing: 8px; }
    """


def load_json_file(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        logging.exception("Failed to load JSON file: %s", path)
        return default


def save_json_file(path, data):
    path = Path(path)
    path.parent.mkdir(exist_ok=True)
    temp_path = path.with_suffix(".json.tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    os.replace(temp_path, path)


def clamp_int(value, minimum, maximum, default):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, value))


def onboarding_state_path():
    return user_data_path(ONBOARDING_STATE_FILE)


def migrate_user_file(filename, target_dir=None):
    source = app_dir() / filename
    target = (target_dir or user_data_dir()) / filename
    if target.exists() or not source.exists():
        return target

    try:
        target.parent.mkdir(exist_ok=True)
        os.replace(source, target)
        logging.info("Migrated %s to %s", source, target)
    except Exception:
        logging.exception("Failed to migrate %s to %s", source, target)
    return target


def migrate_user_files():
    migrate_user_file("config.json")
    migrate_user_file(TRANSLATION_CACHE_FILE)
    migrate_user_file(ONBOARDING_STATE_FILE)
    migrate_user_file("translator.log")
    migrate_user_file(LOCAL_CREDENTIALS_NAME, credentials_dir())
    for credentials_file in app_dir().glob("translate-*.json"):
        migrate_user_file(credentials_file.name, credentials_dir())


def parse_json_array_response(content, expected_length):
    """Extract a JSON string array from plain or markdown-wrapped model output."""
    content = (content or "").strip()
    start_idx = content.find("[")
    end_idx = content.rfind("]")
    if start_idx != -1 and end_idx > start_idx:
        content = content[start_idx:end_idx + 1]

    parsed = json.loads(content)
    if not isinstance(parsed, list) or len(parsed) != expected_length:
        raise ValueError("Model response is not a JSON array with the expected length.")
    return [str(item) for item in parsed]


def google_cloud_error_message(exc):
    message = str(exc)
    if "Regional Access Boundary" in message or "FAILED_PRECONDITION" in message:
        return (
            "Google Cloud Vision OCR failed because the selected credential or project "
            "is blocked by a Google Cloud precondition/policy. Check that the service "
            "account belongs to a project with Cloud Vision API enabled, billing enabled, "
            "and permission to call Vision API. If your organization uses Regional Access "
            "Boundary or other access policies, create/use a service account that is allowed "
            "to call Cloud Vision."
        )
    return message


class GoogleCloudService:
    def __init__(self):
        self._vision = None
        self._translate = None
        self._vision_client = None
        self._translate_client = None

    def _ensure_credentials(self):
        credentials_path = os.environ.get(GOOGLE_CREDENTIALS_ENV)
        local_credentials = find_local_credentials()

        if not credentials_path and local_credentials:
            credentials_path = str(local_credentials)
            os.environ[GOOGLE_CREDENTIALS_ENV] = credentials_path

        if not credentials_path:
            raise RuntimeError(
                "Google Cloud Vision credential is required for OCR. "
                "Place google_credentials.json or translate-*.json in user_data/credentials, "
                f"or set {GOOGLE_CREDENTIALS_ENV} to your credential file path."
            )

        if credentials_path and not Path(credentials_path).exists():
            raise RuntimeError(f"Credential file not found: {credentials_path}")

    def _ensure_clients(self):
        if self._vision_client and self._translate_client:
            return

        self._ensure_credentials()
        try:
            from google.cloud import translate_v2 as translate
            from google.cloud import vision
        except ImportError as exc:
            raise RuntimeError(
                "Missing Google Cloud libraries. Install google-cloud-vision and "
                "google-cloud-translate."
            ) from exc

        try:
            self._vision = vision
            self._translate = translate
            self._vision_client = vision.ImageAnnotatorClient()
            self._translate_client = translate.Client()
        except Exception as exc:
            raise RuntimeError(
                f"Cannot connect to Google Cloud: {google_cloud_error_message(exc)}"
            ) from exc

    def get_text_regions(self, image_bytes, scale, source_language=None):
        self._ensure_clients()
        image = self._vision.Image(content=image_bytes)
        image_context = {}
        if source_language:
            image_context["language_hints"] = [source_language]

        try:
            response = self._vision_client.text_detection(
                image=image,
                image_context=image_context or None,
            )
        except Exception as exc:
            raise RuntimeError(
                f"Google Cloud Vision OCR failed: {google_cloud_error_message(exc)}"
            ) from exc
        if response.error.message:
            raise RuntimeError(response.error.message)

        regions = []
        annotation = response.full_text_annotation
        for page in annotation.pages:
            for block in page.blocks:
                for paragraph in block.paragraphs:
                    text = paragraph_text(paragraph)
                    rect = bounds_to_rect(paragraph.bounding_box, scale)
                    if text and rect.isValid():
                        regions.append(TextRegion(text, rect))

        if regions:
            return merge_nearby_regions(regions)

        texts = response.text_annotations
        if not texts:
            return []

        main_block = texts[0]
        return [
            TextRegion(
                main_block.description.replace("\n", " ").strip(),
                bounds_to_rect(main_block.bounding_poly, scale),
            )
        ]

    def translate_text(self, text, target_language="th", source_language=None):
        if not text:
            return ""

        self._ensure_clients()
        kwargs = {"target_language": target_language}
        if source_language:
            kwargs["source_language"] = source_language
        result = self._translate_client.translate(text, **kwargs)
        return unescape(result["translatedText"])

    def translate_batch(self, texts, target_language="th", source_language=None):
        if not texts:
            return []

        self._ensure_clients()
        try:
            contextual_text = "".join(
                f'<p data-region="{index}">{escape(text)}</p>'
                for index, text in enumerate(texts)
            )
            translate_kwargs = {
                "target_language": target_language,
                "format_": "html",
            }
            if source_language:
                translate_kwargs["source_language"] = source_language
            result = self._translate_client.translate(contextual_text, **translate_kwargs)
            parser = TranslatedRegionParser()
            parser.feed(result["translatedText"])
            if len(parser.regions) != len(texts):
                raise ValueError("Contextual translation did not preserve every region.")
            return [parser.regions[index].strip() for index in range(len(texts))]
        except Exception:
            logging.exception(
                "Contextual translation failed. Falling back to independent batch."
            )

        try:
            translate_kwargs = {"target_language": target_language}
            if source_language:
                translate_kwargs["source_language"] = source_language
            results = self._translate_client.translate(texts, **translate_kwargs)
        except Exception:
            logging.exception("Independent batch failed. Falling back to single requests.")
            return [self.translate_text(text, target_language, source_language) for text in texts]

        if isinstance(results, dict):
            results = [results]

        return [unescape(result["translatedText"]) for result in results]


def virtual_screen_geometry():
    screens = QApplication.screens()
    if not screens:
        return QApplication.desktop().screenGeometry()

    geometry = QRect(screens[0].geometry())
    for screen in screens[1:]:
        geometry = geometry.united(screen.geometry())
    return geometry


def screen_for_rect(rect):
    screen = QApplication.screenAt(rect.center())
    if screen:
        return screen
    return QApplication.primaryScreen()


def capture_screen_region(rect):
    screen = screen_for_rect(rect)
    screens = QApplication.screens()
    screen_index = screens.index(screen) if screen in screens else 0
    screen_geometry = screen.geometry()
    scale = screen.devicePixelRatio()

    mss_factory = getattr(mss, "MSS", mss.mss)
    with mss_factory() as sct:
        mss_monitor = (
            sct.monitors[screen_index + 1]
            if screen_index + 1 < len(sct.monitors)
            else sct.monitors[0]
        )
        monitor = {
            "top": mss_monitor["top"] + round((rect.top() - screen_geometry.top()) * scale),
            "left": mss_monitor["left"] + round((rect.left() - screen_geometry.left()) * scale),
            "width": max(1, round(rect.width() * scale)),
            "height": max(1, round(rect.height() * scale)),
        }
        image = sct.grab(monitor)
        return mss.tools.to_png(image.rgb, image.size), scale


def paragraph_text(paragraph):
    parts = []
    for word in paragraph.words:
        for symbol in word.symbols:
            parts.append(symbol.text)
            detected_break = getattr(getattr(symbol, "property", None), "detected_break", None)
            break_type = getattr(detected_break, "type_", 0)
            if break_type in (1, 2, 3, 5):
                parts.append(" ")

    return " ".join("".join(parts).split())


def bounds_to_rect(bounds, scale):
    vertices = list(bounds.vertices)
    if not vertices:
        return QRect()

    xs = [getattr(vertex, "x", 0) for vertex in vertices]
    ys = [getattr(vertex, "y", 0) for vertex in vertices]
    left = round(min(xs) / scale)
    top = round(min(ys) / scale)
    right = round(max(xs) / scale)
    bottom = round(max(ys) / scale)
    return QRect(left, top, max(1, right - left), max(1, bottom - top))


def horizontal_overlap_ratio(first, second):
    overlap = max(0, min(first.right(), second.right()) - max(first.left(), second.left()))
    return overlap / max(1, min(first.width(), second.width()))


def vertical_overlap_ratio(first, second):
    overlap = max(0, min(first.bottom(), second.bottom()) - max(first.top(), second.top()))
    return overlap / max(1, min(first.height(), second.height()))


def rect_gap(first, second):
    horizontal = max(0, max(first.left(), second.left()) - min(first.right(), second.right()))
    vertical = max(0, max(first.top(), second.top()) - min(first.bottom(), second.bottom()))
    return horizontal, vertical


def should_merge_regions(first, second):
    first_rect = first.source_rect
    second_rect = second.source_rect
    horizontal_gap, vertical_gap = rect_gap(first_rect, second_rect)

    same_column = (
        horizontal_overlap_ratio(first_rect, second_rect) >= 0.25
        and vertical_gap <= max(18, min(first_rect.height(), second_rect.height()))
    )
    same_line = (
        vertical_overlap_ratio(first_rect, second_rect) >= 0.45
        and horizontal_gap <= max(16, min(first_rect.width(), second_rect.width()) // 3)
    )
    return same_column or same_line


def merge_nearby_regions(regions):
    merged = []
    for region in sorted(regions, key=lambda item: (item.source_rect.top(), item.source_rect.left())):
        target = None
        for candidate in merged:
            if should_merge_regions(candidate, region):
                target = candidate
                break

        if target:
            target.original = f"{target.original} {region.original}".strip()
            target.source_rect = target.source_rect.united(region.source_rect)
        else:
            merged.append(TextRegion(region.original, QRect(region.source_rect)))

    return merged


def keep_rect_visible(rect):
    screen_geometry = virtual_screen_geometry()
    rect = QRect(rect)

    if rect.right() > screen_geometry.right():
        rect.moveRight(screen_geometry.right())
    if rect.bottom() > screen_geometry.bottom():
        rect.moveBottom(screen_geometry.bottom())
    if rect.left() < screen_geometry.left():
        rect.moveLeft(screen_geometry.left())
    if rect.top() < screen_geometry.top():
        rect.moveTop(screen_geometry.top())

    return rect


def contains_script(text, source_label):
    for char in text:
        codepoint = ord(char)
        if source_label == "JP":
            if (
                0x3040 <= codepoint <= 0x30FF
                or 0x3400 <= codepoint <= 0x9FFF
                or 0xF900 <= codepoint <= 0xFAFF
            ):
                return True
        elif source_label == "KR":
            if 0xAC00 <= codepoint <= 0xD7AF or 0x1100 <= codepoint <= 0x11FF:
                return True
        elif source_label == "CH":
            if 0x3400 <= codepoint <= 0x9FFF and not contains_script(text, "JP_KANA"):
                return True
        elif source_label == "TH":
            if 0x0E00 <= codepoint <= 0x0E7F:
                return True
        elif source_label == "EN":
            if "A" <= char <= "Z" or "a" <= char <= "z":
                return True
        elif source_label == "JP_KANA":
            if 0x3040 <= codepoint <= 0x30FF:
                return True
    return False


def has_any_letter(text):
    return any(category(char).startswith("L") for char in text)


def should_translate_text(text, settings):
    if not has_any_letter(text):
        return False
    if settings.source_code and settings.source_code == settings.target_code:
        return False
    if settings.source_label == "AUTO":
        return True
    return contains_script(text, settings.source_label)


def translation_text_cache_key(settings, text):
    return json.dumps(
        {
            "engine": settings.engine_index,
            "source": settings.source_label,
            "target": settings.target_code,
            "text": text,
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def startup_check_items(control_panel):
    settings = control_panel.current_translation_settings()
    credentials_path = os.environ.get(GOOGLE_CREDENTIALS_ENV)
    local_credentials = find_local_credentials()
    credential_ready = bool(
        (credentials_path and Path(credentials_path).exists()) or local_credentials
    )

    api_ready = True
    api_detail = control_panel.t("check_api_not_required")
    if settings.engine_index in (1, 2, 3):
        api_ready = bool(settings.api_key)
        api_detail = control_panel.t("check_api_ready") if api_ready else control_panel.t("check_api_missing")
    elif settings.engine_index == 4:
        api_detail = control_panel.t("check_gateway")

    return [
        (
            credential_ready,
            control_panel.t("check_credential_title"),
            control_panel.t("check_credential_ready") if credential_ready else control_panel.t("check_credential_missing"),
        ),
        (
            True,
            control_panel.t("check_engine_title"),
            settings.engine_name,
        ),
        (
            api_ready,
            control_panel.t("check_api_key_title"),
            api_detail,
        ),
        (
            True,
            control_panel.t("check_language_title"),
            f"{settings.source_label} -> {settings.target_name}",
        ),
        (
            True,
            control_panel.t("check_cache_title"),
            control_panel.t("check_cache_detail"),
        ),
        (
            True,
            control_panel.t("check_hotkeys_title"),
            control_panel.t("check_hotkeys_detail"),
        ),
    ]


def build_startup_checklist_html(control_panel):
    rows = []
    language = control_panel.current_ui_language()
    for ok, title, detail in startup_check_items(control_panel):
        icon = "OK" if ok else ui_text(language, "check_needs_setup")
        color = "#8fd694" if ok else "#ffb86b"
        rows.append(
            f'<p style="margin:6px 0;"><b style="color:{color};">{escape(icon)}</b> '
            f'<b>{escape(title)}</b><br><span>{escape(detail)}</span></p>'
        )
    return "".join(rows)


def startup_has_required_items(control_panel):
    return all(ok for ok, _, _ in startup_check_items(control_panel)[:3])


def should_show_onboarding(control_panel):
    state = load_json_file(onboarding_state_path(), default={}) or {}
    if not startup_has_required_items(control_panel):
        return True
    return not state.get("hide_when_ready", False)


def show_onboarding_if_needed(control_panel):
    if not should_show_onboarding(control_panel):
        return

    dialog = FirstRunDialog(control_panel, control_panel)
    dialog.exec_()
    if dialog.should_skip_next_time() and startup_has_required_items(control_panel):
        save_json_file(
            onboarding_state_path(),
            {
                "hide_when_ready": True,
                "version": 1,
            },
        )


def text_units(text):
    units = []
    current = ""
    for char in text:
        if not current or category(char).startswith("M"):
            current += char
        else:
            units.append(current)
            current = char
    if current:
        units.append(current)
    return units


def split_long_token(token, metrics, max_width):
    lines = []
    current = ""
    for unit in text_units(token):
        candidate = current + unit
        if not current or metrics.horizontalAdvance(candidate) <= max_width:
            current = candidate
            continue

        lines.append(current)
        current = unit

    if current:
        lines.append(current)
    return lines


def wrap_text_lines(text, font, max_width):
    metrics = QFontMetrics(font)
    wrap_limit = max(10, max_width - 8)  # 8px safety margin to avoid QPainter accidental wraps
    lines = []

    for paragraph in text.splitlines() or [text]:
        # Tokenize paragraph using pythainlp if available
        use_pythainlp = HAS_PYTHAINLP
        words = []
        if use_pythainlp:
            try:
                words = word_tokenize(paragraph)
            except Exception:
                use_pythainlp = False

        if not use_pythainlp:
            words = paragraph.split()

        if not words:
            lines.append("")
            continue

        current = ""
        for word in words:
            if use_pythainlp:
                candidate = current + word
            else:
                candidate = f"{current} {word}" if current else word

            # Measure width of candidate (strip for measurement to ignore trailing whitespace impact)
            measured_candidate = candidate.strip()
            if not measured_candidate or metrics.horizontalAdvance(measured_candidate) <= wrap_limit:
                current = candidate
                continue

            # If it doesn't fit, commit current line
            if current:
                stripped_current = current.strip()
                if stripped_current:
                    lines.append(stripped_current)
                current = ""

            # Ignore leading spaces on the new line
            if word.strip() == "":
                continue

            # Measure word itself
            if metrics.horizontalAdvance(word.strip()) <= wrap_limit:
                current = word
            else:
                # If a single word is too long to fit, split it character-by-character
                broken = split_long_token(word, metrics, wrap_limit)
                for part in broken[:-1]:
                    stripped_part = part.strip()
                    if stripped_part:
                        lines.append(stripped_part)
                current = broken[-1] if broken else ""

        if current:
            stripped_current = current.strip()
            if stripped_current:
                lines.append(stripped_current)

    return lines


def wrapped_text(text, font, max_width):
    return "\n".join(wrap_text_lines(text, font, max_width))


def text_box_size(source_rect, text, font):
    metrics = QFontMetrics(font)
    natural_width = max(
        metrics.horizontalAdvance(line)
        for line in (text.splitlines() or [text])
    ) + (OVERLAY_PADDING * 2)
    width = max(
        MIN_OVERLAY_WIDTH,
        min(MAX_OVERLAY_WIDTH, max(source_rect.width() + 120, natural_width)),
    )
    if len(text) > 45:
        width = min(MAX_OVERLAY_WIDTH, max(width, 300))
    if len(text) > 90:
        width = MAX_OVERLAY_WIDTH

    text_width = width - (OVERLAY_PADDING * 2)
    lines = wrap_text_lines(text, font, text_width)
    line_height = metrics.lineSpacing()
    height = max(MIN_OVERLAY_HEIGHT, (line_height * max(1, len(lines))) + (OVERLAY_PADDING * 2))
    return width, min(height, MAX_OVERLAY_HEIGHT)


def padded_intersects(rect, others, padding=6):
    padded = QRect(rect).adjusted(-padding, -padding, padding, padding)
    return any(padded.intersects(other) for other in others)


def candidate_overlay_rects(source_rect, width, height):
    margin = OVERLAY_MARGIN
    center_x = source_rect.center().x() - (width // 2)
    return [
        QRect(source_rect.right() + margin, source_rect.top(), width, height),
        QRect(source_rect.left() - width - margin, source_rect.top(), width, height),
        QRect(center_x, source_rect.bottom() + margin, width, height),
        QRect(center_x, source_rect.top() - height - margin, width, height),
        QRect(source_rect.right() + margin, source_rect.bottom() + margin, width, height),
        QRect(source_rect.left() - width - margin, source_rect.bottom() + margin, width, height),
        QRect(source_rect.right() + margin, source_rect.top() - height - margin, width, height),
        QRect(source_rect.left() - width - margin, source_rect.top() - height - margin, width, height),
    ]


def place_overlay_regions(regions, overlay_style=None):
    overlay_style = overlay_style or OverlayStyle()
    font = QFont("Segoe UI", overlay_style.font_size, QFont.Bold)
    source_rects = [region.source_rect for region in regions]
    placed_rects = []

    for region in sorted(regions, key=lambda item: (item.source_rect.top(), item.source_rect.left())):
        text = region.translated or region.original
        width, height = text_box_size(region.source_rect, text, font)
        chosen = None

        for candidate in candidate_overlay_rects(region.source_rect, width, height):
            candidate = keep_rect_visible(candidate)
            if padded_intersects(candidate, placed_rects):
                continue
            if padded_intersects(candidate, source_rects):
                continue
            chosen = candidate
            break

        if chosen is None:
            chosen = keep_rect_visible(
                QRect(
                    region.source_rect.left(),
                    region.source_rect.top(),
                    width,
                    height,
                )
            )

        region.overlay_rect = chosen
        placed_rects.append(chosen)

    return regions


class Communicate(QObject):
    crop_requested = pyqtSignal()
    hide_requested = pyqtSignal()
    job_ready = pyqtSignal(object)
    job_failed = pyqtSignal(str)
    job_finished = pyqtSignal()
    translation_ready = pyqtSignal(object)


class FirstRunDialog(QDialog):
    def __init__(self, control_panel, parent=None):
        super().__init__(parent)
        self.control_panel = control_panel
        self.setWindowTitle(self.control_panel.t("first_run_title"))
        self.setMinimumWidth(560)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.title_label = QLabel()
        self.title_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        layout.addWidget(self.title_label)

        self.description_label = QLabel()
        self.description_label.setWordWrap(True)
        layout.addWidget(self.description_label)

        self.checklist_label = QLabel()
        self.checklist_label.setTextFormat(Qt.RichText)
        self.checklist_label.setWordWrap(True)
        layout.addWidget(self.checklist_label)

        credential_actions = QHBoxLayout()
        self.import_credentials_button = QPushButton("Import google_credentials.json")
        self.credentials_help_button = QPushButton()
        credential_actions.addWidget(self.import_credentials_button)
        credential_actions.addWidget(self.credentials_help_button)
        layout.addLayout(credential_actions)

        self.skip_checkbox = QCheckBox()
        layout.addWidget(self.skip_checkbox)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

        self.import_credentials_button.clicked.connect(self.import_credentials)
        self.credentials_help_button.clicked.connect(
            lambda: show_google_credentials_help(self, self.control_panel.current_ui_language())
        )
        self.apply_language()
        self.refresh()

    def apply_language(self):
        self.setWindowTitle(self.control_panel.t("first_run_title"))
        self.title_label.setText(self.control_panel.t("first_run_heading"))
        self.description_label.setText(self.control_panel.t("first_run_description"))
        self.credentials_help_button.setText(self.control_panel.t("credentials_help_button"))
        self.skip_checkbox.setText(self.control_panel.t("skip_ready"))

    def refresh(self):
        self.apply_language()
        self.checklist_label.setText(build_startup_checklist_html(self.control_panel))

    def should_skip_next_time(self):
        return self.skip_checkbox.isChecked()

    def import_credentials(self):
        if import_google_credentials_with_dialog(self, self.control_panel.current_ui_language()):
            self.refresh()
            if hasattr(self.control_panel, "refresh_credentials_status"):
                self.control_panel.refresh_credentials_status()


class ControlPanelWindow(QWidget):
    overlay_style_changed = pyqtSignal(object)

    def __init__(self):
        self.is_loading = True
        super().__init__()
        self.setWindowTitle(APP_NAME)
        icon_path = resource_path("icon.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        self.setMinimumSize(450, 600)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        self.info_label = QLabel("กด 'F9' เพื่อเลือกพื้นที่ | กด 'Esc' เพื่อปิดคำแปล")
        self.info_label.setFont(QFont("Segoe UI", 11))
        self.info_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.info_label)

        self.crop_button = QPushButton("เลือกพื้นที่เพื่อแปล (F9)")
        self.crop_button.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.crop_button.setMinimumHeight(40)
        self.layout.addWidget(self.crop_button)

        credential_actions = QHBoxLayout()
        self.import_credentials_button = QPushButton("Import google_credentials.json")
        self.credentials_help_button = QPushButton("วิธีเอาไฟล์ Google")
        credential_actions.addWidget(self.import_credentials_button)
        credential_actions.addWidget(self.credentials_help_button)
        self.layout.addLayout(credential_actions)

        self.credentials_status_label = QLabel()
        self.credentials_status_label.setFont(QFont("Segoe UI", 9))
        self.credentials_status_label.setWordWrap(True)
        self.layout.addWidget(self.credentials_status_label)

        self.continuous_checkbox = QCheckBox("Continuous mode: watch the latest area")
        self.continuous_checkbox.setFont(QFont("Segoe UI", 10))
        self.layout.addWidget(self.continuous_checkbox)

        # Settings Widget for Translation Engine & API Key
        self.settings_widget = QWidget()
        self.settings_layout = QFormLayout(self.settings_widget)
        self.settings_layout.setContentsMargins(0, 0, 0, 0)
        self.settings_layout.setSpacing(10)
        self.settings_labels = {}

        self.ui_language_combo = QComboBox()
        self.ui_language_combo.addItem("English", "en")
        self.ui_language_combo.addItem("ไทย", "th")
        self.ui_language_combo.setFont(QFont("Segoe UI", 10))
        self.settings_layout.addRow("UI language:", self.ui_language_combo)
        self.settings_labels["ui_language"] = self.settings_layout.labelForField(self.ui_language_combo)

        self.engine_combo = QComboBox()
        self.engine_combo.addItems([
            "Google Translate (เดิม)",
            "9arm API (Qwen3.6)",
            "9arm API (Gemma)",
            "Gemini API (Google)",
            "API Gateway (Local)"
        ])
        self.engine_combo.setFont(QFont("Segoe UI", 10))
        self.settings_layout.addRow("ระบบแปลภาษา:", self.engine_combo)
        self.settings_labels["engine_label"] = self.settings_layout.labelForField(self.engine_combo)

        self.source_lang_combo = QComboBox()
        self.source_lang_combo.addItems(["AUTO", "JP", "EN", "KR", "CH", "TH"])
        self.source_lang_combo.setFont(QFont("Segoe UI", 10))
        self.settings_layout.addRow("ภาษาต้นทาง:", self.source_lang_combo)
        self.settings_labels["source_label"] = self.settings_layout.labelForField(self.source_lang_combo)

        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["TH", "EN", "JP", "KR", "CH"])
        self.lang_combo.setFont(QFont("Segoe UI", 10))
        self.settings_layout.addRow("ภาษาปลายทาง:", self.lang_combo)
        self.settings_labels["target_label"] = self.settings_layout.labelForField(self.lang_combo)

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("ใส่ API Key...")
        self.api_key_input.setFont(QFont("Segoe UI", 10))
        self.api_key_input.setEchoMode(QLineEdit.Password)

        self.show_key_checkbox = QCheckBox("แสดงคีย์")
        self.show_key_checkbox.setFont(QFont("Segoe UI", 9))
        self.show_key_checkbox.toggled.connect(
            lambda checked: self.api_key_input.setEchoMode(
                QLineEdit.Normal if checked else QLineEdit.Password
            )
        )

        key_layout = QVBoxLayout()
        key_layout.addWidget(self.api_key_input)
        key_layout.addWidget(self.show_key_checkbox)
        self.settings_layout.addRow("API Key:", key_layout)
        self.settings_labels["api_key"] = self.settings_layout.labelForField(key_layout)

        self.overlay_font_size_input = QSpinBox()
        self.overlay_font_size_input.setRange(9, 32)
        self.overlay_font_size_input.setSingleStep(1)
        self.overlay_font_size_input.setValue(14)
        self.overlay_font_size_input.setSuffix(" px")
        self.overlay_font_size_input.setFont(QFont("Segoe UI", 10))
        self.settings_layout.addRow("ขนาดตัวอักษรคำแปล:", self.overlay_font_size_input)
        self.settings_labels["font_size_label"] = self.settings_layout.labelForField(self.overlay_font_size_input)

        opacity_layout = QHBoxLayout()
        self.overlay_opacity_slider = QSlider(Qt.Horizontal)
        self.overlay_opacity_slider.setRange(20, 100)
        self.overlay_opacity_slider.setSingleStep(5)
        self.overlay_opacity_slider.setPageStep(10)
        self.overlay_opacity_slider.setValue(88)
        self.overlay_opacity_value_label = QLabel("88%")
        self.overlay_opacity_value_label.setMinimumWidth(42)
        opacity_layout.addWidget(self.overlay_opacity_slider)
        opacity_layout.addWidget(self.overlay_opacity_value_label)
        self.settings_layout.addRow("ความทึบพื้นหลังคำแปล:", opacity_layout)
        self.settings_labels["opacity_label"] = self.settings_layout.labelForField(opacity_layout)

        self.layout.addWidget(self.settings_widget)

        self.status_label = QLabel("Ready")
        self.status_label.setFont(QFont("Segoe UI", 9))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.status_label)

        self.title_label = QLabel("บันทึกคำแปลล่าสุด")
        self.title_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.layout.addWidget(self.title_label)

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Segoe UI", 10))
        self.layout.addWidget(self.log_display)

        # Connect settings events and load existing config
        self.ui_language_combo.currentIndexChanged.connect(self.apply_ui_language)
        self.ui_language_combo.currentIndexChanged.connect(self.save_settings)
        self.engine_combo.currentIndexChanged.connect(self.toggle_api_key_visibility)
        self.engine_combo.currentIndexChanged.connect(self.save_settings)
        self.source_lang_combo.currentIndexChanged.connect(self.save_settings)
        self.lang_combo.currentIndexChanged.connect(self.save_settings)
        self.api_key_input.textChanged.connect(self.save_settings)
        self.overlay_font_size_input.valueChanged.connect(self.save_settings)
        self.overlay_opacity_slider.valueChanged.connect(self.update_opacity_label)
        self.overlay_opacity_slider.valueChanged.connect(self.save_settings)
        self.import_credentials_button.clicked.connect(self.import_credentials)
        self.credentials_help_button.clicked.connect(
            lambda: show_google_credentials_help(self, self.current_ui_language())
        )
        self.load_settings()
        self.refresh_credentials_status()
        self.is_loading = False

    def load_settings(self):
        config_path = user_data_path("config.json")
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    engine = data.get("engine", "google")
                    api_key = data.get("gemini_api_key", "")
                    ui_language = data.get("ui_language", DEFAULT_UI_LANGUAGE)
                    source_lang = data.get("source_lang", "AUTO")
                    target_lang = data.get("target_lang", "TH")
                    overlay_font_size = clamp_int(
                        data.get("overlay_font_size", 14), 9, 32, 14
                    )
                    overlay_opacity = clamp_int(
                        data.get("overlay_background_opacity", 88), 20, 100, 88
                    )
                    
                    if engine == "9arm_qwen":
                        self.engine_combo.setCurrentIndex(1)
                    elif engine == "9arm_gemma":
                        self.engine_combo.setCurrentIndex(2)
                    elif engine == "gemini":
                        self.engine_combo.setCurrentIndex(3)
                    elif engine == "api_gateway":
                        self.engine_combo.setCurrentIndex(4)
                    else:
                        self.engine_combo.setCurrentIndex(0)
                    self.api_key_input.setText(api_key)

                    language_index = self.ui_language_combo.findData(ui_language)
                    if language_index >= 0:
                        self.ui_language_combo.setCurrentIndex(language_index)

                    source_index = self.source_lang_combo.findText(source_lang)
                    if source_index >= 0:
                        self.source_lang_combo.setCurrentIndex(source_index)
                    
                    lang_index = self.lang_combo.findText(target_lang)
                    if lang_index >= 0:
                        self.lang_combo.setCurrentIndex(lang_index)

                    self.overlay_font_size_input.setValue(overlay_font_size)
                    self.overlay_opacity_slider.setValue(overlay_opacity)
            except Exception as e:
                logging.error(f"Failed to load settings: {e}")
        self.toggle_api_key_visibility()
        self.update_opacity_label()
        self.apply_ui_language()

    def save_settings(self):
        config_path = user_data_path("config.json")
        engine_idx = self.engine_combo.currentIndex()
        if engine_idx == 1:
            engine, engine_name = "9arm_qwen", "9arm API (Qwen3.6)"
        elif engine_idx == 2:
            engine, engine_name = "9arm_gemma", "9arm API (Gemma)"
        elif engine_idx == 3:
            engine, engine_name = "gemini", "Gemini API (Google)"
        elif engine_idx == 4:
            engine, engine_name = "api_gateway", "API Gateway (Local)"
        else:
            engine = "google"
            engine_name = "Google Translate (เดิม)"
            
        api_key = self.api_key_input.text().strip()
        ui_language = self.current_ui_language()
        source_lang = self.source_lang_combo.currentText()
        target_lang = self.lang_combo.currentText()
        overlay_font_size = self.overlay_font_size_input.value()
        overlay_opacity = self.overlay_opacity_slider.value()
        data = {
            "engine": engine,
            "gemini_api_key": api_key,
            "ui_language": ui_language,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "overlay_font_size": overlay_font_size,
            "overlay_background_opacity": overlay_opacity,
        }
        try:
            temp_path = config_path.with_suffix(".json.tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            os.replace(temp_path, config_path)
            if not getattr(self, "is_loading", False):
                self.set_status(self.t("settings_saved"))
                self.overlay_style_changed.emit(self.current_overlay_style())
                logging.info(f"Engine changed to: {engine_name}")
        except Exception as e:
            logging.error(f"Failed to save settings: {e}")

    def toggle_api_key_visibility(self):
        needs_key = self.engine_combo.currentIndex() in (1, 2, 3)
        self.api_key_input.setEnabled(needs_key)
        self.show_key_checkbox.setEnabled(needs_key)

    def current_ui_language(self):
        return self.ui_language_combo.currentData() or DEFAULT_UI_LANGUAGE

    def t(self, key, **kwargs):
        return ui_text(self.current_ui_language(), key, **kwargs)

    def apply_ui_language(self, *_):
        if not hasattr(self, "info_label"):
            return

        self.info_label.setText(self.t("select_area_hint"))
        self.crop_button.setText(self.t("select_area_button"))
        self.credentials_help_button.setText(self.t("credentials_help_button"))
        self.continuous_checkbox.setText(self.t("continuous_mode"))
        self.api_key_input.setPlaceholderText(self.t("api_key_placeholder"))
        self.show_key_checkbox.setText(self.t("show_key"))
        self.title_label.setText(self.t("latest_log"))

        label_map = {
            "ui_language": "ui_language",
            "engine_label": "engine_label",
            "source_label": "source_label",
            "target_label": "target_label",
            "font_size_label": "font_size_label",
            "opacity_label": "opacity_label",
        }
        for label_key, text_key in label_map.items():
            label = self.settings_labels.get(label_key)
            if label:
                label.setText(self.t(text_key))

        api_label = self.settings_labels.get("api_key")
        if api_label:
            api_label.setText("API Key:")

        self.refresh_credentials_status()

    def current_translation_settings(self):
        engine_idx = self.engine_combo.currentIndex()
        source_lang = self.source_lang_combo.currentText()
        target_lang = self.lang_combo.currentText()
        source_info = LANG_MAP.get(source_lang, LANG_MAP["AUTO"])
        target_info = LANG_MAP.get(target_lang, LANG_MAP["TH"])
        return TranslationSettings(
            engine_index=engine_idx,
            engine_name=self.engine_combo.currentText(),
            source_label=source_lang,
            source_code=source_info["code"],
            source_name=source_info["name"],
            target_code=target_info["code"],
            target_name=target_info["name"],
            api_key=self.api_key_input.text().strip(),
        )

    def update_opacity_label(self):
        self.overlay_opacity_value_label.setText(f"{self.overlay_opacity_slider.value()}%")

    def current_overlay_style(self):
        opacity_percent = self.overlay_opacity_slider.value()
        return OverlayStyle(
            font_size=self.overlay_font_size_input.value(),
            background_opacity=round(255 * opacity_percent / 100),
        )

    def refresh_credentials_status(self):
        credentials_path = os.environ.get(GOOGLE_CREDENTIALS_ENV)
        local_credentials = find_local_credentials()
        if credentials_path and Path(credentials_path).exists():
            active_path = Path(credentials_path)
        else:
            active_path = local_credentials

        if active_path:
            self.credentials_status_label.setText(
                self.t("credential_ready", name=active_path.name)
            )
        else:
            self.credentials_status_label.setText(
                self.t("credential_missing")
            )

    def import_credentials(self):
        if import_google_credentials_with_dialog(self, self.current_ui_language()):
            self.refresh_credentials_status()

    def add_page_to_log(self, regions):
        if not regions:
            return

        engine_name = self.engine_combo.currentText()
        lines = [self.t("log_heading", engine=engine_name)]
        for index, region in enumerate(regions, 1):
            lines.append(f"{index}. {self.t('log_original')}: {region.original}")
            lines.append(f"   {self.t('log_translation')}: {region.translated}")
        lines.append("-" * 50)
        log_entry = "\n".join(lines)
        self.log_display.append(log_entry)

    def set_status(self, message):
        self.status_label.setText(message)


class TextBubbleOverlay(QWidget):
    def __init__(self, region, overlay_style=None, parent=None):
        super().__init__(parent)
        self.region = region
        self.overlay_style = overlay_style or OverlayStyle()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setMouseTracking(True)
        self.setMinimumSize(100, 45)
        
        self.drag_position = None
        self.resize_zone = 0
        self.initial_geometry = None
        self.overlay_font = QFont("Segoe UI", self.overlay_style.font_size, QFont.Bold)
        self.setGeometry(region.overlay_rect)

    def apply_style(self, overlay_style):
        self.overlay_style = overlay_style
        self.overlay_font = QFont("Segoe UI", self.overlay_style.font_size, QFont.Bold)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setFont(self.overlay_font)

        box = self.rect()
        text_rect = box.adjusted(
            OVERLAY_PADDING,
            OVERLAY_PADDING,
            -OVERLAY_PADDING,
            -OVERLAY_PADDING,
        )
        painter.setBrush(QColor(0, 0, 0, self.overlay_style.background_opacity))
        painter.setPen(QPen(QColor(255, 255, 255, 100), 1))
        painter.drawRoundedRect(box, 8, 8)
        
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(
            text_rect,
            Qt.AlignCenter,
            wrapped_text(self.region.translated, self.overlay_font, text_rect.width()),
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            rect = self.rect()
            border = 8
            
            self.resize_zone = 0
            if pos.x() < border:
                self.resize_zone |= 1  # LEFT
            elif pos.x() > rect.width() - border:
                self.resize_zone |= 2  # RIGHT
                
            if pos.y() < border:
                self.resize_zone |= 4  # TOP
            elif pos.y() > rect.height() - border:
                self.resize_zone |= 8  # BOTTOM
                
            self.drag_position = event.globalPos()
            self.initial_geometry = self.geometry()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            if self.drag_position is None:
                return
                
            delta = event.globalPos() - self.drag_position
            new_geom = QRect(self.initial_geometry)
            
            if self.resize_zone == 0:
                # Dragging mode (move window)
                new_geom.translate(delta)
                self.setGeometry(new_geom)
                self.region.overlay_rect = self.geometry()
            else:
                # Resizing mode
                min_w = 100
                min_h = 45
                
                # Left
                if self.resize_zone & 1:
                    new_left = self.initial_geometry.left() + delta.x()
                    if new_left > self.initial_geometry.right() - min_w:
                        new_left = self.initial_geometry.right() - min_w
                    new_geom.setLeft(new_left)
                # Right
                elif self.resize_zone & 2:
                    new_right = self.initial_geometry.right() + delta.x()
                    if new_right < self.initial_geometry.left() + min_w:
                        new_right = self.initial_geometry.left() + min_w
                    new_geom.setRight(new_right)
                    
                # Top
                if self.resize_zone & 4:
                    new_top = self.initial_geometry.top() + delta.y()
                    if new_top > self.initial_geometry.bottom() - min_h:
                        new_top = self.initial_geometry.bottom() - min_h
                    new_geom.setTop(new_top)
                # Bottom
                elif self.resize_zone & 8:
                    new_bottom = self.initial_geometry.bottom() + delta.y()
                    if new_bottom < self.initial_geometry.top() + min_h:
                        new_bottom = self.initial_geometry.top() + min_h
                    new_geom.setBottom(new_bottom)
                    
                self.setGeometry(new_geom)
                self.region.overlay_rect = self.geometry()
            event.accept()
        else:
            # Change cursor shape on hover
            pos = event.pos()
            rect = self.rect()
            border = 8
            
            zone = 0
            if pos.x() < border:
                zone |= 1
            elif pos.x() > rect.width() - border:
                zone |= 2
                
            if pos.y() < border:
                zone |= 4
            elif pos.y() > rect.height() - border:
                zone |= 8
                
            if zone == 5 or zone == 10:  # TOP|LEFT or BOTTOM|RIGHT
                self.setCursor(Qt.SizeFDiagCursor)
            elif zone == 6 or zone == 9:  # TOP|RIGHT or BOTTOM|LEFT
                self.setCursor(Qt.SizeBDiagCursor)
            elif zone & 3:  # LEFT or RIGHT
                self.setCursor(Qt.SizeHorCursor)
            elif zone & 12:  # TOP or BOTTOM
                self.setCursor(Qt.SizeVerCursor)
            else:
                self.setCursor(Qt.ArrowCursor)

    def mouseReleaseEvent(self, event):
        self.drag_position = None
        self.resize_zone = 0


class OverlayWindow(QObject):
    def __init__(self):
        super().__init__()
        self.bubbles = []
        self.overlay_style = OverlayStyle()

    def apply_style(self, overlay_style):
        self.overlay_style = overlay_style
        for bubble in self.bubbles:
            bubble.apply_style(overlay_style)

    def update_translations(self, regions):
        # We want to map each new region to a previous bubble to reuse its geometry
        assigned_bubbles = set()
        new_geometries = {} # map of id(region) -> QRect
        
        # 1. Match by source_rect overlap
        for region in regions:
            best_bubble = None
            best_overlap = 0.0
            for bubble in self.bubbles:
                if bubble in assigned_bubbles or not bubble.isVisible():
                    continue
                intersection = region.source_rect.intersected(bubble.region.source_rect)
                if not intersection.isEmpty():
                    area_int = intersection.width() * intersection.height()
                    area_new = region.source_rect.width() * region.source_rect.height()
                    area_old = bubble.region.source_rect.width() * bubble.region.source_rect.height()
                    overlap = area_int / max(1, min(area_new, area_old))
                    if overlap > best_overlap and overlap > 0.3:
                        best_overlap = overlap
                        best_bubble = bubble
            if best_bubble:
                new_geometries[id(region)] = best_bubble.geometry()
                assigned_bubbles.add(best_bubble)
                
        # 2. Match remaining by distance
        for region in regions:
            if id(region) in new_geometries:
                continue
            best_bubble = None
            best_dist = 100000.0
            for bubble in self.bubbles:
                if bubble in assigned_bubbles or not bubble.isVisible():
                    continue
                dist = (region.source_rect.center() - bubble.region.source_rect.center()).manhattanLength()
                if dist < best_dist and dist < 150:
                    best_dist = dist
                    best_bubble = bubble
            if best_bubble:
                new_geometries[id(region)] = best_bubble.geometry()
                assigned_bubbles.add(best_bubble)

        self.hide_overlay()
        
        if not regions:
            return

        for region in regions:
            if id(region) in new_geometries:
                region.overlay_rect = new_geometries[id(region)]
            
            bubble = TextBubbleOverlay(region, self.overlay_style)
            bubble.show()
            self.bubbles.append(bubble)

    def hide_overlay(self):
        for bubble in self.bubbles:
            bubble.close()
        self.bubbles.clear()


class CropWindow(QWidget):
    crop_completed = pyqtSignal(QRect)

    def __init__(self):
        super().__init__()
        self.start_pos = None
        self.end_pos = None

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setCursor(Qt.CrossCursor)
        self.setGeometry(virtual_screen_geometry())
        self.setWindowOpacity(0.3)

    def paintEvent(self, event):
        if self.start_pos and self.end_pos:
            painter = QPainter(self)
            crop_rect = QRect(self.start_pos, self.end_pos).normalized()
            painter.setPen(QPen(QColor(255, 255, 255), 2, Qt.SolidLine))
            painter.drawRect(crop_rect)

    def mousePressEvent(self, event):
        self.start_pos = event.pos()
        self.end_pos = event.pos()
        self.update()

    def mouseMoveEvent(self, event):
        self.end_pos = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        self.hide()
        crop_rect = QRect(self.start_pos, self.end_pos).normalized()
        self.crop_completed.emit(crop_rect.translated(self.geometry().topLeft()))
        self.close()


class Controller:
    def __init__(self, overlay_window, control_panel_window, google_service):
        self.overlay = overlay_window
        self.control_panel = control_panel_window
        self.google_service = google_service
        self.crop_window = None
        self.comm = Communicate()
        self.active_crop_rect = None
        self.translation_in_progress = False
        self.pending_scan = False
        self.scene_history = deque(maxlen=SCENE_HISTORY_LIMIT)
        self.translation_cache = OrderedDict()
        self.translation_text_cache = self.load_translation_text_cache()
        self.continuous_timer = QTimer()
        self.continuous_timer.setInterval(CONTINUOUS_INTERVAL_MS)

        self.comm.job_ready.connect(self.handle_job_ready)
        self.comm.job_failed.connect(self.handle_job_failed)
        self.comm.job_finished.connect(self.handle_job_finished)
        self.comm.translation_ready.connect(self.overlay.update_translations)
        self.comm.translation_ready.connect(self.control_panel.add_page_to_log)
        self.comm.crop_requested.connect(self.trigger_cropping)
        self.comm.hide_requested.connect(self.overlay.hide_overlay)
        self.control_panel.continuous_checkbox.toggled.connect(
            self.set_continuous_mode
        )
        self.control_panel.overlay_style_changed.connect(self.overlay.apply_style)
        self.overlay.apply_style(self.control_panel.current_overlay_style())
        self.continuous_timer.timeout.connect(self.scan_continuous_area)

    def trigger_cropping(self):
        if self.crop_window and self.crop_window.isVisible():
            return
        self.crop_window = CropWindow()
        self.crop_window.crop_completed.connect(self.set_translation_area)
        self.crop_window.show()

    def request_crop_from_hotkey(self):
        self.comm.crop_requested.emit()

    def request_hide_from_hotkey(self):
        self.comm.hide_requested.emit()

    def set_continuous_mode(self, enabled):
        if enabled:
            self.continuous_timer.start()
            if self.active_crop_rect:
                self.control_panel.set_status(self.control_panel.t("continuous_watching"))
            else:
                self.control_panel.set_status(self.control_panel.t("continuous_needs_area"))
        else:
            self.continuous_timer.stop()
            self.control_panel.set_status(self.control_panel.t("continuous_stopped"))

    def set_translation_area(self, crop_rect):
        logging.info("Area selected: %s", crop_rect)
        if crop_rect.width() < 5 or crop_rect.height() < 5:
            logging.info("Selected area is too small.")
            return

        self.active_crop_rect = QRect(crop_rect)
        self._last_pixels = None
        if self.translation_in_progress:
            self.pending_scan = True
            self.control_panel.set_status(self.control_panel.t("new_area_queued"))
            return

        self.scan_active_area(force=True)

    def scan_continuous_area(self):
        self.scan_active_area()

    def scan_active_area(self, force=False):
        if not self.active_crop_rect or self.translation_in_progress:
            return

        try:
            crop_rect = QRect(self.active_crop_rect)
            image_bytes, capture_scale = capture_screen_region(crop_rect)
            
            # Perceptual similarity check using downscaled grayscale image
            qimg = QImage.fromData(image_bytes)
            small_img = qimg.scaled(16, 16, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            
            current_pixels = []
            for y in range(16):
                for x in range(16):
                    color = QColor(small_img.pixel(x, y))
                    gray = int(0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue())
                    current_pixels.append(gray)
            
            if not force and hasattr(self, "_last_pixels") and self._last_pixels:
                diff = sum(abs(a - b) for a, b in zip(current_pixels, self._last_pixels)) / 256.0
                if diff < 3.0:  # Threshold: less than ~1.2% average pixel change
                    return
            
            self._last_pixels = current_pixels
            self.start_translation_job(crop_rect, image_bytes, capture_scale)
        except Exception as exc:
            self.handle_job_failed(str(exc))

    def start_translation_job(self, crop_rect, image_bytes, capture_scale):
        self.translation_in_progress = True
        self.control_panel.set_status(self.control_panel.t("reading_translating"))
        settings = self.control_panel.current_translation_settings()

        worker = Thread(
            target=self.run_translation_job,
            args=(crop_rect, image_bytes, capture_scale, settings),
            daemon=True,
        )
        worker.start()

    def run_translation_job(self, crop_rect, image_bytes, capture_scale, settings):
        try:
            regions = self.google_service.get_text_regions(
                image_bytes,
                capture_scale,
                settings.source_code,
            )
            if not regions:
                logging.info("No text found in selected area.")
                self.comm.job_ready.emit([])
                return

            for region in regions:
                region.source_rect = region.source_rect.translated(crop_rect.topLeft())

            scene_key = tuple(region.original for region in regions)
            translation_key = (
                settings.engine_index,
                settings.source_label,
                settings.target_code,
                scene_key,
            )
            translations = self.get_cached_translations(translation_key)
            if translations is None:
                # Only translate text that matches the selected source language.
                translated_map = {}
                to_translate = []
                for text in scene_key:
                    if should_translate_text(text, settings):
                        cached_translation = self.get_cached_text_translation(settings, text)
                        if cached_translation is not None:
                            translated_map[text] = cached_translation
                        elif text not in to_translate:
                            to_translate.append(text)
                    else:
                        translated_map[text] = text
                
                if to_translate:
                    engine_idx = settings.engine_index
                    target_code = settings.target_code
                    target_name = settings.target_name
                    
                    if engine_idx in (1, 2, 3, 4):
                        if engine_idx in (1, 2, 3):
                            api_key = settings.api_key
                            if not api_key:
                                raise ValueError("กรุณากรอก API Key ในช่องตั้งค่าการแปลภาษา")
                            
                            if engine_idx == 1:
                                gemini_results = self.translate_with_custom_api(to_translate, api_key, "qwen3.6-35b-a3b", target_name, settings.source_name)
                            elif engine_idx == 2:
                                gemini_results = self.translate_with_custom_api(to_translate, api_key, "diffusiongemma-26b-a4b", target_name, settings.source_name)
                            elif engine_idx == 3:
                                gemini_results = self.translate_with_gemini_api(to_translate, api_key, target_name, settings.source_name)
                        elif engine_idx == 4:
                            gemini_results = self.translate_with_api_gateway(to_translate, service="aistudio")
                    else:
                        gemini_results = self.google_service.translate_batch(
                            to_translate,
                            target_code,
                            settings.source_code,
                        )
                    
                    for text, trans in zip(to_translate, gemini_results):
                        translated_map[text] = trans
                        self.cache_text_translation(settings, text, trans)
                    self.save_translation_text_cache()
                
                # Reconstruct translations list in original order
                translations = [translated_map[text] for text in scene_key]
                self.cache_translations(translation_key, translations)

            for region, translated_text in zip(regions, translations):
                region.translated = translated_text

            self.comm.job_ready.emit(regions)
        except Exception as exc:
            self.comm.job_failed.emit(str(exc))
        finally:
            self.comm.job_finished.emit()

    def translate_with_custom_api(self, texts, api_key, model_name="qwen3.6-35b-a3b", target_name="Thai", source_name="Auto detect"):
        import urllib.request
        source_instruction = (
            "Detect the source language automatically and translate"
            if source_name == "Auto detect"
            else f"Translate from {source_name}"
        )
        prompt = (
            f"You are a professional game translator. {source_instruction} into natural, flowing {target_name}.\n"
            "The translation should match the style of a visual novel/light novel, choosing appropriate pronouns for characters.\n"
            "Maintain the context of the game. Translate the input list and return ONLY a JSON array of strings in the same order.\n"
            f"Input:\n{json.dumps(texts, ensure_ascii=False)}"
        )
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        url = "https://gateway.9arm.co/v1/chat/completions"
        
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=15) as response:
                response_data = response.read().decode('utf-8')
                response_json = json.loads(response_data)
                content = response_json["choices"][0]["message"]["content"]
            
            return parse_json_array_response(content, len(texts))
        except Exception as e:
            logging.error(f"Failed to parse API response: {e}")

        # Fallback to single translate
        fallback_translations = []
        for text in texts:
            try:
                single_prompt = (
                    f"{source_instruction} into natural {target_name} for a game:\n"
                    f"{text}"
                )
                single_payload = {
                    "model": model_name,
                    "messages": [{"role": "user", "content": single_prompt}]
                }
                req = urllib.request.Request(url, data=json.dumps(single_payload).encode('utf-8'), headers=headers, method='POST')
                with urllib.request.urlopen(req, timeout=10) as response:
                    single_response_data = response.read().decode('utf-8')
                    single_response_json = json.loads(single_response_data)
                    single_content = single_response_json["choices"][0]["message"]["content"]
                fallback_translations.append(single_content.strip())
            except Exception as e:
                logging.error(f"API fallback failed for '{text}': {e}")
                fallback_translations.append(text)
        return fallback_translations

    def translate_with_gemini_api(self, texts, api_key, target_name="Thai", source_name="Auto detect"):
        import urllib.request
        source_instruction = (
            "Detect the source language automatically and translate"
            if source_name == "Auto detect"
            else f"Translate from {source_name}"
        )
        prompt = (
            f"You are a professional game translator. {source_instruction} into natural, flowing {target_name}.\n"
            "The translation should match the style of a visual novel/light novel, choosing appropriate pronouns for characters.\n"
            "Maintain the context of the game. Translate the input list and return ONLY a JSON array of strings in the same order.\n"
            f"Input:\n{json.dumps(texts, ensure_ascii=False)}"
        )
        
        headers = {
            "Content-Type": "application/json"
        }
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=15) as response:
                response_data = response.read().decode('utf-8')
                response_json = json.loads(response_data)
                content = response_json["candidates"][0]["content"]["parts"][0]["text"]
            
            return parse_json_array_response(content, len(texts))
        except Exception as e:
            logging.error(f"Failed to parse Gemini API response: {e}")

        # Fallback to single translate
        fallback_translations = []
        for text in texts:
            try:
                single_prompt = (
                    f"{source_instruction} into natural {target_name} for a game:\n"
                    f"{text}"
                )
                single_payload = {
                    "contents": [{
                        "parts": [{
                            "text": single_prompt
                        }]
                    }]
                }
                req = urllib.request.Request(url, data=json.dumps(single_payload).encode('utf-8'), headers=headers, method='POST')
                with urllib.request.urlopen(req, timeout=10) as response:
                    single_response_data = response.read().decode('utf-8')
                    single_response_json = json.loads(single_response_data)
                    single_content = single_response_json["candidates"][0]["content"]["parts"][0]["text"]
                fallback_translations.append(single_content.strip())
            except Exception as e:
                logging.error(f"Gemini API fallback failed for '{text}': {e}")
                fallback_translations.append(text)
        return fallback_translations

    def translate_with_api_gateway(self, texts, service="aistudio"):
        import urllib.request
        url = "http://localhost:3000/api/v1/translations/"
        headers = {
            "Content-Type": "application/json"
        }
        
        results = []
        for text in texts:
            payload = {
                "service": service,
                "text": text
            }
            try:
                req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
                with urllib.request.urlopen(req, timeout=15) as response:
                    response_data = response.read().decode('utf-8')
                    response_json = json.loads(response_data)
                    translated = response_json.get("data", {}).get("result", "")
                    if translated:
                        results.append(translated)
                    else:
                        logging.error(f"API Gateway returned no result for '{text}': {response_data}")
                        results.append(text)
            except Exception as e:
                logging.error(f"API Gateway failed for '{text}': {e}")
                results.append(text)
        return results

    def load_translation_text_cache(self):
        cache_path = user_data_path(TRANSLATION_CACHE_FILE)
        cache = OrderedDict()
        if not cache_path.exists():
            return cache

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            entries = data.get("entries", {}) if isinstance(data, dict) else {}
            if isinstance(entries, dict):
                for key, value in entries.items():
                    if isinstance(key, str) and isinstance(value, str):
                        cache[key] = value
            logging.info("Loaded %s persistent translations.", len(cache))
        except Exception:
            logging.exception("Failed to load persistent translation cache.")
        return cache

    def save_translation_text_cache(self):
        cache_path = user_data_path(TRANSLATION_CACHE_FILE)
        try:
            temp_path = cache_path.with_suffix(".json.tmp")
            data = {
                "version": 1,
                "entries": dict(self.translation_text_cache),
            }
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(temp_path, cache_path)
        except Exception:
            logging.exception("Failed to save persistent translation cache.")

    def get_cached_text_translation(self, settings, text):
        key = translation_text_cache_key(settings, text)
        translation = self.translation_text_cache.get(key)
        if translation is not None:
            self.translation_text_cache.move_to_end(key)
            logging.info("Persistent translation cache hit.")
        return translation

    def cache_text_translation(self, settings, text, translation):
        if not text or not translation:
            return

        key = translation_text_cache_key(settings, text)
        self.translation_text_cache[key] = translation
        self.translation_text_cache.move_to_end(key)
        while len(self.translation_text_cache) > TRANSLATION_TEXT_CACHE_LIMIT:
            self.translation_text_cache.popitem(last=False)

    def get_cached_translations(self, scene_key):
        translations = self.translation_cache.get(scene_key)
        if translations is not None:
            self.translation_cache.move_to_end(scene_key)
            logging.info("Translation cache hit.")
        return translations

    def cache_translations(self, scene_key, translations):
        self.translation_cache[scene_key] = tuple(translations)
        self.translation_cache.move_to_end(scene_key)
        while len(self.translation_cache) > TRANSLATION_CACHE_LIMIT:
            self.translation_cache.popitem(last=False)

    def handle_job_ready(self, regions):
        if regions:
            regions = place_overlay_regions(
                regions,
                self.control_panel.current_overlay_style(),
            )
            scene_key = tuple(region.original for region in regions)
            if not self.scene_history or self.scene_history[-1] != scene_key:
                self.scene_history.append(scene_key)
            self.control_panel.set_status(
                self.control_panel.t(
                    "translated_status",
                    count=len(self.scene_history),
                    limit=SCENE_HISTORY_LIMIT,
                )
            )
        else:
            self.control_panel.set_status(self.control_panel.t("no_text_found"))

        self.comm.translation_ready.emit(regions)

    def handle_job_failed(self, message):
        self._last_pixels = None
        show_error(self.control_panel.t("translation_failed"), message)
        self.control_panel.set_status(self.control_panel.t("translation_failed"))

    def handle_job_finished(self):
        self.translation_in_progress = False
        if self.pending_scan:
            self.pending_scan = False
            self.scan_active_area(force=True)


def start_hotkey_listener(controller):
    def on_crop_activate():
        controller.request_crop_from_hotkey()

    def on_close_activate():
        controller.request_hide_from_hotkey()

    hotkeys = keyboard.GlobalHotKeys(
        {
            "<f9>": on_crop_activate,
            "<esc>": on_close_activate,
        }
    )
    hotkeys.run()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(app_stylesheet())
    migrate_user_files()

    control_panel = ControlPanelWindow()
    overlay = OverlayWindow()
    google_service = GoogleCloudService()
    controller = Controller(overlay, control_panel, google_service)

    control_panel.crop_button.clicked.connect(controller.trigger_cropping)

    listener_thread = Thread(target=start_hotkey_listener, args=(controller,), daemon=True)
    listener_thread.start()

    logging.info("%s is ready.", APP_NAME)
    control_panel.show()
    show_onboarding_if_needed(control_panel)
    sys.exit(app.exec_())
