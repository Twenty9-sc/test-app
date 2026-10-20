# 02 — Schéma électrique détaillé

**Version :** 1.0 (premier prototype)  
**Format :** description texte/netlist — à retranscrire en schéma CAO (KiCad, Altium, Cadence…) pour réalisation du PCB.

---

## 1. Arbre de blocs (résumé)

```
BATTERIE Li-Po (3,7 V / 300 mAh)
        |
   +----v----+      +-------------------+
   | PROTECTION|----| VBAT (rail brut)  |
   | DW01A +   |      |                 |
   | MOSFETs   |      +----+----+-------+
   +----+----+           |    |    |
        |                |    |    |
  +-----v-----+  +-------v----+    +----v------+
  | RECHARGE  |  |  REGUL 3,3V |    |  REGUL 1,8V|
  | induction |  |  (LDO)      |    | (buck opt.)|
  | Qi RX +   |  |  MCU+sensors|    |  (option)  |
  | MCP73831  |  +------+------+    +-----+------+
  +-----+-----+         |              |
        |               |              |
   +----v----+           |              |
   | COIL    |           |              |
   | INDUCTION|          |              |
   +----------+          |              |
                         |              |
              +----------v----------+   |
              |   MCUNRF52840 QFN48   |   |
              |  BLE 5.2 + Cortex-M4F |   |
              +----------+------------+   |
                         |                |
        +----------------+----------------+----------------+
        |                |                |                |
 +------v------+ +------v------+ +------v------+ +------v------+
 | Accéléromètre| | Gyroscope   | | Temp./Humid.| | Flash SPI   |
 | LIS2DH12      | | BMI270      | | SHT31       | | W25Q16JV    |
 | I2C + INT     | | I2C         | | I2C         | | SPI         |
 +------+--------+ +------+-----+ +------+------+ +------+------+
        |                |                |                |
        +----------------+----------------+----------------+
                                    |
                         +----------v----------+
                         |  MATRICE PRESSION   |
                         |  4 x FSR + diviseurs|
                         |  vers ADC MCU       |
                         +---------------------+
```

---

## 2. Liste des circuits intégrés (U)

| Réf. | Composant | Fonction | Boîtier | Alimentation |
|------|-----------|----------|---------|--------------|
| U1 | nRF52840-QIAA | MCU + BLE 5.2 | QFN48 6×6 mm | 1,7–3,6 V (VDD), 1,8 V (DVDD) |
| U2 | LIS2DH12TR | Accéléromètre 3 axes | LGA-14 | 1,7–3,6 V |
| U3 | BMI270 | Gyroscope 3 axes (+ accel) | LGA-14 | 1,2–3,6 V |
| U4 | SHT31-DIS | Température + humidité | DFN-8 | 2,4–5,5 V |
| U5 | W25Q16JVSIQ | Flash SPI 2 Mo | SOP-8 | 2,7–3,6 V |
| U6 | MCP73831T-2ACI/OT | Chargeur Li-Po | SOT-23-5 | 3,75–6,5 V entrée |
| U7 | DW01A + 2× MOSFET | Protection batterie (over/under-current, over/under-voltage) | SOT-23 / SOT-23-6 | — |
| U8 | TPS7A02 / MCP1700 | LDO 3,3 V (rail capteurs + MCU) | SOT-23-5 | 2,2–5,5 V entrée |

---

## 3. Composants passifs et électromécaniques

| Réf. | Composant | Valeur / type | Fonction |
|------|-----------|---------------|----------|
| BAT1 | Batterie Li-Po souple | 3,7 V / 300 mAh, ~45×30×4 mm | Stockage énergie |
| COIL1 | Bobine réceptrice induction | Module Qi-like 5 W, sortie 5 V | Recharge sans contact |
| D1 | Diode Schottky | 1N5819 ou équivalent | Protection polarité inverse (optionnel) |
| L1 | Inducteur DCDC | 4,7 µA si buck utilisé (TPS62745) | Conversion 3,3 V → 1,8 V |
| X1 | Cristal | 32 MHz | Horloge nRF52840 |
| X2 | Cristal | 32,768 kHz | Horloge RTC / veille basse conso |
| C1–C8 | Condensateurs découpillage | 100 nF + 10 µF (tantale/MLCC) | Stabilité rails |
| R1–R8 | Résistances pull-up I2C | 4,7 kΩ | Bus I2C capteurs |
| R9–R12 | Diviseurs pression FSR | 10 kΩ (à calibrer) | Lecture capteurs pression sur ADC |
| BTN1 | Bouton-poussoir | ON/OFF caché sous semelle | Marche/arrêt |
| LED1 | LED verte | 0603 | État allumé / charge |
| LED2 | LED rouge | 0603 | Erreur / batterie faible |
| NTC1 | Thermistance | 10 kΩ, B=3435 | Surveillance température batterie |
| ANT1 | Antenne BLE | Piste PCB 2,4 GHz ou chip antenna | Radio BLE |

---

## 4. Connexions détaillées (netlist simplifié)

### 4.1 Alimentation

```
BAT1 (+) ──> PROTECTION (U7) ──> VBAT ──> LDO U8 (3,3 V) ──> VCC_3V3 ──> U1, U2, U3, U4, U5
VBAT ───────────────────────────────────────────────────────────────────> VCC_BAT (direct)
COIL1 ──> REDRESSEUR ──> 5 V ──> MCP73831 (U6) ──> BAT1 (+) (charge)
MCP7381 STAT ──> GPIO nRF52840 (état charge)
NTC1 ───────────────────────> thermistor pin MCP73831 (température batterie)
```

