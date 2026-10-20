# 06 — Plan de tests et validation

**Objet :** vérifier que le matériel de semelle répond au cahier des charges rugby (8–12 h d'autonomie, impacts, humidité, température, BLE, stockage local, sécurité) avant intégration dans l'application d'analyse.

---

## 1. Phases de tests

| Phase | Objectif | Étape |
|-------|----------|-------|
| A | Validation électronique de base | Allumage, programmation MCU, lecture capteurs, BLE |
| B | Validation autonomie | Mesure de consommation, test durée réelle sur batterie |
| C | Validation mécanique (rugby) | Chocs, flexion, immersion, température |
| D | Validation système complète | Match simulé, stockage local, synchronisation, applicatif |

---

## 2. Phase A — Électronique de base (banc d'essai)

| Test | Méthode | Critère de succès |
|------|---------|-------------------|
| A1 — Allumage / programmation | Flash du nRF52840 via SWD, exécution du blink | LED clignote, MCU répond |
| A2 — Lectures capteurs | Lecture I2C accéléromètre, gyroscope, T/H ; ADC pression | Valeurs cohérentes, plages attendues |
| A3 — BLE | Appairage avec smartphone, envoi d'une mesure de test | Connexion établie, données reçues, chiffrement activé |
| A4 — Mémoire Flash | Écriture/lecture de 1 Mo, cycle marche-arrêt | Données conservées après reset |
| A5 — Réveil par mouvement | MCU en SYSTEM OFF, secousses sur accéléromètre | Réveil < 100 ms, consommation veille < 5 µA |
| A6 — Recharge induction | Pose sur socle induction, mesure courant charge | LED verte, charge ~100 mA, fin de charge automatique |
| A7 — Protection batterie | Court-circuit testé sur banc (avec fusible de protection) | Coupure par DW01A/MOSFET, pas d'incendie |

---

## 3. Phase B — Autonomie (cible 8–12 h)

| Test | Méthode | Critère de succès |
|------|---------|-------------------|
| B1 — Consommation par état | Multimètre/analyseur de puissance sur chaque mode (veille, marche, course, BLE continu) | Conforme au budget `04_budget_energetique_autonomie.md` (≤ 10 mA moyen visé) |
| B2 — Test endurance réel | Semelle allumée, cycle d'activité simulé (marche/course par intermittence), jusqu'à extinction | ≥ 8 h avec batterie 300 mAh ; objectif 10–12 h |
| B3 — Autonomie par température | Test B2 à +5 °C et +35 °C | ≥ 8 h dans les deux cas (la capacité Li-Po baisse au froid) |
| B4 — Cycle de charge | Charge complète, mesure du temps | 3–4 h à 100 mA, NTC coupe la charge si T > 45 °C |

---

## 4. Phase C — Mécanique et environnement (rugby)

| Test | Méthode | Critère de succès |
|------|---------|-------------------|
| C1 — Chocs / impacts | Chute de la semelle (avec électronique) depuis 1 m sur béton, 50 chocs ; ou impact masse 5 kg | Pas de casse, pas de désolidarisation, électronique encore fonctionnelle |
| C2 — Flexion répétée | 10 000 cycles de flexion de la semelle (machine à flexer) sur les ailes flexibles | Pas de casse des pistes flexibles ni décollement rigide/flex |
| C3 — Immersion / IP68 | Immersion 30 min à 1 m d'eau, puis séchage et test fonctionnel | Aucun court-circuit, toutes fonctions OK |
| C4 — Brouillard de sueur | Exposition à solution saline synthétique (simule sueur) 48 h | Pas de corrosion visible sur contacts, isolation maintenue |
| C5 — Température | Cycle -10 °C / +50 °C pendant 24 h, test fonctionnel à chaque extrême | Pas de dérive critique des capteurs, électronique opérationnelle |
| C6 — Confort / port | Test sur pied, marche et course 2 h | Pas d'arête saillante, pas de point de compression douloureux, poids < 30 g/semelle |

---

## 5. Phase D — Système complet (match simulé)

| Test | Méthode | Critère de succès |
|------|---------|-------------------|
| D1 — Acquisition complète | Course sur terrain avec la semelle, acquisition pression + accéléromètre + gyroscope + T/H | Données cohérentes, timestamps, pas de perte de frame |
| D2 — Stockage local | Smartphone éloigné pendant l'activité, puis rapproché pour synchronisation | Aucune donnée perdue, buffer Flash géré correctement |
| D3 — Synchronisation après-match | Transfert vers l'application d'analyse | Données lisibles, chiffrement OK, appareils non autorisés rejetés |
| D4 — Estimation vitesse/puissance | Comparaison avec une référence (chrono, tapis de course, plateforme de force) | L'algorithme d'estimation est cohérent (marge d'erreur à définir avec l'équipe data) |
| D5 — Autonomie réelle terrain | Match ou entraînement de 80–90 min, plusieurs sessions sans recharge | ≥ 8 h d'usage effectif |

---

## 6. Matériel de test nécessaire

- Programmeur/débogueur SWD (nRF52840 DK ou J-Link)
- Analyseur de consommation (ou multimètre de précision + shunt)
- Socle de recharge par induction 5 W
- Chambre climatique (-10…+60 °C) ou congélateur/étuve
- Bac d'immersion + solution saline synthétique
- Machine à flexion (ou test manuel répétitif)
- Smartphone/tablette avec l'application staff (BLE)
- Plateau de force / chrono / tapis de référence pour validation de l'estimation de performance

---

## 7. Critères d'acceptation (Go / No-Go)

La conception est validée pour passer au prototypage fonctionnel si :

1. Autonomie mesurée ≥ 8 h à 20 °C avec batterie 300 mAh ;
2. Aucun échec aux tests C1–C5 (impacts, flexion, immersion, sueur, température) ;
3. Connexion BLE stable à 5 m avec le smartphone dans la poche ;
4. Stockage local fonctionnel : 0 donnée perdue sur un match simulé de 90 min ;
5. Confort validé par au moins 3 joueurs lors du test C6 ;
6. Pas d'échauffement anormal de la batterie pendant la charge (NTC fonctionnel).

---
Suite : aucun document — conception matérielle terminée. Voir `README.md` pour l'index.