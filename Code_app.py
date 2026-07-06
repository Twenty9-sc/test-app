import os
import uuid
import sqlite3
from flask import (Flask, render_template, request, redirect,
                   url_for, jsonify, send_from_directory)

# ── Config ────────────────────────────────────────────────────────────────────
# Utilise le dossier du script comme dossier de base
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
DB_PATH       = os.path.join(BASE_DIR, "procapp.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXT   = {"png", "jpg", "jpeg", "gif", "webp", "mp4", "mov", "webm", "avi"}
MAX_MB        = 200  # Mo

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_MB * 1024 * 1024

# S'assurer que le dossier des uploads existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

def is_video(filename):
    return filename.rsplit(".", 1)[1].lower() in {"mp4", "mov", "webm", "avi"}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Activer impérativement les clés étrangères à CHAQUE connexion
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ── Init DB ───────────────────────────────────────────────────────────────────

def init_db():
    with get_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS processus (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                nom          TEXT    NOT NULL,
                produit      TEXT    NOT NULL DEFAULT '',
                categorie   TEXT    NOT NULL DEFAULT 'Production',
                description TEXT,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS etapes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                proc_id     INTEGER NOT NULL REFERENCES processus(id) ON DELETE CASCADE,
                ordre       INTEGER NOT NULL,
                titre       TEXT    NOT NULL,
                instruction TEXT,
                duree_min   INTEGER DEFAULT NULL,
                avertissement TEXT  DEFAULT NULL
            );

            CREATE TABLE IF NOT EXISTS medias (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                etape_id    INTEGER NOT NULL REFERENCES etapes(id) ON DELETE CASCADE,
                filename    TEXT    NOT NULL,
                is_video    INTEGER NOT NULL DEFAULT 0,
                legende     TEXT    DEFAULT ''
            );
        """)


# ── Routes — liste & recherche ─────────────────────────────────────────────────

@app.route("/")
def index():
    with get_db() as db:
        cats = [r[0] for r in db.execute(
            "SELECT DISTINCT categorie FROM processus ORDER BY categorie").fetchall()]
        total = db.execute("SELECT COUNT(*) FROM processus").fetchone()[0]
        recents = db.execute(
            "SELECT * FROM processus ORDER BY updated_at DESC LIMIT 5").fetchall()
    return render_template("index.html", categories=cats, total=total, recents=recents)


@app.route("/api/search")
def api_search():
    q   = request.args.get("q", "").strip()
    cat = request.args.get("cat", "").strip()
    with get_db() as db:
        sql    = "SELECT id, nom, produit, categorie, updated_at FROM processus WHERE 1=1"
        params = []
        if q:
            sql   += " AND (nom LIKE ? OR produit LIKE ? OR description LIKE ?)"
            params += [f"%{q}%"] * 3
        if cat:
            sql   += " AND categorie = ?"
            params.append(cat)
        sql += " ORDER BY updated_at DESC"
        rows = db.execute(sql, params).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/categories")
def api_categories():
    with get_db() as db:
        cats = [r[0] for r in db.execute(
            "SELECT DISTINCT categorie FROM processus ORDER BY categorie").fetchall()]
    return jsonify(cats)


# ── Routes — détail ────────────────────────────────────────────────────────────

@app.route("/processus/<int:pid>")
def detail(pid):
    with get_db() as db:
        proc = db.execute("SELECT * FROM processus WHERE id=?", (pid,)).fetchone()
        if not proc:
            return redirect(url_for("index"))
        etapes = db.execute(
            "SELECT * FROM etapes WHERE proc_id=? ORDER BY ordre", (pid,)).fetchall()
        medias_map = {}
        for e in etapes:
            medias_map[e["id"]] = db.execute(
                "SELECT * FROM medias WHERE etape_id=?", (e["id"],)).fetchall()
    return render_template("detail.html", proc=proc, etapes=etapes, medias=medias_map)


# ── Routes — création ──────────────────────────────────────────────────────────

@app.route("/nouveau", methods=["GET", "POST"])
def nouveau():
    if request.method == "POST":
        pid = _save_processus(None, request)
        return redirect(url_for("detail", pid=pid))
    with get_db() as db:
        cats = [r[0] for r in db.execute(
            "SELECT DISTINCT categorie FROM processus ORDER BY categorie").fetchall()]
    return render_template("formulaire.html", proc=None, etapes=[], medias={}, categories=cats)


# ── Routes — modification ──────────────────────────────────────────────────────

@app.route("/modifier/<int:pid>", methods=["GET", "POST"])
def modifier(pid):
    with get_db() as db:
        proc = db.execute("SELECT * FROM processus WHERE id=?", (pid,)).fetchone()
        if not proc:
            return redirect(url_for("index"))
        if request.method == "POST":
            _save_processus(pid, request)
            return redirect(url_for("detail", pid=pid))
        
        etapes = db.execute(
            "SELECT * FROM etapes WHERE proc_id=? ORDER BY ordre", (pid,)).fetchall()
        medias_map = {}
        for e in etapes:
            medias_map[e["id"]] = db.execute(
                "SELECT * FROM medias WHERE etape_id=?", (e["id"],)).fetchall()
        cats = [r[0] for r in db.execute(
            "SELECT DISTINCT categorie FROM processus ORDER BY categorie").fetchall()]
    return render_template("formulaire.html", proc=proc, etapes=etapes, medias=medias_map, categories=cats)


def _save_processus(pid, req):
    f  = req.form
    files = req.files

    with get_db() as db:
        if pid is None:
            cur = db.execute("""
                INSERT INTO processus (nom, produit, categorie, description)
                VALUES (?,?,?,?)
            """, (f["nom"].strip(), f.get("produit","").strip(),
                  f.get("categorie","Production"), f.get("description","").strip()))
            pid = cur.lastrowid
        else:
            db.execute("""
                UPDATE processus SET nom=?, produit=?, categorie=?, description=?,
                    updated_at=CURRENT_TIMESTAMP WHERE id=?
            """, (f["nom"].strip(), f.get("produit","").strip(),
                  f.get("categorie","Production"), f.get("description","").strip(), pid))
            
            # Nettoyage avant suppression des étapes : on efface physiquement les fichiers médias
            old_etapes = db.execute("SELECT id FROM etapes WHERE proc_id=?", (pid,)).fetchall()
            for oe in old_etapes:
                old_medias = db.execute("SELECT filename FROM medias WHERE etape_id=?", (oe["id"],)).fetchall()
                for om in old_medias:
                    _delete_file(om["filename"])
            
            # Suppression des étapes (les entrées 'medias' en BDD sauteront grâce au ON DELETE CASCADE)
            db.execute("DELETE FROM etapes WHERE proc_id=?", (pid,))

        # Insérer les nouvelles étapes transmises par le formulaire
        titres         = f.getlist("etape_titre[]")
        instructions   = f.getlist("etape_instruction[]")
        durees         = f.getlist("etape_duree[]")
        avertissements = f.getlist("etape_avert[]")

        for i, (titre, instruction, duree, avert) in enumerate(
                zip(titres, instructions, durees, avertissements), 1):
            if not titre.strip():
                continue
            d = int(duree) if duree.strip().isdigit() else None
            cur2 = db.execute("""
                INSERT INTO etapes (proc_id, ordre, titre, instruction, duree_min, avertissement)
                VALUES (?,?,?,?,?,?)
            """, (pid, i, titre.strip(), instruction.strip(), d,
                  avert.strip() if avert.strip() else None))
            eid = cur2.lastrowid

            # Gestion des fichiers médias liés à l'étape `i`
            field_key = f"medias_{i}[]"
            legendes  = f.getlist(f"legende_{i}[]")
            uploaded  = files.getlist(field_key)
            
            for j, file in enumerate(uploaded):
                if file and file.filename and allowed(file.filename):
                    ext      = file.filename.rsplit(".", 1)[1].lower()
                    fname    = f"{uuid.uuid4().hex}.{ext}"
                    file.save(os.path.join(app.config["UPLOAD_FOLDER"], fname))
                    
                    leg      = legendes[j] if j < len(legendes) else ""
                    db.execute("""
                        INSERT INTO medias (etape_id, filename, is_video, legende)
                        VALUES (?,?,?,?)
                    """, (eid, fname, 1 if is_video(fname) else 0, leg.strip()))
    return pid


def _delete_file(filename):
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass  # Évite de bloquer l'application si le fichier est verrouillé


# ── Routes — suppression ───────────────────────────────────────────────────────

@app.route("/supprimer/<int:pid>", methods=["POST"])
def supprimer(pid):
    with get_db() as db:
        etapes = db.execute("SELECT id FROM etapes WHERE proc_id=?", (pid,)).fetchall()
        for e in etapes:
            for m in db.execute("SELECT filename FROM medias WHERE etape_id=?", (e["id"],)).fetchall():
                _delete_file(m["filename"])
        db.execute("DELETE FROM processus WHERE id=?", (pid,))
    return redirect(url_for("index"))


@app.route("/supprimer_media/<int:mid>", methods=["POST"])
def supprimer_media(mid):
    with get_db() as db:
        m = db.execute("SELECT * FROM medias WHERE id=?", (mid,)).fetchone()
        if m:
            _delete_file(m["filename"])
            db.execute("DELETE FROM medias WHERE id=?", (mid,))
    return jsonify({"ok": True})


# ── Serve uploads ──────────────────────────────────────────────────────────────

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# ── Run ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    print("✅  Base de données prête.")
    print("🏭  App disponible sur http://127.0.0.1:5000")
    app.run(debug=True, use_reloader=False)