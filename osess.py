#!/usr/bin/env python3
"""osess.py — snapshot local de la base Ollama desktop, listage, export .md."""
import argparse, os, re, shutil, sqlite3, sys, tempfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
LOCAL_DB = HERE / "db.sqlite"          # copie de travail (gitignorée)

def client_db():
    # Windows : %LOCALAPPDATA%\Ollama\db.sqlite ou %APPDATA%\Ollama\db.sqlite
    for base in ("LOCALAPPDATA", "APPDATA"):
        p = Path(os.environ.get(base, "")) / "Ollama" / "db.sqlite"
        if p.exists():
            return p
    # Linux / macOS : ~/.ollama/db.sqlite (install par défaut)
    p = Path.home() / ".ollama" / "db.sqlite"
    if p.exists():
        return p
    sys.exit(
        "Base cliente Ollama introuvable.\n"
        "  Windows : %LOCALAPPDATA%\\Ollama\\db.sqlite\n"
        "  Linux/macOS : ~/.ollama/db.sqlite\n"
        "Si Ollama est installé ailleurs, arrêtez le client Ollama puis "
        "copiez manuellement db.sqlite dans ce dossier avant de relancer."
    )

def confirm(question, default=True):
    r = input(f"{question} [{'O/n' if default else 'o/N'}] : ").strip().lower()
    return (default if not r else r in ("o", "oui", "y", "yes"))

def pull(assume_yes=False):
    if LOCAL_DB.exists():
        age = datetime.fromtimestamp(LOCAL_DB.stat().st_mtime)
        if not (assume_yes or confirm(
                f"Une copie locale existe (du {age:%Y-%m-%d %H:%M}). L'écraser ?")):
            print("copie conservée.")
            return
    src = sqlite3.connect(str(client_db()))
    dst = sqlite3.connect(LOCAL_DB)
    with dst:
        src.backup(dst)
    dst.close()
    src.close()
    print(f"snapshot OK -> {LOCAL_DB}")

def open_local():
    if LOCAL_DB.exists():
        return sqlite3.connect(LOCAL_DB)
    print(f"Aucune copie locale ({LOCAL_DB.name}).")
    if confirm("En créer une depuis la base cliente ?"):
        pull()
        return sqlite3.connect(LOCAL_DB)
    sys.exit("annulé.")

def list_sessions(con):
    return con.execute("""
        SELECT c.id, c.title, COUNT(m.id),
               (SELECT content FROM messages WHERE chat_id=c.id AND role='user'
                ORDER BY id LIMIT 1),
               (SELECT MAX(updated_at) FROM messages WHERE chat_id=c.id) AS last
        FROM chats c LEFT JOIN messages m ON m.chat_id = c.id
        GROUP BY c.id ORDER BY last DESC
    """).fetchall()

def slugify(text, maxlen=40):
    import unicodedata
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()[:maxlen] or "session"

def export_md(con, chat_id, out=None):
    chat = con.execute("SELECT id, title, created_at FROM chats WHERE id=?",
                       (chat_id,)).fetchone()
    if not chat:
        sys.exit(f"introuvable : {chat_id}")
    msgs = con.execute("""
        SELECT role, content, model_name FROM messages
        WHERE chat_id = ? AND role IN ('user','assistant')
          AND TRIM(COALESCE(content,'')) <> ''
        ORDER BY id
    """, (chat_id,)).fetchall()
    title = chat[1] or (msgs[0][1][:60] if msgs else "(sans titre)")
    stamp = f"{datetime.now():%Y%m%d-%H%M}"
    if out is None:
        out = Path(f"{slugify(title)}-{stamp}.md")
    else:
        out = out.with_name(f"{out.stem}-{stamp}{out.suffix}")

    lines = [f"# {title}", "",
             f"> id: `{chat[0]}` · créé : {chat[2]} · "
             f"exporté : {datetime.now().isoformat(timespec='seconds')}", ""]
    for role, content, model in msgs:
        if role == "user":
            lines += ["## 👤 User", "", content, ""]
        else:
            lines += [f"## 🤖 Assistant{f' — {model}' if model else ''}", "", content, ""]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"OK -> {out} ({len(msgs)} messages)")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?", choices=["pull", "list", "export"])
    ap.add_argument("target", nargs="?")
    ap.add_argument("-o", "--out")
    ap.add_argument("-y", "--yes", action="store_true", help="confirmer tout (scripts)")
    args = ap.parse_args()

    if args.cmd == "pull":
        pull(args.yes)
        return
    con = open_local()          # copie locale d'abord, question seulement si absente
    try:
        if args.cmd == "list":
            for i, (cid, title, n, first, last) in enumerate(list_sessions(con), 1):
                print(f"[{i:>3}] {cid[:8]}  {n:>3} msg  {last or ''}  "
                      f"{title or (first or '')[:60]}")
        else:
            if not args.target:
                sys.exit("cible attendue : n° affiché par 'list' ou préfixe d'id")
            tid = args.target.strip()
            row = con.execute("SELECT id FROM chats WHERE id=? OR id LIKE ?",
                              (tid, tid + "%")).fetchone()
            if not row:
                sys.exit(f"id '{tid}' introuvable")
            export_md(con, row[0], Path(args.out) if args.out else None)
    finally:
        con.close()

if __name__ == "__main__":
    main()
