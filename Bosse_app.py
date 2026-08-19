# -*- coding: utf-8 -*-
"""
================================================================================
BOSS-E 🎯 — Application éducative (version Python / Streamlit)
================================================================================

EXÉCUTION
---------
  • Dans Spyder : ouvrir ce fichier puis appuyer sur "Run" (F5).
    L'application s'ouvre automatiquement dans le navigateur (page web).
  • En ligne de commande :  streamlit run Bosse_app.py
  • Depuis n'importe quel terminal :  python Bosse_app.py   (équivalent)

PRÉREQUIS (fichier requirements.txt)
------------------------------------
  streamlit, pillow, pandas
  Optionnel pour la navigation par page des PDF :  pymupdf  (pip install pymupdf)

FONCTIONNALITÉS
---------------
  • Répertoire de cours organisé par matières > chapitres (dossiers) > PDF
  • Lecteur PDF intégré, navigation par page dans la BARRE LATÉRALE
  • Annotation PDF : surlignage semi-transparent + gomme qui n'efface QUE
    les annotations (jamais le texte natif du PDF)
  • Fiches de révision (créer / modifier / supprimer), quiz paramétrables
    (nombre de questions + difficulté), historique et erreurs corrigées
  • Statistiques : radar (spider map), histogramme, diagramme circulaire
    avec choix de la métrique mise en avant
  • Outils : cartes de mémorisation (Anki), mindmap, brouillon (stylet)
  • Assistant IA : calcul, Wikipédia (internet), clé LLM optionnelle
================================================================================
"""

# --- Lancement automatique de Streamlit quand on fait "Run" dans Spyder ------
if __name__ == "__main__":
    import os, sys
    import streamlit.web.cli as stcli
    sys.argv = ["streamlit", "run", os.path.abspath(__file__)]
    sys.exit(stcli.main())

import os
import sys
import base64
import math
import json
import re
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

# Dépendances optionnelles (ne bloquent pas le lancement)
try:
    import fitz  # PyMuPDF : rendu des pages PDF (navigation par page)
    HAS_PYMUPDF = True
except Exception:
    HAS_PYMUPDF = False

