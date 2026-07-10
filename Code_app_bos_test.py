import streamlit as st
import json
import os
import base64
from PIL import Image
import io
import re
import datetime
import random 
import streamlit.components.v1 as components

# --- CONFIGURATION INITIALE DE LA PAGE ---
st.set_page_config(
    page_title="BOS2 - Gestion Industrielle",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INITIALISATION DES ÉTATS DE SESSION ---
if "etat_sidebar" not in st.session_state: st.session_state.etat_sidebar = "expanded"
if "mode_sombre" not in st.session_state: st.session_state.mode_sombre = False
if "logged_in" not in st.session_state: st.session_state.logged_in = False  # <- NOUVEAU : État de connexion

# =========================================================
# SYSTÈME DE CONNEXION (LOGIN)
# =========================================================
def afficher_page_connexion():
    """Affiche une page de connexion centrée et sécurisée."""
    
    # CSS spécifique pour centrer la boîte de login
    st.markdown("""
    <style>
    .login-box {
        max-width: 400px;
        margin: 10vh auto;
        padding: 40px;
        background-color: #F4F1EA;
        border-radius: 8px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        border: 1px solid #E2E8F0;
        text-align: center;
    }
    /* Si mode sombre activé, on adapte la boîte de login */
    @media (prefers-color-scheme: dark) {
        .login-box { background-color: #070b12; border-color: #334155; }
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    
    # Affichage du logo sur la page de connexion s'il existe
    logo_path = os.path.join(os.getcwd(), "Martineau logo.png")
    if os.path.exists(logo_path):
        st.image(logo_path, width=200)
    
    st.markdown("<h2>Connexion BOS2</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b; margin-bottom: 20px;'>Veuillez vous identifier pour accéder au portail.</p>", unsafe_allow_html=True)
    
    with st.form("formulaire_connexion"):
        identifiant = st.text_input("Identifiant")
        mot_de_passe = st.text_input("Mot de passe", type="password")
        submit = st.form_submit_button("Se connecter", use_container_width=True)
        
        if submit:
            # --- VÉRIFICATION DES IDENTIFIANTS ---
            # Pour l'instant on utilise un dictionnaire en dur. 
            # Plus tard, cela sera connecté à ta base de données SQL.
            utilisateurs_valides = {
                "admin": "bos2024",
                "labo": "labo123",
                "atelier": "atelier123"
            }
            
            if identifiant in utilisateurs_valides and utilisateurs_valides[identifiant] == mot_de_passe:
                st.session_state.logged_in = True
                st.session_state.current_user = identifiant
                st.success("Connexion réussie !")
                st.rerun()
            else:
                st.error("Identifiant ou mot de passe incorrect.")
                
    st.markdown('</div>', unsafe_allow_html=True)

# 🛑 LE VIDEUR : Si non connecté, on affiche le login et on STOPPE le script.
if not st.session_state.logged_in:
    afficher_page_connexion()
    st.stop()  # Empêche l'exécution du reste de l'application !

# =========================================================
# L'APPLICATION PRINCIPALE COMMENCE ICI (Si connecté)
# =========================================================

st.markdown("""
<style>
/* 1. Typographie Raffinée */
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;1,400&family=Inter:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
h1, h2, h3 { font-family: 'Playfair Display', serif !important; color: #1E293B; }

/* 2. Animations d'entrée */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(5px); }
    to { opacity: 1; transform: translateY(0); }
}

[data-testid="stDialog"] { animation: fadeIn 0.3s ease-out; }
.stApp { animation: fadeIn 0.6s ease-out; }

/* 3. Boutons : Noir au clic / Blanc au repos */
div[data-testid="stButton"] > button {
    background-color: #FFFFFF !important;
    color: #000000 !important;
    border: 1px solid #000000 !important;
    transition: all 0.2s ease-in-out !important;
    border-radius: 0px !important; /* Style Old Money anguleux */
}

div[data-testid="stButton"] > button:hover, 
div[data-testid="stButton"] > button:active {
    background-color: #000000 !important;
    color: #FFFFFF !important;
    transform: translateY(-2px);
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

/* 4. Effet de survol sur les tableaux et expanders */
.stExpander:hover { border-color: #000000 !important; }
</style>
""", unsafe_allow_html=True)

# Essayer d'importer ReportLab pour la génération du PDF standard
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas
    REPORTLAB_DISPO = True
except ImportError:
    REPORTLAB_DISPO = False

OPTIONS_REDACTEURS = ["Labo / R&D", "Atelier: couleurs", "Atelier: perles/croix", "Atelier: pose peinture", "Atelier: moulage", "Atelier: résine", "Atelier: finition", "Atelier: assemblage"]
MAX_LIGNES_AFFICHAGE = 200

# Dans tes modules, enveloppe ton contenu :
with st.container():
    st.markdown('<div class="main-content">', unsafe_allow_html=True)

FICHIER_SAUVEGARDE = "donnees_bos2.json"

# --- UTILITAIRES & CALLBACKS D'ÉTAT ---
def get_svg_icon(icon_name):
    icons = {
        "search": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>',
        "chart": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>'
    }
    return icons.get(icon_name, "")

@st.cache_data 
def encoder_image_systeme(nom_fichier):
    if os.path.exists(nom_fichier):
        try:
            with open(nom_fichier, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception:
            return ""
    return ""

LOGO_BACKGROUND_BASE64 = encoder_image_systeme("Logo-Beraudy-rectangle.png")

if LOGO_BACKGROUND_BASE64:
    st.markdown(f"""
    <style>
    [data-testid="stAppViewContainer"]::before {{
        content: ""; 
        position: absolute; top: 0; left: 0; right: 0; bottom: 0;
        background-image: url("data:image/png;base64,{LOGO_BACKGROUND_BASE64}");
        background-size: 45%;
        background-repeat: no-repeat;
        background-position: center center;
        background-attachment: fixed;
        opacity: 0.04;
        z-index: 0;
        pointer-events: none;
    }}
    [data-testid="stHeader"], [data-testid="stVerticalBlock"], .stMain {{ 
        position: relative; 
        z-index: 1; 
        background-color: transparent !important; 
    }}
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURATION DU MODE SOMBRE DYNAMIQUE ---
IMAGE_BG_DARK = "ton_image_sombre.png" 

if st.session_state.mode_sombre:
    img_b64 = encoder_image_systeme(IMAGE_BG_DARK)
    st.markdown(f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-color: #0F172A !important;
        background-image: url("data:image/png;base64,{img_b64}") !important;
        background-size: cover !important;
        background-position: center !important;
    }}
    h1, h2, h3, p, label, span, div, .stMarkdown {{
        color: #FFFFFF !important;
    }}
    div[data-testid="stButton"] > button {{
        background-color: transparent !important;
        color: #FFFFFF !important;
        border: 1px solid #FFFFFF !important;
    }}
    </style>
    """, unsafe_allow_html=True)

def encoder_fichier_local(uploaded_file):
    try:
        bytes_data = uploaded_file.getvalue()
        return {"name": uploaded_file.name, "mime": uploaded_file.type, "data": base64.b64encode(bytes_data).decode("utf-8")}
    except Exception as e:
        st.error(f"Erreur lors de l'encodage de l'image : {e}")
        return None

def afficher_image_base64(base64_string, width=None):
    try:
        st.image(Image.open(io.BytesIO(base64.b64decode(base64_string))), use_container_width=True if width is None else False, width=width)
    except Exception as e:
        st.error(f"Erreur d'image : {e}")

def interpreter_texte_avec_images(texte, images_en_ligne=None):
    if not texte: return ""
    st.markdown(texte, unsafe_allow_html=True)

def est_dosage_valide(txt_dosage):
    if not txt_dosage: return False
    clean = str(txt_dosage).strip().lower()
    return clean not in ["", "0", "0g", "0 g", "0ml", "0 ml", "none"]

def gerer_historique_dates(ancien_dict, date_edition_str):
    date_crea = ancien_dict.get("date_creation", date_edition_str)
    derniere_maj = ancien_dict.get("date_derniere_maj", date_edition_str)
    avant_derniere_maj = ancien_dict.get("date_avant_derniere_maj", "-")
    if list(derniere_maj)[:10] != list(date_edition_str)[:10]:
        avant_derniere_maj = derniere_maj
        derniere_maj = date_edition_str
    return date_crea, derniere_maj, avant_derniere_maj

def nettoyer_valeur_pdf(val):
    if val is None: return "-"
    s = str(val).strip()
    return s if s != "" else "-"

def generer_fichier_export(donnees_list, nom_fichier="export"):
    if not donnees_list: return None, None, None
    import io
    if "Couleurs" in nom_fichier:
        colonnes_map = {'ref': 'Référence', 'nom_actuel': 'Nom', 'nom_futur': 'Futur nom', 'ral': 'RAL', 'societe': 'Société', 'type': 'Type'}
    elif "Elements" in nom_fichier:
        colonnes_map = {'nom': 'Nom', 'code': 'Code', 'designation': 'Désignation', 'fournisseur': 'Fournisseur', 'sous_groupe': 'Sous-groupe', 'commentaire': 'Commentaire'}
    elif "Melanges" in nom_fichier:
        colonnes_map = {'ref': 'Référence', 'nom': 'Nom', 'emplacement': 'Emplacement', 'commentaire': 'Commentaire'}
    else: colonnes_map = None

    donnees_propres = []
    colonnes_dynamiques_melange = []
    for row in donnees_list:
        row_propre = {}
        if colonnes_map:
            for cle_dict, nom_colonne in colonnes_map.items():
                row_propre[nom_colonne] = str(row.get(cle_dict, ""))
            if "Couleurs" not in nom_fichier and "Elements" not in nom_fichier and "Melanges" in nom_fichier and "couleurs_associees" in row and isinstance(row["couleurs_associees"], list):
                for i, composant in enumerate(row["couleurs_associees"]):
                    col_nom, col_dos = f"Composant {i+1}", f"Dosage {i+1}"
                    row_propre[col_nom] = composant.get("nom", "Inconnu")
                    row_propre[col_dos] = composant.get("dosage", "-")
                    if col_nom not in colonnes_dynamiques_melange: colonnes_dynamiques_melange.extend([col_nom, col_dos])
            if "Elements" in nom_fichier: row_propre["Compartiments"] = ", ".join(row.get("compartiments", []))
        else: row_propre = {k: (str(v) if isinstance(v, (dict, list)) else v) for k, v in row.items()}
        donnees_propres.append(row_propre)

    colonnes_finales = list(colonnes_map.values()) + colonnes_dynamiques_melange if colonnes_map else list({k for r in donnees_propres for k in r.keys()})

    try:
        import pandas as pd
        df = pd.DataFrame(donnees_propres).reindex(columns=colonnes_finales)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer: df.to_excel(writer, index=False, sheet_name='Export')
        return buffer.getvalue(), f"{nom_fichier}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    except ImportError:
        import csv
        buffer = io.StringIO()
        if donnees_propres:
            writer = csv.DictWriter(buffer, fieldnames=colonnes_finales, extrasaction='ignore', delimiter=';')
            writer.writeheader()
            for row in donnees_propres: writer.writerow(row)
        return buffer.getvalue().encode('utf-8-sig'), f"{nom_fichier}.csv", "text/csv"

def add_tmp_item(state_dict_name, k, data):
    if state_dict_name in st.session_state: st.session_state[state_dict_name][k] = data

def remove_tmp_item_cb(state_dict_name, widget_key, dict_key):
    if state_dict_name in st.session_state:
        if not st.session_state.get(widget_key, True): st.session_state[state_dict_name].pop(dict_key, None)

class NumeroteurDePages(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumeroteurDePages, self).__init__(*args, **kwargs)
        self.pages = []
    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()
    def save(self):
        num_pages = len(self.pages)
        for page in self.pages:
            self.__dict__.update(page)
            if num_pages > 1:
                self.setFont("Helvetica", 8)
                self.setFillColor(colors.HexColor('#64748B'))
                self.drawRightString(612 - 40, 20, f"Page {self._pageNumber} sur {num_pages}")
            super(NumeroteurDePages, self).showPage()
        super(NumeroteurDePages, self).save()

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
                prep.setdefault("compartiments", ["résine", "peinture"])
                prep.setdefault("sous_groupes", ["Général"])
                return donnees
        except Exception:
            pass
    return {"creation_processus": {}, "preparation_melanges": {"couleurs": [], "melanges": [], "fiches_methode": [], "additifs": [], "base_rals": [], "compartiments": ["résine", "peinture"], "sous_groupes": ["Général"]}}

def sauvegarder_donnees():
    with open(FICHIER_SAUVEGARDE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.processus_db, f, ensure_ascii=False, indent=4)

if "processus_db" not in st.session_state: st.session_state.processus_db = charger_donnees()
if "groupe_actif" not in st.session_state: st.session_state.groupe_actif = None
if "produit_selectionne" not in st.session_state: st.session_state.produit_selectionne = None
if "sub_section_melange" not in st.session_state: st.session_state.sub_section_melange = "🎨 Nuancier de couleurs"

def generer_pdf_fiche_technique(data_obj, type_ft="melange"):
    buffer = io.BytesIO()
    if not REPORTLAB_DISPO:
        buffer.write(b"ReportLab non disponible.")
        buffer.seek(0)
        return buffer

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []

    title_style = ParagraphStyle('TitleStyle', fontName='Helvetica-Bold', fontSize=18, textColor=colors.HexColor('#CC0605'), alignment=2, spaceBefore=15)
    h2_style = ParagraphStyle('H2Style', fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#1E293B'), spaceBefore=8, spaceAfter=4)
    body_style = ParagraphStyle('BodyStyle', fontName='Helvetica', fontSize=8, leading=11, textColor=colors.HexColor('#334155'))
    body_bold = ParagraphStyle('BodyBold', fontName='Helvetica-Bold', fontSize=8, leading=11, textColor=colors.HexColor('#1E293B'))

    titre_principal = "FICHE TECHNIQUE PRODUIT" if type_ft == "melange" else "FICHE TECHNIQUE COULEUR" if type_ft == "couleur" else "FICHE TECHNIQUE ÉLÉMENT"
    header_data = [["", Paragraph(titre_principal, title_style)]]
    header_table = Table(header_data, colWidths=[170, 330])
    
    img_path = "Logo-Beraudy-rectangle.png"
    if os.path.exists(img_path):
        from reportlab.platypus import Image as RLImage
        img_rl = RLImage(img_path, width=215, height=56)
        img_rl.hAlign = 'LEFT'
        header_table._cellvalues[0][0] = img_rl

    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LINEBELOW', (0,0), (-1,-1), 1, colors.HexColor('#CC0605'))
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))

    ft_data = data_obj.get("fiche_technique", {})

    story.append(Paragraph("Informations Générales", h2_style))
    if type_ft == "melange":
        titre_melange = data_obj.get("nom", "-") + (" <font color='#CC0605'>🔴</font>" if data_obj.get("statut") == "Vérifier" else "")
        infos_rows = [
            [Paragraph("<b>Nom du Mélange :</b>", body_style), Paragraph(titre_melange, body_style)],
            [Paragraph("<b>Référence interne :</b>", body_style), Paragraph(nettoyer_valeur_pdf(data_obj.get("ref")), body_style)],
            [Paragraph("<b>Stockage / Emplacement :</b>", body_style), Paragraph(nettoyer_valeur_pdf(data_obj.get("emplacement")), body_style)]
        ]
    elif type_ft == "couleur":
        infos_rows = [
            [Paragraph("<b>Nom actuel :</b>", body_style), Paragraph(nettoyer_valeur_pdf(data_obj.get("nom_actuel")), body_style)],
            [Paragraph("<b>Référence :</b>", body_style), Paragraph(nettoyer_valeur_pdf(data_obj.get("ref")), body_style)],
            [Paragraph("<b>Futur nom :</b>", body_style), Paragraph(nettoyer_valeur_pdf(data_obj.get("nom_futur")), body_style)],
            [Paragraph("<b>Code RAL :</b>", body_style), Paragraph(nettoyer_valeur_pdf(data_obj.get("ral")), body_style)],
            [Paragraph("<b>Société :</b>", body_style), Paragraph(nettoyer_valeur_pdf(data_obj.get("societe")), body_style)],
            [Paragraph("<b>Type :</b>", body_style), Paragraph(nettoyer_valeur_pdf(data_obj.get("type")), body_style)]
        ]
    else:
        titre_element = data_obj.get("nom", "-") + (" <font color='#CC0605'>🔴</font>" if data_obj.get("statut") == "Vérifier" else "")
        infos_rows = [
            [Paragraph("<b>Nom de l'élément :</b>", body_style), Paragraph(titre_element, body_style)],
            [Paragraph("<b>Code :</b>", body_style), Paragraph(nettoyer_valeur_pdf(data_obj.get("code")), body_style)],
            [Paragraph("<b>Désignation :</b>", body_style), Paragraph(nettoyer_valeur_pdf(data_obj.get("designation")), body_style)],
            [Paragraph("<b>Fournisseur :</b>", body_style), Paragraph(nettoyer_valeur_pdf(data_obj.get("fournisseur")), body_style)],
            [Paragraph("<b>Code Article Achat :</b>", body_style), Paragraph(nettoyer_valeur_pdf(data_obj.get("code_article")), body_style)]
        ]
    
    t_infos = Table(infos_rows, colWidths=[150, 350])
    t_infos.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1'))
    ]))
    story.append(t_infos)
    story.append(Spacer(1, 8))

    story.append(Paragraph("Spécifications Techniques", h2_style))
    if "champs_ft" in ft_data:
        liste_champs = ft_data["champs_ft"]
    else:
        liste_champs = [
            {"nom": "Aspect", "valeur": ft_data.get("aspect", "-")},
            {"nom": "Viscosité", "valeur": ft_data.get("viscosite", "-")},
            {"nom": "Densité", "valeur": ft_data.get("densite", "-")},
            {"nom": "Séchage", "valeur": ft_data.get("sechage", "-")},
            {"nom": "Conditions", "valeur": ft_data.get("conditions", "-")}
        ]
        liste_champs = [c for c in liste_champs if c['valeur'] != "-" and c['valeur'] != ""]

    spec_rows = []
    for i in range(0, len(liste_champs), 2):
        row = [
            Paragraph(f"<b>{liste_champs[i]['nom']} :</b>", body_style), 
            Paragraph(nettoyer_valeur_pdf(liste_champs[i]['valeur']), body_style)
        ]
        if i + 1 < len(liste_champs):
            row.extend([
                Paragraph(f"<b>{liste_champs[i+1]['nom']} :</b>", body_style), 
                Paragraph(nettoyer_valeur_pdf(liste_champs[i+1]['valeur']), body_style)
            ])
        else:
            row.extend(["", ""])
        spec_rows.append(row)

    if spec_rows:
        t_spec = Table(spec_rows, colWidths=[110, 140, 110, 140])
        t_spec.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFFFF')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0'))
        ]))
        story.append(t_spec)
        story.append(Spacer(1, 8))

    doc.build(story, canvasmaker=NumeroteurDePages)
    buffer.seek(0)
    return buffer

def editeur_champs_dynamiques(fiche_data):
    if "champs_ft" not in fiche_data:
        fiche_data["champs_ft"] = [{"nom": k.capitalize(), "valeur": v} for k, v in fiche_data.items() 
                                   if k in ["aspect", "viscosite", "densite", "sechage", "conditions"]]
    
    st.markdown("##### ⚙️ Spécifications techniques")
    for i, champ in enumerate(fiche_data["champs_ft"]):
        col1, col2, col3 = st.columns([2, 3, 1])
        with col1: champ["nom"] = st.text_input(f"Champ", value=champ["nom"], key=f"nom_{i}_{hash(str(fiche_data))}")
        with col2: champ["valeur"] = st.text_input(f"Valeur", value=champ["valeur"], key=f"val_{i}_{hash(str(fiche_data))}")
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️", key=f"del_{i}_{hash(str(fiche_data))}"):
                fiche_data["champs_ft"].pop(i)
                st.rerun()

    if st.button("➕ Ajouter un champ"):
        fiche_data["champs_ft"].append({"nom": "Nouveau", "valeur": ""})
        st.rerun()

@st.dialog("📄 Visualisation Fiche Technique", width="large")
def ouvrir_visualisation_ft(melange):
    st.markdown(f"### 📄 Fiche Technique : {melange.get('nom')}")
    ft = melange.get("fiche_technique", {})
    st.info(f"📅 **Création :** {ft.get('date_creation','-')} | 🔄 **Dernière MÀJ :** {ft.get('date_derniere_maj','-')} | ⏳ **Avant-dernière MÀJ :** {ft.get('date_avant_derniere_maj','-')}")
    
    col_visu, col_actions = st.columns([1, 2])
    with col_visu:
        if "image_rendu" in melange and melange["image_rendu"]:
            afficher_image_base64(melange["image_rendu"]["data"], width=150)
    with col_actions:
        st.markdown("**Actions :**")
        c1, c2, c3 = st.columns(3)
        nom_telechargement = f"FT_produit_{melange.get('nom', 'inconnu')}_{melange.get('ref', 'vide')}.pdf".replace(" ", "_")
        c1.download_button("⬇️ PDF", data=generer_pdf_fiche_technique(melange, "melange"), file_name=nom_telechargement, mime="application/pdf", use_container_width=True)

@st.dialog("👁️ Détails de la couleur", width="large")
def ouvrir_details_couleur(couleur):
    st.markdown(f"### 🎨 {couleur.get('nom_actuel')} ({couleur.get('ref')})")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Nom Futur :** {couleur.get('nom_futur', '-')}")
        st.markdown(f"**Code RAL :** {couleur.get('ral', '-')}")
    with col2:
        st.markdown(f'<div style="width:120px; height:120px; background-color:{couleur.get("visuel", "#3B82F6")}; border-radius:12px; border:2px solid #1E293B;"></div>', unsafe_allow_html=True)
    if st.button("Fermer la vue", use_container_width=True): st.rerun()

@st.dialog("👁️ Détails de l'élément", width="large")
def ouvrir_details_element(element):
    st.markdown(f"### 🧪 {element.get('nom')} ({element.get('code')})")
    st.markdown(f"**Désignation :** {element.get('designation', '-')}")
    st.markdown(f"**Fournisseur :** {element.get('fournisseur', '-')}")
    if st.button("Fermer la vue", use_container_width=True): st.rerun()

@st.dialog("👁️ Détails complets du mélange", width="large")
def ouvrir_details_melange(melange):
    st.markdown(f"### 🧪 {melange.get('nom')} ({melange.get('ref')})")
    st.markdown(f"**Emplacement:** {melange.get('emplacement', 'Non défini')}")
    st.markdown(f"**État:** {melange.get('statut', 'Non défini')}")
    if st.button("Fermer la vue", use_container_width=True): st.rerun()

@st.dialog("➕ Créer une nouvelle fiche méthode", width="large")
def ouvrir_ajout_fiche_methode():
    nom = st.text_input("Nom de la fiche méthode")
    if st.button("Créer la fiche", type="primary"):
        if nom:
            st.session_state.processus_db["preparation_melanges"]["fiches_methode"].append({"nom": nom, "formes": [], "liaisons": []})
            sauvegarder_donnees()
            st.rerun()

@st.dialog("➕ Ajouter une étape", width="large")
def ouvrir_formulaire_etape(groupe, prod):
    titre = st.text_input("Titre de l'étape")
    description = st.text_area("Description de l'étape")
    if st.button("Enregistrer l'étape", type="primary"):
        if titre:
            if "etapes" not in st.session_state.processus_db[groupe][prod]:
                st.session_state.processus_db[groupe][prod]["etapes"] = []
            st.session_state.processus_db[groupe][prod]["etapes"].append({"titre": titre, "description": description, "is_local": False})
            sauvegarder_donnees()
            st.rerun()

@st.dialog("❓ Centre d'Aide Intégré BOS2", width="large")
def ouvrir_fenetre_aide():
    onglets = st.tabs([
        "📖 Premiers pas", "🎨 Processus & Couleurs", "⚗️ Formulations & FT", 
        "❓ FAQ", "⚠ Dépannage", "📞 Support & Versions"
    ])
    
    with onglets[0]: st.write("Bienvenue dans le centre de formation de votre application industrielle.")
    
    with onglets[3]:
        st.markdown("### ❓ Foire Aux Questions (FAQ)")
        faq_data = {
            "Démarrage & Navigation": {
                "Comment changer la langue du logiciel ?": "Actuellement, BOS2 est disponible uniquement en français. Une version multilingue est prévue dans les mises à jour futures.",
                "Comment revenir à l'accueil ?": "Cliquez sur le bouton 'Menu Principal / Retour' situé dans la barre latérale gauche.",
                "Est-ce que je peux ouvrir deux onglets BOS2 ?": "Oui, mais attention : si vous modifiez la même donnée dans deux onglets, la dernière sauvegarde écrasera la première.",
                "Comment rafraîchir les données ?": "Utilisez le bouton de rafraîchissement de votre navigateur (F5) ou retournez au menu principal.",
                "Le logiciel est-il compatible tablette ?": "Oui, le design est responsive. Utilisez le 'Mode Grand Écran' pour une meilleure expérience tactile.",
                "Où voir ma version actuelle ?": "La version est affichée dans l'onglet 'Support & Versions' de ce centre d'aide.",
                "Comment masquer la barre latérale ?": "Utilisez la flèche en haut à gauche de la barre latérale pour la réduire et gagner de l'espace.",
                "Comment faire une recherche rapide ?": "Appuyez sur 'Ctrl+F' pour rechercher un élément textuel dans la page courante.",
                "La session se ferme-t-elle automatiquement ?": "Oui, par mesure de sécurité, après 60 minutes d'inactivité.",
                "Puis-je changer la taille de police ?": "Le zoom du navigateur (Ctrl + +/-) est la méthode recommandée."
            },
            "Gestion des Couleurs & RAL": {
                "Pourquoi mon RAL est-il affiché en noir ?": "Cela signifie que la valeur hexadécimale associée dans votre base est #000000, vérifiez sa configuration.",
                "Puis-je créer des RAL personnalisés ?": "Oui, utilisez le référentiel 'Référentiel des codes RAL' pour ajouter vos propres nuances.",
                "Peut-on supprimer une couleur utilisée ?": "Le système vous alertera si elle est liée à un mélange. Il est préférable de la renommer ou de la passer en 'Inactif'.",
                "La couleur est-elle liée à un client ?": "Oui, via le champ 'Société' lors de la création de la couleur.",
                "Pourquoi ma couleur n'apparaît pas dans le nuancier ?": "Vérifiez que vous n'avez pas activé un filtre textuel qui masque vos résultats.",
                "Puis-je dupliquer une couleur ?": "Oui, ouvrez la couleur, notez ses paramètres, créez-en une nouvelle et copiez les valeurs.",
                "Que faire en cas d'erreur de frappe sur une référence ?": "Modifiez la référence via l'icône crayon ✏️. La modification est instantanée.",
                "Comment trier les couleurs par type ?": "Utilisez le menu déroulant 'Trier par' au-dessus de la table des couleurs.",
                "Le code RAL est-il obligatoire ?": "Non, mais fortement recommandé pour la standardisation industrielle.",
                "Où sont stockées les images des couleurs ?": "Elles sont encodées en base64 directement dans le fichier json."
            },
            "Mélanges & Formulations": {
                "Quelle est la différence entre Mélange et Composant ?": "Un composant est une matière première (additif) ; un mélange est une recette assemblée de composants.",
                "Puis-je mélanger deux mélanges ?": "Oui, utilisez la catégorie 'Mélanges existants (Bases)'.",
                "Pourquoi mon dosage est en rouge ?": "C'est une alerte de sécurité ou une erreur de formatage dans le champ dosage.",
                "Comment calculer le poids total d'un mélange ?": "Le logiciel calcule la somme des dosages saisis automatiquement.",
                "Puis-je modifier un mélange après validation ?": "Oui, mais cela remettra le statut à 'Pas vérifié' pour sécurité.",
                "Comment ajouter une photo à mon mélange ?": "Lors de l'édition, utilisez le champ d'upload d'image dédié au mélange.",
                "Le dosage en pourcentage est-il géré ?": "Oui, saisissez simplement le signe % dans le champ dosage.",
                "Peut-on imprimer une étiquette de mélange ?": "La génération PDF sert de base, vous pouvez imprimer ce PDF.",
                "Pourquoi le bouton 'Enregistrer' est grisé ?": "Vérifiez que le champ 'Référence' est bien rempli.",
                "Comment voir l'historique d'un mélange ?": "Les dates de création et de modification sont visibles dans la FT."
            },
            "Fiches Techniques (FT)": {
                "Comment ajouter un risque spécifique ?": "Via l'éditeur d'élément, activez la FT et renseignez le champ 'Danger'.",
                "La FT est-elle modifiable par tous ?": "Les droits d'accès dépendent de votre profil configuré dans l'ERP.",
                "Comment exporter toutes les FT d'un coup ?": "L'export Excel permet de centraliser les données.",
                "Peut-on ajouter une vidéo dans une FT ?": "Non, seul le format image est supporté actuellement.",
                "Comment changer le logo sur la FT ?": "Le logo est automatique via le fichier Logo à la racine.",
                "Le rédacteur doit-il être choisi ?": "Oui, pour assurer la traçabilité des modifications effectuées.",
                "Que faire si la FT dépasse une page ?": "ReportLab gère automatiquement la pagination et la numérotation.",
                "Puis-je joindre une MSDS externe ?": "Non, le système est auto-suffisant avec les informations de risques internes.",
                "Pourquoi ma FT ne montre pas les composants ?": "Vérifiez que vous avez bien coché les composants dans la section formulation.",
                "Comment valider une FT ?": "La validation est implicite via le changement de statut vers 'Vérifié'."
            },
            "Maintenance & Dépannage": {
                "La recherche ne donne aucun résultat ?": "Videz votre barre de recherche et réessayez sans filtres.",
                "Erreur lors de la sauvegarde JSON ?": "Vérifiez que votre fichier n'est pas ouvert dans un autre logiciel.",
                "L'interface semble 'figée' ?": "Il s'agit peut-être de la limite anti-lag. Réduisez vos résultats avec les filtres.",
                "Comment réinitialiser tous les filtres ?": "Supprimez simplement le texte dans toutes les barres de filtres.",
                "Puis-je faire une sauvegarde manuelle ?": "Oui, copiez simplement le fichier json dans un dossier sécurisé.",
                "Comment restaurer une ancienne sauvegarde ?": "Renommez votre ancienne copie (attention à sauvegarder le courant).",
                "Pourquoi les icônes ne s'affichent pas ?": "Vérifiez que vous avez accès à internet pour charger les polices.",
                "Une image est trop lourde pour l'app ?": "Redimensionnez-la à 500x500 pixels avant l'importation.",
                "Le bouton Aide est grisé ?": "Cela n'arrive jamais, si c'est le cas, rafraîchissez la page.",
                "Comment contacter le support en cas d'urgence ?": "Utilisez le formulaire interne ou l'email du responsable qualité/IT."
            }
        }
        for categorie, questions in faq_data.items():
            st.subheader(f"📂 {categorie}")
            for question, reponse in questions.items():
                with st.expander(f"▶ {question}"):
                    st.write(reponse)
                    
    with onglets[4]:
        st.error("**Problème : Mon PDF de fiche technique est vide ou incomplet**\n*Solution :* Éditez le mélange, activez la gestion de la FT, et complétez les champs.")
        st.warning("**Problème : Un code RAL n'est pas reconnu par le système**\n*Solution :* Vous pouvez utiliser la pipette de sélection manuelle.")
    if st.button("Fermer l'aide", type="primary", use_container_width=True):
        st.rerun()

# --- CONTENU DE LA BARRE LATÉRALE ---
with st.sidebar:
    logo_path = os.path.join(os.getcwd(), "Martineau logo.png")
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    
    st.markdown('<div style="text-align: center; margin-top: 20px;"><h2>PORTAIL</h2></div>', unsafe_allow_html=True)
    
    if st.button("❓ Centre de formation / Aide", use_container_width=True):
        ouvrir_fenetre_aide()
        
    # --- NOUVEAU : BOUTON DÉCONNEXION ---
    if st.button("🚪 Déconnexion", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.groupe_actif = None
        st.rerun()
        
    st.markdown("---")

st.markdown("<br>", unsafe_allow_html=True)
search_icon = get_svg_icon("search")

if st.session_state.groupe_actif is None:
    st.title("Portail Industriel")
    st.markdown("### Sélectionnez votre espace de travail :")
    c_g1, c_g2 = st.columns(2)
    with c_g1:
        if st.button(f"CRÉATION DES PROCESSUS", type="primary", use_container_width=True):
            st.session_state.groupe_actif = "creation_processus"
            st.rerun()
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

# --- RECHERCHE GLOBALE ---
# (Reste inchangé mais déplacé ici pour structuration logique)
st.markdown(f'<div style="display:flex; align-items:center;">{search_icon}<span>RECHERCHE ULTRA-RAPIDE (Filtre instantané)...</span></div>', unsafe_allow_html=True)
recherche_globale = st.text_input("", label_visibility="collapsed").strip()

if recherche_globale:
    icon_chart = get_svg_icon("chart")
    st.markdown(f"### {icon_chart} Résultats de la recherche globale", unsafe_allow_html=True)
    
    resultats_trouves = []
    db_prep = st.session_state.processus_db.get("preparation_melanges", {})
    
    for prod_nom in st.session_state.processus_db.get("creation_processus", {}).keys():
        if recherche_globale.lower() in prod_nom.lower():
            resultats_trouves.append({"label": f"Dossier : {prod_nom}", "chemin": "Processus ➔ " + prod_nom, "type": "process", "data": prod_nom})
            
    for c in db_prep.get("couleurs", []):
        if any(recherche_globale.lower() in str(c.get(k, "")).lower() for k in ["ref", "nom_actuel", "nom_futur", "ral", "societe"]):
            resultats_trouves.append({"label": f"Couleur : {c.get('nom_actuel')} ({c.get('ref')})", "chemin": "Mélanges ➔ Nuancier", "type": "couleur", "data": c})
            
    for a in db_prep.get("additifs", []):
        if any(recherche_globale.lower() in str(a.get(k, "")).lower() for k in ["nom", "code", "designation", "fournisseur"]):
            resultats_trouves.append({"label": f"Élément : {a.get('nom')} ({a.get('code')})", "chemin": "Mélanges ➔ Catalogue", "type": "element", "data": a})
            
    for m in db_prep.get("melanges", []):
        if any(recherche_globale.lower() in str(m.get(k, "")).lower() for k in ["ref", "nom", "emplacement"]):
            resultats_trouves.append({"label": f"Mélange : {m.get('nom')} ({m.get('ref')})", "chemin": "Mélanges ➔ Formulations", "type": "melange", "data": m})

    if resultats_trouves:
        for idx_r, res in enumerate(resultats_trouves[:15]): 
            col_res_txt, col_res_btn = st.columns([4, 1])
            with col_res_txt:
                st.markdown(f"**{res['label']}**")
                st.caption(f"📍 Chemin : {res['chemin']}")
            with col_res_btn:
                if res["type"] in ["couleur", "element", "melange"]:
                    if st.button("👁️ Voir", key=f"global_res_{idx_r}"):
                        if res["type"] == "couleur": ouvrir_details_couleur(res["data"])
                        elif res["type"] == "element": ouvrir_details_element(res["data"])
                        elif res["type"] == "melange": ouvrir_details_melange(res["data"])
                else:
                    if st.button("Accéder", key=f"global_res_{idx_r}"):
                        st.session_state.groupe_actif = "creation_processus"
                        st.session_state.produit_selectionne = res["data"]
                        st.rerun()
            st.markdown("<hr style='margin: 0.3em 0px; opacity: 0.15;'>", unsafe_allow_html=True)
            
        if len(resultats_trouves) > 15:
            st.caption(f"*... et {len(resultats_trouves)-15} autres résultats trouvés. Affinez votre recherche.*")
    else:
        st.info("Aucun résultat trouvé.")
    st.markdown("---")

# =========================================================
# MENU HAUT DROIT (3 PETITS POINTS) & MODE SOMBRE INDÉPENDANT
# =========================================================
col_vide, col_menu = st.columns([9.7, 0.3])
with col_menu:
    with st.popover("⋮"):
        st.markdown("**Paramètres**")
        st.session_state.mode_sombre = st.toggle("🌙 Mode Sombre", value=st.session_state.mode_sombre)

# /!\ RENSEIGNE ICI LE NOM DE TON IMAGE POUR LE FOND SOMBRE /!\
IMAGE_FOND_SOMBRE = "ton_image_sombre.png" 

if st.session_state.mode_sombre:
    img_b64_dark = encoder_image_systeme(IMAGE_FOND_SOMBRE)
    bg_property = f'background-image: url("data:image/png;base64,{img_b64_dark}") !important;' if img_b64_dark else 'background-color: #090e17 !important;'
    
    st.markdown(f"""
    <style>
    .main {{
        {bg_property}
        background-size: cover !important;
        background-position: center !important;
        background-attachment: fixed !important;
    }}
    .main *, div[role="dialog"] * {{ color: #FFFFFF !important; }}
    div[role="dialog"] {{ background-color: rgba(9, 14, 23, 0.95) !important; }}
    .main div[data-testid="stButton"] > button {{ border: 1px solid #FFFFFF !important; color: #FFFFFF !important; }}
    .main div[data-testid="stButton"] > button:hover {{ background-color: #D4AF37 !important; border-color: #D4AF37 !important; color: #000000 !important; }}
    [data-testid="stSidebar"] {{ background-color: #F4F1EA !important; }}
    [data-testid="stSidebar"] * {{ color: #1E293B !important; }}
    </style>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------
# MODULE 1 : CRÉATION DES PROCESSUS
# ---------------------------------------------------------
if G_ACTIF == "creation_processus":
    db_courante = st.session_state.processus_db[G_ACTIF]
    st.sidebar.title("🏗️ Édition SOP")
    recherche_sidebar = st.sidebar.text_input("🔍 Filtrer la liste...", "").strip()
    liste_produits = sorted(list(db_courante.keys()))
    if recherche_sidebar: liste_produits = sorted([p for p in liste_produits if recherche_sidebar.lower() in p.lower()])

    if liste_produits: st.info(f"📊 **Nombre de processus :** {len(liste_produits)}")
    else: st.sidebar.warning("Aucun processus trouvé")

    producto_index = liste_produits.index(st.session_state.produit_selectionne) if st.session_state.produit_selectionne in liste_produits else 0
    if liste_produits:
        produit_selectionne = st.sidebar.selectbox("Choisir un processus actif :", liste_produits, index=producto_index)
        st.session_state.produit_selectionne = produit_selectionne
    else: produit_selectionne = None

    st.sidebar.markdown("---")
    st.sidebar.subheader("➕ Nouvel Fichier")
    nouveau_nom = st.sidebar.text_input("Nom du processus")
    if st.sidebar.button("Créer la fiche"):
        if nouveau_nom and nouveau_nom not in db_courante:
            st.session_state.processus_db[G_ACTIF][nouveau_nom] = {"etapes": [], "ressources": []}
            st.session_state.produit_selectionne = nouveau_nom
            sauvegarder_donnees()
            st.rerun()

    st.title("🏗️ Création des Processus")
    if produit_selectionne:
        if "mode_grand_ecran" not in st.session_state: st.session_state.mode_grand_ecran = False
        col_titre, col_btn_mode = st.columns([3, 1])
        with col_titre: st.subheader(f"📦 Processus : {produit_selectionne}")
        with col_btn_mode:
            if st.button("🖥️ Basculer Grand Écran"):
                st.session_state.mode_grand_ecran = not st.session_state.mode_grand_ecran
                st.rerun()

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
                            if st.button("🗑️ Supprimer l'étape", key=f"del_etp_{i}"):
                                st.session_state[key_del] = True
                                st.rerun()
                        else:
                            st.warning("💥 Confirmer la suppression ?")
                            c_del_col1, c_del_col2 = st.columns(2)
                            with c_del_col1:
                                if st.button("Oui, effacer", key=f"del_etp_yes_{i}", type="primary"):
                                    st.session_state.processus_db[G_ACTIF][produit_selectionne]["etapes"].pop(i)
                                    st.session_state[key_del] = False
                                    sauvegarder_donnees()
                                    st.rerun()
                            with c_del_col2:
                                if st.button("Annuler", key=f"del_etp_no_{i}"):
                                    st.session_state[key_del] = False
                                    st.rerun()
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
    choix_section = st.sidebar.radio("Sélectionnez la section :", ["🎨 Nuancier de couleurs", "🧪 Catalogue des éléments", "🔢 Référentiel des codes RAL", "⚗️ Formulations d'atelier", "📐 Fiches Méthode"])
    st.session_state.sub_section_melange = choix_section
    st.markdown(f"## {st.session_state.sub_section_melange}")

    fiches_m = st.session_state.processus_db["preparation_melanges"].setdefault("fiches_methode", [])
    liste_couleurs = st.session_state.processus_db["preparation_melanges"].setdefault("couleurs", [])
    liste_additifs = st.session_state.processus_db["preparation_melanges"].setdefault("additifs", [])
    liste_melanges = st.session_state.processus_db["preparation_melanges"].setdefault("melanges", [])

    if choix_section == "🎨 Nuancier de couleurs":
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
            with c_ral_col: c_ral = st.text_input("Code RAL", value=st.session_state["add_ral"])
            with c_chk_col:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button(f"Vérifier RAL", key="btn_check_add_ral"):
                    num_ral = ''.join(filter(str.isdigit, c_ral.strip()))
                    if num_ral in RAL_DICT:
                        st.session_state["add_hex"] = RAL_DICT[num_ral]
                        st.session_state["add_ral"] = c_ral
            with c_hex_col: c_hex = st.color_picker("Sélectionner la nuance", value=st.session_state["add_hex"])

            activer_ft = st.toggle("📝 Créer la Fiche Technique (FT)", value=False)
            ft_cond, m_comm_glob = "", ""
            ft_redacteur = OPTIONS_REDACTEURS[0]
            if activer_ft:
                if "champs_ft_c" not in st.session_state: st.session_state["champs_ft_c"] = []
                editeur_champs_dynamiques({"champs_ft": st.session_state["champs_ft_c"]})
                ft_redacteur = st.selectbox("Rédacteur / Modifié par :", OPTIONS_REDACTEURS, index=0)

            if st.button("Enregistrer la couleur", type="primary"):
                if c_ref:
                    num_ral = ''.join(filter(str.isdigit, c_ral.strip()))
                    couleur_finale = RAL_DICT.get(num_ral, c_hex) if num_ral else c_hex
                    today_str = datetime.datetime.now().strftime("%d/%m/%Y - %H:%M")
                    
                    st.session_state.processus_db["preparation_melanges"]["couleurs"].append({
                        "ref": c_ref, "nom_actuel": c_actuel, "nom_futur": c_futur,
                        "ral": c_ral, "societe": c_societe, "type": c_type, "visuel": couleur_finale,
                        "has_ft": activer_ft,
                        "fiche_technique": {"date_creation": today_str, "date_derniere_maj": today_str, "date_avant_derniere_maj": "-", "redacteur": ft_redacteur, "champs_ft": st.session_state.get("champs_ft_c", [])}
                    })
                    st.session_state.pop("add_ral", None)
                    st.session_state.pop("add_hex", None)
                    st.session_state.pop("champs_ft_c", None)
                    sauvegarder_donnees()
                    st.rerun()

        @st.dialog("✏️ Modifier une couleur", width="large")
        def ouvrir_modif_couleur(index, couleur_data):
            m_ref = st.text_input("Référence", value=couleur_data.get("ref", ""))
            m_actuel = st.text_input("Nom actuel", value=couleur_data.get("nom_actuel", ""))
            m_futur = st.text_input("Futur nom", value=couleur_data.get("nom_futur", ""))
            m_societe = st.text_input("Société / Client", value=couleur_data.get("societe", ""))
            m_type = st.selectbox("Type", ["Opaque", "Translucide", "2"], index=["Opaque", "Translucide", "2"].index(couleur_data.get("type", "Opaque")))

            c_ral_col, c_chk_col, c_hex_col = st.columns([2, 1, 2])
            with c_ral_col: m_ral = st.text_input("Code RAL", value=couleur_data.get("ral", ""))
            with c_chk_col:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Vérifier RAL"): pass # simplifié pour l'exemple
            with c_hex_col: m_hex = st.color_picker("Ajuster la nuance", value=couleur_data.get("visuel", "#3B82F6"))

            has_ft_init = couleur_data.get("has_ft", False)
            activer_ft = st.toggle("📝 Gérer la Fiche Technique (FT)", value=has_ft_init)
            ft_old = couleur_data.get("fiche_technique", {})
            idx_redacteur = OPTIONS_REDACTEURS.index(ft_old.get("redacteur", "Labo / R&D")) if ft_old.get("redacteur", "Labo / R&D") in OPTIONS_REDACTEURS else 0

            if activer_ft:
                editeur_champs_dynamiques(ft_old)
                m_redacteur = st.selectbox("Rédacteur / Modifié par :", OPTIONS_REDACTEURS, index=idx_redacteur)

            if st.button("Mettre à jour", type="primary"):
                today_str = datetime.datetime.now().strftime("%d/%m/%Y - %H:%M")
                d_crea, d_der, d_av = gerer_historique_dates(ft_old, today_str)
                
                st.session_state.processus_db["preparation_melanges"]["couleurs"][index].update({
                    "ref": m_ref, "nom_actuel": m_actuel, "nom_futur": m_futur,
                    "ral": m_ral, "societe": m_societe, "type": m_type, "visuel": m_hex, "has_ft": activer_ft
                })
                st.session_state.processus_db["preparation_melanges"]["couleurs"][index]["fiche_technique"].update({"date_creation": d_crea, "date_derniere_maj": d_der, "date_avant_derniere_maj": d_av})
                if activer_ft: st.session_state.processus_db["preparation_melanges"]["couleurs"][index]["fiche_technique"]["redacteur"] = m_redacteur
                sauvegarder_donnees()
                st.rerun()

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

            col_info, col_export = st.columns([4, 1])
            with col_info:
                st.info(f"📊 **Nombre de couleurs :** {len(couleurs_filtrees)}")
            with col_export:
                donnees_a_exporter = [item["data"] for item in couleurs_filtrees]
                excel_data, nom_fichier, mime_type = generer_fichier_export(donnees_a_exporter, "Export_Couleurs")
                if excel_data:
                    st.download_button("📥 Exporter Excel", data=excel_data, file_name=nom_fichier, mime=mime_type, use_container_width=True)

            if len(couleurs_filtrees) > MAX_LIGNES_AFFICHAGE:
                st.warning(f"⚠️ Affichage limité aux {MAX_LIGNES_AFFICHAGE} premiers résultats pour des raisons de fluidité. Utilisez les filtres.")
            couleurs_a_afficher = couleurs_filtrees[:MAX_LIGNES_AFFICHAGE]

            thead_ref, thead_act, thead_fut, thead_ral, thead_soc, thead_typ, thead_vis, thead_act2 = st.columns([1.2, 1.6, 1.6, 1.2, 1.6, 1.2, 0.8, 2.5])
            with thead_ref: st.markdown("**Référence**")
            with thead_act: st.markdown("**Nom actuel**")
            with thead_fut: st.markdown("**Futur nom**")
            with thead_ral: st.markdown("**RAL**")
            with thead_soc: st.markdown("**Société**")
            with thead_typ: st.markdown("**Type**")
            with thead_vis: st.markdown("**Visuel**")
            with thead_act2: st.markdown("**Actions**")
            st.markdown("<hr style='margin:4px 0px; border-width:2px; border-color:black;'>", unsafe_allow_html=True)

            for item in couleurs_a_afficher:
                idx_c = item["index_origine"]
                c_data = item["data"]
                trow_ref, trow_act, trow_fut, trow_ral, trow_soc, trow_typ, trow_vis, trow_act2 = st.columns([1.2, 1.6, 1.6, 1.2, 1.6, 1.2, 0.8, 2.5])
                with trow_ref: st.write(str(c_data.get("ref", "")).title())
                with trow_act: st.write(str(c_data.get("nom_actuel", "")).title())
                with trow_fut: st.write(str(c_data.get("nom_futur", "")).title())
                with trow_ral: st.write(str(c_data.get("ral", "")).title() or "-")
                with trow_soc: st.write(str(c_data.get("societe", "")).upper())
                with trow_typ: st.write(str(c_data.get("type", "")).title())
                with trow_vis: st.markdown(f'<div style="width:22px; height:25px; background-color:{c_data.get("visuel", "#3B82F6")}; border-radius:50%; border:1px solid #000; margin:auto;"></div>', unsafe_allow_html=True)
                
                with trow_act2:
                    c_v, c_e, c_d, c_ft = st.columns([1, 1, 1, 1.5])
                    if c_v.button("👁️", key=f"v_col_{idx_c}"): ouvrir_details_couleur(c_data)
                    if c_e.button("✏️", key=f"e_col_{idx_c}"): ouvrir_modif_couleur(idx_c, c_data)
                    
                    key_del_c = f"del_confirm_col_{idx_c}"
                    if key_del_c not in st.session_state: st.session_state[key_del_c] = False
                    if not st.session_state[key_del_c]:
                        if c_d.button("🗑️", key=f"d_col_{idx_c}"):
                            st.session_state[key_del_c] = True
                            st.rerun()
                    else:
                        if c_d.button("Oui", key=f"d_col_y_{idx_c}", type="primary"):
                            st.session_state.processus_db["preparation_melanges"]["couleurs"].pop(idx_c)
                            st.session_state[key_del_c] = False
                            sauvegarder_donnees()
                            st.rerun()
                        if c_d.button("Non", key=f"d_col_n_{idx_c}"):
                            st.session_state[key_del_c] = False
                            st.rerun()
                            
                    if c_data.get("has_ft"):
                        if c_ft.button("📄 FT", key=f"ft_col_{idx_c}"):
                            ouvrir_visualisation_ft_couleur(c_data)

    elif choix_section == "🧪 Catalogue des éléments":
        @st.dialog("➕ Ajouter un élément", width="large")
        def ouvrir_ajout_element_complet():
            e_nom = st.text_input("Nom de l'élément (Clé unique/Référence)")
            e_code = st.text_input("Code")
            e_des = st.text_input("Désignation")
            e_comm = st.text_input("Commentaire court (Formulation)")
            e_statut = st.radio("État de l'élément :", ["Pas vérifié", "Vérifier"], index=0, horizontal=True)

            activer_ft = st.toggle("📝 Créer la Fiche Technique (FT)", value=False)
            
            st.markdown("##### 🗂️ Classification")
            liste_compartiments = st.session_state.processus_db["preparation_melanges"].setdefault("compartiments", ["résine", "peinture"])
            liste_sous_groupes = st.session_state.processus_db["preparation_melanges"].setdefault("sous_groupes", ["Général"])
            
            col_c, col_sg = st.columns(2)
            with col_c:
                e_compartiments = st.multiselect("Compartiments :", liste_compartiments, default=[])
                nouveau_comp = st.text_input("➕ Nouveau compartiment :")
            with col_sg:
                e_sous_groupe = st.selectbox("Sous-groupe :", liste_sous_groupes, index=0)
                nouveau_sg = st.text_input("➕ Nouveau sous-groupe :")
                
            st.markdown("<br>", unsafe_allow_html=True)

            e_fourn, e_art, e_des_ach, e_nat, e_dang, e_dang_txt, e_manip, e_comm_glob = "", "", "", "Liquide", "-", "", "", ""
            ft_redacteur = OPTIONS_REDACTEURS[0]
            champs_dyn = []

            if activer_ft:
                if "champs_ft_el" not in st.session_state: st.session_state["champs_ft_el"] = []
                editeur_champs_dynamiques({"champs_ft": st.session_state["champs_ft_el"]})
                champs_dyn = st.session_state["champs_ft_el"]
                
                e_fourn = st.text_input("Fournisseur")
                e_art = st.text_input("Code Article Achat")
                e_nat = st.selectbox("Nature", ["-", "Liquide", "Poudre", "Granulé", "Gel", "Autre"])         
                e_dang = st.radio("Risque / Danger ?", ["-", "Non", "Oui"], index=0, horizontal=True)
                if e_dang == "Oui":
                    e_dang_txt = st.text_area("Préciser le risque / danger")
                ft_redacteur = st.selectbox("Rédacteur / Modifié par :", OPTIONS_REDACTEURS, index=0)

            if st.button("Enregistrer l'élément", type="primary"):
                if e_nom:
                    comps_finaux = list(e_compartiments)
                    if nouveau_comp.strip() and nouveau_comp.strip() not in liste_compartiments:
                        st.session_state.processus_db["preparation_melanges"]["compartiments"].append(nouveau_comp.strip())
                        comps_finaux.append(nouveau_comp.strip())
                        
                    if nouveau_sg.strip() and nouveau_sg.strip() not in liste_sous_groupes:
                        st.session_state.processus_db["preparation_melanges"]["sous_groupes"].append(nouveau_sg.strip())
                        sg_final = nouveau_sg.strip()
                    else:
                        sg_final = e_sous_groupe

                    today_str = datetime.datetime.now().strftime("%d/%m/%Y - %H:%M")
                    st.session_state.processus_db["preparation_melanges"]["additifs"].append({
                        "nom": e_nom, "code": e_code, "designation": e_des, "statut": e_statut,
                        "compartiments": comps_finaux, "sous_groupe": sg_final,
                        "fournisseur": e_fourn, "code_article": e_art, "designation_achat": e_des_ach,
                        "nature": e_nat, "danger": e_dang, "danger_texte": e_dang_txt, "manipulation": e_manip,
                        "commentaire": e_comm, "commentaire_global": e_comm_glob, "has_ft": activer_ft,
                        "fiche_technique": {"date_creation": today_str, "date_derniere_maj": today_str, "date_avant_derniere_maj": "-", "redacteur": ft_redacteur, "champs_ft": champs_dyn}
                    })
                    st.session_state.pop("champs_ft_el", None)
                    sauvegarder_donnees()
                    st.rerun()

        @st.dialog("✏️ Modifier un élément", width="large")
        def ouvrir_modif_element_complet(index, data):
            m_nom = st.text_input("Nom de l'élément", value=data.get("nom", ""))
            m_code = st.text_input("Code", value=data.get("code", ""))
            m_des = st.text_input("Désignation", value=data.get("designation", ""))
            m_comm = st.text_input("Commentaire court (Formulation)", value=data.get("commentaire", ""))
            m_statut = st.radio("État de l'élément :", ["Pas vérifié", "Vérifier"], index=["Pas vérifié", "Vérifier"].index(data.get("statut", "Pas vérifié")), horizontal=True)

            st.markdown("##### 🗂️ Classification")
            liste_compartiments = st.session_state.processus_db["preparation_melanges"].setdefault("compartiments", ["résine", "peinture"])
            liste_sous_groupes = st.session_state.processus_db["preparation_melanges"].setdefault("sous_groupes", ["Général"])
            
            comps_actuels = data.get("compartiments", [])
            def_comps = [c for c in comps_actuels if c in liste_compartiments]
            sg_actuel = data.get("sous_groupe", "Général")
            if sg_actuel not in liste_sous_groupes: sg_actuel = "Général"
            
            col_c, col_sg = st.columns(2)
            with col_c:
                m_compartiments = st.multiselect("Compartiments :", liste_compartiments, default=def_comps)
                nouveau_comp_m = st.text_input("➕ Nouveau compartiment :")
            with col_sg:
                m_sous_groupe = st.selectbox("Sous-groupe :", liste_sous_groupes, index=liste_sous_groupes.index(sg_actuel))
                nouveau_sg_m = st.text_input("➕ Nouveau sous-groupe :")
                
            st.markdown("<br>", unsafe_allow_html=True)

            has_ft_init = data.get("has_ft", False)
            activer_ft = st.toggle("📝 Gérer la Fiche Technique (FT)", value=has_ft_init)

            m_fourn = data.get("fournisseur", "")
            m_art = data.get("code_article", "")
            m_nat = data.get("nature", "Liquide")
            m_dang = data.get("danger", "-")
            if m_dang not in ["-", "Non", "Oui"]: m_dang = "-"
            m_dang_txt = data.get("danger_texte", "")
            
            ft_old = data.get("fiche_technique", {})
            idx_redacteur = OPTIONS_REDACTEURS.index(ft_old.get("redacteur", "Labo / R&D")) if ft_old.get("redacteur", "Labo / R&D") in OPTIONS_REDACTEURS else 0

            if activer_ft:
                editeur_champs_dynamiques(ft_old)
                m_fourn = st.text_input("Fournisseur", value=m_fourn)
                m_art = st.text_input("Code Article Achat", value=m_art)
                m_nat = st.selectbox("Nature", ["-", "Liquide", "Poudre", "Granulé", "Gel", "Autre"], index=["-", "Liquide", "Poudre", "Granulé", "Gel", "Autre"].index(m_nat))
                m_dang = st.radio("Risque / Danger ?", ["-", "Non", "Oui"], index=["-", "Non", "Oui"].index(m_dang), horizontal=True)
                if m_dang == "Oui":
                    m_dang_txt = st.text_area("Préciser le risque / danger", value=m_dang_txt)
                m_redacteur = st.selectbox("Rédacteur / Modifié par :", OPTIONS_REDACTEURS, index=idx_redacteur)

            if st.button("Mettre à jour l'élément", type="primary"):
                comps_finaux = list(m_compartiments)
                if nouveau_comp_m.strip() and nouveau_comp_m.strip() not in liste_compartiments:
                    st.session_state.processus_db["preparation_melanges"]["compartiments"].append(nouveau_comp_m.strip())
                    comps_finaux.append(nouveau_comp_m.strip())
                    
                if nouveau_sg_m.strip() and nouveau_sg_m.strip() not in liste_sous_groupes:
                    st.session_state.processus_db["preparation_melanges"]["sous_groupes"].append(nouveau_sg_m.strip())
                    sg_final = nouveau_sg_m.strip()
                else:
                    sg_final = m_sous_groupe

                today_str = datetime.datetime.now().strftime("%d/%m/%Y - %H:%M")
                d_crea, d_der, d_av = gerer_historique_dates(ft_old, today_str)

                st.session_state.processus_db["preparation_melanges"]["additifs"][index].update({
                    "nom": m_nom, "code": m_code, "designation": m_des, "statut": m_statut,
                    "compartiments": comps_finaux, "sous_groupe": sg_final,
                    "fournisseur": m_fourn, "code_article": m_art,
                    "nature": m_nat, "danger": m_dang, "danger_texte": m_dang_txt if m_dang == "Oui" else "",
                    "commentaire": m_comm, "has_ft": activer_ft
                })
                st.session_state.processus_db["preparation_melanges"]["additifs"][index]["fiche_technique"].update({"date_creation": d_crea, "date_derniere_maj": d_der, "date_avant_derniere_maj": d_av})
                sauvegarder_donnees()
                st.rerun()

        if st.button("Ajouter un élément", type="primary"):
            ouvrir_ajout_element_complet()

        if liste_additifs:
            with st.expander("🔍 Outils de filtrage (Global)", expanded=True):
                liste_compartiments = st.session_state.processus_db["preparation_melanges"].setdefault("compartiments", ["résine", "peinture"])
                e_f1, e_f2, e_f3, e_f4 = st.columns([1.5, 1.5, 1.5, 1])
                with e_f1: filtre_e_nom = st.text_input("Filtrer par Nom", "")
                with e_f2: filtre_e_emp = st.text_input("Filtrer par Code", "")
                with e_f3: tri_e_colonne = st.selectbox("Trier par :", ["Nom", "Code", "Fournisseur", "Sous-groupe"])
                with e_f4: sens_e_tri = st.selectbox("Ordre :", ["Croissant ⬆️", "Décroissant ⬇️"], key="sens_e")

            # Filtrage global
            elements_filtres = []
            for idx, a in enumerate(liste_additifs):
                match_nom = filtre_e_nom.lower() in a.get("nom", "").lower()
                match_code = filtre_e_emp.lower() in a.get("code", "").lower()
                if match_nom and match_code:
                    elements_filtres.append({"index_origine": idx, "data": a})
            
            tri_cle = {"Nom": "nom", "Code": "code", "Fournisseur": "fournisseur", "Sous-groupe": "sous_groupe"}[tri_e_colonne]
            elements_filtres.sort(key=lambda x: str(x["data"].get(tri_cle, "")).lower(), reverse=(sens_e_tri == "Décroissant ⬇️"))

            col_info_el, col_export_el = st.columns([4, 1])
            with col_info_el:
                st.info(f"📊 **Nombre total d'éléments trouvés :** {len(elements_filtres)}")
            with col_export_el:
                donnees_el_export = [item["data"] for item in elements_filtres]
                excel_data, nom_fichier, mime_type = generer_fichier_export(donnees_el_export, "Export_Elements")
                if excel_data:
                    st.download_button("📥 Exporter Excel", data=excel_data, file_name=nom_fichier, mime=mime_type, use_container_width=True)

            def afficher_tableau_elements(liste_a_afficher, prefix_tab):
                if not liste_a_afficher:
                    st.warning("Aucun élément dans cette section.")
                    return
                
                if len(liste_a_afficher) > MAX_LIGNES_AFFICHAGE:
                    st.warning(f"⚠️ Affichage limité aux {MAX_LIGNES_AFFICHAGE} premiers résultats.")
                elements_pagines = liste_a_afficher[:MAX_LIGNES_AFFICHAGE]

                thead = st.columns([1.5, 1, 1.5, 1.5, 1.5, 1.5, 1.5])
                thead[0].markdown("**Nom**")
                thead[1].markdown("**Code**")
                thead[2].markdown("**Désignation**")
                thead[3].markdown("**Fournisseur**")
                thead[4].markdown("**Compartiments**")
                thead[5].markdown("**Commentaire**")
                thead[6].markdown("**Actions**")
                st.markdown("<hr style='margin:4px 0px; border-width:2px; border-color:black;'>", unsafe_allow_html=True)

                for item in elements_pagines:
                    idx_a = item["index_origine"]
                    a_data = item["data"]
                    
                    is_verified = a_data.get("statut") == "Vérifier"
                    txt_style = "color: #CC0605; font-weight: bold;" if is_verified else "color: inherit;"
                    
                    row = st.columns([1.5, 1, 1.5, 1.5, 1.5, 1.5, 1.5])
                    
                    pastille = "🔴 " if is_verified else ""
                    row[0].markdown(f'<span style="{txt_style}">{pastille}{str(a_data.get("nom", "-")).title()}</span>', unsafe_allow_html=True)
                    row[1].write(str(a_data.get("code", "-")).upper())
                    row[2].write(str(a_data.get("designation", "-")).title())
                    row[3].write(str(a_data.get("fournisseur", "-") if a_data.get("fournisseur") else "-").upper())
                    
                    comps = a_data.get("compartiments", [])
                    row[4].write(", ".join(comps) if comps else "-")
                    
                    row[5].write(str(a_data.get("commentaire", "-")))
                    
                    c_v, c_edit, c_del, c_ft = row[6].columns([1, 1, 1, 1.5])
                    if c_v.button("👁️", key=f"v_add_{prefix_tab}_{idx_a}"):
                        ouvrir_details_element(a_data)
                    
                    if c_edit.button("✏️", key=f"ed_add_{prefix_tab}_{idx_a}"):
                        ouvrir_modif_element_complet(idx_a, a_data)
                    
                    key_del_a = f"del_confirm_add_{idx_a}" 
                    if key_del_a not in st.session_state: st.session_state[key_del_a] = False
                    if not st.session_state[key_del_a]:
                        if c_del.button("🗑️", key=f"del_add_{prefix_tab}_{idx_a}"):
                            st.session_state[key_del_a] = True
                            st.rerun()
                    else:
                        if c_del.button("Oui", key=f"d_add_y_{prefix_tab}_{idx_a}", type="primary"):
                            st.session_state.processus_db["preparation_melanges"]["additifs"].pop(idx_a)
                            st.session_state[key_del_a] = False
                            sauvegarder_donnees()
                            st.rerun()
                        if c_del.button("Non", key=f"d_add_n_{prefix_tab}_{idx_a}"):
                            st.session_state[key_del_a] = False
                            st.rerun()
                    
                    if a_data.get("has_ft"):
                        if c_ft.button("📄 FT", key=f"ft_add_{prefix_tab}_{idx_a}"):
                            ouvrir_visualisation_ft_additif(a_data)

            # ONGLET DYNAMIQUES
            noms_onglets = ["🗂️ Tous les éléments"] + [f"📁 {c.capitalize()}" for c in liste_compartiments]
            onglets_comp = st.tabs(noms_onglets)
            
            with onglets_comp[0]:
                afficher_tableau_elements(elements_filtres, "tous")
                
            for i, comp in enumerate(liste_compartiments):
                with onglets_comp[i+1]:
                    elements_du_comp = [e for e in elements_filtres if comp in e["data"].get("compartiments", [])]
                    if not elements_du_comp:
                        st.info(f"Aucun élément n'est classé dans le compartiment : {comp}.")
                    else:
                        sgs_presents = sorted(list(set([e["data"].get("sous_groupe", "Général") for e in elements_du_comp])))
                        for sg in sgs_presents:
                            st.markdown(f"#### 📂 Sous-groupe : {sg}")
                            elements_sg = [e for e in elements_du_comp if e["data"].get("sous_groupe", "Général") == sg]
                            afficher_tableau_elements(elements_sg, f"comp_{i}_sg_{sg.replace(' ', '_')}")

    elif choix_section == "🔢 Référentiel des codes RAL":
        @st.dialog("➕ Ajouter un nouveau RAL au nuancier", width="large")
        def ouvrir_ajout_ral_base():
            r_code = st.text_input("Code RAL (ex: 5015)")
            r_nom = st.text_input("Nom officiel de la teinte")
            r_hex = st.color_picker("Sélectionner la valeur Hexadécimale", "#FFFFFF")
            if st.button("Enregistrer dans le catalogue", type="primary"):
                if r_code and r_nom:
                    RAL_DICT[r_code.strip()] = r_hex
                    st.session_state.processus_db["preparation_melanges"].setdefault("base_rals", []).append(
                        {"code": r_code.strip(), "nom": r_nom.strip(), "visuel": r_hex}
                    )
                    sauvegarder_donnees()
                    st.rerun()

        if st.button("Ajouter une nuance RAL", type="primary"): ouvrir_ajout_ral_base()
        catalogue_complet_ral = [{"code": code_r, "nom": f"Teinte RAL CLASSIC {code_r}", "visuel": hex_r} for code_r, hex_r in RAL_DICT.items()]

        with st.expander("🔍 Filtrer et trier le catalogue complet des RALs", expanded=True):
            r_f1, r_f2, r_f3 = st.columns([2, 2, 1])
            with r_f1: filtre_r_code = st.text_input("Filtrer par Code RAL", "")
            with r_f2: filtre_r_nom = st.text_input("Filtrer par Libellé", "")
            with r_f3: sens_r_tri = st.selectbox("Ordre de tri :", ["Croissant ⬆️", "Décroissant ⬇️"])

        rals_filtres = [r for r in catalogue_complet_ral if (filtre_r_code in r["code"]) and (filtre_r_nom.lower() in r["nom"].lower())]
        rals_filtres.sort(key=lambda x: int(x["code"]) if x["code"].isdigit() else x["code"], reverse=(sens_r_tri == "Décroissant ⬇️"))

        if len(rals_filtres) > MAX_LIGNES_AFFICHAGE:
            st.warning(f"⚠️ Affichage limité aux {MAX_LIGNES_AFFICHAGE} premiers résultats. Utilisez les filtres.")
        rals_a_afficher = rals_filtres[:MAX_LIGNES_AFFICHAGE]

        if rals_filtres: st.info(f"📊 **Nombre de codes RAL :** {len(rals_filtres)} | **Premier affiché :** RAL {rals_a_afficher[0]['code']} | **Dernier affiché :** RAL {rals_a_afficher[-1]['code']}")

        th_r_code, th_r_nom, th_r_vis, th_r_act = st.columns([2, 4, 2, 2])
        with th_r_code: st.markdown("**Code RAL**")
        with th_r_nom: st.markdown("**Désignation**")
        with th_r_vis: st.markdown("**Visuel de la teinte**")
        with th_r_act: st.markdown("**Action**")
        st.markdown("<hr style='margin:4px 0px; border-width:2px; border-color:black;'>", unsafe_allow_html=True)

        for idx_r, r_data in enumerate(rals_a_afficher):
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
        @st.dialog("➕ Créer un mélange", width="large")
        def ouvrir_ajout_melange_complet():
            m_ref = st.text_input("Référence du mélange")
            m_nom = st.text_input("Nom du mélange")
            m_cat = st.selectbox("Catégorie", ["Mélange Couleurs", "Autre Mélange"])
            m_emp = st.text_input("Emplacement de stockage")
            m_comm = st.text_input("Commentaire court (Formulation)")
            m_statut = st.radio("État du mélange :", ["Pas vérifié", "Vérifier"], index=0, horizontal=True)
            
            activer_ft = st.toggle("📝 Créer la Fiche Technique (FT)", value=False)
            ft_redacteur = OPTIONS_REDACTEURS[0]
            
            if activer_ft:
                if "champs_ft_mel" not in st.session_state: st.session_state["champs_ft_mel"] = []
                editeur_champs_dynamiques({"champs_ft": st.session_state["champs_ft_mel"]})
                ft_redacteur = st.selectbox("Rédacteur / Modifié par :", OPTIONS_REDACTEURS, index=0)

            if "tmp_form_state" not in st.session_state: st.session_state.tmp_form_state = {}

            st.markdown("---")
            container_selection = st.container()

            st.markdown("#### ➕ Ajouter des composants")
            recherche_filtre_c = st.text_input("🔍 Filtrer les composants (Nom, Réf, Code RAL, Élément existant) :").strip()

            st.markdown("**🎨 Couleurs du Nuancier :**")
            couleurs_trouvees = [c for c in liste_couleurs if not recherche_filtre_c or (recherche_filtre_c.lower() in c["nom_actuel"].lower() or recherche_filtre_c.lower() in c["ref"].lower() or recherche_filtre_c.lower() in c.get("ral", "").lower())]
            for idx, c in enumerate(couleurs_trouvees if recherche_filtre_c else couleurs_trouvees[:5]):
                key_c = f"color_{c['ref']}"
                if key_c not in st.session_state.tmp_form_state:
                    col_chk, col_vis = st.columns([7, 1])
                    with col_chk:
                        st.checkbox(f"{c['nom_actuel']} ({c['ref']})", value=False, key=f"chk_add_c_{idx}_{c['ref']}",
                                    on_change=add_tmp_item, args=("tmp_form_state", key_c, {"type": "couleur", "ref": c['ref'], "nom": c['nom_actuel'], "dosage": "100g", "commentaire_composant": ""}))
                    with col_vis: st.markdown(f'<div style="width:22px; height:22px; background-color:{c["visuel"]}; border-radius:50%; border:1px solid #000; margin-top:5px;"></div>', unsafe_allow_html=True)

            st.markdown("**🧪 Éléments (Additifs) :**")
            elements_trouves = [a for a in liste_additifs if not recherche_filtre_c or recherche_filtre_c.lower() in a["nom"].lower()]
            for idx, a in enumerate(elements_trouves if recherche_filtre_c else elements_trouves[:5]):
                key_a = f"additif_{a['nom']}"
                if key_a not in st.session_state.tmp_form_state:
                    col_chk_a, _ = st.columns([7, 1])
                    with col_chk_a:
                        st.checkbox(f"Élément : {a['nom']}", value=False, key=f"chk_add_add_{idx}_{a['nom']}",
                                    on_change=add_tmp_item, args=("tmp_form_state", key_a, {"type": "additif", "ref": a['nom'], "nom": a['nom'], "dosage": "10g", "commentaire_composant": ""}))

            with container_selection:
                st.markdown("### 🛠️ Composants de ce mélange :")
                cles_existantes = list(st.session_state.tmp_form_state.keys())
                if cles_existantes:
                    for idx, k in enumerate(cles_existantes):
                        v = st.session_state.tmp_form_state.get(k)
                        if not v: continue
                        col_chk, col_vis = st.columns([7, 1])
                        with col_chk:
                            label_aff = "ÉLÉMENT" if v['type'] == "additif" else v['type'].upper()
                            label_affichage = f"[{label_aff}] {v['nom']} ({v['ref']})"
                            widget_k = f"form_item_chk_{idx}_{v['ref']}"
                            
                            is_checked = st.checkbox(label_affichage, value=True, key=widget_k, on_change=remove_tmp_item_cb, args=("tmp_form_state", widget_k, k))
                            if is_checked:
                                st.session_state.tmp_form_state[k]["dosage"] = st.text_input(f"Dosage pour {v['nom']}", value=v["dosage"], key=f"dos_form_item_{idx}_{v['ref']}")
                                st.session_state.tmp_form_state[k]["commentaire_composant"] = st.text_input(f"Commentaire pour {v['nom']}", value=v.get("commentaire_composant", ""), key=f"comm_form_item_{idx}_{v['ref']}")
                        with col_vis:
                            if v.get("visuel"): st.markdown(f'<div style="width:22px; height:22px; background-color:{v["visuel"]}; border-radius:50%; border:1px solid #000; margin-top:5px;"></div>', unsafe_allow_html=True)
                else:
                    st.warning("Aucun composant sélectionné dans ce mélange.")

            st.markdown("---")
            if st.button("Enregistrer la formulation", type="primary"):
                if m_ref and m_nom:
                    comp = []
                    for k, v in st.session_state.tmp_form_state.items():
                        if est_dosage_valide(v.get("dosage", "")):
                            item_dict = {"ref": v["ref"], "nom": v["nom"], "dosage": v["dosage"], "commentaire_composant": v.get("commentaire_composant", "")}
                            if v["type"] == "couleur":
                                couleur_trouvee = next((x for x in liste_couleurs if x["ref"] == v["ref"]), None)
                                item_dict.update({"type": "couleur", "nom": couleur_trouvee["nom_actuel"] if couleur_trouvee else v["nom"], "visuel": couleur_trouvee["visuel"] if couleur_trouvee else "#CCCCCC"})
                            else:
                                item_dict.update({"type": "additif", "visuel": "#E2E8F0"})
                            comp.append(item_dict)
                    
                    today_str = datetime.datetime.now().strftime("%d/%m/%Y - %H:%M")
                    st.session_state.processus_db["preparation_melanges"]["melanges"].append({
                        "ref": m_ref, "nom": m_nom, "categorie_choisie": m_cat, "emplacement": m_emp,
                        "commentaire": m_comm, "couleurs_associees": comp, "statut": m_statut, "has_ft": activer_ft,
                        "fiche_technique": {
                            "date_creation": today_str, "date_derniere_maj": today_str, "date_avant_derniere_maj": "-",
                            "redacteur": ft_redacteur, "champs_ft": st.session_state.get("champs_ft_mel", [])
                        }
                    })
                    st.session_state.tmp_form_state = {}
                    st.session_state.pop("champs_ft_mel", None)
                    sauvegarder_donnees()
                    st.rerun()

        @st.dialog("✏️ Modifier une fiche de mélange", width="large")
        def ouvrir_modification_melange_complet(index, melange_data):
            init_key = f"mod_init_{index}"
            if init_key not in st.session_state:
                st.session_state.tmp_mod_state = {}
                for c in melange_data.get("couleurs_associees", []):
                    type_c = c.get("type", "couleur")
                    key = f"{type_c}_{c['ref']}"
                    st.session_state.tmp_mod_state[key] = {"type": type_c, "ref": c["ref"], "nom": c.get("nom", ""), "dosage": c["dosage"], "visuel": c.get("visuel"), "commentaire_composant": c.get("commentaire_composant", "")}
                st.session_state[init_key] = True

            if "tmp_mod_state" not in st.session_state: st.session_state.tmp_mod_state = {}

            m_ref = st.text_input("Référence du mélange", value=melange_data.get("ref", ""))
            m_nom = st.text_input("Nom du mélange", value=melange_data.get("nom", ""))
            m_cat = st.selectbox("Catégorie de rangement", ["Mélange Couleurs", "Autre Mélange"], index=["Mélange Couleurs", "Autre Mélange"].index(melange_data.get("categorie_choisie", "Mélange Couleurs")))
            m_statut = st.radio("État du mélange :", ["Pas vérifié", "Vérifier"], index=["Pas vérifié", "Vérifier"].index(melange_data.get("statut", "Pas vérifié")), horizontal=True)
            
            if melange_data.get("image_rendu"):
                st.caption("Aperçu de l'image actuelle :")
                afficher_image_base64(melange_data["image_rendu"]["data"], width=100)
            m_img_file = st.file_uploader("Remplacer ou importer l'image du mélange", type=["png", "jpg", "jpeg", "webp"])
            
            m_emp = st.text_input("Emplacement de stockage", value=melange_data.get("emplacement", ""))
            m_comm = st.text_input("Commentaire court (Formulation)", value=melange_data.get("commentaire", ""))

            fiche_tech_existante = melange_data.get("fiche_technique", {})
            has_ft_init = melange_data.get("has_ft", False)
            activer_ft = st.toggle("📝 Gérer la Fiche Technique (FT)", value=has_ft_init)

            if activer_ft:
                editeur_champs_dynamiques(fiche_tech_existante)
                idx_redacteur = OPTIONS_REDACTEURS.index(fiche_tech_existante.get("redacteur", "Labo / R&D")) if fiche_tech_existante.get("redacteur", "Labo / R&D") in OPTIONS_REDACTEURS else 0
                m_redacteur = st.selectbox("Rédacteur / Modifié par :", OPTIONS_REDACTEURS, index=idx_redacteur)

            st.markdown("---")
            container_selection_mod = st.container()

            st.markdown("#### ➕ Ajouter des composants")
            recherche_filtre_m = st.text_input("🔍 Filtrer les composants (Nom, Réf, Code RAL, Élément) :", key=f"rech_mod_{index}").strip()

            st.markdown("**🎨 Couleurs du Nuancier :**")
            couleurs_t = [c for c in liste_couleurs if not recherche_filtre_m or (recherche_filtre_m.lower() in c["nom_actuel"].lower() or recherche_filtre_m.lower() in c["ref"].lower())]
            for idx_c, c in enumerate(couleurs_t if recherche_filtre_m else couleurs_t[:5]):
                key_c = f"color_{c['ref']}"
                if key_c not in st.session_state.tmp_mod_state:
                    col_chk, _ = st.columns([7, 1])
                    with col_chk:
                        st.checkbox(f"{c['nom_actuel']} ({c['ref']})", value=False, key=f"chk_madd_c_{idx_c}_{c['ref']}",
                                    on_change=add_tmp_item, args=("tmp_mod_state", key_c, {"type": "couleur", "ref": c['ref'], "nom": c['nom_actuel'], "visuel": c["visuel"], "dosage": "100g", "commentaire_composant": ""}))

            st.markdown("**🧪 Éléments (Additifs) :**")
            elements_t = [a for a in liste_additifs if not recherche_filtre_m or recherche_filtre_m.lower() in a["nom"].lower()]
            for idx_a, a in enumerate(elements_t if recherche_filtre_m else elements_t[:5]):
                key_a = f"additif_{a['nom']}"
                if key_a not in st.session_state.tmp_mod_state:
                    col_chk_a, _ = st.columns([7, 1])
                    with col_chk_a:
                        st.checkbox(f"Élément : {a['nom']}", value=False, key=f"chk_madd_add_{idx_a}_{a['nom']}",
                                    on_change=add_tmp_item, args=("tmp_mod_state", key_a, {"type": "additif", "ref": a['nom'], "nom": a['nom'], "visuel": "#E2E8F0", "dosage": "10g", "commentaire_composant": ""}))

            with container_selection_mod:
                st.markdown("### 🛠️ Composants de ce mélange :")
                cles_existantes = list(st.session_state.tmp_mod_state.keys())

                if cles_existantes:
                    for idx_ex, k in enumerate(cles_existantes):
                        v = st.session_state.tmp_mod_state.get(k)
                        if not v: continue
                        col_chk, col_vis = st.columns([7, 1])
                        with col_chk:
                            label_aff = "ÉLÉMENT" if v['type'] == "additif" else v['type'].upper()
                            label_affichage = f"[{label_aff}] {v['nom']} ({v['ref']})"
                            widget_k = f"mod_item_chk_{idx_ex}_{v['ref']}"
                            
                            is_checked = st.checkbox(label_affichage, value=True, key=widget_k, on_change=remove_tmp_item_cb, args=("tmp_mod_state", widget_k, k))
                            if is_checked:
                                st.session_state.tmp_mod_state[k]["dosage"] = st.text_input(f"Dosage pour {v['nom']}", value=v["dosage"], key=f"dos_mod_item_{idx_ex}_{v['ref']}")
                                st.session_state.tmp_mod_state[k]["commentaire_composant"] = st.text_input(f"Commentaire pour {v['nom']}", value=v.get("commentaire_composant", ""), key=f"comm_mod_item_{idx_ex}_{v['ref']}")
                        with col_vis:
                            if v.get("visuel"): st.markdown(f'<div style="width:22px; height:22px; background-color:{v["visuel"]}; border-radius:50%; border:1px solid #000; margin-top:5px;"></div>', unsafe_allow_html=True)
                else:
                    st.warning("Aucun composant sélectionné dans ce mélange.")

            st.markdown("---")
            if st.button("Mettre à jour le mélange", type="primary"):
                comp_finaux = []
                for k, v in st.session_state.tmp_mod_state.items():
                    if est_dosage_valide(v.get("dosage", "")):
                        item_dict = {"ref": v["ref"], "nom": v["nom"], "dosage": v["dosage"], "commentaire_composant": v.get("commentaire_composant", "")}
                        if v["type"] == "couleur":
                            couleur_trouvee = next((x for x in liste_couleurs if x["ref"] == v["ref"]), None)
                            item_dict.update({"type": "couleur", "nom": couleur_trouvee["nom_actuel"] if couleur_trouvee else v["nom"], "visuel": couleur_trouvee["visuel"] if couleur_trouvee else v.get("visuel", "#CCCCCC")})
                        else:
                            item_dict.update({"type": "additif", "visuel": "#E2E8F0"})
                        comp_finaux.append(item_dict)

                today_str = datetime.datetime.now().strftime("%d/%m/%Y - %H:%M")
                d_crea, d_der, d_av = gerer_historique_dates(fiche_tech_existante, today_str)

                fiche_tech_existante.update({"date_creation": d_crea, "date_derniere_maj": d_der, "date_avant_derniere_maj": d_av})
                if activer_ft:
                    fiche_tech_existante["redacteur"] = m_redacteur

                img_final = encoder_fichier_local(m_img_file) if m_img_file else melange_data.get("image_rendu")
                st.session_state.processus_db["preparation_melanges"]["melanges"][index].update({
                    "ref": m_ref, "nom": m_nom, "categorie_choisie": m_cat, "emplacement": m_emp,
                    "commentaire": m_comm, "couleurs_associees": comp_finaux,
                    "statut": m_statut, "has_ft": activer_ft, "fiche_technique": fiche_tech_existante, "image_rendu": img_final
                })
                st.session_state.tmp_mod_state.clear()
                if init_key in st.session_state: del st.session_state[init_key]
                sauvegarder_donnees()
                st.rerun()

        if st.button("Créer une fiche de mélange", type="primary"):
            ouvrir_ajout_melange_complet()

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

            col_info_mel, col_export_mel = st.columns([4, 1])
            with col_info_mel:
                st.info(f"📊 **Nombre de mélanges trouvés :** {len(melanges_filtres)}")
            with col_export_mel:
                donnees_mel_export = [item["data"] for item in melanges_filtres]
                excel_data, nom_fichier, mime_type = generer_fichier_export(donnees_mel_export, "Export_Melanges")
                if excel_data:
                    st.download_button("📥 Exporter Excel", data=excel_data, file_name=nom_fichier, mime=mime_type, use_container_width=True)

            melanges_couleurs = [item for item in melanges_filtres if item["data"].get("categorie_choisie", "Mélange Couleurs") == "Mélange Couleurs"]
            autres_melanges = [item for item in melanges_filtres if item["data"].get("categorie_choisie", "Mélange Couleurs") != "Mélange Couleurs"]

            onglet_c1, onglet_c2 = st.tabs(["🎨 Mélanges Couleurs", "⚙️ Autres Mélanges"])

            def afficher_tableau_melanges(liste_m_categorie, identifiant_unique):
                if liste_m_categorie:
                    if len(liste_m_categorie) > MAX_LIGNES_AFFICHAGE:
                        st.warning(f"⚠️ Affichage limité aux {MAX_LIGNES_AFFICHAGE} premiers résultats. Utilisez les filtres.")
                    liste_a_afficher = liste_m_categorie[:MAX_LIGNES_AFFICHAGE]

                    th_m_ref, th_m_nom, th_m_vis, th_m_comp, th_m_emp, th_m_com, th_m_act = st.columns([0.8, 1.2, 0.8, 3.2, 1.2, 2.3, 2.5])
                    with th_m_ref: st.markdown("**Référence**")
                    with th_m_nom: st.markdown("**Nom mélange**")
                    with th_m_vis: st.markdown("**Aperçu**")
                    with th_m_comp: st.markdown("**Couleurs & Éléments**")
                    with th_m_emp: st.markdown("**Emplacement**")
                    with th_m_com: st.markdown("**Commentaires**")
                    with th_m_act: st.markdown("**Actions**")
                    st.markdown("<hr style='margin:4px 0px; border-width:2px; border-color:black;'>", unsafe_allow_html=True)

                    for item_m in liste_a_afficher:
                        idx_m = item_m["index_origine"]
                        melange = item_m["data"]
                        is_verified = melange.get("statut") == "Vérifier"
                        txt_style = "color: #CC0605; font-weight: bold;" if is_verified else "color: inherit;"
                        
                        tr_m_ref, tr_m_nom, tr_m_vis, tr_m_comp, tr_m_emp, tr_m_com, tr_m_act = st.columns([0.8, 1.2, 0.8, 3.2, 1.2, 2.3, 2.5])
                        
                        pastille_mel = "🔴 " if is_verified else ""
                        with tr_m_ref: st.markdown(f'<span style="{txt_style}"><b>{pastille_mel}{str(melange.get("ref", "")).title()}</b></span>', unsafe_allow_html=True)
                        with tr_m_nom: st.markdown(f'<span style="{txt_style}">{str(melange.get("nom", "")).title()}</span>', unsafe_allow_html=True)
                        with tr_m_vis:
                            if melange.get("image_rendu"): afficher_image_base64(melange["image_rendu"]["data"], width=45)
                            else: st.caption("Pas d'image")
                        with tr_m_comp:
                            for t in melange.get("couleurs_associees", []):
                                type_comp = t.get("type", "couleur")
                                comm_comp_aff = f" ({t['commentaire_composant']})" if t.get("commentaire_composant") else ""
                                if type_comp == "couleur":
                                    st.markdown(f'<div style="display:flex; align-items:center;"><div style="width:14px; height:14px; background-color:{t.get("visuel","#CCCCCC")}; border-radius:50%; margin-right:6px; border:1px solid #333;"></div><span style="{txt_style}">Nuancier : {str(t["nom"]).title()} ➔ <b>{str(t["dosage"]).title()}</b>{comm_comp_aff}</span></div>', unsafe_allow_html=True)
                                elif type_comp == "melange_base":
                                    st.markdown(f'<div style="display:flex; align-items:center;"><div style="width:14px; height:14px; background-color:#CBD5E1; border-radius:2px; margin-right:6px; border:1px solid #333;"></div><span style="{txt_style}">Base : {str(t["nom"]).title()} ➔ <b>{str(t["dosage"]).title()}</b>{comm_comp_aff}</span></div>', unsafe_allow_html=True)
                                else:
                                    st.markdown(f'<div style="display:flex; align-items:center;"><span style="{txt_style}">Élément : {str(t["nom"]).title()} ➔ <b>{str(t["dosage"]).title()}</b>{comm_comp_aff}</span></div>', unsafe_allow_html=True)

                        with tr_m_emp: st.markdown(f'<span style="{txt_style}">{str(melange.get("emplacement", "")).title()}</span>', unsafe_allow_html=True)
                        with tr_m_com: st.markdown(f'<span style="{txt_style}">{str(melange.get("commentaire", "")) or "-"}</span>', unsafe_allow_html=True)

                        with tr_m_act:
                            col_me1, col_me2, col_me3, col_pdf = st.columns([1, 1, 1, 2])
                            with col_me1:
                                if st.button("✏️", key=f"edit_m_{identifiant_unique}_{idx_m}"): ouvrir_modification_melange_complet(idx_m, melange)
                            with col_me2:
                                if st.button("🗑️", key=f"del_m_{identifiant_unique}_{idx_m}"): st.session_state[f"del_confirm_{identifiant_unique}_{idx_m}"] = True
                            with col_me3:
                                if st.button("👁️", key=f"det_m_{identifiant_unique}_{idx_m}"): ouvrir_details_melange(melange)
                            with col_pdf:
                                if melange.get("has_ft"):
                                    if st.button("📄 FT", key=f"view_pdf_{identifiant_unique}_{idx_m}"): ouvrir_visualisation_ft(melange)

                        if st.session_state.get(f"del_confirm_{identifiant_unique}_{idx_m}", False):
                            st.warning("Supprimer ?")
                            if st.button("Oui", key=f"y_{identifiant_unique}_{idx_m}"):
                                st.session_state.processus_db["preparation_melanges"]["melanges"].pop(idx_m)
                                sauvegarder_donnees()
                                st.rerun()
                            if st.button("Non", key=f"n_{identifiant_unique}_{idx_m}"):
                                st.session_state[f"del_confirm_{identifiant_unique}_{idx_m}"] = False
                                st.rerun()
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
                sauvegarder_donnees()
                st.rerun()

        if "click_node_id" in st.query_params and "click_fiche_idx" in st.query_params:
            try:
                c_nid = int(st.query_params["click_node_id"])
                c_fidx = int(st.query_params["click_fiche_idx"])
                st.query_params.clear()
                if c_fidx < len(fiches_m):
                    for idx_shape, s in enumerate(fiches_m[c_fidx]["formes"]):
                        if s["id"] == c_nid: ouvrir_edition_bloc_methode(c_fidx, idx_shape, s)
            except Exception:
                pass

        if st.button("Créer une Fiche Méthode (Page vierge)", type="primary"): ouvrir_ajout_fiche_methode()
        if fiches_m:
            noms_fiches = [f["nom"] for f in fiches_m]
            fiche_choisie_nom = st.selectbox("Fiche Méthode active :", noms_fiches)
            idx_fid = noms_fiches.index(fiche_choisie_nom)
            fiche = fiches_m[idx_fid]

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
                            sauvegarder_donnees()
                            st.rerun()

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
                                sauvegarder_donnees()
                                st.rerun()

            with col_canvas:
                list_nodes = []
                for f in fiche["formes"]:
                    node_dict = {"id": f["id"], "label": f["label"], "shape": f["shape"], "color": {"background": f.get("color", "#E0F2FE"), "border": "#1E293B"}, "margin": 10}
                    if f.get("x") is not None and f.get("y") is not None:
                        node_dict["x"], node_dict["y"] = f["x"], f["y"]
                    list_nodes.append(node_dict)

                edges_data = [{"from": lien["from"], "to": lien["to"], "arrows": "to", "color": {"color": "#475569"}} for lien in fiche["liaisons"]]
                nodes_json, edges_json = json.dumps(list_nodes), json.dumps(edges_data)

                vis_html = f"""
                <div id="mynetwork" style="width: 100%; height: 580px; background-color: transparent; border: 2px dashed #CBD5E1; border-radius: 8px;"></div>
                <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
                <script type="text/javascript">
                  var container = document.getElementById('mynetwork');
                  var options = {{ physics: {{ enabled: false }}, interaction: {{ dragNodes: true, dragView: false, zoomView: true }}, nodes: {{ font: {{ size: 14, face: 'Arial' }}, borderWidth: 2 }} }};
                  var network = new vis.Network(container, {{ nodes: new vis.DataSet({nodes_json}), edges: new vis.DataSet({edges_json}) }}, options);

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