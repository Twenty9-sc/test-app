# -*- coding: utf-8 -*-
"""
F1 Setup Complet - 2012 Rouge / 2017 Bleu / 2020 Violet
Edition Tablette + Desktop - Tous circuits et stratégies adaptés par année
"""

import streamlit as st
import json
import datetime

st.set_page_config(page_title="F1 Setup Complet 2012-2017-2020", page_icon="🏁", layout="wide", initial_sidebar_state="expanded")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;800&family=Inter:wght@500;700;800&display=swap');
[data-testid="stAppViewContainer"]{background:radial-gradient(1000px 500px at 10% 0%,rgba(124,58,237,0.18),transparent),radial-gradient(1000px 500px at 90% 0%,rgba(37,99,235,0.18),transparent),radial-gradient(800px 400px at 50% 100%,rgba(220,38,38,0.12),transparent),linear-gradient(180deg,#0A0E1A 0%,#12182A 100%)}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0F1220,#1A1A2E);border-right:2px solid #2A2A4A}
h1{font-family:Orbitron!important;font-weight:800!important;letter-spacing:0.02em}
.year-2012{background:linear-gradient(135deg,#450A0A,#B91C1C,#EF4444);color:white;padding:14px 18px;border-radius:14px;border:1px solid #FCA5A5;box-shadow:0 8px 24px rgba(185,28,28,0.35)}
.year-2017{background:linear-gradient(135deg,#1E1B4B,#1E40AF,#3B82F6);color:white;padding:14px 18px;border-radius:14px;border:1px solid #93C5FD;box-shadow:0 8px 24px rgba(37,99,235,0.35)}
.year-2020{background:linear-gradient(135deg,#1E1640,#5B21B6,#7C3AED);color:white;padding:14px 18px;border-radius:14px;border:1px solid #C4B5FD;box-shadow:0 8px 24px rgba(124,58,237,0.35)}
.card-2012{background:linear-gradient(135deg,rgba(69,10,10,0.9),rgba(127,29,29,0.8));border-left:4px solid #EF4444;border-radius:12px;padding:14px;margin:8px 0}
.card-2017{background:linear-gradient(135deg,rgba(30,27,75,0.9),rgba(30,64,175,0.8));border-left:4px solid #3B82F6;border-radius:12px;padding:14px;margin:8px 0}
.card-2020{background:linear-gradient(135deg,rgba(30,22,64,0.9),rgba(91,33,182,0.8));border-left:4px solid #7C3AED;border-radius:12px;padding:14px;margin:8px 0}
.badge-red{background:#EF4444;color:white;padding:3px 10px;border-radius:999px;font-weight:800;font-size:11px}
.badge-blue{background:#3B82F6;color:white;padding:3px 10px;border-radius:999px;font-weight:800;font-size:11px}
.badge-violet{background:#7C3AED;color:white;padding:3px 10px;border-radius:999px;font-weight:800;font-size:11px}
.stButton>button{border-radius:10px!important;font-weight:800!important}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# DATA PAR ANNEE
YEARS = {
    "2012": {
        "color": "rouge",
        "hex": "#EF4444",
        "hex_dark": "#B91C1C",
        "icon": "🔴",
        "title": "F1 2012 - Edition Rouge",
        "circuits": {
            "🇦🇺 Australie - Melbourne": {"code": "AUS", "type": "Semi-urbain", "strategie": "1-2 arrêts, KERS essentiel ligne droite"},
            "🇲🇾 Malaisie - Sepang": {"code": "MYS", "type": "Chaud/Humide", "strategie": "2-3 arrêts, gestion température"},
            "🇨🇳 Chine - Shanghai": {"code": "CHN", "type": "Technique", "strategie": "1-2 arrêts, graining avant"},
            "🇧🇭 Bahreïn - Sakhir": {"code": "BHR", "type": "Traction", "strategie": "2 arrêts, freinage critique"},
            "🇪🇸 Espagne - Barcelone": {"code": "ESP", "type": "Aéro", "strategie": "2-3 arrêts, test aéro"},
            "🇲🇨 Monaco - Monte-Carlo": {"code": "MCO", "type": "Urbain", "strategie": "1 arrêt, qualif cruciale"},
            "🇨🇦 Canada - Montréal": {"code": "CAN", "type": "Freinage", "strategie": "1-2 arrêts, mur des champions"},
            "🇪🇺 Europe - Valence": {"code": "EUR", "type": "Urbain", "strategie": "1-2 arrêts, traction"},
            "🇬🇧 GB - Silverstone": {"code": "GBR", "type": "Rapide", "strategie": "2 arrêts, Copse rapide"},
            "🇩🇪 Allemagne - Hockenheim": {"code": "GER", "type": "Stadium", "strategie": "2 arrêts, Motodrom"},
            "🇭🇺 Hongrie - Hungaroring": {"code": "HUN", "type": "Technique", "strategie": "2 arrêts, pas de dépassement"},
            "🇧🇪 Belgique - Spa": {"code": "BEL", "type": "Légendaire", "strategie": "1-2 arrêts, Eau Rouge à fond"},
            "🇮🇹 Italie - Monza": {"code": "ITA", "type": "Vitesse", "strategie": "1 arrêt, ailerons mini"},
            "🇸🇬 Singapour - Marina Bay": {"code": "SGP", "type": "Nuit", "strategie": "2-3 arrêts, SC fréquent"},
            "🇯🇵 Japon - Suzuka": {"code": "JPN", "type": "Pilote", "strategie": "2 arrêts, 130R à fond"},
            "🇰🇷 Corée - Yeongam": {"code": "KOR", "type": "Mixte", "strategie": "2 arrêts, poussière"},
            "🇮🇳 Inde - Buddh": {"code": "IND", "type": "Fluide", "strategie": "1-2 arrêts, 3 DRS"},
            "🇦🇪 Abu Dhabi - Yas Marina": {"code": "ABU", "type": "Twillight", "strategie": "1-2 arrêts, hôtel"},
            "🇺🇸 USA - Austin": {"code": "USA", "type": "Moderne", "strategie": "1-2 arrêts, COTA T1"},
            "🇧🇷 Brésil - Interlagos": {"code": "BRA", "type": "Anti-horaire", "strategie": "2 arrêts, pluie 50%"},
        },
        "strategies": [
            "🔋 KERS: 6s/tour, utilise en sortie virage lent + défense",
            "⛽ Essence: Lean/Standard/Rich - Rich = +0.4s mais +20% conso",
            "🛞 Pneus 2012: Prime (dur) / Option (tendre) - Option 1.2s plus rapide mais 10 tours max",
            "🏁 DRS: 1 zone en 2012, seulement si <1s",
            "🔧 Setup 2012 méta: Ailerons hauts car pas d'ERS, ressorts durs",
        ],
        "presets": {
            "🔴 2012 Rouge - Equilibré": {"aero_av": 7, "aero_ar": 7, "diff_on": 75, "diff_off": 65, "camber_av": -2.5, "camber_ar": -1.2, "toe_av": 0.08, "toe_ar": 0.25, "susp_av": 6, "susp_ar": 5, "arb_av": 6, "arb_ar": 5, "height_av": 4, "height_ar": 5, "brake_press": 92, "brake_bias": 56, "tyre_av": 22.5, "tyre_ar": 20.5, "ballast": 6},
            "🚀 2012 Monza - Mini ailerons": {"aero_av": 1, "aero_ar": 1, "diff_on": 80, "diff_off": 70, "camber_av": -2.2, "camber_ar": -1.0, "toe_av": 0.12, "toe_ar": 0.35, "susp_av": 8, "susp_ar": 7, "arb_av": 8, "arb_ar": 7, "height_av": 2, "height_ar": 2, "brake_press": 98, "brake_bias": 58, "tyre_av": 24.0, "tyre_ar": 22.0, "ballast": 5},
            "🔄 2012 Monaco - Max appui": {"aero_av": 11, "aero_ar": 11, "diff_on": 65, "diff_off": 60, "camber_av": -2.8, "camber_ar": -1.4, "toe_av": 0.05, "toe_ar": 0.20, "susp_av": 3, "susp_ar": 2, "arb_av": 3, "arb_ar": 2, "height_av": 6, "height_ar": 7, "brake_press": 88, "brake_bias": 54, "tyre_av": 21.5, "tyre_ar": 19.5, "ballast": 7},
        }
    },
    "2017": {
        "color": "bleu",
        "hex": "#3B82F6",
        "hex_dark": "#1E40AF",
        "icon": "🔵",
        "title": "F1 2017 - Edition Bleue",
        "circuits": {
            "🇦🇺 Australie - Melbourne": {"code": "AUS", "type": "Semi-urbain", "strategie": "1 arrêt US-SS, ERS Medium"},
            "🇨🇳 Chine - Shanghai": {"code": "CHN", "type": "Avant limité", "strategie": "2 arrêts, S1 graining"},
            "🇧🇭 Bahreïn - Sakhir": {"code": "BHR", "type": "Arrière limité", "strategie": "2 arrêts SS-S-SS, traction"},
            "🇷🇺 Russie - Sotchi": {"code": "RUS", "type": "Lisse", "strategie": "1 arrêt US-S, peu d'usure"},
            "🇪🇸 Espagne - Barcelone": {"code": "ESP", "type": "Complet", "strategie": "2 arrêts, T3 usure"},
            "🇲🇨 Monaco - Monte-Carlo": {"code": "MCO", "type": "Urbain", "strategie": "1 arrêt US-US, HyperSoft qualif"},
            "🇨🇦 Canada - Montréal": {"code": "CAN", "type": "Freinage", "strategie": "1 arrêt US-SS, épingle"},
            "🇦🇿 Azerbaïdjan - Bakou": {"code": "AZE", "type": "Urbain rapide", "strategie": "1 arrêt, SC 80%"},
            "🇦🇹 Autriche - Spielberg": {"code": "AUT", "type": "Court", "strategie": "1 arrêt US-SS, 71 tours"},
            "🇬🇧 GB - Silverstone": {"code": "GBR", "type": "Rapide", "strategie": "2 arrêts, Maggotts-Becketts"},
            "🇭🇺 Hongrie - Hungaroring": {"code": "HUN", "type": "Lent", "strategie": "1 arrêt, dépassement impossible"},
            "🇧🇪 Belgique - Spa": {"code": "BEL", "type": "Légendaire", "strategie": "1-2 arrêts, ERS High"},
            "🇮🇹 Italie - Monza": {"code": "ITA", "type": "Vitesse", "strategie": "1 arrêt US-S, slipstream"},
            "🇸🇬 Singapour - Marina Bay": {"code": "SGP", "type": "Nuit", "strategie": "2 arrêts US-US-SS, 61 tours"},
            "🇲🇾 Malaisie - Sepang": {"code": "MYS", "type": "Chaud", "strategie": "2 arrêts, pluie 60%"},
            "🇯🇵 Japon - Suzuka": {"code": "JPN", "type": "Pilote", "strategie": "2 arrêts, Degner"},
            "🇺🇸 USA - Austin": {"code": "USA", "type": "Moderne", "strategie": "1 arrêt, T1 aveugle"},
            "🇲🇽 Mexique - Mexico": {"code": "MEX", "type": "Altitude", "strategie": "1 arrêt, freinage long"},
            "🇧🇷 Brésil - Interlagos": {"code": "BRA", "type": "Court", "strategie": "2 arrêts, pluie"},
            "🇦🇪 Abu Dhabi - Yas Marina": {"code": "ABU", "type": "Twillight", "strategie": "1 arrêt US-S, hôtel"},
        },
        "strategies": [
            "⚡ ERS 2017: 5 modes - Low/Med/High/Overtake/Hotlap - Hotlap = +0.6s/tour mais batterie vide en 1 tour",
            "⛽ Carburant 2017: 105kg max, Lean = -0.3s mais -15% conso, Rich = +0.3s",
            "🛞 Pneus 2017: HyperSoft/Ultra/Super/Soft/Medium/Hard - Hyper 1.5s plus rapide mais 8 tours",
            "🏁 DRS 2017: 2-3 zones, ouverture 85% efficacité",
            "🔧 Setup 2017 méta: Suspensions plus souples que 2012, aéro médium, diff 75%",
        ],
        "presets": {
            "🔵 2017 Bleu - Equilibré": {"aero_av": 5, "aero_ar": 6, "diff_on": 75, "diff_off": 68, "camber_av": -2.70, "camber_ar": -1.35, "toe_av": 0.09, "toe_ar": 0.28, "susp_av": 5, "susp_ar": 4, "arb_av": 5, "arb_ar": 4, "height_av": 5, "height_ar": 6, "brake_press": 90, "brake_bias": 55, "tyre_av": 22.8, "tyre_ar": 21.0, "ballast": 6},
            "🚀 2017 Monza - Vitesse": {"aero_av": 2, "aero_ar": 2, "diff_on": 80, "diff_off": 72, "camber_av": -2.80, "camber_ar": -1.45, "toe_av": 0.11, "toe_ar": 0.32, "susp_av": 6, "susp_ar": 5, "arb_av": 7, "arb_ar": 6, "height_av": 3, "height_ar": 3, "brake_press": 95, "brake_bias": 57, "tyre_av": 23.8, "tyre_ar": 21.8, "ballast": 5},
            "🔄 2017 Monaco - Appui": {"aero_av": 10, "aero_ar": 11, "diff_on": 65, "diff_off": 60, "camber_av": -2.50, "camber_ar": -1.20, "toe_av": 0.06, "toe_ar": 0.22, "susp_av": 3, "susp_ar": 2, "arb_av": 3, "arb_ar": 2, "height_av": 6, "height_ar": 7, "brake_press": 86, "brake_bias": 53, "tyre_av": 21.8, "tyre_ar": 20.0, "ballast": 8},
        }
    },
    "2020": {
        "color": "violet",
        "hex": "#7C3AED",
        "hex_dark": "#5B21B6",
        "icon": "💜",
        "title": "F1 2020 - Edition Violette",
        "circuits": {
            "🇦🇺 Australie - Melbourne": {"code": "AUS", "type": "Semi-urbain", "strategie": "1 arrêt M-H, ERS Medium, DRS 3 zones"},
            "🇧🇭 Bahreïn - Sakhir": {"code": "BHR", "type": "Traction", "strategie": "2 arrêts M-H-M, S3 traction, ERS High"},
            "🇻🇳 Vietnam - Hanoï": {"code": "VNM", "type": "Urbain", "strategie": "1 arrêt M-H, nouveau 2020, S3 rapide"},
            "🇨🇳 Chine - Shanghai": {"code": "CHN", "type": "Avant limité", "strategie": "2 arrêts, T1-T4 graining"},
            "🇳🇱 Pays-Bas - Zandvoort": {"code": "NLD", "type": "Old-School", "strategie": "1 arrêt, nouveau 2020, banking"},
            "🇪🇸 Espagne - Barcelone": {"code": "ESP", "type": "Complet", "strategie": "2 arrêts M-H-M, T3 usure extrême"},
            "🇲🇨 Monaco - Monte-Carlo": {"code": "MCO", "type": "Urbain Extrême", "strategie": "1 arrêt M-H, qualif 100% course"},
            "🇦🇿 Azerbaïdjan - Bakou": {"code": "AZE", "type": "Urbain Rapide", "strategie": "1 arrêt, SC 70%, slipstream 350km/h"},
            "🇨🇦 Canada - Montréal": {"code": "CAN", "type": "Freinage", "strategie": "1 arrêt M-H, mur champions"},
            "🇫🇷 France - Paul Ricard": {"code": "FRA", "type": "Technique", "strategie": "1 arrêt, Mistral DRS"},
            "🇦🇹 Autriche - Spielberg": {"code": "AUT", "type": "Court", "strategie": "1 arrêt M-H, 71 tours, ERS Overtake T1"},
            "🇬🇧 GB - Silverstone": {"code": "GBR", "type": "Rapide", "strategie": "2 arrêts, C1 dur, Maggotts"},
            "🇭🇺 Hongrie - Hungaroring": {"code": "HUN", "type": "Lent", "strategie": "1 arrêt, pas de dépassement, ERS Low"},
            "🇧🇪 Belgique - Spa": {"code": "BEL", "type": "Légendaire", "strategie": "1-2 arrêts, ERS High, Kemmel DRS"},
            "🇮🇹 Italie - Monza": {"code": "ITA", "type": "Temple Vitesse", "strategie": "1 arrêt M-H, ailerons 1-1, 360km/h"},
            "🇸🇬 Singapour - Marina Bay": {"code": "SGP", "type": "Nuit", "strategie": "2 arrêts, 61 tours, SC 100%"},
            "🇷🇺 Russie - Sotchi": {"code": "RUS", "type": "Lisse", "strategie": "1 arrêt M-H, T3 long"},
            "🇯🇵 Japon - Suzuka": {"code": "JPN", "type": "Pilote", "strategie": "2 arrêts, 130R, S1 rapide"},
            "🇺🇸 USA - Austin": {"code": "USA", "type": "Complet", "strategie": "1 arrêt, T1 aveugle, S1 technique"},
            "🇲🇽 Mexique - Mexico": {"code": "MEX", "type": "Altitude", "strategie": "1 arrêt, 2250m, freinage 25% moins"},
            "🇧🇷 Brésil - Interlagos": {"code": "BRA", "type": "Anti-horaire", "strategie": "2 arrêts, pluie 70%, S2 usure"},
            "🇦🇪 Abu Dhabi - Yas Marina": {"code": "ABU", "type": "Twillight", "strategie": "1 arrêt M-H, S3 technique"},
        },
        "strategies": [
            "⚡ ERS 2020: 5 modes + Auto - Overtake = +0.7s, Hotlap qualif, déploiement auto en course",
            "⛽ Carburant 2020: 110kg, Lean -0.4s / Standard / Rich +0.5s / OverTake - gère avec ERS",
            "🛞 Pneus 2020: C1-C5 (C1 dur, C5 tendre) + Inter/Wet - C5 1.8s plus rapide mais 6 tours, fenêtre 85-105°C",
            "🏁 DRS 2020: 1-3 zones, +12-15 km/h, + ERS Overtake = +25 km/h",
            "🔧 Setup 2020 méta: Aéro 4-6, diff 70-75%, carrossage -2.7/-1.3, toe 0.07/0.22, susp 4/3, hauteur 5/6, ballast 6 - My Team ajoute R&D",
            "🌧️ Pluie 2020: Inter 0-80% eau, Wet 60-100%, hauteur +3, aéro +3, diff -15%, pression -1 PSI",
        ],
        "presets": {
            "💜 2020 Violet - Signature": {"aero_av": 6, "aero_ar": 7, "diff_on": 70, "diff_off": 62, "camber_av": -2.65, "camber_ar": -1.25, "toe_av": 0.07, "toe_ar": 0.22, "susp_av": 4, "susp_ar": 3, "arb_av": 4, "arb_ar": 3, "height_av": 5, "height_ar": 6, "brake_press": 92, "brake_bias": 55, "tyre_av": 23.0, "tyre_ar": 21.0, "ballast": 6},
            "⚡ 2020 Qualif Sec": {"aero_av": 4, "aero_ar": 5, "diff_on": 85, "diff_off": 75, "camber_av": -2.80, "camber_ar": -1.40, "toe_av": 0.10, "toe_ar": 0.30, "susp_av": 5, "susp_ar": 4, "arb_av": 6, "arb_ar": 5, "height_av": 4, "height_ar": 5, "brake_press": 95, "brake_bias": 56, "tyre_av": 23.5, "tyre_ar": 21.5, "ballast": 6},
            "🏁 2020 Course": {"aero_av": 5, "aero_ar": 6, "diff_on": 75, "diff_off": 65, "camber_av": -2.70, "camber_ar": -1.30, "toe_av": 0.08, "toe_ar": 0.25, "susp_av": 4, "susp_ar": 3, "arb_av": 5, "arb_ar": 4, "height_av": 5, "height_ar": 6, "brake_press": 90, "brake_bias": 54, "tyre_av": 22.8, "tyre_ar": 20.8, "ballast": 6},
            "🌧️ 2020 Pluie": {"aero_av": 8, "aero_ar": 9, "diff_on": 55, "diff_off": 50, "camber_av": -2.50, "camber_ar": -1.10, "toe_av": 0.05, "toe_ar": 0.20, "susp_av": 2, "susp_ar": 1, "arb_av": 2, "arb_ar": 1, "height_av": 8, "height_ar": 9, "brake_press": 80, "brake_bias": 52, "tyre_av": 22.0, "tyre_ar": 20.0, "ballast": 7},
            "🚀 2020 Monza Vitesse": {"aero_av": 1, "aero_ar": 1, "diff_on": 80, "diff_off": 70, "camber_av": -2.90, "camber_ar": -1.50, "toe_av": 0.12, "toe_ar": 0.35, "susp_av": 7, "susp_ar": 6, "arb_av": 8, "arb_ar": 7, "height_av": 3, "height_ar": 3, "brake_press": 100, "brake_bias": 58, "tyre_av": 24.5, "tyre_ar": 22.0, "ballast": 5},
            "🔄 2020 Monaco Appui": {"aero_av": 11, "aero_ar": 11, "diff_on": 65, "diff_off": 60, "camber_av": -2.50, "camber_ar": -1.20, "toe_av": 0.05, "toe_ar": 0.20, "susp_av": 3, "susp_ar": 2, "arb_av": 3, "arb_ar": 2, "height_av": 6, "height_ar": 7, "brake_press": 88, "brake_bias": 53, "tyre_av": 22.2, "tyre_ar": 20.2, "ballast": 8},
        }
    }
}

# INIT SESSION
if "f1_year" not in st.session_state:
    st.session_state.f1_year = "2020"
if "f1_setups" not in st.session_state:
    st.session_state.f1_setups = {
        "2012": YEARS["2012"]["presets"]["🔴 2012 Rouge - Equilibré"].copy(),
        "2017": YEARS["2017"]["presets"]["🔵 2017 Bleu - Equilibré"].copy(),
        "2020": YEARS["2020"]["presets"]["💜 2020 Violet - Signature"].copy(),
    }
if "f1_tracks" not in st.session_state:
    st.session_state.f1_tracks = {"2012": "🇮🇹 Italie - Monza", "2017": "🇮🇹 Italie - Monza", "2020": "🇮🇹 Italie - Monza"}

with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:12px 0">
    <div style="font-family:Orbitron;font-size:26px;font-weight:800;background:linear-gradient(90deg,#EF4444,#3B82F6,#7C3AED);-webkit-background-clip:text;-webkit-text-fill-color:transparent">F1 SETUP LAB</div>
    <div style="font-size:11px;letter-spacing:0.3em;font-weight:800;color:#94A3B8">2012 • 2017 • 2020</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("### 📅 Année")
    year = st.radio("Choisis l'année", ["2012 🔴 Rouge", "2017 🔵 Bleu", "2020 💜 Violet"], index=2, key="year_radio")
    year_key = year.split()[0]
    st.session_state.f1_year = year_key
    ydata = YEARS[year_key]

    st.markdown(f"<div class='year-{year_key}'><b>{ydata['icon']} {ydata['title']}</b><br><small>{len(ydata['circuits'])} circuits | {len(ydata['strategies'])} stratégies</small></div>", unsafe_allow_html=True)
    
    st.markdown("### 🏁 Circuit")
    track_list = list(ydata["circuits"].keys())
    cur_track = st.session_state.f1_tracks[year_key]
    if cur_track not in track_list:
        cur_track = track_list[0]
    sel_track = st.selectbox(f"Circuit {year_key}", track_list, index=track_list.index(cur_track), key=f"track_{year_key}")
    st.session_state.f1_tracks[year_key] = sel_track
    tinfo = ydata["circuits"][sel_track]
    st.markdown(f"<div class='card-{year_key}'><span class='badge-{ydata['color']}'>{tinfo['code']}</span> <b>{tinfo['type']}</b><br><small>{tinfo['strategie']}</small></div>", unsafe_allow_html=True)

    st.markdown("### 🎨 Presets")
    preset_list = list(ydata["presets"].keys())
    sel_preset = st.selectbox(f"Preset {year_key}", preset_list, key=f"preset_{year_key}")
    if st.button(f"{ydata['icon']} Appliquer {year_key}", use_container_width=True, key=f"apply_{year_key}"):
        st.session_state.f1_setups[year_key] = ydata["presets"][sel_preset].copy()
        st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Légende couleurs")
    st.markdown('<span class="badge-red">2012 ROUGE</span> KERS / Prime-Option<br><span class="badge-blue">2017 BLEU</span> ERS / HyperSoft<br><span class="badge-violet">2020 VIOLET</span> ERS Auto / C1-C5', unsafe_allow_html=True)

# MAIN
ykey = st.session_state.f1_year
ydata = YEARS[ykey]
setup = st.session_state.f1_setups[ykey]
track = st.session_state.f1_tracks[ykey]
tinfo = ydata["circuits"][track]

st.markdown(f"<div class='year-{ykey}'><div style='display:flex;align-items:center;gap:12px'><div style='font-size:32px'>{ydata['icon']}</div><div><div style='font-family:Orbitron;font-size:24px;font-weight:800'>{ydata['title']}</div><div style='font-size:12px;opacity:0.9'>{track} [{tinfo['code']}] • {tinfo['type']}</div></div><div style='margin-left:auto'><span class='badge-{ydata['color']}'>{ykey} • {len(ydata['circuits'])} GP</span></div></div></div>", unsafe_allow_html=True)

col_strat, col_setup = st.columns([1, 1.8])

with col_strat:
    st.markdown(f"<div class='card-{ykey}'><h4 style='margin:0 0 8px'>🧠 Stratégies {ykey} adaptées</h4></div>", unsafe_allow_html=True)
    for s in ydata["strategies"]:
        st.markdown(f"<div class='card-{ykey}' style='padding:10px;font-size:13px'>{s}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='card-{ykey}'><b>Stratégie pour {track}:</b><br>{tinfo['strategie']}</div>", unsafe_allow_html=True)

with col_setup:
    tab_aero, tab_trans, tab_geo, tab_susp, tab_frein, tab_pneu, tab_resume = st.tabs(["🌀 Aéro", "⚙️ Trans", "📐 Géo", "🔧 Susp", "🛑 Freins", "🛞 Pneus", "📋 Résumé"])
    with tab_aero:
        c1,c2=st.columns(2)
        with c1: setup["aero_av"]=st.slider(f"Aileron Avant {ykey}",1,11,setup["aero_av"],key=f"aero_av_{ykey}")
        with c2: setup["aero_ar"]=st.slider(f"Aileron Arrière {ykey}",1,11,setup["aero_ar"],key=f"aero_ar_{ykey}")
        st.caption(f"Balance {setup['aero_av']-setup['aero_ar']:+d} = {'Sur-vireur' if setup['aero_av']-setup['aero_ar']<-2 else 'Sous-vireur' if setup['aero_av']-setup['aero_ar']>2 else 'Neutre'}")
    with tab_trans:
        c1,c2=st.columns(2)
        with c1: setup["diff_on"]=st.slider("Diff On %",50,100,setup["diff_on"],key=f"don_{ykey}")
        with c2: setup["diff_off"]=st.slider("Diff Off %",50,100,setup["diff_off"],key=f"doff_{ykey}")
    with tab_geo:
        c1,c2=st.columns(2)
        with c1:
            setup["camber_av"]=st.slider("Carrossage AV",-3.5,-2.0,setup["camber_av"],step=0.05,key=f"cam_av_{ykey}")
            setup["camber_ar"]=st.slider("Carrossage AR",-2.0,-1.0,setup["camber_ar"],step=0.05,key=f"cam_ar_{ykey}")
        with c2:
            setup["toe_av"]=st.slider("Pincement AV",0.05,0.15,setup["toe_av"],step=0.01,key=f"toe_av_{ykey}")
            setup["toe_ar"]=st.slider("Pincement AR",0.20,0.50,setup["toe_ar"],step=0.01,key=f"toe_ar_{ykey}")
    with tab_susp:
        c1,c2,c3=st.columns(3)
        with c1:
            setup["susp_av"]=st.slider("Susp AV",1,11,setup["susp_av"],key=f"sav_{ykey}")
            setup["susp_ar"]=st.slider("Susp AR",1,11,setup["susp_ar"],key=f"sar_{ykey}")
        with c2:
            setup["arb_av"]=st.slider("ARB AV",1,11,setup["arb_av"],key=f"aav_{ykey}")
            setup["arb_ar"]=st.slider("ARB AR",1,11,setup["arb_ar"],key=f"aar_{ykey}")
        with c3:
            setup["height_av"]=st.slider("Hauteur AV",1,11,setup["height_av"],key=f"hav_{ykey}")
            setup["height_ar"]=st.slider("Hauteur AR",1,11,setup["height_ar"],key=f"har_{ykey}")
    with tab_frein:
        c1,c2=st.columns(2)
        with c1: setup["brake_press"]=st.slider("Pression %",70,100,setup["brake_press"],key=f"bp_{ykey}")
        with c2: setup["brake_bias"]=st.slider("Bias AV %",50,70,setup["brake_bias"],key=f"bb_{ykey}")
    with tab_pneu:
        c1,c2=st.columns(2)
        with c1: setup["tyre_av"]=st.slider("Pression AV PSI",21.0,25.0,setup["tyre_av"],step=0.1,key=f"tav_{ykey}")
        with c2: setup["tyre_ar"]=st.slider("Pression AR PSI",19.5,23.5,setup["tyre_ar"],step=0.1,key=f"tar_{ykey}")
        setup["ballast"]=st.slider("Ballast 1-11",1,11,setup["ballast"],key=f"bal_{ykey}")
    with tab_resume:
        st.code(f"""F1 {ykey} {ydata['icon']} SETUP - {track} [{tinfo['code']}]
Aero AV:{setup['aero_av']} AR:{setup['aero_ar']} Bal:{setup['aero_av']-setup['aero_ar']:+d}
Diff ON:{setup['diff_on']}% OFF:{setup['diff_off']}%
Camber AV:{setup['camber_av']} AR:{setup['camber_ar']} Toe AV:{setup['toe_av']} AR:{setup['toe_ar']}
Susp AV:{setup['susp_av']} AR:{setup['susp_ar']} ARB AV:{setup['arb_av']} AR:{setup['arb_ar']} H AV:{setup['height_av']} AR:{setup['height_ar']}
Brake {setup['brake_press']}% Bias {setup['brake_bias']}%
Tyre AV:{setup['tyre_av']} AR:{setup['tyre_ar']} Ballast:{setup['ballast']}
Vmax Est: {340-(setup['aero_av']+setup['aero_ar'])*4} km/h
Strat: {tinfo['strategie']}
""", language="yaml")
        export = {"jeu": f"F1 {ykey}", "edition": ydata["color"], "circuit": track, "code": tinfo["code"], "setup": setup, "strategie": tinfo["strategie"], "date": datetime.datetime.now().isoformat()}
        st.download_button(f"💾 Télécharger JSON {ykey} {ydata['icon']}", data=json.dumps(export, indent=2, ensure_ascii=False), file_name=f"F1_{ykey}_{tinfo['code']}_{ydata['color']}.json", mime="application/json", use_container_width=True)

st.markdown("---")
st.markdown("""
<div style="text-align:center;padding:12px;background:linear-gradient(90deg,rgba(185,28,28,0.2),rgba(37,99,235,0.2),rgba(124,58,237,0.2));border-radius:12px;border:1px solid rgba(255,255,255,0.1)">
<span style="font-family:Orbitron;font-weight:800;letter-spacing:0.15em;background:linear-gradient(90deg,#EF4444,#3B82F6,#A78BFA);-webkit-background-clip:text;-webkit-text-fill-color:transparent">2012 ROUGE • 2017 BLEU • 2020 VIOLET • PACK COMPLET</span><br>
<span style="font-size:11px;color:#94A3B8">20 circuits 2012 • 20 circuits 2017 • 22 circuits 2020 • Stratégies KERS/ERS/C1-C5 adaptées</span>
</div>
""", unsafe_allow_html=True)
