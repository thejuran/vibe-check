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
# NOTE idiom_floor defaults to "medium" (NOT None) — the NOISE-01 cap is ACTIVE
# BY DEFAULT (A1), the OPPOSITE default-direction from the None-defaulting knobs.
# codex defaults to "auto" (NOT None) — the behavior-unchanged Codex posture
# (LEGIBLE-02, D-14), same non-None default-direction as idiom_floor.
_DEFAULTS = {"thresholds": None, "disabled": [], "top_model": None,
             "min_confidence": None, "idiom_floor": "medium",
             "codex": "auto"}


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

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink required")
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
# min_confidence validation (CONF-02, D-04 — [noise] int in [0, 100]).
# --------------------------------------------------------------------------- #
class TestMinConfidenceValidation(unittest.TestCase):
    """The [noise] min_confidence knob: a valid int in [0, 100] round-trips;
    anything else (out-of-range, non-int, bool) degrades to None + one warning
    naming the KEY (never fatal). Mirrors TestThresholdsValidation / TestTopModel.
    """

    def _load(self, value_literal):
        with tempfile.TemporaryDirectory() as d:
            path = _write_config(
                d, "[noise]\nmin_confidence = " + value_literal + "\n")
            return config.load_config(path)

    def test_valid_int_round_trips(self):
        values, warnings = self._load("40")
        self.assertEqual(values["min_confidence"], 40)
        self.assertEqual(warnings, [])

    def test_zero_round_trips(self):
        # 0 is a valid in-range value (no filtering, but explicitly configured).
        values, warnings = self._load("0")
        self.assertEqual(values["min_confidence"], 0)
        self.assertEqual(warnings, [])

    def test_forty_nine_round_trips(self):
        # 49 is the top of the valid range (Fable A3): the last value that can
        # never pre-filter a finding able to reach the critical band.
        values, warnings = self._load("49")
        self.assertEqual(values["min_confidence"], 49)
        self.assertEqual(warnings, [])

    def test_at_or_above_critical_floor_refused(self):
        # Fable A3 (the H-KNOB kill-shot): min_confidence >= 50 would silently
        # drop findings that score into the critical band (the filter runs
        # BEFORE scoring, so in_diff/cross-confirm/persisted can never rescue
        # them). 50 exactly, the spec's old illustrative 60, and 100 are ALL
        # refused -> None + ONE warning whose text explains the critical-drop
        # hazard (distinct from the generic invalid reason).
        for value in ("50", "60", "100"):
            values, warnings = self._load(value)
            self.assertIsNone(values["min_confidence"],
                              "min_confidence=%s must be refused" % value)
            self.assertEqual(len(warnings), 1)
            self.assertIn("min_confidence", warnings[0])
            self.assertIn("critical", warnings[0])

    def test_above_range_defaults_with_warning(self):
        values, warnings = self._load("101")
        self.assertIsNone(values["min_confidence"])
        self.assertEqual(len(warnings), 1)
        self.assertIn("min_confidence", warnings[0])

    def test_below_range_defaults_with_warning(self):
        values, warnings = self._load("-1")
        self.assertIsNone(values["min_confidence"])
        self.assertEqual(len(warnings), 1)
        self.assertIn("min_confidence", warnings[0])

    def test_non_int_defaults_with_warning(self):
        values, warnings = self._load('"70"')
        self.assertIsNone(values["min_confidence"])
        self.assertEqual(len(warnings), 1)
        self.assertIn("min_confidence", warnings[0])

    def test_bool_rejected_with_warning(self):
        # bool is an int subclass but is NOT a valid confidence value.
        values, warnings = self._load("true")
        self.assertIsNone(values["min_confidence"])
        self.assertEqual(len(warnings), 1)
        self.assertIn("min_confidence", warnings[0])

    def test_absent_key_silent(self):
        # A [noise] section with no min_confidence => None, no warning.
        with tempfile.TemporaryDirectory() as d:
            path = _write_config(d, "[noise]\n")
            values, warnings = config.load_config(path)
        self.assertIsNone(values["min_confidence"])
        self.assertEqual(warnings, [])

    def test_absent_section_silent(self):
        # No [noise] section at all => None, no warning (zero-config silence).
        with tempfile.TemporaryDirectory() as d:
            path = _write_config(d, '[agents]\ntop_model = "opus"\n')
            values, warnings = config.load_config(path)
        self.assertIsNone(values["min_confidence"])
        self.assertEqual(warnings, [])

    def test_validator_direct(self):
        # Unit-level: the validator returns the documented (value, warning) shape.
        # Valid range is [0, 49] (Fable A3 — >= 50 can annihilate criticals).
        self.assertEqual(config._validate_min_confidence(40), (40, None))
        self.assertEqual(config._validate_min_confidence(0), (0, None))
        self.assertEqual(config._validate_min_confidence(49), (49, None))
        for bad in (50, 60, 100, 101, -1, "70", True, False, 3.5, None, {}):
            resolved, warning = config._validate_min_confidence(bad)
            self.assertIsNone(resolved)
            self.assertIsNotNone(warning)
            self.assertIn("min_confidence", warning)


