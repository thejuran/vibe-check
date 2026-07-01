"""Unit tests for config.py — the .vibe-check.toml I/O boundary (Phase 30).

These lock every fail-safe branch of the never-raise config reader: absent /
unparseable / non-UTF-8 / oversized / non-regular-file / one-bad-key /
no-tomllib, the validate-then-overlay precedence tier, and the DEGRADE-not-abort
__main__ posture (the OPPOSITE of test_score.py's TestFailClosed, which asserts a
non-zero exit — config.py must exit 0 on a broken config).

Run from repo root:
    python3 -m unittest discover -s plugins/vibe-check/scripts -p 'test_*.py'
Or from this dir:
    cd plugins/vibe-check/scripts && python3 -m unittest

NOTE: importing os/ast/subprocess/tempfile in THIS test file is fine — the
score.py import ban is scoped to score.py only. config.py's own (wider) import
guard is asserted below in TestImportSet.
"""

import ast
import json
import os
import subprocess
import sys
import tempfile
import unittest

# Make `import config` resolve when unittest discovery runs from the repo root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config  # noqa: E402  (sibling module under test)

CONFIG_PY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.py")

# The default-value shape load_config returns when everything degrades.
_DEFAULTS = {"thresholds": None, "disabled": [], "top_model": None}


def _write_config(dir_path, content):
    """Write a .vibe-check.toml (text or bytes) into dir_path; return its path."""
    path = os.path.join(dir_path, ".vibe-check.toml")
    mode = "wb" if isinstance(content, bytes) else "w"
    with open(path, mode) as fh:
        fh.write(content)
    return path


