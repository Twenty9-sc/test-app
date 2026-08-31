# -*- coding: utf-8 -*-
"""
F1 2020 - Setup Manager | Edition Violet
App dédiée F1 2020 avec tous les paramètres adaptés, thème violet intégral
"""

import streamlit as st
import json
import datetime

st.set_page_config(
    page_title="F1 2020 - Setup Violet",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# THEME VIOLET - CSS GLOBAL
# ==============================================================================
VIOLET_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800&family=Inter:wght@400;600;800&display=swap');

:root {
    --violet-primary: #7C3AED;
    --violet-dark: #5B21B6;
    --violet-light: #A78BFA;
    --violet-ultra-light: #EDE9FE;
    --violet-bg: #0F0A1E;
    --violet-card: #1E1640;
    --violet-border: #6D28D9;
}

[data-testid="stAppViewContainer"] {
    background: radial-gradient(1200px 600px at 20% -10%, rgba(124,58,237,0.25), transparent),
                radial-gradient(900px 500px at 90% 0%, rgba(139,92,246,0.20), transparent),
                linear-gradient(180deg, #0F0A1E 0%, #15102A 35%, #1A1540 100%);
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #140E2F 0%, #1E1650 100%);
    border-right: 2px solid #6D28D9;
}

[data-testid="stSidebar"] * {
    color: #EDE9FE !important;
}

h1, h2, h3 {
    font-family: 'Orbitron', sans-serif !important;
    color: #EDE9FE !important;
    letter-spacing: 0.02em;
}

h1 {
    background: linear-gradient(90deg, #A78BFA, #7C3AED, #C4B5FD);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 2.6rem !important;
    font-weight: 800 !important;
}

.stSlider > div > div > div > div {
    background: #7C3AED !important;
}

div[data-baseweb="slider"] > div > div {
    background: linear-gradient(90deg, #5B21B6, #7C3AED, #A78BFA) !important;
}

.stButton > button {
    background: linear-gradient(135deg, #6D28D9 0%, #7C3AED 50%, #8B5CF6 100%) !important;
    color: white !important;
    border: 1px solid #A78BFA !important;
    border-radius: 12px !important;
    font-weight: 800 !important;
    font-family: 'Inter', sans-serif !important;
    box-shadow: 0 6px 20px rgba(124,58,237,0.4) !important;
    transition: all 0.2s ease !important;
}

.stButton > button:hover {
    transform: translateY(-2px) scale(1.02);
    box-shadow: 0 10px 28px rgba(124,58,237,0.6) !important;
    border-color: #C4B5FD !important;
}

.violet-card {
    background: linear-gradient(135deg, rgba(30,22,64,0.95), rgba(46,32,96,0.9));
    border: 1px solid rgba(139,92,246,0.35);
    border-left: 4px solid #7C3AED;
    border-radius: 16px;
    padding: 18px 20px;
    margin: 12px 0;
    box-shadow: 0 8px 24px rgba(0,0,0,0.35), inset 0 1px 0 rgba(167,139,250,0.15);
}

.violet-metric {
    background: linear-gradient(135deg, #1E1650, #2A1F6B);
    border: 1px solid #6D28D9;
    border-radius: 12px;
    padding: 14px;
    text-align: center;
}

.violet-badge {
    display: inline-block;
    background: linear-gradient(90deg, #7C3AED, #8B5CF6);
    color: white;
    padding: 4px 12px;
    border-radius: 999px;
    font-weight: 800;
    font-size: 11px;
    letter-spacing: 0.08em;
}

.violet-track {
    background: rgba(124,58,237,0.12);
    border: 1px solid rgba(124,58,237,0.35);
    border-radius: 10px;
    padding: 10px 14px;
    margin: 4px 0;
}

hr {
    border-color: rgba(124,58,237,0.25) !important;
}

[data-testid="stTabs"] button[aria-selected="true"] {
    background: linear-gradient(90deg, #6D28D9, #7C3AED) !important;
    color: white !important;
    border-radius: 10px 10px 0 0 !important;
}

[data-testid="stMetric"] {
    background: rgba(30,22,64,0.7);
    border: 1px solid rgba(124,58,237,0.25);
    border-radius: 12px;
    padding: 12px;
}
</style>
"""
st.markdown(VIOLET_CSS, unsafe_allow_html=True)

# ==============================================================================
# DATA - F1 2020
# ==============================================================================

TRACKS_F1_2020 = {
    "🇦🇺 Australie - Melbourne": {"type": "Semi-urbain", "downforce": "Moyen-Élevé", "usure": "Moyen", "traction": "Élevée", "vitesse": "Moyenne", "code": "AUS"},
    "🇧🇭 Bahreïn - Sakhir": {"type": "Traction", "downforce": "Faible-Moyen", "usure": "Élevée", "traction": "Très Élevée", "vitesse": "Élevée", "code": "BHR"},
    "🇻🇳 Vietnam - Hanoï": {"type": "Urbain", "downforce": "Moyen", "usure": "Faible", "traction": "Moyenne", "vitesse": "Très Élevée", "code": "VNM"},
    "🇨🇳 Chine - Shanghai": {"type": "Technique", "downforce": "Moyen-Élevé", "usure": "Élevée", "traction": "Moyenne", "vitesse": "Élevée", "code": "CHN"},
    "🇳🇱 Pays-Bas - Zandvoort": {"type": "Old-School", "downforce": "Élevé", "usure": "Moyenne", "traction": "Élevée", "vitesse": "Moyenne", "code": "NLD"},
    "🇪🇸 Espagne - Barcelone": {"type": "Complet", "downforce": "Élevé", "usure": "Très Élevée", "traction": "Moyenne", "vitesse": "Moyenne", "code": "ESP"},
    "🇲🇨 Monaco - Monte-Carlo": {"type": "Urbain Extrême", "downforce": "Très Élevé", "usure": "Faible", "traction": "Faible", "vitesse": "Très Faible", "code": "MCO"},
    "🇦🇿 Azerbaïdjan - Bakou": {"type": "Urbain Rapide", "downforce": "Très Faible", "usure": "Faible", "traction": "Moyenne", "vitesse": "Extrême", "code": "AZE"},
    "🇨🇦 Canada - Montréal": {"type": "Semi-urbain", "downforce": "Faible", "usure": "Moyenne", "traction": "Élevée", "vitesse": "Élevée", "code": "CAN"},
    "🇫🇷 France - Paul Ricard": {"type": "Technique", "downforce": "Moyen", "usure": "Élevée", "traction": "Moyenne", "vitesse": "Élevée", "code": "FRA"},
    "🇦🇹 Autriche - Spielberg": {"type": "Rapide", "downforce": "Moyen", "usure": "Moyenne", "traction": "Élevée", "vitesse": "Élevée", "code": "AUT"},
    "🇬🇧 Grande-Bretagne - Silverstone": {"type": "Rapide", "downforce": "Élevé", "usure": "Très Élevée", "traction": "Moyenne", "vitesse": "Très Élevée", "code": "GBR"},
    "🇭🇺 Hongrie - Hungaroring": {"type": "Technique", "downforce": "Très Élevé", "usure": "Faible", "traction": "Faible", "vitesse": "Faible", "code": "HUN"},
    "🇧🇪 Belgique - Spa": {"type": "Légendaire", "downforce": "Faible-Moyen", "usure": "Élevée", "traction": "Moyenne", "vitesse": "Extrême", "code": "BEL"},
    "🇮🇹 Italie - Monza": {"type": "Temple Vitesse", "downforce": "Minimal", "usure": "Faible", "traction": "Moyenne", "vitesse": "Extrême Max", "code": "ITA"},
    "🇸🇬 Singapour - Marina Bay": {"type": "Urbain Nuit", "downforce": "Très Élevé", "usure": "Moyenne", "traction": "Élevée", "vitesse": "Faible", "code": "SGP"},
    "🇷🇺 Russie - Sotchi": {"type": "Semi-urbain", "downforce": "Moyen", "usure": "Faible", "traction": "Moyenne", "vitesse": "Moyenne", "code": "RUS"},
    "🇯🇵 Japon - Suzuka": {"type": "Pilote", "downforce": "Élevé", "usure": "Élevée", "traction": "Moyenne", "vitesse": "Élevée", "code": "JPN"},
    "🇺🇸 USA - Austin": {"type": "Complet", "downforce": "Moyen-Élevé", "usure": "Élevée", "traction": "Élevée", "vitesse": "Moyenne", "code": "USA"},
    "🇲🇽 Mexique - Mexico": {"type": "Altitude", "downforce": "Très Élevé", "usure": "Moyenne", "traction": "Élevée", "vitesse": "Élevée", "code": "MEX"},
    "🇧🇷 Brésil - Interlagos": {"type": "Anti-horaire", "downforce": "Élevé", "usure": "Élevée", "traction": "Élevée", "vitesse": "Moyenne", "code": "BRA"},
    "🇦🇪 Abu Dhabi - Yas Marina": {"type": "Twillight", "downforce": "Moyen", "usure": "Moyenne", "traction": "Élevée", "vitesse": "Moyenne", "code": "ABU"},
}

PRESETS_F1_2020 = {
    "⚡ Qualif Sec - Attaque": {
        "aero_av": 4, "aero_ar": 5,
        "diff_on": 85, "diff_off": 75,
        "camber_av": -2.80, "camber_ar": -1.40, "toe_av": 0.10, "toe_ar": 0.30,
        "susp_av": 5, "susp_ar": 4, "arb_av": 6, "arb_ar": 5, "height_av": 4, "height_ar": 5,
        "brake_press": 95, "brake_bias": 56,
        "tyre_av": 23.5, "tyre_ar": 21.5,
        "ballast": 6,
        "desc": "Setup agressif qualif, rotation max, pneus surchauffés rapidement"
    },
    "🏁 Course Sec - Equilibré": {
        "aero_av": 5, "aero_ar": 6,
        "diff_on": 75, "diff_off": 65,
        "camber_av": -2.70, "camber_ar": -1.30, "toe_av": 0.08, "toe_ar": 0.25,
        "susp_av": 4, "susp_ar": 3, "arb_av": 5, "arb_ar": 4, "height_av": 5, "height_ar": 6,
        "brake_press": 90, "brake_bias": 54,
        "tyre_av": 22.8, "tyre_ar": 20.8,
        "ballast": 6,
        "desc": "Le plus polyvalent F1 2020, préserve pneus, stable"
    },
    "🌧️ Pluie - Full Wet": {
        "aero_av": 8, "aero_ar": 9,
        "diff_on": 55, "diff_off": 50,
        "camber_av": -2.50, "camber_ar": -1.10, "toe_av": 0.05, "toe_ar": 0.20,
        "susp_av": 2, "susp_ar": 1, "arb_av": 2, "arb_ar": 1, "height_av": 8, "height_ar": 9,
        "brake_press": 80, "brake_bias": 52,
        "tyre_av": 22.0, "tyre_ar": 20.0,
        "ballast": 7,
        "desc": "Max appui, suspensions soft, hauteur max anti-aquaplaning"
    },
    "🚀 Monza / Bakou - Vitesse Max": {
        "aero_av": 1, "aero_ar": 1,
        "diff_on": 80, "diff_off": 70,
        "camber_av": -2.90, "camber_ar": -1.50, "toe_av": 0.12, "toe_ar": 0.35,
        "susp_av": 7, "susp_ar": 6, "arb_av": 8, "arb_ar": 7, "height_av": 3, "height_ar": 3,
        "brake_press": 100, "brake_bias": 58,
        "tyre_av": 24.5, "tyre_ar": 22.0,
        "ballast": 5,
        "desc": "Ailerons mini, traînée mini, 350+ km/h"
    },
    "🔄 Monaco / Hongrie - Appui Max": {
        "aero_av": 11, "aero_ar": 11,
        "diff_on": 65, "diff_off": 60,
        "camber_av": -2.50, "camber_ar": -1.20, "toe_av": 0.05, "toe_ar": 0.20,
        "susp_av": 3, "susp_ar": 2, "arb_av": 3, "arb_ar": 2, "height_av": 6, "height_ar": 7,
        "brake_press": 88, "brake_bias": 53,
        "tyre_av": 22.2, "tyre_ar": 20.2,
        "ballast": 8,
        "desc": "Grip mécanique max, rotation lente, traction urbaine"
    },
    "💜 Violet - Setup Signature": {
        "aero_av": 6, "aero_ar": 7,
        "diff_on": 70, "diff_off": 62,
        "camber_av": -2.65, "camber_ar": -1.25, "toe_av": 0.07, "toe_ar": 0.22,
        "susp_av": 4, "susp_ar": 3, "arb_av": 4, "arb_ar": 3, "height_av": 5, "height_ar": 6,
        "brake_press": 92, "brake_bias": 55,
        "tyre_av": 23.0, "tyre_ar": 21.0,
        "ballast": 6,
        "desc": "Setup signature violet, compromis idéal F1 2020 - créé pour toi"
    },
}

# Session State init
if "f1_setup" not in st.session_state:
    st.session_state.f1_setup = PRESETS_F1_2020["💜 Violet - Setup Signature"].copy()
if "f1_track" not in st.session_state:
    st.session_state.f1_track = "🇮🇹 Italie - Monza"
if "f1_preset" not in st.session_state:
    st.session_state.f1_preset = "💜 Violet - Setup Signature"
if "f1_saved" not in st.session_state:
    st.session_state.f1_saved = []

def apply_preset(name):
    if name in PRESETS_F1_2020:
        st.session_state.f1_setup = PRESETS_F1_2020[name].copy()
        st.session_state.f1_preset = name

def get_balance():
    s = st.session_state.f1_setup
    aero_balance = s["aero_av"] - s["aero_ar"]
    if aero_balance < -2:
        return "Sur-vireur (arrière fuyant)", "#F59E0B"
    elif aero_balance > 2:
        return "Sous-vireur (avant qui pousse)", "#3B82F6"
    else:
        return "Neutre / Équilibré", "#7C3AED"

def get_tyre_wear_risk():
    s = st.session_state.f1_setup
    score = 0
    score += max(0, (abs(s["camber_av"]) - 2.5) * 10)
    score += max(0, (abs(s["camber_ar"]) - 1.2) * 10)
    score += max(0, (s["toe_av"] - 0.08) * 100)
    score += max(0, (s["susp_av"] - 6) * 2)
    if score < 5:
        return "Faible usure", "#10B981"
    elif score < 15:
        return "Moyenne usure", "#F59E0B"
    else:
        return "Usure élevée", "#EF4444"

# ==============================================================================
# SIDEBAR - VIOLET
# ==============================================================================
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:18px 0 8px 0;">
        <div style="font-family:Orbitron; font-size:28px; font-weight:800; background:linear-gradient(90deg,#C4B5FD,#7C3AED); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">F1 2020</div>
        <div style="font-size:12px; letter-spacing:0.35em; color:#A78BFA; font-weight:800; margin-top:4px;">VIOLET EDITION</div>
        <div style="margin-top:12px; width:100%; height:3px; background:linear-gradient(90deg,#5B21B6,#7C3AED,#A78BFA); border-radius:999px;"></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🏁 Circuit")
    track = st.selectbox("Choisis ton GP", list(TRACKS_F1_2020.keys()), index=list(TRACKS_F1_2020.keys()).index(st.session_state.f1_track) if st.session_state.f1_track in TRACKS_F1_2020 else 14, key="sel_track")
    st.session_state.f1_track = track
    info = TRACKS_F1_2020[track]
    st.markdown(f"""
    <div class="violet-track">
        <span class="violet-badge">{info['code']}</span><br>
        <b style="color:#C4B5FD;">Type:</b> {info['type']}<br>
        <b style="color:#C4B5FD;">Appui:</b> {info['downforce']}<br>
        <b style="color:#C4B5FD;">Usure:</b> {info['usure']}<br>
        <b style="color:#C4B5FD;">Traction:</b> {info['traction']}<br>
        <b style="color:#C4B5FD;">Vitesse:</b> {info['vitesse']}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🎨 Presets F1 2020")
    preset = st.selectbox("Setup de base", list(PRESETS_F1_2020.keys()), index=list(PRESETS_F1_2020.keys()).index(st.session_state.f1_preset) if st.session_state.f1_preset in PRESETS_F1_2020 else 5, key="sel_preset")
    if st.button("💜 Appliquer ce preset", use_container_width=True):
        apply_preset(preset)
        st.rerun()

    st.caption(PRESETS_F1_2020[preset]["desc"])

    st.markdown("---")
    st.markdown("### 💾 Mes Setups")
    setup_name = st.text_input("Nom du setup", placeholder=f"{info['code']}_Violet_{datetime.datetime.now().strftime('%d%m')}")
    if st.button("💾 Sauvegarder setup actuel", use_container_width=True):
        if setup_name.strip():
            entry = {
                "nom": setup_name.strip(),
                "track": track,
                "date": datetime.datetime.now().strftime("%d/%m %H:%M"),
                "setup": st.session_state.f1_setup.copy()
            }
            st.session_state.f1_saved.append(entry)
            st.success(f"Setup '{setup_name}' sauvegardé!")
    
    if st.session_state.f1_saved:
        st.markdown(f"**{len(st.session_state.f1_saved)} setups sauvegardés**")
        for i, sv in enumerate(reversed(st.session_state.f1_saved[-5:])):
            with st.expander(f"💜 {sv['nom']} - {sv['track'][:12]}"):
                st.json(sv["setup"])
                if st.button(f"Charger", key=f"load_{i}"):
                    st.session_state.f1_setup = sv["setup"].copy()
                    st.session_state.f1_track = sv["track"]
                    st.rerun()

# ==============================================================================
# MAIN - HEADER
# ==============================================================================
col_title, col_stats = st.columns([2.2, 1])

with col_title:
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:16px; margin-bottom:6px;">
        <div style="font-size:42px;">🏎️</div>
        <div>
            <h1 style="margin:0; line-height:1.1;">F1 2020 SETUP LAB</h1>
            <div style="color:#A78BFA; font-family:Inter; font-weight:800; letter-spacing:0.18em; font-size:13px; margin-top:2px;">EDITION VIOLETTE • TOUS PARAMÈTRES ADAPTÉS • CODÉ POUR TOI</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"<div class='violet-card'> <span class='violet-badge'>CIRCUIT ACTIF</span> <b style='font-size:18px; margin-left:10px; color:#EDE9FE;'>{track}</b> — <span style='color:#A78BFA;'>{info['type']} | Appui {info['downforce']} | {info['code']}</span> </div>", unsafe_allow_html=True)

with col_stats:
    balance_text, balance_color = get_balance()
    wear_text, wear_color = get_tyre_wear_risk()
    s = st.session_state.f1_setup
    st.markdown(f"""
    <div class="violet-card" style="text-align:center;">
        <div style="font-size:11px; letter-spacing:0.2em; color:#A78BFA; font-weight:800;">BALANCE AÉRO</div>
        <div style="font-size:16px; font-weight:800; color:{balance_color}; margin:4px 0;">{balance_text}</div>
        <div style="height:2px; background:linear-gradient(90deg,{balance_color},transparent); margin:8px 0;"></div>
        <div style="font-size:11px; letter-spacing:0.2em; color:#A78BFA; font-weight:800;">USURE PNEUS</div>
        <div style="font-size:15px; font-weight:800; color:{wear_color};">{wear_text}</div>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# TABS - TOUS LES PARAMETRES F1 2020
# ==============================================================================
tab_aero, tab_trans, tab_geo, tab_susp, tab_brake, tab_tyre, tab_ballast, tab_resume = st.tabs([
    "🌀 AÉRODYNAMIQUE", "⚙️ TRANSMISSION", "📐 GÉOMÉTRIE", "🔧 SUSPENSION", "🛑 FREINS", "🛞 PNEUS", "⚖️ LEST", "📋 RÉSUMÉ VIOLET"
])

s = st.session_state.f1_setup

with tab_aero:
    st.markdown("#### 🌀 Aérodynamique - F1 2020 (1 = Vitesse, 11 = Appui Max)")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="violet-card">', unsafe_allow_html=True)
        st.markdown("**Aileron Avant**")
        s["aero_av"] = st.slider("Aileron Avant", 1, 11, s["aero_av"], key="aero_av", help="1 = vitesse max Monza, 11 = appui max Monaco. Affecte sous-virage et usure avant.")
        st.markdown(f"<div class='violet-metric'>Valeur: <b style='color:#A78BFA; font-size:22px;'>{s['aero_av']}</b> / 11<br><small>{'⬇️ Vitesse' if s['aero_av']<4 else '⚖️ Équilibré' if s['aero_av']<8 else '⬆️ Appui Max'}</small></div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="violet-card">', unsafe_allow_html=True)
        st.markdown("**Aileron Arrière**")
        s["aero_ar"] = st.slider("Aileron Arrière", 1, 11, s["aero_ar"], key="aero_ar", help="Gère traction et stabilité haute vitesse. Plus élevé = plus stable mais moins de Vmax.")
        st.markdown(f"<div class='violet-metric'>Valeur: <b style='color:#A78BFA; font-size:22px;'>{s['aero_ar']}</b> / 11<br><small>{'⬇️ Vitesse' if s['aero_ar']<4 else '⚖️ Équilibré' if s['aero_ar']<8 else '⬆️ Appui Max'}</small></div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.info(f"💜 Conseil Violet pour {track}: {info['downforce']} recommandé. Actuel: AV {s['aero_av']} / AR {s['aero_ar']} = Diff {s['aero_av']-s['aero_ar']:+d}")

with tab_trans:
    st.markdown("#### ⚙️ Transmission - Différentiel F1 2020")
    st.markdown('<div class="violet-card">Le différentiel F1 2020 contrôle comment la puissance est répartie. Plus ouvert = plus de rotation mais plus de patinage.</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        s["diff_on"] = st.slider("Différentiel Accélération (On-Throttle)", 50, 100, s["diff_on"], key="diff_on", help="50% = très ouvert, rotation max mais traction faible. 100% = verrouillé, traction max mais sous-vireur à l'accélération.")
        st.progress((s["diff_on"]-50)/50)
        if s["diff_on"] < 65:
            st.warning("🔓 Ouvert: Risque patinage sur traction")
        elif s["diff_on"] > 85:
            st.success("🔒 Fermé: Traction max")
    with col2:
        s["diff_off"] = st.slider("Différentiel Décélération (Off-Throttle)", 50, 100, s["diff_off"], key="diff_off", help="Gère stabilité au freinage et entrée virage. Bas = plus de rotation au freinage, haut = plus stable.")
        st.progress((s["diff_off"]-50)/50)
    st.caption("💜 Setup Violet: 70% ON / 62% OFF = compromis idéal pour rotation sans perdre traction")

with tab_geo:
    st.markdown("#### 📐 Géométrie Suspension - F1 2020")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="violet-card">', unsafe_allow_html=True)
        st.markdown("**Carrossage (Camber)**")
        s["camber_av"] = st.slider("Carrossage Avant", -3.5, -2.5, s["camber_av"], step=0.05, key="camber_av", help="Plus négatif = plus de grip en virage mais usure intérieure + surchauffe. F1 2020 méta: -2.70 à -2.80")
        s["camber_ar"] = st.slider("Carrossage Arrière", -2.0, -1.0, s["camber_ar"], step=0.05, key="camber_ar", help="F1 2020 méta: -1.20 à -1.50 pour traction")
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="violet-card">', unsafe_allow_html=True)
        st.markdown("**Pincement (Toe)**")
        s["toe_av"] = st.slider("Pincement Avant", 0.05, 0.15, s["toe_av"], step=0.01, key="toe_av", help="Plus élevé = meilleure réponse direction mais usure et instabilité ligne droite. Méta 0.05-0.10")
        s["toe_ar"] = st.slider("Pincement Arrière", 0.20, 0.50, s["toe_ar"], step=0.01, key="toe_ar", help="Stabilise arrière. Méta 0.20-0.35")
        st.markdown('</div>', unsafe_allow_html=True)

with tab_susp:
    st.markdown("#### 🔧 Suspension & Barre Anti-Roulis - F1 2020")
    st.markdown("1 = Souple (confort, grip mécanique, pluie) | 11 = Rigide (réactif, qualif sec)")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="violet-card">', unsafe_allow_html=True)
        s["susp_av"] = st.slider("Suspension Avant", 1, 11, s["susp_av"], key="susp_av")
        s["susp_ar"] = st.slider("Suspension Arrière", 1, 11, s["susp_ar"], key="susp_ar")
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="violet-card">', unsafe_allow_html=True)
        s["arb_av"] = st.slider("Barre Anti-Roulis Avant", 1, 11, s["arb_av"], key="arb_av", help="Gère roulis et sous/sur-virage. AV dur = plus de sous-virage")
        s["arb_ar"] = st.slider("Barre Anti-Roulis Arrière", 1, 11, s["arb_ar"], key="arb_ar")
        st.markdown('</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="violet-card">', unsafe_allow_html=True)
        s["height_av"] = st.slider("Hauteur Caisse Avant", 1, 11, s["height_av"], key="height_av", help="Bas = aéro efficace mais risque fond plat sur vibreurs. Pluie = haut.")
        s["height_ar"] = st.slider("Hauteur Caisse Arrière", 1, 11, s["height_ar"], key="height_ar")
        st.markdown('</div>', unsafe_allow_html=True)

with tab_brake:
    st.markdown("#### 🛑 Freins - F1 2020")
    col1, col2 = st.columns(2)
    with col1:
        s["brake_press"] = st.slider("Pression Freins", 70, 100, s["brake_press"], key="brake_press", help="100% = puissance max mais blocage facile sans ABS. Méta 90-95%")
        st.markdown(f"<div class='violet-metric'>Pression: <b>{s['brake_press']}%</b></div>", unsafe_allow_html=True)
    with col2:
        s["brake_bias"] = st.slider("Répartition Freinage Avant", 50, 70, s["brake_bias"], key="brake_bias", help="50% = équilibré, >56% = avant bloque d'abord (plus sûr), <54% = arrière instable")
        st.markdown(f"<div class='violet-metric'>Bias Avant: <b>{s['brake_bias']}%</b> | Arrière: {100-s['brake_bias']}%</div>", unsafe_allow_html=True)
    if s["brake_bias"] > 58:
        st.warning("Bias très avant - sous-vireur au freinage")
    elif s["brake_bias"] < 53:
        st.error("Bias arrière - risque tête-à-queue au freinage!")

with tab_tyre:
    st.markdown("#### 🛞 Pression Pneus - F1 2020 (PSI)")
    st.caption("Basse pression = plus de grip mais surchauffe et usure. Haute pression = moins de grip mais Vmax + réactivité. F1 2020 méta: AV 22.5-23.5, AR 20.5-21.5")
    col1, col2 = st.columns(2)
    with col1:
        s["tyre_av"] = st.slider("Pression Pneus Avant", 21.0, 25.0, s["tyre_av"], step=0.1, key="tyre_av")
        st.markdown(f"<div class='violet-metric' style='border-color:#A78BFA;'>AV: <b style='color:#C4B5FD; font-size:20px;'>{s['tyre_av']} PSI</b></div>", unsafe_allow_html=True)
    with col2:
        s["tyre_ar"] = st.slider("Pression Pneus Arrière", 19.5, 23.5, s["tyre_ar"], step=0.1, key="tyre_ar")
        st.markdown(f"<div class='violet-metric' style='border-color:#7C3AED;'>AR: <b style='color:#A78BFA; font-size:20px;'>{s['tyre_ar']} PSI</b></div>", unsafe_allow_html=True)

with tab_ballast:
    st.markdown("#### ⚖️ Répartition Poids / Lest - F1 2020")
    st.markdown('<div class="violet-card">Le lest déplace le centre de gravité. 1 = vers avant (sous-vireur, stable), 11 = vers arrière (sur-vireur, traction arrière). F1 2020 méta: 5-7</div>', unsafe_allow_html=True)
    s["ballast"] = st.slider("Lest (Ballast)", 1, 11, s["ballast"], key="ballast")
    col1, col2, col3 = st.columns(3)
    col1.metric("Position", f"{s['ballast']}/11", f"{'AVANT' if s['ballast']<5 else 'ARRIÈRE' if s['ballast']>7 else 'CENTRE'}")
    col2.metric("Tendance", "Sous-vireur" if s["ballast"]<4 else "Sur-vireur" if s["ballast"]>8 else "Neutre")
    col3.metric("Recommandé Violet", "6", "Signature")

with tab_resume:
    st.markdown(f"### 💜 Résumé Setup Violet - {track}")
    
    col_a, col_b = st.columns([1.3, 1])
    with col_a:
        st.markdown('<div class="violet-card">', unsafe_allow_html=True)
        st.markdown("#### 📋 Tous les paramètres F1 2020")
        st.code(f"""
# F1 2020 SETUP VIOLET - {track} - {info['code']}
# Généré: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')} | Preset: {st.session_state.f1_preset}

AERODYNAMIQUE
  Aileron Avant: {s['aero_av']}
  Aileron Arrière: {s['aero_ar']}

TRANSMISSION
  Diff On-Throttle: {s['diff_on']}%
  Diff Off-Throttle: {s['diff_off']}%

GEOMETRIE SUSPENSION
  Carrossage Avant: {s['camber_av']}°
  Carrossage Arrière: {s['camber_ar']}°
  Pincement Avant: {s['toe_av']}°
  Pincement Arrière: {s['toe_ar']}°

SUSPENSION
  Suspension Avant: {s['susp_av']}
  Suspension Arrière: {s['susp_ar']}
  Barre Anti-Roulis Avant: {s['arb_av']}
  Barre Anti-Roulis Arrière: {s['arb_ar']}
  Hauteur Avant: {s['height_av']}
  Hauteur Arrière: {s['height_ar']}

FREINS
  Pression: {s['brake_press']}%
  Répartition Avant: {s['brake_bias']}%

PNEUS
  Pression Avant: {s['tyre_av']} PSI
  Pression Arrière: {s['tyre_ar']} PSI

LEST
  Ballast: {s['ballast']}

# Notes: {PRESETS_F1_2020.get(st.session_state.f1_preset, {}).get('desc','Setup violet custom')}
        """, language="yaml")
        
        # Export JSON
        export_data = {
            "jeu": "F1 2020",
            "edition": "Violet",
            "circuit": track,
            "circuit_code": info['code'],
            "preset": st.session_state.f1_preset,
            "date": datetime.datetime.now().isoformat(),
            "setup": s,
            "conseils": {
                "downforce_requis": info['downforce'],
                "usure": info['usure'],
                "balance": balance_text,
                "usure_risque": wear_text
            }
        }
        st.download_button("💾 Télécharger JSON Violet", data=json.dumps(export_data, indent=2, ensure_ascii=False), file_name=f"F1_2020_{info['code']}_Violet.json", mime="application/json", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="violet-card">', unsafe_allow_html=True)
        st.markdown("#### 🎯 Analyse Violet")
        balance_text, balance_color = get_balance()
        wear_text, wear_color = get_tyre_wear_risk()
        
        st.markdown(f"""
        <div style="display:flex; flex-direction:column; gap:10px;">
            <div class="violet-metric">Balance<br><b style="color:{balance_color};">{balance_text}</b></div>
            <div class="violet-metric">Usure<br><b style="color:{wear_color};">{wear_text}</b></div>
            <div class="violet-metric">Vmax Estimée<br><b style="color:#A78BFA;">{340 - (s['aero_av']+s['aero_ar'])*4} km/h</b></div>
            <div class="violet-metric">Grip Virage<br><b style="color:#C4B5FD;">{(s['aero_av']+s['aero_ar'])*4 + (12-s['susp_av'])*2}%</b></div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("#### 💡 Conseils F1 2020")
        conseils = []
        if s['aero_av'] == 1 and s['aero_ar'] == 1 and info['downforce'] in ["Élevé", "Très Élevé"]:
            conseils.append("⚠️ Appui trop faible pour ce circuit! Tu vas glisser.")
        if s['height_av'] < 4 and s['height_ar'] < 4:
            conseils.append("⚠️ Hauteur très basse - attention vibreurs à " + track)
        if s['diff_on'] > 85 and info['traction'] == "Élevée":
            conseils.append("💡 Diff ON élevé ok ici, traction importante")
        if not conseils:
            conseils.append("✅ Setup cohérent pour " + track)
            conseils.append("💜 Violet Edition validée!")
        
        for c in conseils:
            st.markdown(f"<div class='violet-track'>{c}</div>", unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

# Footer violet
st.markdown("---")
st.markdown("""
<div style="text-align:center; padding:12px; background:linear-gradient(90deg, rgba(91,33,182,0.2), rgba(124,58,237,0.2)); border-radius:12px; border:1px solid rgba(124,58,237,0.3);">
    <span style="font-family:Orbitron; color:#C4B5FD; font-weight:800; letter-spacing:0.2em;">F1 2020 • VIOLET EDITION • TOUS PARAMÈTRES ADAPTÉS</span><br>
    <span style="color:#A78BFA; font-size:12px;">Aéro • Transmission • Géométrie • Suspension • Freins • Pneus • Lest • 22 Circuits • 6 Presets</span>
</div>
""", unsafe_allow_html=True)
