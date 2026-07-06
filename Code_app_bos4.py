import streamlit as st
import json
import os
import base64
from PIL import Image
import io
import re
import datetime
import streamlit.components.v1 as components

# Essayer d'importer ReportLab pour la génération du PDF standard
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    REPORTLAB_DISPO = True
except ImportError:
    REPORTLAB_DISPO = False

# --- CONFIGURATION INITIALE ---
if "etat_sidebar" not in st.session_state:
    st.session_state.etat_sidebar = "expanded"

st.set_page_config(
    page_title="BOS2 - Gestion Industrielle",
    layout="wide",
    initial_sidebar_state=st.session_state.etat_sidebar
)

# --- OPTIONS GLOBALES ---
OPTIONS_REDACTEURS = ["Labo / R&D", "Atelier: couleurs", "Atelier: perles/croix", "Atelier: pose peinture", "Atelier: moulage", "Atelier: résine", "Atelier: finition", "Atelier: assemblage"]

# --- CSS PERSONNALISÉ ET BOUTON D'AIDE FLOTTANT ---
st.markdown("""
<style>
.text-highlight { background-color: #CC0605; padding: 2px 6px; border-radius: 4px; color: white; font-weight: bold; }
.verified-text { color: #CC0605 !important; }
.verified-text span, .verified-text b, .verified-text p, .verified-text div { color: #CC0605 !important; }
.normal-row { background-color: transparent; padding: 12px; margin-bottom: 8px; }
.floating-btn {
    position: fixed; bottom: 30px; right: 30px; background-color: #1E293B; color: white !important;
    border-radius: 50%; width: 55px; height: 55px; display: flex; align-items: center; justify-content: center;
    font-size: 26px; box-shadow: 2px 4px 10px rgba(0,0,0,0.3); z-index: 99999; text-decoration: none;
    transition: transform 0.2s, background-color 0.2s;
}
.floating-btn:hover { transform: scale(1.1); background-color: #334155; color: white; }
</style>
<a href="?action=help" target="_self" class="floating-btn" title="Besoin d'aide ?">❔</a>
""", unsafe_allow_html=True)

FICHIER_SAUVEGARDE = "donnees_bos2.json"

# --- UTILITAIRES ---
def get_svg_icon(icon_name):
    icons = {
        "search": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>',
        "chart": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>'
    }
    return icons.get(icon_name, "")

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
    [data-testid="stAppViewContainer"] {{
        background-image: url("data:image/png;base64,{LOGO_BACKGROUND_BASE64}");
        background-size: 45%;
        background-repeat: no-repeat;
        background-position: center center;
        background-attachment: fixed;
    }}
    [data-testid="stAppViewContainer"]::before {{
        content: ""; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
        background-color: rgba(255, 255, 255, 0.90); z-index: 0;
    }}
    [data-testid="stHeader"], [data-testid="stVerticalBlock"], .stMain {{ position: relative; z-index: 1; background-color: transparent !important; }}
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
    
    if derniere_maj != date_edition_str:
        avant_derniere_maj = derniere_maj
        derniere_maj = date_edition_str
        
    return date_crea, derniere_maj, avant_derniere_maj

# --- BASE DE DONNÉES NUANCIER RAL OFFICIEL ---
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
        except Exception:
            pass
    return {"creation_processus": {}, "preparation_melanges": {"couleurs": [], "melanges": [], "fiches_methode": [], "additifs": [], "base_rals": []}}

def sauvegarder_donnees():
    with open(FICHIER_SAUVEGARDE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.processus_db, f, ensure_ascii=False, indent=4)

if "processus_db" not in st.session_state: st.session_state.processus_db = charger_donnees()
if "groupe_actif" not in st.session_state: st.session_state.groupe_actif = None
if "produit_selectionne" not in st.session_state: st.session_state.produit_selectionne = None
if "sub_section_melange" not in st.session_state: st.session_state.sub_section_melange = "🎨 Nuancier de couleurs"