# --------------------------------------------------------------------------- #
# Fail-safe branches (CONFIG-01 / CONFIG-03) — degrade, never raise.
# --------------------------------------------------------------------------- #
class TestFailSafe(unittest.TestCase):
    def test_absent_file_silent_defaults(self):
        # Absent file => all defaults, NO warning (CONFIG-01 zero-config silence).
        values, warnings = config.load_config("/nonexistent/.vibe-check.toml")
        self.assertEqual(values, _DEFAULTS)
        self.assertEqual(warnings, [])

    def test_default_disabled_list_not_shared_across_calls(self):
        # lang-py-001: the returned `disabled` must be a FRESH list each call, not an
        # alias of the module-level default. Mutating one call's list must NOT poison
        # the default for a later call (shallow `dict(_DEFAULT_VALUES)` would leak).
        values1, _ = config.load_config("/nonexistent/.vibe-check.toml")
        values1["disabled"].append("poison")
        values2, _ = config.load_config("/also-nonexistent/.vibe-check.toml")
        self.assertEqual(values2["disabled"], [])
        # The module-level default itself must remain pristine.
        self.assertEqual(config._DEFAULT_VALUES["disabled"], [])

    def test_unparseable_defaults_plus_warning(self):
        # Malformed TOML => all defaults + exactly one warning; never raises.
        with tempfile.TemporaryDirectory() as d:
            path = _write_config(d, "this is = = not toml\n")
            values, warnings = config.load_config(path)
        self.assertEqual(values, _DEFAULTS)
        self.assertEqual(len(warnings), 1)

    def test_one_bad_key_isolated(self):
        # top_model bogus but thresholds + disabled valid => only top_model
        # defaults (with a warning naming it); the other keys still apply.
        toml = ('[review]\n'
                'thresholds = { critical = 90, warning = 80, medium = 70 }\n'
                '[agents]\n'
                'top_model = "gpt-5"\n'
                'disabled = ["language-go"]\n')
        with tempfile.TemporaryDirectory() as d:
            path = _write_config(d, toml)
            values, warnings = config.load_config(path)
        self.assertEqual(values["thresholds"],
                         {"critical": 90, "warning": 80, "medium": 70})
        self.assertEqual(values["disabled"], ["language-go"])
        self.assertIsNone(values["top_model"])
        self.assertEqual(len(warnings), 1)
        self.assertIn("top_model", warnings[0])

    def test_no_tomllib_degrades(self):
        # Force `import tomllib` to fail => defaults + 1 warning, no raise (D-01).
        saved = sys.modules.get("tomllib", "__unset__")
        sys.modules["tomllib"] = None  # `import tomllib` raises ImportError
        try:
            values, warnings = config.load_config("/whatever/.vibe-check.toml")
        finally:
            if saved == "__unset__":
                del sys.modules["tomllib"]
            else:
                sys.modules["tomllib"] = saved
        self.assertEqual(values, _DEFAULTS)
        self.assertEqual(len(warnings), 1)
        self.assertIn("tomllib", warnings[0])

    def test_non_utf8_defaults_plus_warning(self):
        # Non-UTF-8 bytes => defaults + 1 warning; tomllib raises UnicodeDecodeError
        # (NOT a TOMLDecodeError/OSError subclass) which MUST be caught (Finding #2).
        with tempfile.TemporaryDirectory() as d:
            path = _write_config(d, b"\xff\xfe x = 1")
            values, warnings = config.load_config(path)
        self.assertEqual(values, _DEFAULTS)
        self.assertEqual(len(warnings), 1)

    def test_oversized_defaults_plus_warning(self):
        # A regular file just over _MAX_CONFIG_BYTES => defaults + 1 warning,
        # NEVER parsed (the pre-parse size guard fires first — Finding #2 round-3).
        blob = b"# " + b"x" * (config._MAX_CONFIG_BYTES + 16)
        with tempfile.TemporaryDirectory() as d:
            path = _write_config(d, blob)
            values, warnings = config.load_config(path)
        self.assertEqual(values, _DEFAULTS)
        self.assertEqual(len(warnings), 1)
        self.assertIn("too large", warnings[0])

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX only (os.mkfifo)")
    def test_non_regular_fifo_defaults_plus_warning(self):
        # A FIFO at the config path => defaults + 1 warning WITHOUT blocking; the
        # os.path.isfile guard degrades it before any open/read (Finding #2 round-4).
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, ".vibe-check.toml")
            os.mkfifo(path)
            values, warnings = config.load_config(path)
        self.assertEqual(values, _DEFAULTS)
        self.assertEqual(len(warnings), 1)
        self.assertIn("not a regular file", warnings[0])

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX only (symlink->special)")
    def test_non_regular_symlink_to_devnull_defaults_plus_warning(self):
        # A symlink->/dev/null (char device) => defaults + 1 warning WITHOUT
        # blocking; getsize would report 0 and pass a size-only guard, so the
        # regular-file guard MUST run first (Finding #2 round-4).
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, ".vibe-check.toml")
            os.symlink("/dev/null", path)
            values, warnings = config.load_config(path)
        self.assertEqual(values, _DEFAULTS)
        self.assertEqual(len(warnings), 1)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink required")
    def test_symlink_to_regular_file_is_honored(self):
        # A symlink->a real regular file is parsed normally (isfile True).
        with tempfile.TemporaryDirectory() as d:
            real = os.path.join(d, "real.toml")
            with open(real, "w") as fh:
                fh.write('[agents]\ntop_model = "opus"\n')
            path = os.path.join(d, ".vibe-check.toml")
            os.symlink(real, path)
            values, warnings = config.load_config(path)
        self.assertEqual(values["top_model"], "opus")
        self.assertEqual(warnings, [])


