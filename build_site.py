#!/usr/bin/env python3
import json, shutil, yaml
from pathlib import Path

ROOT = Path(__file__).parent
AUDIO_SRC = Path.home() / "sewing-leads-saas/milana-lesson/audio/esenia"
AUDIO_DST = ROOT / "audio"

def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

CSS = """
body { font-family: system-ui; max-width: 640px; margin: 20px auto; padding: 16px; background: #f5f5f5; }
h1 { text-align: center; color: #2E7D32; } h2 { color: #37474f; }
.card { border: 2px solid #4CAF50; border-radius: 16px; padding: 16px; margin: 14px 0; text-align: center; background: #fff; box-shadow: 0 2px 8px rgba(0,0,0,.1); }
.en { font-size: 26px; font-weight: bold; color: #2E7D32; }
.ru { font-size: 17px; color: #555; margin-top: 6px; }
.tr { font-size: 15px; color: #888; font-style: italic; margin-top: 4px; }
.bigemoji { font-size: 48px; }
.badge { display: inline-block; padding: 4px 14px; border-radius: 20px; color: #fff; font-weight: bold; margin-bottom: 8px; }
.badge.lulu { background: #e91e63; } .badge.larry { background: #2196f3; }
.status { min-height: 20px; margin-top: 6px; font-size: 15px; color: #2E7D32; }
button { font-size: 18px; padding: 10px 20px; margin: 6px 4px; border-radius: 12px; border: none; cursor: pointer; }
.play { background: #4CAF50; color: #fff; } .slow { background: #FF9800; color: #fff; }
button:active { transform: scale(.95); }
.opt { display: block; width: 100%; margin: 8px 0; background: #fff; border: 2px solid #90a4ae; color: #000; font-size: 20px; padding: 12px; border-radius: 12px; }
.opt.good { background: #c8e6c9; border-color: #4CAF50; }
.opt.bad { background: #ffcdd2; border-color: #e53935; }
.note { color: #777; font-size: 14px; font-style: italic; }
"""

JS = """
function playOne(id, stId) {
  const el = document.getElementById(id);
  const st = stId ? document.getElementById(stId) : null;
  if (!el) return;
  el.currentTime = 0;
  if (st) st.textContent = '▶️ Играет...';
  el.onended = () => { if (st) st.textContent = '✅ Теперь повтори вслух!'; };
  el.onerror = () => { if (st) st.textContent = '❌ Файл не найден или повреждён'; };
  const p = el.play();
  if (p) p.catch(e => { if (st) st.textContent = '❌ ' + e.message; });
}
function playSeq(ids) {
  let i = 0;
  (function next() {
    if (i >= ids.length) return;
    const el = document.getElementById(ids[i++]);
    if (!el) { next(); return; }
    el.currentTime = 0;
    el.onended = () => setTimeout(next, 500);
    el.play().catch(() => setTimeout(next, 500));
  })();
}
function answer(btn, correct, okId, stId) {
  const st = document.getElementById(stId);
  if (correct) {
    btn.classList.add('good');
    st.textContent = '✅ Правильно! Молодец! 🎉';
    playOne(okId, null);
  } else {
    btn.classList.add('bad');
    st.textContent = '❌ Не совсем. Попробуй ещё раз!';
    setTimeout(() => btn.classList.remove('bad'), 900);
  }
}
"""

TEMPLATE = """<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{TITLE}}</title>
<style>{{CSS}}</style></head><body>
{{BODY}}
<script>{{JS}}</script>
</body></html>
"""

def build():
    lesson = yaml.safe_load((ROOT / "lesson.yaml").read_text(encoding="utf-8"))
    AUDIO_DST.mkdir(exist_ok=True)
    for f in AUDIO_SRC.glob("*.mp3"):
        shutil.copy2(f, AUDIO_DST / f.name)

    parts = [f"<h1>{lesson.get('emoji', '')} {esc(lesson['title'])}</h1>"]
    for si, sec in enumerate(lesson.get("sections", []), 1):
        t = sec.get("type")
        parts.append(f"<h2>{esc(sec['title'])}</h2>")
        if sec.get("note"):
            parts.append(f"<p class=\"note\">{esc(sec['note'])}</p>")
        if t in ("dialog", "song", "words", "phrases"):
            ids = []
            for li, line in enumerate(sec.get("lines", []), 1):
                base = f"{si:02d}_{li:02d}"
                ids.append(f"a_{base}")
                badge = f"<span class=\"badge {line['speaker'].lower()}\">{esc(line['speaker'])}</span>" if line.get("speaker") else ""
                emo = f"<div class=\"bigemoji\">{line['emoji']}</div>" if line.get("emoji") else ""
                parts.append(
                    f"<div class=\"card\">{badge}{emo}"
                    f"<div class=\"en\">{esc(line['en'])}</div>"
                    f"<div class=\"ru\">{esc(line['ru'])}</div>"
                    f"<div class=\"tr\">{esc(line['translit'])}</div>"
                    f"<audio id=\"a_{base}\" src=\"audio/{base}.mp3\" preload=\"auto\"></audio>"
                    f"<audio id=\"s_{base}\" src=\"audio/{base}_slow.mp3\" preload=\"auto\"></audio><br>"
                    f"<button class=\"slow\" onclick=\"playOne('s_{base}','st_{base}')\">🐢 Медленно</button>"
                    f"<button class=\"play\" onclick=\"playOne('a_{base}','st_{base}')\">🔊 Нормально</button>"
                    f"<div class=\"status\" id=\"st_{base}\"></div></div>"
                )
            if t in ("dialog", "song"):
                parts.append(f"<button class=\"play\" onclick='playSeq({json.dumps(ids)})'>▶️ Послушать целиком</button>")
        elif t == "quiz":
            for qi, q in enumerate(sec.get("questions", []), 1):
                base = f"{si:02d}_q{qi}"
                opts = "".join(
                    f"<button class=\"opt\" onclick=\"answer(this,{'true' if o.get('correct') else 'false'},'ok_{base}','stq_{base}')\">{esc(o['text'])}</button>"
                    for o in q["options"]
                )
                parts.append(
                    f"<div class=\"card\"><div class=\"en\">{esc(q['q'])}</div>"
                    f"<div class=\"ru\">{esc(q['q_ru'])}</div>"
                    f"<audio id=\"q_{base}\" src=\"audio/{base}.mp3\" preload=\"auto\"></audio>"
                    f"<audio id=\"ok_{base}\" src=\"audio/{base}_ok.mp3\" preload=\"auto\"></audio>"
                    f"<button class=\"play\" onclick=\"playOne('q_{base}','stq_{base}')\">🔊 Послушать вопрос</button>"
                    f"{opts}<div class=\"status\" id=\"stq_{base}\"></div></div>"
                )

    html = (TEMPLATE
            .replace("{{TITLE}}", esc(lesson["title"]))
            .replace("{{CSS}}", CSS)
            .replace("{{JS}}", JS)
            .replace("{{BODY}}", "\n".join(parts)))
    (ROOT / "index.html").write_text(html, encoding="utf-8")
    print(f"✅ index.html собран, аудио: {len(list(AUDIO_DST.glob('*.mp3')))} файлов")

if __name__ == "__main__":
    build()