# --- GENERATEUR DE FICHE TECHNIQUE STANDARD PDF (REPORTLAB) ---
def generer_pdf_fiche_technique(data_obj, type_ft="melange"):
    buffer = io.BytesIO()
    if not REPORTLAB_DISPO:
        buffer.write(b"ReportLab non disponible.")
        buffer.seek(0)
        return buffer

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []

    title_style = ParagraphStyle('TitleStyle', fontName='Helvetica-Bold', fontSize=20, textColor=colors.HexColor('#CC0605'), alignment=2, spaceBefore=15)
    h2_style = ParagraphStyle('H2Style', fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor('#1E293B'), spaceBefore=10, spaceAfter=6)
    body_style = ParagraphStyle('BodyStyle', fontName='Helvetica', fontSize=9, leading=13, textColor=colors.HexColor('#334155'))
    body_bold = ParagraphStyle('BodyBold', fontName='Helvetica-Bold', fontSize=9, leading=13, textColor=colors.HexColor('#1E293B'))

    # EN-TÊTE : Logo à gauche plus grand / Titre à droite
    header_data = [["", Paragraph("FICHE TECHNIQUE PRODUIT" if type_ft == "melange" else "FICHE TECHNIQUE ÉLÉMENT", title_style)]]
    header_table = Table(header_data, colWidths=[170, 330])
    
    img_path = "Logo-Beraudy-rectangle.png"
    if os.path.exists(img_path):
        from reportlab.platypus import Image as RLImage
        img_rl = RLImage(img_path, width=160, height=56)
        img_rl.hAlign = 'LEFT'
        header_table._cellvalues[0][0] = img_rl

    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LINEBELOW', (0,0), (-1,-1), 1, colors.HexColor('#CC0605'))
    ]))
    story.append(header_table)
    story.append(Spacer(1, 15))

    ft_data = data_obj.get("fiche_technique", {})

    # CADRE 1 : INFORMATIONS GÉNÉRALES
    story.append(Paragraph("Informations Générales", h2_style))
    if type_ft == "melange":
        infos_rows = [
            [Paragraph("<b>Nom du Mélange :</b>", body_style), Paragraph(data_obj.get("nom", "-"), body_style)],
            [Paragraph("<b>Référence interne :</b>", body_style), Paragraph(data_obj.get("ref", "-"), body_style)],
            [Paragraph("<b>Stockage / Emplacement :</b>", body_style), Paragraph(data_obj.get("emplacement", "-"), body_style)]
        ]
    else:
        infos_rows = [
            [Paragraph("<b>Nom de l'élément :</b>", body_style), Paragraph(data_obj.get("nom", "-"), body_style)],
            [Paragraph("<b>Code :</b>", body_style), Paragraph(data_obj.get("code", "-"), body_style)],
            [Paragraph("<b>Désignation :</b>", body_style), Paragraph(data_obj.get("designation", "-"), body_style)],
            [Paragraph("<b>Fournisseur :</b>", body_style), Paragraph(data_obj.get("fournisseur", "-"), body_style)],
            [Paragraph("<b>Code Article Achat :</b>", body_style), Paragraph(data_obj.get("code_article", "-"), body_style)],
            [Paragraph("<b>Désignation Achat :</b>", body_style), Paragraph(data_obj.get("designation_achat", "-"), body_style)]
        ]
    
    t_infos = Table(infos_rows, colWidths=[150, 350])
    t_infos.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#E2E8F0'))
    ]))
    story.append(t_infos)

    # CADRE 2 : SPÉCIFICATIONS TECHNIQUES / CARACTÉRISTIQUES
    if type_ft == "melange":
        story.append(Paragraph("Spécifications Physico-Chimiques", h2_style))
        spec_rows = [
            [Paragraph("<b>Aspect / Finition :</b>", body_style), Paragraph(ft_data.get("aspect", "Non renseigné"), body_style), Paragraph("<b>Densité :</b>", body_style), Paragraph(ft_data.get("densite", "Non renseigné"), body_style)],
            [Paragraph("<b>Viscosité :</b>", body_style), Paragraph(ft_data.get("viscosite", "Non renseigné"), body_style), Paragraph("<b>pH :</b>", body_style), Paragraph(ft_data.get("ph", "Non renseigné"), body_style)],
            [Paragraph("<b>Taux de COV :</b>", body_style), Paragraph(ft_data.get("cov", "Non renseigné"), body_style), Paragraph("<b>Temps de séchage :</b>", body_style), Paragraph(ft_data.get("sechage", "Non renseigné"), body_style)],
            [Paragraph("<b>Conditions d'application :</b>", body_style), Paragraph(ft_data.get("conditions", "Non renseigné"), body_style), "", ""]
        ]
        t_spec = Table(spec_rows, colWidths=[110, 140, 110, 140])
        t_spec.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFFFF')),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('SPAN', (1, 3), (3, 3)),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0'))
        ]))
        story.append(t_spec)
    else:
        story.append(Paragraph("Propriétés & Sécurités", h2_style))
        danger_txt = f"DANGER : {data_obj.get('danger_texte', '')}" if data_obj.get("danger") == "Oui" else "Aucun risque signalé"
        spec_rows = [
            [Paragraph("<b>Nature physique :</b>", body_style), Paragraph(data_obj.get("nature", "-"), body_style)],
            [Paragraph("<b>Risques & Dangers :</b>", body_style), Paragraph(danger_txt, body_style)],
            [Paragraph("<b>Instructions Manipulation :</b>", body_style), Paragraph(data_obj.get("manipulation", "-") or "Aucune consigne spécifique", body_style)]
        ]
        t_spec = Table(spec_rows, colWidths=[150, 350])
        t_spec.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFFFF')),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#E2E8F0'))
        ]))
        story.append(t_spec)

    # CADRE 3 : FORMULATION (UNIQUEMENT POUR MÉLANGES)
    if type_ft == "melange":
        story.append(Paragraph("Formulation de Base Associée", h2_style))
        data_comp = [[Paragraph("<b>Composant</b>", body_bold), Paragraph("<b>Dosage</b>", body_bold), Paragraph("<b>Commentaire d'origine</b>", body_bold)]]
        
        db_prep = st.session_state.processus_db.get("preparation_melanges", {})
        for c in data_obj.get("couleurs_associees", []):
            comm_src = ""
            if c.get('type') == "additif" or c.get('type') == "element":
                item = next((a for a in db_prep.get("additifs", []) if a["nom"] == c.get("ref")), None)
                if item: comm_src = item.get("commentaire", "")
            elif c.get('type') == "melange_base":
                item = next((m for m in db_prep.get("melanges", []) if m["ref"] == c.get("ref")), None)
                if item: comm_src = item.get("commentaire", "")

            data_comp.append([Paragraph(f"{c.get('nom')} ({c.get('ref')})", body_style), Paragraph(c.get('dosage', '-'), body_style), Paragraph(comm_src, body_style)])

        if len(data_comp) > 1:
            t_comp = Table(data_comp, colWidths=[180, 100, 220])
            t_comp.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E2E8F0')),
                ('PADDING', (0, 0), (-1, -1), 5),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1'))
            ]))
            story.append(t_comp)
        else:
            story.append(Paragraph("Aucune formulation liée.", body_style))

    # CADRE 4 : HISTORIQUE DES DATES
    story.append(Paragraph("Suivi et Historique de la Fiche", h2_style))
    date_rows = [
        [Paragraph("<b>Création :</b>", body_style), Paragraph(ft_data.get("date_creation", ft_data.get("date", "-")), body_style),
         Paragraph("<b>Dernière MÀJ :</b>", body_style), Paragraph(ft_data.get("date_derniere_maj", "-"), body_style),
         Paragraph("<b>MÀJ Précédente :</b>", body_style), Paragraph(ft_data.get("date_avant_derniere_maj", "-"), body_style)]
    ]
    t_date = Table(date_rows, colWidths=[65, 80, 85, 80, 100, 90])
    t_date.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0'))
    ]))
    story.append(t_date)

    # CADRE 5 : COMMENTAIRE GLOBAL FINAL
    story.append(Paragraph("Commentaires Généraux / Notes", h2_style))
    comm_global = data_obj.get("commentaire_global", "")
    t_comm = Table([[Paragraph(comm_global or "Aucun commentaire général enregistré.", body_style)]], colWidths=[500])
    t_comm.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFBEB')),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#F59E0B'))
    ]))
    story.append(t_comm)

    # SIGNATURE AVEC REDACTEUR DYNAMIQUE
    story.append(Spacer(1, 20))
    redacteur = ft_data.get('redacteur', 'Labo / R&D')
    data_sign = [
        [Paragraph(f"<b>Modifié / Rédigé par :</b> {redacteur}", body_style), Paragraph("<b>Approuvé par :</b> Responsable Qualité", body_style)],
        [Paragraph("<br/><br/>Visa :", body_style), Paragraph("<br/><br/>Visa :", body_style)]
    ]
    t_sign = Table(data_sign, colWidths=[250, 250])
    t_sign.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBEFORE', (1, 0), (1, -1), 0.5, colors.HexColor('#CBD5E1'))
    ]))
    story.append(t_sign)

    doc.build(story)
    buffer.seek(0)
    return buffer

# --- VISUALISATIONS DIALOGS (STREAMLIT UI) ---
# --- FONCTIONS DE VISUALISATION AMÉLIORÉES ---

def generer_miniature_ft(data_obj):
    """Génère une vue texte/simplifiée des specs pour la miniature dans la dialog."""
    ft = data_obj.get("fiche_technique", {})
    if not ft or not ft.get("aspect"): return None
    return f"Aspect: {ft.get('aspect', '-')}\nDensité: {ft.get('densite', '-')}\nViscosité: {ft.get('viscosite', '-')}"