# --------------------------------------------------------------------------- #
# thresholds validation (D-02 locked schema).
# --------------------------------------------------------------------------- #
class TestThresholdsValidation(unittest.TestCase):
    def _load(self, table_body):
        with tempfile.TemporaryDirectory() as d:
            path = _write_config(d, "[review]\nthresholds = " + table_body + "\n")
            return config.load_config(path)

    def test_valid_descending_round_trips(self):
        values, warnings = self._load("{ critical = 95, warning = 80, medium = 70 }")
        self.assertEqual(values["thresholds"],
                         {"critical": 95, "warning": 80, "medium": 70})
        self.assertEqual(warnings, [])

    def test_non_monotonic_defaults_with_warning(self):
        values, warnings = self._load("{ critical = 70, warning = 80, medium = 60 }")
        self.assertIsNone(values["thresholds"])
        self.assertEqual(len(warnings), 1)
        self.assertIn("thresholds", warnings[0])

    def test_medium_below_floor_defaults_with_warning(self):
        # medium < 70 is a dead band both commands filter => whole-set fallback.
        values, warnings = self._load("{ critical = 90, warning = 80, medium = 65 }")
        self.assertIsNone(values["thresholds"])
        self.assertEqual(len(warnings), 1)

    def test_missing_sub_key_defaults_with_warning(self):
        values, warnings = self._load("{ critical = 90, warning = 80 }")
        self.assertIsNone(values["thresholds"])
        self.assertEqual(len(warnings), 1)

    def test_extra_sub_key_defaults_with_warning(self):
        values, warnings = self._load(
            "{ critical = 90, warning = 80, medium = 70, low = 50 }")
        self.assertIsNone(values["thresholds"])
        self.assertEqual(len(warnings), 1)

    def test_non_int_sub_key_defaults_with_warning(self):
        values, warnings = self._load(
            '{ critical = "90", warning = 80, medium = 70 }')
        self.assertIsNone(values["thresholds"])
        self.assertEqual(len(warnings), 1)

    def test_out_of_range_sub_key_defaults_with_warning(self):
        values, warnings = self._load("{ critical = 101, warning = 80, medium = 70 }")
        self.assertIsNone(values["thresholds"])
        self.assertEqual(len(warnings), 1)

    def test_below_cutoff_floor_accepted(self):
        # Finding #4: a below-80 band floor is VALID (observability under
        # /review vs /deep-review is the per-command-cutoff layer, not a reject).
        values, warnings = self._load("{ critical = 72, warning = 71, medium = 70 }")
        self.assertEqual(values["thresholds"],
                         {"critical": 72, "warning": 71, "medium": 70})
        self.assertEqual(warnings, [])


# --------------------------------------------------------------------------- #
# top_model validation (opus/fable allowlist).
# --------------------------------------------------------------------------- #
class TestTopModel(unittest.TestCase):
    def _load(self, value_literal):
        with tempfile.TemporaryDirectory() as d:
            path = _write_config(d, "[agents]\ntop_model = " + value_literal + "\n")
            return config.load_config(path)

    def test_opus_round_trips(self):
        values, warnings = self._load('"opus"')
        self.assertEqual(values["top_model"], "opus")
        self.assertEqual(warnings, [])

    def test_fable_round_trips(self):
        values, warnings = self._load('"fable"')
        self.assertEqual(values["top_model"], "fable")
        self.assertEqual(warnings, [])

    def test_bogus_string_defaults_with_warning(self):
        values, warnings = self._load('"gpt-5"')
        self.assertIsNone(values["top_model"])
        self.assertEqual(len(warnings), 1)
        self.assertIn("top_model", warnings[0])

    def test_non_str_defaults_with_warning(self):
        values, warnings = self._load("42")
        self.assertIsNone(values["top_model"])
        self.assertEqual(len(warnings), 1)


# --------------------------------------------------------------------------- #
# disabled validation (list of strings; core agents honored, not stripped).
# --------------------------------------------------------------------------- #
class TestDisabled(unittest.TestCase):
    def _load(self, value_literal):
        with tempfile.TemporaryDirectory() as d:
            path = _write_config(d, "[agents]\ndisabled = " + value_literal + "\n")
            return config.load_config(path)

    def test_valid_list_round_trips(self):
        values, warnings = self._load('["language-go", "framework-vue"]')
        self.assertEqual(values["disabled"], ["language-go", "framework-vue"])
        self.assertEqual(warnings, [])

    def test_non_list_defaults_with_warning(self):
        values, warnings = self._load('"language-go"')
        self.assertEqual(values["disabled"], [])
        self.assertEqual(len(warnings), 1)

    def test_non_string_element_kept_strings_and_warns(self):
        values, warnings = self._load('["language-go", 7, "framework-vue"]')
        self.assertEqual(values["disabled"], ["language-go", "framework-vue"])
        self.assertEqual(len(warnings), 1)

    def test_core_agent_disable_is_honored(self):
        # Disabling bugs/security IS honored (returned, NOT stripped) — the
        # orchestrator surfaces it on the config-health line, not the validator.
        values, warnings = self._load('["bugs", "security"]')
        self.assertEqual(values["disabled"], ["bugs", "security"])
        self.assertEqual(warnings, [])


