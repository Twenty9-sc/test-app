# 01 — Spécification matérielle et architecture

**Objet :** système électronique compact intégré dans la semelle d'une chaussure de rugby pour la mesure des performances sportives.

**Destinataire :** bureau d'études électronique / prototypage rapide.

---

## 1. Exigences du cahier des charges (rappel)

| Exigence | Cible |
|----------|-------|
| Fonction | Mesure des performances sportives (course, appuis, impacts, accélérations) |
| Milieu d'usage | Rugby : impacts répétés, transpiration, humidité, variations de température |
| Intégration | Dans la semelle, fine, flexible si possible, sans arête saillante |
| Alimentation | Microbatterie Li-Po rechargeable, zone protégée de la semelle |
| Autonomie | 8 à 12 h (entraînement ou match) |
| Recharge | Par induction (pas de connecteur exposé) |
| Gestion énergie | Capteurs actifs pendant l'activité, veille quand le sportif ne court pas |
| Sécurité batterie | Protection contre chocs, surchauffe, déformations |
| Communication | Bluetooth Low Energy (BLE) vers smartphone / tablette / équipement staff |
| Stockage | Mémoire interne (mesures conservées si smartphone éloigné) |
| Sécurité données | Transmission chiffrée, authentification des appareils autorisés |
| Capteurs | Pression, accéléromètre, gyroscope, température, humidité |
| Contrainte clé | Vitesse et puissance de frappe = estimés par algorithmes (pas de puce directe) |
| Contrainte clé | Capteurs d'impact = caractérisation de chocs, pas de diagnostic de blessure |

---

## 2. Architecture matérielle proposée (blocs)

