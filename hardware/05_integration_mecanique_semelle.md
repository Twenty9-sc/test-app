# 05 — Intégration mécanique dans la semelle de rugby

**Objectif :** loger l'électronique dans la semelle en résistant aux contraintes du rugby (impacts répétés, humidité, transpiration, variations de température) tout en préservant le confort du joueur.

---

## 1. Contraintes de conception et solutions retenues

| Contrainte rugby | Solution envisagée (d'après le cahier des charges) | Détail de mise en œuvre |
|------------------|---------------------------------------------------|-------------------------|
| Impacts répétés (tackles, appuis au sol) | Boîtier électronique protégé, composants résistants aux chocs | Île rigide PCB sous le médio-pied, composants CMS basse profile, potting silicone/époxy, fixation par surmoulage TPU |
| Transpiration et humidité | Encapsulation étanche, matériaux résistants à la sueur | Boîtier IP68 (surmoulage TPU médical ou silicone), connecteurs absents (recharge induction), joints d'étanchéité aux zones de pression |
| Confort du joueur | Électronique fine, flexible si possible, sans arête saillante | PCB rigide-flex : île rigide < 6 mm d'épaisseur, ailes flexibles < 0,3 mm, bords arrondis, pas de composant saillant > 1 mm |
| Poids supplémentaire | Miniaturisation, intégration en zone peu sollicitée | Objectif < 30 g par semelle (électronique + batterie), positionnement sous le médio-pied (zone d'appui moindre que talon/avant-pied) |
| Déformation de la semelle | Composants rigides en zone protégée | Les composants rigides (MCU, batterie, chargeur) restent sur l'île rigide au médio-pied ; seules les ailes flexibles et les FSR suivent la déformation de la semelle |
| Autonomie | Capteurs basse consommation, transmission intermittente | Voir `04_budget_energetique_autonomie.md` |

---

## 2. Architecture mécanique proposée

```
                        SEMELLE DE RUGBY (coupe schématique)
   ___________________________________________________________________
  |                                                                   |
  |  [ Tige de la chaussure ]                                         |
  |                                                                   |
  |  +----------------------+--------------------------+            |
  |  |                      |                          |            |
  |  |   CAPTEURS PRESSION  |      CAPTEURS PRESSION   |            |
  |  |   (FSR zone talon)   |    (FSR zone avant-pied) |            |
  |  |   (aile flexible)    |       (aile flexible)    |            |
  |  |                      |                          |            |
  |  +---------+------------+------------+-----------+ |            |
  |            |                        |           | |            |
  |            |    SEMELLE INTERMÉDIAIRE  (EVA/TPU)   | |            |
  |            |  (absorption chocs, ~4–6 mm)          | |            |
  |            |                        |           | |            |
  |            +------------+------------+-----------+ |            |
  |                     |              |               |            |
  |           +---------v----------+   |               |            |
  |           |   ÎLE RIGIDE PCB   |   |               |            |
  |           |  (MCU, Flash,      |   |               |            |
  |           |   Chargeur, Prot.) |   |               |            |
  |           |  ~40 × 30 mm, < 6  |   |               |            |
  |           |   mm d'épaisseur   |   |               |            |
  |           +---------+----------+   |               |            |
  |                     |              |               |            |
  |           +---------v----------+   |               |            |
  |           |  BATTERIE Li-Po    |   |               |            |
  |           |  300 mAh, protégée |   |               |            |
  |           |  (zone protégée)   |   |               |            |
  |           +---------+----------+   |               |            |
  |                     |              |               |            |
  |           +---------v----------+   |               |            |
  |           |  BOBINE INDUCTION  |   |               |            |
  |           |  (recharge Qi)     |   |               |            |
  |           +--------------------+   |               |            |
  |                                                                   |
  |  Surmoulage TPU / silicone IP68 sur toute l'assemblage            |
  |___________________________________________________________________|
```

**Zones de placement :**
1. **Médio-pied (zone protégée)** : île rigide portant le nRF52840, la Flash, le LDO, le chargeur MCP73831, la protection batterie, les cristaux et l'antenne BLE (vers le bord externe, loin du métal).
2. **Médio-pied, sous l'île rigide** : batterie Li-Po souple 300 mAh, encapsulée, protégée contre la perforation.
3. **Bord externe du médio-pied** : bobine de recharge par induction (placée près de la surface pour le couplage magnétique, mais recouverte de TPU).
4. **Ailes flexibles (talon et avant-pied)** : 4 capteurs de pression FSR reliés par pistes flexibles à l'île rigide.
5. **Surface de la semelle (accès externe)** : aucune ouverture — aucune prise, aucun connecteur. Indication LED éventuellement visible à travers le TPU translucide.

---

## 3. Choix des matériaux

| Élément | Matériau recommandé | Justification |
|---------|---------------------|---------------|
| PCB rigide-flex | Polyimide (flex) + FR-4 (rigide), 2–4 couches | Flexibilité des ailes, rigidité de l'île composants, faible épaisseur |
| Encapsulation | TPU médical shore A 70–85 ou silicone biocompatible | Résistance à l'abrasion, à la sueur, aux produits de nettoyage, souplesse |
| Joints / surmoulage | TPU injecté ou silicone RTV | Étanchéité IP68, absorption des chocs |
| Batterie | Cellule Li-Po poche souple avec film de protection | Form factor mince, résistance à la déformation limitée |
| Fixation PCB | Adhésif double face industriel (3M 467 ou équivalent) + surmoulage | Pas de vis ni de clips saillants |

---

## 4. Étanchéité et protection

- **Indice de protection visé : IP68** (poussière + immersion temporaire). Aucun connecteur exposé.
- **Recharge par induction** : la bobine est sous le TPU ; le poseur de recharge se pose sous la semelle (ou sur un socle de vestiaire).
- **Batterie** : enfermée dans une poche rigide souple (TPU) soudée sur l'île PCB ; protection contre la perforation par une plaque de renfort mince sous la cellule.
- **Câblage interne** : pistes flexibles gainées, aucun fil dénudé, relief de contrainte aux transitions rigide/flex.

---

## 5. Poids et encombrement cibles

| Élément | Masse cible | Encombrement cible |
|---------|-------------|---------------------|
| Électronique (PCB + composants) | < 12 g | 40 × 30 × 6 mm (île rigide) |
| Batterie 300 mAh | < 10 g | 45 × 30 × 4 mm |
| Bobine induction + encapsulant | < 5 g | Ø ~25 mm |
| Capteurs pression (4 × FSR + pistes) | < 3 g | Ailes flexibles |
| **TOTAL par semelle** | **< 30 g** | — |

---

## 6. Risques et actions de mitigation

| Risque | Niveau | Mitigation |
|--------|--------|------------|
| Éclatement de la batterie sous impact | Critique | Boîtier protecteur, plaque de renfort, cellule Li-Po poche avec limite de déformation, test de choc |
| Infiltration de sueur → court-circuit | Majeur | IP68, surmoulage complet, pas de connecteur, tests d'immersion |
| Confort / arête saillante | Majeur | Profil < 6 mm, bords arrondis, tests de port par des joueurs |
| Perte de signal BLE à travers la semelle | Mineure | Antenne au bord externe, tests de portée avec pied au sol |
| Décollement des pistes flexibles | Mineure | Renfort rigide-flex, adhésif industriel, tests de flexion répétée |

---

## 7. Suivant

- Plan de tests et validation : `06_plan_tests_validation.md`