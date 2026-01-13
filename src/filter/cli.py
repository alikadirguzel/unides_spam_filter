"""Minimal CLI wrapper for manual testing."""

from __future__ import annotations

import argparse
import json
import sys

from .moderator import ContentModerator


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the spam filter against a snippet of text.")
    parser.add_argument("text", help="Gönderi içeriği")
    args = parser.parse_args(argv)

    moderator = ContentModerator.load_default()
    result = moderator.moderate(args.text)

    print(json.dumps({"status": result.status.value, "reason": result.reason, "scores": result.scores}, ensure_ascii=False))
    if result.metadata:
        print(json.dumps(result.metadata, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