@st.dialog("📄 Visualisation Fiche Technique", width="large")
def ouvrir_visualisation_ft(melange):
    st.markdown(f"### 📄 Fiche Technique : {melange.get('nom')}")
    ft = melange.get("fiche_technique", {})
    
    # 1. Barre d'infos dates
    st.info(f"📅 **Création :** {ft.get('date_creation','-')} | 🔄 **Dernière MÀJ :** {ft.get('date_derniere_maj','-')} | ⏳ **Avant-dernière MÀJ :** {ft.get('date_avant_derniere_maj','-')}")
    
    # 2. Miniature et actions
    col_visu, col_actions = st.columns([1, 2])
    
    with col_visu:
        miniature = generer_miniature_ft(melange)
        if miniature:
            st.markdown("**Aperçu des specs :**")
            st.code(miniature)
        else:
            st.warning("Aucune donnée technique pour générer une miniature.")

    with col_actions:
        st.markdown("**Actions :**")
        c1, c2, c3 = st.columns(3)
        c1.download_button("⬇️ PDF", data=generer_pdf_fiche_technique(melange, "melange"), file_name=f"FT_{melange.get('ref')}.pdf", mime="application/pdf", use_container_width=True)
        if c2.button("📋 Copier", use_container_width=True): st.toast("Contenu copié !")
        if c3.button("🔗 Partager", use_container_width=True): st.toast("Lien de partage généré !")

@st.dialog("📄 Fiche Technique - Élément", width="large")
def ouvrir_visualisation_ft_additif(additif):
    st.markdown(f"### 📄 Fiche Technique Élément : {additif.get('nom')}")
    ft = additif.get("fiche_technique", {})
    st.info(f"📅 **Création :** {ft.get('date_creation','-')} | 🔄 **Dernière MÀJ :** {ft.get('date_derniere_maj','-')}")
    
    col_visu, col_actions = st.columns([1, 2])
    with col_visu:
        st.markdown("**Nature :**")
        st.write(additif.get("nature", "-"))
        
    with col_actions:
        st.markdown("**Actions :**")
        c1, c2, c3 = st.columns(3)
        c1.download_button("⬇️ PDF", data=generer_pdf_fiche_technique(additif, "additif"), file_name=f"FT_Element_{additif.get('nom')}.pdf", mime="application/pdf", use_container_width=True)
        if c2.button("📋 Copier", use_container_width=True): st.toast("Contenu copié !")
        if c3.button("🔗 Partager", use_container_width=True): st.toast("Lien de partage généré !")