# --------------------------------------------------------------------------- #
# idiom_floor validation (NOISE-01 — [noise] band-cap knob).
# --------------------------------------------------------------------------- #
class TestIdiomFloorValidation(unittest.TestCase):
    """The [noise] idiom_floor knob (NOISE-01): a valid band name round-trips
    (INCLUDING "low" — a valid cap value, Finding NEW-2); "off"/"none" (both
    spellings) → the LITERAL "off" sentinel (NOT None — Finding #2, Option A) so
    the explicit-disable provenance survives onto the envelope and is DISTINCT
    from omission; malformed → the "medium" DEFAULT (NOT None, NOT the sentinel)
    + one warning naming the KEY (ROADMAP criterion 4 — malformed keeps the cap
    ACTIVE). Zero-config default is "medium". Mirrors TestMinConfidenceValidation
    but with the OPPOSITE malformed direction (medium, not None)."""

    def _load(self, value_literal):
        with tempfile.TemporaryDirectory() as d:
            path = _write_config(
                d, "[noise]\nidiom_floor = " + value_literal + "\n")
            return config.load_config(path)

    def test_valid_band_round_trips(self):
        for band in ("critical", "warning", "medium", "low"):
            values, warnings = self._load('"' + band + '"')
            self.assertEqual(values["idiom_floor"], band)
            self.assertEqual(warnings, [])

    def test_low_is_a_valid_cap_not_a_disable(self):
        # Finding NEW-2: "low" is IN the valid band set — it caps at the literal
        # "low" band, it is NOT a disable sentinel and produces NO warning.
        values, warnings = self._load('"low"')
        self.assertEqual(values["idiom_floor"], "low")
        self.assertEqual(warnings, [])

    def test_case_insensitive_band(self):
        values, warnings = self._load('"MEDIUM"')
        self.assertEqual(values["idiom_floor"], "medium")
        self.assertEqual(warnings, [])

    def test_off_returns_literal_off_sentinel(self):
        # Finding #2 (Option A): explicit "off" → the LITERAL "off" sentinel,
        # NOT None, with NO warning.
        values, warnings = self._load('"off"')
        self.assertEqual(values["idiom_floor"], "off")
        self.assertEqual(warnings, [])

    def test_none_normalizes_to_off_sentinel(self):
        # Both disable spellings normalize to the single canonical "off" sentinel.
        values, warnings = self._load('"none"')
        self.assertEqual(values["idiom_floor"], "off")
        self.assertEqual(warnings, [])

    def test_off_case_insensitive(self):
        values, warnings = self._load('"OFF"')
        self.assertEqual(values["idiom_floor"], "off")
        self.assertEqual(warnings, [])
        values, warnings = self._load('"None"')
        self.assertEqual(values["idiom_floor"], "off")
        self.assertEqual(warnings, [])

    def test_unknown_string_defaults_to_medium_with_warning(self):
        # Malformed unknown band name → the "medium" DEFAULT (NOT None, NOT the
        # "off" sentinel) + one warning naming the key. ROADMAP criterion 4: a
        # bad value keeps the cap ACTIVE.
        values, warnings = self._load('"bogus"')
        self.assertEqual(values["idiom_floor"], "medium")
        self.assertEqual(len(warnings), 1)
        self.assertIn("idiom_floor", warnings[0])

    def test_non_string_defaults_to_medium_with_warning(self):
        # A non-str TOML literal (int) → "medium" + one warning. Non-str is never
        # the off sentinel — the cap stays active.
        values, warnings = self._load("70")
        self.assertEqual(values["idiom_floor"], "medium")
        self.assertEqual(len(warnings), 1)
        self.assertIn("idiom_floor", warnings[0])

    def test_bool_defaults_to_medium_with_warning(self):
        values, warnings = self._load("true")
        self.assertEqual(values["idiom_floor"], "medium")
        self.assertEqual(len(warnings), 1)
        self.assertIn("idiom_floor", warnings[0])

    def test_warning_does_not_leak_raw_value(self):
        # V7: the warning names the KEY + a fixed reason ONLY — never the raw text.
        values, warnings = self._load('"sneaky-raw-value-xyz"')
        self.assertEqual(len(warnings), 1)
        self.assertNotIn("sneaky-raw-value-xyz", warnings[0])

    def test_absent_key_defaults_to_medium_silent(self):
        # Zero-config default (A1): a [noise] section with no idiom_floor →
        # "medium" (the default-active cap), NO warning.
        with tempfile.TemporaryDirectory() as d:
            path = _write_config(d, "[noise]\n")
            values, warnings = config.load_config(path)
        self.assertEqual(values["idiom_floor"], "medium")
        self.assertEqual(warnings, [])

    def test_absent_section_defaults_to_medium_silent(self):
        # No [noise] section at all → "medium" default (A1), no warning.
        with tempfile.TemporaryDirectory() as d:
            path = _write_config(d, '[agents]\ntop_model = "opus"\n')
            values, warnings = config.load_config(path)
        self.assertEqual(values["idiom_floor"], "medium")
        self.assertEqual(warnings, [])

    def test_zero_config_load_defaults_to_medium(self):
        # An entirely absent config file → "medium" default (A1).
        values, warnings = config.load_config("/nonexistent/.vibe-check.toml")
        self.assertEqual(values["idiom_floor"], "medium")
        self.assertEqual(warnings, [])

    def test_validator_direct(self):
        # Unit-level: the validator returns the documented (value, warning) shape.
        for band in ("critical", "warning", "medium", "low"):
            self.assertEqual(config._validate_idiom_floor(band), (band, None))
        # Case-insensitive band names.
        self.assertEqual(config._validate_idiom_floor("LOW"), ("low", None))
        # Disable sentinels → the literal "off" (NOT None), no warning.
        self.assertEqual(config._validate_idiom_floor("off"), ("off", None))
        self.assertEqual(config._validate_idiom_floor("none"), ("off", None))
        self.assertEqual(config._validate_idiom_floor("NONE"), ("off", None))
        # Malformed → "medium" (NOT None, NOT "off") + a warning naming the key.
        for bad in ("bogus", "", 70, True, False, 3.5, None, {}, []):
            resolved, warning = config._validate_idiom_floor(bad)
            self.assertEqual(resolved, "medium")
            self.assertIsNotNone(warning)
            self.assertIn("idiom_floor", warning)


