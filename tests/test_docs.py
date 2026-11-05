"""Docs site tests."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

import zquota

REFERENCE = (
    Path(__file__).resolve().parents[1]
    / "website"
    / "src"
    / "content"
    / "docs"
    / "reference"
    / "cli.mdx"
)


def documented_flags() -> list[frozenset[str]]:
    """Return each row of the CLI reference page's flag lists as its set of option strings."""
    text = REFERENCE.read_text(encoding="utf-8")
    rows: list[frozenset[str]] = []
    for body in re.findall(r"^export const \w+ = \[(.*?)^\];", text, re.M | re.S):
        for short, flag in re.findall(r'(?:short: "(-\w)", )?flag: "(--[a-z0-9-]+)"', body):
            rows.append(frozenset(filter(None, (short, flag))))
    return rows


def parser_flags() -> list[frozenset[str]]:
    """Return each of the parser's options as its set of option strings."""
    # argparse has no public way to list a parser's options.
    # pylint: disable-next=protected-access
    actions = zquota.build_parser()._actions
    return [frozenset(action.option_strings) for action in actions if action.option_strings]


class CLIReferenceTests(unittest.TestCase):
    def test_cli_reference_covers_every_flag(self) -> None:
        """The CLI reference documents exactly the options zquota accepts, each pairing right.

        The page is written by hand so the flags can be explained, which means nothing
        regenerates it when one changes. Each row of its flag lists is compared with an
        option of build_parser(), so a flag added, removed, renamed or misspelt on either side,
        or a short form paired with the wrong long one, fails here.
        """
        documented = documented_flags()
        self.assertEqual(
            len(documented), len(set(documented)), "the page lists a flag more than once"
        )
        self.assertEqual(
            sorted(map(sorted, documented)),
            sorted(map(sorted, parser_flags())),
            f"update {REFERENCE.relative_to(REFERENCE.parents[5])} to match build_parser()",
        )


if __name__ == "__main__":
    unittest.main()
