from __future__ import annotations

import http.client
import json
import os
import re
import unittest
import urllib.error
from datetime import datetime, timezone
from email.message import Message
from io import BytesIO, StringIO
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

    def test_format_number_rolls_over_to_the_next_unit(self) -> None:
        cases = {
            999: "999",
            999.5: "999.5",
            999.99995: "1.0k",
            1_000: "1.0k",
            1_234.5: "1.2k",
            999_949: "999.9k",
            999_950: "1.0M",
            999_999: "1.0M",
            1_000_000: "1.0M",
            2_480_000: "2.5M",
            999_949_999: "999.9M",
            999_950_000: "1.0B",
            1_500_000_000: "1.5B",
            2_000_000_000_000: "2000.0B",
            -1_500: "-1.5k",
            -999_999: "-1.0M",
        }
        for value, shown in cases.items():
            with self.subTest(value=value):
                self.assertEqual(zquota.format_number(value), shown)

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

    def test_default_view_puts_every_value_in_one_column(self) -> None:
        _, limits = zquota.parse_payload(sample_payload())
        item = zquota.build_quota_item(
            limits[0],
            zquota.get_timezone("Europe/London"),
            datetime(2026, 5, 23, 13, 30, tzinfo=timezone.utc),
        )
        stdout = StringIO()

        with patch("sys.stdout", new=stdout):
            zquota.print_pretty("pro", [item], use_color=False)

        # Each match runs from the start of a "Label: value" line to the value's first character.
        fields = re.findall(r"^  \u2502  [A-Z][a-z ]+: +\S", stdout.getvalue(), re.M)
        self.assertEqual(
            [field.split(":")[0].split("  ")[-1] for field in fields],
            ["Remaining", "Limit", "Used", "Remaining", "Resets in", "Resets at"],
        )
        self.assertEqual({len(field) for field in fields}, {18}, fields)

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

    def test_unknown_timezone_warns_once_while_watching(self) -> None:
        output = StringIO()
        with (
            patch("zquota.fetch_json", return_value=sample_payload()),
            patch("time.sleep", side_effect=[None, None, KeyboardInterrupt]),
            patch("sys.stdout", new=output),
            patch("sys.stderr", new=output),
        ):
            code = zquota.main(
                ["--api-key", "test", "--watch", "1", "--compact", "--timezone", "Mars/Base"]
            )

        text = output.getvalue()
        clears = [i for i in range(len(text)) if text.startswith("\033[2J", i)]
        self.assertEqual(code, 0)
        self.assertEqual(len(clears), 3)
        self.assertEqual(text.count("WARNING: unknown timezone 'Mars/Base'"), 1)
        # It's printed after the first clear, so it's on screen until the second refresh.
        self.assertTrue(clears[0] < text.index("WARNING") < clears[1])

    def test_path_shaped_timezone_warns_and_falls_back(self) -> None:
        for name in ("Europe/", "../etc", "/etc/localtime"):
            with self.subTest(name=name):
                code, stdout, stderr = self.run_json("--timezone", name)

                self.assertEqual(code, 0)
                self.assertEqual(json.loads(stdout)["quotas"][0]["timezone"], "Europe/London")
                self.assertEqual(
                    stderr, f"WARNING: unknown timezone {name!r}; using Europe/London\n"
                )


class BrokenBody(BytesIO):
    """A response body whose read() fails the way a dropped or stalled connection does."""

    def __init__(self, error: BaseException) -> None:
        super().__init__()
        self.error = error

    def read(self, *args: object) -> bytes:
        raise self.error


class FakeResponse:
    """Just enough of urlopen()'s response for fetch_json(): a context manager with read()."""

    def __init__(self, error: BaseException) -> None:
        self.body = BrokenBody(error)

    def __enter__(self) -> BrokenBody:
        return self.body

    def __exit__(self, *exc_info: object) -> None:
        return None


class ReadErrorTests(unittest.TestCase):
    def run_failing(self, urlopen_effect: object) -> tuple[int, str]:
        """Run main() with urlopen() patched to urlopen_effect; return (code, stderr)."""
        stderr = StringIO()
        with (
            patch("urllib.request.urlopen", side_effect=urlopen_effect),
            patch("sys.stdout", new=StringIO()),
            patch("sys.stderr", new=stderr),
        ):
            code = zquota.main(["--json", "--api-key", "test"])
        return code, stderr.getvalue()

    def test_failures_while_reading_the_response_are_errors(self) -> None:
        cases = {
            "timeout": (TimeoutError("timed out"), "ERROR: request failed: timed out\n"),
            "reset": (
                ConnectionResetError(54, "Connection reset by peer"),
                "ERROR: request failed: [Errno 54] Connection reset by peer\n",
            ),
            "cut off": (
                http.client.IncompleteRead(b'{"success": tr', 486),
                "ERROR: request failed: the response broke off after 14 bytes\n",
            ),
        }
        for name, (error, message) in cases.items():
            with self.subTest(name):
                code, stderr = self.run_failing([FakeResponse(error)])

                self.assertEqual(code, 1)
                self.assertEqual(stderr, message)

    def test_failures_while_waiting_for_the_answer_are_errors(self) -> None:
        cases = {
            "timeout": (TimeoutError("timed out"), "ERROR: request failed: timed out\n"),
            "closed": (
                http.client.RemoteDisconnected("Remote end closed connection without response"),
                "ERROR: request failed: Remote end closed connection without response\n",
            ),
            "not http": (
                http.client.BadStatusLine("NOT HTTP"),
                "ERROR: request failed: invalid HTTP response: NOT HTTP\n",
            ),
        }
        for name, (error, message) in cases.items():
            with self.subTest(name):
                code, stderr = self.run_failing(error)

                self.assertEqual(code, 1)
                self.assertEqual(stderr, message)

    def test_http_error_whose_body_times_out_still_reports_the_status(self) -> None:
        error = urllib.error.HTTPError(
            zquota.API_URL, 500, "Internal Server Error", Message(), BrokenBody(TimeoutError())
        )

        code, stderr = self.run_failing(error)

        self.assertEqual(code, 1)
        self.assertEqual(stderr, "ERROR: HTTP 500: Internal Server Error\n")


class ClosedPipe(StringIO):
    """A stdout whose reader has gone: writing or flushing fails as it does on a closed pipe."""

    def __init__(self, fd: int) -> None:
        super().__init__()
        self.fd = fd

    def write(self, text: str) -> int:
        raise BrokenPipeError(32, "Broken pipe")

    def flush(self) -> None:
        raise BrokenPipeError(32, "Broken pipe")

    def fileno(self) -> int:
        return self.fd


class BrokenPipeTests(unittest.TestCase):
    def run_into_closed_pipe(self, *argv: str) -> tuple[int, str]:
        """Run main() with stdout a closed pipe; return (code, stderr)."""
        fd = os.open(os.devnull, os.O_WRONLY)
        self.addCleanup(os.close, fd)
        stderr = StringIO()
        with (
            patch("zquota.fetch_json", return_value=sample_payload()),
            patch("sys.stdout", new=ClosedPipe(fd)),
            patch("sys.stderr", new=stderr),
        ):
            code = zquota.main(["--api-key", "test", *argv])
        return code, stderr.getvalue()

    def test_closed_pipe_stops_a_single_run_quietly(self) -> None:
        self.assertEqual(self.run_into_closed_pipe("--json"), (141, ""))

    def test_closed_pipe_stops_a_watch_quietly(self) -> None:
        self.assertEqual(self.run_into_closed_pipe("--watch", "30", "--compact"), (141, ""))


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