# --------------------------------------------------------------------------- #
# codex validation (LEGIBLE-02, D-10/D-14 — [noise] off/auto/on enum knob).
# --------------------------------------------------------------------------- #
class TestCodexValidation(unittest.TestCase):
    """The [noise] codex knob (LEGIBLE-02): a valid mode round-trips
    (case-insensitive → lowercased) with NO warning; malformed → the "auto"
    DEFAULT (NOT None) + one warning naming the KEY (behavior-unchanged posture,
    D-14). Zero-config default is "auto". Mirrors TestTopModel (fixed-enum) with
    the idiom_floor malformed-direction (non-None default)."""

    def _load(self, value_literal):
        with tempfile.TemporaryDirectory() as d:
            path = _write_config(
                d, "[noise]\ncodex = " + value_literal + "\n")
            return config.load_config(path)

    def test_valid_mode_round_trips(self):
        for mode in ("off", "auto", "on"):
            values, warnings = self._load('"' + mode + '"')
            self.assertEqual(values["codex"], mode)
            self.assertEqual(warnings, [])

    def test_case_insensitive_mode(self):
        values, warnings = self._load('"ON"')
        self.assertEqual(values["codex"], "on")
        self.assertEqual(warnings, [])
        values, warnings = self._load('"Off"')
        self.assertEqual(values["codex"], "off")
        self.assertEqual(warnings, [])

    def test_unknown_string_defaults_to_auto_with_warning(self):
        # Malformed unknown mode → the "auto" DEFAULT (NOT None) + one warning
        # naming the key. D-14: a bad value keeps Codex running (auto).
        values, warnings = self._load('"bogus"')
        self.assertEqual(values["codex"], "auto")
        self.assertEqual(len(warnings), 1)
        self.assertIn("codex", warnings[0])

    def test_non_string_defaults_to_auto_with_warning(self):
        # A non-str TOML literal (int) → "auto" + one warning.
        values, warnings = self._load("5")
        self.assertEqual(values["codex"], "auto")
        self.assertEqual(len(warnings), 1)
        self.assertIn("codex", warnings[0])

    def test_bool_defaults_to_auto_with_warning(self):
        values, warnings = self._load("true")
        self.assertEqual(values["codex"], "auto")
        self.assertEqual(len(warnings), 1)
        self.assertIn("codex", warnings[0])

    def test_warning_does_not_leak_raw_value(self):
        # V5/V7: the warning names the KEY + a fixed reason ONLY — never the raw.
        values, warnings = self._load('"sneaky-raw-value-xyz"')
        self.assertEqual(len(warnings), 1)
        self.assertNotIn("sneaky-raw-value-xyz", warnings[0])

    def test_absent_key_defaults_to_auto_silent(self):
        # Zero-config default: a [noise] section with no codex → "auto", NO warning.
        with tempfile.TemporaryDirectory() as d:
            path = _write_config(d, "[noise]\n")
            values, warnings = config.load_config(path)
        self.assertEqual(values["codex"], "auto")
        self.assertEqual(warnings, [])

    def test_absent_section_defaults_to_auto_silent(self):
        # No [noise] section at all → "auto" default, no warning.
        with tempfile.TemporaryDirectory() as d:
            path = _write_config(d, '[agents]\ntop_model = "opus"\n')
            values, warnings = config.load_config(path)
        self.assertEqual(values["codex"], "auto")
        self.assertEqual(warnings, [])

    def test_zero_config_load_defaults_to_auto(self):
        # An entirely absent config file → "auto" default.
        values, warnings = config.load_config("/nonexistent/.vibe-check.toml")
        self.assertEqual(values["codex"], "auto")
        self.assertEqual(warnings, [])

    def test_validator_direct(self):
        # Unit-level: the validator returns the documented (value, warning) shape.
        for mode in ("off", "auto", "on"):
            self.assertEqual(config._validate_codex(mode), (mode, None))
        # Case-insensitive modes lowercase.
        self.assertEqual(config._validate_codex("ON"), ("on", None))
        self.assertEqual(config._validate_codex("Off"), ("off", None))
        # Malformed → "auto" (NOT None) + a warning naming the key.
        for bad in ("bogus", "", 5, True, False, 3.5, None, {}, []):
            resolved, warning = config._validate_codex(bad)
            self.assertEqual(resolved, "auto")
            self.assertIsNotNone(warning)
            self.assertIn("codex", warning)


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

    def test_flag_overrides_toml_min_confidence(self):
        # --min-confidence 45 beats [noise] min_confidence = 30 (flag > toml).
        with tempfile.TemporaryDirectory() as d:
            path = _write_config(d, "[noise]\nmin_confidence = 30\n")
            values, warnings = config.load_config(
                path, flags={"min_confidence": 45})
            self.assertEqual(values["min_confidence"], 45)
            self.assertEqual(warnings, [])
            # flags=None leaves the toml value.
            values_none, _ = config.load_config(path, flags=None)
            self.assertEqual(values_none["min_confidence"], 30)
            # A None flag value (no override) also leaves the toml value.
            values_flagnone, _ = config.load_config(
                path, flags={"min_confidence": None})
            self.assertEqual(values_flagnone["min_confidence"], 30)

    def test_bad_flag_min_confidence_degrades(self):
        # A bad flag runs the SAME validator as a bad toml value (never bypass):
        # 999 => None + one warning naming the key.
        with tempfile.TemporaryDirectory() as d:
            path = _write_config(d, "[noise]\nmin_confidence = 40\n")
            values, warnings = config.load_config(
                path, flags={"min_confidence": 999})
        self.assertIsNone(values["min_confidence"])
        self.assertEqual(len(warnings), 1)
        self.assertIn("min_confidence", warnings[0])

    def test_flag_overrides_toml_codex(self):
        # --codex on beats [noise] codex = "off" (flag > toml).
        with tempfile.TemporaryDirectory() as d:
            path = _write_config(d, '[noise]\ncodex = "off"\n')
            values, warnings = config.load_config(path, flags={"codex": "on"})
            self.assertEqual(values["codex"], "on")
            self.assertEqual(warnings, [])
            # flags=None leaves the toml value.
            values_none, _ = config.load_config(path, flags=None)
            self.assertEqual(values_none["codex"], "off")
            # A None flag value (no override) also leaves the toml value.
            values_flagnone, _ = config.load_config(path, flags={"codex": None})
            self.assertEqual(values_flagnone["codex"], "off")

    def test_bad_flag_codex_degrades(self):
        # A bad flag runs the SAME validator as a bad toml value: "bogus" =>
        # "auto" (NOT None — codex's non-None default-direction) + one warning.
        with tempfile.TemporaryDirectory() as d:
            path = _write_config(d, '[noise]\ncodex = "on"\n')
            values, warnings = config.load_config(
                path, flags={"codex": "bogus"})
        self.assertEqual(values["codex"], "auto")
        self.assertEqual(len(warnings), 1)
        self.assertIn("codex", warnings[0])

    def test_codex_default_when_neither_flag_nor_toml(self):
        # Absent flag + absent toml => the "auto" default.
        with tempfile.TemporaryDirectory() as d:
            path = _write_config(d, "# empty\n")
            values, warnings = config.load_config(path, flags=None)
        self.assertEqual(values["codex"], "auto")
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

    def _run_main(self, env_extra, config_body=None):
        with tempfile.TemporaryDirectory() as d:
            if config_body is not None:
                _write_config(d, config_body)
            env = {**os.environ, "REPO_ROOT": d}
            env.update(env_extra)
            proc = subprocess.run(
                [sys.executable, CONFIG_PY],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
            )
        self.assertEqual(proc.returncode, 0)
        return json.loads(proc.stdout)

    def test_min_confidence_flag_overrides_toml_via_main(self):
        # MIN_CONFIDENCE_FLAG=45 threads into _apply_flags and beats toml 30.
        payload = self._run_main(
            {"MIN_CONFIDENCE_FLAG": "45"},
            config_body="[noise]\nmin_confidence = 30\n",
        )
        self.assertEqual(payload["values"]["min_confidence"], 45)
        self.assertEqual(payload["warnings"], [])

    def test_bad_min_confidence_flag_degrades_via_main(self):
        # An out-of-range flag runs the SAME validator: None + warning, exit 0.
        payload = self._run_main(
            {"MIN_CONFIDENCE_FLAG": "999"},
            config_body="[noise]\nmin_confidence = 40\n",
        )
        self.assertIsNone(payload["values"]["min_confidence"])
        self.assertTrue(any("min_confidence" in w for w in payload["warnings"]))

    def test_non_int_min_confidence_flag_no_crash(self):
        # A non-int MIN_CONFIDENCE_FLAG is parsed defensively -> forwarded as no
        # flag override; the shim still exits 0 (never-abort contract).
        payload = self._run_main(
            {"MIN_CONFIDENCE_FLAG": "notanint"},
            config_body="[noise]\nmin_confidence = 40\n",
        )
        # No flag override => the toml value stands.
        self.assertEqual(payload["values"]["min_confidence"], 40)

    def test_empty_min_confidence_flag_behaves_as_no_flag(self):
        # Unset/empty MIN_CONFIDENCE_FLAG => byte-identical to today's no-flag path.
        payload = self._run_main(
            {"MIN_CONFIDENCE_FLAG": ""},
            config_body="[noise]\nmin_confidence = 40\n",
        )
        self.assertEqual(payload["values"]["min_confidence"], 40)

    def test_min_confidence_flag_empty_repo_root_no_crash(self):
        # Empty REPO_ROOT (no config file) + a valid flag => exit 0, and the flag
        # STILL applies: load_config("") returns defaults, then _apply_flags overlays
        # the flag, so min_confidence resolves to 45 (the flag-always-applies invariant,
        # asserted below). __main__ threads the flag without crashing.
        env = {**os.environ, "REPO_ROOT": "", "MIN_CONFIDENCE_FLAG": "45"}
        proc = subprocess.run(
            [sys.executable, CONFIG_PY],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )
        self.assertEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        # 45 is a valid flag; with no toml value it becomes the resolved value.
        self.assertEqual(payload["values"]["min_confidence"], 45)

    def test_codex_flag_overrides_toml_via_main(self):
        # CODEX_FLAG=on threads into _apply_flags and beats toml "off".
        payload = self._run_main(
            {"CODEX_FLAG": "on"},
            config_body='[noise]\ncodex = "off"\n',
        )
        self.assertEqual(payload["values"]["codex"], "on")
        self.assertEqual(payload["warnings"], [])

    def test_bad_codex_flag_degrades_via_main(self):
        # A bogus flag token runs the SAME validator: "auto" + warning, exit 0
        # (no int() parse — a non-empty string flows straight into _validate_codex).
        payload = self._run_main(
            {"CODEX_FLAG": "bogus"},
            config_body='[noise]\ncodex = "on"\n',
        )
        self.assertEqual(payload["values"]["codex"], "auto")
        self.assertTrue(any("codex" in w for w in payload["warnings"]))

    def test_empty_codex_flag_behaves_as_no_flag(self):
        # Unset/empty CODEX_FLAG => byte-identical to today's no-flag path: the
        # toml value stands.
        payload = self._run_main(
            {"CODEX_FLAG": ""},
            config_body='[noise]\ncodex = "off"\n',
        )
        self.assertEqual(payload["values"]["codex"], "off")

    def test_codex_and_min_confidence_flags_coexist_via_main(self):
        # Both flags on ONE invocation merge into the same flags dict.
        payload = self._run_main(
            {"CODEX_FLAG": "on", "MIN_CONFIDENCE_FLAG": "45"},
            config_body='[noise]\ncodex = "off"\nmin_confidence = 30\n',
        )
        self.assertEqual(payload["values"]["codex"], "on")
        self.assertEqual(payload["values"]["min_confidence"], 45)
        self.assertEqual(payload["warnings"], [])

    def test_codex_flag_empty_repo_root_no_crash(self):
        # Empty REPO_ROOT (no config file) + a valid CODEX_FLAG => exit 0, and the
        # flag STILL applies: load_config("") returns the "auto" default, then
        # _apply_flags overlays the flag, so codex resolves to "on".
        env = {**os.environ, "REPO_ROOT": "", "CODEX_FLAG": "on"}
        proc = subprocess.run(
            [sys.executable, CONFIG_PY],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )
        self.assertEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["values"]["codex"], "on")


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
