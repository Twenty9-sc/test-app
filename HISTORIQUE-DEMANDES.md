# 🎯 BOSS-E — Historique complet des demandes (cahier des charges cumulé)

> Ce document regroupe **toutes les demandes** faites au fil du projet, pour qu'une
> nouvelle IA puisse reprendre le travail avec le contexte complet.

---

## 1. Concept initial (message 1)

Application éducative/d'apprentissage nommée **« Boss-e 🎯 »** (logo : cible/bullseye).
Quiz, visualisation de données, outils de révision, intégration IA, cours par défaut.

**Contrainte fondatrice :** d'abord voir l'interface en **site web** (mobile-first) avant de
l'adapter en appli téléphone.

### Fonctionnalités demandées (transcription initiale)
1. **Évaluation & QCM**
   - Réponses affichées à la fin du quiz.
   - Système de références détaillé : page, titre, chapitre, texte, explication, accès direct au PDF source, liens externes.
   - « Exo complet », statistiques (résultat, % de réussite).
2. **Outils de révision**
   - Répertoire de cours. Module type Anki, Mindmap, Brouillon (page blanche), interaction PDF (surligner/écrire), bouton « AIDE ? ».
3. **Visualisation des données**
   - « Spider map » (radar) toutes matières, comparaison « notes réelles vs virtuelles ».
   - Légende radar : *Premier essai, Deuxième essai, Réel, Globale, Globale réel*.
   - Histogrammes + diagrammes circulaires. Code couleur : vert plein = « Yes » ; hachuré bleu = « Yes but blue » (→ **retiré ensuite**).
   - Animations/transitions, fond dynamique par matière.
4. **Organisation / UI**
   - Tags : « À réviser », « Nouveau chapitre », « PDF » + nombre de jours (« durée de 2 semaines »).
   - Gestion fichiers : Supprimer, Confirmation, Retrouver, Corbeille.
5. **IA Arena** : poser des questions faisant intervenir l'IA.
6. **Contenu natif** : C++, Commandes Arduino, Anglais (B2→C2), Espagnol (B1→C2). Web scraping / génération depuis internet avec vraies sources et vrais exercices.
7. « Crée une beta ».

---

## 2. Premier lot de corrections (message 2)

- L'IA **ne répond pas aux questions simples** (ex. « 1+1 ») → doit savoir calculer et parler de tout.
- Pouvoir **ajouter des PDF de cours** dans des chapitres/dossiers.
- L'app doit **créer/modifier/supprimer** des **fiches de révision** et des **quiz**.
- Pouvoir **lire le PDF après** l'avoir ajouté.
- **Boutons retour** partout pour revenir en arrière.
- **Liens + ouvertures de PDF** cassés → doivent marcher, **dans la même fenêtre**, avec possibilité de revenir.
- Donner un **lien** ouvrable dans d'autres fenêtres/appareils.
- « Exo complet » et « Brouillon » ne s'ouvraient pas → les faire marcher.
- Brouillon : **écrire au stylet** (comme sur Xiaomi), pression sensible.
- **Sous-sections** pour tout répertorier.
- **Quiz modulables** : nombre de questions (5-10-15-20-40-50-100) + niveau de difficulté.
- Quand on entre dans « Quiz » : **ne pas lancer directement**, choisir d'abord les réglages.
- **Historique des quiz** + **historique des erreurs** (erreurs corrigées et expliquées).
- Rendre le site **lisible, épuré, pas surchargé**.
- **Bouton Aide petit**.

---

## 3. Deuxième lot (message 3)