Rails :
- **VBAT** : 3,0–4,2 V (batterie) — alimente directement le chargeur et, via LDO, le reste.
- **VCC_3V3** : 3,3 V régulés — MCU, capteurs, flash.
- **VDD_RF** : 1,8–3,3 V (nRF52840, alimentation radio interne, découplage proche).

### 4.2 Microcontrôleur nRF52840 (U1) — connexions principales

| Broche nRF52840 | Signal | Destination | Commentaire |
|-----------------|--------|-------------|-------------|
| VDD / VDDH | 3,3 V | LDO U8 | Alimentation MCU |
| VSS | GND | Masse commune | — |
| DEC1–DEC4 | 1 µF | GND (proche du puce) | Découplage régulateur interne |
| XC1 / XC2 | 32 MHz | Cristal X1 + condensateurs | Horloge système |
| XL1 / XL2 | 32,768 kHz | Cristal X2 | RTC basse consommation |
| ANT | 2,4 GHz | Piste/antenne ANT1 via réseau de匹配 | Sortie radio BLE |
| P0.02 / P0.03 | SDA / SCL I2C | U2, U3, U4 | Bus capteurs (pull-up 4,7 kΩ) |
| P0.06 | SCK SPI | U5 (flash) | Horloge SPI |
| P0.07 | MOSI SPI | U5 (flash) | Données sortie MCU |
| P0.08 | MISO SPI | U5 (flash) | Données entrée MCU |
| P0.09 | CSn SPI | U5 (flash) | Sélecteur flash |
| P0.10 | INT accéléromètre | U2 INT1 | Wake-on-motion (réveil MCU) |
| P0.11 | INT gyroscope | U3 INT | Interruption gyroscope |
| P0.30 | ADC IN | Diviseur pression zone 1 | Lecture FSR1 |
| P0.31 | ADC IN | Diviseur pression zone 2 | Lecture FSR2 |
| P0.04 | ADC IN | Diviseur pression zone 3 | Lecture FSR3 |
| P0.05 | ADC IN | Diviseur pression zone 4 | Lecture FSR4 |
| P0.16 | GPIO | BTN1 | Marche/arrêt |
| P0.17 | GPIO | LED1 (verte) | État |
| P0.18 | GPIO | LED2 (rouge) | Erreur / faible batterie |
| P0.19 | GPIO | MCP73831 STAT | État de charge |
| RESET | GPIO | Bouton reset (debug) | Reset externe |

> **Réveil :** en mode SYSTEM OFF, seul le RTC et l'interruption INT1 de l'accéléromètre (wake-on-motion) maintiennent le MCU réveillable. Consommation < 5 µA.

### 4.3 Capteurs

**I2C (bus partagé) :**
```
MCU SDA (P0.02) ── pull-up 4,7 kΩ ──> SDA U2 (LIS2DH12)
MCU SCL (P0.03) ── pull-up 4,7 kΩ ──> SCL U2
                                   ├──> SDA U3 (BMI270)
                                   ├──> SCL U3
                                   ├──> SDA U4 (SHT31)
                                   └──> SCL U4
```
Adresses I2C : LIS2DH12 0x18/0x19, BMI270 0x68/0x69, SHT31 0x44/0x45 — sélectionner des adresses distinctes via broches ADDR.

**SPI (flash) :** comme indiqué au tableau 4.2 (U5).

**Pression (analogique) :** chaque FSR en diviseur avec 10 kΩ vers VCC_3V3 ; point milieu sur entrée ADC 12 bits du nRF52840. Élançage des diviseurs seulement pendant les mesures (via GPIO ou load switch) pour économiser l'énergie.

---

## 5. Schéma de principe (ASCII)

```
                     +3,3 V
                      |
   +------------------+------------------+
   |                  |                  |
  [U8]              [U1]              [U5]
 LDO 3,3 V        nRF52840          Flash 2 Mo
   |         +-----+-----+             |
   |         |  BLE 5.2  |             |
   |         +-----+-----+             |
   |              |                    |
   |      +-------+-------+            |
   |      |               |            |
   |   [U2]           [U3]            |
   | Accéléro.      Gyroscope         |
   | I2C + INT      I2C               |
   |      |               |            |
   |      +-------+-------+            |
   |              |                    |
   |          [U4]                     |
   |       Temp./Humid.                |
   |       I2C                         |
   |              |                    |
   +------+-------+---------------------+
          |
     [Matrice pression 4×FSR]
          |
     (ADC MCU)
```

---

## 6. Règles de conception PCB (résumé)

- **Empilement :** 2 couches minimum, 4 couches recommandées (plan de masse continu sous la radio).
- **Radio BLE :** antenne 2,4 GHz sur bord de plaque, pas de plan de masse sous l'antenne, piste d'alimentation radio courte et découplée (C < 2 mm de VDD nRF52840).
- **Flexibilité :** PCB rigide-flex — île rigide sous le médio-pied (MCU, chargeur, protection), ailes flexibles vers les zones de pression (talon, avant-pied).
- **Épaisseur cible :** < 1,2 mm rigide, < 0,3 mm flex.
- **Masse :** une seule masse (star ground près de la batterie), pas de boucles de masse sous les capteurs de pression.
- **Test points :** accès SVO (SWD) et UART sur pastilles pour programmation/debug en atelier.

---

## 7. Suivant

- Nomenclature complète : `03_nomenclature_BOM.csv`
- Budget d'énergie et autonomie : `04_budget_energetique_autonomie.md`
- Intégration mécanique dans la semelle : `05_integration_mecanique_semelle.md`