import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import i18n  # noqa: E402


class LocaleFileTest(unittest.TestCase):
    def test_en_and_ko_have_the_same_keys(self):
        en = i18n.load_strings("en")
        ko = i18n.load_strings("ko")
        self.assertEqual(set(en), set(ko))

    def test_controls_have_the_same_number_of_lines(self):
        self.assertEqual(
            len(i18n.load_strings("en")["controls"]),
            len(i18n.load_strings("ko")["controls"]),
        )

    def test_monitor_command_strings_have_the_same_keys(self):
        en = i18n.load_strings("en")["monitor"]
        ko = i18n.load_strings("ko")["monitor"]
        self.assertEqual(set(en), set(ko))
        self.assertEqual(set(en["command_help"]), set(ko["command_help"]))

    def test_dashboard_text_is_not_in_the_language_files(self):
        for lang in ("en", "ko"):
            self.assertNotIn("log_templates", i18n.load_strings(lang)["monitor"])


class SystemLanguageTest(unittest.TestCase):
    def test_windows_korean_locale_name_maps_to_ko(self):
        with mock.patch("locale.getlocale", return_value=("Korean_Korea", "949")):
            self.assertEqual(i18n.system_language(), "ko")

    def test_posix_korean_locale_maps_to_ko(self):
        with mock.patch("locale.getlocale", return_value=("ko_KR", "UTF-8")):
            self.assertEqual(i18n.system_language(), "ko")

    def test_unsupported_locale_falls_back_to_en(self):
        with mock.patch("locale.getlocale", return_value=("ja_JP", "UTF-8")):
            self.assertEqual(i18n.system_language(), "en")

    def test_missing_locale_uses_lang_env_then_en(self):
        with mock.patch("locale.getlocale", return_value=(None, None)), mock.patch.dict(
            os.environ, {"LANG": "ko_KR.UTF-8"}
        ):
            self.assertEqual(i18n.system_language(), "ko")
        with mock.patch("locale.getlocale", return_value=(None, None)), mock.patch.dict(
            os.environ, {"LANG": ""}
        ):
            self.assertEqual(i18n.system_language(), "en")


class ResolveLanguageTest(unittest.TestCase):
    def test_cli_option_wins_over_env(self):
        with mock.patch.dict(os.environ, {"HERDR_TETRIS_LANG": "en"}):
            self.assertEqual(i18n.resolve_language("ko"), "ko")

    def test_env_wins_over_config_and_system(self):
        with mock.patch.dict(os.environ, {"HERDR_TETRIS_LANG": "ko"}), mock.patch.object(
            i18n, "_config_language", return_value="en"
        ):
            self.assertEqual(i18n.resolve_language("auto"), "ko")

    def test_old_tetris_lang_variable_is_no_longer_read(self):
        with mock.patch.dict(os.environ, {"TETRIS_LANG": "ko"}), mock.patch.object(
            i18n, "_config_language", return_value=None
        ), mock.patch.object(i18n, "system_language", return_value="en"):
            self.assertEqual(i18n.resolve_language(), "en")

    def test_config_used_when_cli_and_env_unset(self):
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(
            i18n, "_config_language", return_value="ko"
        ):
            self.assertEqual(i18n.resolve_language("auto"), "ko")

    def test_auto_or_invalid_values_fall_through_to_system(self):
        with mock.patch.dict(os.environ, {"HERDR_TETRIS_LANG": "fr"}), mock.patch.object(
            i18n, "_config_language", return_value="auto"
        ), mock.patch.object(i18n, "system_language", return_value="ko"):
            self.assertEqual(i18n.resolve_language("auto"), "ko")


if __name__ == "__main__":
    unittest.main()
