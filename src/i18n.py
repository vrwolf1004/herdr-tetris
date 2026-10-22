"""언어 선택과 화면 문자열 로딩. 문자열은 src/locales/<언어>.json에 있다.

선택 우선순위: --lang 옵션 > HERDR_TETRIS_LANG 환경 변수 > config.json의 language > 시스템 로케일 > 영어.
"auto"는 "지정하지 않음"과 같다.
"""

import json
import locale
import os

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
LOCALE_DIR = os.path.join(SRC_DIR, "locales")
CONFIG_PATH = os.path.join(SRC_DIR, "..", "config.json")
SUPPORTED = ("en", "ko", "ja", "de", "es", "fr", "ru")
DEFAULT = "en"
# Windows 는 "Korean_Korea" 처럼 언어 이름으로 준다. 그 이름을 언어 코드로 바꾼다.
LANGUAGE_NAMES = {
    "korean": "ko",
    "japanese": "ja",
    "german": "de",
    "spanish": "es",
    "french": "fr",
    "russian": "ru",
}


def system_language():
    try:
        code = locale.getlocale()[0]
    except ValueError:
        code = None
    code = code or os.environ.get("LANG", "")
    for name, lang in LANGUAGE_NAMES.items():
        if code.lower().startswith(name):
            return lang
    prefix = code.split("_")[0].split(".")[0].lower()
    return prefix if prefix in SUPPORTED else DEFAULT


def _config_language():
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f).get("language")
    except (OSError, ValueError, AttributeError):
        return None


def resolve_language(cli_value=None):
    for value in (cli_value, os.environ.get("HERDR_TETRIS_LANG"), _config_language()):
        if value in SUPPORTED:
            return value
    return system_language()


def load_strings(lang):
    with open(os.path.join(LOCALE_DIR, lang + ".json"), encoding="utf-8") as f:
        return json.load(f)