# --------------------------------------------------------------------------- #
# precedence (CONFIG-02) — flag > toml > default, flags validated (Finding #3).
# --------------------------------------------------------------------------- #
class TestPrecedence(unittest.TestCase):
    def test_flag_overrides_toml(self):
        with tempfile.TemporaryDirectory() as d:
            path = _write_config(d, '[agents]\ntop_model = "fable"\n')
            values, warnings = config.load_config(path, flags={"top_model": "opus"})
            self.assertEqual(values["top_model"], "opus")
            self.assertEqual(warnings, [])
            # flags=None leaves the toml value.
            values_none, _ = config.load_config(path, flags=None)
            self.assertEqual(values_none["top_model"], "fable")

    def test_bad_flag_top_model_degrades(self):
        with tempfile.TemporaryDirectory() as d:
            path = _write_config(d, '[agents]\ntop_model = "opus"\n')
            values, warnings = config.load_config(path, flags={"top_model": "gpt-5"})
        self.assertIsNone(values["top_model"])
        self.assertEqual(len(warnings), 1)
        self.assertIn("top_model", warnings[0])

    def test_bad_flag_thresholds_degrades(self):
        with tempfile.TemporaryDirectory() as d:
            path = _write_config(d, "# empty\n")
            values, warnings = config.load_config(
                path, flags={"thresholds": {"critical": 70, "warning": 80, "medium": 60}})
        self.assertIsNone(values["thresholds"])
        self.assertEqual(len(warnings), 1)
        self.assertIn("thresholds", warnings[0])

    def test_bad_flag_disabled_degrades(self):
        with tempfile.TemporaryDirectory() as d:
            path = _write_config(d, "# empty\n")
            values, warnings = config.load_config(
                path, flags={"disabled": "not-a-list"})
        self.assertEqual(values["disabled"], [])
        self.assertEqual(len(warnings), 1)
        self.assertIn("disabled", warnings[0])

    def test_valid_flag_thresholds_overlays(self):
        with tempfile.TemporaryDirectory() as d:
            path = _write_config(d, "# empty\n")
            values, warnings = config.load_config(
                path, flags={"thresholds": {"critical": 90, "warning": 80, "medium": 70}})
        self.assertEqual(values["thresholds"],
                         {"critical": 90, "warning": 80, "medium": 70})
        self.assertEqual(warnings, [])


# --------------------------------------------------------------------------- #
# DEGRADE-not-abort __main__ shim (subprocess) — the INVERSE of score.py's
# TestFailClosed: a broken config makes the process exit 0 with defaults.
# --------------------------------------------------------------------------- #
class TestDegradeNotAbort(unittest.TestCase):
    def test_malformed_config_exits_zero_with_warning(self):
        with tempfile.TemporaryDirectory() as d:
            _write_config(d, "this is = = not toml\n")
            proc = subprocess.run(
                [sys.executable, CONFIG_PY],
                env={**os.environ, "REPO_ROOT": d},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
            )
        self.assertEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["values"], _DEFAULTS)
        self.assertTrue(payload["warnings"])

    def test_absent_config_exits_zero_silent(self):
        with tempfile.TemporaryDirectory() as d:
            proc = subprocess.run(
                [sys.executable, CONFIG_PY],
                env={**os.environ, "REPO_ROOT": d},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
            )
        self.assertEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["values"], _DEFAULTS)
        self.assertEqual(payload["warnings"], [])


# --------------------------------------------------------------------------- #
# config.py import-set guard — a SEPARATE class from score.py's TestImportSet,
# with a WIDER allowlist (config.py is the I/O boundary). Does NOT touch score.py.
# --------------------------------------------------------------------------- #
class TestImportSet(unittest.TestCase):
    ALLOWED = {"json", "os", "sys", "tomllib"}

    def _tree(self):
        with open(CONFIG_PY, "r", encoding="utf-8") as fh:
            return ast.parse(fh.read())

    def test_import_set_subset_of_allowed(self):
        tree = self._tree()
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported.add(node.module.split(".")[0])
        self.assertTrue(
            imported.issubset(self.ALLOWED),
            "config.py imports outside {json,os,sys,tomllib}: "
            + str(imported - self.ALLOWED),
        )


if __name__ == "__main__":
    unittest.main()
