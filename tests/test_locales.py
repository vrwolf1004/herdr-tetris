import os
import re
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import i18n  # noqa: E402
import minesweeper  # noqa: E402
import snake  # noqa: E402

PLACEHOLDER = re.compile(r"\{(\w+)")
ALL_LANGUAGES = ("en", "ko", "ja", "de", "es", "fr", "ru")


def flatten(value, prefix=""):
    """중첩된 언어 문서를 (키 경로, 값) 목록으로 펼친다. 목록 값은 항목마다 번호를 붙인다."""
    if isinstance(value, dict):
        out = []
        for key, item in value.items():
            out.extend(flatten(item, prefix + key + "."))
        return out
    if isinstance(value, list):
        out = []
        for index, item in enumerate(value):
            out.extend(flatten(item, prefix + str(index) + "."))
        return out
    return [(prefix[:-1], value)]


class SupportedLanguagesTest(unittest.TestCase):
    def test_all_seven_languages_are_supported(self):
        self.assertEqual(set(i18n.SUPPORTED), set(ALL_LANGUAGES))

    def test_every_language_file_exists(self):
        for lang in ALL_LANGUAGES:
            self.assertTrue(os.path.exists(os.path.join(i18n.LOCALE_DIR, lang + ".json")), lang)


class LocaleKeysTest(unittest.TestCase):
    def setUp(self):
        self.english = dict(flatten(i18n.load_strings("en")))

    def test_every_language_has_every_english_key(self):
        for lang in ALL_LANGUAGES:
            keys = {key for key, _ in flatten(i18n.load_strings(lang))}
            self.assertEqual(keys, set(self.english), lang)

    def test_no_value_is_empty(self):
        for lang in ALL_LANGUAGES:
            for key, value in flatten(i18n.load_strings(lang)):
                self.assertTrue(value.strip(), (lang, key))

    def test_placeholders_match_the_english_text(self):
        for lang in ALL_LANGUAGES:
            for key, value in flatten(i18n.load_strings(lang)):
                if not isinstance(value, str):
                    continue
                wanted = sorted(PLACEHOLDER.findall(self.english[key]))
                self.assertEqual(sorted(PLACEHOLDER.findall(value)), wanted, (lang, key))

    def test_the_control_lists_have_the_same_length_as_english(self):
        for lang in ALL_LANGUAGES:
            self.assertEqual(len(i18n.load_strings(lang)["controls"]), len(i18n.load_strings("en")["controls"]), lang)


class SystemLanguageTest(unittest.TestCase):
    def test_windows_language_names_map_to_their_codes(self):
        cases = {
            "Japanese_Japan": "ja",
            "German_Germany": "de",
            "Spanish_Spain": "es",
            "French_France": "fr",
            "Russian_Russia": "ru",
            "Korean_Korea": "ko",
        }
        for name, lang in cases.items():
            with mock.patch("locale.getlocale", return_value=(name, "UTF-8")):
                self.assertEqual(i18n.system_language(), lang, name)

    def test_an_unsupported_language_still_falls_back_to_english(self):
        with mock.patch("locale.getlocale", return_value=("Italian_Italy", "UTF-8")):
            self.assertEqual(i18n.system_language(), "en")


class PanelRenderTest(unittest.TestCase):
    def test_snake_and_minesweeper_panels_render_in_every_language(self):
        import re as regex
        ansi = regex.compile(chr(27) + r"\[[0-9;]*m")
        for lang in ALL_LANGUAGES:
            text = i18n.load_strings(lang)
            snake_lines = [ansi.sub("", line) for line in snake.Snake().render(text.get("snake"))]
            mine_lines = [ansi.sub("", line) for line in minesweeper.Minesweeper().render(0, text.get("minesweeper"))]
            self.assertTrue(any(text["snake"]["title"] in line for line in snake_lines), lang)
            self.assertTrue(any(text["minesweeper"]["title"] in line for line in mine_lines), lang)


if __name__ == "__main__":
    unittest.main()