- **Liens et sources de l'IA cliquables** + retour facile.
- **Retirer « Yes (en bleu) »** des stats (c'était une blague) → à la place, **option pour choisir quoi mettre en avant**.
- **Recherche rapide** ne marchait pas → chercher **partout** (cours, chapitres, questions, fiches, quiz, fichiers, cartes).
- Pouvoir **supprimer les cours/fichiers par défaut**.
- **Ajouter Python et Excel**.
- Prendre de **vrais PDF** de cours sur internet (université de Paris, l'X/Polytechnique, Centrale) → **vrais PDF complets avec beaucoup de pages**.
- **Connecter le site à internet** et l'**IA aussi** → qu'elle aille chercher les réponses sur internet, qu'elle réponde à **tout** (« 1+1 », culture générale…), « reliée directement à Arena ».

---

## 4. Troisième lot (message 4)

- L'IA doit **cliquer les liens/sources** et pouvoir revenir.
- Stats : couleurs + **légende** correspondant aux textes à côté des graphiques.
- **PDF ajoutés qui ne s'ouvrent pas** → doivent être **lisibles directement dans la page**, sans ouvrir de nouveau lien/onglet.
- Génération automatique : quand on ajoute un PDF, créer automatiquement **mindmap, quiz, flashcards** en lisant le texte et en prenant les données utiles.
- Rendre le tout **professionnel et pas surchargé**.

---

## 5. Demande de transposition (message « 268399 » + image)

Suite de notes fournies (fichier image), formatées en retours de bugs :

1. **Corrections outil d'annotation PDF**
   - **Gomme** : effaçait le texte natif du PDF → elle ne doit effacer **que les annotations utilisateur**.
   - **Surligneur** : trop opaque → diminuer l'opacité pour que le texte reste lisible.
2. **Gestion cours / UI**
   - Intégrer les PDF fournis, bien organisés/rangés.
   - **Menu de sélection des pages** des PDF dans une **barre latérale (sidebar)**.
3. **Instructions techniques**
   - Transcrire le code en **Python**.
   - Script ouvert dans **Spyder**.
   - Au « Run » : l'app doit s'ouvrir directement **en page web**.

---

## 6. Directives de design « iOS-Native Clean » (message avec le transcript IA)

L'utilisateur a collé les **design guidelines** produites par un agent de design :

- **Personnalité : « iOS-Native Clean »** — interface ultra-épurée, minimaliste.
- **Couleur de marque : charcoal `#1C1C1E`** — **INTERDIT : bleu, indigo, violet**.
- **Vert plein `#34C759` = Yes / correct** (obligatoire). Pas de « yes in blue ».
- Palette : fond `#F2F2F7`, texte `#1C1C1E`, secondaire `#8E8E93`, bordure `#E5E5EA`,
  orange `#FF9500`, rouge `#FF3B30`.
- **Navigation stack** (boutons retour partout).
- Bouton **Aide** = petite pastille discrète (pas un gros FAB).
- **Fond dynamique par matière** (imagerie floutée + scrim sombre).
- Quiz = carte unique centrée façon Anki, distraction minimale.
- Couleurs matières (seed) : C++ `#00599C`, Arduino `#00979D`, Anglais `#012169`,
  Espagnol `#AA151B`, Python `#3776AB`, Excel `#217346`.
- Un transcript décrivait une stack **React Native/Expo + FastAPI + MongoDB + Claude**
  (environnement externe `/app`, domaine `quiz-bosse.preview.emergentagent.com`, clé `EMERGENT_LLM_KEY`).

---

## 7. Demandes finales (messages les plus récents)

- **Lien pour tester sur une tablette (Xiaomi Pad 7).**
- « **Sandbox Not Found** » / « **Missing Traffic Access Token** » : problèmes d'accès
  liés à la sandbox (re-provisionnement continu), pas à l'app.
- Le PDF affichait une **option « ouvrir »** au lieu du document → il faut **voir le PDF
  directement dans la page**, pas un bouton d'ouverture.
- La **création automatique** de quiz/flashcards/mindmap **ne marchait pas** → réajuster.
- **Demande actuelle** : fournir **l'intégralité des fichiers + lignes de code + toutes les
  requêtes**, sous forme de **fichier ZIP**, pour le confier à une autre IA.

---

## Synthèse des exigences « non négociables »

1. Interface **web mobile-first**, lisible, épurée, professionnelle.
2. Couleur marque **charcoal**, **vert plein = correct**, **pas de bleu/indigo/violet**.
3. Bouton **Aide petit**, **boutons retour partout**.
4. **Lecteur PDF intégré** (rendu direct dans la page, sidebar de navigation par page,
   annotations : gomme qui n'efface que les annotations, surlignage semi-transparent, stylet).
5. **Génération automatique** depuis un PDF ajouté : résumé + flashcards + quiz + mindmap.
6. **Quiz modulables** (5/10/15/20/40/50/100 questions, difficulté), historique + erreurs expliquées.
7. **Recherche globale** (tout le contenu).
8. **Corbeille / suppression / restauration** (y compris cours par défaut).
9. **Stats** : radar (légende Premier/Deuxième essai, Réel, Globale, Globale réel),
   histogramme, pie chart — avec **légendes couleur** à côté.
10. **IA** reliée à internet, qui répond à tout (calcul, culture G, cours), sources cliquables.
11. Matières : **C++, Arduino, Anglais B2-C2, Espagnol B1-C2, Python, Excel**.
12. Version **Python (Streamlit)** lancée depuis **Spyder** → s'ouvre en page web.

---

## Architecture actuelle du projet (dossier `test-app/`)

```
web/                      → app web (la version principale, mobile-first)
  index.html
  css/styles.css
  js/app.js               → logique applicative (~1500 lignes)
  js/data.js              → données (matières, chapitres, questions, flashcards)
  js/vendor/pdf.min.js    → pdf.js (rendu PDF local)
  js/vendor/pdf.worker.min.js
  pdf/catalog.json        → mapping des PDF fournis
  pdf/README.txt
Bosse_app.py              → version Python / Streamlit (Spyder → page web)
requirements.txt          → dépendances Python
Dockerfile / docker-compose.yml (hérités du repo d'origine)
```

### Points techniques clés de `js/app.js`
- **Stockage** : `localStorage` (clé `bosse_data`) + **IndexedDB** (`bosse_files`) pour les blobs PDF.
- **Lecteur PDF** : `pdfjsLib.getDocument({ data })` → rendu canvas page par page.
- **Extraction texte** : `getTextContent()` → items `.str`.
- **Génération heuristique** (sans IA externe) : `generateFromText()` détecte
  définitions (« X est/signifie/désigne… ») → flashcards, QCM, détection de titres → mindmap,
  phrases clés → résumé.
- **IA** : calcul local + Wikipédia (fetch côté navigateur) + clé LLM optionnelle (endpoint OpenAI-compatible).

### Problèmes d'environnement rencontrés (importants pour la suite)
- Le **sandbox est re-provisionné en continu** → l'URL de préview `*.e2b.app` change/casse.
- La préview est **liée à la session** (jeton) → pas accessible depuis un appareil externe.
- Le sandbox n'a **pas d'accès internet direct** (curl → 000) sauf registries npm/pip.
- **MongoDB n'est pas disponible** dans le sandbox.
- Pas de clé LLM fournie (la clé `EMERGENT_LLM_KEY` citée dans un transcript appartient à un autre environnement).
- Les PDF fournis par l'utilisateur (ex. « Cours de C C++_copie.pdf ») **n'ont jamais été reçus** dans le workspace (dossier uploads vide).

---

## État d'avancement (où on en est)

✅ Interface web mobile-first complète (5 vues : Accueil, Quiz, Stats, Outils, IA).
✅ Design iOS-Clean charcoal/vert appliqué.
✅ Lecteur PDF intégré (canvas + sidebar pages), annotations corrigées.
✅ Génération auto (résumé/cartes/quiz/mindmap) depuis PDF ajouté — heuristique.
✅ Quiz modulables, historique, erreurs expliquées, recherche globale, corbeille.
✅ Stats radar/bar/pie avec légendes couleur.
✅ IA : calcul + Wikipédia + clé LLM optionnelle.
✅ Version Python/Streamlit (`Bosse_app.py`).

⚠️ Reste à faire / limites :
- La génération automatique est **heuristique** (pas de vraie IA) → qualité moyenne.
- L'IA « Arena » réelle n'est **pas branchée** (pas de clé/endpoint fourni).
- Le **déploiement stable** (GitHub Pages) dépend d'une activation manuelle côté utilisateur.
- Les **PDF distants** (universités) peuvent être bloqués par CORS → repli par proxy ou message.
