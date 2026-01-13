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

from flask import Flask, redirect, render_template_string, request, url_for

from src.filter import ContentModerator

BASE_DIR = Path(__file__).parent
PENDING_FILE = BASE_DIR / "pending_posts.json"

app = Flask(__name__)
moderator = ContentModerator.load_default()


def _load_pending() -> List[Dict[str, Any]]:
    if not PENDING_FILE.exists():
        return []
    try:
        return json.loads(PENDING_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_pending(items: List[Dict[str, Any]]) -> None:
    PENDING_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def _next_id(items: List[Dict[str, Any]]) -> int:
    if not items:
        return 1
    return max(int(it.get("id", 0)) for it in items) + 1


def highlight_text(text: str, forbidden_keywords: List[str], other_keywords: List[str] = None) -> Markup:
    """Metindeki yasaklı kelimeleri kırmızı, diğer riskli kelimeleri farklı renklerle işaretle."""
    if not text:
        return Markup("")
    
    if not forbidden_keywords and not other_keywords:
        return Markup(escape(text))
    
    result = escape(text)
    
    # Önce diğer riskli kelimeleri işaretle (spam, politics - sarı/turuncu)
    if other_keywords:
        unique_other = sorted({k for k in other_keywords if k}, key=len, reverse=True)
        if unique_other:
            pattern_other = re.compile("(" + "|".join(re.escape(k) for k in unique_other) + ")", re.IGNORECASE)
            result = pattern_other.sub(lambda m: f'<mark class="hl-other">{escape(m.group(0))}</mark>', result)
    
    # Sonra yasaklı kelimeleri işaretle (kırmızı) - öncelikli olduğu için sonra yapıyoruz
    if forbidden_keywords:
        unique_forbidden = sorted({k for k in forbidden_keywords if k}, key=len, reverse=True)
        if unique_forbidden:
            pattern_forbidden = re.compile("(" + "|".join(re.escape(k) for k in unique_forbidden) + ")", re.IGNORECASE)
            result = pattern_forbidden.sub(lambda m: f'<mark class="hl-forbidden">{escape(m.group(0))}</mark>', result)
    
    return Markup(result)


USER_FORM_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="utf-8" />
    <title>Spam Filter Test Arayüzü</title>
    <style>
        :root { color-scheme: light; }
        body { font-family: Arial, sans-serif; margin: 24px; background: #f5f5f5; }
        .container { max-width: 820px; margin: 0 auto; padding: 24px; background: #fff; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,.08); }
        h1 { margin-bottom: 8px; }
        .lead { color: #444; margin-bottom: 20px; }
        form { display: grid; gap: 12px; }
        label { font-weight: 600; font-size: 14px; }
        input[type="text"], textarea, select {
            width: 100%; padding: 12px; font-size: 15px; border: 1px solid #d1d5db; border-radius: 8px; box-sizing: border-box;
        }
        textarea { min-height: 160px; resize: vertical; }
        button { justify-self: flex-start; margin-top: 4px; padding: 10px 18px; font-size: 15px; cursor: pointer; border-radius: 8px; border: none; background: #2563eb; color: white; }
        .result { margin-top: 24px; padding: 16px; border-radius: 10px; background: #eef2ff; border: 1px solid #d9dfff; }
        .grid { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }
        pre { background: #111; color: #f7f7f7; padding: 12px; overflow-x: auto; border-radius: 6px; }
        dt { font-weight: bold; margin-top: 8px; }
        .badge { display: inline-block; padding: 4px 8px; border-radius: 999px; background: #e0e7ff; color: #1d4ed8; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Forum Gönderi Oluştur</h1>
        <p class="lead">Kullanıcı bu formu doldurduğunda gönderi doğrudan yayına çıkmaz; önce moderasyon kuyruğuna düşer.</p>
        <form method="post">
            <div class="grid">
                <div>
                    <label for="title">Başlık</label>
                    <input id="title" name="title" type="text" placeholder="Örn: Satılık telefon" value="{{ title }}" />
                </div>
                <div>
                    <label for="category">Kategori</label>
                    <input id="category" name="category" type="text" placeholder="Örn: İkinci el / Duyuru / Politika" value="{{ category }}" />
                </div>
            </div>
            <div>
                <label for="body">Ana metin</label>
                <textarea id="body" name="body" placeholder="Gönderiyi buraya yazın">{{ body }}</textarea>
            </div>
            <div class="grid">
                <div>
                    <label for="notes">Moderasyon notu (opsiyonel)</label>
                    <textarea id="notes" name="notes" placeholder="Yetkili öncesi manuel notlar">{{ notes }}</textarea>
                </div>
            </div>
            <button type="submit">Gönder (Beklemeye Al)</button>
        </form>

        {% if success %}
          <div class="result">
            <strong>Gönderiniz moderasyon için kuyruğa alındı.</strong><br />
            Yetkili incelemesi tamamlandığında sisteminizden uygun aksiyonu alabilirsiniz.
          </div>
        {% endif %}
        <p style="margin-top:24px; font-size:13px; color:#666;">
          Yetkili ekranı için: <code>{{ admin_url }}</code>
        </p>
    </div>
</body>
</html>
"""
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


@app.route("/", methods=["GET", "POST"])
def submit_post():
    title = ""
    body = ""
    category = ""
    notes = ""
    if request.method == "POST":
        title = request.form.get("title", "")
        body = request.form.get("body", "")
        category = request.form.get("category", "")
        notes = request.form.get("notes", "")

        items = _load_pending()
        post_id = _next_id(items)
        items.append(
            {
                "id": post_id,
                "title": title,
                "body": body,
                "category": category,
                "notes": notes,
                "status": "pending",
                "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            }
        )
        _save_pending(items)
        return render_template_string(
            USER_FORM_TEMPLATE,
            title="",
            body="",
            category="",
            notes="",
            success=True,
            admin_url=url_for("admin_list", _external=True),
        )

    return render_template_string(
        USER_FORM_TEMPLATE,
        title=title,
        body=body,
        category=category,
        notes=notes,
        success=False,
        admin_url=url_for("admin_list", _external=True),
    )


ADMIN_LIST_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="utf-8" />
  <title>Bekleyen Gönderiler - Admin</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 24px; background:#f5f5f5; }
    .container { max-width: 900px; margin: 0 auto; background:#fff; padding:24px; border-radius:12px; box-shadow:0 2px 8px rgba(0,0,0,.08); }
    table { width: 100%; border-collapse: collapse; margin-top: 12px; }
    th, td { padding: 8px 10px; border-bottom: 1px solid #e5e7eb; text-align:left; font-size:14px; }
    th { background:#f3f4f6; }
    a.btn { display:inline-block; padding:6px 10px; border-radius:999px; background:#2563eb; color:#fff; text-decoration:none; font-size:13px; }
    .badge { padding:2px 8px; border-radius:999px; font-size:11px; background:#fee2e2; color:#b91c1c; }
    .empty { margin-top:16px; color:#666; font-size:14px; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Beklemede Olan Gönderiler</h1>
    {% if items %}
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Başlık</th>
            <th>Kategori</th>
            <th>Oluşturma</th>
            <th>Durum</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {% for it in items %}
          <tr>
            <td>{{ it.id }}</td>
            <td>{{ it.title or "-" }}</td>
            <td>{{ it.category or "-" }}</td>
            <td>{{ it.created_at }}</td>
            <td><span class="badge">{{ it.status }}</span></td>
            <td><a class="btn" href="{{ url_for('admin_review', post_id=it.id) }}">İncele</a></td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    {% else %}
      <p class="empty">Şu anda beklemede gönderi bulunmuyor.</p>
    {% endif %}
  </div>
</body>
</html>
"""


ADMIN_REVIEW_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="utf-8" />
  <title>Gönderi İncele - Admin</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 24px; background:#f5f5f5; }
    .container { max-width: 900px; margin: 0 auto; background:#fff; padding:24px; border-radius:12px; box-shadow:0 2px 8px rgba(0,0,0,.08); }
    .field { margin-bottom: 16px; }
    .label { font-weight:600; margin-bottom:4px; font-size:14px; }
    .value-box { padding:10px 12px; border-radius:8px; background:#f9fafb; border:1px solid #e5e7eb; white-space:pre-wrap; font-size:14px; }
    .meta { margin-top: 20px; padding: 12px; border-radius: 8px; background:#eef2ff; border:1px solid #d9dfff; }
    pre { background:#111; color:#f7f7f7; padding:10px; border-radius:6px; overflow-x:auto; font-size:13px; }
    a { color:#2563eb; text-decoration:none; font-size:14px; }
    mark.hl-forbidden { background:#fee2e2; color:#b91c1c; padding:2px 4px; border-radius:3px; font-weight:600; border:1px solid #fca5a5; }
    mark.hl-other { background:#fef3c7; color:#92400e; padding:2px 4px; border-radius:3px; }
    .keywords-info { margin-top: 12px; padding: 10px; background:#fef2f2; border-left:3px solid #dc2626; border-radius:4px; }
    .keywords-info h4 { margin:0 0 8px 0; color:#991b1b; font-size:14px; }
    .keywords-list { font-size:13px; color:#7f1d1d; }
  </style>
</head>
<body>
  <div class="container">
    <a href="{{ url_for('admin_list') }}">&larr; Bekleyen listeye dön</a>
    <h1 style="margin-top:12px;">Gönderi #{{ item.id }} İncele</h1>

    <div class="field">
      <div class="label">Başlık</div>
      <div class="value-box">{{ marked_title|safe }}</div>
    </div>
    <div class="field">
      <div class="label">Kategori</div>
      <div class="value-box">{{ marked_category|safe }}</div>
    </div>
    <div class="field">
      <div class="label">Ana Metin</div>
      <div class="value-box">{{ marked_body|safe }}</div>
    </div>
    <div class="field">
      <div class="label">Moderasyon Notu</div>
      <div class="value-box">{{ marked_notes|safe }}</div>
    </div>

    {% if forbidden_words %}
    <div class="keywords-info">
      <h4>⚠️ Yasaklı Kelimeler Bulundu</h4>
      <div class="keywords-list">
        <strong>Metinde geçen yasaklı kelimeler:</strong>
        <ul style="margin:6px 0 0 20px; padding:0;">
          {% for word in forbidden_words %}
          <li>{{ word }}</li>
          {% endfor %}
        </ul>
      </div>
    </div>
    {% endif %}

    <div class="meta">
      <h3>Spam Filtresi Sonucu</h3>
      <p><strong>Durum:</strong> {{ result.status.value }}</p>
      <p><strong>Neden:</strong> {{ result.reason }}</p>
      <p><strong>Skorlar:</strong></p>
      <pre>{{ result.scores | tojson(indent=2) }}</pre>
      {% if result.metadata %}
      <p><strong>Ek Bilgi:</strong></p>
      <pre>{{ result.metadata | tojson(indent=2) }}</pre>
      {% endif %}
    </div>

    <p style="margin-top:18px; font-size:13px; color:#6b7280;">
      Bu ekranda içerik sadece görüntülenebilir; üzerinde değişiklik yapılamaz.
      Sistem entegrasyonunda bu sonuca göre "Yayınla / Reddet / Yeniden incele" butonlarını ekleyebilirsiniz.
    </p>
  </div>
</body>
</html>
"""


@app.route("/admin")
def admin_list():
    items = _load_pending()
    pending = [it for it in items if it.get("status") == "pending"]
    return render_template_string(ADMIN_LIST_TEMPLATE, items=pending)


@app.route("/admin/post/<int:post_id>")
def admin_review(post_id: int):
    items = _load_pending()
    item = next((it for it in items if int(it.get("id", 0)) == post_id), None)
    if not item:
        return redirect(url_for("admin_list"))

    combined = "\n".join(
        [
            item.get("title") or "",
            item.get("category") or "",
            item.get("body") or "",
            item.get("notes") or "",
        ]
    )
    mod_result = moderator.moderate(combined)
    meta = mod_result.metadata or {}
    forbidden = meta.get("matches", [])
    spam_kw = meta.get("spam_keywords", [])
    politics_kw = meta.get("politics_keywords", [])
    other_keywords: List[str] = list({*spam_kw, *politics_kw})

    marked_title = highlight_text(item.get("title") or "-", forbidden, other_keywords)
    marked_category = highlight_text(item.get("category") or "-", forbidden, other_keywords)
    marked_body = highlight_text(item.get("body") or "-", forbidden, other_keywords)
    marked_notes = highlight_text(item.get("notes") or "-", forbidden, other_keywords)

    return render_template_string(
        ADMIN_REVIEW_TEMPLATE,
        item=item,
        result=mod_result,
        marked_title=marked_title,
        marked_category=marked_category,
        marked_body=marked_body,
        marked_notes=marked_notes,
        forbidden_words=forbidden,
    )


if __name__ == "__main__":
    import os
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", "5002"))
    app.run(debug=debug_mode, host=host, port=port)

