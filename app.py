"""Minimal Flask interface to manually test the content moderator."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from markupsafe import Markup, escape

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from flask import Flask, redirect, render_template_string, request, url_for, jsonify

from src.filter import ContentModerator

BASE_DIR = Path(__file__).parent
PENDING_FILE = BASE_DIR / "pending_posts.json"

app = Flask(__name__)
moderator = ContentModerator.load_default()


def moderation_result_to_response(result):
    return {
        "status": result.status.value if hasattr(result.status, "value") else str(result.status),
        "reason": result.reason,
        "scores": {
            "spam_rule": result.scores.get("spam_rule", 0),
            "spam_model": result.scores.get("spam_model", 0),
            "politics_rule": result.scores.get("politics_rule", 0),
            "politics_model": result.scores.get("politics_model", 0)
        },
        "politics_keywords": result.metadata.get("politics_keywords", [])
    }

@app.route("/api/moderate", methods=["POST"])
def moderate_api():
    data = request.get_json()

    if not data:
        return jsonify({"error": "JSON body required"}), 400

    combined = "\n".join([
        data.get("title", ""),
        data.get("category", ""),
        data.get("body", ""),
        data.get("notes", ""),
    ])

    mod_result = moderator.moderate(combined)
    meta = mod_result.metadata or {}

    forbidden = meta.get("forbidden_words", [])
    spam_kw = meta.get("spam_keywords", [])
    politics_kw = meta.get("politics_keywords", [])

    response = {
        "moderation": moderation_result_to_response(mod_result),

        "analysis": {
            "forbidden": {
                "count": len(forbidden),
                "words": forbidden
            },
            "spam": {
                "count": len(spam_kw),
                "keywords": spam_kw
            },
            "politics": {
                "count": len(politics_kw),
                "keywords": politics_kw
            }
        },

    }

    return jsonify(response)


if __name__ == "__main__":
    import os
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", "5002"))
    app.run(debug=debug_mode, host=host, port=port)
