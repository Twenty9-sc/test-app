import streamlit as st
import json
import os
import base64
from PIL import Image
import io
import re
import streamlit.components.v1 as components

# --- CONFIGURATION INITIALE ---
if "etat_sidebar" not in st.session_state:
    st.session_state.etat_sidebar = "expanded"

st.set_page_config(
    page_title="BOS2 - Gestion Industrielle", 
    layout="wide",
    initial_sidebar_state=st.session_state.etat_sidebar
)

# --- CSS PERSONNALISÉ ---
st.markdown("""
<style>
.text-highlight {
    background-color: #CC0605;
    padding: 2px 6px;
    border-radius: 4px;
    color: white;
    font-weight: bold;
}
.verified-text {
    color: #CC0605 !important;
}
.verified-text span, .verified-text b, .verified-text p, .verified-text div {
    color: #CC0605 !important;
}
.normal-row {
    background-color: transparent;
    padding: 12px;
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

FICHIER_SAUVEGARDE = "donnees_bos2.json"

# --- BANQUE D'ICÔNES SVG FORMELLES ET ADAPTATIVES ---
def get_svg_icon(icon_name):
    icons = {
        "search": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>',
        "folder": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>',
        "palette": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 14.7255 3.09032 17.1962 4.85857 19C5.03444 19.1759 5.27092 19.2638 5.51034 19.2435C6.73278 19.1397 7.82283 18.4239 8.35824 17.3061C8.61483 16.7713 9.15545 16.4348 9.75402 16.4348H10.5C11.3284 16.4348 12 17.1064 12 17.9348V22Z"></path></svg>',
        "beaker": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><path d="M4.5 3h15M6 3v16a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V3M6 14h12"></path></svg>',
        "layers": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polygon points="2 17 12 22 22 17"></polygon><polygon points="2 12 12 17 22 12"></polygon></svg>',
        "plus": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 4px;"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></svg>',
        "chart": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>',
        "eye": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 4px;"><path d="M1 12s4-8 11-8 4 8 4 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>',
        "alert": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>',
        "refresh": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 4px;"><polyline points="23 4 23 10 19 10"></polyline><polyline points="1 20 1 14 5 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>',
        "arrow-left": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 4px;"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>'
    }
    return icons.get(icon_name, "")

# --- FONCTION ENCODAGE SÉCURISÉE ---
def encoder_image_systeme(nom_fichier):
    if os.path.exists(nom_fichier):
        try:
            with open(nom_fichier, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception:
            return ""
    return ""

LOGO_SIDEBAR_BASE64 = encoder_image_systeme("contents-8712.png")
LOGO_BACKGROUND_BASE64 = encoder_image_systeme("Logo-Beraudy-rectangle.png")

if LOGO_BACKGROUND_BASE64:
    css_background = f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image: url("data:image/png;base64,{LOGO_BACKGROUND_BASE64}");
        background-size: 45%;
        background-repeat: no-repeat;
        background-position: center center;
        background-attachment: fixed;
    }}
    [data-testid="stAppViewContainer"]::before {{
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background-color: rgba(255, 255, 255, 0.90); 
        z-index: 0;
    }}
    [data-testid="stHeader"], [data-testid="stVerticalBlock"], .stMain {{
        position: relative;
        z-index: 1;
        background-color: transparent !important;
    }}
    </style>
    """
    st.markdown(css_background, unsafe_allow_html=True)

def encoder_fichier_local(uploaded_file):
    try:
        bytes_data = uploaded_file.getvalue()
        base64_encoded = base64.b64encode(bytes_data).decode("utf-8")
        return {"name": uploaded_file.name, "mime": uploaded_file.type, "data": base64_encoded}
    except Exception as e:
        st.error(f"Erreur lors de l'encodage de l'image : {e}")
        return None

def afficher_image_base64(base64_string, width=None):
    try:
        image_bytes = base64.b64decode(base64_string)
        image = Image.open(io.BytesIO(image_bytes))
        st.image(image, use_container_width=True if width is None else False, width=width)
    except Exception as e:
        st.error(f"Erreur lors de l'affichage de l'image : {e}")

def interpreter_texte_avec_images(texte, images_en_ligne):
    if not texte: return ""
    st.markdown(texte, unsafe_allow_html=True)

# --- BASE DE DONNÉES NUANCIER RAL CLASSIC OFFICIEL ---
RAL_DICT = {
    "1000": "#BEBD7F", "1001": "#C2B07E", "1002": "#C6A664", "1003": "#E5BE01", "1004": "#CDA434",
    "1005": "#A98307", "1006": "#E4A010", "1007": "#DC9D00", "1011": "#8A6642", "1012": "#C7B446",
    "1013": "#EAE6D8", "1014": "#DEC496", "1015": "#E6D5AC", "1016": "#E2E421", "1017": "#F3A505",
    "1018": "#EAAE00", "1019": "#A08679", "1020": "#A3937B", "1021": "#F5D033", "1023": "#F1A94E",
    "1024": "#D1A153", "1027": "#A3822B", "1028": "#F4A900", "1032": "#D6AE01", "1033": "#F3A54A",
    "1034": "#EAAE69", "2000": "#ED760E", "2001": "#C93C20", "2002": "#D43D1A", "2003": "#F54020",
    "2004": "#E75B12", "2008": "#F15C13", "2009": "#E75B12", "2010": "#D43D1A", "2011": "#EC760E",
    "2012": "#E55137", "3000": "#AF2B1E", "3001": "#A31D1B", "3002": "#A2231D", "3003": "#B32428",
    "3004": "#75151E", "3005": "#5E2129", "3007": "#412227", "3009": "#642424", "3011": "#7E191B",
    "3012": "#C6726B", "3013": "#A62B2A", "3014": "#DF7381", "3015": "#E4A0A5", "3016": "#B32821",
    "3017": "#E63244", "3018": "#D53032", "3020": "#CC0605", "3022": "#D9504E", "3027": "#C51D34",
    "3031": "#B32428", "4001": "#80461B", "4002": "#6D3F5B", "4003": "#C64B8C", "4004": "#51283F",
    "4005": "#6C4675", "4006": "#A20067", "4007": "#4A1F45", "4008": "#924E7D", "4009": "#A18594",
    "4010": "#C12869", "5000": "#16345A", "5001": "#174459", "5002": "#111E6C", "5003": "#193740",
    "5004": "#171F26", "5005": "#1F4E5B", "5007": "#29536E", "5008": "#232C3F", "5009": "#20475E",
    "5010": "#0A3C61", "5011": "#131C39", "5012": "#1E7FCB", "5013": "#1B264A", "5014": "#606E8C",
    "5015": "#2271B3", "5017": "#063971", "5018": "#3F888F", "5019": "#1B4D79", "5020": "#1D334A",
    "5021": "#256D7B", "5022": "#252850", "5023": "#49678D", "5024": "#5D9B9B", "6000": "#316650",
    "6001": "#287233", "6002": "#276230", "6003": "#4B5320", "6004": "#0E4243", "6005": "#0F422A",
    "6006": "#40433B", "6007": "#283424", "6008": "#272922", "6009": "#213123", "6010": "#35682D",
    "6011": "#587246", "6012": "#343E40", "6013": "#6C7156", "6014": "#474337", "6015": "#3B3C36",
    "6016": "#1E5945", "6017": "#4C9141", "6018": "#57A639", "6019": "#B9E3AE", "6020": "#2E3B2E",
    "6021": "#89AC76", "6022": "#25221F", "6024": "#29955F", "6025": "#53783B", "6026": "#16544E",
    "6027": "#84C3BE", "6028": "#2E584A", "6029": "#1E7F55", "6032": "#237F52", "6033": "#46827F",
    "6034": "#7FB5B3", "7000": "#788585", "7001": "#8A9597", "7002": "#7E7B52", "7003": "#6C7059",
    "7004": "#969992", "7005": "#6B716F", "7006": "#6B6659", "7008": "#746643", "7009": "#5D675D",
    "7010": "#4C5350", "7011": "#555D50", "7012": "#596163", "7013": "#4E4F42", "7015": "#434B4D",
    "7016": "#383E42", "7021": "#2F353B", "7022": "#4E5154", "7023": "#7E8480", "7024": "#45494E",
    "7026": "#2F3E46", "7030": "#939388", "7031": "#5B686B", "7032": "#B5B8A3", "7033": "#7A8B7B",
    "7034": "#8F8B66", "7035": "#D7D7D7", "7036": "#7F7679", "7037": "#7D7F7D", "7038": "#B5B8B1",
    "7039": "#6C6960", "7040": "#9DA1AA", "7042": "#8D948D", "7043": "#4E5452", "7044": "#B9B8B1",
    "7045": "#909090", "7046": "#828282", "7047": "#D0D0D0", "8000": "#887142", "8001": "#9C6634",
    "8002": "#6C463F", "8003": "#734222", "8004": "#8E402A", "8007": "#59351F", "8008": "#6F4F28",
    "8011": "#5B3A29", "8012": "#593122", "8014": "#382C1E", "8015": "#633A34", "8016": "#4C2F27",
    "8017": "#45322E", "8019": "#403A3A", "8022": "#212121", "8023": "#A65624", "8024": "#79553D",
    "8025": "#755C48", "8028": "#4E3629", "9001": "#FDF4E3", "9002": "#E7EBDA", "9003": "#F4F4F4",
    "9004": "#282828", "9005": "#0A0A0A", "9006": "#A5A5A5", "9007": "#8F8F8F", "9010": "#FFFFFF",
    "9011": "#1C1C1C", "9016": "#F6F6F6", "9017": "#1E1E1E", "9018": "#D7DBDE"
}

# --- CHARGEMENT / SAUVEGARDE MULTI-GROUPES ---
def charger_donnees():
    if os.path.exists(FICHIER_SAUVEGARDE):
        try:
            with open(FICHIER_SAUVEGARDE, "r", encoding="utf-8") as f:
                donnees = json.load(f)
                donnees.setdefault("creation_processus", {})
                prep = donnees.setdefault("preparation_melanges", {})
                prep.setdefault("couleurs", [])
                prep.setdefault("melanges", [])
                prep.setdefault("fiches_methode", [])
                prep.setdefault("additifs", [])
                prep.setdefault("base_rals", [])
                return donnees
        except Exception: pass
    return {"creation_processus": {}, "preparation_melanges": {"couleurs": [], "melanges": [], "fiches_methode": [], "additifs": [], "base_rals": []}}

def sauvegarder_donnees():
    with open(FICHIER_SAUVEGARDE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.processus_db, f, ensure_ascii=False, indent=4)

if "processus_db" not in st.session_state: st.session_state.processus_db = charger_donnees()
if "groupe_actif" not in st.session_state: st.session_state.groupe_actif = None
if "produit_selectionne" not in st.session_state: st.session_state.produit_selectionne = None
if "sub_section_melange" not in st.session_state: st.session_state.sub_section_melange = "🎨 Nuancier de couleurs"

query_params = st.query_params
if "moved_id" in query_params and "moved_x" in query_params and "moved_y" in query_params:
    try:
        m_fid = int(query_params["moved_id"])
        m_fidx = int(query_params["moved_idx"])
        m_fx = int(float(query_params["moved_x"]))
        m_fy = int(float(query_params["moved_y"]))
        fiches_m = st.session_state.processus_db["preparation_melanges"].get("fiches_methode", [])
        if m_fidx < len(fiches_m):
            for s in fiches_m[m_fidx]["formes"]:
                if s["id"] == m_fid:
                    s["x"] = m_fx; s["y"] = m_fy
                    sauvegarder_donnees()
        st.query_params.clear()
    except Exception: pass

def est_dosage_valide(txt_dosage):
    if not txt_dosage: return False
    clean = str(txt_dosage).strip().lower()
    if clean in ["", "0", "0g", "0 g", "0ml", "0 ml", "none"]: return False
    return True

# --- CONTENU DE LA BARRE LATÉRALE ---
with st.sidebar:
    st.markdown('<div style="text-align: center; margin-top: 10px;"><h2>BOS2 PORTAIL</h2></div>', unsafe_allow_html=True)
    st.markdown("---")

st.markdown("<br>", unsafe_allow_html=True)
col_search_bar, col_toggle_side = st.columns([5, 1])

with col_search_bar:
    search_icon = get_svg_icon("search")
    st.markdown(f'<div style="display:flex; align-items:center;">{search_icon}<span>RECHERCHE ULTRA-RAPIDE (Filtre instantané)...</span></div>', unsafe_allow_html=True)
    recherche_globale = st.text_input("", label_visibility="collapsed").strip()

with col_toggle_side:
    texte_bouton_sidebar = "◀️ Fermer Menu" if st.session_state.etat_sidebar == "expanded" else "▶️ Ouvrir Menu"
    if st.button(texte_bouton_sidebar, use_container_width=True):
        st.session_state.etat_sidebar = "collapsed" if st.session_state.etat_sidebar == "expanded" else "expanded"
        st.rerun()

if recherche_globale:
    icon_chart = get_svg_icon("chart")
    st.markdown(f"### {icon_chart} Résultats de la recherche globale", unsafe_allow_html=True)
    resultats_trouves = []
    
    for prod_nom, prod_data in st.session_state.processus_db.get("creation_processus", {}).items():
        if recherche_globale.lower() in prod_nom.lower():
            resultats_trouves.append({"label": f"Dossier : {prod_nom}", "chemin": "Processus ➔ " + prod_nom, "cat": "creation_processus", "prod": prod_nom})
                
    prep_m = st.session_state.processus_db["preparation_melanges"].get("couleurs", [])
    for idx_c, c in enumerate(prep_m):
        if any(recherche_globale.lower() in str(c.get(k, "")).lower() for k in ["ref", "nom_actuel", "nom_futur", "ral", "societe"]):
            resultats_trouves.append({"label": f"Couleur : {c.get('nom_actuel')} ({c.get('ref')})", "chemin": "Mélanges ➔ Nuancier", "cat": "preparation_melanges", "prod": "SECTION_COULEURS"})
            
    if resultats_trouves:
        for idx_r, res in enumerate(resultats_trouves):
            col_res_txt, col_res_btn = st.columns([4, 1])
            with col_res_txt:
                st.markdown(f"**{res['label']}**")
                st.caption(f"📍 Chemin : {res['chemin']}")
            with col_res_btn:
                if st.button(f"Accéder", key=f"global_res_{idx_r}"):
                    st.session_state.groupe_actif = res["cat"]
                    if res["prod"] == "SECTION_COULEURS": st.session_state.sub_section_melange = "🎨 Liste des couleurs"
                    else: st.session_state.produit_selectionne = res["prod"]
                    st.rerun()
            st.markdown("<hr style='margin: 0.3em 0px; opacity: 0.15;'>", unsafe_allow_html=True)
    else: st.info("Aucun résultat trouvé.")
    st.markdown("---")

if st.session_state.groupe_actif is None:
    st.title("Portail Industriel BOS2")
    st.markdown("### Sélectionnez votre espace de travail :")
    c_g1, c_g2 = st.columns(2)
    with c_g1:
        if st.button(f"CRÉATION DES PROCESSUS", type="primary", use_container_width=True):
            st.session_state.groupe_actif = "creation_processus"; st.rerun()
    with c_g2:
        if st.button(f"PRÉPARATION DES MÉLANGES", type="primary", use_container_width=True):
            st.session_state.groupe_actif = "preparation_melanges"
            st.session_state.sub_section_melange = "🎨 Nuancier de couleurs"
            st.rerun()
    st.stop()

G_ACTIF = st.session_state.groupe_actif

if st.sidebar.button(f"Menu Principal / Retour"):
    st.session_state.groupe_actif = None
    st.rerun()

# --- MODALES POUR LES COULEURS ---
@st.dialog("➕ Ajouter une nouvelle couleur", width="large")
def ouvrir_ajout_couleur():
    if "add_ral" not in st.session_state: st.session_state["add_ral"] = ""
    if "add_hex" not in st.session_state: st.session_state["add_hex"] = "#3B82F6"

    c_ref = st.text_input("Référence (Code unique)")
    c_actuel = st.text_input("Nom actuel")
    c_futur = st.text_input("Futur nom")
    c_societe = st.text_input("Société / Client")
    c_type = st.selectbox("Type de couleur", ["Opaque", "Translucide", "2"])
    
    c_ral_col, c_chk_col, c_hex_col = st.columns([2, 1, 2])
    with c_ral_col:
        c_ral = st.text_input("Code RAL", value=st.session_state["add_ral"])
    with c_chk_col:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(f"Vérifier RAL", key="btn_check_add_ral"):
            num_ral = ''.join(filter(str.isdigit, c_ral.strip()))
            if num_ral in RAL_DICT:
                st.session_state["add_hex"] = RAL_DICT[num_ral]
                st.session_state["add_ral"] = c_ral
                st.rerun()
    with c_hex_col:
        c_hex = st.color_picker("Sélectionner la nuance", value=st.session_state["add_hex"])

    if st.button("Enregistrer la couleur", type="primary"):
        if c_ref:
            num_ral = ''.join(filter(str.isdigit, c_ral.strip()))
            couleur_finale = RAL_DICT.get(num_ral, c_hex) if num_ral else c_hex
            st.session_state.processus_db["preparation_melanges"]["couleurs"].append({
                "ref": c_ref, "nom_actuel": c_actuel, "nom_futur": c_futur, "ral": c_ral, "societe": c_societe, "type": c_type, "visuel": couleur_finale
            })
            st.session_state.pop("add_ral", None)
            st.session_state.pop("add_hex", None)
            sauvegarder_donnees(); st.rerun()

@st.dialog("✏️ Modifier une couleur", width="large")
def ouvrir_modif_couleur(index, couleur_data):
    if f"temp_ref_{index}" not in st.session_state:
        st.session_state[f"temp_ref_{index}"] = couleur_data.get("ref", "")
        st.session_state[f"temp_actuel_{index}"] = couleur_data.get("nom_actuel", "")
        st.session_state[f"temp_futur_{index}"] = couleur_data.get("nom_futur", "")
        st.session_state[f"temp_soc_{index}"] = couleur_data.get("societe", "")
        st.session_state[f"temp_type_{index}"] = couleur_data.get("type", "Opaque")
        st.session_state[f"temp_ral_{index}"] = couleur_data.get("ral", "")
        st.session_state[f"temp_hex_{index}"] = couleur_data.get("visuel", "#3B82F6")

    m_ref = st.text_input("Référence", key=f"temp_ref_{index}")
    m_actuel = st.text_input("Nom actuel", key=f"temp_actuel_{index}")
    m_futur = st.text_input("Futur nom", key=f"temp_futur_{index}")
    m_societe = st.text_input("Société / Client", key=f"temp_soc_{index}")
    m_type = st.selectbox("Type", ["Opaque", "Translucide", "2"], 
                          index=["Opaque", "Translucide", "2"].index(st.session_state[f"temp_type_{index}"]),
                          key=f"temp_type_{index}")

    c_ral_col, c_chk_col, c_hex_col = st.columns([2, 1, 2])
    with c_ral_col: m_ral = st.text_input("Code RAL", key=f"temp_ral_{index}")
    with c_chk_col:
        if st.button("Vérifier RAL", key=f"btn_check_{index}"):
            num_ral = ''.join(filter(str.isdigit, m_ral.strip()))
            if num_ral in RAL_DICT:
                st.session_state[f"temp_hex_{index}"] = RAL_DICT[num_ral]
                st.rerun()
    with c_hex_col: m_hex = st.color_picker("Ajuster la nuance", key=f"temp_hex_{index}")

    if st.button("Mettre à jour", type="primary"):
        st.session_state.processus_db["preparation_melanges"]["couleurs"][index] = {
            "ref": m_ref, "nom_actuel": m_actuel, "nom_futur": m_futur, 
            "ral": m_ral, "societe": m_societe, "type": m_type, "visuel": m_hex
        }
        for k in [f"temp_ref_{index}", f"temp_actuel_{index}", f"temp_futur_{index}", 
                  f"temp_soc_{index}", f"temp_type_{index}", f"temp_ral_{index}", f"temp_hex_{index}"]:
            del st.session_state[k]
        sauvegarder_donnees(); st.rerun()

# --- MODALES POUR LES ADDITIFS ---
@st.dialog("➕ Ajouter un additif", width="large")
def ouvrir_ajout_additif():
    a_nom = st.text_input("Nom de l'additif (Sert de référence/identifiant)")
    a_emp = st.text_input("Emplacement de stockage")
    a_comm = st.text_area("Commentaire")
    if st.button("Enregistrer l'additif", type="primary"):
        if a_nom:
            st.session_state.processus_db["preparation_melanges"]["additifs"].append({"nom": a_nom, "emplacement": a_emp, "commentaire": a_comm})
            sauvegarder_donnees(); st.rerun()

@st.dialog("✏️ Modifier un additif", width="large")
def ouvrir_modif_additif(index, additif_data):
    m_nom = st.text_input("Nom de l'additif", value=additif_data.get("nom", ""))
    m_emp = st.text_input("Emplacement de stockage", value=additif_data.get("emplacement", ""))
    m_comm = st.text_area("Commentaire", value=additif_data.get("commentaire", ""))
    if st.button("Mettre à jour", type="primary"):
        st.session_state.processus_db["preparation_melanges"]["additifs"][index] = {"nom": m_nom, "emplacement": m_emp, "commentaire": m_comm}
        sauvegarder_donnees(); st.rerun()

@st.dialog("➕ Ajouter un nouveau RAL au nuancier", width="large")
def ouvrir_ajout_ral_base():
    r_code = st.text_input("Code RAL (ex: 5015)")
    r_nom = st.text_input("Nom officiel de la teinte")
    r_hex = st.color_picker("Sélectionner la valeur Hexadécimale", "#FFFFFF")
    if st.button("Enregistrer dans le catalogue", type="primary"):
        if r_code and r_nom:
            RAL_DICT[r_code.strip()] = r_hex
            st.session_state.processus_db["preparation_melanges"].setdefault("base_rals", []).append({"code": r_code.strip(), "nom": r_nom.strip(), "visuel": r_hex})
            sauvegarder_donnees(); st.rerun()

# --- MODALES POUR LES MÉLANGES ---
@st.dialog("➕ Créer un mélange", width="large")
def ouvrir_ajout_melange():
    liste_teintes = st.session_state.processus_db["preparation_melanges"].get("couleurs", [])
    liste_additifs = st.session_state.processus_db["preparation_melanges"].get("additifs", [])
    liste_melanges = st.session_state.processus_db["preparation_melanges"].get("melanges", [])
    if "tmp_form_state" not in st.session_state: st.session_state.tmp_form_state = {}
    
    m_ref = st.text_input("Référence du mélange")
    m_nom = st.text_input("Nom du mélange")
    m_cat = st.selectbox("Catégorie de rangement du mélange", ["Mélange Couleurs", "Autre Mélange"])
    m_statut = st.radio("État du mélange :", ["Pas vérifié", "Vérifier"], index=0, horizontal=True)
    m_img_file = st.file_uploader("Importer l'image du rendu du mélange", type=["png", "jpg", "jpeg", "webp"])
    m_emp = st.text_input("Emplacement de stockage")
    m_comm = st.text_area("Commentaires")
    
    recherche_filtre_c = st.text_input("🔍 Filtrer les composants (Nom, Réf, Code RAL, Mélange existant) :").strip()
    
    st.markdown("**🎨 Couleurs du Nuancier (Top 5 max) :**")
    couleurs_trouvees = [c for c in liste_teintes if not recherche_filtre_c or (recherche_filtre_c.lower() in c["nom_actuel"].lower() or recherche_filtre_c.lower() in c["ref"].lower() or recherche_filtre_c.lower() in c.get("ral", "").lower())]
    for idx, c in enumerate(couleurs_trouvees[-5:]):
        label = f"{c['nom_actuel']} ({c['ref']})"
        key_c = f"color_{c['ref']}"
        col_chk, col_vis = st.columns([7, 1])
        with col_chk:
            if st.checkbox(label, value=(key_c in st.session_state.tmp_form_state), key=f"chk_add_c_{idx}_{c['ref']}"):
                st.session_state.tmp_form_state[key_c] = {"type": "couleur", "ref": c['ref'], "nom": c['nom_actuel'], "dosage": st.text_input(f"Dosage pour {c['nom_actuel']}", value=st.session_state.tmp_form_state.get(key_c, {}).get("dosage", "100g"), key=f"dos_add_c_{idx}_{c['ref']}")}
            else: st.session_state.tmp_form_state.pop(key_c, None)
        with col_vis: st.markdown(f'<div style="width:22px; height:22px; background-color:{c["visuel"]}; border-radius:50%; border:1px solid #000; margin-top:5px;"></div>', unsafe_allow_html=True)
                
    st.markdown("**🔢 Codes RAL du catalogue (Top 5 max) :**")
    rals_trouves = [(code_ral, hex_ral) for code_ral, hex_ral in RAL_DICT.items() if not recherche_filtre_c or recherche_filtre_c.lower() in code_ral]
    for idx, (code_ral, hex_ral) in enumerate(rals_trouves[-5:]):
        label_ral = f"RAL {code_ral}"
        key_ral = f"ral_std_{code_ral}"
        col_chk_r, col_vis_r = st.columns([7, 1])
        with col_chk_r:
            if st.checkbox(label_ral, value=(key_ral in st.session_state.tmp_form_state), key=f"chk_add_ral_{idx}_{code_ral}"):
                st.session_state.tmp_form_state[key_ral] = {"type": "ral_officiel", "ref": f"RAL {code_ral}", "nom": f"RAL {code_ral}", "visuel": hex_ral, "dosage": st.text_input(f"Dosage pour RAL {code_ral}", value=st.session_state.tmp_form_state.get(key_ral, {}).get("dosage", "100g"), key=f"dos_add_ral_{idx}_{code_ral}")}
            else: st.session_state.tmp_form_state.pop(key_ral, None)
        with col_vis_r: st.markdown(f'<div style="width:22px; height:22px; background-color:{hex_ral}; border-radius:50%; border:1px solid #000; margin-top:5px;"></div>', unsafe_allow_html=True)

    st.markdown("**⚗️ Mélanges existants (Bases - Top 5 max) :**")
    melanges_trouves = [mel for mel in liste_melanges if not recherche_filtre_c or (recherche_filtre_c.lower() in mel["nom"].lower() or recherche_filtre_c.lower() in mel["ref"].lower())]
    for idx, mel in enumerate(melanges_trouves[-5:]):
        label_m = f"Mélange : {mel['nom']} ({mel['ref']})"
        key_m_exist = f"melange_base_{mel['ref']}"
        col_chk_m, _ = st.columns([7, 1])
        with col_chk_m:
            if st.checkbox(label_m, value=(key_m_exist in st.session_state.tmp_form_state), key=f"chk_add_mel_{idx}_{mel['ref']}"):
                st.session_state.tmp_form_state[key_m_exist] = {"type": "melange_base", "ref": mel['ref'], "nom": mel['nom'], "dosage": st.text_input(f"Dosage pour Base {mel['nom']}", value=st.session_state.tmp_form_state.get(key_m_exist, {}).get("dosage", "500g"), key=f"dos_add_mel_{idx}_{mel['ref']}")}
            else: st.session_state.tmp_form_state.pop(key_m_exist, None)

    st.markdown("**🧪 Additifs (Top 5 max) :**")
    additifs_trouves = [a for a in liste_additifs if not recherche_filtre_c or recherche_filtre_c.lower() in a["nom"].lower()]
    for idx, a in enumerate(additifs_trouves[-5:]):
        label = f"Additif : {a['nom']}"
        key_a = f"additif_{a['nom']}"
        col_chk_a, _ = st.columns([7, 1])
        with col_chk_a:
            if st.checkbox(label, value=(key_a in st.session_state.tmp_form_state), key=f"chk_add_add_{idx}_{a['nom']}"):
                st.session_state.tmp_form_state[key_a] = {"type": "additif", "ref": a['nom'], "nom": a['nom'], "dosage": st.text_input(f"Dosage pour {a['nom']}", value=st.session_state.tmp_form_state.get(key_a, {}).get("dosage", "10g"), key=f"dos_add_add_{idx}_{a['nom']}")}
            else: st.session_state.tmp_form_state.pop(key_a, None)

    if st.button("Enregistrer la formulation", type="primary"):
        if m_ref and m_nom:
            comp = []
            for k, v in st.session_state.tmp_form_state.items():
                if est_dosage_valide(v.get("dosage", "")):
                    if v["type"] == "couleur":
                        couleur_trouvee = next((x for x in liste_teintes if x["ref"] == v["ref"]), None)
                        comp.append({"type": "couleur", "ref": v["ref"], "nom": couleur_trouvee["nom_actuel"] if couleur_trouvee else v["nom"], "visuel": couleur_trouvee["visuel"] if couleur_trouvee else "#CCCCCC", "dosage": v["dosage"]})
                    elif v["type"] == "ral_officiel":
                        comp.append({"type": "couleur", "ref": v["ref"], "nom": v["nom"], "visuel": v["visuel"], "dosage": v["dosage"]})
                    elif v["type"] == "melange_base":
                        comp.append({"type": "melange_base", "ref": v["ref"], "nom": v['nom'], "visuel": "#CBD5E1", "dosage": v["dosage"]})
                    else:
                        comp.append({"type": "additif", "ref": v["ref"], "nom": v["nom"], "visuel": "#E2E8F0", "dosage": v["dosage"]})
            img_data = encoder_fichier_local(m_img_file) if m_img_file else None
            st.session_state.processus_db["preparation_melanges"]["melanges"].append({
                "ref": m_ref, "nom": m_nom, "categorie_choisie": m_cat, "emplacement": m_emp, "commentaire": m_comm, "couleurs_associees": comp, "image_rendu": img_data, "statut": m_statut
            })
            st.session_state.tmp_form_state = {}
            sauvegarder_donnees(); st.rerun()


@st.dialog("✏️ Modifier une fiche de mélange", width="large")
def ouvrir_modification_melange(index, melange_data):
    liste_teintes = st.session_state.processus_db["preparation_melanges"].get("couleurs", [])
    
    init_key = f"mod_init_{index}"
    if init_key not in st.session_state:
        st.session_state.tmp_mod_state = {}
        for c in melange_data.get("couleurs_associees", []):
            type_c = c.get("type", "couleur")
            key = f"{type_c}_{c['ref']}"
            st.session_state.tmp_mod_state[key] = {"type": type_c, "ref": c["ref"], "nom": c.get("nom", ""), "dosage": c["dosage"], "visuel": c.get("visuel")}
        st.session_state[init_key] = True

    m_ref = st.text_input("Référence du mélange", value=melange_data.get("ref", ""))
    m_nom = st.text_input("Nom du mélange", value=melange_data.get("nom", ""))
    cat_actuelle = melange_data.get("categorie_choisie", "Mélange Couleurs")
    m_cat = st.selectbox("Catégorie de rangement du mélange", ["Mélange Couleurs", "Autre Mélange"], index=["Mélange Couleurs", "Autre Mélange"].index(cat_actuelle))
    
    statut_actuel = melange_data.get("statut", "Pas vérifié")
    options_statut = ["Pas vérifié", "Vérifier"]
    m_statut = st.radio("État du mélange :", options_statut, index=options_statut.index(statut_actuel) if statut_actuel in options_statut else 0, horizontal=True)

    if melange_data.get("image_rendu"):
        st.caption("Aperçu de l'image actuelle :")
        afficher_image_base64(melange_data["image_rendu"]["data"], width=100)
    m_img_file = st.file_uploader("Remplacer ou importer l'image du mélange", type=["png", "jpg", "jpeg", "webp"])
    m_emp = st.text_input("Emplacement de stockage", value=melange_data.get("emplacement", ""))
    m_comm = st.text_area("Commentaire", value=melange_data.get("commentaire", ""))

    st.markdown("### 🛠️ Composants actuellement dans ce mélange :")
    cles_existantes = list(st.session_state.tmp_mod_state.keys())
    
    if cles_existantes:
        for idx, k in enumerate(cles_existantes):
            v = st.session_state.tmp_mod_state.get(k)
            if not v: continue
            
            col_chk, col_vis = st.columns([7, 1])
            with col_chk:
                deja_present = k in st.session_state.tmp_mod_state
                label_affichage = f"[{v['type'].upper()}] {v['nom']} ({v['ref']})"
                
                if st.checkbox(label_affichage, value=deja_present, key=f"mod_item_chk_{idx}_{v['ref']}"):
                    st.session_state.tmp_mod_state[k]["dosage"] = st.text_input(f"Dosage pour {v['nom']}", value=v["dosage"], key=f"dos_mod_item_{idx}_{v['ref']}")
                else:
                    st.session_state.tmp_mod_state.pop(k, None)
                    st.rerun()
            with col_vis:
                if v.get("visuel"):
                    st.markdown(f'<div style="width:22px; height:22px; background-color:{v["visuel"]}; border-radius:50%; border:1px solid #000; margin-top:5px;"></div>', unsafe_allow_html=True)
    else:
        st.warning("Aucun composant sélectionné dans ce mélange.")

    if st.button("Mettre à jour le mélange", type="primary"):
        comp_finaux = []
        for k, v in st.session_state.tmp_mod_state.items():
            if est_dosage_valide(v.get("dosage", "")):
                if v["type"] == "couleur":
                    couleur_trouvee = next((x for x in liste_teintes if x["ref"] == v["ref"]), None)
                    comp_finaux.append({"type": "couleur", "ref": v["ref"], "nom": couleur_trouvee["nom_actuel"] if couleur_trouvee else v["nom"], "visuel": couleur_trouvee["visuel"] if couleur_trouvee else v.get("visuel", "#CCCCCC"), "dosage": v["dosage"]})
                elif v["type"] == "ral_officiel":
                    comp_finaux.append({"type": "couleur", "ref": v["ref"], "nom": v["nom"], "visuel": v["visuel"], "dosage": v["dosage"]})
                elif v["type"] == "melange_base":
                    comp_finaux.append({"type": "melange_base", "ref": v["ref"], "nom": v['nom'], "visuel": "#CBD5E1", "dosage": v["dosage"]})
                else:
                    comp_finaux.append({"type": "additif", "ref": v["ref"], "nom": v["nom"], "visuel": "#E2E8F0", "dosage": v["dosage"]})

        img_final = encoder_fichier_local(m_img_file) if m_img_file else melange_data.get("image_rendu")
        st.session_state.processus_db["preparation_melanges"]["melanges"][index] = {
            "ref": m_ref, "nom": m_nom, "categorie_choisie": m_cat, "emplacement": m_emp, "commentaire": m_comm, "couleurs_associees": comp_finaux, "image_rendu": img_final, "statut": m_statut
        }
        st.session_state.tmp_mod_state.clear()
        if init_key in st.session_state: del st.session_state[init_key]
        sauvegarder_donnees(); st.rerun()

@st.dialog("➕ Ajouter une étape", width="large")
def ouvrir_formulaire_etape(groupe, prod):
    titre = st.text_input("Titre de l'étape")
    description = st.text_area("Description de l'étape")
    if st.button("Enregistrer l'étape", type="primary"):
        if titre:
            if "etapes" not in st.session_state.processus_db[groupe][prod]: st.session_state.processus_db[groupe][prod]["etapes"] = []
            st.session_state.processus_db[groupe][prod]["etapes"].append({"titre": titre, "description": description, "is_local": False})
            sauvegarder_donnees(); st.rerun()

@st.dialog("➕ Créer une nouvelle fiche", width="large")
def ouvrir_ajout_fiche_methode():
    nom = st.text_input("Nom de la fiche méthode")
    if st.button("Créer la fiche", type="primary"):
        if nom:
            st.session_state.processus_db["preparation_melanges"]["fiches_methode"].append({"nom": nom, "formes": [], "liaisons": []})
            sauvegarder_donnees(); st.rerun()

# ---------------------------------------------------------
# MODULE 1 : CRÉATION DES PROCESSUS
# ---------------------------------------------------------
if G_ACTIF == "creation_processus":
    db_courante = st.session_state.processus_db[G_ACTIF]
    st.sidebar.title("🏗️ Édition SOP")
    recherche_sidebar = st.sidebar.text_input("🔍 Filtrer la liste...", "").strip()
    liste_produits = sorted(list(db_courante.keys()))
    if recherche_sidebar: liste_produits = sorted([p for p in liste_produits if recherche_sidebar.lower() in p.lower()])
    
    # BANDEAU D'INFORMATION UNIQUE POUR LA LISTE DES PROCESSUS
    if liste_produits:
        st.info(f"📊 **Nombre de processus :** {len(liste_produits)} | **Premier :** {liste_produits[0]} | **Dernier :** {liste_produits[-1]}")
    else:
        st.sidebar.warning("Aucun processus trouvé")
        
    producto_index = liste_produits.index(st.session_state.produit_selectionne) if st.session_state.produit_selectionne in liste_produits else 0
    produit_selectionne = st.sidebar.selectbox("Choisir un processus actif :", liste_produits, index=producto_index)
    st.session_state.produit_selectionne = produit_selectionne
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("➕ Nouvel Fichier")
    nouveau_nom = st.sidebar.text_input("Nom du processus")
    if st.sidebar.button("Créer la fiche"):
        if nouveau_nom and nouveau_nom not in db_courante:
            st.session_state.processus_db[G_ACTIF][nouveau_nom] = {"etapes": [], "ressources": []}
            st.session_state.produit_selectionne = nouveau_nom
            sauvegarder_donnees(); st.rerun()

    st.title("🏗️ Création des Processus")
    if produit_selectionne:
        if "mode_grand_ecran" not in st.session_state: st.session_state.mode_grand_ecran = False
        col_titre, col_btn_mode = st.columns([3, 1])
        with col_titre: st.subheader(f"📦 Processus : {produit_selectionne}")
        with col_btn_mode:
            if st.button("🖥️ Basculer Grand Écran"):
                st.session_state.mode_grand_ecran = not st.session_state.mode_grand_ecran; st.rerun()
        
        etapes = db_courante[produit_selectionne].setdefault("etapes", [])
        if not st.session_state.mode_grand_ecran:
            if st.button("➕ Créer une étape", type="primary"): ouvrir_formulaire_etape(G_ACTIF, produit_selectionne)
            st.markdown("---")
            for i, etape in enumerate(list(etapes)):
                with st.expander(f"🛑 Étape {i+1} : {etape['titre']}", expanded=False):
                    col_t, col_m = st.columns([1, 1])
                    with col_t:
                        interpreter_texte_avec_images(etape['description'], etape.get("inline_images", {}))
                        key_del = f"del_confirm_etp_{produit_selectionne}_{i}"
                        if key_del not in st.session_state: st.session_state[key_del] = False
                        if not st.session_state[key_del]:
                            if st.button("🗑️ Supprimer l'étape", key=f"del_etp_{i}"): st.session_state[key_del] = True; st.rerun()
                        else:
                            st.warning("💥 Confirmer la suppression ?")
                            c_del_col1, c_del_col2 = st.columns(2)
                            with c_del_col1:
                                if st.button("Oui, effacer", key=f"del_etp_yes_{i}", type="primary"):
                                    st.session_state.processus_db[G_ACTIF][produit_selectionne]["etapes"].pop(i)
                                    st.session_state[key_del] = False
                                    sauvegarder_donnees(); st.rerun()
                            with c_del_col2:
                                if st.button("Annuler", key=f"del_etp_no_{i}"): st.session_state[key_del] = False; st.rerun()
                    with col_m:
                        if etape.get("is_local") and etape.get("media_data"): afficher_image_base64(etape["media_data"]["data"])
        else:
            for i, etape in enumerate(etapes):
                st.markdown(f"### Étape {i+1} : {etape['titre']}")
                interpreter_texte_avec_images(etape['description'], etape.get("inline_images", {}))
                if etape.get("is_local") and etape.get("media_data"): afficher_image_base64(etape["media_data"]["data"])
                st.markdown("---")

# ---------------------------------------------------------
# MODULE 2 : PRÉPARATION DES MÉLANGES
# ---------------------------------------------------------
elif G_ACTIF == "preparation_melanges":
    choix_section = st.sidebar.radio("Sélectionnez la section :", ["🎨 Nuancier de couleurs", "🧪 Catalogue des additifs", "🔢 Référentiel des codes RAL", "⚗️ Formulations d'atelier", "📐 Fiches Méthode"])
    st.session_state.sub_section_melange = choix_section
    st.markdown(f"## {st.session_state.sub_section_melange}")

    fiches_m = st.session_state.processus_db["preparation_melanges"].setdefault("fiches_methode", [])
    liste_couleurs = st.session_state.processus_db["preparation_melanges"].setdefault("couleurs", [])
    liste_additifs = st.session_state.processus_db["preparation_melanges"].setdefault("additifs", [])

    if choix_section == "🎨 Nuancier de couleurs":
        if st.button("Ajouter une couleur", type="primary"): ouvrir_ajout_couleur()
        if liste_couleurs:
            with st.expander("🔍 Outils de filtrage et de tri du nuancier", expanded=True):
                c_f1, c_f2, c_f3, c_f4, c_f5, c_f6 = st.columns([1, 1, 1, 1, 1.2, 0.8])
                with c_f1: filtre_ref = st.text_input("Filtrer par Référence", "")
                with c_f2: filtre_nom = st.text_input("Filtrer par Nom Actuel/Futur", "")
                with c_f3: filtre_ral = st.text_input("Filtrer par RAL", "")
                with c_f4: filtre_soc = st.text_input("Filtrer par Société", "")
                with c_f5: tri_colonne = st.selectbox("Trier par :", ["Référence", "Nom actuel", "Nom futur", "RAL", "Société", "Type de couleur"])
                with c_f6: sens_tri = st.selectbox("Ordre :", ["Croissant ⬆️", "Décroissant ⬇️"])
            
            couleurs_filtrees = []
            for idx, c in enumerate(liste_couleurs):
                m_ref = filtre_ref.lower() in c.get("ref", "").lower()
                m_nom = (filtre_nom.lower() in c.get("nom_actuel", "").lower()) or (filtre_nom.lower() in c.get("nom_futur", "").lower())
                m_ral = filtre_ral.lower() in c.get("ral", "").lower()
                m_soc = filtre_soc.lower() in c.get("societe", "").lower()
                if m_ref and m_nom and m_ral and m_soc: couleurs_filtrees.append({"index_origine": idx, "data": c})
            
            mapping_cles = {"Référence": "ref", "Nom actuel": "nom_actuel", "Nom futur": "nom_futur", "RAL": "ral", "Société": "societe", "Type de couleur": "type"}
            couleurs_filtrees.sort(key=lambda x: [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', str(x["data"].get(mapping_cles[tri_colonne], "")).lower())], reverse=(sens_tri == "Décroissant ⬇️"))

            # BANDEAU D'INFORMATION UNIQUE POUR LE NUANCIER DE COULEURS
            if couleurs_filtrees:
                st.info(f"📊 **Nombre de couleurs :** {len(couleurs_filtrees)} | **Première :** {couleurs_filtrees[0]['data'].get('nom_actuel','')} ({couleurs_filtrees[0]['data'].get('ref','')}) | **Dernière :** {couleurs_filtrees[-1]['data'].get('nom_actuel','')} ({couleurs_filtrees[-1]['data'].get('ref','')})")

            thead_ref, thead_act, thead_fut, thead_ral, thead_soc, thead_typ, thead_vis, thead_act2 = st.columns([1.2, 1.8, 1.8, 1.2, 1.8, 1.2, 0.8, 1.5])
            with thead_ref: st.markdown("**Référence**")
            with thead_act: st.markdown("**Nom actuel**")
            with thead_fut: st.markdown("**Futur nom**")
            with thead_ral: st.markdown("**RAL**")
            with thead_soc: st.markdown("**Société**")
            with thead_typ: st.markdown("**Type**")
            with thead_vis: st.markdown("**Visuel**")
            with thead_act2: st.markdown("**Actions**")
            st.markdown("<hr style='margin:4px 0px; border-width:2px; border-color:black;'>", unsafe_allow_html=True)
            
            for item in couleurs_filtrees:
                idx_c = item["index_origine"]; c_data = item["data"]
                trow_ref, trow_act, trow_fut, trow_ral, trow_soc, trow_typ, trow_vis, trow_act2 = st.columns([1.2, 1.8, 1.8, 1.2, 1.8, 1.2, 0.8, 1.5])
                with trow_ref: st.write(str(c_data.get("ref", "")).title())
                with trow_act: st.write(str(c_data.get("nom_actuel", "")).title())
                with trow_fut: st.write(str(c_data.get("nom_futur", "")).title())
                with trow_ral: st.write(str(c_data.get("ral", "")).title() or "-")
                with trow_soc: st.write(str(c_data.get("societe", "")).upper())
                with trow_typ: st.write(str(c_data.get("type", "")).title())
                with trow_vis: st.markdown(f'<div style="width:22px; height:25px; background-color:{c_data.get("visuel", "#3B82F6")}; border-radius:50%; border:1px solid #000; margin:auto;"></div>', unsafe_allow_html=True)
                with trow_act2:
                    c_e, c_d = st.columns(2)
                    with c_e:
                        if st.button("✏️", key=f"e_col_{idx_c}"): ouvrir_modif_couleur(idx_c, c_data)
                    with c_d:
                        key_del_c = f"del_confirm_col_{idx_c}"
                        if key_del_c not in st.session_state: st.session_state[key_del_c] = False
                        if not st.session_state[key_del_c]:
                            if st.button("🗑️", key=f"d_col_{idx_c}"): st.session_state[key_del_c] = True; st.rerun()
                        else:
                            if st.button("Confirmer", key=f"d_col_y_{idx_c}", type="primary"):
                                st.session_state.processus_db["preparation_melanges"]["couleurs"].pop(idx_c)
                                sauvegarder_donnees(); st.rerun()

    elif choix_section == "🧪 Catalogue des additifs":
        if st.button("Ajouter un additif", type="primary"): ouvrir_ajout_additif()
        if liste_additifs:
            with st.expander("🔍 Outils de filtrage et de tri des additifs", expanded=True):
                a_f1, a_f2, a_f3, a_f4 = st.columns([2, 2, 2, 1])
                with a_f1: filtre_a_nom = st.text_input("Filtrer par Nom", "")
                with a_f2: filtre_a_emp = st.text_input("Filtrer par Emplacement", "")
                with a_f3: tri_a_colonne = st.selectbox("Trier par :", ["Nom", "Emplacement"])
                with a_f4: sens_a_tri = st.selectbox("Ordre :", ["Croissant ⬆️", "Décroissant ⬇️"], key="sens_a")
                
            additifs_filtres = []
            for idx, a in enumerate(liste_additifs):
                if (filtre_a_nom.lower() in a.get("nom", "").lower()) and (filtre_a_emp.lower() in a.get("emplacement", "").lower()):
                    additifs_filtres.append({"index_origine": idx, "data": a})
            additifs_filtres.sort(key=lambda x: str(x["data"].get("nom" if tri_a_colonne == "Nom" else "emplacement", "")).lower(), reverse=(sens_a_tri == "Décroissant ⬇️"))
            
            # BANDEAU D'INFORMATION UNIQUE POUR LES ADDITIFS
            if additifs_filtres:
                st.info(f"📊 **Nombre d'additifs :** {len(additifs_filtres)} | **Premier :** {additifs_filtres[0]['data'].get('nom','')} | **Dernier :** {additifs_filtres[-1]['data'].get('nom','')}")

            th_a_nom, th_a_emp, th_a_comm, th_a_act = st.columns([2.5, 2.5, 4.0, 1.5])
            with th_a_nom: st.markdown("**Nom additif**")
            with th_a_emp: st.markdown("**Emplacement**")
            with th_a_comm: st.markdown("**Commentaire**")
            with th_a_act: st.markdown("**Actions**")
            st.markdown("<hr style='margin:4px 0px; border-width:2px; border-color:black;'>", unsafe_allow_html=True)
            
            for item in additifs_filtres:
                idx_a = item["index_origine"]; a_data = item["data"]
                tr_a_nom, tr_a_emp, tr_a_comm, tr_a_act = st.columns([2.5, 2.5, 4.0, 1.5])
                with tr_a_nom: st.write(str(a_data.get("nom", "")).title())
                with tr_a_emp: st.write(str(a_data.get("emplacement", "")).title())
                with tr_a_comm: st.write(str(a_data.get("commentaire", "")) or "-")
                with tr_a_act:
                    ca_e, ca_d = st.columns(2)
                    with ca_e:
                        if st.button("✏️", key=f"e_add_{idx_a}"): ouvrir_modif_additif(idx_a, a_data)
                    with ca_d:
                        key_del_a = f"del_confirm_add_{idx_a}"
                        if key_del_a not in st.session_state: st.session_state[key_del_a] = False
                        if not st.session_state[key_del_a]:
                            if st.button("🗑️", key=f"d_add_{idx_a}"): st.session_state[key_del_a] = True; st.rerun()
                        else:
                            if st.button("Confirmer", key=f"d_add_y_{idx_a}", type="primary"):
                                st.session_state.processus_db["preparation_melanges"]["additifs"].pop(idx_a)
                                sauvegarder_donnees(); st.rerun()

    elif choix_section == "🔢 Référentiel des codes RAL":
        if st.button("Ajouter une nuance RAL", type="primary"): ouvrir_ajout_ral_base()
        catalogue_complet_ral = [{"code": code_r, "nom": f"Teinte RAL CLASSIC {code_r}", "visuel": hex_r} for code_r, hex_r in RAL_DICT.items()]
        
        with st.expander("🔍 Filtrer et trier le catalogue complet des RALs", expanded=True):
            r_f1, r_f2, r_f3 = st.columns([2, 2, 1])
            with r_f1: filtre_r_code = st.text_input("Filtrer par Code RAL", "")
            with r_f2: filtre_r_nom = st.text_input("Filtrer par Libellé", "")
            with r_f3: sens_r_tri = st.selectbox("Ordre de tri :", ["Croissant ⬆️", "Décroissant ⬇️"])
            
        rals_filtres = [r for r in catalogue_complet_ral if (filtre_r_code in r["code"]) and (filtre_r_nom.lower() in r["nom"].lower())]
        rals_filtres.sort(key=lambda x: int(x["code"]) if x["code"].isdigit() else x["code"], reverse=(sens_r_tri == "Décroissant ⬇️"))
        
        # BANDEAU D'INFORMATION UNIQUE POUR LE RÉFÉRENTIEL RAL
        if rals_filtres:
            st.info(f"📊 **Nombre de codes RAL :** {len(rals_filtres)} | **Premier :** RAL {rals_filtres[0]['code']} | **Dernier :** RAL {rals_filtres[-1]['code']}")

        th_r_code, th_r_nom, th_r_vis, th_r_act = st.columns([2, 4, 2, 2])
        with th_r_code: st.markdown("**Code RAL**")
        with th_r_nom: st.markdown("**Désignation**")
        with th_r_vis: st.markdown("**Visuel de la teinte**")
        with th_r_act: st.markdown("**Action**")
        st.markdown("<hr style='margin:4px 0px; border-width:2px; border-color:black;'>", unsafe_allow_html=True)
        
        for idx_r, r_data in enumerate(rals_filtres):
            tr_r_code, tr_r_nom, tr_r_vis, tr_r_act = st.columns([2, 4, 2, 2])
            with tr_r_code: st.write(f"<b>RAL {r_data['code']}</b>", unsafe_allow_html=True)
            with tr_r_nom: st.write(r_data['nom'])
            with tr_r_vis: st.markdown(f'<div style="width:50px; height:24px; background-color:{r_data["visuel"]}; border-radius:4px; border:1px solid #1E293B;"></div>', unsafe_allow_html=True)
            with tr_r_act:
                if st.button("Utiliser", key=f"use_ral_{idx_r}_{r_data['code']}"):
                    st.session_state["add_ral"] = r_data['code']
                    st.session_state["add_hex"] = r_data['visuel']
                    st.toast(f"RAL {r_data['code']} copié. Ouvrez l'ajout de couleur !")

    elif choix_section == "⚗️ Formulations d'atelier":
        liste_melanges = st.session_state.processus_db["preparation_melanges"].setdefault("melanges", [])
        if st.button("Créer une fiche de mélange", type="primary"): ouvrir_ajout_melange()
        
        if liste_melanges:
            with st.expander("🔍 Outils de filtrage et de tri de l'atelier de mélanges", expanded=True):
                m_f1, m_f2, m_f3, m_f4, m_f5 = st.columns([1.5, 2, 1.5, 2, 1])
                with m_f1: filtre_m_ref = st.text_input("Filtrer par Référence Mélange", "")
                with m_f2: filtre_m_nom = st.text_input("Filtrer par Nom du Mélange", "")
                with m_f3: filtre_m_emp = st.text_input("Filtrer par Emplacement", "")
                with m_f4: tri_m_colonne = st.selectbox("Trier la table par :", ["Référence", "Nom mélange", "Emplacement", "Commentaire"])
                with m_f5: sens_m_tri = st.selectbox("Ordre table :", ["Croissant ⬆️", "Décroissant ⬇️"])
            
            melanges_filtres = []
            for idx, m in enumerate(liste_melanges):
                if (filtre_m_ref.lower() in str(m.get("ref", "")).lower()) and (filtre_m_nom.lower() in str(m.get("nom", "")).lower()) and (filtre_m_emp.lower() in str(m.get("emplacement", "")).lower()):
                    melanges_filtres.append({"index_origine": idx, "data": m})
            
            mapping_m_cles = {"Référence": "ref", "Nom mélange": "nom", "Emplacement": "emplacement", "Commentaire": "commentaire"}
            melanges_filtres.sort(key=lambda x: [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', str(x["data"].get(mapping_m_cles[tri_m_colonne], "")).lower())], reverse=(sens_m_tri == "Décroissant ⬇️"))

            melanges_couleurs = [item for item in melanges_filtres if item["data"].get("categorie_choisie", "Mélange Couleurs") == "Mélange Couleurs"]
            autres_melanges = [item for item in melanges_filtres if item["data"].get("categorie_choisie", "Mélange Couleurs") != "Mélange Couleurs"]
            
            onglet_c1, onglet_c2 = st.tabs(["🎨 Mélanges Couleurs", "⚙️ Autres Mélanges"])
            
            def afficher_tableau_melanges(liste_m_categorie, identifiant_unique):
                if liste_m_categorie:
                    # BANDEAU D'INFORMATION UNIQUE POUR CHAQUE ONGLET DE MÉLANGES
                    total_mel = len(liste_m_categorie)
                    premier_mel = liste_m_categorie[0]["data"].get("nom", "Aucun")
                    dernier_mel = liste_m_categorie[-1]["data"].get("nom", "Aucun")
                    st.info(f"📊 **Nombre de mélanges :** {total_mel} | **Premier :** {premier_mel} | **Dernier :** {dernier_mel}")
                    
                    th_m_ref, th_m_nom, th_m_vis, th_m_comp, th_m_emp, th_m_com, th_m_act = st.columns([0.8, 1.2, 0.8, 3.2, 1.2, 2.3, 2.5])
                    with th_m_ref: st.markdown("**Référence**")
                    with th_m_nom: st.markdown("**Nom mélange**")
                    with th_m_vis: st.markdown("**Aperçu**")
                    with th_m_comp: st.markdown("**Couleurs & Additifs**")
                    with th_m_emp: st.markdown("**Emplacement**")
                    with th_m_com: st.markdown("**Commentaire**")
                    with th_m_act: st.markdown("**Actions**")
                    st.markdown("<hr style='margin:4px 0px; border-width:2px; border-color:black;'>", unsafe_allow_html=True)
                    
                    for item_m in liste_m_categorie:
                        idx_m = item_m["index_origine"]; melange = item_m["data"]
                        is_verified = melange.get("statut") == "Vérifier"
                        
                        txt_style = "color: #CC0605; font-weight: bold;" if is_verified else "color: inherit;"
                        
                        row_class = "verified-text" if is_verified else "normal-row"
                        st.markdown(f'<div class="{row_class}">', unsafe_allow_html=True)
                        
                        tr_m_ref, tr_m_nom, tr_m_vis, tr_m_comp, tr_m_emp, tr_m_com, tr_m_act = st.columns([0.8, 1.2, 0.8, 3.2, 1.2, 2.3, 2.5])
                        
                        with tr_m_ref: st.markdown(f'<span style="{txt_style}"><b>{str(melange.get("ref", "")).title()}</b></span>', unsafe_allow_html=True)
                        with tr_m_nom: st.markdown(f'<span style="{txt_style}">{str(melange.get("nom", "")).title()}</span>', unsafe_allow_html=True)
                        with tr_m_vis:
                            if melange.get("image_rendu"): afficher_image_base64(melange["image_rendu"]["data"], width=45)
                            else: st.caption("Pas d'image")
                                
                        with tr_m_comp:
                            for t in melange.get("couleurs_associees", []):
                                type_comp = t.get("type", "couleur")
                                if type_comp == "couleur":
                                    st.markdown(f'<div style="display:flex; align-items:center;"><div style="width:14px; height:14px; background-color:{t.get("visuel","#CCCCCC")}; border-radius:50%; margin-right:6px; border:1px solid #333;"></div><span style="{txt_style}">Nuancier : {str(t["nom"]).title()} ➔ <b>{str(t["dosage"]).title()}</b></span></div>', unsafe_allow_html=True)
                                elif type_comp == "melange_base":
                                    st.markdown(f'<div style="display:flex; align-items:center;"><div style="width:14px; height:14px; background-color:#CBD5E1; border-radius:2px; margin-right:6px; border:1px solid #333;"></div><span style="{txt_style}">Base : {str(t["nom"]).title()} ➔ <b>{str(t["dosage"]).title()}</b></span></div>', unsafe_allow_html=True)
                                else:
                                    st.markdown(f'<div style="display:flex; align-items:center;"><span style="{txt_style}">Additif : {str(t["nom"]).title()} ➔ <b>{str(t["dosage"]).title()}</b></span></div>', unsafe_allow_html=True)
                        
                        with tr_m_emp: st.markdown(f'<span style="{txt_style}">{str(melange.get("emplacement", "")).title()}</span>', unsafe_allow_html=True)
                        with tr_m_com: st.markdown(f'<span style="{txt_style}">{str(melange.get("commentaire", "")) or "-"}</span>', unsafe_allow_html=True)
                        
                        with tr_m_act:
                            col_me1, col_me2, col_me3 = st.columns([1, 1, 2])
                            with col_me1:
                                if st.button("✏️", key=f"edit_m_{identifiant_unique}_{idx_m}"): ouvrir_modification_melange(idx_m, melange)
                            with col_me2:
                                key_del_m = f"del_confirm_mel_{identifiant_unique}_{idx_m}"
                                if key_del_m not in st.session_state: st.session_state[key_del_m] = False
                                if not st.session_state[key_del_m]:
                                    if st.button("🗑️", key=f"del_mel_{identifiant_unique}_{idx_m}"): st.session_state[key_del_m] = True; st.rerun()
                                else:
                                    c_del1, c_del2 = st.columns(2)
                                    with c_del1:
                                        if st.button("Oui", key=f"del_mel_y_{identifiant_unique}_{idx_m}", type="primary"):
                                            st.session_state.processus_db["preparation_melanges"]["melanges"].pop(idx_m)
                                            sauvegarder_donnees(); st.rerun()
                                    with c_del2:
                                        if st.button("Non", key=f"del_mel_n_{identifiant_unique}_{idx_m}"):
                                            st.session_state[key_del_m] = False; st.rerun()
                            with col_me3:
                                key_detail = f"show_detail_{identifiant_unique}_{idx_m}"
                                if key_detail not in st.session_state: st.session_state[key_detail] = False
                                if st.button("Détails", key=f"btn_det_{identifiant_unique}_{idx_m}", use_container_width=True):
                                    st.session_state[key_detail] = not st.session_state[key_detail]
                                    st.rerun()
                                    
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        if st.session_state.get(f"show_detail_{identifiant_unique}_{idx_m}", False):
                            st.markdown("<div style='background-color: rgba(226, 232, 240, 0.4); padding: 15px; border-radius: 5px; margin-top: 5px; color: black !important;'>", unsafe_allow_html=True)
                            st.markdown(f"<h4 style='color:black;'>FICHE TECHNIQUE COMPOSANTS POUR : {str(melange.get('nom')).upper()}</h4>", unsafe_allow_html=True)
                            if melange.get("image_rendu"): afficher_image_base64(melange["image_rendu"]["data"], width=300)
                            for t in melange.get("couleurs_associees", []):
                                if t.get("type", "couleur") == "couleur":
                                    orig = next((x for x in liste_couleurs if x["ref"] == t["ref"]), None)
                                    st.markdown(f"• <span style='color:black;'><b>Couleur : {orig['nom_actuel'] if orig else t['nom']}</b> | Réf: `{t['ref']}`</span>", unsafe_allow_html=True)
                                elif t.get("type") == "melange_base":
                                    st.markdown(f"• <span style='color:black;'><b>Sous-mélange de base : {t['nom']}</b> | Réf: `{t['ref']}`</span>", unsafe_allow_html=True)
                                else:
                                    st.markdown(f"• <span style='color:black;'><b>Additif : {t['nom']}</b></span>", unsafe_allow_html=True)
                            st.markdown("</div>", unsafe_allow_html=True)
                        st.markdown("<hr style='margin:4px 0px; opacity:0.2;'>", unsafe_allow_html=True)

            with onglet_c1: afficher_tableau_melanges(melanges_couleurs, "cat_colors")
            with onglet_c2: afficher_tableau_melanges(autres_melanges, "cat_others")

    elif choix_section == "📐 Fiches Méthode":
        @st.dialog("⚙️ Administrer le bloc de méthode", width="large")
        def ouvrir_edition_bloc_methode(idx_fiche, idx_forme, forme_data):
            shapes_keys = ["box", "circle", "diamond", "hexagon"]
            n_shape = st.selectbox("Forme géométrique", shapes_keys, index=shapes_keys.index(forme_data["shape"]) if forme_data["shape"] in shapes_keys else 0)
            raw_label = forme_data["label"].split("\n")[0]
            raw_dosage = forme_data["label"].split("\n")[1].replace("(", "").replace(")", "") if "\n" in forme_data["label"] else ""
            n_nature = st.radio("Nature", ["Titre Formule", "Composant"], index=0 if "\n" not in forme_data["label"] else 1)
            n_txt = st.text_input("Libellé / Texte", value=raw_label)
            n_dos = st.text_input("Dosage / Spécification", value=raw_dosage)
            n_color = st.color_picker("Couleur du bloc", value=forme_data.get("color", "#E0F2FE"))
            
            if st.button("Enregistrer les modifications", type="primary"):
                lbl_final = n_txt.upper() if n_nature == "Titre Formule" else n_txt
                if n_nature == "Composant" and n_dos: lbl_final += f"\n({n_dos})"
                st.session_state.processus_db["preparation_melanges"]["fiches_methode"][idx_fiche]["formes"][idx_forme].update({"shape": n_shape, "label": lbl_final, "color": n_color})
                sauvegarder_donnees(); st.rerun()

        if "click_node_id" in query_params and "click_fiche_idx" in query_params:
            try:
                c_nid = int(query_params["click_node_id"])
                c_fidx = int(query_params["click_fiche_idx"])
                st.query_params.clear()
                if c_fidx < len(fiches_m):
                    for idx_shape, s in enumerate(fiches_m[c_fidx]["formes"]):
                        if s["id"] == c_nid: ouvrir_edition_bloc_methode(c_fidx, idx_shape, s)
            except Exception: pass

        if st.button("Créer une Fiche Méthode (Page vierge)", type="primary"): ouvrir_ajout_fiche_methode()
        if fiches_m:
            noms_fiches = [f["nom"] for f in fiches_m]
            fiche_choisie_nom = st.selectbox("Fiche Méthode active :", noms_fiches)
            idx_fid = noms_fiches.index(fiche_choisie_nom)
            fiche = fiches_m[idx_fid]

            # BANDEAU D'INFORMATION UNIQUE POUR LES FICHES METHODES
            st.info(f"📊 **Nombre de fiches méthode :** {len(fiches_m)} | **Première :** {fiches_m[0]['nom']} | **Dernière :** {fiches_m[-1]['nom']}")

            col_outils, col_canvas = st.columns([1, 2])
            with col_outils:
                with st.expander("Ajouter un Bloc", expanded=True):
                    type_f = st.selectbox("Forme", ["box", "circle", "diamond", "hexagon"])
                    nature = st.radio("Contenu", ["Titre Formule", "Composant"])
                    txt_p = st.text_input("Nom / Libellé")
                    dos_p = st.text_input("Dosage")
                    c_bg = st.color_picker("Couleur", "#E0F2FE")
                    if st.button("Injecter sur la page", use_container_width=True):
                        if txt_p:
                            lbl = txt_p.upper() if nature == "Titre Formule" else txt_p
                            if nature == "Composant" and dos_p: lbl += f"\n({dos_p})"
                            fiche["formes"].append({"id": len(fiche["formes"]) + 1, "shape": type_f, "label": lbl, "color": c_bg, "x": None, "y": None})
                            sauvegarder_donnees(); st.rerun()

                if len(fiche["formes"]) >= 2:
                    with st.expander("Lier des blocs", expanded=True):
                        names = [f["label"].replace('\n', ' ') for f in fiche["formes"]]
                        f_src = st.selectbox("De :", names, key="src")
                        f_dst = st.selectbox("Vers :", names, key="dst")
                        if st.button("Lier les blocs", use_container_width=True):
                            id_src = next(f["id"] for f in fiche["formes"] if f["label"].replace('\n', ' ') == f_src)
                            id_dst = next(f["id"] for f in fiche["formes"] if f["label"].replace('\n', ' ') == f_dst)
                            if id_src != id_dst:
                                fiche["liaisons"].append({"from": id_src, "to": id_dst})
                                sauvegarder_donnees(); st.rerun()

            with col_canvas:
                list_nodes = []
                for f in fiche["formes"]:
                    node_dict = {"id": f["id"], "label": f["label"], "shape": f["shape"], "color": {"background": f.get("color", "#E0F2FE"), "border": "#1E293B"}, "margin": 10}
                    if f.get("x") is not None and f.get("y") is not None:
                        node_dict["x"] = f["x"]; node_dict["y"] = f["y"]
                    list_nodes.append(node_dict)

                vis_html = f"""
                <div id="mynetwork" style="width: 100%; height: 580px; background-color: #FAFAFA; border: 2px dashed #CBD5E1; border-radius: 8px;"></div>
                <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
                <script type="text/javascript">
                  var container = document.getElementById('mynetwork');
                  var options = {{ physics: {{ enabled: false }}, interaction: {{ dragNodes: true, dragView: false, zoomView: true }}, nodes: {{ font: {{ size: 14, face: 'Arial' }}, borderWidth: 2 }} }};
                  var network = new vis.Network(container, {{ nodes: new vis.DataSet({json.dumps(list_nodes)}), edges: new vis.DataSet({json.dumps([{"from": l["from"], "to": l["to"], "arrows": "to", "color": {"color": "#475569"}} for l in fiche["liaisons"]])}) }}, options);
                  
                  network.on("doubleClick", function (params) {{
                     if (params.nodes.length > 0) {{
                        window.parent.location.search = "?click_node_id=" + params.nodes[0] + "&click_fiche_idx=" + {idx_fid};
                     }}
                  }});
                  network.on("dragEnd", function (params) {{
                     if (params.nodes.length > 0) {{
                        var nodeId = params.nodes[0];
                        var pos = network.getPositions([nodeId])[nodeId];
                        window.parent.location.search = "?moved_id=" + nodeId + "&moved_idx=" + {idx_fid} + "&moved_x=" + pos.x + "&moved_y=" + pos.y;
                     }}
                  }});
                </script>
                """
                components.html(vis_html, height=600)