```
┌─────────────────────────────────────────────────────────────────────┐
│                      SEMELLE ÉLECTRONIQUE (TPU, IP68)               │
│                                                                     │
│  ┌──────────┐   ┌─────────────┐   ┌──────────────┐   ┌─────────┐   │
│  │ Pression │   │ Accéléromètre│   │  Gyroscope   │   │Temp./Hum│   │
│  │ (FSR x4) │   │ 3 axes      │   │ 3 axes       │   │  SHT31  │   │
│  └────┬─────┘   └──────┬──────┘   └──────┬───────┘   └────┬────┘   │
│       │                │                 │                │        │
│       └───────┬────────┴────────┬────────┘                │        │
│               │                 │                         │        │
│               └────────┬────────┴──────────────┬──────────┘        │
│                        │                       │                   │
│             ┌──────────▼──────────┐   ┌───────▼───────┐            │
│             │   MICROCONTRÔLEUR   │   │ MÉMOIRE INTERNE│           │
│             │  nRF52840 (BLE 5.2) │   │  Flash 2 Mo SPI│           │
│             │  Cortex-M4F + radio │   └───────┬───────┘            │
│             └──────────┬──────────┘           │                    │
│                        │                      │                    │
│                        └──────────┬───────────┘                    │
│                                   │                                │
│                        ┌──────────▼──────────┐                     │
│                        │   GESTION           │                     │
│                        │   D'ÉNERGIE (PMIC)  │                     │
│                        └──────────┬──────────┘                     │
│                                   │                                │
│              ┌────────────────────┼────────────────────┐           │
│              │                                    │           │
│       ┌──────▼──────┐                   ┌──────────▼──────┐   │
│       │ BATTERIE    │                   │ RECHARGE        │   │
│       │ Li-Po 300   │                   │ PAR INDUCTION   │   │
│       │ mAh + prot. │                   │ (Qi RX + MCP73831)│   │
│       └──────┬──────┘                   └──────────┬──────┘   │
│              │                                    │           │
│              └────────────────────┬────────────────┘           │
│                                   │                            │
│                        ┌──────────▼──────────┐                 │
│                        │  ANTENNE BLE (PCB)  │                 │
│                        └─────────────────────┘                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Choix de composants (premier prototype)

### 3.1 Microcontrôleur — nRF52840 (Nordic Semiconductor)
- **Pourquoi :** Cortex-M4F 64 MHz, radio BLE 5.2 intégrée (+10 mA en TX, -95 dBm en RX), nombreux GPIO, ADC 12 bits, USB (debug), mode SYSTEM OFF ~1 µA avec RTC.
- **Package :** QFN48 (ou module certifié Raytac MDBT50Q-1000 pour réduire la complexité RF).
- **Rôle :** acquisition capteurs, fusion de données, BLE, gestion mémoire, gestion énergie, réveil par interruption accéléromètre.

### 3.2 Capteurs dans la semelle

| Capteur | Composant suggéré | Interface | Plage / Précision | Rôle |
|---------|-------------------|-----------|-------------------|------|
| Pression (4 zones : talon, métatarse, orteils, médio-pied) | FSR406 (Interlink) ou cellules piézoresistives custom | Diviseur de tension + ADC MCU | 0–70 N par zone | Détection des appuis, temps de contact, schéma de foulée |
| Accéléromètre 3 axes | LIS2DH12 (ST) ou LIS3DH | I2C / SPI, INT1/INT2 | ±2/±4/±8/±16 g, 1,6 kHz | Détection d'activité, réveil, impacts, estimation de vitesse |
| Gyroscope 3 axes | BMI270 (Bosch) ou L3GD20H | I2C / SPI | ±250–±2000 °/s | Orientation du pied, rotation, analyse d'appui |
| Température + humidité | SHT31-DIS (Sensirion) | I2C | -40…+125 °C, ±0,3 °C ; 0…100 % HR, ±2 % | Compensation thermique, surveillance environnementale |

### 3.3 Mémoire interne
- **W25Q16JV** (Winbond) — Flash SPI 2 Mo (16 Mbit), sommeil ~1 µA, écriture/page rapide.
- Rôle : stockage local des mesures pendant le match (buffer circulaire), synchronisation différée vers l'application.

### 3.4 Alimentation et recharge

| Bloc | Composant suggéré | Spécification |
|------|-------------------|---------------|
| Batterie | Li-Po souple 3,7 V / 300 mAh, format ~45 × 30 × 4 mm | Autonomie 8–12 h cible |
| Protection batterie | DW01A + 2 MOSFETs (ou S-8261) | Coupure sur surtension, sous-tension, surintensité |
| Thermistance charge | NTC 10 kΩ (0603) | Surveillance température batterie pendant charge |
| Récepteur induction | Module induction 5 W (Qi-like, RX) + redresseur | Entrée 5 V vers chargeur |
| Chargeur Li-Po | MCP73831T-2ACI/OT (ou BQ25125) | Courant de charge programmable ~100 mA, termination automatique |
| Régulateur 3,3 V | TPS7A02 / MCP1700 (LDO, faible bruit) | Alimentation MCU + capteurs |
| Convertisseur buck | TPS62745 (optionnel) | Rendement élevé si rail 1,8 V nécessaire |

### 3.5 Communication sans fil
- **BLE 5.2** intégré au nRF52840. Antenne : piste PCB 2,4 GHz (chip antenna ou trace accordée), boîtier métallique interdit au-dessus.
- Sécurité : pairing LE Secure Connections, chiffrement AES-CCM, whitelist des appareils staff autorisés (côté appli).

### 3.6 Interface utilisateur minimale (prototype)
- 1 bouton ON/OFF (marche/arrêt physique, caché sous la semelle).
- 1 LED verte (état charge / allumé) + 1 LED rouge (erreur / batterie faible), visibles à travers la semelle ou cachées selon le design.

---

## 4. Arbres de décision retenus

| Décision | Option retenue | Justification |
|----------|---------------|---------------|
| Alimentation | Li-Po rechargeable | Réaliste pour premier prototype, énergie volumétrique élevée |
| Recharge | Induction | Évite connecteurs exposés à la sueur/humidité → étanchéité IP68 |
| Connectivité | BLE | Basse consommation, smartphones/tablettes omniprésents |
| Stockage | Flash SPI externe | Conserve les mesures si smartphone éloigné, synchronisation après-match |
| MCU | nRF52840 | BLE + MCU + basse consommation en une seule puce |
| Réveil | Accéléromètre (wake-on-motion) | Capteurs actifs seulement pendant la course |

---

## 5. Limites et hypothèses (à valider)

1. Vitesse et puissance de frappe sont estimées par algorithmes à partir des données pression + accéléromètre (pas de mesure directe par puce).
2. Les capteurs d'impact caractérisent des chocs, mais ne diagnostiquent pas une blessure.
3. L'autonomie 8–12 h dépend du duty cycle (fréquence d'acquisition, activité BLE). Voir `04_budget_energetique_autonomie.md`.
4. Les composants suggérés sont des références de catalogue disponibles en 2026 ; ils peuvent être substitués par des équivalents lors du PCB.

---
Suite : `02_schema_electrique.md`