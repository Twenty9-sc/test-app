# 04 — Budget d'énergie et autonomie (cible : 8–12 h)

**Objectif :** démontrer qu'une microbatterie Li-Po de 300 mAh couvre un entraînement ou un match de rugby (8–12 h) grâce à la mise en veille des capteurs hors activité.

---

## 1. Hypothèses de consommation (composants du schéma `02_schema_electrique.md`)

Courants typiques, alimentation 3,3 V :

| Bloc | État | Courant typique | Durée dans la journée |
|------|------|-----------------|-----------------------|
| nRF52840 (MCU) | CPU actif @ 64 MHz | ~5,5 mA | Pendant l'activité + traitement |
| nRF52840 (radio BLE) | TX 0 dBm, bursts | ~13,5 mA pointe | Quelques ms par mesure (intermittent) |
| nRF52840 | BLE connecté (moyenne, intervalle 100 ms) | ~2–3 mA | Quand le smartphone est à portée |
| nRF52840 | SYSTEM OFF (veille, RTC ON) | ~1–2 µA | Quand le sportif ne court pas |
| LIS2DH12 (accéléromètre) | Low-power, 1 Hz | ~2 µA | En permanence (détection d'activité) |
| LIS2DH12 | Actif, mesures haute vitesse | ~150 µA | Pendant l'activité |
| BMI270 (gyroscope) | Normal | ~2,5–3 mA | Pendant l'activité uniquement |
| SHT31 (T/H) | Mesure 1 Hz | ~0,8 mA pointe, ~1 µA moy. | Ponctuel |
| W25Q16 (Flash SPI) | Écriture/Lecture | ~5 mA pointe | Écritures par blocs (buffer) |
| W25Q16 | Deep power-down | ~1–5 µA | Hors écriture |
| FSR + diviseurs pression | Lecture ADC | ~100 µA | Pendant l'activité |
| LDO TPS7A02 | Quiescent | ~1 µa | En permanence |

---

## 2. Modèle de journée type (match / entraînement intensif)

On suppose un joueur sur le terrain pendant **8 h**, avec une activité de course intermittent :

| Phase | Part du temps | Consommation moyenne estimée |
|-------|---------------|------------------------------|
| Repos / veille (capteurs OFF, MCU en SYSTEM OFF) | 50 % | ~10 µA (MCU 2 µA + accéléromètre 2 µA + flash 5 µA + LDO 1 µA) |
| Marche / échauffement (accéléromètre actif, gyro OFF, BLE peu actif) | 20 % | ~2 mA |
| Course intense (tous capteurs actifs, gyro ON, BLE bursts, flash écriture) | 30 % | ~15 mA (MCU 5,5 + gyro 3 + BLE 3 + flash 1 + pression 0,1 + divers) |

Consommation moyenne pondérée :

```
I_moy = 0,50 × 0,01 mA + 0,20 × 2 mA + 0,30 × 15 mA
      ≈ 0,005 + 0,4 + 4,5
      ≈ 4,9 mA  (disons 5 mA en cible de conception)
```

---

## 3. Autonomie calculée

| Batterie | Capacité | Consommation moyenne | Autonomie théorique | Coefficient de derating (température, vieillissement, pertes) | Autonomie réelle estimée |
|----------|----------|----------------------|---------------------|---------------------------------------------------------------|--------------------------|
| Li-Po | 300 mAh | 5 mA | 60 h | 0,45 | ~27 h |
| Li-Po | 300 mAh | 10 mA (usage intense, BLE continu) | 30 h | 0,45 | ~13,5 h |
| Li-Po | 200 mAh | 10 mA | 20 h | 0,45 | ~9 h |

**Conclusion :** avec une batterie **300 mAh** et une consommation moyenne pilotée à **≤ 10 mA** (veille agressive, BLE intermittent, gyro activé seulement en course), l'autonomie couvre largement la cible **8–12 h**, avec une marge de sécurité pour les jours froids (capacité Li-Po réduite) et le vieillissement de la cellule.

Pour un format encore plus compact, une batterie **200 mAh** reste viable si le logiciel limite l'activité BLE (stockage local privilégié, synchronisation après-match).

---

## 4. Leviers d'économie d'énergie (logiciel + matériel)

1. **Réveil par mouvement :** l'accéléromètre reste en mode low-power (1 Hz, 2 µA) et réveille le MCU par interruption INT1 uniquement quand une course est détectée.
2. **Gyroscope sous-demande :** le gyroscope (3 mA) n'est alimenté que pendant les phases de course détectées.
3. **BLE intermittent :** pas de connexion permanente. Les données sont mises en buffer dans la Flash 2 Mo et transmises par rafales après l'activité, ou quand le smartphone est à portée.
4. **Élançage ponctuel des diviseurs de pression :** les diviseurs FSR sont sous tension uniquement lors des acquisitions ADC.
5. **Pression dynamique :** fréquence d'acquisition adaptative (1 Hz au repos, 100–500 Hz en course).
6. **Flash en deep power-down** entre les écritures.

---

## 5. Recharge par induction

| Paramètre | Valeur cible |
|-----------|--------------|
| Puissance réceptrice | 5 W |
| Tension de sortie redresseur | 5 V → entrée MCP73831 |
| Courant de charge programmé | ~100 mA (C/3 pour 300 mAh) |
| Temps de charge complet | ~3–4 h |
| Indicateur | LED verte (via GPIO STAT du MCP73831) |
| Sécurité | NTC sur batterie (interruption charge si T > 45 °C), coupure fin de charge MCP73831 |

---

## 6. Suivant

- Intégration mécanique dans la semelle : `05_integration_mecanique_semelle.md`