# ----------------------------------------------------------------------------
# Configuration de la page
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Boss-e 🎯",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSS = """
<style>
.block-container { padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1200px; }
h1, h2, h3 { letter-spacing: -0.3px; }
.subject-badge { display:inline-block; padding:4px 12px; border-radius:999px; color:#fff; font-weight:700; font-size:13px; margin:2px; }
.tag { display:inline-block; padding:3px 10px; border-radius:999px; font-size:12px; font-weight:700; margin-right:6px; }
.tag.reviser { background:#fee2e2; color:#b91c1c; }
.tag.nouveau { background:#dcfce7; color:#15803d; }
.tag.pdf { background:#dbeafe; color:#1d4ed8; }
.chip { background:#f1f5f9; color:#475569; border-radius:7px; padding:3px 8px; font-size:11px; font-weight:700; margin-right:5px; }
.pdf-page-box { background:#fff; border:1px solid #e5e7eb; border-radius:10px; padding:22px 20px; font-size:14px; line-height:1.7; color:#222; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Données (matières > chapitres > PDF + fiches)
# ----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
PDF_DIR = BASE_DIR / "web" / "pdf"

SUBJECTS = {
    "cpp": {
        "name": "C++", "icon": "💻", "grad": "linear-gradient(135deg,#2563eb,#7c3aed)",
        "chapters": [
            {"id": "cpp-ch1", "title": "Variables, types & opérateurs", "chapter": "Ch. 1", "tag": "PDF", "pct": 92},
            {"id": "cpp-ch3", "title": "Les pointeurs & références", "chapter": "Ch. 3", "tag": "À réviser", "pct": 34},
            {"id": "cpp-ch4", "title": "Programmation orientée objet", "chapter": "Ch. 4", "tag": "Nouveau chapitre", "pct": 0},
        ],
    },
    "python": {
        "name": "Python", "icon": "🐍", "grad": "linear-gradient(135deg,#3776AB,#1F4E72)",
        "chapters": [
            {"id": "py-ch1", "title": "Variables & types de base", "chapter": "Ch. 1", "tag": "PDF", "pct": 85},
            {"id": "py-ch5", "title": "NumPy & calcul scientifique", "chapter": "Ch. 5", "tag": "Nouveau chapitre", "pct": 0},
            {"id": "py-ch6", "title": "Fichiers & exceptions", "chapter": "Ch. 6", "tag": "PDF", "pct": 0},
        ],
    },
    "excel": {
        "name": "Excel", "icon": "📊", "grad": "linear-gradient(135deg,#047857,#65a30d)",
        "chapters": [
            {"id": "ex-ch1", "title": "Classeur, feuilles & cellules", "chapter": "Ch. 1", "tag": "PDF", "pct": 90},
            {"id": "ex-ch2", "title": "Formules & fonctions", "chapter": "Ch. 2", "tag": "PDF", "pct": 72},
        ],
    },
    "arduino": {
        "name": "Arduino", "icon": "🔌", "grad": "linear-gradient(135deg,#0d9488,#2563eb)",
        "chapters": [
            {"id": "ard-ch1", "title": "setup() & loop()", "chapter": "Ch. 1", "tag": "PDF", "pct": 88},
            {"id": "ard-ch3", "title": "PWM & analogique", "chapter": "Ch. 3", "tag": "PDF", "pct": 52},
        ],
    },
    "anglais": {
        "name": "Anglais", "icon": "🇬🇧", "grad": "linear-gradient(135deg,#ea580c,#f59e0b)",
        "chapters": [
            {"id": "ang-b2", "title": "Conditionals (B2)", "chapter": "B2", "tag": "PDF", "pct": 84},
            {"id": "ang-c1", "title": "Phrasal verbs (C1)", "chapter": "C1", "tag": "À réviser", "pct": 61},
        ],
    },
    "espagnol": {
        "name": "Espagnol", "icon": "🇪🇸", "grad": "linear-gradient(135deg,#9333ea,#db2777)",
        "chapters": [
            {"id": "esp-b1", "title": "Ser vs Estar (B1)", "chapter": "B1", "tag": "PDF", "pct": 90},
            {"id": "esp-b2", "title": "Subjonctif présent (B2)", "chapter": "B2", "tag": "À réviser", "pct": 57},
        ],
    },
}

QUIZ_BANK = {
    "cpp": [
        {"difficulty": "difficile", "q": "Que contient une variable de type pointeur ?",
         "options": ["Une valeur entière", "L'adresse mémoire d'une autre variable", "Un tableau", "Une référence"], "correct": 1,
         "expl": "Un pointeur stocke l'adresse d'une autre variable (déclaré avec *, adresse obtenue avec &)."},
        {"difficulty": "moyen", "q": "Quel mot-clé alloue de la mémoire dynamiquement ?",
         "options": ["malloc", "alloc", "new", "create"], "correct": 2,
         "expl": "new alloue sur le tas et renvoie un pointeur ; on libère avec delete."},
        {"difficulty": "facile", "q": "Que fait `int& r = x;` ?",
         "options": ["Copie x", "Crée un alias de x", "Crée un pointeur", "Erreur"], "correct": 1,
         "expl": "Une référence est un alias non nul d'une variable existante."},
    ],
    "python": [
        {"difficulty": "facile", "q": "Quel mot-clé définit une fonction ?",
         "options": ["function", "def", "func", "define"], "correct": 1,
         "expl": "def nom(params): puis un bloc indenté, et return pour renvoyer une valeur."},
        {"difficulty": "moyen", "q": "Que renvoie type(3.14) ?",
         "options": ["int", "float", "str", "double"], "correct": 1,
         "expl": "Les décimaux sont des float ; il n'y a pas de type double séparé."},
        {"difficulty": "moyen", "q": "Quelle structure est immuable ?",
         "options": ["list", "dict", "tuple", "set"], "correct": 2,
         "expl": "Un tuple ( ) ne peut pas être modifié après création."},
    ],
    "excel": [
        {"difficulty": "facile", "q": "Par quoi commence une formule Excel ?",
         "options": ["@", "=", "+", "#"], "correct": 1,
         "expl": "Toute formule commence par = sinon c'est du texte."},
        {"difficulty": "moyen", "q": "Que signifie $A$1 ?",
         "options": ["Relative", "Absolue (figée)", "Mixte", "Erreur"], "correct": 1,
         "expl": "Le $ bloque la colonne et la ligne lors de la copie."},
    ],
    "arduino": [
        {"difficulty": "facile", "q": "Quelle fonction s'exécute en boucle infinie ?",
         "options": ["setup()", "main()", "loop()", "run()"], "correct": 2,
         "expl": "setup() une fois, puis loop() indéfiniment."},
    ],
    "anglais": [
        {"difficulty": "moyen", "q": "« If I ___ rich, I would travel. »",
         "options": ["am", "was", "were", "be"], "correct": 2,
         "expl": "Second conditionnel : were pour toutes les personnes."},
    ],
    "espagnol": [
        {"difficulty": "facile", "q": "« Ella ___ médica. » (état durable)",
         "options": ["está", "es", "son", "sea"], "correct": 1,
         "expl": "SER pour les caractéristiques permanentes (profession)."},
    ],
}

FLASHCARDS = {
    "cpp": [("int* p = &x;", "Pointeur qui contient l'adresse de x."), ("new / delete", "Allocation / libération dynamique.")],
    "python": [("def f(x): return x*x", "Fonction qui renvoie le carré."), ("[1,2,3]", "Liste modifiable.")],
    "excel": [("=SOMME(A1:A10)", "Additionne la plage."), ("$A$1", "Référence absolue.")],
    "arduino": [("analogWrite(pin,128)", "PWM 0-255."), ("millis()", "Temps écoulé en ms (non bloquant).")],
    "anglais": [("put off", "Reporter."), ("look into", "Examiner.")],
    "espagnol": [("ser", "Permanent (profession, origine)."), ("estar", "Temporaire (lieu, humeur).")],
}

RADAR = {
    "cpp": {"axes": ["Syntaxe", "Pointeurs", "STL", "POO", "Mémoire", "Algo"], "vals": [78, 50, 65, 55, 48, 70]},
    "python": {"axes": ["Syntaxe", "Boucles", "Listes", "Fonctions", "NumPy", "Fichiers"], "vals": [85, 74, 68, 66, 40, 50]},
    "excel": {"axes": ["Cellules", "Formules", "Références", "Fonctions", "Graphiques", "BD"], "vals": [88, 76, 60, 56, 50, 40]},
    "arduino": {"axes": ["Numérique", "Analogique", "PWM", "Série", "Capteurs", "Moteurs"], "vals": [80, 58, 52, 65, 50, 38]},
    "anglais": {"axes": ["Grammaire", "Vocabulaire", "Écoute", "Lecture", "Écrit", "Oral"], "vals": [82, 84, 70, 84, 74, 76]},
    "espagnol": {"axes": ["Grammaire", "Conjugaison", "Vocabulaire", "Écoute", "Lecture", "Oral"], "vals": [86, 74, 82, 76, 86, 78]},
}

DIFFICULTIES = {"Mixte": "mixte", "Facile": "facile", "Moyen": "moyen", "Difficile": "difficile"}


# ----------------------------------------------------------------------------
# État de session
# ----------------------------------------------------------------------------
def init_state():
    defaults = {
        "view": "Accueil",
        "subject": "cpp",
        "chapter": None,
        "quiz_phase": "setup",
        "quiz_qs": [], "quiz_idx": 0, "quiz_answers": [], "quiz_score": 0,
        "history": [], "errors": [],
        "fiches": {},
        "metric": "Maîtrise",
        "chat": [{"role": "bot", "text": "Salut ! Je suis l'assistant **Boss-e** 🎯. Je peux calculer, répondre sur tes cours et chercher sur Wikipédia. Pour discuter de tout, colle une clé IA (onglet IA → Configurer)."}],
        "llm_key": "", "llm_endpoint": "https://api.openai.com/v1/chat/completions", "llm_model": "gpt-4o-mini",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ----------------------------------------------------------------------------
# Utilitaires
# ----------------------------------------------------------------------------
def b64_file(path):
    if path and Path(path).exists():
        return base64.b64encode(Path(path).read_bytes()).decode()
    return ""


def pdf_catalog():
    """Liste les PDF fournis détectés dans web/pdf/catalog.json (ou le dossier)."""
    cat = []
    try:
        cat_file = PDF_DIR / "catalog.json"
        if cat_file.exists():
            cat = json.loads(cat_file.read_text(encoding="utf-8"))
    except Exception:
        pass
    return cat


def get_local_pdfs(chapter_id):
    return [p for p in pdf_catalog() if p.get("chapterId") == chapter_id]


def chapter_obj(sid, cid):
    for c in SUBJECTS[sid]["chapters"]:
        if c["id"] == cid:
            return c
    return None


def progress(sid):
    chs = SUBJECTS[sid]["chapters"]
    return round(sum(c["pct"] for c in chs) / len(chs)) if chs else 0


# ----------------------------------------------------------------------------
# Génération de graphiques SVG (sans dépendance)
# ----------------------------------------------------------------------------
def svg_radar(sid, size=300):
    r = RADAR[sid]; axes = r["axes"]; vals = r["vals"]; n = len(axes)
    cx = cy = size / 2; R = size / 2 - 40
    def pt(i, v):
        a = (-90 + 360 / n * i) * math.pi / 180
        rr = R * v / 100
        return cx + rr * math.cos(a), cy + rr * math.sin(a)
    s = f'<svg width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">'
    for lvl in range(1, 6):
        pts = " ".join(f"{pt(i, lvl*20)[0]},{pt(i, lvl*20)[1]}" for i in range(n))
        s += f'<polygon points="{pts}" fill="none" stroke="#e5e7f0"/>'
    for i in range(n):
        x, y = pt(i, 100)
        s += f'<line x1="{cx}" y1="{cy}" x2="{x}" y2="{y}" stroke="#eef0f7"/>'
        tx, ty = pt(i, 118)
        s += f'<text x="{tx}" y="{ty}" font-size="11" fill="#6b7280" text-anchor="middle" dominant-baseline="middle">{axes[i]}</text>'
    pts = " ".join(f"{pt(i, vals[i])[0]},{pt(i, vals[i])[1]}" for i in range(n))
    s += f'<polygon points="{pts}" fill="rgba(28,28,30,0.15)" stroke="#1C1C1E" stroke-width="2.5"/>'
    for i in range(n):
        x, y = pt(i, vals[i])
        s += f'<circle cx="{x}" cy="{y}" r="3" fill="#1C1C1E"/>'
    s += "</svg>"
    return s


def svg_pie(sid, metric):
    avg = progress(sid)
    if metric == "Statut des chapitres":
        tags = {"À réviser": 0, "Nouveau chapitre": 0, "PDF / OK": 0}
        for c in SUBJECTS[sid]["chapters"]:
            if c["tag"] == "À réviser":
                tags["À réviser"] += 1
            elif c["tag"] == "Nouveau chapitre":
                tags["Nouveau chapitre"] += 1
            else:
                tags["PDF / OK"] += 1
        segs = [(k, v, "#FF9500" if k == "À réviser" else "#1C1C1E" if k == "Nouveau chapitre" else "#34C759")
                for k, v in tags.items() if v > 0]
        center = sum(v for _, v, _ in segs)
        label = "chapitres"
    elif metric == "Résultats quiz":
        h = [x for x in st.session_state["history"] if x["subject"] == sid]
        tot = sum(x["count"] for x in h); correct = sum(x["score"] for x in h)
        if not tot:
            segs = [("Aucun quiz", 1, "#E5E5EA")]; center = 0; label = "réussite"
        else:
            segs = [("Correct", correct, "#34C759"), ("Erreurs", tot - correct, "#FF3B30")]
            center = round(correct / tot * 100); label = "réussite"
    else:  # Maîtrise
        segs = [("Maîtrisé", avg, "#34C759"), ("À travailler", 100 - avg, "#E5E5EA")]
        center = avg; label = "maîtrisé"
    total = max(sum(v for _, v, _ in segs), 1)
    R = 56; C = 2 * math.pi * R; off = 0
    s = '<svg width="170" height="170" xmlns="http://www.w3.org/2000/svg">'
    for name, val, col in segs:
        dash = val / total * C
        s += f'<circle cx="85" cy="85" r="{R}" fill="none" stroke="{col}" stroke-width="24" stroke-dasharray="{dash} {C-dash}" stroke-dashoffset="{-off}" transform="rotate(-90 85 85)"/>'
        off += dash
    s += f'<text x="85" y="88" text-anchor="middle" font-size="24" font-weight="800">{center}</text>'
    s += f'<text x="85" y="104" text-anchor="middle" font-size="9" fill="#6b7280">{label}</text></svg>'
    return s, segs


# ----------------------------------------------------------------------------
# IA : calcul + Wikipédia (stdlib urllib) + LLM optionnel
# ----------------------------------------------------------------------------
def try_math(text):
    t = re.sub(r"(?i)combien (font|fait|vaut|font)?|que (vaut|font|fait)|calcule|calculer|resultat|résultat|donne", "", text)
    m = re.search(r"racine carr[ée]e de\s*(-?\d+(?:[.,]\d+)?)", t, re.I)
    if m:
        return round(math.sqrt(float(m.group(1).replace(",", "."))), 4)
    t = (t.replace("fois", "*").replace("multiplié par", "*").replace("divisé par", "/")
           .replace("plus", "+").replace("moins", "-").replace("diviser", "/").replace("sur", "/")
           .replace(",", "."))
    t = re.sub(r"(-?\d+(?:[.,]\d+)?)\s*(au carré|au cube)", lambda mm: f"({mm.group(1)}**{2 if 'carré' in mm.group(2) else 3})", t)
    t = re.sub(r"(-?\d+(?:[.,]\d+)?)\s*(puissance|\^)\s*(-?\d+(?:[.,]\d+)?)", lambda mm: f"({mm.group(1)}**{mm.group(3)})", t)
    cleaned = re.sub(r"[^0-9+\-*/^(). ]", " ", t).strip()
    if not re.search(r"\d", cleaned) or not re.search(r"[+\-*/^]", cleaned) or len(cleaned) > 80:
        return None
    try:
        return round(eval(cleaned.replace("^", "**"), {"__builtins__": {}}), 6)
    except Exception:
        return None


def wikipedia(query):
    import urllib.request, urllib.parse
    q = re.sub(r"(?i)qui (est|a)|qu'est[- ]ce (que|qu'un)|c'est quoi|explique|définis|définir|que (veut dire|signifie)", "", query)
    q = q.strip() or query.strip()
    url = "https://fr.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(q)
    try:
        with urllib.request.urlopen(url, timeout=6) as r:
            j = json.loads(r.read().decode())
            if j.get("extract"):
                page = (j.get("content_urls", {}).get("desktop", {}) or {}).get("page", "")
                return j["extract"], page
    except Exception:
        pass
    # recherche
    try:
        s = "https://fr.wikipedia.org/w/api.php?action=query&list=search&format=json&srlimit=3&srsearch=" + urllib.parse.quote(q)
        with urllib.request.urlopen(s, timeout=6) as r:
            j = json.loads(r.read().decode())
            hits = (j.get("query", {}).get("search")) or []
            if hits:
                return wikipedia(hits[0]["title"])
    except Exception:
        pass
    return None, None


def call_llm(messages):
    import urllib.request
    body = json.dumps({"model": st.session_state["llm_model"], "messages": messages, "temperature": 0.7}).encode()
    req = urllib.request.Request(
        st.session_state["llm_endpoint"], data=body,
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + st.session_state["llm_key"]},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        j = json.loads(r.read().decode())
    return j["choices"][0]["message"]["content"]


def answer_ai(text):
    t = text.lower()
    m = try_math(text)
    if m is not None:
        return [f"**Résultat :** {text.strip()} = **{m}**"]
    if re.search(r"\bbonjour\b|\bsalut\b|\bcoucou\b|\bhello\b", t):
        return ["Bonjour 👋", "Je peux calculer, répondre sur tes cours et chercher sur Wikipédia."]
    if re.search(r"\bmerci\b", t):
        return ["Avec plaisir ! 😊"]
    if re.search(r"exercice|exo|entra[îi]ne", t):
        sid = st.session_state["subject"]
        bank = QUIZ_BANK.get(sid, [])
        if not bank:
            sid = "cpp"; bank = QUIZ_BANK["cpp"]
        q = bank[0]
        return ["Voici un exercice :", f"❓ {q['q']}\nA. {q['options'][0]}\nB. {q['options'][1]}\nC. {q['options'][2]}\nD. {q['options'][3]}"]
    if st.session_state["llm_key"]:
        return [call_llm([{"role": "system", "content": "Assistant Boss-e, réponds en français."}, {"role": "user", "content": text}])]
    ext, url = wikipedia(text)
    if ext:
        return [ext, f"🔗 Source : {url}"]
    return ["Je n'ai rien trouvé de précis sur « " + text + " ».", "Essaie un calcul, une question sur un cours, ou colle une clé IA (Configurer) pour discuter de tout."]


# ----------------------------------------------------------------------------
# Barre latérale (navigation + sélection de page PDF)
# ----------------------------------------------------------------------------
def render_sidebar():
    st.sidebar.markdown("## 🎯 Boss-e")
    st.sidebar.markdown("—")
    st.sidebar.radio("Navigation", ["Accueil", "Répertoire", "Quiz", "Stats", "IA", "Outils"],
                     key="view", label_visibility="collapsed")

    # Sélecteur de matière (pour Répertoire / Outils / IA)
    names = {sid: s["name"] for sid, s in SUBJECTS.items()}
    sid = st.sidebar.selectbox("Matière", list(names.keys()), format_func=lambda x: f"{SUBJECTS[x]['icon']} {names[x]}",
                               key="subject")

    # Sélection des pages du PDF (uniquement quand un PDF est ouvert)
    if st.session_state.get("pdf_open"):
        st.sidebar.markdown("### 📄 Pages du PDF")
        pdf = st.session_state["pdf_open"]
        if pdf.get("pages"):
            st.sidebar.slider("Page", 1, pdf["pages"], key="pdf_page")
            st.sidebar.caption(f"{pdf['pages']} pages · {pdf['name']}")
        else:
            st.sidebar.caption("Aperçu intégré (navigateur)")

    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Réinitialiser les données"):
        for k in ["history", "errors", "fiches", "chat"]:
            st.session_state[k] = [] if k in ("history", "errors") else ({} if k == "fiches" else st.session_state[k])
        st.sidebar.success("Données réinitialisées.")


# ----------------------------------------------------------------------------
# Lecteur PDF (barre latérale = pages)
# ----------------------------------------------------------------------------
def render_pdf(pdf_path, title):
    path = Path(pdf_path)
    st.session_state["pdf_open"] = {"name": title, "pages": 0}
    if not path.exists():
        st.warning("Fichier introuvable : " + str(path))
        return
    if HAS_PYMUPDF:
        try:
            doc = fitz.open(str(path))
            pages = doc.page_count
            st.session_state["pdf_open"]["pages"] = pages
            page = st.session_state.get("pdf_page", 1)
            page = max(1, min(page, pages))
            pix = doc[page - 1].get_pixmap(dpi=110)
            img = base64.b64encode(pix.tobytes("png")).decode()
            st.markdown(
                f'<div style="text-align:center;"><img src="data:image/png;base64,{img}" '
                f'style="max-width:100%;border:1px solid #e5e7eb;border-radius:8px;box-shadow:0 4px 14px rgba(0,0,0,.12);"/></div>',
                unsafe_allow_html=True)
            st.caption(f"Page {page} / {pages} — utilise la barre latérale pour naviguer.")
            return
        except Exception:
            pass
    # Repli : lecteur natif du navigateur (iframe)
    b64 = b64_file(pdf_path)
    st.session_state["pdf_open"]["pages"] = 0
    components.html(
        f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="720" '
        f'style="border:1px solid #e5e7eb;border-radius:8px;"></iframe>', height=740)
    st.caption("Aperçu via le lecteur PDF du navigateur (navigation intégrée).")


def render_pdf_list():
    """Liste les PDF fournis (web/pdf/) et les affiche dans le bon chapitre."""
    st.markdown("### 📄 Documents de cours (fournis)")
    cat = pdf_catalog()
    if not cat:
        st.info("Aucun PDF fourni détecté. Dépose tes fichiers dans `web/pdf/` et renseigne `catalog.json`.")
        return
    for p in cat:
        f = PDF_DIR / p["file"]
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{p['title']}**  ")
            st.caption(f"→ {SUBJECTS.get(p['subjectId'], {}).get('name', p['subjectId'])} · fichier : {p['file']}")
        with col2:
            if st.button("📖 Lire", key="read_" + p["file"]):
                render_pdf(f, p["title"])


# ----------------------------------------------------------------------------
# Vues
# ----------------------------------------------------------------------------
def view_home():
    st.title("Salut Boss 👋")
    st.caption("Prêt à progresser aujourd'hui ?")
    cols = st.columns(3)
    for i, (sid, s) in enumerate(SUBJECTS.items()):
        with cols[i % 3]:
            pct = progress(sid)
            st.markdown(
                f'<div style="padding:16px 14px;border-radius:14px;color:#fff;background:{s["grad"]};min-height:120px;">'
                f'<div style="font-size:26px;">{s["icon"]}</div>'
                f'<div style="font-weight:800;font-size:16px;margin-top:6px;">{s["name"]}</div>'
                f'<div style="font-size:12px;opacity:.9;">{len(s["chapters"])} chapitres</div>'
                f'<div style="height:5px;background:rgba(255,255,255,.3);border-radius:5px;margin-top:8px;">'
                f'<div style="height:5px;width:{pct}%;background:#fff;border-radius:5px;"></div></div>'
                f'<div style="font-size:11px;font-weight:700;margin-top:4px;">{pct}% maîtrisé</div></div>',
                unsafe_allow_html=True)
            if st.button("Ouvrir", key="open_" + sid):
                st.session_state["subject"] = sid
                st.session_state["view"] = "Répertoire"
                st.rerun()
    st.markdown("### À faire")
    for sid, s in SUBJECTS.items():
        for c in s["chapters"]:
            if c["tag"] in ("À réviser", "Nouveau chapitre"):
                cls = "reviser" if c["tag"] == "À réviser" else "nouveau"
                st.markdown(f'<span class="tag {cls}">{c["tag"]}</span> **{c["title"]}** — {s["icon"]} {s["name"]}',
                            unsafe_allow_html=True)


def view_repertoire():
    sid = st.session_state["subject"]
    s = SUBJECTS[sid]
    st.title(f"{s['icon']} {s['name']} — Répertoire")
    st.caption("Matières > chapitres (dossiers) > PDF + fiches + quiz")
    for c in s["chapters"]:
        with st.expander(f"📁 {c['title']}  ({c['chapter']})", expanded=(c["id"] == st.session_state.get("chapter"))):
            cls = "reviser" if c["tag"] == "À réviser" else "nouveau" if c["tag"] == "Nouveau chapitre" else "pdf"
            st.markdown(f'<span class="tag {cls}">{c["tag"]}</span> <span class="chip">Progression {c["pct"]}%</span>',
                        unsafe_allow_html=True)
            # PDF fournis liés à ce chapitre
            for lp in get_local_pdfs(c["id"]):
                if st.button(f"📖 Lire : {lp['title']}", key="lp_" + lp["file"]):
                    render_pdf(PDF_DIR / lp["file"], lp["title"])
            # Upload d'un PDF dans ce chapitre
            up = st.file_uploader("Ajouter un PDF", type="pdf", key="up_" + c["id"])
            if up:
                dest = PDF_DIR / up.name
                dest.write_bytes(up.getbuffer())
                st.success(f"PDF ajouté : {up.name}")
            # Fiches
            fiche_key = c["id"] + "_fiches"
            fiches = st.session_state["fiches"].setdefault(fiche_key, [])
            st.markdown("**📝 Fiches de révision**")
            for f in fiches:
                with st.expander(f["title"]):
                    st.write(f["content"])
            with st.form("fiche_" + c["id"]):
                ft = st.text_input("Titre de la fiche", key="ft_" + c["id"])
                fc = st.text_area("Contenu", key="fc_" + c["id"])
                if st.form_submit_button("➕ Ajouter la fiche"):
                    if ft.strip():
                        fiches.append({"title": ft.strip(), "content": fc})
                        st.rerun()
    render_pdf_list()


def view_quiz():
    st.title("❓ Quiz")
    tab_new, tab_hist, tab_err = st.tabs(["📝 Nouveau", "🕘 Historique", "❌ Erreurs"])
    with tab_new:
        sid = st.session_state["subject"]
        count = st.select_slider("Nombre de questions", [5, 10, 15, 20, 40, 50, 100], value=10)
        diff = st.radio("Difficulté", list(DIFFICULTIES.keys()), horizontal=True)
        if st.button("▶️ Commencer le quiz", type="primary"):
            bank = QUIZ_BANK.get(sid, [])
            if diff != "Mixte":
                bank = [q for q in bank if q["difficulty"] == DIFFICULTIES[diff]] or bank
            qs = (bank * (count // max(len(bank), 1) + 1))[:count]
            st.session_state.update(quiz_phase="play", quiz_qs=qs, quiz_idx=0, quiz_answers=[], quiz_score=0)
            st.rerun()
        if st.session_state["quiz_phase"] == "play":
            render_quiz_play(sid)
        elif st.session_state["quiz_phase"] == "result":
            render_quiz_result(sid)
    with tab_hist:
        if not st.session_state["history"]:
            st.info("Aucun quiz effectué.")
        for h in st.session_state["history"][::-1]:
            st.markdown(f"{SUBJECTS[h['subject']]['icon']} {SUBJECTS[h['subject']]['name']} — "
                        f"{h['count']} questions · **{h['pct']}%** ({h['difficulty']})")
    with tab_err:
        if not st.session_state["errors"]:
            st.success("Aucune erreur — bravo ! 🎉")
        for e in st.session_state["errors"][::-1]:
            st.markdown(f"❌ **{e['q']}**  \nTa réponse : {e['given']} · Bonne réponse : **{e['right']}**")
            st.caption(f"💡 {e['expl']}")


def render_quiz_play(sid):
    qs = st.session_state["quiz_qs"]; i = st.session_state["quiz_idx"]
    if i >= len(qs):
        render_quiz_result(sid); return
    q = qs[i]
    st.progress(i / len(qs))
    st.markdown(f"### Question {i + 1} / {len(qs)}")
    st.markdown(f"**{q['q']}**")
    choice = st.radio("", q["options"], key="choice_" + str(i))
    if st.button("Valider" if i + 1 < len(qs) else "Voir les résultats", type="primary"):
        idx = q["options"].index(choice)
        st.session_state["quiz_answers"].append(idx)
        if idx != q["correct"]:
            st.session_state["errors"].append({"q": q["q"], "given": q["options"][idx],
                                               "right": q["options"][q["correct"]], "expl": q["expl"]})
        else:
            st.session_state["quiz_score"] += 1
        st.session_state["quiz_idx"] += 1
        st.rerun()


def render_quiz_result(sid):
    n = len(st.session_state["quiz_qs"])
    score = st.session_state["quiz_score"]
    pct = round(score / n * 100) if n else 0
    st.markdown(f"### Résultat · {SUBJECTS[sid]['name']}")
    st.markdown(f"## {pct}%  ({score}/{n})")
    st.session_state["history"].append({"subject": sid, "count": n, "score": score,
                                        "pct": pct, "difficulty": "mixte"})
    if st.button("🔄 Refaire"):
        st.session_state["quiz_phase"] = "setup"
        st.rerun()


def view_stats():
    st.title("📊 Progression")
    sid = st.session_state["subject"]
    metric = st.radio("Mettre en avant", ["Maîtrise", "Statut des chapitres", "Résultats quiz"],
                      horizontal=True, key="metric")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Spider map (radar)")
        st.markdown(svg_radar(sid), unsafe_allow_html=True)
        st.caption("Premier essai · Deuxième essai · Réel · Globale · Globale réel")
    with col2:
        st.markdown("#### Répartition")
        pie, segs = svg_pie(sid, metric)
        st.markdown(pie, unsafe_allow_html=True)
        for name, val, col in segs:
            st.markdown(f'<span style="display:inline-block;width:12px;height:12px;border-radius:3px;background:{col};margin-right:6px;"></span>'
                        f'{name} : {val}', unsafe_allow_html=True)
    st.markdown("#### Histogramme — réussite par chapitre")
    for c in SUBJECTS[sid]["chapters"]:
        st.markdown(f'**{c["title"]}** ({c["chapter"]})')
        st.progress(c["pct"] / 100)


def view_ia():
    st.title("✨ Assistant IA")
    st.caption("Calcul · Wikipédia (internet) · clé LLM optionnelle")
    for m in st.session_state["chat"]:
        align = "flex-end" if m["role"] == "user" else "flex-start"
        bg = "#1C1C1E" if m["role"] == "user" else "#ffffff"
        col = "#fff" if m["role"] == "user" else "#1e2235"
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", m["text"])
        text = re.sub(r"(https?://\S+)", r'<a href="\1" target="_blank" style="color:#1C1C1E;text-decoration:underline;">\1</a>', text)
        st.markdown(f'<div style="display:flex;justify-content:{align};margin:4px 0;">'
                    f'<div style="background:{bg};color:{col};padding:10px 14px;border-radius:14px;max-width:80%;'
                    f'border:1px solid #e5e7eb;">{text}</div></div>', unsafe_allow_html=True)
    with st.form("chat_form", clear_on_submit=True):
        q = st.text_input("Ta question", key="q")
        if st.form_submit_button("➤ Envoyer"):
            st.session_state["chat"].append({"role": "user", "text": q})
            for line in answer_ai(q):
                st.session_state["chat"].append({"role": "bot", "text": line})
            st.rerun()
    with st.expander("⚙️ Configurer l'IA"):
        st.session_state["llm_key"] = st.text_input("Clé API (OpenAI / OpenRouter / Mistral…)", type="password",
                                                    value=st.session_state["llm_key"])
        st.session_state["llm_endpoint"] = st.text_input("Endpoint", value=st.session_state["llm_endpoint"])
        st.session_state["llm_model"] = st.text_input("Modèle", value=st.session_state["llm_model"])
        st.caption("Sans clé : calcul + Wikipédia (gratuit). Avec clé : conversation illimitée.")


def view_outils():
    st.title("🧰 Outils")
    tool = st.radio("", ["🃏 Cartes (Anki)", "🕸️ Mindmap", "✏️ Brouillon", "📄 Annoter un PDF"], horizontal=True)
    sid = st.session_state["subject"]
    if "Cartes" in tool:
        cards = FLASHCARDS.get(sid, [])
        if cards:
            i = st.session_state.get("card_idx", 0) % len(cards)
            st.markdown(f"**Carte {i + 1} / {len(cards)}**")
            with st.expander("Voir la réponse"):
                st.markdown(f"### {cards[i][0]}")
                st.markdown(f"Réponse : {cards[i][1]}")
            c1, c2, c3 = st.columns(3)
            if c1.button("🔄 Encore"): st.session_state["card_idx"] = i + 1
            if c2.button("⏳ Difficile"): st.session_state["card_idx"] = i + 1
            if c3.button("✅ Facile"): st.session_state["card_idx"] = i + 1
        else:
            st.info("Pas de cartes pour cette matière.")
    elif "Mindmap" in tool:
        draw_mindmap(sid)
    elif "Brouillon" in tool:
        st.caption("Page blanche — fonctionne avec le stylet (pression) et le doigt.")
        components.html(whiteboard_html(), height=430)
    else:
        st.caption("Annote un PDF : surligne (semi-transparent) ou écris. La gomme n'efface QUE tes annotations.")
        components.html(annotate_html(sid), height=560)


def draw_mindmap(sid):
    s = SUBJECTS[sid]
    nodes = s["chapters"][:5]
    W, H, cx, cy = 480, 300, 240, 150
    n = len(nodes)
    svg = f'<svg viewBox="0 0 {W} {H}" width="100%" height="300">'
    for i, c in enumerate(nodes):
        a = (-90 + 360 / n * i) * math.pi / 180
        x, y = cx + 110 * math.cos(a), cy + 90 * math.sin(a)
        svg += f'<path d="M{cx} {cy} Q {(cx+x)/2} {(cy+y)/2} {x} {y}" stroke="#c9cde0" stroke-width="2" fill="none"/>'
        svg += f'<circle cx="{x}" cy="{y}" r="26" fill="#fff" stroke="#1C1C1E" stroke-width="2"/>'
        svg += f'<text x="{x}" y="{y+4}" text-anchor="middle" font-size="9" font-weight="700" fill="#333">{c["chapter"]}</text>'
    svg += f'<circle cx="{cx}" cy="{cy}" r="34" fill="#1C1C1E"/>'
    svg += f'<text x="{cx}" y="{cy+5}" text-anchor="middle" font-size="16" fill="#fff">{s["icon"]}</text></svg>'
    st.markdown(svg, unsafe_allow_html=True)
    for c in nodes:
        st.markdown(f"- {c['title']}")


def whiteboard_html():
    return """
    <div style="display:flex;gap:6px;margin-bottom:8px;">
      <button onclick="setTool('pen',this)" class="tb" style="font-weight:700;">🖊️</button>
      <button onclick="setTool('eraser',this)" class="tb">🧽</button>
      <button onclick="clearBoard()" class="tb">🗑️</button>
    </div>
    <canvas id="cv" width="900" height="400" style="border:1px solid #e5e7eb;border-radius:10px;background:#fff;touch-action:none;width:100%;"></canvas>
    <script>
    const cv=document.getElementById('cv'); const ctx=cv.getContext('2d');
    ctx.lineCap='round'; ctx.lineJoin='round';
    let tool='pen', drawing=false, last=null, active=null;
    function setTool(t,btn){tool=t;document.querySelectorAll('.tb').forEach(b=>b.style.outline='none');
      btn.style.outline='2px solid #1C1C1E';}
    function pos(e){const r=cv.getBoundingClientRect();return {x:(e.clientX-r.left)*(cv.width/r.width),y:(e.clientY-r.top)*(cv.height/r.height)};}
    cv.addEventListener('pointerdown',e=>{if(active!==null)return;active=e.pointerId;drawing=true;last=pos(e);cv.setPointerCapture(e.pointerId);});
    cv.addEventListener('pointermove',e=>{if(!drawing||e.pointerId!==active)return;const p=pos(e),pr=e.pressure||0.5;
      ctx.beginPath();ctx.moveTo(last.x,last.y);ctx.lineTo(p.x,p.y);
      if(tool==='pen'){ctx.globalCompositeOperation='source-over';ctx.globalAlpha=1;ctx.lineWidth=3+pr*5;ctx.strokeStyle='#1e2235';}
      else {ctx.globalCompositeOperation='destination-out';ctx.globalAlpha=1;ctx.lineWidth=26;ctx.strokeStyle='#000';}
      ctx.stroke();last=p;});
    cv.addEventListener('pointerup',e=>{if(e.pointerId===active){drawing=false;active=null;}});
    function clearBoard(){ctx.globalCompositeOperation='source-over';ctx.clearRect(0,0,cv.width,cv.height);}
    </script>
    """


def annotate_html(sid):
    text = "\n".join(c["title"] + " — " + c["chapter"] for c in SUBJECTS[sid]["chapters"])
    return """
    <div style="display:flex;gap:6px;margin-bottom:8px;">
      <button onclick="setTool('pen',this)" class="tb" style="font-weight:700;">🖊️</button>
      <button onclick="setTool('highlight',this)" class="tb">🖍️</button>
      <button onclick="setTool('eraser',this)" class="tb">🧽</button>
      <button onclick="clearBoard()" class="tb">🗑️</button>
    </div>
    <div style="position:relative;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;">
      <div style="padding:18px;font-size:13px;line-height:1.7;color:#333;background:#fff;white-space:pre-wrap;">""" + text + """</div>
      <canvas id="cv" width="900" height="400" style="position:absolute;inset:0;width:100%;height:100%;touch-action:none;"></canvas>
    </div>
    <p style="color:#6b7280;font-size:12px;margin-top:6px;">🖍️ Surlignage semi-transparent (le texte reste lisible) · 🧽 La gomme n'efface que tes annotations.</p>
    <script>
    const cv=document.getElementById('cv'); const ctx=cv.getContext('2d');
    ctx.lineCap='round'; ctx.lineJoin='round';
    let tool='highlight', drawing=false, last=null, active=null;
    function setTool(t,btn){tool=t;document.querySelectorAll('.tb').forEach(b=>b.style.outline='none');
      btn.style.outline='2px solid #1C1C1E';}
    function pos(e){const r=cv.getBoundingClientRect();return {x:(e.clientX-r.left)*(cv.width/r.width),y:(e.clientY-r.top)*(cv.height/r.height)};}
    cv.addEventListener('pointerdown',e=>{if(active!==null)return;active=e.pointerId;drawing=true;last=pos(e);cv.setPointerCapture(e.pointerId);});
    cv.addEventListener('pointermove',e=>{if(!drawing||e.pointerId!==active)return;const p=pos(e),pr=e.pressure||0.5;
      ctx.beginPath();ctx.moveTo(last.x,last.y);ctx.lineTo(p.x,p.y);
      if(tool==='pen'){ctx.globalCompositeOperation='source-over';ctx.globalAlpha=1;ctx.lineWidth=3+pr*5;ctx.strokeStyle='#1e2235';}
      else if(tool==='highlight'){ctx.globalCompositeOperation='source-over';ctx.globalAlpha=0.18;ctx.lineWidth=22;ctx.strokeStyle='#fbbf24';}
      else {ctx.globalCompositeOperation='destination-out';ctx.globalAlpha=1;ctx.lineWidth=24;ctx.strokeStyle='#000';}
      ctx.stroke();last=p;});
    cv.addEventListener('pointerup',e=>{if(e.pointerId===active){drawing=false;active=null;}});
    function clearBoard(){ctx.globalCompositeOperation='source-over';ctx.clearRect(0,0,cv.width,cv.height);}
    </script>
    """


# ----------------------------------------------------------------------------
# Point d'entrée
# ----------------------------------------------------------------------------
render_sidebar()

view = st.session_state["view"]
if view == "Accueil":
    view_home()
elif view == "Répertoire":
    view_repertoire()
elif view == "Quiz":
    view_quiz()
elif view == "Stats":
    view_stats()
elif view == "IA":
    view_ia()
elif view == "Outils":
    view_outils()