@st.dialog("👁️ Détails complets du mélange", width="large")
def ouvrir_details_melange(melange):
    st.markdown(f"### 🧪 {melange.get('nom')} ({melange.get('ref')})")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.markdown(f"**Catégorie:** {melange.get('categorie_choisie', 'Non défini')}")
        st.markdown(f"**Emplacement:** {melange.get('emplacement', 'Non défini')}")
        st.markdown(f"**État:** {melange.get('statut', 'Non défini')}")
    with col_d2:
        if melange.get("image_rendu"):
            st.caption("Aperçu du rendu :")
            afficher_image_base64(melange["image_rendu"]["data"], width=150)
        else:
            st.caption("Aucune image associée.")
    
    st.markdown(f"**Commentaire court:**\n> {melange.get('commentaire', '-')}")
    
    st.markdown("---")
    st.markdown("#### 📄 Fiche Technique (Aperçu)")
    has_ft = melange.get("has_ft", False)
    if has_ft:
        ft = melange.get("fiche_technique", {})
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Aspect :** {ft.get('aspect', '-')}")
            st.markdown(f"**Viscosité :** {ft.get('viscosite', '-')}")
            st.markdown(f"**Densité :** {ft.get('densite', '-')}")
            st.markdown(f"**Rédigé par :** {ft.get('redacteur', 'Labo / R&D')}")
        with c2:
            st.markdown(f"**pH :** {ft.get('ph', '-')}")
            st.markdown(f"**COV :** {ft.get('cov', '-')}")
            st.markdown(f"**Séchage :** {ft.get('sechage', '-')}")
        st.markdown(f"**Conditions :** {ft.get('conditions', '-')}")
        st.markdown(f"**Commentaire FT :**\n> {melange.get('commentaire_global', '-')}")
    else:
        st.info("Aucune Fiche Technique enregistrée pour ce mélange.")

    st.markdown("---")
    st.markdown("#### 🧱 Formulation (Composants)")
    comp_list = melange.get("couleurs_associees", [])
    if comp_list:
        for c in comp_list:
            t_comp = c.get('type', 'composant').replace('additif', 'élément')
            st.markdown(f"""
            <div style="display:flex; align-items:center; margin-bottom: 5px; padding: 5px; background: #F8FAFC; border-radius: 4px;">
                <div style="width:16px; height:16px; background-color:{c.get('visuel','#CCCCCC')}; border-radius:50%; margin-right:10px; border:1px solid #333;"></div>
                <span style="flex-grow: 1;"><b>[{t_comp.upper()}]</b> {c.get('nom')} ({c.get('ref')})</span>
                <span style="font-weight: bold; color: #CC0605; background: white; padding: 2px 6px; border-radius: 4px; border: 1px solid #E2E8F0;">Dosage: {c.get('dosage', '-')}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("Aucun composant sélectionné dans ce mélange.")
        
    if st.button("Fermer la vue", use_container_width=True):
        st.rerun()

# --- MODALES POUR PROCESSUS & METHODES ---
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

# --- URL ROUTING & AIDE ---
query_params = st.query_params
@st.dialog("❓ Centre d'Aide BOS2", width="large")
def ouvrir_fenetre_aide():
    st.markdown("### 💬 Besoin d'assistance ?")
    st.info("Cette section sera enrichie avec la documentation complète, les tutoriels d'utilisation et les contacts de votre support technique.")
    if st.button("Fermer l'aide", type="primary", use_container_width=True): st.rerun()

if "action" in query_params and query_params["action"] == "help":
    st.query_params.clear()
    ouvrir_fenetre_aide()

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
                    s["x"], s["y"] = m_fx, m_fy
                    sauvegarder_donnees()
        st.query_params.clear()
    except Exception:
        pass

# --- CONTENU DE LA BARRE LATÉRALE ---
with st.sidebar:
    st.markdown('<div style="text-align: center; margin-top: 10px;"><h2>BOS2 PORTAIL</h2></div>', unsafe_allow_html=True)
    st.markdown("---")

st.markdown("<br>", unsafe_allow_html=True)
search_icon = get_svg_icon("search")
st.markdown(f'<div style="display:flex; align-items:center;">{search_icon}<span>RECHERCHE ULTRA-RAPIDE (Filtre instantané)...</span></div>', unsafe_allow_html=True)
recherche_globale = st.text_input("", label_visibility="collapsed").strip()

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
    for idx_m, m in enumerate(st.session_state.processus_db["preparation_melanges"].get("melanges", [])):
        if any(recherche_globale.lower() in str(m.get(k, "")).lower() for k in ["ref", "nom", "emplacement"]):
            resultats_trouves.append({"label": f"Mélange : {m.get('nom')} ({m.get('ref')})", "chemin": "Mélanges ➔ Formulations", "cat": "preparation_melanges", "prod": "SECTION_MELANGES"})

    if resultats_trouves:
        for idx_r, res in enumerate(resultats_trouves):
            col_res_txt, col_res_btn = st.columns([4, 1])
            with col_res_txt:
                st.markdown(f"**{res['label']}**")
                st.caption(f"📍 Chemin : {res['chemin']}")
            with col_res_btn:
                if st.button(f"Accéder", key=f"global_res_{idx_r}"):
                    st.session_state.groupe_actif = res["cat"]
                    if res["prod"] == "SECTION_COULEURS": st.session_state.sub_section_melange = "🎨 Nuancier de couleurs"
                    elif res["prod"] == "SECTION_MELANGES": st.session_state.sub_section_melange = "⚗️ Formulations d'atelier"
                    else: st.session_state.produit_selectionne = res["prod"]
                    st.rerun()
            st.markdown("<hr style='margin: 0.3em 0px; opacity: 0.15;'>", unsafe_allow_html=True)
    else:
        st.info("Aucun résultat trouvé.")
    st.markdown("---")

if st.session_state.groupe_actif is None:
    st.title("Portail Industriel BOS2")
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

# ---------------------------------------------------------
# MODULE 1 : CRÉATION DES PROCESSUS
# ---------------------------------------------------------
if G_ACTIF == "creation_processus":
    db_courante = st.session_state.processus_db[G_ACTIF]
    st.sidebar.title("🏗️ Édition SOP")
    recherche_sidebar = st.sidebar.text_input("🔍 Filtrer la liste...", "").strip()
    liste_produits = sorted(list(db_courante.keys()))
    if recherche_sidebar: liste_produits = sorted([p for p in liste_produits if recherche_sidebar.lower() in p.lower()])

    if liste_produits: st.info(f"📊 **Nombre de processus :** {len(liste_produits)} | **Premier :** {liste_produits[0]} | **Dernier :** {liste_produits[-1]}")
    else: st.sidebar.warning("Aucun processus trouvé")

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
                        if etape.get("is_local") and etape.get("media_data"):
                            afficher_image_base64(etape["media_data"]["data"])
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
                        st.rerun()
            with c_hex_col: c_hex = st.color_picker("Sélectionner la nuance", value=st.session_state["add_hex"])

            if st.button("Enregistrer la couleur", type="primary"):
                if c_ref:
                    num_ral = ''.join(filter(str.isdigit, c_ral.strip()))
                    couleur_finale = RAL_DICT.get(num_ral, c_hex) if num_ral else c_hex
                    st.session_state.processus_db["preparation_melanges"]["couleurs"].append({
                        "ref": c_ref, "nom_actuel": c_actuel, "nom_futur": c_futur,
                        "ral": c_ral, "societe": c_societe, "type": c_type, "visuel": couleur_finale
                    })
                    st.session_state.pop("add_ral", None)
                    st.session_state.pop("add_hex", None)
                    sauvegarder_donnees()
                    st.rerun()

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
            m_type = st.selectbox("Type", ["Opaque", "Translucide", "2"], index=["Opaque", "Translucide", "2"].index(st.session_state[f"temp_type_{index}"]), key=f"temp_type_{index}")

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
                for k in [f"temp_ref_{index}", f"temp_actuel_{index}", f"temp_futur_{index}", f"temp_soc_{index}", f"temp_type_{index}", f"temp_ral_{index}", f"temp_hex_{index}"]:
                    st.session_state.pop(k, None)
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

            if couleurs_filtrees: st.info(f"📊 **Nombre de couleurs :** {len(couleurs_filtrees)} | **Première :** {couleurs_filtrees[0]['data'].get('nom_actuel','')} ({couleurs_filtrees[0]['data'].get('ref','')}) | **Dernière :** {couleurs_filtrees[-1]['data'].get('nom_actuel','')} ({couleurs_filtrees[-1]['data'].get('ref','')})")

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
                idx_c = item["index_origine"]
                c_data = item["data"]
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
                            if st.button("🗑️", key=f"d_col_{idx_c}"):
                                st.session_state[key_del_c] = True
                                st.rerun()
                        else:
                            if st.button("Confirmer", key=f"d_col_y_{idx_c}", type="primary"):
                                st.session_state.processus_db["preparation_melanges"]["couleurs"].pop(idx_c)
                                sauvegarder_donnees()
                                st.rerun()

    elif choix_section == "🧪 Catalogue des éléments":
        @st.dialog("➕ Ajouter un élément", width="large")
        def ouvrir_ajout_element_complet():
            e_nom = st.text_input("Nom de l'élément (Clé unique/Référence)")
            e_code = st.text_input("Code")
            e_des = st.text_input("Désignation")
            e_comm = st.text_input("Commentaire court (Formulation)")

            activer_ft = st.toggle("📝 Créer la Fiche Technique (FT)", value=False)
            e_fourn, e_art, e_des_ach, e_nat, e_dang, e_dang_txt, e_manip, e_comm_glob = "", "", "", "Liquide", "Non", "", "", ""
            ft_redacteur = OPTIONS_REDACTEURS[0]

            if activer_ft:
                st.markdown("##### Spécifications de la Fiche Technique")
                e_fourn = st.text_input("Fournisseur")
                e_art = st.text_input("Code Article Achat")
                e_des_ach = st.text_input("Désignation Achat")
                e_nat = st.selectbox("Nature", ["Liquide", "Poudre", "Granulé", "Gel", "Autre"])
                
                e_dang = st.radio("Risque / Danger ?", ["Non", "Oui"], horizontal=True)
                if e_dang == "Oui":
                    e_dang_txt = st.text_area("Préciser le risque / danger")
                    
                e_manip = st.text_area("Conseils de manipulation (Optionnel)")
                e_comm_glob = st.text_area("Commentaires Généraux (FT)")
                ft_redacteur = st.selectbox("Rédacteur / Modifié par :", OPTIONS_REDACTEURS, index=0)

            if st.button("Enregistrer l'élément", type="primary"):
                if e_nom:
                    today_str = datetime.date.today().strftime("%d/%m/%Y")
                    st.session_state.processus_db["preparation_melanges"]["additifs"].append({
                        "nom": e_nom, "code": e_code, "designation": e_des,
                        "fournisseur": e_fourn, "code_article": e_art, "designation_achat": e_des_ach,
                        "nature": e_nat, "danger": e_dang, "danger_texte": e_dang_txt, "manipulation": e_manip,
                        "commentaire": e_comm, "commentaire_global": e_comm_glob, "has_ft": activer_ft,
                        "fiche_technique": {"date_creation": today_str, "date_derniere_maj": today_str, "date_avant_derniere_maj": "-", "redacteur": ft_redacteur}
                    })
                    sauvegarder_donnees()
                    st.rerun()

        @st.dialog("✏️ Modifier un élément", width="large")
        def ouvrir_modif_element_complet(index, data):
            m_nom = st.text_input("Nom de l'élément", value=data.get("nom", ""))
            m_code = st.text_input("Code", value=data.get("code", ""))
            m_des = st.text_input("Désignation", value=data.get("designation", ""))
            m_comm = st.text_input("Commentaire court (Formulation)", value=data.get("commentaire", ""))

            has_ft_init = data.get("has_ft", False)
            activer_ft = st.toggle("📝 Gérer la Fiche Technique (FT)", value=has_ft_init)

            m_fourn = data.get("fournisseur", "")
            m_art = data.get("code_article", "")
            m_des_ach = data.get("designation_achat", "")
            m_nat = data.get("nature", "Liquide")
            m_dang = data.get("danger", "Non")
            m_dang_txt = data.get("danger_texte", "")
            m_manip = data.get("manipulation", "")
            m_comm_glob = data.get("commentaire_global", "")
            
            ft_old = data.get("fiche_technique", {})
            idx_redacteur = OPTIONS_REDACTEURS.index(ft_old.get("redacteur", "Labo / R&D")) if ft_old.get("redacteur", "Labo / R&D") in OPTIONS_REDACTEURS else 0
            m_redacteur = OPTIONS_REDACTEURS[idx_redacteur]

            if activer_ft:
                st.markdown("##### Spécifications de la Fiche Technique")
                m_fourn = st.text_input("Fournisseur", value=m_fourn)
                m_art = st.text_input("Code Article Achat", value=m_art)
                m_des_ach = st.text_input("Désignation Achat", value=m_des_ach)
                m_nat = st.selectbox("Nature", ["Liquide", "Poudre", "Granulé", "Gel", "Autre"], index=["Liquide", "Poudre", "Granulé", "Gel", "Autre"].index(m_nat))
                
                m_dang = st.radio("Risque / Danger ?", ["Non", "Oui"], index=["Non", "Oui"].index(m_dang), horizontal=True)
                if m_dang == "Oui":
                    m_dang_txt = st.text_area("Préciser le risque / danger", value=m_dang_txt)
                    
                m_manip = st.text_area("Conseils de manipulation", value=m_manip)
                m_comm_glob = st.text_area("Commentaires Généraux (FT)", value=m_comm_glob)
                m_redacteur = st.selectbox("Rédacteur / Modifié par :", OPTIONS_REDACTEURS, index=idx_redacteur)

            if st.button("Mettre à jour l'élément", type="primary"):
                today_str = datetime.date.today().strftime("%d/%m/%Y")
                d_crea, d_der, d_av = gerer_historique_dates(ft_old, today_str)

                st.session_state.processus_db["preparation_melanges"]["additifs"][index] = {
                    "nom": m_nom, "code": m_code, "designation": m_des,
                    "fournisseur": m_fourn, "code_article": m_art, "designation_achat": m_des_ach,
                    "nature": m_nat, "danger": m_dang, "danger_texte": m_dang_txt if m_dang == "Oui" else "",
                    "manipulation": m_manip, "commentaire": m_comm, "commentaire_global": m_comm_glob, "has_ft": activer_ft,
                    "fiche_technique": {"date_creation": d_crea, "date_derniere_maj": d_der, "date_avant_derniere_maj": d_av, "redacteur": m_redacteur}
                }
                sauvegarder_donnees()
                st.rerun()

        if st.button("Ajouter un élément", type="primary"):
            ouvrir_ajout_element_complet()

        if liste_additifs:
            with st.expander("🔍 Outils de filtrage et de tri des éléments", expanded=True):
                e_f1, e_f2, e_f3, e_f4 = st.columns([2, 2, 2, 1])
                with e_f1: filtre_e_nom = st.text_input("Filtrer par Nom", "")
                with e_f2: filtre_e_emp = st.text_input("Filtrer par Code", "")
                with e_f3: tri_e_colonne = st.selectbox("Trier par :", ["Nom", "Code", "Fournisseur"])
                with e_f4: sens_e_tri = st.selectbox("Ordre :", ["Croissant ⬆️", "Décroissant ⬇️"], key="sens_e")

            elements_filtres = []
            for idx, a in enumerate(liste_additifs):
                if (filtre_e_nom.lower() in a.get("nom", "").lower()) and (filtre_e_emp.lower() in a.get("code", "").lower()):
                    elements_filtres.append({"index_origine": idx, "data": a})
            
            tri_cle = {"Nom": "nom", "Code": "code", "Fournisseur": "fournisseur"}[tri_e_colonne]
            elements_filtres.sort(key=lambda x: str(x["data"].get(tri_cle, "")).lower(), reverse=(sens_e_tri == "Décroissant ⬇️"))

            if elements_filtres: st.info(f"📊 **Nombre d'éléments :** {len(elements_filtres)} | **Premier :** {elements_filtres[0]['data'].get('nom', 'Aucun')} | **Dernier :** {elements_filtres[-1]['data'].get('nom', 'Aucun')}")

            thead = st.columns([1.5, 1, 1.5, 1.5, 1, 1, 1.5, 2])
            thead[0].markdown("**Nom**")
            thead[1].markdown("**Code**")
            thead[2].markdown("**Désignation**")
            thead[3].markdown("**Fournisseur**")
            thead[4].markdown("**Nature**")
            thead[5].markdown("**Danger**")
            thead[6].markdown("**Commentaire**")
            thead[7].markdown("**Actions**")
            st.markdown("<hr style='margin:4px 0px; border-width:2px; border-color:black;'>", unsafe_allow_html=True)

            for item in elements_filtres:
                idx_a = item["index_origine"]
                a_data = item["data"]
                row = st.columns([1.5, 1, 1.5, 1.5, 1, 1, 1.5, 2])
                row[0].write(str(a_data.get("nom", "-")).title())
                row[1].write(str(a_data.get("code", "-")).upper())
                row[2].write(str(a_data.get("designation", "-")).title())
                row[3].write(str(a_data.get("fournisseur", "-") if a_data.get("fournisseur") else "-").upper())
                row[4].write(str(a_data.get("nature", "-") if a_data.get("nature") else "-"))
                
                danger_icon = "⚠️ Oui" if a_data.get("danger") == "Oui" else "Non"
                row[5].write(danger_icon)
                row[6].write(str(a_data.get("commentaire", "-")))
                
                c_edit, c_del, c_ft = row[7].columns([1, 1, 2])
                if c_edit.button("✏️", key=f"ed_add_{idx_a}"):
                    ouvrir_modif_element_complet(idx_a, a_data)
                
                key_del_a = f"del_confirm_add_{idx_a}"
                if key_del_a not in st.session_state: st.session_state[key_del_a] = False
                if not st.session_state[key_del_a]:
                    if c_del.button("🗑️", key=f"del_add_{idx_a}"):
                        st.session_state[key_del_a] = True
                        st.rerun()
                else:
                    if c_del.button("Oui", key=f"d_add_y_{idx_a}", type="primary"):
                        st.session_state.processus_db["preparation_melanges"]["additifs"].pop(idx_a)
                        sauvegarder_donnees()
                        st.rerun()
                
                if a_data.get("has_ft"):
                    if c_ft.button("📄 FT", key=f"ft_add_{idx_a}"):
                        ouvrir_visualisation_ft_additif(a_data)

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

        if rals_filtres: st.info(f"📊 **Nombre de codes RAL :** {len(rals_filtres)} | **Premier :** RAL {rals_filtres[0]['code']} | **Dernier :** RAL {rals_filtres[-1]['code']}")

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
        @st.dialog("➕ Créer un mélange", width="large")
        def ouvrir_ajout_melange_complet():
            m_ref = st.text_input("Référence du mélange")
            m_nom = st.text_input("Nom du mélange")
            m_cat = st.selectbox("Catégorie", ["Mélange Couleurs", "Autre Mélange"])
            m_emp = st.text_input("Emplacement de stockage")
            m_comm = st.text_input("Commentaire court (Formulation)")
            
            activer_ft = st.toggle("📝 Créer la Fiche Technique (FT)", value=False)
            ft_aspect, ft_visco, ft_densite, ft_ph, ft_cov, ft_sechage, ft_cond, m_comm_glob = "", "", "", "", "", "", "", ""
            ft_redacteur = OPTIONS_REDACTEURS[0]
            
            if activer_ft:
                st.markdown("##### Spécifications Physico-Chimiques (FT)")
                c_f1, c_f2 = st.columns(2)
                ft_aspect = c_f1.text_input("Aspect / Finition")
                ft_visco = c_f1.text_input("Viscosité attendue")
                ft_densite = c_f2.text_input("Densité")
                ft_ph = c_f2.text_input("pH")
                ft_cov = c_f1.text_input("Taux de COV")
                ft_sechage = c_f2.text_input("Temps de séchage")
                ft_cond = st.text_area("Conditions d'application")
                m_comm_glob = st.text_area("Commentaires Généraux (FT)")
                ft_redacteur = st.selectbox("Rédacteur / Modifié par :", OPTIONS_REDACTEURS, index=0)

            if "tmp_form_state" not in st.session_state: st.session_state.tmp_form_state = {}

            st.markdown("---")
            recherche_filtre_c = st.text_input("🔍 Filtrer les composants (Nom, Réf, Code RAL, Élément existant) :").strip()

            st.markdown("**🎨 Couleurs du Nuancier :**")
            couleurs_trouvees = [c for c in liste_couleurs if not recherche_filtre_c or (recherche_filtre_c.lower() in c["nom_actuel"].lower() or recherche_filtre_c.lower() in c["ref"].lower() or recherche_filtre_c.lower() in c.get("ral", "").lower())]
            for idx, c in enumerate(couleurs_trouvees if recherche_filtre_c else couleurs_trouvees[:5]):
                label = f"{c['nom_actuel']} ({c['ref']})"
                key_c = f"color_{c['ref']}"
                col_chk, col_vis = st.columns([7, 1])
                with col_chk:
                    if st.checkbox(label, value=(key_c in st.session_state.tmp_form_state), key=f"chk_add_c_{idx}_{c['ref']}"):
                        st.session_state.tmp_form_state[key_c] = {"type": "couleur", "ref": c['ref'], "nom": c['nom_actuel'], "dosage": st.text_input(f"Dosage pour {c['nom_actuel']}", value=st.session_state.tmp_form_state.get(key_c, {}).get("dosage", "100g"), key=f"dos_add_c_{idx}_{c['ref']}")}
                    else:
                        st.session_state.tmp_form_state.pop(key_c, None)
                with col_vis: st.markdown(f'<div style="width:22px; height:22px; background-color:{c["visuel"]}; border-radius:50%; border:1px solid #000; margin-top:5px;"></div>', unsafe_allow_html=True)

            st.markdown("**🔢 Codes RAL du catalogue :**")
            rals_trouves = [(code_ral, hex_ral) for code_ral, hex_ral in RAL_DICT.items() if not recherche_filtre_c or recherche_filtre_c.lower() in code_ral]
            for idx, (code_ral, hex_ral) in enumerate(rals_trouves if recherche_filtre_c else rals_trouves[:5]):
                label_ral = f"RAL {code_ral}"
                key_ral = f"ral_std_{code_ral}"
                col_chk_r, col_vis_r = st.columns([7, 1])
                with col_chk_r:
                    if st.checkbox(label_ral, value=(key_ral in st.session_state.tmp_form_state), key=f"chk_add_ral_{idx}_{code_ral}"):
                        st.session_state.tmp_form_state[key_ral] = {"type": "ral_officiel", "ref": f"RAL {code_ral}", "nom": f"RAL {code_ral}", "visuel": hex_ral, "dosage": st.text_input(f"Dosage pour RAL {code_ral}", value=st.session_state.tmp_form_state.get(key_ral, {}).get("dosage", "100g"), key=f"dos_add_ral_{idx}_{code_ral}")}
                    else:
                        st.session_state.tmp_form_state.pop(key_ral, None)
                with col_vis_r: st.markdown(f'<div style="width:22px; height:22px; background-color:{hex_ral}; border-radius:50%; border:1px solid #000; margin-top:5px;"></div>', unsafe_allow_html=True)

            st.markdown("**⚗️ Mélanges existants (Bases) :**")
            melanges_trouves = [mel for mel in liste_melanges if not recherche_filtre_c or (recherche_filtre_c.lower() in mel["nom"].lower() or recherche_filtre_c.lower() in mel["ref"].lower())]
            for idx, mel in enumerate(melanges_trouves if recherche_filtre_c else melanges_trouves[:5]):
                label_m = f"Mélange : {mel['nom']} ({mel['ref']})"
                key_m_exist = f"melange_base_{mel['ref']}"
                col_chk_m, _ = st.columns([7, 1])
                with col_chk_m:
                    if st.checkbox(label_m, value=(key_m_exist in st.session_state.tmp_form_state), key=f"chk_add_mel_{idx}_{mel['ref']}"):
                        st.session_state.tmp_form_state[key_m_exist] = {"type": "melange_base", "ref": mel['ref'], "nom": mel['nom'], "dosage": st.text_input(f"Dosage pour Base {mel['nom']}", value=st.session_state.tmp_form_state.get(key_m_exist, {}).get("dosage", "500g"), key=f"dos_add_mel_{idx}_{mel['ref']}")}
                    else:
                        st.session_state.tmp_form_state.pop(key_m_exist, None)

            st.markdown("**🧪 Éléments (Additifs) :**")
            elements_trouves = [a for a in liste_additifs if not recherche_filtre_c or recherche_filtre_c.lower() in a["nom"].lower()]
            for idx, a in enumerate(elements_trouves if recherche_filtre_c else elements_trouves[:5]):
                label = f"Élément : {a['nom']}"
                key_a = f"additif_{a['nom']}"
                col_chk_a, _ = st.columns([7, 1])
                with col_chk_a:
                    if st.checkbox(label, value=(key_a in st.session_state.tmp_form_state), key=f"chk_add_add_{idx}_{a['nom']}"):
                        st.session_state.tmp_form_state[key_a] = {"type": "additif", "ref": a['nom'], "nom": a['nom'], "dosage": st.text_input(f"Dosage pour {a['nom']}", value=st.session_state.tmp_form_state.get(key_a, {}).get("dosage", "10g"), key=f"dos_add_add_{idx}_{a['nom']}")}
                    else:
                        st.session_state.tmp_form_state.pop(key_a, None)

            if st.button("Enregistrer la formulation", type="primary"):
                if m_ref and m_nom:
                    comp = []
                    for k, v in st.session_state.tmp_form_state.items():
                        if est_dosage_valide(v.get("dosage", "")):
                            if v["type"] == "couleur":
                                couleur_trouvee = next((x for x in liste_couleurs if x["ref"] == v["ref"]), None)
                                comp.append({"type": "couleur", "ref": v["ref"], "nom": couleur_trouvee["nom_actuel"] if couleur_trouvee else v["nom"], "visuel": couleur_trouvee["visuel"] if couleur_trouvee else "#CCCCCC", "dosage": v["dosage"]})
                            elif v["type"] == "ral_officiel":
                                comp.append({"type": "couleur", "ref": v["ref"], "nom": v["nom"], "visuel": v["visuel"], "dosage": v["dosage"]})
                            elif v["type"] == "melange_base":
                                comp.append({"type": "melange_base", "ref": v["ref"], "nom": v['nom'], "visuel": "#CBD5E1", "dosage": v["dosage"]})
                            else:
                                comp.append({"type": "additif", "ref": v["ref"], "nom": v["nom"], "visuel": "#E2E8F0", "dosage": v["dosage"]})
                    
                    today_str = datetime.date.today().strftime("%d/%m/%Y")
                    st.session_state.processus_db["preparation_melanges"]["melanges"].append({
                        "ref": m_ref, "nom": m_nom, "categorie_choisie": m_cat, "emplacement": m_emp,
                        "commentaire": m_comm, "commentaire_global": m_comm_glob,
                        "couleurs_associees": comp, "statut": "Pas vérifié", "has_ft": activer_ft,
                        "fiche_technique": {
                            "date_creation": today_str, "date_derniere_maj": today_str, "date_avant_derniere_maj": "-",
                            "aspect": ft_aspect, "viscosite": ft_visco, "densite": ft_densite, "ph": ft_ph, "cov": ft_cov, "sechage": ft_sechage, "conditions": ft_cond, "redacteur": ft_redacteur
                        }
                    })
                    st.session_state.tmp_form_state = {}
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
                    st.session_state.tmp_mod_state[key] = {"type": type_c, "ref": c["ref"], "nom": c.get("nom", ""), "dosage": c["dosage"], "visuel": c.get("visuel")}
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

            ft_aspect = fiche_tech_existante.get("aspect", "")
            ft_visco = fiche_tech_existante.get("viscosite", "")
            ft_densite = fiche_tech_existante.get("densite", "")
            ft_ph = fiche_tech_existante.get("ph", "")
            ft_cov = fiche_tech_existante.get("cov", "")
            ft_sechage = fiche_tech_existante.get("sechage", "")
            ft_cond = fiche_tech_existante.get("conditions", "")
            m_comm_glob = melange_data.get("commentaire_global", "")
            idx_redacteur = OPTIONS_REDACTEURS.index(fiche_tech_existante.get("redacteur", "Labo / R&D")) if fiche_tech_existante.get("redacteur", "Labo / R&D") in OPTIONS_REDACTEURS else 0
            m_redacteur = OPTIONS_REDACTEURS[idx_redacteur]
            
            if activer_ft:
                st.markdown("##### Spécifications Physico-Chimiques (FT)")
                col_ft1, col_ft2 = st.columns(2)
                with col_ft1:
                    ft_aspect = st.text_input("Aspect / Finition", value=ft_aspect)
                    ft_visco = st.text_input("Viscosité attendue", value=ft_visco)
                    ft_densite = st.text_input("Densité", value=ft_densite)
                with col_ft2:
                    ft_ph = st.text_input("pH", value=ft_ph)
                    ft_cov = st.text_input("Taux de COV", value=ft_cov)
                    ft_sechage = st.text_input("Temps de séchage", value=ft_sechage)
                ft_cond = st.text_area("Conditions d'application idéales", value=ft_cond)
                m_comm_glob = st.text_area("Commentaires Généraux (FT)", value=m_comm_glob)
                m_redacteur = st.selectbox("Rédacteur / Modifié par :", OPTIONS_REDACTEURS, index=idx_redacteur)

            st.markdown("---")
            st.markdown("### 🛠️ Composants de ce mélange :")
            cles_existantes = list(st.session_state.tmp_mod_state.keys())

            if cles_existantes:
                for idx, k in enumerate(cles_existantes):
                    v = st.session_state.tmp_mod_state.get(k)
                    if not v: continue
                    col_chk, col_vis = st.columns([7, 1])
                    with col_chk:
                        label_aff = "ÉLÉMENT" if v['type'] == "additif" else v['type'].upper()
                        label_affichage = f"[{label_aff}] {v['nom']} ({v['ref']})"
                        if st.checkbox(label_affichage, value=True, key=f"mod_item_chk_{idx}_{v['ref']}"):
                            st.session_state.tmp_mod_state[k]["dosage"] = st.text_input(f"Dosage pour {v['nom']}", value=v["dosage"], key=f"dos_mod_item_{idx}_{v['ref']}")
                        else:
                            st.session_state.tmp_mod_state.pop(k, None)
                            st.rerun()
                    with col_vis:
                        if v.get("visuel"): st.markdown(f'<div style="width:22px; height:22px; background-color:{v["visuel"]}; border-radius:50%; border:1px solid #000; margin-top:5px;"></div>', unsafe_allow_html=True)
            else:
                st.warning("Aucun composant sélectionné dans ce mélange.")

            st.markdown("---")
            st.markdown("#### ➕ Ajouter des composants")
            recherche_filtre_m = st.text_input("🔍 Filtrer les composants (Nom, Réf, Code RAL, Élément) :", key=f"rech_mod_{index}").strip()

            st.markdown("**🎨 Couleurs du Nuancier :**")
            couleurs_t = [c for c in liste_couleurs if not recherche_filtre_m or (recherche_filtre_m.lower() in c["nom_actuel"].lower() or recherche_filtre_m.lower() in c["ref"].lower())]
            for idx_c, c in enumerate(couleurs_t if recherche_filtre_m else couleurs_t[:5]):
                key_c = f"color_{c['ref']}"
                if key_c not in st.session_state.tmp_mod_state:
                    col_chk, _ = st.columns([7, 1])
                    with col_chk:
                        if st.checkbox(f"{c['nom_actuel']} ({c['ref']})", value=False, key=f"chk_madd_c_{idx_c}_{c['ref']}"):
                            st.session_state.tmp_mod_state[key_c] = {"type": "couleur", "ref": c['ref'], "nom": c['nom_actuel'], "visuel": c["visuel"], "dosage": "100g"}
                            st.rerun()

            st.markdown("**🧪 Éléments (Additifs) :**")
            elements_t = [a for a in liste_additifs if not recherche_filtre_m or recherche_filtre_m.lower() in a["nom"].lower()]
            for idx_a, a in enumerate(elements_t if recherche_filtre_m else elements_t[:5]):
                key_a = f"additif_{a['nom']}"
                if key_a not in st.session_state.tmp_mod_state:
                    col_chk_a, _ = st.columns([7, 1])
                    with col_chk_a:
                        if st.checkbox(f"Élément : {a['nom']}", value=False, key=f"chk_madd_add_{idx_a}_{a['nom']}"):
                            st.session_state.tmp_mod_state[key_a] = {"type": "additif", "ref": a['nom'], "nom": a['nom'], "visuel": "#E2E8F0", "dosage": "10g"}
                            st.rerun()

            if st.button("Mettre à jour le mélange", type="primary"):
                comp_finaux = []
                for k, v in st.session_state.tmp_mod_state.items():
                    if est_dosage_valide(v.get("dosage", "")):
                        if v["type"] == "couleur":
                            couleur_trouvee = next((x for x in liste_couleurs if x["ref"] == v["ref"]), None)
                            comp_finaux.append({"type": "couleur", "ref": v["ref"], "nom": couleur_trouvee["nom_actuel"] if couleur_trouvee else v["nom"], "visuel": couleur_trouvee["visuel"] if couleur_trouvee else v.get("visuel", "#CCCCCC"), "dosage": v["dosage"]})
                        elif v["type"] == "ral_officiel":
                            comp_finaux.append({"type": "couleur", "ref": v["ref"], "nom": v["nom"], "visuel": v["visuel"], "dosage": v["dosage"]})
                        elif v["type"] == "melange_base":
                            comp_finaux.append({"type": "melange_base", "ref": v["ref"], "nom": v['nom'], "visuel": "#CBD5E1", "dosage": v["dosage"]})
                        else:
                            comp_finaux.append({"type": "additif", "ref": v["ref"], "nom": v["nom"], "visuel": "#E2E8F0", "dosage": v["dosage"]})

                today_str = datetime.date.today().strftime("%d/%m/%Y")
                d_crea, d_der, d_av = gerer_historique_dates(fiche_tech_existante, today_str)

                fiche_tech_finale = {"date_creation": d_crea, "date_derniere_maj": d_der, "date_avant_derniere_maj": d_av}
                if activer_ft:
                    fiche_tech_finale.update({"aspect": ft_aspect, "viscosite": ft_visco, "densite": ft_densite, "ph": ft_ph, "cov": ft_cov, "sechage": ft_sechage, "conditions": ft_cond, "redacteur": m_redacteur})

                img_final = encoder_fichier_local(m_img_file) if m_img_file else melange_data.get("image_rendu")
                st.session_state.processus_db["preparation_melanges"]["melanges"][index] = {
                    "ref": m_ref, "nom": m_nom, "categorie_choisie": m_cat, "emplacement": m_emp,
                    "commentaire": m_comm, "commentaire_global": m_comm_glob, "couleurs_associees": comp_finaux,
                    "statut": m_statut, "has_ft": activer_ft, "fiche_technique": fiche_tech_finale, "image_rendu": img_final
                }
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

            melanges_couleurs = [item for item in melanges_filtres if item["data"].get("categorie_choisie", "Mélange Couleurs") == "Mélange Couleurs"]
            autres_melanges = [item for item in melanges_filtres if item["data"].get("categorie_choisie", "Mélange Couleurs") != "Mélange Couleurs"]

            onglet_c1, onglet_c2 = st.tabs(["🎨 Mélanges Couleurs", "⚙️ Autres Mélanges"])

            def afficher_tableau_melanges(liste_m_categorie, identifiant_unique):
                if liste_m_categorie:
                    total_mel = len(liste_m_categorie)
                    premier_mel = liste_m_categorie[0]["data"].get("nom", "Aucun")
                    dernier_mel = liste_m_categorie[-1]["data"].get("nom", "Aucun")
                    st.info(f"📊 **Nombre d'éléments :** {total_mel} | **Premier :** {premier_mel} | **Dernier :** {dernier_mel}")

                    th_m_ref, th_m_nom, th_m_vis, th_m_comp, th_m_emp, th_m_com, th_m_act = st.columns([0.8, 1.2, 0.8, 3.2, 1.2, 2.3, 2.5])
                    with th_m_ref: st.markdown("**Référence**")
                    with th_m_nom: st.markdown("**Nom mélange**")
                    with th_m_vis: st.markdown("**Aperçu**")
                    with th_m_comp: st.markdown("**Couleurs & Éléments**")
                    with th_m_emp: st.markdown("**Emplacement**")
                    with th_m_com: st.markdown("**Commentaires**")
                    with th_m_act: st.markdown("**Actions**")
                    st.markdown("<hr style='margin:4px 0px; border-width:2px; border-color:black;'>", unsafe_allow_html=True)

                    for item_m in liste_m_categorie:
                        idx_m = item_m["index_origine"]
                        melange = item_m["data"]
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
                                    st.markdown(f'<div style="display:flex; align-items:center;"><span style="{txt_style}">Élément : {str(t["nom"]).title()} ➔ <b>{str(t["dosage"]).title()}</b></span></div>', unsafe_allow_html=True)

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
                        st.markdown('</div>', unsafe_allow_html=True)
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

        if "click_node_id" in query_params and "click_fiche_idx" in query_params:
            try:
                c_nid = int(query_params["click_node_id"])
                c_fidx = int(query_params["click_fiche_idx"])
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
                <div id="mynetwork" style="width: 100%; height: 580px; background-color: #FAFAFA; border: 2px dashed #CBD5E1; border-radius: 8px;"></div>
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