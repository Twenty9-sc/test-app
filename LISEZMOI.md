# 🎯 BOSS-E — Package complet pour reprise par une IA

Ce dossier contient **tout le code** et **tout l'historique des demandes** du projet
Boss-e, prêt à être confié à une autre IA.

---

## 📁 Contenu

| Fichier | Rôle |
|---|---|
| `HISTORIQUE-DEMANDES.md` | **Toutes les demandes** faites depuis le début (cahier des charges cumulé). À lire en premier. |
| `LISEZMOI.md` | Ce fichier. |
| `web/` | **App web mobile-first** (la version principale). |
| `web/index.html` | Structure HTML (5 vues + lecteur PDF). |
| `web/css/styles.css` | Styles (thème iOS-Clean charcoal/vert). |
| `web/js/app.js` | **Toute la logique** (~1500 lignes). |
| `web/js/data.js` | Données : matières, chapitres, questions, flashcards. |
| `web/js/vendor/` | **pdf.js** local (rendu PDF) — indispensable, ne pas supprimer. |
| `web/pdf/catalog.json` | Mapping des PDF « fournis » (dossiers du répertoire). |
| `Bosse_app.py` | Version **Python / Streamlit** (lancement depuis Spyder). |
| `requirements.txt` | Dépendances Python. |

---

## 🚀 Lancer l'app web (le plus simple)

Aucune dépendance à installer (pur HTML/CSS/JS + pdf.js local).

### Option A — serveur local Python
```bash
cd web
python3 -m http.server 8000
# puis ouvrir http://localhost:8000
```

### Option B — ouvrir directement
Double-cliquer sur `web/index.html` (fonctionne, sauf stockage IndexedDB
limité sur certains navigateurs en mode `file://`).

### Option C — GitHub Pages (déploiement permanent)
Pousser le contenu de `web/` sur une branche `gh-pages`, activer Pages.

---

## 🐍 Lancer la version Python (Streamlit / Spyder)

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m streamlit run Bosse_app.py   # ou "Run" (F5) dans Spyder
```

> `Bosse_app.py` contient un launcher : exécuter `python Bosse_app.py`
> lance automatiquement Streamlit.

---

## ⚙️ Fonctionnement interne (résumé pour l'IA qui reprend)

### Stockage
- `localStorage` — clé `bosse_data` (fiches, quiz, fichiers-métadonnées, historique,
  cartes générées, mindmaps, config IA, corbeille, chapitres supprimés).
- `IndexedDB` — base `bosse_files` (blobs des PDF ajoutés).

### Lecteur PDF (`js/app.js`)
- `pdfjsLib.getDocument({ data: ArrayBuffer })` → rendu canvas page par page.
- Sidebar de navigation (`renderPdfSidebar`), boutons ←/→.
- Ouverture directe **dans la page** (jamais d'iframe ni de nouvel onglet).

### Génération automatique
- À l'ajout d'un PDF : `extractTextFromBlob()` (via `getTextContent()`),
  puis `generateFromText()` (heuristique) :
  - flashcards : détection « X **est/signifie/désigne** … » ;
  - quiz QCM : « Que signifie X ? » avec 3 leurres ;
  - mindmap : détection de titres/sections ;
  - résumé : phrases clés.
- `applyGeneratedContent()` sauvegarde le tout dans le bon dossier.

### IA
- Calcul local (`tryMath`), Wikipédia (fetch navigateur), clé LLM optionnelle
  (endpoint OpenAI-compatible, configurable via ⚙️ dans l'onglet IA).

### Points d'attention connus
- Génération **heuristique** (pas de vraie IA) → améliorable en branchant un LLM.
- PDF **distants** parfois bloqués par CORS → proxy `api.allorigins.win` en secours.
- Le sandbox d'origine était **re-provisionné en continu** (URL préview instable).
