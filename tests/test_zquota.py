from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone
from io import StringIO
from unittest.mock import patch

import zquota


def reset_ms() -> int:
    return int(datetime(2026, 5, 23, 14, 0, tzinfo=timezone.utc).timestamp() * 1000)


def sample_payload() -> dict[str, object]:
    return {
        "success": True,
        "data": {
            "level": "pro",
            "limits": [
                {
                    "type": "TOKENS_LIMIT",
                    "unit": 3,
                    "number": 5,
                    "percentage": 50,
                    "usage": 1_000_000,
                    "currentValue": 500_000,
                    "remaining": 500_000,
                    "nextResetTime": reset_ms(),
                    "usageDetails": [
                        {"modelCode": "glm-4.5", "usage": 1234},
                    ],
                }
            ],
        },
    }


class QuotaFormattingTests(unittest.TestCase):
    def test_format_duration_keeps_three_largest_units(self) -> None:
        self.assertEqual(zquota.format_duration(90061), "1d 1h 1m")
        self.assertEqual(zquota.format_duration(0), "now")

    def test_progress_bar_clamps_out_of_range_percentages(self) -> None:
        negative = zquota.progress_bar(-20, width=4, use_color=False)
        too_large = zquota.progress_bar(140, width=4, use_color=False)

        self.assertEqual(negative, zquota.BAR_EMPTY * 4)
        self.assertEqual(too_large, zquota.BAR_FILLED * 4)

    def test_build_quota_item_includes_exact_reset_times(self) -> None:
        _, limits = zquota.parse_payload(sample_payload())
        now = datetime(2026, 5, 23, 13, 30, tzinfo=timezone.utc)

        item = zquota.build_quota_item(limits[0], zquota.get_timezone("Europe/London"), now)

        self.assertEqual(item["name_compact"], "5h-rolling")
        self.assertEqual(item["resets_in"], "30m")
        self.assertEqual(item["resets_at"], "2026-05-23 15:00:00 BST")
        self.assertEqual(item["resets_at_utc"], "2026-05-23T14:00:00Z")
        self.assertEqual(item["reset_epoch_ms"], reset_ms())
        self.assertEqual(item["timezone"], "Europe/London")

    def test_json_lines_contains_script_friendly_reset_fields(self) -> None:
        _, limits = zquota.parse_payload(sample_payload())
        item = zquota.build_quota_item(
            limits[0],
            zquota.get_timezone("Europe/London"),
            datetime(2026, 5, 23, 13, 30, tzinfo=timezone.utc),
        )

        line = json.loads(zquota.output_json_lines("pro", [item]))

        self.assertEqual(line["quota"], "5h-rolling")
        self.assertEqual(line["resets_at_utc"], "2026-05-23T14:00:00Z")
        self.assertEqual(line["reset_epoch_ms"], reset_ms())


class MainTests(unittest.TestCase):
    def test_raw_output_prints_payload_without_parsing_assertion(self) -> None:
        stdout = StringIO()

        with (
            patch("zquota.fetch_json", return_value=sample_payload()),
            patch("sys.stdout", new=stdout),
        ):
            code = zquota.main(["--raw", "--api-key", "test"])

        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout.getvalue()), sample_payload())

    def test_raw_output_cannot_be_combined_with_threshold(self) -> None:
        stderr = StringIO()

        with patch("sys.stderr", new=stderr):
            code = zquota.main(["--raw", "--threshold", "80", "--api-key", "test"])

        self.assertEqual(code, 1)
        self.assertIn("--threshold cannot be used with --raw", stderr.getvalue())

    def test_threshold_must_be_a_percentage(self) -> None:
        stderr = StringIO()

        with patch("sys.stderr", new=stderr):
            code = zquota.main(["--threshold", "101", "--api-key", "test"])

        self.assertEqual(code, 1)
        self.assertIn("--threshold must be between 0 and 100", stderr.getvalue())


class TimezoneTests(unittest.TestCase):
    def run_json(self, *argv: str, env: dict[str, str] | None = None) -> tuple[int, str, str]:
        """Run main() with --json against the sample payload; return (code, stdout, stderr)."""
        stdout, stderr = StringIO(), StringIO()
        with (
            patch.dict("os.environ", env or {}),
            patch("zquota.fetch_json", return_value=sample_payload()),
            patch("sys.stdout", new=stdout),
            patch("sys.stderr", new=stderr),
        ):
            code = zquota.main(["--json", "--api-key", "test", *argv])
        return code, stdout.getvalue(), stderr.getvalue()

    def test_empty_timezone_variable_counts_as_unset(self) -> None:
        code, stdout, stderr = self.run_json(env={"ZAI_TIMEZONE": ""})

        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout)["quotas"][0]["timezone"], "Europe/London")
        self.assertEqual(stderr, "")

    def test_path_shaped_timezone_warns_and_falls_back(self) -> None:
        for name in ("Europe/", "../etc", "/etc/localtime"):
            with self.subTest(name=name):
                code, stdout, stderr = self.run_json("--timezone", name)

                self.assertEqual(code, 0)
                self.assertEqual(json.loads(stdout)["quotas"][0]["timezone"], "Europe/London")
                self.assertEqual(
                    stderr, f"WARNING: unknown timezone {name!r}; using Europe/London\n"
                )


class InterruptTests(unittest.TestCase):
    def run_interrupted(self, *argv: str) -> tuple[int, str, str]:
        """Run main() with Ctrl-C pressed during the request; return (code, stdout, stderr)."""
        stdout, stderr = StringIO(), StringIO()
        with (
            patch("zquota.fetch_json", side_effect=KeyboardInterrupt),
            patch("sys.stdout", new=stdout),
            patch("sys.stderr", new=stderr),
        ):
            try:
                code = zquota.main(["--api-key", "test", *argv])
            except KeyboardInterrupt:
                self.fail("Ctrl-C escaped main() and would print a traceback")
        return code, stdout.getvalue(), stderr.getvalue()

    def test_ctrl_c_during_a_request_exits_130(self) -> None:
        code, stdout, stderr = self.run_interrupted("--json")

        self.assertEqual(code, 130)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "\n")

    def test_ctrl_c_during_a_watch_refresh_stops_it_cleanly(self) -> None:
        code, _, stderr = self.run_interrupted("--watch", "30", "--no-color")

        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")

    def test_ctrl_c_while_watch_waits_stops_it_cleanly(self) -> None:
        stdout = StringIO()
        with (
            patch("zquota.fetch_json", return_value=sample_payload()),
            patch("time.sleep", side_effect=KeyboardInterrupt),
            patch("sys.stdout", new=stdout),
        ):
            code = zquota.main(["--api-key", "test", "--watch", "30", "--compact", "--no-color"])

        self.assertEqual(code, 0)
        self.assertTrue(stdout.getvalue().endswith("\n\n"))


if __name__ == "__main__":
    unittest.main()
