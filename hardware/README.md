# Conception matérielle — Système de mesure de performance intégré à la semelle (rugby)

> Projet : électronique embarquée dans une semelle de rugby pour la mesure des performances sportives (pression, accélération, gyroscope, température/humidité), communication BLE vers smartphone/tablette, stockage local, recharge par induction.
>
> Langue des documents : français (conformément au cahier des charges utilisateur).

## Contenu du dossier

| Fichier | Description |
|---------|-------------|
| `01_specification_materiel.md` | Cahier des charges technique, architecture bloc, choix des composants |
| `02_schema_electrique.md` | Schéma électrique détaillé (blocs, connexions, netlist simplifiée) |
| `03_nomenclature_BOM.csv` | Nomenclature (Bill of Materials) avec références, quantités, coûts indicatifs |
| `04_budget_energetique_autonomie.md` | Calcul de consommation et autonomie visée 8–12 h |
| `05_integration_mecanique_semelle.md` | Intégration dans la semelle, contraintes rugby, étanchéité, confort |
| `06_plan_tests_validation.md` | Plan de tests, validation et qualification (impacts, humidité, température) |

## Comment lire cette conception

Cette conception est un **premier prototype réaliste** (TRL 4–5). Elle reprend exactement les choix proposés dans le cahier des charges utilisateur :

1. **Alimentation** : microbatterie Li-Po rechargeable, zone protégée de la semelle, autonomie 8–12 h, recharge par induction, gestion énergétique (capteurs actifs uniquement pendant l'activité, veille sinon), protection batterie (chocs, surchauffe, déformations).
2. **Communication** : Bluetooth Low Energy (BLE) vers smartphone/tablette/staff, mémoire interne pour stockage local pendant le match, synchronisation après l'activité, transmission chiffrée.
3. **Capteurs** : pression, accéléromètre, gyroscope, température et humidité intégrés dans la semelle.
4. **Microcontrôleur** : acquisition des mesures et gestion des capteurs.

> **Point important du cahier des charges** : la vitesse et la puissance de frappe ne sont pas mesurées directement par une puce ; elles sont estimées à partir des données des capteurs par des algorithmes validés (côté application). Les capteurs d'impact caractérisent certains chocs, mais ne diagnostiquent pas à eux seuls une blessure.

## Aperçu de l'architecture

```
+-----------------------------------------------------------------------+
|                         SEMELLE DE RUGBY (TPU, IP68)                  |
|                                                                       |
|  [ Pression ]  [ Accéléromètre ]  [ Gyroscope ]  [ Temp./Humidité ]   |
|       |               |               |               |               |
|       +-------+-------+---------------+---------------+               |
|                   |                       |                           |
|             +-----v-----+           +-----v-----+                     |
|             |  MCU nRF  |           |  Flash 2  |                     |
|             | 52840     |           |  Mo SPI   |                     |
|             | (BLE +    |           +-----+-----+                     |
|             |  Cortex   |           |                       |
|             |  -M4F)    |           |                       |
|             +-----+-----+           |                       |
|                   |                  |                       |
|                   +---------+--------+                       |
|                             |                                  |
|                    +--------v--------+                         |
|                    | Gestion         |                         |
|                    | d'énergie       |                         |
|                    +--------+--------+                         |
|                             |                                  |
|              +--------------v--------------+                    |
|              | Batterie Li-Po 300 mAh      |                    |
|              | + Protection + NTC          |                    |
|              +--------------+--------------+                    |
|                             |                                  |
|                    +--------v--------+                         |
|                    | Recharge par    |                         |
|                    | induction (Qi)  |                         |
|                    +-----------------+                         |
+-----------------------------------------------------------------------+
```

## Prérequis pour la suite

Aucun outil de CAO électronique n'est obligatoire : les fichiers de ce dossier sont des spécifications d'ingénierie lisibles qui permettent de faire dessiner le schéma et le circuit imprimé par un bureau d'études (KiCad, Altium, Cadence…).

---
Dernière mise à jour : 2026-10-20 — Branche `arena/57896d29-test-app`