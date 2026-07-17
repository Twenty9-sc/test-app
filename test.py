# -*- coding: utf-8 -*-
"""
B&V — Portail de gestion industrielle
Version corrigée : les cinq sections de Préparation des mélanges sont au même
niveau d'indentation et s'affichent indépendamment.
"""

# =============================================================================
# IMPORTS ET CONFIGURATION — st.set_page_config doit rester le premier appel st
# =============================================================================

import base64
import copy
import csv
import datetime
import hashlib
import html as html_lib
import io
import json
import math
import os
import random
import re
import time
import uuid

import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
)


st.set_page_config(
    page_title="B&V - Portail de Gestion",
    layout="wide",
    initial_sidebar_state="expanded",
)


try:
    from theme_bos2_safe import appliquer_theme_bos2_professionnel

    appliquer_theme_bos2_professionnel()
except Exception:
    # Le fonctionnement de BOS2 ne dépend pas du fichier de thème.
    pass


# =============================================================================
# IMPORTS REPORTLAB
# =============================================================================
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape, letter
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfgen import canvas
    from reportlab.platypus import (
        Image as RLImage,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
    # C'est cette ligne qui résout le 'Undefined name Line, String, Rect, Drawing' :
    from reportlab.graphics.shapes import Drawing, Rect, String, Line

    REPORTLAB_DISPO = True
except ImportError:
    REPORTLAB_DISPO = False




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

# =============================================================================
# ÉTAT DE SESSION
# =============================================================================

if "etat_sidebar" not in st.session_state:
    st.session_state.etat_sidebar = "expanded"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "groupe_actif" not in st.session_state:
    st.session_state.groupe_actif = None
if "produit_selectionne" not in st.session_state:
    st.session_state.produit_selectionne = None
if "sub_section_melange" not in st.session_state:
    st.session_state.sub_section_melange = None
if "historique_recherches" not in st.session_state:
    st.session_state.historique_recherches = []
if "recherche_globale_val" not in st.session_state:
    st.session_state.recherche_globale_val = ""
if "active_dialog" not in st.session_state:
    st.session_state.active_dialog = None
if "ft_champs_defaut" not in st.session_state:
    st.session_state.ft_champs_defaut = [
        "Aspect / Finition",
        "Viscosité attendue",
        "Densité",
        "Temps de séchage",
        "Conditions d'application",
    ]


# =============================================================================
# CONSTANTES
# =============================================================================

FICHIER_SAUVEGARDE = "donnees_bos2.json"
MAX_LIGNES_AFFICHAGE = 200
OPTIONS_REDACTEURS = [
    "Labo / R&D",
    "Atelier : couleurs",
    "Atelier : perles/croix",
    "Atelier : pose peinture",
    "Atelier : moulage",
    "Atelier : résine",
    "Atelier : finition",
    "Atelier : assemblage",
]


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
    "9011": "#1C1C1C", "9016": "#F6F6F6", "9017": "#1E1E1E", "9018": "#D7DBDE",
}


# =============================================================================
# CONNEXION
# =============================================================================


def afficher_page_connexion():
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    logo_path = os.path.join(os.getcwd(), "Martineau logo.png")
    if os.path.exists(logo_path):
        st.image(logo_path, width=260)
    st.markdown("<h2>Connexion au Portail B&V</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color:#64748b;margin-bottom:20px;'>Veuillez vous identifier.</p>",
        unsafe_allow_html=True,
    )
    with st.form("formulaire_connexion"):
        identifiant = st.text_input("Identifiant", autocomplete="off", key="login_identifiant")
        mot_de_passe = st.text_input("Mot de passe", type="password", autocomplete="new-password", key="login_password")
        
        if st.form_submit_button("Se connecter", use_container_width=True):
            utilisateurs_valides = {
                "1": "1",
                "admin": "bos2024",
                "labo": "labo123",
                "atelier": "atelier123",
                "test": "1234",
            }
            if (
                identifiant in utilisateurs_valides
                and utilisateurs_valides[identifiant] == mot_de_passe
            ):
                st.session_state.logged_in = True
                st.session_state.current_user = identifiant
                st.rerun()
            else:
                st.error("Identifiant ou mot de passe incorrect.")
    st.markdown('</div>', unsafe_allow_html=True)

if not st.session_state.logged_in:
    afficher_page_connexion()
    st.stop()


# =============================================================================
# REPORTLAB OPTIONNEL
# =============================================================================

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.pdfgen import canvas
    from reportlab.platypus import (
        Image as RLImage,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    REPORTLAB_DISPO = True
except ImportError:
    REPORTLAB_DISPO = False


if REPORTLAB_DISPO:
    class NumeroteurDePages(canvas.Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.pages = []

        def showPage(self):
            self.pages.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            nombre_pages = len(self.pages)
            for page in self.pages:
                self.__dict__.update(page)
                if nombre_pages > 1:
                    self.setFont("Helvetica", 8)
                    self.setFillColor(colors.HexColor("#64748B"))
                    self.drawRightString(
                        A4[0] - 35,
                        20,
                        f"Page {self._pageNumber} sur {nombre_pages}",
                    )
                super().showPage()
            super().save()


# =============================================================================
# CHARGEMENT ET SAUVEGARDE
# =============================================================================


def structure_donnees_vide():
    return {
        "creation_processus": {},
        "preparation_melanges": {
            "couleurs": [],
            "melanges": [],
            "fiches_methode": [],
            "additifs": [],
            "base_rals": [],
            "compartiments": ["résine", "peinture"],
            "sous_groupes": ["Général"],
            "ateliers": ["Atelier Résine", "Atelier Peinture"],
            "corbeille": [],  # <-- AJOUTER CETTE LIGNE
        },
    }


def charger_donnees():
    donnees = structure_donnees_vide()
    if os.path.exists(FICHIER_SAUVEGARDE):
        try:
            with open(FICHIER_SAUVEGARDE, "r", encoding="utf-8") as fichier:
                contenu = json.load(fichier)
            if isinstance(contenu, dict):
                donnees = contenu
        except (OSError, json.JSONDecodeError):
            pass
    donnees.setdefault("creation_processus", {})
    
    # 1. On définit la variable 'preparation'
    preparation = donnees.setdefault("preparation_melanges", {})
    
    # 2. On configure tous les sous-ensembles
    preparation.setdefault("couleurs", [])
    preparation.setdefault("melanges", [])
    preparation.setdefault("fiches_methode", [])
    preparation.setdefault("additifs", [])
    preparation.setdefault("base_rals", [])
    preparation.setdefault("compartiments", ["résine", "peinture"])
    preparation.setdefault("sous_groupes", ["Général"])
    preparation.setdefault("ateliers", ["Atelier Résine", "Atelier Peinture"])
    preparation.setdefault("corbeille", [])  # <-- Ne pose aucun problème ici
    
    return donnees


def sauvegarder_donnees():
    fichier_temporaire = f"{FICHIER_SAUVEGARDE}.tmp"
    with open(fichier_temporaire, "w", encoding="utf-8") as fichier:
        json.dump(
            st.session_state.processus_db,
            fichier,
            ensure_ascii=False,
            indent=4,
        )
    os.replace(fichier_temporaire, FICHIER_SAUVEGARDE)


if "processus_db" not in st.session_state:
    st.session_state.processus_db = charger_donnees()


# =============================================================================
# UTILITAIRES
# =============================================================================
def deplacer_vers_corbeille(type_item, item_data, identifiant=""):
    """
    Déplace un élément supprimé vers la corbeille avec horodatage automatique.
    """
    prep = st.session_state.processus_db["preparation_melanges"]
    corbeille = prep.setdefault("corbeille", [])
    
    nom_affiche = identifiant or item_data.get("nom") or item_data.get("ref") or item_data.get("code") or "Sans nom"
    
    corbeille.append({
        "id_corbeille": str(uuid.uuid4())[:8],
        "type": type_item,  # Exemple : "Couleur", "Élément", "Mélange", "Code RAL", "Fiche Méthode"
        "identifiant": nom_affiche,
        "date_suppression": pro_date_maintenant(),  # Horodatage auto (JJ/MM/AAAA - HH:MM)
        "data": copy.deepcopy(item_data)
    })
    sauvegarder_donnees()

def afficher_animation_validation(message):
    emplacement = st.empty()
    emplacement.markdown(
        f"""
        <div style="position:fixed;top:35%;left:50%;transform:translate(-50%,-50%);z-index:100000;background:#FFFEFB;padding:26px 48px;border-radius:14px;box-shadow:0 20px 60px rgba(16,26,39,.25);text-align:center;border:2px solid #397D67;">
            <div style="font-size:52px;margin-bottom:10px;line-height:1;">✅</div>
            <div style="font-size:16px;font-weight:800;color:#142235;font-family:Arial,sans-serif;">{message}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    time.sleep(1.0)
    emplacement.empty()

def afficher_page_connexion():
    st.markdown(
        """
        <style>
        .login-box { max-width: 440px; margin: 30px auto; padding: 25px; background: #FFFEFB; border-radius: 14px; box-shadow: 0 10px 30px rgba(16,26,39,.1); border: 1px solid #D9BF91; }
        input[type="text"], input[type="password"] {
            autocomplete: off !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    logo_path = os.path.join(os.getcwd(), "Martineau logo.png")
    if os.path.exists(logo_path):
        st.image(logo_path, width=260)
    st.markdown("<h2>Connexion au Portail B&V</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color:#64748b;margin-bottom:20px;'>Veuillez vous identifier.</p>",
        unsafe_allow_html=True,
    )
    with st.form("formulaire_connexion"):
        identifiant = st.text_input("Identifiant", autocomplete="off", key="login_identifiant")
        mot_de_passe = st.text_input("Mot de passe", type="password", autocomplete="new-password", key="login_password")
        
        if st.form_submit_button("Se connecter", use_container_width=True):
            utilisateurs_valides = {
                "1": "1",
                "admin": "bos2024",
                "labo": "labo123",
                "atelier": "atelier123",
                "test": "1234",
            }
            if (
                identifiant in utilisateurs_valides
                and utilisateurs_valides[identifiant] == mot_de_passe
            ):
                st.session_state.logged_in = True
                st.session_state.current_user = identifiant
                st.rerun()
            else:
                st.error("Identifiant ou mot de passe incorrect.")
    st.markdown('</div>', unsafe_allow_html=True)


def get_svg_icon(icon_name):
    icons = {
        "search": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:8px;"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>',
        "chart": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:8px;"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>',
    }
    return icons.get(icon_name, "")


@st.cache_data
def encoder_image_systeme(nom_fichier):
    if not os.path.exists(nom_fichier):
        return ""
    try:
        with open(nom_fichier, "rb") as fichier:
            return base64.b64encode(fichier.read()).decode("utf-8")
    except OSError:
        return ""


def encoder_fichier_local(uploaded_file):
    if uploaded_file is None:
        return None
    try:
        bytes_data = uploaded_file.getvalue()
        return {
            "name": uploaded_file.name,
            "mime": uploaded_file.type,
            "data": base64.b64encode(bytes_data).decode("utf-8"),
        }
    except Exception as erreur:
        st.error(f"Erreur lors de l'encodage de l'image : {erreur}")
        return None


def afficher_image_base64(base64_string, width=None):
    if not base64_string:
        return
    try:
        image = Image.open(io.BytesIO(base64.b64decode(base64_string)))
        if width is None:
            st.image(image, use_container_width=True)
        else:
            st.image(image, width=width)
    except Exception as erreur:
        st.error(f"Erreur d'image : {erreur}")


def interpreter_texte_avec_images(texte, images_en_ligne=None):
    if texte:
        st.markdown(texte, unsafe_allow_html=True)


def est_dosage_valide(txt_dosage):
    if not txt_dosage:
        return False
    propre = str(txt_dosage).strip().lower()
    return propre not in ["", "0", "0g", "0 g", "0ml", "0 ml", "none"]


def pro_date_maintenant():
    return datetime.datetime.now().strftime("%d/%m/%Y - %H:%M")

def gerer_historique_dates_et_causes(ancien_dict, date_edition_str, cause_saisie=""):
    date_creation = ancien_dict.get("date_creation", date_edition_str)
    derniere = ancien_dict.get("date_derniere_maj", date_edition_str)
    avant_derniere = ancien_dict.get("date_avant_derniere_maj", "-")
    
    if derniere != date_edition_str:
        avant_derniere = derniere
        derniere = date_edition_str
        
    causes_existantes = list(ancien_dict.get("causes_modification", []))
    num_version = ancien_dict.get("num_version", 1)
    
    cause_clean = str(cause_saisie or "").strip()
    if cause_clean:
        num_version += 1
        causes_existantes.append({
            "version": f"v{num_version}",
            "date": date_edition_str,
            "cause": cause_clean
        })
        # Conserve uniquement les 4 modifications les plus récentes
        if len(causes_existantes) > 4:
            causes_existantes = causes_existantes[-4:]
            
    ancien_dict["num_version"] = num_version
    return date_creation, derniere, avant_derniere, causes_existantes

def nettoyer_valeur_pdf(valeur):
    if valeur is None:
        return "-"
    texte = str(valeur).strip()
    if not texte:
        return "-"
    # 1. Échappe les caractères spéciaux (<, >, &) pour éviter les erreurs ReportLab
    # 2. Remplace chaque saut de ligne (\n) par la balise <br/> reconnue par ReportLab
    texte_securise = html_lib.escape(texte)
    return texte_securise.replace("\n", "<br/>")


if "ft_champs_defaut" not in st.session_state:
    st.session_state.ft_champs_defaut = [
        "Aspect / Finition",
        "Viscosité attendue",
        "Densité",
        "Temps de séchage",
        "Conditions d'application",
    ]

def extraire_specs_du_state(dialog_id):
    """Lit les specs physico-chimiques directement depuis le session_state."""
    specs = {}
    for champ in st.session_state.ft_champs_defaut:
        val = st.session_state.get(f"input_{dialog_id}_{champ}", "")
        specs[champ] = val
    return specs

def render_dynamic_ft_inputs(fiche_existante, dialog_id):
    has_champs = bool(st.session_state.ft_champs_defaut)
    
    if has_champs:
        st.markdown("##### Spécifications Physico-Chimiques (Champs personnalisables)")
        st.caption("Vous pouvez ajouter de nouveaux champs ou supprimer des champs existants.")
    
    # --- Gestion du vidage de l'input (AVANT instanciation du widget) ---
    input_key = f"new_spec_input_{dialog_id}"
    reset_key = f"reset_spec_input_{dialog_id}"
    
    if st.session_state.get(reset_key, False):
        st.session_state[input_key] = ""
        st.session_state[reset_key] = False
    
    col_new_f, col_btn_add = st.columns([3, 1])
    with col_new_f:
        nouveau_champ = st.text_input("Ajouter un champ personnalisé", key=input_key)
    with col_btn_add:
        st.write("")
        st.write("")
        if st.button("➕ Ajouter", key=f"btn_add_spec_{dialog_id}"):
            f_clean = nouveau_champ.strip()
            if f_clean and f_clean not in st.session_state.ft_champs_defaut:
                st.session_state.ft_champs_defaut.append(f_clean)
                st.session_state[reset_key] = True   # ← demande le vidage au prochain run
                st.rerun()
    
    if has_champs:
        with st.expander("Gérer / Supprimer les champs existants", expanded=False):
            champs_a_retirer = []
            for index_c, champ_courant in enumerate(st.session_state.ft_champs_defaut):
                c1, c2 = st.columns([4, 1])
                c1.write(f"• **{champ_courant}**")
                if c2.button("🗑️", key=f"del_spec_{dialog_id}_{index_c}"):
                    champs_a_retirer.append(champ_courant)
            if champs_a_retirer:
                for c_rem in champs_a_retirer:
                    st.session_state.ft_champs_defaut.remove(c_rem)
                st.rerun()

    valeurs = {}
    if has_champs:
        specifications_existantes = fiche_existante.get("specs_dynamiques", {})
        for champ in st.session_state.ft_champs_defaut:
            valeur_defaut = specifications_existantes.get(champ, fiche_existante.get(champ.lower(), ""))
            valeurs[champ] = st.text_input(
                champ,
                value=valeur_defaut,
                key=f"input_{dialog_id}_{champ}",
            )
    return valeurs

def deplacer_vers_corbeille(type_item, item_data, identifiant=""):
    """
    Déplace un élément supprimé vers la corbeille avec horodatage automatique.
    """
    # On définit explicitement 'prep' ici
    prep = st.session_state.processus_db.setdefault("preparation_melanges", {})
    corbeille = prep.setdefault("corbeille", [])
    
    nom_affiche = identifiant or item_data.get("nom") or item_data.get("ref") or item_data.get("code") or "Sans nom"
    
    corbeille.append({
        "id_corbeille": str(uuid.uuid4())[:8],
        "type": type_item,
        "identifiant": nom_affiche,
        "date_suppression": pro_date_maintenant(),
        "data": copy.deepcopy(item_data)
    })
    sauvegarder_donnees()

def gerer_affichage_dialogues():
    dialog = st.session_state.get("dialog_actif")
    if not isinstance(dialog, dict):
        return
    
    d_type = dialog.get("type")
    idx = dialog.get("index")
    data = dialog.get("data")
    
    if d_type == "ajout_couleur":
        ouvrir_ajout_couleur()
    elif d_type == "modif_couleur" and idx is not None:
        ouvrir_modif_couleur(idx)
    elif d_type == "ajout_element":
        ouvrir_ajout_element_complet()
    elif d_type == "modif_element" and idx is not None:
        ouvrir_modif_element_complet(idx)
    elif d_type == "ajout_melange":
        ouvrir_ajout_melange_complet()
    elif d_type == "modif_melange" and idx is not None:
        ouvrir_modification_melange_complet(idx)
    elif d_type == "edit_trash_Couleur" and idx is not None:
        ouvrir_modif_couleur_corbeille(idx)
    elif d_type == "edit_trash_Élément" and idx is not None:
        ouvrir_modif_element_corbeille(idx)
    elif d_type == "edit_trash_Mélange" and idx is not None:
        ouvrir_modif_melange_corbeille(idx)
    elif d_type == "voir_details_couleur" and data:
        ouvrir_details_couleur(data)
    elif d_type == "voir_details_element" and data:
        ouvrir_details_element(data)
    elif d_type == "voir_details_melange" and data:
        ouvrir_details_melange(data)
    elif d_type == "ft_couleur" and data:
        ouvrir_visualisation_ft_couleur(data)
    elif d_type == "ft_element" and data:
        ouvrir_visualisation_ft_additif(data)
    elif d_type == "ft_melange" and data:
        ouvrir_visualisation_ft(data)

def generer_fichier_export(donnees_list, nom_fichier="export"):
    if not donnees_list:
        return None, None, None

    if "Couleurs" in nom_fichier:
        colonnes_map = {
            "ref": "Référence",
            "nom_actuel": "Nom",
            "nom_futur": "Futur nom",
            "ral": "RAL",
            "societe": "Société",
            "type": "Type",
        }
    elif "Elements" in nom_fichier:
        colonnes_map = {
            "nom": "Nom",
            "code": "Code",
            "designation": "Désignation",
            "fournisseur": "Fournisseur",
            "sous_groupe": "Sous-groupe",
            "commentaire": "Commentaire",
        }
    elif "Melanges" in nom_fichier:
        colonnes_map = {
            "ref": "Référence",
            "nom": "Nom",
            "emplacement": "Emplacement",
            "commentaire": "Commentaire",
        }
    else:
        colonnes_map = None

    donnees_propres = []
    colonnes_finales = []

    for ligne in donnees_list:
        if colonnes_map:
            ligne_propre = {
                libelle: ligne.get(cle, "")
                for cle, libelle in colonnes_map.items()
            }
            if "Elements" in nom_fichier:
                ligne_propre["Compartiments"] = ", ".join(
                    ligne.get("compartiments", [])
                )
            if "Melanges" in nom_fichier:
                for index_composant, composant in enumerate(
                    ligne.get("couleurs_associees", []),
                    start=1,
                ):
                    ligne_propre[f"Composant {index_composant}"] = composant.get(
                        "nom",
                        "",
                    )
                    ligne_propre[f"Dosage {index_composant}"] = composant.get(
                        "dosage",
                        "",
                    )
        else:
            ligne_propre = {
                cle: json.dumps(valeur, ensure_ascii=False)
                if isinstance(valeur, (list, dict))
                else valeur
                for cle, valeur in ligne.items()
            }
        donnees_propres.append(ligne_propre)
        for cle in ligne_propre:
            if cle not in colonnes_finales:
                colonnes_finales.append(cle)

    try:
        import pandas as pd

        dataframe = pd.DataFrame(donnees_propres).reindex(columns=colonnes_finales)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            dataframe.to_excel(writer, index=False, sheet_name="Export")
        return (
            buffer.getvalue(),
            f"{nom_fichier}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except (ImportError, ModuleNotFoundError):
        buffer_texte = io.StringIO()
        writer = csv.DictWriter(
            buffer_texte,
            fieldnames=colonnes_finales,
            extrasaction="ignore",
            delimiter=";",
        )
        writer.writeheader()
        writer.writerows(donnees_propres)
        return (
            buffer_texte.getvalue().encode("utf-8-sig"),
            f"{nom_fichier}.csv",
            "text/csv",
        )


def add_tmp_item(state_dict_name, cle, data):
    st.session_state.setdefault(state_dict_name, {})[cle] = data


def remove_tmp_item_cb(state_dict_name, widget_key, dict_key):
    if not st.session_state.get(widget_key, True):
        st.session_state.setdefault(state_dict_name, {}).pop(dict_key, None)


# Filigrane général facultatif.
LOGO_BACKGROUND_BASE64 = encoder_image_systeme("Logo-Beraudy-rectangle.png")
if LOGO_BACKGROUND_BASE64:
    st.markdown(
        f"""
        <style>
        [data-testid="stAppViewContainer"]::before {{
            content:"";
            position:fixed;
            inset:0;
            background-image:url("data:image/png;base64,{LOGO_BACKGROUND_BASE64}");
            background-size:45%;
            background-repeat:no-repeat;
            background-position:center;
            opacity:.035;
            z-index:0;
            pointer-events:none;
        }}
        [data-testid="stHeader"], [data-testid="stVerticalBlock"], .stMain {{
            position:relative;
            z-index:1;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# PDF
# =============================================================================


def dessiner_fond_pdf(canvas_pdf, document):
    canvas_pdf.saveState()
    canvas_pdf.setFillColor(colors.HexColor("#FCFAF5"))
    canvas_pdf.rect(
        0,
        0,
        document.pagesize[0],
        document.pagesize[1],
        fill=True,
        stroke=False,
    )
    logo = "Logo-Beraudy-rectangle.png"
    if os.path.exists(logo):
        try:
            canvas_pdf.setFillAlpha(0.07)
            canvas_pdf.drawImage(
                logo,
                document.pagesize[0] / 2 - 145,
                document.pagesize[1] / 2 - 45,
                width=290,
                height=90,
                mask="auto",
            )
        except Exception:
            pass
    canvas_pdf.restoreState()

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

def dessiner_fond_ivoire_et_filigrane(canvas, doc):
    canvas.saveState()
    # 1. Application de la couleur de fond Ivoire / Crème Vintage
    canvas.setFillColor(colors.HexColor('#F9F8F6'))
    canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], fill=True, stroke=False)
    
    # 2. Application du filigrane transparent à 10% au centre de la page
    img_path = "Logo-Beraudy-rectangle.png"
    if os.path.exists(img_path):
        try:
            canvas.setFillAlpha(0.1) # Opacité stricte de 10%
            # Format Letter (612 x 792 points) - Centrage parfait
            canvas.drawImage(img_path, doc.pagesize[0]/2 - 150, doc.pagesize[1]/2 - 50, width=300, height=100, mask='auto')
        except Exception:
            pass # Sécurité anti-crash si la version de ReportLab gère mal l'alpha
    canvas.restoreState()

def generer_pdf_mindmap(fiche):
    buffer = io.BytesIO()
    if not REPORTLAB_DISPO:
        buffer.write("ReportLab non disponible.".encode("utf-8"))
        buffer.seek(0)
        return buffer

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=25,
        rightMargin=25,
        topMargin=25,
        bottomMargin=25,
    )
    story = []
    
    title_style = ParagraphStyle(
        'MMTitle',
        fontName='Times-Bold',
        fontSize=15,
        textColor=colors.HexColor('#142235'),
        alignment=1,
        spaceAfter=6,
    )
    story.append(Paragraph(f"MIND MAP / FICHE MÉTHODE : {fiche.get('nom', 'Mind Map')}", title_style))
    if fiche.get('description'):
        desc_style = ParagraphStyle('MMDesc', fontName='Times-Italic', fontSize=9, textColor=colors.HexColor('#50657D'), alignment=1, spaceAfter=8)
        story.append(Paragraph(fiche.get('description'), desc_style))

    noeuds = fiche.get('formes', [])
    liaisons = fiche.get('liaisons', [])
    
    dw_width = 790
    dw_height = 470
    d = Drawing(dw_width, dw_height)
    
    d.add(Rect(0, 0, dw_width, dw_height, fillColor=colors.HexColor('#FCFAF5'), strokeColor=colors.HexColor('#D9BF91'), strokeWidth=0.5))
    
    if noeuds:
        xs = [float(n.get('x', 0)) for n in noeuds]
        ys = [float(n.get('y', 0)) for n in noeuds]
        min_x, max_x = min(xs) - 100, max(xs) + 100
        min_y, max_y = min(ys) - 70, max(ys) + 70
        
        box_w = max(400, max_x - min_x)
        box_h = max(250, max_y - min_y)
        
        scale_x = (dw_width - 40) / box_w
        scale_y = (dw_height - 40) / box_h
        scale = min(scale_x, scale_y, 1.1)
        
        def to_pdf_coords(nx, ny):
            px = 20 + (nx - min_x) * scale
            py = dw_height - (20 + (ny - min_y) * scale)
            return px, py
        
        node_map_coords = {}
        for n in noeuds:
            px, py = to_pdf_coords(float(n.get('x', 0)), float(n.get('y', 0)))
            node_map_coords[str(n.get('id'))] = (px, py, n)
            
        for l in liaisons:
            src_id = str(l.get('from'))
            dst_id = str(l.get('to'))
            if src_id in node_map_coords and dst_id in node_map_coords:
                x1, y1, _ = node_map_coords[src_id]
                x2, y2, _ = node_map_coords[dst_id]
                edge_color = colors.HexColor(l.get('color', '#50657D'))
                d.add(Line(x1, y1, x2, y2, strokeColor=edge_color, strokeWidth=1.5))
                if l.get('label'):
                    mx, my = (x1 + x2)/2, (y1 + y2)/2
                    d.add(String(mx, my, str(l.get('label')), fontName='Times-Roman', fontSize=7, textAnchor='middle', fillColor=colors.HexColor('#344A63')))
                    
        for nid, (px, py, n) in node_map_coords.items():
            nw = float(n.get('width', 190)) * scale * 0.72
            nh = float(n.get('height', 78)) * scale * 0.72
            fill_c = colors.HexColor(n.get('color', '#F4EBDD'))
            border_c = colors.HexColor(n.get('border_color', '#9B7740'))
            text_c = colors.HexColor(n.get('text_color', '#142235'))
            
            d.add(Rect(px - nw/2, py - nh/2, nw, nh, rx=6, ry=6, fillColor=fill_c, strokeColor=border_c, strokeWidth=1.5))
            lbl = str(n.get('label', ''))
            sub = str(n.get('subtitle', ''))
            d.add(String(px, py + (2 if sub else -2), lbl, fontName='Times-Bold', fontSize=min(10, max(7, int(10 * scale))), textAnchor='middle', fillColor=text_c))
            if sub:
                d.add(String(px, py - 8, sub, fontName='Times-Italic', fontSize=min(8, max(6, int(8 * scale))), textAnchor='middle', fillColor=text_c))

    story.append(d)
    
    def on_page(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(colors.HexColor('#F9F8F6'))
        canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], fill=True, stroke=False)
        canvas.restoreState()

    doc.build(story, onFirstPage=on_page, canvasmaker=NumeroteurDePages)
    buffer.seek(0)
    return buffer

# --- GENERATEUR DE FICHE TECHNIQUE STANDARD PDF (REPORTLAB) ---
def dessiner_fond_ivoire_et_entete(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(colors.HexColor('#F9F8F6'))
    canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], fill=True, stroke=False)
    
    img_path = "Logo-Beraudy-rectangle.png"
    if os.path.exists(img_path):
        try:
            canvas.setFillAlpha(0.08)
            canvas.drawImage(img_path, doc.pagesize[0]/2 - 150, doc.pagesize[1]/2 - 50, width=300, height=100, mask='auto')
        except Exception:
            pass
            
    # Entête répété sur chaque page après la 1ère
    if doc.page > 1:
        canvas.setFillColor(colors.HexColor('#142235'))
        canvas.setFont('Times-Bold', 9)
        canvas.drawString(45, doc.pagesize[1] - 28, "B&V — FICHE TECHNIQUE INDUSTRIELLE (SUITE)")
        canvas.setStrokeColor(colors.HexColor('#2C3539'))
        canvas.setLineWidth(0.5)
        canvas.line(45, doc.pagesize[1] - 32, doc.pagesize[0] - 45, doc.pagesize[1] - 32)
        
    canvas.restoreState()

def generer_pdf_fiche_technique(data_obj, type_ft="melange"):
    """
    Génère une Fiche Technique PDF (Mélange, Couleur ou Élément) au format
    Béraudy & Vaure avec mise en page fidèle au template visuel.
    """
    buffer = io.BytesIO()

    # -----------------------------------------------------------------------
    # Vérification ReportLab (à adapter selon votre constante globale)
    # -----------------------------------------------------------------------
    try:
        from reportlab.platypus import SimpleDocTemplate
    except ImportError:
        buffer.write("ReportLab non disponible sur ce système.".encode('utf-8'))
        buffer.seek(0)
        return buffer

    # -----------------------------------------------------------------------
    # Configuration du document (marges éditoriales classiques)
    # -----------------------------------------------------------------------
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50
    )
    story = []

    # -----------------------------------------------------------------------
    # Styles typographiques (Vintage / Serif – Times)
    # -----------------------------------------------------------------------
    title_style = ParagraphStyle(
        'TitleStyle',
        fontName='Times-Bold',
        fontSize=20,
        textColor=colors.HexColor('#CC0605'),
        alignment=2,  # Droite
        spaceBefore=10,
        spaceAfter=5
    )

    h2_style = ParagraphStyle(
        'H2Style',
        fontName='Times-Bold',
        fontSize=11,
        textColor=colors.HexColor('#2C3539'),
        spaceBefore=14,
        spaceAfter=8,
        borderPadding=4,
        borderBottom=0.5,
        borderBottomColor=colors.HexColor('#2C3539')
    )

    body_style = ParagraphStyle(
        'BodyStyle',
        fontName='Times-Roman',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#2C3539')
    )

    body_bold = ParagraphStyle(
        'BodyBold',
        fontName='Times-Bold',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#2C3539')
    )

    # -----------------------------------------------------------------------
    # Titre principal selon le type de fiche
    # -----------------------------------------------------------------------
    if type_ft == "melange":
        titre_principal = "FICHE TECHNIQUE PRODUIT"
    elif type_ft == "couleur":
        titre_principal = "FICHE TECHNIQUE COULEUR"
    else:
        titre_principal = "FICHE TECHNIQUE ÉLÉMENT"

    # =======================================================================
    # 1. EN-TÊTE : Logo (gauche) + Titre (droite)
    # =======================================================================
    header_data = [["", Paragraph(titre_principal, title_style)]]
    header_table = Table(header_data, colWidths=[160, 352])

    img_path = "Logo-Beraudy-rectangle.png"
    if os.path.exists(img_path):
        try:
            img_rl = RLImage(img_path, width=170, height=44)
            img_rl.hAlign = 'LEFT'
            header_table._cellvalues[0][0] = img_rl
        except Exception:
            header_table._cellvalues[0][0] = Paragraph("<b>BÉRAUDY & VAURE</b>", body_bold)
    else:
        header_table._cellvalues[0][0] = Paragraph("<b>BÉRAUDY & VAURE</b>", body_bold)

    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LINEBELOW', (0, 0), (-1, -1), 1, colors.HexColor('#2C3539'))
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8))

    ft_data = data_obj.get("fiche_technique", {})

    # =======================================================================
    # 2. BLOC SUPÉRIEUR : Informations Générales (gauche) | Aperçu Visuel (droite)
    # =======================================================================

    # -- Colonne gauche : Informations Générales --
    if type_ft == "melange":
        story.append(Paragraph("Informations Générales", h2_style))
        titre_melange = data_obj.get("nom", "-")
        if data_obj.get("statut") == "Vérifier":
            titre_melange += " <font color='#CC0605'>🔴 (Vérifier)</font>"
        infos_rows = [
            [Paragraph("<b>Nom du Mélange :</b>", body_style), Paragraph(titre_melange, body_style)],
            [Paragraph("<b>Référence interne :</b>", body_style), Paragraph(nettoyer_valeur_pdf(data_obj.get("ref")), body_style)],
            [Paragraph("<b>Stockage / Emplacement :</b>", body_style), Paragraph(nettoyer_valeur_pdf(data_obj.get("emplacement")), body_style)]
        ]
    elif type_ft == "couleur":
        story.append(Paragraph("Informations Générales", h2_style))
        infos_rows = [
            [Paragraph("<b>Nom actuel :</b>", body_style), Paragraph(nettoyer_valeur_pdf(data_obj.get("nom_actuel")), body_style)],
            [Paragraph("<b>Référence :</b>", body_style), Paragraph(nettoyer_valeur_pdf(data_obj.get("ref")), body_style)],
            [Paragraph("<b>Futur nom :</b>", body_style), Paragraph(nettoyer_valeur_pdf(data_obj.get("nom_futur")), body_style)],
            [Paragraph("<b>Code RAL :</b>", body_style), Paragraph(nettoyer_valeur_pdf(data_obj.get("ral")), body_style)],
            [Paragraph("<b>Société :</b>", body_style), Paragraph(nettoyer_valeur_pdf(data_obj.get("societe")), body_style)],
            [Paragraph("<b>Type :</b>", body_style), Paragraph(nettoyer_valeur_pdf(data_obj.get("type")), body_style)]
        ]
    else:
        story.append(Paragraph("Informations Générales", h2_style))
        titre_element = data_obj.get("nom", "-")
        if data_obj.get("statut") == "Vérifier":
            titre_element += " <font color='#CC0605'>🔴 (Vérifier)</font>"
        infos_rows = [
            [Paragraph("<b>Nom de l'élément :</b>", body_style), Paragraph(titre_element, body_style)],
            [Paragraph("<b>Code :</b>", body_style), Paragraph(nettoyer_valeur_pdf(data_obj.get("code")), body_style)],
            [Paragraph("<b>Désignation :</b>", body_style), Paragraph(nettoyer_valeur_pdf(data_obj.get("designation")), body_style)],
            [Paragraph("<b>Fournisseur :</b>", body_style), Paragraph(nettoyer_valeur_pdf(data_obj.get("fournisseur")), body_style)],
            [Paragraph("<b>Code Article Achat :</b>", body_style), Paragraph(nettoyer_valeur_pdf(data_obj.get("code_article")), body_style)],
            [Paragraph("<b>Désignation Achat :</b>", body_style), Paragraph(nettoyer_valeur_pdf(data_obj.get("designation_achat")), body_style)]
        ]

    t_infos = Table(infos_rows, colWidths=[140, 180])
    t_infos.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFFFF')),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#E2E8F0')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    # -- Colonne droite : Aperçu Visuel --
    apercu_rows = []
    img_apercu = None
    if "image_rendu" in data_obj and data_obj["image_rendu"]:
        try:
            img_bytes = base64.b64decode(data_obj["image_rendu"]["data"])
            img_apercu = RLImage(io.BytesIO(img_bytes), width=80, height=80)
            img_apercu.hAlign = 'CENTER'
            apercu_rows.append([img_apercu])
        except Exception:
            apercu_rows.append([Paragraph("-", body_style)])
    elif type_ft == "couleur" or ("visuel" in data_obj and data_obj.get("visuel")):
        try:
            # Génération dynamique du carré de couleur pour le PDF
            hex_color = data_obj.get("visuel", "#D8DEE4")
            if not hex_color or not re.fullmatch(r"#[0-9a-fA-F]{6}", str(hex_color)):
                hex_color = "#D8DEE4"
            
            img_pastille = Image.new('RGB', (160, 160), color=hex_color)
            buffer_img = io.BytesIO()
            img_pastille.save(buffer_img, format='PNG')
            buffer_img.seek(0)
            
            img_apercu = RLImage(buffer_img, width=80, height=80)
            img_apercu.hAlign = 'CENTER'
            apercu_rows.append([img_apercu])
        except Exception:
            apercu_rows.append([Paragraph("-", body_style)])
    else:
        apercu_rows.append([Paragraph("-", body_style)])

    t_apercu = Table(apercu_rows, colWidths=[192])
    t_apercu.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 0),
    ]))

    # -- Assemblage des deux colonnes --
    top_table = Table([[t_infos, t_apercu]], colWidths=[320, 192])
    top_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(top_table)
    story.append(Spacer(1, 1))



    # =======================================================================
    # 3. FORMULATION INDUSTRIELLE DE BASE (Mélanges uniquement)
    # =======================================================================
    if type_ft == "melange":
        story.append(Paragraph("Formulation Industrielle de Base", h2_style))
        data_comp = [[
            Paragraph("<b>Code/Réf</b>", body_bold),
            Paragraph("<b>Composant</b>", body_bold),
            Paragraph("<b>Désignation</b>", body_bold),
            Paragraph("<b>Dosage</b>", body_bold),
            Paragraph("<b>Note / Commentaire</b>", body_bold),
            Paragraph("<b>Risque</b>", body_bold)
        ]]

        db_prep = st.session_state.processus_db.get("preparation_melanges", {})
        tous_elements = db_prep.get("additifs", [])
        toutes_couleurs = db_prep.get("couleurs", [])
        tous_melanges = db_prep.get("melanges", [])

        for c in data_obj.get("couleurs_associees", []):
            code_aff, des_aff, dan_aff = "-", "-", "-"
            ctype = c.get('type')

            if ctype in ["additif", "element"]:
                item = next((a for a in tous_elements if a["nom"] == c.get("ref")), None)
                if item:
                    code_aff = item.get("code", "-")
                    des_aff = item.get("designation", "-")
                    dan_aff = item.get("danger", "-")
            elif ctype == "couleur":
                item = next((a for a in toutes_couleurs if a["ref"] == c.get("ref")), None)
                if item:
                    code_aff = item.get("ref", "-")
                    des_aff = item.get("nom_actuel", "-")
            elif ctype == "melange_base":
                item = next((a for a in tous_melanges if a["ref"] == c.get("ref")), None)
                if item:
                    code_aff = item.get("ref", "-")
                    des_aff = item.get("nom", "-")
            elif ctype == "ral_officiel":
                code_aff = c.get("ref", "-")
                des_aff = c.get("nom", "-")

            comm_comp = c.get("commentaire_composant", "") or "-"
            data_comp.append([
                Paragraph(nettoyer_valeur_pdf(code_aff), body_style),
                Paragraph(c.get('nom', '-'), body_style),
                Paragraph(nettoyer_valeur_pdf(des_aff), body_style),
                Paragraph(nettoyer_valeur_pdf(c.get('dosage')), body_style),
                Paragraph(nettoyer_valeur_pdf(comm_comp), body_style),
                Paragraph(nettoyer_valeur_pdf(dan_aff), body_style)
            ])

        if len(data_comp) > 1:
            # Largeurs ajustées pour un total exact de 512 pt
            t_comp = Table(data_comp, colWidths=[55, 100, 100, 65, 122, 70], repeatRows=1)
            t_comp.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
                ('PADDING', (0, 0), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(t_comp)
        else:
            story.append(Paragraph("Aucun composant rattaché à cette formulation.", body_style))
        story.append(Spacer(1, 1))

    # =======================================================================
    # 4. COMMENTAIRES GÉNÉRAUX / NOTES
    # =======================================================================
    story.append(Paragraph("Commentaires Généraux / Notes", h2_style))
    comm_global = data_obj.get("commentaire_global", "")
    t_comm = Table([[Paragraph(nettoyer_valeur_pdf(comm_global), body_style)]], colWidths=[512])
    t_comm.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFBEB')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('BOX', (0, 0), (-1, -1), 0.2, colors.HexColor('#F59E0B')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(t_comm)
    story.append(Spacer(1, 1))

    
    # =======================================================================
    # 5. SPÉCIFICATIONS PHYSICO-CHIMIQUES
    # =======================================================================
    specs_dyn = ft_data.get("specs_dynamiques", {})
    
    # Fallback compatibilité descendante : anciens champs fixes
    if not specs_dyn:
        mapping_legacy = {
            "Aspect / Finition": ft_data.get("aspect", ""),
            "Viscosité attendue": ft_data.get("viscosite", ""),
            "Densité": ft_data.get("densite", ""),
            "Temps de séchage": ft_data.get("sechage", ""),
            "Conditions d'application": ft_data.get("conditions", ""),
        }
        specs_dyn = {k: v for k, v in mapping_legacy.items() if str(v).strip()}
    
    # Filtrer également les valeurs vides du nouveau format
    specs_dyn = {k: v for k, v in specs_dyn.items() if str(v).strip()}
    
    if specs_dyn:
        story.append(Paragraph("Spécifications Physico-Chimiques", h2_style))
        spec_rows = []
        items = list(specs_dyn.items())
        for i in range(0, len(items), 2):
            row = [
                Paragraph(f"<b>{items[i][0]} :</b>", body_style),
                Paragraph(nettoyer_valeur_pdf(items[i][1]), body_style)
            ]
            if i + 1 < len(items):
                row.extend([
                    Paragraph(f"<b>{items[i + 1][0]} :</b>", body_style),
                    Paragraph(nettoyer_valeur_pdf(items[i + 1][1]), body_style)
                ])
            else:
                row.extend(["", ""])
            spec_rows.append(row)
        t_spec = Table(spec_rows, colWidths=[110, 146, 110, 146])
        t_spec.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFFFF')),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(t_spec)
        story.append(Spacer(1, 2))
        
        
    # =======================================================================
    # 6. SUIVI ET TRAÇABILITÉ
    # =======================================================================
    story.append(Paragraph("Suivi et Traçabilité de la Fiche", h2_style))
    date_rows = [
        [
            Paragraph("<b>Création :</b>", body_style),
            Paragraph(nettoyer_valeur_pdf(ft_data.get("date_creation")), body_style),
            Paragraph("<b>Dernière MÀJ :</b>", body_style),
            Paragraph(nettoyer_valeur_pdf(ft_data.get("date_derniere_maj")), body_style),
            Paragraph("<b>Précédente MÀJ :</b>", body_style),
            Paragraph(nettoyer_valeur_pdf(ft_data.get("date_avant_derniere_maj")), body_style)
        ]
    ]
    t_date = Table(date_rows, colWidths=[65, 95, 85, 95, 90, 82])
    t_date.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFFFF')),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(t_date)

    # --- Tableau des causes de modification (Version | Date | Modification) ---
    causes_list = ft_data.get("causes_modification", [])
    if causes_list:
        table_causes_data = [[
            Paragraph("<b>Version</b>", body_bold),
            Paragraph("<b>Date</b>", body_bold),
            Paragraph("<b>Modification</b>", body_bold)
        ]]
        
        for idx, item in enumerate(causes_list[-4:], start=1):
            if isinstance(item, dict):
                ver_str = item.get("version", f"v{idx + 1}")
                date_str = item.get("date", "-")
                cause_str = item.get("cause", "-")
            else:
                ver_str = f"v{idx + 1}"
                date_str = "-"
                cause_str = str(item)
                
            table_causes_data.append([
                Paragraph(nettoyer_valeur_pdf(ver_str), body_style),
                Paragraph(nettoyer_valeur_pdf(date_str), body_style),
                Paragraph(nettoyer_valeur_pdf(cause_str), body_style)
            ])
            
        t_causes = Table(table_causes_data, colWidths=[60, 115, 337], repeatRows=1)
        t_causes.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
            ('PADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(Spacer(1, 4))
        story.append(t_causes)

    story.append(Spacer(1, 1))    
    
    # =======================================================================
    # 7. SIGNATURES (poussées vers le bas de page)
    # =======================================================================
    # Spacer flexible pour pousser le bloc signature en bas si l'espace le permet
    story.append(Spacer(1, 11))

    redacteur = ft_data.get('redacteur', 'Labo / R&D')
    data_sign = [
        [
            Paragraph(f"<b>Visa Rédacteur / Émetteur :</b><br/>{redacteur}", body_style),
            Paragraph("<b>Approbation Direction :</b><br/>Responsable Qualité Industrielle", body_style)
        ],
        [
            Paragraph("<br/><br/><i>Signature : ___________________</i>", body_style),
            Paragraph("<br/><br/><i>Signature : ___________________</i>", body_style)
        ]
    ]
    t_sign = Table(data_sign, colWidths=[256, 256])
    t_sign.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 2.5),
        ('LINEBEFORE', (1, 0), (1, -1), 0.5, colors.HexColor('#CBD5E1')),
    ]))
    story.append(t_sign)

    # =======================================================================
    # CONSTRUCTION FINALE
    # =======================================================================
    # Remplacez dessiner_fond_ivoire_et_filigrane et NumeroteurDePages
    # par vos callbacks / canvasmaker existants dans votre projet.
    doc.build(
        story,
        onFirstPage=dessiner_fond_ivoire_et_filigrane,
        onLaterPages=dessiner_fond_ivoire_et_filigrane,
        canvasmaker=NumeroteurDePages
    )

    buffer.seek(0)
    return buffer



# =============================================================================
# DIALOGUES DE CONSULTATION
# =============================================================================


@st.dialog("Fiche Technique — Mélange", width="large")
def ouvrir_visualisation_ft(melange):
    st.markdown(f"### {melange.get('nom', 'Mélange')}")
    fiche = melange.get("fiche_technique", {})
    st.info(
        f"Création : {fiche.get('date_creation', '-')} | "
        f"Dernière mise à jour : {fiche.get('date_derniere_maj', '-')}"
    )
    col_visuel, col_actions = st.columns([1, 2])
    with col_visuel:
        if melange.get("image_rendu"):
            afficher_image_base64(melange["image_rendu"].get("data"), width=160)
        else:
            st.caption("Aucune image associée.")
    with col_actions:
        nom_p = melange.get('nom', 'Melange')
        ref_p = melange.get('ref', 'sans_ref')
        nom = f"FT_{nom_p}_{ref_p}.pdf".replace(" ", "_").replace("/", "-")
        st.download_button(
            "Télécharger le PDF",
            data=generer_pdf_fiche_technique(melange, "melange"),
            file_name=nom,
            mime="application/pdf",
            use_container_width=True,
        )


@st.dialog("Fiche Technique — Élément", width="large")
def ouvrir_visualisation_ft_additif(additif):
    st.markdown(f"### {additif.get('nom', 'Élément')}")
    fiche = additif.get("fiche_technique", {})
    st.info(
        f"Création : {fiche.get('date_creation', '-')} | "
        f"Dernière mise à jour : {fiche.get('date_derniere_maj', '-')}"
    )
    nom_p = additif.get('nom', 'Element')
    code_p = additif.get('code') or additif.get('ref', 'sans_code')
    nom = f"FT_{nom_p}_{code_p}.pdf".replace(" ", "_").replace("/", "-")
    st.download_button(
        "Télécharger le PDF",
        data=generer_pdf_fiche_technique(additif, "additif"),
        file_name=nom,
        mime="application/pdf",
        use_container_width=True,
    )


@st.dialog("Fiche Technique — Couleur", width="large")
def ouvrir_visualisation_ft_couleur(couleur):
    st.markdown(
        f"### {couleur.get('nom_actuel', 'Couleur')} ({couleur.get('ref', '-')})"
    )
    col_apercu, col_action = st.columns([1, 2])
    with col_apercu:
        st.markdown(
            f"<div style='width:120px;height:120px;background:{couleur.get('visuel', '#D8DEE4')};border:1px solid #142235;border-radius:12px;'></div>",
            unsafe_allow_html=True,
        )
    with col_action:
        nom_p = couleur.get('nom_actuel', 'Couleur')
        ref_p = couleur.get('ref', 'sans_ref')
        nom = f"FT_{nom_p}_{ref_p}.pdf".replace(" ", "_").replace("/", "-")
        st.download_button(
            "Télécharger le PDF",
            data=generer_pdf_fiche_technique(couleur, "couleur"),
            file_name=nom,
            mime="application/pdf",
            use_container_width=True,
        )


@st.dialog("Détails de la couleur", width="large")
def ouvrir_details_couleur(couleur):
    st.markdown(
        f"### {couleur.get('nom_actuel', 'Couleur')} ({couleur.get('ref', '-')})"
    )
    col_texte, col_apercu = st.columns(2)
    with col_texte:
        st.write(f"**Futur nom :** {couleur.get('nom_futur', '-')}")
        st.write(f"**RAL :** {couleur.get('ral', '-')}")
        st.write(f"**Société :** {couleur.get('societe', '-')}")
        st.write(f"**Type :** {couleur.get('type', '-')}")
        st.write(f"**Statut :** {couleur.get('statut', 'Pas vérifié')}")
    with col_apercu:
        st.markdown(
            f"<div style='width:150px;height:150px;margin:auto;background:{couleur.get('visuel', '#D8DEE4')};border:2px solid #142235;border-radius:14px;'></div>",
            unsafe_allow_html=True,
        )


@st.dialog("Détails de l'élément", width="large")
def ouvrir_details_element(element):
    st.markdown(f"### {element.get('nom', 'Élément')} ({element.get('code', '-')})")
    col_gauche, col_droite = st.columns(2)
    with col_gauche:
        st.write(f"**Désignation :** {element.get('designation', '-')}")
        st.write(f"**Fournisseur :** {element.get('fournisseur', '-')}")
        st.write(
            f"**Compartiments :** {', '.join(element.get('compartiments', [])) or '-'}"
        )
        st.write(f"**Sous-groupe :** {element.get('sous_groupe', 'Général')}")
    with col_droite:
        st.write(f"**Nature :** {element.get('nature', '-')}")
        st.write(f"**Danger :** {element.get('danger', '-')}")
        st.write(f"**Précision :** {element.get('danger_texte', '-')}")
        st.write(f"**Statut :** {element.get('statut', 'Pas vérifié')}")
    st.write(f"**Commentaire :** {element.get('commentaire', '-')}")


# Alias conservé pour compatibilité avec l'ancien code.
abrir_details_element = ouvrir_details_element


@st.dialog("Détails du mélange", width="large")
def ouvrir_details_melange(melange):
    st.markdown(
        f"### {melange.get('nom', 'Mélange')} ({melange.get('ref', '-')})"
    )
    col_gauche, col_droite = st.columns(2)
    with col_gauche:
        st.write(f"**Catégorie :** {melange.get('categorie_choisie', '-')}")
        st.write(f"**Emplacement :** {melange.get('emplacement', '-')}")
        st.write(f"**Statut :** {melange.get('statut', '-')}")
        st.write(f"**Commentaire :** {melange.get('commentaire', '-')}")
    with col_droite:
        if melange.get("image_rendu"):
            afficher_image_base64(melange["image_rendu"].get("data"), width=170)
        else:
            st.caption("Aucune image associée.")

    st.markdown("#### Composants")
    composants = melange.get("couleurs_associees", [])
    if not composants:
        st.info("Aucun composant enregistré.")
    for composant in composants:
        st.markdown(
            f"- **{composant.get('nom', '-')}** — {composant.get('dosage', '-')}"
        )

# --- URL ROUTING & AIDE ---
query_params = st.query_params
@st.dialog("❓ Centre d'Aide Intégré B&V", width="large")
def ouvrir_fenetre_aide():
    astuces = [
        "Utilisez la recherche globale dans le menu de gauche pour retrouver instantanément un produit par son nom, sa référence ou son code RAL.",
        "Les codes RAL reconnus (ex: 5015) mettent automatiquement à jour le visuel de la couleur.",
        "Pensez à générer une FT pour chaque nouveau mélange pour avoir un export PDF complet et professionnel.",
        "Les commentaires courts saisis lors de la formulation sont inclus directement dans le récapitulatif PDF.",
        "Le mode Grand Écran est disponible dans la création de processus pour une meilleure lisibilité en atelier.",
        "Vous pouvez exporter n'importe quel tableau (Couleurs, Mélanges) au format Excel en un seul clic."
    ]
    recherche_aide = st.text_input("🔎 Rechercher dans l'aide (ex: pdf, couleur, mélange, erreur)...").strip().lower()
    if recherche_aide:
        st.markdown(f"### 🔍 Résultats de recherche pour '{recherche_aide}'")
        if any(mot in recherche_aide for mot in ["pdf", "export", "imprimer", "excel"]):
            st.info("📄 **Export PDF / Excel :** Utilisez les boutons 'Exporter Excel' au-dessus des tableaux de données, ou les boutons '📄 FT' / '⬇️ PDF' pour générer la fiche technique d'un produit.")
        if any(mot in recherche_aide for mot in ["couleur", "ral", "teinte", "nuancier"]):
            st.info("🎨 **Couleurs :** Allez dans l'onglet 'Nuancier de couleurs' pour ajouter ou modifier une teinte. La vérification du code RAL est entièrement automatisée.")
        if any(mot in recherche_aide for mot in ["mélange", "formulation", "dosage", "composant"]):
            st.info("⚗️ **Mélanges :** Naviguez vers 'Formulations d'atelier', cliquez sur 'Créer une fiche de mélange', puis filtrez et cochez les composants souhaités en indiquant leur dosage.")
        if any(mot in recherche_aide for mot in ["processus", "étape", "sop"]):
            st.info("🏭 **Processus :** Rendez-vous dans 'Création des Processus', ajoutez un nouveau fichier, puis ajoutez des étapes avec descriptions et images.")
        st.markdown("---")
    
    onglets = st.tabs([
        "📖 Premiers pas", 
        "🎨 Processus & Couleurs", 
        "⚗️ Formulations & FT", 
        "❓ FAQ", 
        "⚠ Dépannage", 
        "📞 Support & Versions"
    ])
    
    with onglets[0]:
        st.markdown("### 📖 Guide de démarrage rapide")
        st.write("B&V est divisé en plusieurs modules accessibles depuis la barre latérale. Sélectionnez une action ci-dessous pour découvrir comment l'utiliser :")
        with st.expander("🏭 Création des processus industriels (SOP)", expanded=True):
            st.markdown("""
            - **Créer un nouveau processus :** Saisissez un nom dans le menu latéral gauche et cliquez sur "Créer la fiche".
            - **Ajouter une étape :** Cliquez sur le bouton principal "➕ Créer une étape" puis remplissez le titre et la description.
            - **Mode Grand Écran :** Utilisez le bouton 🖥️ en haut à droite de l'écran pour basculer l'affichage (idéal pour les écrans d'atelier).
            """)
        with st.expander("🔍 Utiliser la recherche globale"):
            st.markdown("""
            La barre de recherche ultra-rapide (en haut à gauche) permet de retrouver instantanément :
            - Une **couleur** par son nom, sa référence ou son code RAL.
            - Un **mélange** par sa référence ou son emplacement.
            - Un **élément/additif** par sa désignation ou son fournisseur.
            Cliquez simplement sur **👁️ Voir** ou **Accéder** dans les résultats pour ouvrir la fiche correspondante sans perdre votre travail en cours.
            """)

    with onglets[1]:
        st.markdown("### 🎨 Gestion du Nuancier et des Éléments")
        with st.expander("🎨 Nuancier de couleurs", expanded=True):
            st.markdown("""
            - **Ajouter une couleur :** Renseignez la référence unique, le nom actuel/futur et le type.
            - **Vérification automatique RAL :** Saisissez un code (ex: 3020) et cliquez sur "Vérifier RAL" pour appliquer la teinte hexadécimale officielle.
            - **Créer une Fiche Technique :** Activez le toggle "📝 Créer la Fiche Technique" pour ajouter les conditions d'application et assigner un rédacteur.
            """)
        with st.expander("🧪 Catalogue des composants (Additifs)"):
            st.markdown("""
            Gérez vos matières premières et additifs d'atelier :
            - **Déclarer un danger :** Sélectionnez "Oui" dans la catégorie Risque/Danger pour afficher une pastille rouge 🔴 d'avertissement sur toutes les interfaces liées.
            - **Traçabilité :** Renseignez le fournisseur et le code article achat pour faire le lien avec l'ERP.
            """)

    with onglets[2]:
        st.markdown("### ⚗️ Formulations d'atelier & Fiches Techniques")
        with st.expander("🧪 Créer et modifier un mélange", expanded=True):
            st.markdown("""
            1. Cliquez sur **➕ Créer une fiche de mélange**.
            2. Renseignez la référence, le nom, la catégorie et l'emplacement de stockage.
            3. **Ajouter des composants :** Utilisez la barre de filtre pour trouver rapidement vos couleurs, bases existantes ou additifs. Cochez les cases correspondantes.
            4. **Dosage :** Renseignez la quantité exacte (ex: 100g, 50ml, 2%) pour chaque composant coché.
            5. Cliquez sur Enregistrer en bas de la fenêtre.
            """)
        with st.expander("📄 Gestion des Fiches Techniques (PDF)"):
            st.markdown("""
            La Fiche Technique (FT) centralise toutes les données physico-chimiques d'un produit (Viscosité, Densité, Séchage).
            - **Gestion des révisions :** Les dates de création, de dernière mise à jour et de mise à jour précédente sont gérées automatiquement à chaque modification.
            - **Génération PDF :** Cliquez sur le bouton "📄 FT" depuis un tableau pour ouvrir l'aperçu, puis sur "⬇️ PDF" pour télécharger le document formaté et prêt à l'impression.
            """)

    with onglets[3]:
        st.markdown("### ❓ Foire Aux Questions (FAQ)")
        faq_data = {
        "Démarrage & Navigation": {
            "Comment changer la langue du logiciel ?": "Actuellement, B&V est disponible uniquement en français. Une version multilingue est prévue dans les mises à jour futures.",
            "Comment revenir à l'accueil ?": "Cliquez sur le bouton 'Menu Principal / Retour' situé dans la barre latérale gauche.",
            "Est-ce que je peux ouvrir deux onglets B&V ?": "Oui, mais attention : si vous modifiez la même donnée dans deux onglets, la dernière sauvegarde écrasera la première.",
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
            "Où sont stockées les images des couleurs ?": "Elles sont encodées en base64 directement dans le fichier `donnees_bos2.json`."
        },
        "Mélanges & Formulations": {
            "Quelle est la différence entre Mélange et Composant ?": "Un composant est une matière première (additif) ; un mélange est une recette assemblée de composants.",
            "Puis-je mélanger deux mélanges ?": "Oui, utilisez la catégorie 'Mélanges existants (Bases)' lors de la sélection des composants.",
            "Pourquoi mon dosage est en rouge ?": "C'est une alerte de sécurité ou une erreur de formatage dans le champ dosage.",
            "Comment calculer le poids total d'un mélange ?": "Le logiciel calcule la somme des dosages saisis automatiquement dans la FT.",
            "Puis-je modifier un mélange après validation ?": "Oui, mais cela remettra le statut à 'Pas vérifié' pour sécurité.",
            "Comment ajouter une photo à mon mélange ?": "Lors de l'édition, utilisez le champ d'upload d'image dédié au mélange.",
            "Le dosage en pourcentage est-il géré ?": "Oui, saisissez simplement le signe % dans le champ dosage.",
            "Peut-on imprimer une étiquette de mélange ?": "La génération PDF sert de base, vous pouvez imprimer ce PDF pour votre étiquetage.",
            "Pourquoi le bouton 'Enregistrer' est grisé ?": "Vérifiez que le champ 'Référence' est bien rempli.",
            "Comment voir l'historique d'un mélange ?": "Les dates de création et de modification sont visibles dans la Fiche Technique PDF."
        },
        "Fiches Techniques (FT)": {
            "Comment ajouter un risque spécifique ?": "Via l'éditeur d'élément, activez la FT et renseignez le champ 'Danger'.",
            "La FT est-elle modifiable par tous ?": "Les droits d'accès dépendent de votre profil configuré dans l'ERP.",
            "Comment exporter toutes les FT d'un coup ?": "L'export Excel permet de centraliser les données ; pour les PDF, il faut les générer individuellement.",
            "Peut-on ajouter une vidéo dans une FT ?": "Non, seul le format image est supporté actuellement.",
            "Comment changer le logo sur la FT ?": "Le logo est automatique via le fichier `Logo-Beraudy-rectangle.png` à la racine.",
            "Le rédacteur doit-il être choisi ?": "Oui, pour assurer la traçabilité des modifications effectuées.",
            "Que faire si la FT dépasse une page ?": "ReportLab gère automatiquement la pagination et la numérotation.",
            "Puis-je joindre une MSDS externe ?": "Non, le système est auto-suffisant avec les informations de risques internes.",
            "Pourquoi ma FT ne montre pas les composants ?": "Vérifiez que vous avez bien coché les composants dans la section formulation.",
            "Comment valider une FT ?": "La validation est implicite via le changement de statut vers 'Vérifié'."
        },
        "Maintenance & Dépannage": {
            "La recherche ne donne aucun résultat ?": "Videz votre barre de recherche et réessayez sans filtres.",
            "Erreur lors de la sauvegarde JSON ?": "Vérifiez que votre fichier `donnees_bos2.json` n'est pas ouvert dans un autre logiciel.",
            "L'interface semble 'figée' ?": "Il s'agit peut-être de la limite anti-lag. Réduisez vos résultats avec les filtres.",
            "Comment réinitialiser tous les filtres ?": "Supprimez simplement le texte dans toutes les barres de filtres.",
            "Puis-je faire une sauvegarde manuelle ?": "Oui, copiez simplement le fichier `donnees_bos2.json` dans un dossier sécurisé.",
            "Comment restaurer une ancienne sauvegarde ?": "Renommez votre ancienne copie en `donnees_bos2.json` (attention à sauvegarder le courant).",
            "Pourquoi les icônes ne s'affichent pas ?": "Vérifiez que vous avez accès à internet pour charger les polices et icônes externes.",
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
        st.markdown("### ⚠ Dépannage des erreurs fréquentes")
        st.error("""
        **Problème : Mon PDF de fiche technique est vide ou incomplet**
        *Cause probable :* Les spécifications physico-chimiques n'ont pas été remplies lors de la création.
        *Solution :* Éditez le mélange (✏️), activez la gestion de la FT, et complétez les champs Densité, Viscosité, Aspect, etc.
        """)
        st.warning("""
        **Problème : Un code RAL n'est pas reconnu par le système**
        *Cause probable :* Le code saisi n'existe pas dans le référentiel industriel RAL CLASSIC intégré.
        *Solution :* Vous pouvez utiliser la pipette de sélection manuelle (Ajuster la nuance) pour définir la couleur exacte.
        """)
        st.info("""
        **Problème : La liste des couleurs ou des mélanges est tronquée**
        *Cause probable :* La limitation anti-lag est active (50 lignes maximum affichées).
        *Solution :* Utilisez les barres de filtres au-dessus des tableaux pour affiner les résultats et trouver votre produit.
        """)

    with onglets[5]:
        st.markdown("### 📞 Support technique & Historique")
        col_sup, col_ver = st.columns(2)
        with col_sup:
            st.markdown("**Contact Équipe B&V**")
            st.markdown("""
            En cas de blocage critique, veuillez contacter :
            - 🏭 **Responsable R&D** (Anomalie sur les formulations)
            - 📋 **Responsable Qualité** (Validation des FT et processus)
            - 💻 **Support Informatique** (Bugs, lenteurs, sauvegardes serveur)
            """)
        with col_ver:
            st.markdown("**Historique des versions**")
            st.markdown("""
            **B&V v2.5 (Version Actuelle)**
            - ✔️ Intégration du Centre d'aide interactif complet
            - ✔️ Moteur de recherche globale avancé
            - ✔️ Export Excel universel (Couleurs, Éléments, Mélanges)
            - ✔️ Optimisation anti-lag de l'interface
            
            **B&V v1.5**
            - Intégration du générateur de PDF standardisé (ReportLab)
            - Ajout de l'éditeur de fiches méthodes visuel
            """)
            
    st.markdown("---")
    st.success(f"💡 **Astuce du jour :** {random.choice(astuces)}")
    
    if st.button("Fermer l'aide", type="primary", use_container_width=True):
        st.rerun()

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



# =============================================================================
# BARRE LATÉRALE ET RECHERCHE GLOBALE
# =============================================================================

with st.sidebar:
    logo_path = os.path.join(os.getcwd(), "Martineau logo.png")
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    st.markdown(
        '<div style="text-align:center;margin-top:10px;margin-bottom:15px;"><h2>PORTAIL</h2></div>',
        unsafe_allow_html=True,
    )

    # --- Bouton Retour au Menu Principal ---
    if st.button("🏠 Menu Principal", use_container_width=True, key="btn_return_main_menu"):
        st.session_state.groupe_actif = None
        st.session_state.sub_section_melange = None
        st.session_state.navigation_preparation = None
        st.rerun()

    st.markdown("---")

    # --- MENU DES SECTIONS DIRECTEMENT DANS LA BARRE LATÉRALE ---
    sections_preparation = [
        "🎨 Nuancier de couleurs",
        "🧪 Catalogue des composants",
        "🔢 Référentiel des codes RAL",
        "⚗️ Formulations d'atelier",
        "📐 Fiches Méthode",
        "⚖️ Comparaison",
    ]

    # Initialisation de la clé de navigation si absente
    if "navigation_preparation" not in st.session_state:
        st.session_state.navigation_preparation = None

    # Récupération de l'index courant
    nav_actuelle = st.session_state.get("navigation_preparation")
    idx_defaut = sections_preparation.index(nav_actuelle) if nav_actuelle in sections_preparation else None

    choix_section = st.radio(
        "Sélectionnez une section",
        sections_preparation,
        index=idx_defaut,
        key="radio_nav_sidebar",
    )

    # Détection du changement de sélection dans le menu
    if choix_section != st.session_state.navigation_preparation:
        st.session_state.navigation_preparation = choix_section
        if choix_section is None:
            st.session_state.groupe_actif = None
            st.session_state.sub_section_melange = None
        else:
            st.session_state.groupe_actif = "preparation_melanges"
            st.session_state.sub_section_melange = choix_section
        st.rerun()

    st.markdown("---")

    if st.button("❓ Centre de formation", use_container_width=True):
        ouvrir_fenetre_aide()

    st.markdown("---")

    # --- Corbeille en bas du menu latéral ---
    prep_db = st.session_state.processus_db.get("preparation_melanges", {})
    corbeille_list = prep_db.get("corbeille", [])
    nb_elements_corbeille = len(corbeille_list)
    if st.button(f"🗑️ Corbeille ({nb_elements_corbeille})", use_container_width=True, key="sidebar_btn_corbeille"):
        st.session_state.groupe_actif = "corbeille"
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)
search_icon = get_svg_icon("search")
st.markdown(
    f'<div style="display:flex;align-items:center;">{search_icon}<span>RECHERCHE ULTRA-RAPIDE (Filtre instantané)...</span></div>',
    unsafe_allow_html=True,
)
recherche_globale = st.text_input(
    "Recherche globale",
    label_visibility="collapsed",
    key="recherche_globale_principale",
).strip()


if recherche_globale:
    requete = recherche_globale.lower()
    resultats = []
    preparation = st.session_state.processus_db.get("preparation_melanges", {})

    for couleur in preparation.get("couleurs", []):
        if any(
            requete in str(couleur.get(cle, "")).lower()
            for cle in ["ref", "nom_actuel", "nom_futur", "ral", "societe"]
        ):
            resultats.append(
                {
                    "type": "couleur",
                    "label": f"{couleur.get('nom_actuel')} ({couleur.get('ref')})",
                    "data": couleur,
                }
            )
    for element in preparation.get("additifs", []):
        if any(
            requete in str(element.get(cle, "")).lower()
            for cle in ["nom", "code", "designation", "fournisseur"]
        ):
            resultats.append(
                {
                    "type": "élément",
                    "label": f"{element.get('nom')} ({element.get('code')})",
                    "data": element,
                }
            )
    for melange in preparation.get("melanges", []):
        if any(
            requete in str(melange.get(cle, "")).lower()
            for cle in ["ref", "nom", "emplacement"]
        ):
            resultats.append(
                {
                    "type": "mélange",
                    "label": f"{melange.get('nom')} ({melange.get('ref')})",
                    "data": melange,
                }
            )

    if not resultats:
        st.info("Aucun résultat trouvé.")
    else:
        with st.expander(
            f"Résultats de la recherche ({len(resultats)})",
            expanded=True,
        ):
            for index_resultat, resultat in enumerate(resultats[:20]):
                col_texte, col_action = st.columns([4, 1])
                col_texte.markdown(
                    f"**{resultat['type'].title()} :** {resultat['label']}"
                )
                if resultat["type"] == "couleur":
                    if col_action.button("Voir", key=f"search_color_{index_resultat}"):
                        ouvrir_details_couleur(resultat["data"])
                elif resultat["type"] == "élément":
                    if col_action.button("Voir", key=f"search_element_{index_resultat}"):
                        ouvrir_details_element(resultat["data"])
                elif resultat["type"] == "mélange":
                    if col_action.button("Voir", key=f"search_mix_{index_resultat}"):
                        ouvrir_details_melange(resultat["data"])
                else:
                    if col_action.button("Accéder", key=f"search_process_{index_resultat}"):
                        st.session_state.groupe_actif = "creation_processus"
                        st.session_state.produit_selectionne = resultat["data"]
                        st.rerun()



# =============================================================================
# PORTAIL PRINCIPAL — ÉCRAN D'ACCUEIL BLANC AVEC FILIGRANE
# =============================================================================
if st.session_state.groupe_actif is None or st.session_state.get("navigation_preparation") is None:
    if st.session_state.groupe_actif != "corbeille":
        st.markdown(
            """
            <div style="
                min-height: 70vh;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                text-align: center;
                padding: 40px;
            ">
                <h1 style="color: #142235; font-family: Georgia, serif; font-size: 36px; margin-bottom: 12px;">
                    Portail Industriel Béraudy & Vaure
                </h1>
                <p style="color: #64748B; font-size: 16px; max-width: 550px; line-height: 1.6;">
                    Veuillez sélectionner une section dans le menu latéral à gauche pour afficher son contenu.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.stop()


G_ACTIF = st.session_state.groupe_actif

# =============================================================================
# MODULE 1 — PRÉPARATION DES MÉLANGES
# =============================================================================

if G_ACTIF == "preparation_melanges":
    choix_section = st.session_state.get("navigation_preparation")
    if choix_section is None:
        st.stop()
    
    st.session_state.sub_section_melange = choix_section
    st.markdown(f"## {choix_section}")

    preparation = st.session_state.processus_db["preparation_melanges"]
    fiches_m = preparation.setdefault("fiches_methode", [])
    liste_couleurs = preparation.setdefault("couleurs", [])
    liste_additifs = preparation.setdefault("additifs", [])
    liste_melanges = preparation.setdefault("melanges", [])
    
    if choix_section is None:
        st.session_state.groupe_actif = None
        st.rerun()
    
    
    # ========================================================================
    # OUTILS VISUELS ET FONCTIONNELS COMMUNS AUX SECTIONS DE PRÉPARATION
    # À conserver juste avant le premier :
    # if choix_section == "🎨 Nuancier de couleurs":
    # ========================================================================

    import copy
    import hashlib
    import html as html_lib
    import math


    def pro_texte(valeur):
        return str(valeur or "").strip()


    def pro_naturel(valeur):
        return [
            int(partie) if partie.isdigit() else partie.lower()
            for partie in re.split(r"(\d+)", pro_texte(valeur))
        ]


    def pro_date_maintenant():
        return datetime.datetime.now().strftime("%d/%m/%Y - %H:%M")


    def pro_couleur_valide(valeur, defaut="#D8DEE4"):
        valeur = pro_texte(valeur)
        if re.fullmatch(r"#[0-9a-fA-F]{6}", valeur):
            return valeur.upper()
        return defaut


    def pro_identifiant_unique(prefixe, donnees, cle):
        numero = 1
        valeurs = {pro_texte(item.get(cle)).lower() for item in donnees}
        candidat = prefixe
        while candidat.lower() in valeurs:
            numero += 1
            candidat = f"{prefixe}-{numero}"
        return candidat


    def pro_entete_section(surtitre, titre, description, statistiques, badge="BASE B&V"):
        cartes = "".join(
            f'<div style="min-width:110px;padding:8px 12px;background:rgba(255,254,251,.08);border:1px solid rgba(217,191,145,.20);border-radius:8px;">'
            f'<div style="color:#D9BF91;font-size:9.5px;font-weight:800;text-transform:uppercase;">{html_lib.escape(str(libelle))}</div>'
            f'<div style="color:#FFFEFB;font-family:Georgia,serif;font-size:20px;margin-top:2px;">{html_lib.escape(str(valeur))}</div>'
            f'</div>'
            for libelle, valeur in statistiques
        )
        
        html_code = (
            f'<div style="margin:2px 0 16px 0;padding:16px 18px;color:#FFFEFB;background:linear-gradient(135deg,rgba(20,34,53,.98),rgba(32,52,77,.94));border:1px solid rgba(200,165,107,.36);border-radius:12px;">'
            f'<div style="display:flex;align-items:flex-start;justify-content:space-between;gap:16px;flex-wrap:wrap;">'
            f'<div style="flex:1;min-width:260px;">'
            f'<div style="color:#D9BF91;font-size:10px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;">{html_lib.escape(surtitre)}</div>'
            f'<div style="font-family:Georgia,serif;font-size:26px;line-height:1.15;margin-top:4px;">{html_lib.escape(titre)}</div>'
            f'<div style="max-width:760px;color:rgba(255,254,251,.68);font-size:12.5px;margin-top:5px;">{html_lib.escape(description)}</div>'
            f'</div>'
            f'<div style="color:#142235;background:#D9BF91;padding:6px 10px;border-radius:999px;font-size:10px;font-weight:800;">{html_lib.escape(badge)}</div>'
            f'</div>'
            f'<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:12px;">{cartes}</div>'
            f'</div>'
        )
        st.markdown(html_code, unsafe_allow_html=True)

    def pro_barre_resultats(nombre, total, libelle="résultats"):
        html_code = (
            f'<div style="min-height:42px;display:flex;align-items:center;justify-content:space-between;gap:12px;padding:8px 12px;margin:8px 0 10px 0;color:#344A63;background:rgba(255,254,251,.78);border:1px solid rgba(20,34,53,.13);border-radius:9px;font-size:12px;font-weight:700;">'
            f'<span>{nombre} {html_lib.escape(libelle)}</span>'
            f'<span style="color:#6D7F91;">Total enregistré : {total}</span>'
            f'</div>'
        )
        st.markdown(html_code, unsafe_allow_html=True)

    def pro_paginer(liste, prefixe, taille_defaut=25):
        if not liste:
            return [], 1, 1

        col_taille, col_page = st.columns([1, 1])
        tailles = [10, 25, 50, 100, 200]
        index_taille = tailles.index(taille_defaut) if taille_defaut in tailles else 1

        with col_taille:
            taille = st.selectbox(
                "Lignes par page",
                tailles,
                index=index_taille,
                key=f"{prefixe}_taille_page",
            )

        nombre_pages = max(1, math.ceil(len(liste) / taille))
        cle_page = f"{prefixe}_numero_page"
        ancienne_page = int(st.session_state.get(cle_page, 1))
        ancienne_page = min(max(1, ancienne_page), nombre_pages)
        st.session_state[cle_page] = ancienne_page

        with col_page:
            page = st.number_input(
                "Page",
                min_value=1,
                max_value=nombre_pages,
                step=1,
                key=cle_page,
            )

        debut = (int(page) - 1) * taille
        fin = debut + taille
        return liste[debut:fin], int(page), nombre_pages


    def pro_export_json(donnees, nom_fichier, key):
        contenu = json.dumps(donnees, ensure_ascii=False, indent=2).encode("utf-8")
        st.download_button(
            "⬇️ Sauvegarde JSON",
            data=contenu,
            file_name=nom_fichier,
            mime="application/json",
            use_container_width=True,
            key=key,
        )


    def pro_audit_donnees(donnees, champs_obligatoires, cle_unique=None):
        manquants = []
        doublons = []
        valeurs_vues = {}

        for index_item, item in enumerate(donnees):
            champs_vides = [
                libelle
                for cle, libelle in champs_obligatoires
                if not pro_texte(item.get(cle))
            ]
            if champs_vides:
                manquants.append((index_item, champs_vides))

            if cle_unique:
                valeur = pro_texte(item.get(cle_unique)).lower()
                if valeur:
                    if valeur in valeurs_vues:
                        doublons.append((valeurs_vues[valeur], index_item, valeur))
                    else:
                        valeurs_vues[valeur] = index_item

        return manquants, doublons


    def pro_afficher_audit(donnees, champs_obligatoires, cle_unique, prefixe):
        manquants, doublons = pro_audit_donnees(
            donnees,
            champs_obligatoires,
            cle_unique,
        )
        with st.expander("🛡️ Contrôle qualité des données", expanded=False):
            if not manquants and not doublons:
                st.success("Aucune anomalie structurelle détectée.")
            if manquants:
                st.warning(f"{len(manquants)} fiche(s) comportent des champs essentiels vides.")
                for index_item, champs in manquants[:25]:
                    st.caption(f"Ligne {index_item + 1} : {', '.join(champs)}")
            if doublons:
                st.error(f"{len(doublons)} doublon(s) potentiel(s) détecté(s).")
                for premier, second, valeur in doublons[:25]:
                    st.caption(
                        f"Valeur « {valeur} » présente aux lignes {premier + 1} et {second + 1}."
                    )


    def pro_total_dosages(composants):
        totaux = {}
        for composant in composants:
            dosage = pro_texte(composant.get("dosage")).replace(",", ".")
            resultat = re.fullmatch(r"\s*([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z%]+)\s*", dosage)
            if resultat:
                valeur = float(resultat.group(1))
                unite = resultat.group(2).lower()
                totaux[unite] = totaux.get(unite, 0.0) + valeur
        return totaux


    # ========================================================================
    # SECTION 1 — NUANCIER DE COULEURS
    # ========================================================================

    if choix_section == "🎨 Nuancier de couleurs":
        nombre_couleurs_ft = sum(1 for item in liste_couleurs if item.get("has_ft"))
        nombre_couleurs_verifiees = sum(
            1 for item in liste_couleurs if item.get("statut") == "Vérifier"
        )
        nombre_couleurs_ral = sum(1 for item in liste_couleurs if pro_texte(item.get("ral")))

        pro_entete_section(
            "Référentiel chromatique",
            "Nuancier de couleurs",
            "Centralisez les références, appellations, clients, codes RAL et fiches techniques de vos teintes industrielles.",
            [
                ("Couleurs", len(liste_couleurs)),
                ("Avec FT", nombre_couleurs_ft),
                ("Vérifiées", nombre_couleurs_verifiees),
                ("Avec RAL", nombre_couleurs_ral),
            ],
            "NUANCIER INDUSTRIEL",
        )


        @st.dialog("Ajouter une nouvelle couleur", width="large")
        def ouvrir_ajout_couleur():
            st.markdown("### Nouvelle référence couleur")
            st.caption("Les informations sont enregistrées dans le nuancier B&V existant.")

            onglet_identite, onglet_visuel, onglet_ft = st.tabs(
                ["Identité", "Nuance et statut", "Fiche Technique"]
            )

            with onglet_identite:
                col_identite_1, col_identite_2 = st.columns(2)
                with col_identite_1:
                    c_ref = st.text_input(
                        "Référence (code unique) *",
                        key="pro_add_color_ref",
                    )
                    c_actuel = st.text_input(
                        "Nom actuel",
                        key="pro_add_color_name",
                    )
                    c_futur = st.text_input(
                        "Futur nom",
                        key="pro_add_color_future",
                    )
                with col_identite_2:
                    c_societe = st.text_input(
                        "Société / Client",
                        key="pro_add_color_company",
                    )
                    c_type = st.selectbox(
                        "Type de couleur",
                        ["Opaque", "Translucide", "2"],
                        key="pro_add_color_type",
                    )
                    commentaire_court = st.text_input(
                        "Commentaire court",
                        key="pro_add_color_comment",
                    )

            with onglet_visuel:
                col_visuel_1, col_visuel_2 = st.columns(2)
                with col_visuel_1:
                    c_ral = st.text_input(
                        "Code RAL",
                        value=st.session_state.get("add_ral", ""),
                        placeholder="Exemple : 5015",
                        key="pro_add_color_ral",
                    )
                    c_statut = "Pas vérifié"
                with col_visuel_2:
                    numero_ral = "".join(filter(str.isdigit, c_ral))
                    couleur_ral = RAL_DICT.get(numero_ral)
                    valeur_initiale = couleur_ral or st.session_state.get(
                        "add_hex",
                        "#3B82F6",
                    )
                    c_hex = st.color_picker(
                        "Nuance personnalisée",
                        pro_couleur_valide(valeur_initiale, "#3B82F6"),
                        key="pro_add_color_hex",
                    )
                    if couleur_ral:
                        st.success(f"RAL {numero_ral} reconnu : {couleur_ral}")
                    elif c_ral:
                        st.warning("Code RAL absent du référentiel. La nuance manuelle sera utilisée.")

            with onglet_ft:
                activer_ft = st.toggle(
                    "Créer la Fiche Technique (FT)",
                    value=False,
                    key="pro_add_color_has_ft",
                )
                valeurs_dynamiques = {}
                commentaire_global = ""
                conditions = ""
                redacteur = OPTIONS_REDACTEURS[0]

                # Dans la partie Fiche Technique de ouvrir_ajout_couleur() :
                if activer_ft:
                    valeurs_dynamiques = render_dynamic_ft_inputs({}, "add_couleur")
                    conditions = st.text_area(
                        "Conditions d'application",
                        key="pro_add_color_conditions",
                    )
                    commentaire_global = st.text_area(
                        "Commentaires généraux (FT)",
                        key="pro_add_color_global_comment",
                    )
                    redacteur = st.selectbox(
                        "Rédacteur / Modifié par",
                        OPTIONS_REDACTEURS,
                        key="pro_add_color_writer",
                    )

            if st.button(
                "Enregistrer la couleur",
                type="primary",
                use_container_width=True,
                key="pro_add_color_save",
            ):
                reference = c_ref.strip()
                if not reference:
                    st.error("La référence est obligatoire.")
                    return

                if any(pro_texte(item.get("ref")).lower() == reference.lower() for item in liste_couleurs):
                    st.error("Cette référence existe déjà dans le nuancier.")
                    return

                numero_ral = "".join(filter(str.isdigit, c_ral))
                couleur_finale = RAL_DICT.get(numero_ral, c_hex) if numero_ral else c_hex
                date_creation = pro_date_maintenant()
                if activer_ft:
                    specs_dynamiques = extraire_specs_du_state("add_couleur")
                else:
                    specs_dynamiques = {}
                liste_couleurs.append(
                    {
                        "ref": reference,
                        "nom_actuel": c_actuel.strip(),
                        "nom_futur": c_futur.strip(),
                        "ral": c_ral.strip(),
                        "societe": c_societe.strip(),
                        "type": c_type,
                        "visuel": couleur_finale,
                        "statut": c_statut,
                        "commentaire": commentaire_court.strip(),
                        "commentaire_global": commentaire_global.strip(),
                        "has_ft": activer_ft,
                        "fiche_technique": {
                            "specs_dynamiques": specs_dynamiques,
                            "date_creation": date_creation,
                            "date_derniere_maj": date_creation,
                            "date_avant_derniere_maj": "-",
                            "redacteur": redacteur,
                        },
                    }
                )
                st.session_state.pop("add_ral", None)
                st.session_state.pop("add_hex", None)
                sauvegarder_donnees()
                afficher_animation_validation("Couleur ajoutée")
                st.session_state.pop("dialog_actif", None)
                st.rerun()


        @st.dialog("Modifier une couleur", width="large")
        def ouvrir_modif_couleur(index, couleur_data):
            st.markdown(f"### {couleur_data.get('nom_actuel') or couleur_data.get('ref')}")

            onglet_identite, onglet_visuel, onglet_ft = st.tabs(
                ["Identité", "Nuance et statut", "Fiche Technique"]
            )

            with onglet_identite:
                col_identite_1, col_identite_2 = st.columns(2)
                with col_identite_1:
                    m_ref = st.text_input(
                        "Référence *",
                        value=couleur_data.get("ref", ""),
                        key=f"pro_edit_color_ref_{index}",
                    )
                    m_actuel = st.text_input(
                        "Nom actuel",
                        value=couleur_data.get("nom_actuel", ""),
                        key=f"pro_edit_color_name_{index}",
                    )
                    m_futur = st.text_input(
                        "Futur nom",
                        value=couleur_data.get("nom_futur", ""),
                        key=f"pro_edit_color_future_{index}",
                    )
                with col_identite_2:
                    m_societe = st.text_input(
                        "Société / Client",
                        value=couleur_data.get("societe", ""),
                        key=f"pro_edit_color_company_{index}",
                    )
                    types = ["Opaque", "Translucide", "2"]
                    type_actuel = couleur_data.get("type", "Opaque")
                    if type_actuel not in types:
                        types.append(type_actuel)
                    m_type = st.selectbox(
                        "Type",
                        types,
                        index=types.index(type_actuel),
                        key=f"pro_edit_color_type_{index}",
                    )
                    m_commentaire = st.text_input(
                        "Commentaire court",
                        value=couleur_data.get("commentaire", ""),
                        key=f"pro_edit_color_comment_{index}",
                    )

            with onglet_visuel:
                col_visuel_1, col_visuel_2 = st.columns(2)
                with col_visuel_1:
                    m_ral = st.text_input(
                        "Code RAL",
                        value=couleur_data.get("ral", ""),
                        key=f"pro_edit_color_ral_{index}",
                    )
                    statuts = ["Pas vérifié", "Vérifier"]
                    statut_actuel = couleur_data.get("statut", "Pas vérifié")
                    if statut_actuel not in statuts:
                        statut_actuel = "Pas vérifié"
                    m_statut = couleur_data.get("statut", "Pas vérifié")
                with col_visuel_2:
                    numero_ral = "".join(filter(str.isdigit, m_ral))
                    couleur_ral = RAL_DICT.get(numero_ral)
                    m_hex = st.color_picker(
                        "Ajuster la nuance",
                        pro_couleur_valide(couleur_data.get("visuel"), "#3B82F6"),
                        key=f"pro_edit_color_hex_{index}",
                    )
                    if couleur_ral:
                        st.info(f"Référence officielle disponible : {couleur_ral}")

            with onglet_ft:
                ft_ancienne = couleur_data.get("fiche_technique", {})
                activer_ft = st.toggle(
                    "Gérer la Fiche Technique (FT)",
                    value=bool(couleur_data.get("has_ft", False)),
                    key=f"pro_edit_color_has_ft_{index}",
                )
                valeurs_dynamiques = ft_ancienne.get("specs_dynamiques", {})
                conditions = ft_ancienne.get("conditions", "")
                commentaire_global = couleur_data.get("commentaire_global", "")
                redacteur = ft_ancienne.get("redacteur", OPTIONS_REDACTEURS[0])
                m_cause_modification = st.text_input(
                    "Cause de la modification (optionnel)",
                    key=f"pro_edit_element_cause_dlg_{index}",
                )
                if activer_ft:
                    valeurs_dynamiques = render_dynamic_ft_inputs(
                        ft_ancienne,
                        f"pro_edit_couleur_{index}",
                    )
                    conditions = st.text_area(
                        "Conditions d'application",
                        value=conditions,
                        key=f"pro_edit_color_conditions_{index}",
                    )
                    commentaire_global = st.text_area(
                        "Commentaires généraux (FT)",
                        value=commentaire_global,
                        key=f"pro_edit_color_global_{index}",
                    )
                    m_cause_modification = st.text_input(
                        "Cause de la modification (optionnel)",
                        key=f"pro_edit_color_cause_{index}",
                    )
                    index_redacteur = (
                        OPTIONS_REDACTEURS.index(redacteur)
                        if redacteur in OPTIONS_REDACTEURS
                        else 0
                    )
                    redacteur = st.selectbox(
                        "Rédacteur / Modifié par",
                        OPTIONS_REDACTEURS,
                        index=index_redacteur,
                        key=f"pro_edit_color_writer_{index}",
                    )

            if st.button(
                "Enregistrer les modifications",
                type="primary",
                use_container_width=True,
                key=f"pro_edit_color_save_{index}",
            ):
                reference = m_ref.strip()
                if not reference:
                    st.error("La référence est obligatoire.")
                    return

                doublon = any(
                    autre_index != index
                    and pro_texte(item.get("ref")).lower() == reference.lower()
                    for autre_index, item in enumerate(liste_couleurs)
                )
                if doublon:
                    st.error("Cette référence appartient déjà à une autre couleur.")
                    return

                date_edition = pro_date_maintenant()
                date_creation, date_derniere, date_avant, causes_modifs = gerer_historique_dates_et_causes(
                    ft_ancienne,
                    date_edition,
                    cause_saisie=m_cause_modification,
                )
                numero_ral = "".join(filter(str.isdigit, m_ral))
                nuance_finale = RAL_DICT.get(numero_ral, m_hex) if numero_ral else m_hex
                if activer_ft:
                    specs_dynamiques = extraire_specs_du_state(f"pro_edit_couleur_{index}")
                else:
                    specs_dynamiques = ft_ancienne.get("specs_dynamiques", {})
                couleur_mise_a_jour = copy.deepcopy(couleur_data)
                couleur_mise_a_jour.update(
                    {
                        "ref": reference,
                        "nom_actuel": m_actuel.strip(),
                        "nom_futur": m_futur.strip(),
                        "ral": m_ral.strip(),
                        "societe": m_societe.strip(),
                        "type": m_type,
                        "visuel": nuance_finale,
                        "statut": m_statut,
                        "commentaire": m_commentaire.strip(),
                        "commentaire_global": commentaire_global.strip(),
                        "has_ft": activer_ft,
                        "fiche_technique": {
                            **copy.deepcopy(ft_ancienne),
                            "specs_dynamiques": specs_dynamiques,
                            "date_creation": date_creation,
                            "date_derniere_maj": date_derniere,
                            "date_avant_derniere_maj": date_avant,
                            "conditions": conditions.strip(),
                            "redacteur": redacteur,
                        },
                    }
                )
                liste_couleurs[index] = couleur_mise_a_jour
                sauvegarder_donnees()
                afficher_animation_validation("Couleur mise à jour")
                st.session_state.pop("dialog_actif", None)
                st.rerun()


        barre_action_1, barre_action_2, barre_action_3 = st.columns([1.2, 1, 1])
        with barre_action_1:
            if st.button(
                "＋ Ajouter une couleur",
                type="primary",
                use_container_width=True,
                key="pro_color_add_main",
            ):
                st.session_state.dialog_actif = {"type": "ajout_couleur"}
                st.rerun()
                
        with barre_action_2:
            excel_couleurs, nom_excel_couleurs, mime_excel_couleurs = generer_fichier_export(
                liste_couleurs,
                "Export_Couleurs",
            )
            if excel_couleurs:
                st.download_button(
                    "⬇️ Exporter Excel",
                    data=excel_couleurs,
                    file_name=nom_excel_couleurs,
                    mime=mime_excel_couleurs,
                    use_container_width=True,
                    key="pro_color_export_excel",
                )
        with barre_action_3:
            pro_export_json(
                liste_couleurs,
                "Sauvegarde_Couleurs_BOS2.json",
                "pro_color_export_json",
            )

        pro_afficher_audit(
            liste_couleurs,
            [("ref", "Référence"), ("nom_actuel", "Nom actuel")],
            "ref",
            "pro_color_audit",
        )

        with st.expander("Filtres et organisation du nuancier", expanded=True):
            filtre_col_1, filtre_col_2, filtre_col_3, filtre_col_4 = st.columns(4)
            with filtre_col_1:
                filtre_global_couleur = st.text_input(
                    "Recherche globale",
                    placeholder="Réf., nom, société, RAL...",
                    key="pro_color_filter_global",
                ).lower().strip()
            with filtre_col_2:
                types_disponibles = sorted(
                    {pro_texte(item.get("type")) for item in liste_couleurs if pro_texte(item.get("type"))}
                )
                filtre_type_couleur = st.multiselect(
                    "Types",
                    types_disponibles,
                    key="pro_color_filter_types",
                )
            with filtre_col_3:
                filtre_ft_couleur = st.selectbox(
                    "Fiche Technique",
                    ["Toutes", "Avec FT", "Sans FT"],
                    key="pro_color_filter_ft",
                )
            with filtre_col_4:
                filtre_statut_couleur = st.selectbox(
                    "Statut",
                    ["Tous", "Vérifier", "Pas vérifié"],
                    key="pro_color_filter_status",
                )

            tri_col_1, tri_col_2 = st.columns([2, 1])
            with tri_col_1:
                tri_couleur = st.selectbox(
                    "Trier par",
                    ["Référence", "Nom actuel", "Nom futur", "RAL", "Société", "Type"],
                    key="pro_color_sort",
                )
            with tri_col_2:
                ordre_couleur = st.selectbox(
                    "Ordre",
                    ["Croissant", "Décroissant"],
                    key="pro_color_order",
                )

        mapping_tri_couleur = {
            "Référence": "ref",
            "Nom actuel": "nom_actuel",
            "Nom futur": "nom_futur",
            "RAL": "ral",
            "Société": "societe",
            "Type": "type",
        }

        couleurs_filtrees = []
        for index_couleur, couleur_item in enumerate(liste_couleurs):
            texte_recherche = " ".join(
                pro_texte(couleur_item.get(cle))
                for cle in ["ref", "nom_actuel", "nom_futur", "ral", "societe", "type"]
            ).lower()
            if filtre_global_couleur and filtre_global_couleur not in texte_recherche:
                continue
            if filtre_type_couleur and couleur_item.get("type") not in filtre_type_couleur:
                continue
            if filtre_ft_couleur == "Avec FT" and not couleur_item.get("has_ft"):
                continue
            if filtre_ft_couleur == "Sans FT" and couleur_item.get("has_ft"):
                continue
            if filtre_statut_couleur != "Tous" and couleur_item.get("statut", "Pas vérifié") != filtre_statut_couleur:
                continue
            couleurs_filtrees.append({"index_origine": index_couleur, "data": couleur_item})

        couleurs_filtrees.sort(
            key=lambda element: pro_naturel(
                element["data"].get(mapping_tri_couleur[tri_couleur], "")
            ),
            reverse=ordre_couleur == "Décroissant",
        )

        pro_barre_resultats(len(couleurs_filtrees), len(liste_couleurs), "couleurs")
        couleurs_page, page_couleur, pages_couleur = pro_paginer(
            couleurs_filtrees,
            "pro_color_pagination",
            25,
        )
        st.caption(f"Page {page_couleur} sur {pages_couleur}")

        if not couleurs_page:
            st.info("Aucune couleur ne correspond aux filtres sélectionnés.")
        else:
            entete = st.columns([1.1, 1.5, 1.5, 1, 1.4, 1, .7, 2.35])
            for colonne, libelle in zip(
                entete,
                ["Référence", "Nom actuel", "Futur nom", "RAL", "Société", "Type", "Visuel", "Actions"],
            ):
                colonne.markdown(f"**{libelle}**")
            st.markdown("<hr style='margin:4px 0;border-width:2px;border-color:#142235;'>", unsafe_allow_html=True)

            for couleur_ligne in couleurs_page:
                index_couleur = couleur_ligne["index_origine"]
                couleur_data = couleur_ligne["data"]
                ligne = st.columns([1.1, 1.5, 1.5, 1, 1.4, 1, .7, 2.35])
                ligne[0].write(pro_texte(couleur_data.get("ref")) or "-")
                ligne[1].write(pro_texte(couleur_data.get("nom_actuel")) or "-")
                ligne[2].write(pro_texte(couleur_data.get("nom_futur")) or "-")
                ligne[3].write(pro_texte(couleur_data.get("ral")) or "-")
                ligne[4].write(pro_texte(couleur_data.get("societe")) or "-")
                ligne[5].write(pro_texte(couleur_data.get("type")) or "-")
                ligne[6].markdown(
                    f"<div style='width:28px;height:28px;margin:auto;background:{pro_couleur_valide(couleur_data.get('visuel'),'#D8DEE4')};border:2px solid #FFFEFB;border-radius:50%;box-shadow:0 0 0 1px rgba(20,34,53,.25),0 4px 9px rgba(16,26,39,.14);'></div>",
                    unsafe_allow_html=True,
                )

                action_voir, action_modifier, action_dupliquer, action_supprimer, action_ft = ligne[7].columns(
                    [1, 1, 1, 1, 1.35]
                )
                if action_voir.button("👁", key=f"pro_color_view_{index_couleur}"):
                    ouvrir_details_couleur(couleur_data)
                if action_modifier.button("✎", key=f"pro_color_edit_{index_couleur}"):
                    st.session_state.dialog_actif = {"type": "modif_couleur", "index": index_couleur}
                    st.rerun()
                if action_dupliquer.button("⧉", key=f"pro_color_copy_{index_couleur}"):
                    copie_couleur = copy.deepcopy(couleur_data)
                    copie_couleur["ref"] = pro_identifiant_unique(
                        f"{pro_texte(couleur_data.get('ref'))}-COPIE",
                        liste_couleurs,
                        "ref",
                    )
                    copie_couleur["nom_actuel"] = f"{pro_texte(couleur_data.get('nom_actuel'))} — Copie"
                    copie_couleur["statut"] = "Pas vérifié"
                    ft_copie = copie_couleur.setdefault("fiche_technique", {})
                    ft_copie["date_creation"] = pro_date_maintenant()
                    ft_copie["date_derniere_maj"] = ft_copie["date_creation"]
                    ft_copie["date_avant_derniere_maj"] = "-"
                    liste_couleurs.append(copie_couleur)
                    sauvegarder_donnees()
                    st.rerun()

                cle_suppression = f"pro_color_delete_confirm_{index_couleur}"
                if action_supprimer.button("🗑", key=f"pro_color_delete_{index_couleur}"):
                    st.session_state.pop("dialog_actif", None)  # <-- Réinitialise le dialogue actif
                    st.session_state[cle_suppression] = True
                if couleur_data.get("has_ft"):
                    if action_ft.button("FT", key=f"pro_color_ft_{index_couleur}"):
                        ouvrir_visualisation_ft_couleur(couleur_data)

                if st.session_state.get(cle_suppression, False):
                    st.warning(
                        f"Supprimer définitivement la couleur {couleur_data.get('ref', '')} ?"
                    )
                    col_oui, col_non = st.columns(2)
                    if col_oui.button("Oui, supprimer", key=f"pro_color_delete_yes_{index_couleur}"):
                        item_supprime = liste_couleurs.pop(index_couleur)
                        deplacer_vers_corbeille(
                            "Couleur", 
                            item_supprime, 
                            identifiant=f"{item_supprime.get('nom_actuel', '')} ({item_supprime.get('ref', '')})"
                        )                     
                        st.session_state[cle_suppression] = False
                        sauvegarder_donnees()
                        st.rerun()
                    if col_non.button("Annuler", key=f"pro_color_delete_no_{index_couleur}"):
                        st.session_state[cle_suppression] = False
                        st.rerun()

                st.markdown("<hr style='margin:5px 0;opacity:.16;'>", unsafe_allow_html=True)
                
            # --- Réouverture persistante des dialogs ---
        dialog_actif = st.session_state.get("dialog_actif")
        if isinstance(dialog_actif, dict):
            d_type = dialog_actif.get("type")
            if d_type == "ajout_couleur":
                ouvrir_ajout_couleur()
            elif d_type == "modif_couleur":
                idx = dialog_actif.get("index")
                if idx is not None and 0 <= idx < len(liste_couleurs):
                    ouvrir_modif_couleur(idx, liste_couleurs[idx])            
                
    # ========================================================================
    # SECTION 2 — CATALOGUE DES ÉLÉMENTS
    # ========================================================================

    elif choix_section == "🧪 Catalogue des composants":
        nombre_elements_ft = sum(1 for item in liste_additifs if item.get("has_ft"))
        nombre_elements_dangereux = sum(
            1 for item in liste_additifs if item.get("danger") == "Oui"
        )
        nombre_elements_verifies = sum(
            1 for item in liste_additifs if item.get("statut") == "Vérifier"
        )
        liste_compartiments = st.session_state.processus_db[
            "preparation_melanges"
        ].setdefault("compartiments", ["résine", "peinture"])
        liste_sous_groupes = st.session_state.processus_db[
            "preparation_melanges"
        ].setdefault("sous_groupes", ["Général"])

        pro_entete_section(
            "Matières et composants",
            "Catalogue des Composants",
            "Gérez les matières premières, additifs, fournisseurs, classifications, risques et fiches techniques.",
            [
                ("Éléments", len(liste_additifs)),
                ("Avec FT", nombre_elements_ft),
                ("Risques", nombre_elements_dangereux),
                ("Vérifiés", nombre_elements_verifies),
            ],
            "CATALOGUE MATIÈRES",
        )


        @st.dialog("Ajouter un élément", width="large")
        def ouvrir_ajout_element_complet():
            st.markdown("### Nouvelle matière / nouvel élément")
            onglet_identite, onglet_classement, onglet_ft = st.tabs(
                ["Identité", "Classement", "Fiche Technique"]
            )

            with onglet_identite:
                col_identite_1, col_identite_2 = st.columns(2)
                with col_identite_1:
                    e_nom = st.text_input(
                        "Nom du composant (clé unique) *",
                        key="pro_add_element_name",
                    )
                    e_code = st.text_input("Code", key="pro_add_element_code")
                    e_des = st.text_input(
                        "Désignation",
                        key="pro_add_element_designation",
                    )
                with col_identite_2:
                    e_comm = st.text_input(
                        "Commentaire court (formulation)",
                        key="pro_add_element_short_comment",
                    )
                    e_statut = "Pas vérifié"

            with onglet_classement:
                col_classement_1, col_classement_2 = st.columns(2)
                with col_classement_1:
                    e_compartiments = st.multiselect(
                        "Compartiments",
                        liste_compartiments,
                        key="pro_add_element_compartments",
                    )
                    nouveau_compartiment = st.text_input(
                        "Nouveau compartiment",
                        key="pro_add_element_new_compartment",
                    )
                with col_classement_2:
                    e_sous_groupe = st.selectbox(
                        "Sous-groupe",
                        liste_sous_groupes,
                        key="pro_add_element_subgroup",
                    )
                    nouveau_sous_groupe = st.text_input(
                        "Nouveau sous-groupe",
                        key="pro_add_element_new_subgroup",
                    )

            with onglet_ft:
                activer_ft = st.toggle(
                    "Créer la Fiche Technique (FT)",
                    value=False,
                    key="pro_add_element_has_ft",
                )
                e_fournisseur = ""
                e_article = ""
                e_designation_achat = ""
                e_nature = "Liquide"
                e_danger = "-"
                e_danger_texte = ""
                e_manipulation = ""
                e_commentaire_global = ""
                e_redacteur = OPTIONS_REDACTEURS[0]
                specs_dynamiques = {}

                if activer_ft:
                    col_ft_1, col_ft_2 = st.columns(2)
                    with col_ft_1:
                        e_fournisseur = st.text_input(
                            "Fournisseur",
                            key="pro_add_element_supplier",
                        )
                        e_article = st.text_input(
                            "Code Article Achat",
                            key="pro_add_element_purchase_code",
                        )
                        e_designation_achat = st.text_input(
                            "Désignation Achat",
                            key="pro_add_element_purchase_name",
                        )
                    with col_ft_2:
                        e_nature = st.selectbox(
                            "Nature",
                            ["-", "Liquide", "Poudre", "Granulé", "Gel", "Autre"],
                            index=1,
                            key="pro_add_element_nature",
                        )
                        e_danger = st.radio(
                            "Risque / Danger ?",
                            ["-", "Non", "Oui"],
                            horizontal=True,
                            key="pro_add_element_danger",
                        )
                        if e_danger == "Oui":
                            e_danger_texte = st.text_area(
                                "Préciser le risque / danger",
                                key="pro_add_element_danger_text",
                            )

                    specs_dynamiques = render_dynamic_ft_inputs({}, "pro_add_element")
                    e_manipulation = st.text_area(
                        "Conseils de manipulation",
                        key="pro_add_element_handling",
                    )
                    e_commentaire_global = st.text_area(
                        "Commentaires généraux (FT)",
                        key="pro_add_element_global_comment",
                    )
                    e_redacteur = st.selectbox(
                        "Rédacteur / Modifié par",
                        OPTIONS_REDACTEURS,
                        key="pro_add_element_writer",
                    )

            if st.button(
                "Enregistrer l'élément",
                type="primary",
                use_container_width=True,
                key="pro_add_element_save",
            ):
                nom_element = e_nom.strip()
                if not nom_element:
                    st.error("Le nom du composant est obligatoire.")
                    return
                if any(
                    pro_texte(item.get("nom")).lower() == nom_element.lower()
                    for item in liste_additifs
                ):
                    st.error("Un élément portant ce nom existe déjà.")
                    return

                compartiments_finaux = list(e_compartiments)
                nouveau_compartiment = nouveau_compartiment.strip()
                if nouveau_compartiment:
                    if nouveau_compartiment not in liste_compartiments:
                        liste_compartiments.append(nouveau_compartiment)
                    if nouveau_compartiment not in compartiments_finaux:
                        compartiments_finaux.append(nouveau_compartiment)

                nouveau_sous_groupe = nouveau_sous_groupe.strip()
                if nouveau_sous_groupe:
                    if nouveau_sous_groupe not in liste_sous_groupes:
                        liste_sous_groupes.append(nouveau_sous_groupe)
                    sous_groupe_final = nouveau_sous_groupe
                else:
                    sous_groupe_final = e_sous_groupe
                    
                if activer_ft:
                    specs_dynamiques = extraire_specs_du_state("pro_add_element")
                else:
                    specs_dynamiques = {}
                    
                date_creation = pro_date_maintenant()
                liste_additifs.append(
                    {
                        "nom": nom_element,
                        "code": e_code.strip(),
                        "designation": e_des.strip(),
                        "statut": e_statut,
                        "compartiments": compartiments_finaux,
                        "sous_groupe": sous_groupe_final,
                        "fournisseur": e_fournisseur.strip(),
                        "code_article": e_article.strip(),
                        "designation_achat": e_designation_achat.strip(),
                        "nature": e_nature,
                        "danger": e_danger,
                        "danger_texte": e_danger_texte.strip() if e_danger == "Oui" else "",
                        "manipulation": e_manipulation.strip(),
                        "commentaire": e_comm.strip(),
                        "commentaire_global": e_commentaire_global.strip(),
                        "has_ft": activer_ft,
                        "fiche_technique": {
                            "specs_dynamiques": specs_dynamiques,
                            "date_creation": date_creation,
                            "date_derniere_maj": date_creation,
                            "date_avant_derniere_maj": "-",
                            "redacteur": e_redacteur,
                        },
                    }
                )
                sauvegarder_donnees()
                afficher_animation_validation("Élément ajouté")
                st.session_state.pop("dialog_actif", None)              
                st.rerun()


        @st.dialog("Modifier un élément", width="large")
        def ouvrir_modif_element_complet(index, data):
            st.markdown(f"### {data.get('nom', 'Élément')}")
            onglet_identite, onglet_classement, onglet_ft = st.tabs(
                ["Identité", "Classement", "Fiche Technique"]
            )
            with onglet_identite:
                col_identite_1, col_identite_2 = st.columns(2)
                with col_identite_1:
                    m_nom = st.text_input(
                        "Nom du composant ",
                        value=data.get("nom", ""),
                        key=f"pro_edit_element_name_{index}",
                    )
                    m_code = st.text_input(
                        "Code",
                        value=data.get("code", ""),
                        key=f"pro_edit_element_code_{index}",
                    )
                    m_designation = st.text_input(
                        "Désignation",
                        value=data.get("designation", ""),
                        key=f"pro_edit_element_designation_{index}",
                    )
                with col_identite_2:
                    m_commentaire = st.text_input(
                        "Commentaire court (formulation)",
                        value=data.get("commentaire", ""),
                        key=f"pro_edit_element_short_comment_{index}",
                    )
                    statuts = ["Pas vérifié", "Vérifier"]
                    statut_actuel = data.get("statut", "Pas vérifié")
                    if statut_actuel not in statuts:
                        statut_actuel = "Pas vérifié"
                    m_statut = data.get("statut", "Pas vérifié")

            with onglet_classement:
                compartiments_actuels = [
                    valeur
                    for valeur in data.get("compartiments", [])
                    if valeur in liste_compartiments
                ]
                sous_groupe_actuel = data.get("sous_groupe", "Général")
                if sous_groupe_actuel not in liste_sous_groupes:
                    liste_sous_groupes.append(sous_groupe_actuel)

                col_classement_1, col_classement_2 = st.columns(2)
                with col_classement_1:
                    m_compartiments = st.multiselect(
                        "Compartiments",
                        liste_compartiments,
                        default=compartiments_actuels,
                        key=f"pro_edit_element_compartments_{index}",
                    )
                    nouveau_compartiment = st.text_input(
                        "Nouveau compartiment",
                        key=f"pro_edit_element_new_compartment_{index}",
                    )
                with col_classement_2:
                    m_sous_groupe = st.selectbox(
                        "Sous-groupe",
                        liste_sous_groupes,
                        index=liste_sous_groupes.index(sous_groupe_actuel),
                        key=f"pro_edit_element_subgroup_{index}",
                    )
                    nouveau_sous_groupe = st.text_input(
                        "Nouveau sous-groupe",
                        key=f"pro_edit_element_new_subgroup_{index}",
                    )

            with onglet_ft:
                fiche_ancienne = data.get("fiche_technique", {})
                activer_ft = st.toggle(
                    "Gérer la Fiche Technique (FT)",
                    value=bool(data.get("has_ft", False)),
                    key=f"pro_edit_element_has_ft_{index}",
                )
                m_fournisseur = data.get("fournisseur", "")
                m_article = data.get("code_article", "")
                m_designation_achat = data.get("designation_achat", "")
                m_nature = data.get("nature", "Liquide")
                m_danger = data.get("danger", "-")
                m_danger_texte = data.get("danger_texte", "")
                m_manipulation = data.get("manipulation", "")
                m_commentaire_global = data.get("commentaire_global", "")
                m_redacteur = fiche_ancienne.get("redacteur", OPTIONS_REDACTEURS[0])
                specs_dynamiques = fiche_ancienne.get("specs_dynamiques", {})
                m_cause_modification = st.text_input(
                    "Cause de la modification (optionnel)",
                    key=f"pro_edit_element_cause_dlg_{index}",
                )
                if activer_ft:
                    col_ft_1, col_ft_2 = st.columns(2)
                    with col_ft_1:
                        m_fournisseur = st.text_input(
                            "Fournisseur",
                            value=m_fournisseur,
                            key=f"pro_edit_element_supplier_{index}",
                        )
                        m_article = st.text_input(
                            "Code Article Achat",
                            value=m_article,
                            key=f"pro_edit_element_purchase_code_{index}",
                        )
                        m_designation_achat = st.text_input(
                            "Désignation Achat",
                            value=m_designation_achat,
                            key=f"pro_edit_element_purchase_name_{index}",
                        )
                    with col_ft_2:
                        natures = ["-", "Liquide", "Poudre", "Granulé", "Gel", "Autre"]
                        if m_nature not in natures:
                            natures.append(m_nature)
                        m_nature = st.selectbox(
                            "Nature",
                            natures,
                            index=natures.index(m_nature),
                            key=f"pro_edit_element_nature_{index}",
                        )
                        dangers = ["-", "Non", "Oui"]
                        if m_danger not in dangers:
                            m_danger = "-"
                        m_danger = st.radio(
                            "Risque / Danger ?",
                            dangers,
                            index=dangers.index(m_danger),
                            horizontal=True,
                            key=f"pro_edit_element_danger_{index}",
                        )
                        if m_danger == "Oui":
                            m_danger_texte = st.text_area(
                                "Préciser le risque / danger",
                                value=m_danger_texte,
                                key=f"pro_edit_element_danger_text_{index}",
                            )

                    specs_dynamiques = render_dynamic_ft_inputs(
                        fiche_ancienne,
                        f"pro_edit_element_{index}",
                    )
                    m_manipulation = st.text_area(
                        "Conseils de manipulation",
                        value=m_manipulation,
                        key=f"pro_edit_element_handling_{index}",
                    )
                    m_commentaire_global = st.text_area(
                        "Commentaires généraux (FT)",
                        value=m_commentaire_global,
                        key=f"pro_edit_element_global_comment_{index}",
                    )
                    m_cause_modification = st.text_input(
                        "Cause de la modification (optionnel)",
                        key=f"pro_edit_element_cause_{index}",
                    )
                    index_redacteur = (
                        OPTIONS_REDACTEURS.index(m_redacteur)
                        if m_redacteur in OPTIONS_REDACTEURS
                        else 0
                    )
                    m_redacteur = st.selectbox(
                        "Rédacteur / Modifié par",
                        OPTIONS_REDACTEURS,
                        index=index_redacteur,
                        key=f"pro_edit_element_writer_{index}",
                    )

            if st.button(
                "Enregistrer les modifications",
                type="primary",
                use_container_width=True,
                key=f"pro_edit_element_save_{index}",
            ):
                nom_element = m_nom.strip()
                if not nom_element:
                    st.error("Le nom du composant est obligatoire.")
                    return
                if any(
                    autre_index != index
                    and pro_texte(item.get("nom")).lower() == nom_element.lower()
                    for autre_index, item in enumerate(liste_additifs)
                ):
                    st.error("Ce nom appartient déjà à un autre élément.")
                    return

                compartiments_finaux = list(m_compartiments)
                nouveau_compartiment = nouveau_compartiment.strip()
                if nouveau_compartiment:
                    if nouveau_compartiment not in liste_compartiments:
                        liste_compartiments.append(nouveau_compartiment)
                    if nouveau_compartiment not in compartiments_finaux:
                        compartiments_finaux.append(nouveau_compartiment)

                nouveau_sous_groupe = nouveau_sous_groupe.strip()
                if nouveau_sous_groupe:
                    if nouveau_sous_groupe not in liste_sous_groupes:
                        liste_sous_groupes.append(nouveau_sous_groupe)
                    sous_groupe_final = nouveau_sous_groupe
                else:
                    sous_groupe_final = m_sous_groupe

                date_creation, date_derniere, date_avant, causes_modifs = gerer_historique_dates_et_causes(
                    fiche_ancienne,
                    pro_date_maintenant(),
                    cause_saisie=m_cause_modification,
                )
                if activer_ft:
                    specs_dynamiques = extraire_specs_du_state(f"pro_edit_element_{index}")
                else:
                    specs_dynamiques = fiche_ancienne.get("specs_dynamiques", {})
                element_modifie = copy.deepcopy(data)
                element_modifie.update(
                    {
                        "nom": nom_element,
                        "code": m_code.strip(),
                        "designation": m_designation.strip(),
                        "statut": m_statut,
                        "compartiments": compartiments_finaux,
                        "sous_groupe": sous_groupe_final,
                        "fournisseur": m_fournisseur.strip(),
                        "code_article": m_article.strip(),
                        "designation_achat": m_designation_achat.strip(),
                        "nature": m_nature,
                        "danger": m_danger,
                        "danger_texte": m_danger_texte.strip() if m_danger == "Oui" else "",
                        "manipulation": m_manipulation.strip(),
                        "commentaire": m_commentaire.strip(),
                        "commentaire_global": m_commentaire_global.strip(),
                        "has_ft": activer_ft,
                        "fiche_technique": {
                            **copy.deepcopy(fiche_ancienne),
                            "specs_dynamiques": specs_dynamiques,
                            "date_creation": date_creation,
                            "date_derniere_maj": date_derniere,
                            "date_avant_derniere_maj": date_avant,
                            "causes_modification": causes_modifs,
                            "redacteur": m_redacteur,
                        },
                    }
                )
                liste_additifs[index] = element_modifie
                sauvegarder_donnees()
                afficher_animation_validation("Élément mis à jour")
                st.session_state.pop("dialog_actif", None)
                st.rerun()


        barre_element_1, barre_element_2, barre_element_3 = st.columns([1.2, 1, 1])
        with barre_element_1:
            if st.button("＋ Ajouter un composant", type="primary", use_container_width=True, key="pro_element_add_main"):
                st.session_state.dialog_actif = {"type": "ajout_element"}
                st.rerun()
        with barre_element_2:
            excel_elements, nom_excel_elements, mime_excel_elements = generer_fichier_export(
                liste_additifs,
                "Export_Elements",
            )
            if excel_elements:
                st.download_button(
                    "⬇️ Exporter Excel",
                    data=excel_elements,
                    file_name=nom_excel_elements,
                    mime=mime_excel_elements,
                    use_container_width=True,
                    key="pro_element_export_excel",
                )
        with barre_element_3:
            pro_export_json(
                liste_additifs,
                "Sauvegarde_Elements_BOS2.json",
                "pro_element_export_json",
            )

        pro_afficher_audit(
            liste_additifs,
            [("nom", "Nom"), ("code", "Code")],
            "nom",
            "pro_element_audit",
        )

        with st.expander("Filtres et organisation du catalogue", expanded=True):
            filtre_element_1, filtre_element_2, filtre_element_3, filtre_element_4 = st.columns(4)
            with filtre_element_1:
                recherche_element = st.text_input(
                    "Recherche globale",
                    placeholder="Nom, code, fournisseur...",
                    key="pro_element_filter_global",
                ).lower().strip()
            with filtre_element_2:
                compartiments_filtre = st.multiselect(
                    "Compartiments",
                    liste_compartiments,
                    key="pro_element_filter_compartments",
                )
            with filtre_element_3:
                sous_groupes_filtres = st.multiselect(
                    "Sous-groupes",
                    liste_sous_groupes,
                    key="pro_element_filter_subgroups",
                )
            with filtre_element_4:
                filtre_danger = st.selectbox(
                    "Risque",
                    ["Tous", "Oui", "Non", "Non renseigné"],
                    key="pro_element_filter_danger",
                )

            tri_element_1, tri_element_2, filtre_element_ft, filtre_element_statut = st.columns(4)
            with tri_element_1:
                tri_element = st.selectbox(
                    "Trier par",
                    ["Nom", "Code", "Fournisseur", "Sous-groupe"],
                    key="pro_element_sort",
                )
            with tri_element_2:
                ordre_element = st.selectbox(
                    "Ordre",
                    ["Croissant", "Décroissant"],
                    key="pro_element_order",
                )
            with filtre_element_ft:
                filtre_ft_element = st.selectbox(
                    "Fiche Technique",
                    ["Toutes", "Avec FT", "Sans FT"],
                    key="pro_element_filter_ft",
                )
            with filtre_element_statut:
                filtre_statut_element = st.selectbox(
                    "Statut",
                    ["Tous", "Vérifier", "Pas vérifié"],
                    key="pro_element_filter_status",
                )

        mapping_tri_element = {
            "Nom": "nom",
            "Code": "code",
            "Fournisseur": "fournisseur",
            "Sous-groupe": "sous_groupe",
        }
        elements_filtres = []
        for index_element, element_item in enumerate(liste_additifs):
            texte_recherche = " ".join(
                pro_texte(element_item.get(cle))
                for cle in ["nom", "code", "designation", "fournisseur", "sous_groupe", "commentaire"]
            ).lower()
            if recherche_element and recherche_element not in texte_recherche:
                continue
            if compartiments_filtre and not any(
                compartiment in element_item.get("compartiments", [])
                for compartiment in compartiments_filtre
            ):
                continue
            if sous_groupes_filtres and element_item.get("sous_groupe", "Général") not in sous_groupes_filtres:
                continue
            danger_item = element_item.get("danger", "-")
            if filtre_danger == "Oui" and danger_item != "Oui":
                continue
            if filtre_danger == "Non" and danger_item != "Non":
                continue
            if filtre_danger == "Non renseigné" and danger_item not in ["", "-"]:
                continue
            if filtre_ft_element == "Avec FT" and not element_item.get("has_ft"):
                continue
            if filtre_ft_element == "Sans FT" and element_item.get("has_ft"):
                continue
            if filtre_statut_element != "Tous" and element_item.get("statut", "Pas vérifié") != filtre_statut_element:
                continue
            elements_filtres.append({"index_origine": index_element, "data": element_item})

        elements_filtres.sort(
            key=lambda element: pro_naturel(
                element["data"].get(mapping_tri_element[tri_element], "")
            ),
            reverse=ordre_element == "Décroissant",
        )
        pro_barre_resultats(len(elements_filtres), len(liste_additifs), "éléments")


        def pro_afficher_tableau_elements(liste_tableau, prefixe_tableau):
            elements_page, page_element, pages_element = pro_paginer(
                liste_tableau,
                f"pro_element_page_{prefixe_tableau}",
                25,
            )
            st.caption(f"Page {page_element} sur {pages_element}")
            if not elements_page:
                st.info("Aucun élément dans cette vue.")
                return

            entete = st.columns([1.35, .9, 1.4, 1.2, 1.25, 1.25, 2.15])
            for colonne, libelle in zip(
                entete,
                ["Nom", "Code", "Désignation", "Fournisseur", "Compartiments", "Commentaire", "Actions"],
            ):
                colonne.markdown(f"**{libelle}**")
            st.markdown("<hr style='margin:4px 0;border-width:2px;border-color:#142235;'>", unsafe_allow_html=True)

            for element_ligne in elements_page:
                index_element = element_ligne["index_origine"]
                element_data = element_ligne["data"]
                ligne = st.columns([1.35, .9, 1.4, 1.2, 1.25, 1.25, 2.15])
                indicateur = "🔴 " if element_data.get("danger") == "Oui" else ""
                ligne[0].markdown(f"**{indicateur}{html_lib.escape(pro_texte(element_data.get('nom')) or '-')}**")
                ligne[1].write(pro_texte(element_data.get("code")) or "-")
                ligne[2].write(pro_texte(element_data.get("designation")) or "-")
                ligne[3].write(pro_texte(element_data.get("fournisseur")) or "-")
                ligne[4].write(", ".join(element_data.get("compartiments", [])) or "-")
                ligne[5].write(pro_texte(element_data.get("commentaire")) or "-")

                action_voir, action_modifier, action_dupliquer, action_supprimer, action_ft = ligne[6].columns(
                    [1, 1, 1, 1, 1.3]
                )
                if action_voir.button("👁", key=f"pro_element_view_{prefixe_tableau}_{index_element}"):
                    ouvrir_details_element(element_data)
                if action_modifier.button("✎", key=f"pro_element_edit_{prefixe_tableau}_{index_element}"):
                    st.session_state.dialog_actif = {"type": "modif_element", "index": index_element}
                    st.rerun()
                if action_dupliquer.button("⧉", key=f"pro_element_copy_{prefixe_tableau}_{index_element}"):
                    copie_element = copy.deepcopy(element_data)
                    copie_element["nom"] = pro_identifiant_unique(
                        f"{pro_texte(element_data.get('nom'))} — Copie",
                        liste_additifs,
                        "nom",
                    )
                    if copie_element.get("code"):
                        copie_element["code"] = pro_identifiant_unique(
                            f"{pro_texte(element_data.get('code'))}-C",
                            liste_additifs,
                            "code",
                        )
                    copie_element["statut"] = "Pas vérifié"
                    ft_copie = copie_element.setdefault("fiche_technique", {})
                    ft_copie["date_creation"] = pro_date_maintenant()
                    ft_copie["date_derniere_maj"] = ft_copie["date_creation"]
                    ft_copie["date_avant_derniere_maj"] = "-"
                    liste_additifs.append(copie_element)
                    sauvegarder_donnees()
                    st.rerun()

                cle_suppression = f"pro_element_delete_confirm_{index_element}"
                if action_supprimer.button("🗑", key=f"pro_element_delete_{prefixe_tableau}_{index_element}"):
                    st.session_state.pop("dialog_actif", None)  # <-- Réinitialise le dialogue actif
                    st.session_state[cle_suppression] = True
                if element_data.get("has_ft"):
                    if action_ft.button("FT", key=f"pro_element_ft_{prefixe_tableau}_{index_element}"):
                        ouvrir_visualisation_ft_additif(element_data)

                if st.session_state.get(cle_suppression, False):
                    st.warning(f"Supprimer définitivement {element_data.get('nom', '')} ?")
                    col_oui, col_non = st.columns(2)
                    if col_oui.button("Oui, supprimer", key=f"pro_element_delete_yes_{prefixe_tableau}_{index_element}"):
                        item_supprime = liste_additifs.pop(index_element)
                        deplacer_vers_corbeille(
                            "Élément", 
                            item_supprime, 
                            identifiant=f"{item_supprime.get('nom', '')} ({item_supprime.get('code', '-')})"
                        )
                        st.session_state[cle_suppression] = False
                        sauvegarder_donnees()
                        st.rerun()
                    if col_non.button("Annuler", key=f"pro_element_delete_no_{prefixe_tableau}_{index_element}"):
                        st.session_state[cle_suppression] = False
                        st.rerun()

                st.markdown("<hr style='margin:5px 0;opacity:.16;'>", unsafe_allow_html=True)


        noms_onglets_elements = ["Tous les composants"] + [
            f"{compartiment.capitalize()}"
            for compartiment in liste_compartiments
        ]
        onglets_elements = st.tabs(noms_onglets_elements)
        with onglets_elements[0]:
            pro_afficher_tableau_elements(elements_filtres, "tous")

        for index_compartiment, compartiment in enumerate(liste_compartiments):
            with onglets_elements[index_compartiment + 1]:
                elements_compartiment = [
                    item
                    for item in elements_filtres
                    if compartiment in item["data"].get("compartiments", [])
                ]
                sous_groupes_presents = sorted(
                    {
                        item["data"].get("sous_groupe", "Général")
                        for item in elements_compartiment
                    }
                )
                if not sous_groupes_presents:
                    st.info(f"Aucun élément classé dans « {compartiment} ».")
                for sous_groupe in sous_groupes_presents:
                    st.markdown(f"##### Sous-groupe : {sous_groupe}")
                    elements_sous_groupe = [
                        item
                        for item in elements_compartiment
                        if item["data"].get("sous_groupe", "Général") == sous_groupe
                    ]
                    prefixe = f"comp_{index_compartiment}_{re.sub(r'[^a-zA-Z0-9]+', '_', sous_groupe)}"
                    pro_afficher_tableau_elements(elements_sous_groupe, prefixe)    
                    

                    
                    
    # ========================================================================
    # SECTION 3 — RÉFÉRENTIEL DES CODES RAL
    # ========================================================================

    elif choix_section == "🔢 Référentiel des codes RAL":
        rals_personnalises = st.session_state.processus_db[
            "preparation_melanges"
        ].setdefault("base_rals", [])

        catalogue_ral_map = {
            str(code): {
                "code": str(code),
                "nom": f"Teinte RAL CLASSIC {code}",
                "visuel": valeur,
                "origine": "Officiel",
            }
            for code, valeur in RAL_DICT.items()
        }
        for ral_personnalise in rals_personnalises:
            code_personnalise = pro_texte(ral_personnalise.get("code"))
            if code_personnalise:
                catalogue_ral_map[code_personnalise] = {
                    "code": code_personnalise,
                    "nom": pro_texte(ral_personnalise.get("nom")) or f"RAL {code_personnalise}",
                    "visuel": pro_couleur_valide(ral_personnalise.get("visuel"), "#FFFFFF"),
                    "origine": "Personnalisé",
                }
        catalogue_ral = list(catalogue_ral_map.values())

        pro_entete_section(
            "Standardisation des teintes",
            "Référentiel des codes RAL",
            "Consultez le catalogue RAL, ajoutez vos nuances internes et recherchez la teinte la plus proche d'une couleur.",
            [
                ("Codes", len(catalogue_ral)),
                ("Officiels", len(RAL_DICT)),
                ("Personnalisés", len(rals_personnalises)),
                ("Série 9000", sum(1 for item in catalogue_ral if item["code"].startswith("9"))),
            ],
            "RÉFÉRENTIEL RAL",
        )


        @st.dialog("Ajouter une nuance RAL", width="large")
        def ouvrir_ajout_ral_base():
            col_ral_1, col_ral_2 = st.columns(2)
            with col_ral_1:
                r_code = st.text_input(
                    "Code RAL *",
                    placeholder="Exemple : 5015-BIS",
                    key="pro_add_ral_code",
                )
                r_nom = st.text_input(
                    "Nom de la teinte *",
                    key="pro_add_ral_name",
                )
            with col_ral_2:
                r_hex = st.color_picker(
                    "Valeur hexadécimale",
                    "#FFFFFF",
                    key="pro_add_ral_hex",
                )
                st.markdown(
                    f"<div style='height:82px;background:{r_hex};border:1px solid rgba(20,34,53,.28);border-radius:10px;'></div>",
                    unsafe_allow_html=True,
                )

            if st.button(
                "Enregistrer dans le catalogue",
                type="primary",
                use_container_width=True,
                key="pro_add_ral_save",
            ):
                code = r_code.strip()
                nom = r_nom.strip()
                if not code or not nom:
                    st.error("Le code et le nom sont obligatoires.")
                    return
                if code in catalogue_ral_map:
                    st.error("Ce code existe déjà dans le référentiel.")
                    return

                rals_personnalises.append(
                    {"code": code, "nom": nom, "visuel": r_hex}
                )
                sauvegarder_donnees()
                afficher_animation_validation("Nuance RAL ajoutée")
                st.rerun()


        @st.dialog("Modifier une nuance personnalisée", width="large")
        def pro_modifier_ral_personnalise(index_ral, ral_data):
            code_modifie = st.text_input(
                "Code RAL",
                value=ral_data.get("code", ""),
                key=f"pro_edit_ral_code_{index_ral}",
            )
            nom_modifie = st.text_input(
                "Nom",
                value=ral_data.get("nom", ""),
                key=f"pro_edit_ral_name_{index_ral}",
            )
            couleur_modifiee = st.color_picker(
                "Valeur hexadécimale",
                pro_couleur_valide(ral_data.get("visuel"), "#FFFFFF"),
                key=f"pro_edit_ral_hex_{index_ral}",
            )

            if st.button(
                "Enregistrer la nuance",
                type="primary",
                use_container_width=True,
                key=f"pro_edit_ral_save_{index_ral}",
            ):
                code = code_modifie.strip()
                nom = nom_modifie.strip()
                if not code or not nom:
                    st.error("Le code et le nom sont obligatoires.")
                    return
                doublon = any(
                    autre_index != index_ral
                    and pro_texte(item.get("code")).lower() == code.lower()
                    for autre_index, item in enumerate(rals_personnalises)
                ) or (code in RAL_DICT)
                if doublon:
                    st.error("Ce code est déjà utilisé.")
                    return

                rals_personnalises[index_ral] = {
                    **copy.deepcopy(ral_data),
                    "code": code,
                    "nom": nom,
                    "visuel": couleur_modifiee,
                }
                sauvegarder_donnees()
                st.rerun()


        barre_ral_1, barre_ral_2 = st.columns([1.2, 1])
        with barre_ral_1:
            if st.button(
                "＋ Ajouter une nuance personnalisée",
                type="primary",
                use_container_width=True,
                key="pro_ral_add_main",
            ):
                ouvrir_ajout_ral_base()
        with barre_ral_2:
            pro_export_json(
                catalogue_ral,
                "Referentiel_RAL_BOS2.json",
                "pro_ral_export_json",
            )

        with st.expander("🎯 Rechercher la couleur RAL la plus proche", expanded=False):
            col_proche_1, col_proche_2 = st.columns([1, 2])
            with col_proche_1:
                couleur_recherchee = st.color_picker(
                    "Couleur à comparer",
                    "#3B82F6",
                    key="pro_ral_nearest_color",
                )
            with col_proche_2:
                def pro_hex_rgb(couleur):
                    couleur = pro_couleur_valide(couleur, "#000000").lstrip("#")
                    return tuple(int(couleur[position:position + 2], 16) for position in (0, 2, 4))

                cible_r, cible_g, cible_b = pro_hex_rgb(couleur_recherchee)
                proximites = []
                for ral_item in catalogue_ral:
                    ral_r, ral_g, ral_b = pro_hex_rgb(ral_item["visuel"])
                    distance = math.sqrt(
                        (cible_r - ral_r) ** 2
                        + (cible_g - ral_g) ** 2
                        + (cible_b - ral_b) ** 2
                    )
                    proximites.append((distance, ral_item))
                proximites.sort(key=lambda item: item[0])

                for distance, ral_proche in proximites[:5]:
                    st.markdown(
                        f"""
                        <div style="display:flex;align-items:center;gap:10px;padding:7px 9px;margin-bottom:5px;background:rgba(255,254,251,.72);border:1px solid rgba(20,34,53,.12);border-radius:8px;">
                            <div style="width:30px;height:30px;background:{ral_proche['visuel']};border:1px solid rgba(20,34,53,.25);border-radius:6px;"></div>
                            <div style="flex:1;"><b>RAL {html_lib.escape(ral_proche['code'])}</b><br><span style="font-size:11px;color:#6D7F91;">{html_lib.escape(ral_proche['nom'])}</span></div>
                            <div style="font-size:11px;color:#6D7F91;">écart {distance:.1f}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        with st.expander("Filtres du référentiel", expanded=True):
            filtre_ral_1, filtre_ral_2, filtre_ral_3, filtre_ral_4 = st.columns(4)
            with filtre_ral_1:
                filtre_code_ral = st.text_input(
                    "Code RAL",
                    key="pro_ral_filter_code",
                ).strip().lower()
            with filtre_ral_2:
                filtre_nom_ral = st.text_input(
                    "Désignation",
                    key="pro_ral_filter_name",
                ).strip().lower()
            with filtre_ral_3:
                filtre_origine_ral = st.selectbox(
                    "Origine",
                    ["Toutes", "Officiel", "Personnalisé"],
                    key="pro_ral_filter_origin",
                )
            with filtre_ral_4:
                ordre_ral = st.selectbox(
                    "Ordre",
                    ["Croissant", "Décroissant"],
                    key="pro_ral_order",
                )

        rals_filtres = []
        for ral_item in catalogue_ral:
            if filtre_code_ral and filtre_code_ral not in ral_item["code"].lower():
                continue
            if filtre_nom_ral and filtre_nom_ral not in ral_item["nom"].lower():
                continue
            if filtre_origine_ral != "Toutes" and ral_item["origine"] != filtre_origine_ral:
                continue
            rals_filtres.append(ral_item)

        rals_filtres.sort(
            key=lambda item: pro_naturel(item["code"]),
            reverse=ordre_ral == "Décroissant",
        )
        pro_barre_resultats(len(rals_filtres), len(catalogue_ral), "codes RAL")
        rals_page, page_ral, pages_ral = pro_paginer(
            rals_filtres,
            "pro_ral_pagination",
            25,
        )
        st.caption(f"Page {page_ral} sur {pages_ral}")

        entete_ral = st.columns([1.2, 2.5, 1.2, 1.1, 2])
        for colonne, libelle in zip(
            entete_ral,
            ["Code", "Désignation", "Origine", "Visuel", "Actions"],
        ):
            colonne.markdown(f"**{libelle}**")
        st.markdown("<hr style='margin:4px 0;border-width:2px;border-color:#142235;'>", unsafe_allow_html=True)

        for ral_ligne in rals_page:
            ligne = st.columns([1.2, 2.5, 1.2, 1.1, 2])
            ligne[0].markdown(f"**RAL {ral_ligne['code']}**")
            ligne[1].write(ral_ligne["nom"])
            ligne[2].write(ral_ligne["origine"])
            ligne[3].markdown(
                f"<div style='width:52px;height:27px;background:{ral_ligne['visuel']};border:1px solid rgba(20,34,53,.30);border-radius:6px;'></div>",
                unsafe_allow_html=True,
            )

            bouton_utiliser, bouton_modifier, bouton_supprimer = ligne[4].columns([1.4, 1, 1])
            if bouton_utiliser.button(
                "Utiliser",
                key=f"pro_ral_use_{ral_ligne['code']}",
            ):
                st.session_state["add_ral"] = ral_ligne["code"]
                st.session_state["add_hex"] = ral_ligne["visuel"]
                st.toast(f"RAL {ral_ligne['code']} préparé pour le nuancier.")

            if ral_ligne["origine"] == "Personnalisé":
                index_personnalise = next(
                    (
                        index_ral
                        for index_ral, item in enumerate(rals_personnalises)
                        if pro_texte(item.get("code")) == ral_ligne["code"]
                    ),
                    None,
                )
                if index_personnalise is not None:
                    if bouton_modifier.button(
                        "✎",
                        key=f"pro_ral_edit_{ral_ligne['code']}",
                    ):
                        pro_modifier_ral_personnalise(
                            index_personnalise,
                            rals_personnalises[index_personnalise],
                        )
                    if bouton_supprimer.button(
                        "🗑",
                        key=f"pro_ral_delete_{ral_ligne['code']}",
                    ):
                        cle_confirmation_ral = f"pro_ral_confirm_{ral_ligne['code']}"
                        st.session_state[cle_confirmation_ral] = True
                    cle_confirmation_ral = f"pro_ral_confirm_{ral_ligne['code']}"
                    if st.session_state.get(cle_confirmation_ral, False):
                        st.warning(f"Supprimer la nuance RAL {ral_ligne['code']} ?")
                        col_oui, col_non = st.columns(2)
                        if col_oui.button("Oui", key=f"pro_ral_delete_yes_{ral_ligne['code']}"):
                            item_supprime = rals_personnalises.pop(index_personnalise)
                            deplacer_vers_corbeille(
                                "Code RAL", 
                                item_supprime, 
                                identifiant=f"RAL {item_supprime.get('code', '')} — {item_supprime.get('nom', '')}"
                            )
                            st.session_state[cle_confirmation_ral] = False
                            sauvegarder_donnees()
                            st.rerun()
                        if col_non.button("Non", key=f"pro_ral_delete_no_{ral_ligne['code']}"):
                            st.session_state[cle_confirmation_ral] = False
                            st.rerun()

            st.markdown("<hr style='margin:5px 0;opacity:.16;'>", unsafe_allow_html=True)

    # ========================================================================
    # SECTION 4 — FORMULATIONS D'ATELIER
    # ========================================================================

    elif choix_section == "⚗️ Formulations d'atelier":
        liste_ateliers = st.session_state.processus_db[
            "preparation_melanges"
        ].setdefault("ateliers", ["Atelier Résine", "Atelier Peinture"])        
        nombre_melanges_ft = sum(1 for item in liste_melanges if item.get("has_ft"))
        nombre_melanges_verifies = sum(
            1 for item in liste_melanges if item.get("statut") == "Vérifier"
        )
        nombre_composants_total = sum(
            len(item.get("couleurs_associees", [])) for item in liste_melanges
        )

        pro_entete_section(
            "Recettes et préparations",
            "Formulations d'atelier",
            "Créez et maintenez vos recettes de mélange, dosages, composants, emplacements et fiches techniques.",
            [
                ("Mélanges", len(liste_melanges)),
                ("Avec FT", nombre_melanges_ft),
                ("Vérifiés", nombre_melanges_verifies),
                ("Composants", nombre_composants_total),
            ],
            "FORMULATION INDUSTRIELLE",
        )


        def pro_candidats_composants(reference_melange_exclue=None):
            candidats = []
            for index_couleur_candidate, couleur in enumerate(liste_couleurs):
                candidats.append(
                    {
                        "uid": (
                            f"couleur|{index_couleur_candidate}|"
                            f"{pro_texte(couleur.get('ref')) or 'sans-reference'}"
                        ),
                        "type": "couleur",
                        "ref": pro_texte(couleur.get("ref")),
                        "nom": pro_texte(couleur.get("nom_actuel")) or pro_texte(couleur.get("ref")),
                        "visuel": pro_couleur_valide(couleur.get("visuel"), "#D8DEE4"),
                        "dosage": "100g",
                        "groupe": "Couleurs du nuancier",
                        "recherche": " ".join(
                            [
                                pro_texte(couleur.get("ref")),
                                pro_texte(couleur.get("nom_actuel")),
                                pro_texte(couleur.get("nom_futur")),
                                pro_texte(couleur.get("ral")),
                            ]
                        ).lower(),
                    }
                )

            for code_ral, valeur_ral in RAL_DICT.items():
                candidats.append(
                    {
                        "uid": f"ral_officiel|RAL {code_ral}",
                        "type": "ral_officiel",
                        "ref": f"RAL {code_ral}",
                        "nom": f"RAL {code_ral}",
                        "visuel": valeur_ral,
                        "dosage": "100g",
                        "groupe": "Codes RAL officiels",
                        "recherche": f"ral {code_ral}".lower(),
                    }
                )

            for index_melange_candidate, melange_base in enumerate(liste_melanges):
                if reference_melange_exclue and pro_texte(melange_base.get("ref")) == pro_texte(reference_melange_exclue):
                    continue
                candidats.append(
                    {
                        "uid": (
                            f"melange_base|{index_melange_candidate}|"
                            f"{pro_texte(melange_base.get('ref')) or 'sans-reference'}"
                        ),
                        "type": "melange_base",
                        "ref": pro_texte(melange_base.get("ref")),
                        "nom": pro_texte(melange_base.get("nom")) or pro_texte(melange_base.get("ref")),
                        "visuel": "#D8DEE4",
                        "dosage": "500g",
                        "groupe": "Mélanges existants",
                        "recherche": " ".join(
                            [
                                pro_texte(melange_base.get("ref")),
                                pro_texte(melange_base.get("nom")),
                                pro_texte(melange_base.get("emplacement")),
                            ]
                        ).lower(),
                    }
                )

            for index_additif_candidate, additif in enumerate(liste_additifs):
                candidats.append(
                    {
                        "uid": (
                            f"additif|{index_additif_candidate}|"
                            f"{pro_texte(additif.get('nom')) or 'sans-nom'}"
                        ),
                        "type": "additif",
                        "ref": pro_texte(additif.get("nom")),
                        "nom": pro_texte(additif.get("nom")),
                        "visuel": "#EAEDEF",
                        "dosage": "10g",
                        "groupe": "Composants",
                        "recherche": " ".join(
                            [
                                pro_texte(additif.get("nom")),
                                pro_texte(additif.get("code")),
                                pro_texte(additif.get("designation")),
                            ]
                        ).lower(),
                    }
                )
            return candidats


        def pro_cle_composant_widget(uid):
            empreinte = hashlib.sha1(str(uid).encode("utf-8")).hexdigest()[:18]
            return empreinte


        def pro_editeur_composants(cle_etat, prefixe_widgets, reference_exclue=None):
            etat_composants = st.session_state.setdefault(cle_etat, {})
            candidats = pro_candidats_composants(reference_exclue)

            # Migration des anciennes clés type|référence vers les nouvelles clés
            # qui contiennent aussi l'index source. Cela évite les collisions quand
            # plusieurs mélanges ou éléments ont une référence vide ou identique.
            uids_valides = {candidat["uid"] for candidat in candidats}
            uids_utilises = set(etat_composants.keys()) & uids_valides
            for ancien_uid, ancien_composant in list(etat_composants.items()):
                if ancien_uid in uids_valides:
                    continue
                correspondance = next(
                    (
                        candidat
                        for candidat in candidats
                        if candidat["uid"] not in uids_utilises
                        and candidat["type"] == ancien_composant.get("type")
                        and pro_texte(candidat["ref"])
                        == pro_texte(ancien_composant.get("ref"))
                    ),
                    None,
                )
                if correspondance is not None:
                    etat_composants[correspondance["uid"]] = etat_composants.pop(
                        ancien_uid
                    )
                    uids_utilises.add(correspondance["uid"])

            recherche = st.text_input(
                "Rechercher un composant",
                placeholder="Nom, référence, code RAL, additif...",
                key=f"{prefixe_widgets}_search",
            ).strip().lower()

            groupes = [
                "Couleurs du nuancier",
                "Codes RAL officiels",
                "Mélanges existants",
                "Composants",
            ]
            onglets = st.tabs(groupes)

            for index_groupe, groupe in enumerate(groupes):
                with onglets[index_groupe]:
                    candidats_groupe = [
                        candidat
                        for candidat in candidats
                        if candidat["groupe"] == groupe
                        and (not recherche or recherche in candidat["recherche"])
                    ]
                    if not recherche:
                        candidats_groupe = candidats_groupe[:10]
                    if not candidats_groupe:
                        st.info("Aucun composant trouvé dans cette catégorie.")

                    for candidat in candidats_groupe:
                        uid = candidat["uid"]
                        empreinte_uid = pro_cle_composant_widget(uid)
                        cle_case = f"{prefixe_widgets}_candidate_{empreinte_uid}"
                        coche = st.checkbox(
                            f"{candidat['nom']} ({candidat['ref']})",
                            value=uid in etat_composants,
                            key=cle_case,
                        )
                        if coche and uid not in etat_composants:
                            etat_composants[uid] = {
                                "type": candidat["type"],
                                "ref": candidat["ref"],
                                "nom": candidat["nom"],
                                "visuel": candidat["visuel"],
                                "dosage": candidat["dosage"],
                                "commentaire_composant": "",
                            }
                        elif not coche and uid in etat_composants:
                            etat_composants.pop(uid, None)

            st.markdown("##### Composants sélectionnés")
            if not etat_composants:
                st.info("Aucun composant sélectionné.")
            else:
                for index_selection, (uid, composant) in enumerate(list(etat_composants.items())):
                    with st.expander(
                        f"{composant.get('nom', 'Composant')} — {composant.get('dosage', '-')}",
                        expanded=True,
                    ):
                        col_dosage, col_note = st.columns([1, 2])
                        with col_dosage:
                            composant["dosage"] = st.text_input(
                                "Dosage",
                                value=pro_texte(composant.get("dosage")),
                                key=(
                                    f"{prefixe_widgets}_dosage_{index_selection}_"
                                    f"{pro_cle_composant_widget(uid)}"
                                ),
                            )
                        with col_note:
                            composant["commentaire_composant"] = st.text_input(
                                "Note/Commentaire",
                                value=pro_texte(composant.get("commentaire_composant")),
                                key=(
                                    f"{prefixe_widgets}_note_{index_selection}_"
                                    f"{pro_cle_composant_widget(uid)}"
                                ),
                            )
                        col_info, col_retrait = st.columns([3, 1])
                        with col_info:
                            st.caption(
                                f"Type : {composant.get('type')} • Référence : {composant.get('ref')}"
                            )
                        with col_retrait:
                            if st.button(
                                "Retirer",
                                key=(
                                    f"{prefixe_widgets}_remove_{index_selection}_"
                                    f"{pro_cle_composant_widget(uid)}"
                                ),
                            ):
                                etat_composants.pop(uid, None)
                                st.rerun()

            return etat_composants


        def pro_formulation_depuis_etat(etat_composants):
            resultat = []
            for composant in etat_composants.values():
                if not est_dosage_valide(composant.get("dosage")):
                    continue
                resultat.append(
                    {
                        "type": composant.get("type", "additif"),
                        "ref": pro_texte(composant.get("ref")),
                        "nom": pro_texte(composant.get("nom")),
                        "visuel": pro_couleur_valide(
                            composant.get("visuel"),
                            "#EAEDEF",
                        ),
                        "dosage": pro_texte(composant.get("dosage")),
                        "commentaire_composant": pro_texte(
                            composant.get("commentaire_composant")
                        ),
                    }
                )
            return resultat


        @st.dialog("Créer un mélange", width="large")
        def ouvrir_ajout_melange_complet():
            st.markdown("### Nouvelle formulation")
            onglet_general, onglet_ft, onglet_composants = st.tabs(
                ["Informations générales", "Fiche Technique", "Composants"]
            )
            with onglet_general:
                col_general_1, col_general_2 = st.columns(2)
                with col_general_1:
                    m_ref = st.text_input(
                        "Référence du mélange *",
                        key="pro_add_mix_ref",
                    )
                    m_nom = st.text_input(
                        "Nom du mélange *",
                        key="pro_add_mix_name",
                    )
                    m_categorie = st.selectbox(
                        "Catégorie",
                        ["Mélange Couleurs", "Autre Mélange"],
                        key="pro_add_mix_category",
                    )
                with col_general_2:
                    m_emplacement = st.text_input(
                        "Emplacement de stockage",
                        key="pro_add_mix_location",
                    )
                    m_commentaire = st.text_input(

                        "Commentaire court (formulation)",
                        key="pro_add_mix_comment",
                    )
                    # --- NOUVEAU : Choix des Ateliers & Création à la volée ---
                    m_ateliers = st.multiselect(
                        "Ateliers (Compartiments)",
                        liste_ateliers,
                        key="pro_add_mix_ateliers",
                    )
                    nouveau_atelier = st.text_input(
                        "Nouveau compartiment Atelier",
                        key="pro_add_mix_new_atelier",
                    )
                    # L'option 'Vérifier' s'affiche UNIQUEMENT si la catégorie choisie est 'Mélange Couleurs'
                    if m_categorie == "Mélange Couleurs":
                        m_statut = st.radio(
                            "État du mélange",
                            ["Pas vérifié", "Vérifier"],
                            horizontal=True,
                            key="pro_add_mix_status",
                        )
                    else:
                        m_statut = "Pas vérifié"
                m_image = st.file_uploader(
                    "Image du mélange (optionnel)",
                    type=["png", "jpg", "jpeg", "webp"],
                    key="pro_add_mix_image",
                )

            with onglet_ft:
                activer_ft = st.toggle(
                    "Créer la Fiche Technique (FT)",
                    value=False,
                    key="pro_add_mix_has_ft",
                )
                commentaire_global = ""
                ft_redacteur = OPTIONS_REDACTEURS[0]
                specs_dynamiques = {}

                if activer_ft:
                    # --- NOUVEAU : Spécifications physico-chimiques dynamiques ---
                    specs_dynamiques = render_dynamic_ft_inputs({}, "pro_add_mix")
                    
                    commentaire_global = st.text_area(
                        "Commentaires généraux (FT)",
                        key="pro_add_mix_global_comment",
                    )
                    ft_redacteur = st.selectbox(
                        "Rédacteur / Modifié par",
                        OPTIONS_REDACTEURS,
                        key="pro_add_mix_writer",
                    )

            with onglet_composants:
                composants_selectionnes = pro_editeur_composants(
                    "pro_add_mix_components_state",
                    "pro_add_mix_components",
                )

            if st.button(
                "Enregistrer la formulation",
                type="primary",
                use_container_width=True,
                key="pro_add_mix_save",
            ):
                reference = m_ref.strip()
                nom = m_nom.strip()
                if not reference or not nom:
                    st.error("La référence et le nom du mélange sont obligatoires.")
                    return
                if any(
                    pro_texte(item.get("ref")).lower() == reference.lower()
                    for item in liste_melanges
                ):
                    st.error("Cette référence de mélange existe déjà.")
                    return

                # --- NOUVEAU : Traitement du nouveau compartiment Atelier ---
                ateliers_finaux = list(m_ateliers)
                nouveau_atelier_clean = nouveau_atelier.strip()
                if nouveau_atelier_clean:
                    if nouveau_atelier_clean not in liste_ateliers:
                        liste_ateliers.append(nouveau_atelier_clean)
                    if nouveau_atelier_clean not in ateliers_finaux:
                        ateliers_finaux.append(nouveau_atelier_clean)

                composants_finaux = pro_formulation_depuis_etat(composants_selectionnes)
                date_creation = pro_date_maintenant()
                image_finale = encoder_fichier_local(m_image) if m_image else None

                # --- NOUVEAU : Extraction explicite des specs dynamiques ---
                specs_dynamiques = extraire_specs_du_state("pro_add_mix") if activer_ft else {}

                liste_melanges.append(
                    {
                        "ref": reference,
                        "nom": nom,
                        "categorie_choisie": m_categorie,
                        "ateliers": ateliers_finaux,  # <-- NOUVEAU : Sauvegarde des ateliers
                        "emplacement": m_emplacement.strip(),
                        "commentaire": m_commentaire.strip(),
                        "commentaire_global": commentaire_global.strip(),
                        "couleurs_associees": composants_finaux,
                        "statut": m_statut,
                        "has_ft": activer_ft,
                        "fiche_technique": {
                            "date_creation": date_creation,
                            "date_derniere_maj": date_creation,
                            "date_avant_derniere_maj": "-",
                            "redacteur": ft_redacteur,
                            "specs_dynamiques": specs_dynamiques,
                        },
                        "image_rendu": image_finale,
                    }
                )
                st.session_state["pro_add_mix_components_state"] = {}
                sauvegarder_donnees()
                afficher_animation_validation("Formulation créée")
                st.session_state.pop("dialog_actif", None)
                st.rerun()


        @st.dialog("Modifier une fiche de mélange", width="large")
        def ouvrir_modification_melange_complet(index, melange_data):
            cle_initialisation = f"pro_edit_mix_initialized_{index}"
            cle_etat_composants = f"pro_edit_mix_components_state_{index}"

            if not st.session_state.get(cle_initialisation):
                etat_initial = {}
                for index_composant_initial, composant in enumerate(
                    melange_data.get("couleurs_associees", [])
                ):
                    uid = (
                        f"{composant.get('type', 'additif')}|existant|"
                        f"{index_composant_initial}|{pro_texte(composant.get('ref'))}"
                    )
                    etat_initial[uid] = copy.deepcopy(composant)
                st.session_state[cle_etat_composants] = etat_initial
                st.session_state[cle_initialisation] = True

            st.markdown(f"### {melange_data.get('nom', 'Mélange')}")
            onglet_general, onglet_ft, onglet_composants = st.tabs(
                ["Informations générales", "Fiche Technique", "Composants"]
            )

            with onglet_general:
                col_general_1, col_general_2 = st.columns(2)
                with col_general_1:
                    m_ref = st.text_input(
                        "Référence du mélange *",
                        value=melange_data.get("ref", ""),
                        key=f"pro_edit_mix_ref_{index}",
                    )
                    m_nom = st.text_input(
                        "Nom du mélange *",
                        value=melange_data.get("nom", ""),
                        key=f"pro_edit_mix_name_{index}",
                    )
                    categories = ["Mélange Couleurs", "Autre Mélange"]
                    categorie_actuelle = melange_data.get(
                        "categorie_choisie",
                        "Mélange Couleurs",
                    )
                    if categorie_actuelle not in categories:
                        categories.append(categorie_actuelle)
                    m_categorie = st.selectbox(
                        "Catégorie",
                        categories,
                        index=categories.index(categorie_actuelle),
                        key=f"pro_edit_mix_category_{index}",
                    )
                with col_general_2:
                    m_emplacement = st.text_input(
                        "Emplacement de stockage",
                        value=melange_data.get("emplacement", ""),
                        key=f"pro_edit_mix_location_{index}",
                    )
                    m_commentaire = st.text_input(
                        "Commentaire court (formulation)",
                        value=melange_data.get("commentaire", ""),
                        key=f"pro_edit_mix_comment_{index}",
                    )
                    ateliers_actuels = [
                        valeur
                        for valeur in melange_data.get("ateliers", [])
                        if valeur in liste_ateliers
                    ]
                    m_ateliers = st.multiselect(
                        "Ateliers (Compartiments)",
                        liste_ateliers,
                        default=ateliers_actuels,
                        key=f"pro_edit_mix_ateliers_{index}",
                    )
                    nouveau_atelier = st.text_input(
                        "Nouveau compartiment Atelier",
                        key=f"pro_edit_mix_new_atelier_{index}",
                    )
                    statuts = ["Pas vérifié", "Vérifier"]
                    statut_actuel = melange_data.get("statut", "Pas vérifié")
                    if statut_actuel not in statuts:
                        statut_actuel = "Pas vérifié"
                    if m_categorie == "Mélange Couleurs":
                        statuts = ["Pas vérifié", "Vérifier"]
                        statut_actuel = melange_data.get("statut", "Pas vérifié")
                        if statut_actuel not in statuts:
                            statut_actuel = "Pas vérifié"
                        m_statut = st.radio(
                            "État du mélange",
                            statuts,
                            index=statuts.index(statut_actuel),
                            horizontal=True,
                            key=f"pro_edit_mix_status_{index}",
                        )
                    else:
                        m_statut = "Pas vérifié"

                if melange_data.get("image_rendu"):
                    st.caption("Aperçu de l'image actuelle")
                    afficher_image_base64(
                        melange_data["image_rendu"]["data"],
                        width=120,
                    )
                m_image = st.file_uploader(
                    "Remplacer l'image",
                    type=["png", "jpg", "jpeg", "webp"],
                    key=f"pro_edit_mix_image_{index}",
                )
                supprimer_image = st.checkbox(
                    "Supprimer l'image actuelle",
                    value=False,
                    key=f"pro_edit_mix_remove_image_{index}",
                )

            with onglet_ft:
                fiche_ancienne = melange_data.get("fiche_technique", {})
                # Migration auto : anciens champs vers specs_dynamiques
                if not fiche_ancienne.get("specs_dynamiques"):
                    fiche_ancienne["specs_dynamiques"] = {}
                    legacy_map = {
                        "Aspect / Finition": "aspect",
                        "Viscosité attendue": "viscosite",
                        "Densité": "densite",
                        "Temps de séchage": "sechage",
                        "Conditions d'application": "conditions",
                    }
                    for label, key in legacy_map.items():
                        val = fiche_ancienne.get(key, "")
                        if str(val).strip():
                            fiche_ancienne["specs_dynamiques"][label] = val
                
                activer_ft = st.toggle(
                    "Gérer la Fiche Technique (FT)",
                    value=bool(melange_data.get("has_ft", False)),
                    key=f"pro_edit_mix_has_ft_{index}",
                )
                specs_dynamiques = fiche_ancienne.get("specs_dynamiques", {})
                commentaire_global = melange_data.get("commentaire_global", "")
                ft_redacteur = fiche_ancienne.get("redacteur", OPTIONS_REDACTEURS[0])
                m_cause_modification = st.text_input(
                    "Cause de la modification (optionnel)",
                    placeholder="Ex : Modification de la recette originale",
                    key=f"pro_edit_mix_cause_dlg_{index}",
                )
                if activer_ft:
                    specs_dynamiques = render_dynamic_ft_inputs(
                        fiche_ancienne,
                        f"pro_edit_mix_{index}",
                    )
                    commentaire_global = st.text_area(
                        "Commentaires généraux (FT)",
                        value=commentaire_global,
                        key=f"pro_edit_mix_global_comment_{index}",
                    )
                    # --- NOUVEAU : Champ pour saisir la cause de modification ---
                    m_cause_modification = st.text_input(
                        "Cause de la modification (optionnel)",
                        key=f"pro_edit_element_cause_dlg_{index}",
                    )
                    index_redacteur = (
                        OPTIONS_REDACTEURS.index(ft_redacteur)
                        if ft_redacteur in OPTIONS_REDACTEURS
                        else 0
                    )
                    ft_redacteur = st.selectbox(
                        "Rédacteur / Modifié par",
                        OPTIONS_REDACTEURS,
                        index=index_redacteur,
                        key=f"pro_edit_mix_writer_{index}",
                    )            

            with onglet_composants:
                composants_selectionnes = pro_editeur_composants(
                    cle_etat_composants,
                    f"pro_edit_mix_components_{index}",
                    reference_exclue=melange_data.get("ref"),
                )

            if st.button(
                "Enregistrer les modifications",
                type="primary",
                use_container_width=True,
                key=f"pro_edit_mix_save_{index}",
            ):
                # Récupération EXPLICITE des specs depuis le session_state
                if activer_ft:
                    specs_dynamiques = extraire_specs_du_state(f"pro_edit_mix_{index}")
                else:
                    specs_dynamiques = fiche_ancienne.get("specs_dynamiques", {})
                reference = m_ref.strip()
                nom = m_nom.strip()
                if not reference or not nom:
                    st.error("La référence et le nom sont obligatoires.")
                    return
                if any(
                    autre_index != index
                    and pro_texte(item.get("ref")).lower() == reference.lower()
                    for autre_index, item in enumerate(liste_melanges)
                ):
                    st.error("Cette référence appartient déjà à un autre mélange.")
                    return

                composants_finaux = pro_formulation_depuis_etat(composants_selectionnes)
                date_creation, date_derniere, date_avant, causes_modifs = gerer_historique_dates_et_causes(
                    fiche_ancienne,
                    pro_date_maintenant(),
                    cause_saisie=m_cause_modification,
                )
                specs_dynamiques = {
                } if activer_ft else {}

                if supprimer_image:
                    image_finale = None
                elif m_image:
                    image_finale = encoder_fichier_local(m_image)
                else:
                    image_finale = melange_data.get("image_rendu")
                    
                # Récupération EXPLICITE des specs depuis le session_state
                if activer_ft:
                    specs_dynamiques = extraire_specs_du_state(f"pro_edit_mix_{index}")
                else:
                    specs_dynamiques = fiche_ancienne.get("specs_dynamiques", {})
                ateliers_finaux = list(m_ateliers)
                nouveau_atelier_clean = nouveau_atelier.strip()
                if nouveau_atelier_clean:
                    if nouveau_atelier_clean not in liste_ateliers:
                        liste_ateliers.append(nouveau_atelier_clean)
                    if nouveau_atelier_clean not in ateliers_finaux:
                        ateliers_finaux.append(nouveau_atelier_clean)                    
                melange_modifie = copy.deepcopy(melange_data)
                melange_modifie.update(
                    {
                        "ref": reference,
                        "nom": nom,
                        "categorie_choisie": m_categorie,
                        "emplacement": m_emplacement.strip(),
                        "commentaire": m_commentaire.strip(),
                        "commentaire_global": commentaire_global.strip(),
                        "couleurs_associees": composants_finaux,
                        "statut": m_statut,
                        "ateliers": ateliers_finaux,
                        "has_ft": activer_ft,
                        "fiche_technique": {
                            **copy.deepcopy(fiche_ancienne),
                            "date_creation": date_creation,
                            "date_derniere_maj": date_derniere,
                            "date_avant_derniere_maj": date_avant,
                            "redacteur": ft_redacteur,
                            "specs_dynamiques": specs_dynamiques,
                            "causes_modification": causes_modifs,  # <-- ESSENTIEL
                        },
                        "image_rendu": image_finale,
                    }
                )
                liste_melanges[index] = melange_modifie
                st.session_state.pop(cle_initialisation, None)
                st.session_state.pop(cle_etat_composants, None)
                sauvegarder_donnees()
                afficher_animation_validation("Mélange mis à jour")
                st.session_state.pop("dialog_actif", None)
                st.rerun()

        barre_melange_1, barre_melange_2, barre_melange_3 = st.columns([1.2, 1, 1])
        with barre_melange_1:
            if st.button(
                "＋ Créer une fiche de mélange",
                type="primary",
                use_container_width=True,
                key="pro_mix_add_main",
            ):
                st.session_state["pro_add_mix_components_state"] = {}
                st.session_state.dialog_actif = {"type": "ajout_melange"}
                st.rerun()
        with barre_melange_2:
            excel_melanges, nom_excel_melanges, mime_excel_melanges = generer_fichier_export(
                liste_melanges,
                "Export_Melanges",
            )
            if excel_melanges:
                st.download_button(
                    "⬇️ Exporter Excel",
                    data=excel_melanges,
                    file_name=nom_excel_melanges,
                    mime=mime_excel_melanges,
                    use_container_width=True,
                    key="pro_mix_export_excel",
                )
        with barre_melange_3:
            pro_export_json(
                liste_melanges,
                "Sauvegarde_Melanges_BOS2.json",
                "pro_mix_export_json",
            )

        pro_afficher_audit(
            liste_melanges,
            [("ref", "Référence"), ("nom", "Nom")],
            "ref",
            "pro_mix_audit",
        )

        with st.expander("Filtres et organisation des formulations", expanded=True):
            filtre_mix_1, filtre_mix_2, filtre_mix_3, filtre_mix_4 = st.columns(4)
            with filtre_mix_1:
                recherche_melange = st.text_input(
                    "Recherche globale",
                    placeholder="Réf., nom, emplacement, composant...",
                    key="pro_mix_filter_global",
                ).lower().strip()
            with filtre_mix_2:
                filtre_categorie_melange = st.selectbox(
                    "Catégorie",
                    ["Toutes", "Mélange Couleurs", "Autre Mélange"],
                    key="pro_mix_filter_category",
                )
            with filtre_mix_3:
                filtre_ft_melange = st.selectbox(
                    "Fiche Technique",
                    ["Toutes", "Avec FT", "Sans FT"],
                    key="pro_mix_filter_ft",
                )
            with filtre_mix_4:
                filtre_statut_melange = st.selectbox(
                    "Statut",
                    ["Tous", "Vérifier", "Pas vérifié"],
                    key="pro_mix_filter_status",
                )

            tri_mix_1, tri_mix_2, filtre_composant_mix = st.columns([1.2, 1, 2])
            with tri_mix_1:
                tri_melange = st.selectbox(
                    "Trier par",
                    ["Référence", "Nom", "Emplacement", "Nombre de composants"],
                    key="pro_mix_sort",
                )
            with tri_mix_2:
                ordre_melange = st.selectbox(
                    "Ordre",
                    ["Croissant", "Décroissant"],
                    key="pro_mix_order",
                )
            with filtre_composant_mix:
                composant_recherche = st.text_input(
                    "Contient le composant",
                    placeholder="Nom ou référence du composant...",
                    key="pro_mix_filter_component",
                ).lower().strip()

        melanges_filtres = []
        for index_melange, melange_item in enumerate(liste_melanges):
            texte_composants = " ".join(
                f"{pro_texte(comp.get('nom'))} {pro_texte(comp.get('ref'))}"
                for comp in melange_item.get("couleurs_associees", [])
            ).lower()
            texte_recherche = " ".join(
                [
                    pro_texte(melange_item.get("ref")),
                    pro_texte(melange_item.get("nom")),
                    pro_texte(melange_item.get("emplacement")),
                    pro_texte(melange_item.get("commentaire")),
                    texte_composants,
                ]
            ).lower()
            if recherche_melange and recherche_melange not in texte_recherche:
                continue
            if composant_recherche and composant_recherche not in texte_composants:
                continue
            categorie_item = melange_item.get("categorie_choisie", "Mélange Couleurs")
            if filtre_categorie_melange != "Toutes" and categorie_item != filtre_categorie_melange:
                continue
            if filtre_ft_melange == "Avec FT" and not melange_item.get("has_ft"):
                continue
            if filtre_ft_melange == "Sans FT" and melange_item.get("has_ft"):
                continue
            if filtre_statut_melange != "Tous" and melange_item.get("statut", "Pas vérifié") != filtre_statut_melange:
                continue
            melanges_filtres.append({"index_origine": index_melange, "data": melange_item})

        def pro_cle_tri_melange(element):
            melange = element["data"]
            if tri_melange == "Référence":
                return pro_naturel(melange.get("ref"))
            if tri_melange == "Nom":
                return pro_naturel(melange.get("nom"))
            if tri_melange == "Emplacement":
                return pro_naturel(melange.get("emplacement"))
            return [len(melange.get("couleurs_associees", []))]

        melanges_filtres.sort(
            key=pro_cle_tri_melange,
            reverse=ordre_melange == "Décroissant",
        )
        pro_barre_resultats(len(melanges_filtres), len(liste_melanges), "mélanges")

        melanges_couleurs = [
            item
            for item in melanges_filtres
            if item["data"].get("categorie_choisie", "Mélange Couleurs") == "Mélange Couleurs"
        ]
        autres_melanges = [
            item
            for item in melanges_filtres
            if item["data"].get("categorie_choisie", "Mélange Couleurs") != "Mélange Couleurs"
        ]


        def pro_afficher_tableau_melanges(liste_tableau, prefixe_tableau):
            melanges_page, page_melange, pages_melange = pro_paginer(
                liste_tableau,
                f"pro_mix_page_{prefixe_tableau}",
                25,
            )
            st.caption(f"Page {page_melange} sur {pages_melange}")
            if not melanges_page:
                st.info("Aucun mélange dans cette vue.")
                return

            entete = st.columns([.9, 1.25, .75, 2.8, 1.1, 1.5, 2.2])
            for colonne, libelle in zip(
                entete,
                ["Référence", "Nom", "Aperçu", "Composants", "Emplacement", "Commentaires", "Actions"],
            ):
                colonne.markdown(f"**{libelle}**")
            st.markdown("<hr style='margin:4px 0;border-width:2px;border-color:#142235;'>", unsafe_allow_html=True)

            for melange_ligne in melanges_page:
                index_melange = melange_ligne["index_origine"]
                melange_data = melange_ligne["data"]
                ligne = st.columns([.9, 1.25, .75, 2.8, 1.1, 1.5, 2.2])
                verification = "🔴 " if melange_data.get("statut") == "Vérifier" else ""
                ligne[0].markdown(
                    f"**{verification}{html_lib.escape(pro_texte(melange_data.get('ref')) or '-')}**"
                )
                ligne[1].write(pro_texte(melange_data.get("nom")) or "-")
                if melange_data.get("image_rendu"):
                    with ligne[2]:
                        afficher_image_base64(
                            melange_data["image_rendu"]["data"],
                            width=48,
                        )
                else:
                    ligne[2].caption("—")

                composants = melange_data.get("couleurs_associees", [])
                with ligne[3]:
                    for composant in composants[:8]:
                        couleur_composant = pro_couleur_valide(
                            composant.get("visuel"),
                            "#EAEDEF",
                        )
                        st.markdown(
                            f"""
                            <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;font-size:12px;">
                                <span style="width:12px;height:12px;flex:0 0 12px;background:{couleur_composant};border:1px solid rgba(20,34,53,.30);border-radius:50%;"></span>
                                <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{html_lib.escape(pro_texte(composant.get('nom')) or '-')}</span>
                                <b style="margin-left:auto;white-space:nowrap;">{html_lib.escape(pro_texte(composant.get('dosage')) or '-')}</b>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    if len(composants) > 8:
                        st.caption(f"+ {len(composants) - 8} autre(s)")
                    totaux = pro_total_dosages(composants)
                    if totaux:
                        resume = " • ".join(
                            f"{valeur:g} {unite}"
                            for unite, valeur in sorted(totaux.items())
                        )
                        st.caption(f"Total lisible : {resume}")

                ligne[4].write(pro_texte(melange_data.get("emplacement")) or "-")
                ligne[5].write(pro_texte(melange_data.get("commentaire")) or "-")

                action_voir, action_modifier, action_dupliquer, action_supprimer, action_ft = ligne[6].columns(
                    [1, 1, 1, 1, 1.3]
                )
                if action_voir.button("👁", key=f"pro_mix_view_{prefixe_tableau}_{index_melange}"):
                    ouvrir_details_melange(melange_data)
                if action_modifier.button("✎", key=f"pro_mix_edit_{prefixe_tableau}_{index_melange}"):
                    st.session_state.dialog_actif = {"type": "modif_melange", "index": index_melange}
                    st.rerun()
                if action_dupliquer.button("⧉", key=f"pro_mix_copy_{prefixe_tableau}_{index_melange}"):
                    copie_melange = copy.deepcopy(melange_data)
                    copie_melange["ref"] = pro_identifiant_unique(
                        f"{pro_texte(melange_data.get('ref'))}-COPIE",
                        liste_melanges,
                        "ref",
                    )
                    copie_melange["nom"] = f"{pro_texte(melange_data.get('nom'))} — Copie"
                    copie_melange["statut"] = "Pas vérifié"
                    ft_copie = copie_melange.setdefault("fiche_technique", {})
                    ft_copie["date_creation"] = pro_date_maintenant()
                    ft_copie["date_derniere_maj"] = ft_copie["date_creation"]
                    ft_copie["date_avant_derniere_maj"] = "-"
                    liste_melanges.append(copie_melange)
                    sauvegarder_donnees()
                    st.rerun()

                cle_suppression = f"pro_mix_delete_confirm_{index_melange}"
                if action_supprimer.button("🗑", key=f"pro_mix_delete_{prefixe_tableau}_{index_melange}"):
                    st.session_state.pop("dialog_actif", None)  # <-- Réinitialise le dialogue actif
                    st.session_state[cle_suppression] = True
                if melange_data.get("has_ft"):
                    if action_ft.button("FT", key=f"pro_mix_ft_{prefixe_tableau}_{index_melange}"):
                        ouvrir_visualisation_ft(melange_data)

                if st.session_state.get(cle_suppression, False):
                    st.warning(
                        f"Supprimer définitivement le mélange {melange_data.get('ref', '')} ?"
                    )
                    col_oui, col_non = st.columns(2)
                    if col_oui.button("Oui, supprimer", key=f"pro_mix_delete_yes_{prefixe_tableau}_{index_melange}"):
                        item_supprime = liste_melanges.pop(index_melange)
                        deplacer_vers_corbeille(
                            "Mélange", 
                            item_supprime, 
                            identifiant=f"{item_supprime.get('nom', '')} ({item_supprime.get('ref', '-')})"
                        )
                        st.session_state[cle_suppression] = False
                        sauvegarder_donnees()
                        st.rerun()
                    if col_non.button("Annuler", key=f"pro_mix_delete_no_{prefixe_tableau}_{index_melange}"):
                        st.session_state[cle_suppression] = False
                        st.rerun()

                st.markdown("<hr style='margin:5px 0;opacity:.16;'>", unsafe_allow_html=True)


        onglet_melanges_couleurs, onglet_autres_melanges = st.tabs(
            ["Mélanges Couleurs", "Autres Mélanges"]
        )
        with onglet_melanges_couleurs:
            pro_afficher_tableau_melanges(melanges_couleurs, "couleurs")
        with onglet_autres_melanges:
            # --- Module de gestion / création / suppression des compartiments Ateliers ---
            with st.expander("⚙️ Gérer / Supprimer les compartiments Atelier", expanded=False):
                c_add_at, c_btn_at = st.columns([3, 1])
                with c_add_at:
                    nouveau_nom_atelier = st.text_input("Créer un nouvel Atelier", key="input_new_atelier_mgt")
                with c_btn_at:
                    st.write("")
                    st.write("")
                    if st.button("➕ Ajouter Atelier", key="btn_add_atelier_mgt", use_container_width=True):
                        at_propre = nouveau_nom_atelier.strip()
                        if at_propre and at_propre not in liste_ateliers:
                            liste_ateliers.append(at_propre)
                            sauvegarder_donnees()
                            st.rerun()
        
                if liste_ateliers:
                    st.markdown("**Compartiments Ateliers existants :**")
                    ateliers_a_retirer = []
                    for idx_at, at_nom in enumerate(liste_ateliers):
                        col_at_nom, col_at_del = st.columns([4, 1])
                        col_at_nom.write(f"• **{at_nom}**")
                        if col_at_del.button("🗑️ Supprimer", key=f"btn_del_atelier_{idx_at}"):
                            ateliers_a_retirer.append(at_nom)
        
                    if ateliers_a_retirer:
                        for at_rem in ateliers_a_retirer:
                            liste_ateliers.remove(at_rem)
                        sauvegarder_donnees()
                        st.rerun()
        
            # --- Sous-onglets par compartiment Atelier ---
            noms_onglets_ateliers = ["Tous les Autres Mélanges"] + [
                f"Atelier : {at.capitalize()}" for at in liste_ateliers
            ]
            onglets_ateliers = st.tabs(noms_onglets_ateliers)
        
            # Onglet Général (Tous)
            with onglets_ateliers[0]:
                pro_afficher_tableau_melanges(autres_melanges, "autres_tous")
        
            # Onglets spécifiques par Atelier
            for index_at, at_nom in enumerate(liste_ateliers):
                with onglets_ateliers[index_at + 1]:
                    melanges_atelier = [
                        item
                        for item in autres_melanges
                        if at_nom in item["data"].get("ateliers", [])
                    ]
                    prefixe_at = f"autres_at_{index_at}_{re.sub(r'[^a-zA-Z0-9]+', '_', at_nom)}"
                    pro_afficher_tableau_melanges(melanges_atelier, prefixe_at)
            
            
            # --- Réouverture persistante des dialogs ---
        dialog_actif = st.session_state.get("dialog_actif")
        if isinstance(dialog_actif, dict):
            d_type = dialog_actif.get("type")
            if d_type == "ajout_melange":
                ouvrir_ajout_melange_complet()
            elif d_type == "modif_melange":
                idx = dialog_actif.get("index")
                if idx is not None and 0 <= idx < len(liste_melanges):
                    ouvrir_modification_melange_complet(idx, liste_melanges[idx])

    elif choix_section == "📐 Fiches Méthode":
        # =====================================================================
        # NOUVEL ÉDITEUR DE MIND MAP — STYLE BLANK DIAGRAM / LUCIDCHART
        # Cette section remplace uniquement l'ancienne section Fiches Méthode.
        # Toutes les données restent enregistrées dans donnees_bos2.json.
        # =====================================================================

        import copy
        import html as html_lib
        import uuid

        # ---------------------------------------------------------------------
        # OUTILS INTERNES DU NOUVEL ÉDITEUR
        # ---------------------------------------------------------------------

        def mm_maintenant():
            return datetime.datetime.now().strftime("%d/%m/%Y - %H:%M")


        def mm_id(prefixe):
            return f"{prefixe}_{uuid.uuid4().hex[:12]}"


        def mm_limite_nombre(valeur, minimum, maximum, defaut):
            try:
                valeur_float = float(valeur)
                return max(minimum, min(maximum, valeur_float))
            except (TypeError, ValueError):
                return defaut


        def mm_couleur_valide(valeur, defaut):
            valeur = str(valeur or "").strip()
            if re.fullmatch(r"#[0-9a-fA-F]{6}", valeur):
                return valeur.upper()
            return defaut


        def mm_prochain_numero_noeud(fiche):
            numeros = []
            for noeud in fiche.get("formes", []):
                texte_id = str(noeud.get("id", ""))
                morceaux = re.findall(r"\d+", texte_id)
                if morceaux:
                    numeros.append(int(morceaux[-1]))
            return max(numeros, default=0) + 1


        def mm_prochain_numero_liaison(fiche):
            numeros = []
            for liaison in fiche.get("liaisons", []):
                texte_id = str(liaison.get("id", ""))
                morceaux = re.findall(r"\d+", texte_id)
                if morceaux:
                    numeros.append(int(morceaux[-1]))
            return max(numeros, default=0) + 1


        def mm_trouver_fiche(fiche_id):
            for index_fiche, fiche_item in enumerate(fiches_m):
                if str(fiche_item.get("id")) == str(fiche_id):
                    return index_fiche, fiche_item
            return None, None


        def mm_trouver_noeud(fiche, noeud_id):
            for index_noeud, noeud in enumerate(fiche.get("formes", [])):
                if str(noeud.get("id")) == str(noeud_id):
                    return index_noeud, noeud
            return None, None


        def mm_trouver_liaison(fiche, liaison_id):
            for index_liaison, liaison in enumerate(fiche.get("liaisons", [])):
                if str(liaison.get("id")) == str(liaison_id):
                    return index_liaison, liaison
            return None, None


        def mm_marquer_modification(fiche):
            fiche["date_modification"] = mm_maintenant()


        def mm_sauvegarder(fiche=None):
            if fiche is not None:
                mm_marquer_modification(fiche)
            sauvegarder_donnees()


        def mm_cle_historique(fiche):
            return f"mm_historique_{fiche.get('id')}"


        def mm_cle_retablir(fiche):
            return f"mm_retablir_{fiche.get('id')}"


        def mm_memoriser_etat(fiche):
            cle_historique = mm_cle_historique(fiche)
            historique = st.session_state.setdefault(cle_historique, [])
            historique.append(
                {
                    "formes": copy.deepcopy(fiche.get("formes", [])),
                    "liaisons": copy.deepcopy(fiche.get("liaisons", [])),
                    "description": fiche.get("description", ""),
                    "orientation": fiche.get("orientation", "horizontal"),
                }
            )
            if len(historique) > 40:
                del historique[:-40]
            st.session_state[mm_cle_retablir(fiche)] = []


        def mm_annuler(fiche):
            historique = st.session_state.setdefault(mm_cle_historique(fiche), [])
            if not historique:
                return False

            etat_courant = {
                "formes": copy.deepcopy(fiche.get("formes", [])),
                "liaisons": copy.deepcopy(fiche.get("liaisons", [])),
                "description": fiche.get("description", ""),
                "orientation": fiche.get("orientation", "horizontal"),
            }
            st.session_state.setdefault(mm_cle_retablir(fiche), []).append(etat_courant)

            ancien_etat = historique.pop()
            fiche["formes"] = ancien_etat["formes"]
            fiche["liaisons"] = ancien_etat["liaisons"]
            fiche["description"] = ancien_etat["description"]
            fiche["orientation"] = ancien_etat["orientation"]
            mm_sauvegarder(fiche)
            return True


        def mm_retablir(fiche):
            pile_retablir = st.session_state.setdefault(mm_cle_retablir(fiche), [])
            if not pile_retablir:
                return False

            etat_courant = {
                "formes": copy.deepcopy(fiche.get("formes", [])),
                "liaisons": copy.deepcopy(fiche.get("liaisons", [])),
                "description": fiche.get("description", ""),
                "orientation": fiche.get("orientation", "horizontal"),
            }
            st.session_state.setdefault(mm_cle_historique(fiche), []).append(etat_courant)

            etat_suivant = pile_retablir.pop()
            fiche["formes"] = etat_suivant["formes"]
            fiche["liaisons"] = etat_suivant["liaisons"]
            fiche["description"] = etat_suivant["description"]
            fiche["orientation"] = etat_suivant["orientation"]
            mm_sauvegarder(fiche)
            return True


        def mm_nouveau_noeud(
            fiche,
            titre="Nouvelle idée",
            sous_titre="",
            forme="rounded",
            categorie="idee",
            couleur="#F4EBDD",
            bordure="#9B7740",
            texte="#142235",
            x=480,
            y=320,
            largeur=190,
            hauteur=78,
        ):
            numero = mm_prochain_numero_noeud(fiche)
            return {
                "id": f"n{numero}",
                "label": str(titre or "Nouvelle idée").strip(),
                "subtitle": str(sous_titre or "").strip(),
                "notes": "",
                "shape": forme,
                "categorie": categorie,
                "color": mm_couleur_valide(couleur, "#F4EBDD"),
                "border_color": mm_couleur_valide(bordure, "#9B7740"),
                "text_color": mm_couleur_valide(texte, "#142235"),
                "x": round(float(x), 2),
                "y": round(float(y), 2),
                "width": int(mm_limite_nombre(largeur, 110, 420, 190)),
                "height": int(mm_limite_nombre(hauteur, 54, 220, 78)),
                "locked": False,
            }


        def mm_nouvelle_liaison(
            fiche,
            source,
            destination,
            libelle="",
            couleur="#50657D",
            style="solid",
            fleche="to",
        ):
            numero = mm_prochain_numero_liaison(fiche)
            return {
                "id": f"e{numero}",
                "from": str(source),
                "to": str(destination),
                "label": str(libelle or "").strip(),
                "color": mm_couleur_valide(couleur, "#50657D"),
                "style": style,
                "arrow": fleche,
                "width": 2,
            }


        def mm_supprimer_noeud(fiche, noeud_id):
            fiche["formes"] = [
                noeud
                for noeud in fiche.get("formes", [])
                if str(noeud.get("id")) != str(noeud_id)
            ]
            fiche["liaisons"] = [
                liaison
                for liaison in fiche.get("liaisons", [])
                if str(liaison.get("from")) != str(noeud_id)
                and str(liaison.get("to")) != str(noeud_id)
            ]


        def mm_disposition_automatique(fiche, mode):
            noeuds = fiche.get("formes", [])
            liaisons = fiche.get("liaisons", [])

            if not noeuds:
                return

            ids_noeuds = [str(noeud.get("id")) for noeud in noeuds]
            noeuds_par_id = {str(noeud.get("id")): noeud for noeud in noeuds}
            enfants = {noeud_id: [] for noeud_id in ids_noeuds}
            parents = {noeud_id: [] for noeud_id in ids_noeuds}

            for liaison in liaisons:
                source = str(liaison.get("from"))
                destination = str(liaison.get("to"))
                if source in enfants and destination in enfants:
                    enfants[source].append(destination)
                    parents[destination].append(source)

            racines = [noeud_id for noeud_id in ids_noeuds if not parents[noeud_id]]
            racine = racines[0] if racines else ids_noeuds[0]

            niveaux = {racine: 0}
            file_attente = [racine]

            while file_attente:
                courant = file_attente.pop(0)
                for enfant in enfants.get(courant, []):
                    if enfant not in niveaux:
                        niveaux[enfant] = niveaux[courant] + 1
                        file_attente.append(enfant)

            niveau_maximum = max(niveaux.values(), default=0)
            for noeud_id in ids_noeuds:
                if noeud_id not in niveaux:
                    niveau_maximum += 1
                    niveaux[noeud_id] = niveau_maximum

            groupes = {}
            for noeud_id, niveau in niveaux.items():
                groupes.setdefault(niveau, []).append(noeud_id)

            if mode == "horizontal":
                for niveau, ids_niveau in groupes.items():
                    hauteur_totale = max(1, len(ids_niveau) - 1) * 135
                    debut_y = 430 - hauteur_totale / 2
                    for position, noeud_id in enumerate(ids_niveau):
                        noeuds_par_id[noeud_id]["x"] = 280 + niveau * 285
                        noeuds_par_id[noeud_id]["y"] = debut_y + position * 135

            elif mode == "vertical":
                for niveau, ids_niveau in groupes.items():
                    largeur_totale = max(1, len(ids_niveau) - 1) * 245
                    debut_x = 720 - largeur_totale / 2
                    for position, noeud_id in enumerate(ids_niveau):
                        noeuds_par_id[noeud_id]["x"] = debut_x + position * 245
                        noeuds_par_id[noeud_id]["y"] = 180 + niveau * 155

            elif mode == "radial":
                noeuds_par_id[racine]["x"] = 720
                noeuds_par_id[racine]["y"] = 430

                for niveau, ids_niveau in groupes.items():
                    if niveau == 0:
                        continue
                    rayon = 180 + (niveau - 1) * 175
                    nombre = max(1, len(ids_niveau))
                    for position, noeud_id in enumerate(ids_niveau):
                        angle = (2 * 3.141592653589793 * position / nombre) - 1.5708
                        noeuds_par_id[noeud_id]["x"] = 720 + rayon * __import__("math").cos(angle)
                        noeuds_par_id[noeud_id]["y"] = 430 + rayon * __import__("math").sin(angle)


        # ---------------------------------------------------------------------
        # MIGRATION AUTOMATIQUE DES ANCIENNES FICHES
        # ---------------------------------------------------------------------

        migration_modifiee = False

        for index_migration, fiche_migration in enumerate(fiches_m):
            if not isinstance(fiche_migration, dict):
                fiches_m[index_migration] = {
                    "id": mm_id("fiche"),
                    "nom": f"Fiche méthode {index_migration + 1}",
                    "description": "",
                    "orientation": "horizontal",
                    "formes": [],
                    "liaisons": [],
                    "date_creation": mm_maintenant(),
                    "date_modification": mm_maintenant(),
                }
                fiche_migration = fiches_m[index_migration]
                migration_modifiee = True

            if not fiche_migration.get("id"):
                fiche_migration["id"] = mm_id("fiche")
                migration_modifiee = True

            fiche_migration.setdefault("nom", f"Fiche méthode {index_migration + 1}")
            fiche_migration.setdefault("description", "")
            fiche_migration.setdefault("orientation", "horizontal")
            fiche_migration.setdefault("formes", [])
            fiche_migration.setdefault("liaisons", [])
            fiche_migration.setdefault("date_creation", mm_maintenant())
            fiche_migration.setdefault("date_modification", mm_maintenant())

            correspondance_ids = {}

            for index_noeud_migration, noeud_migration in enumerate(fiche_migration["formes"]):
                ancien_id = str(noeud_migration.get("id", index_noeud_migration + 1))
                nouvel_id = ancien_id if ancien_id.startswith("n") else f"n{ancien_id}"
                correspondance_ids[ancien_id] = nouvel_id

                if str(noeud_migration.get("id")) != nouvel_id:
                    noeud_migration["id"] = nouvel_id
                    migration_modifiee = True

                ancienne_forme = noeud_migration.get("shape", "rounded")
                mapping_formes = {
                    "box": "rounded",
                    "circle": "ellipse",
                    "diamond": "diamond",
                    "hexagon": "hexagon",
                }
                nouvelle_forme = mapping_formes.get(ancienne_forme, ancienne_forme)
                if nouvelle_forme not in [
                    "rounded",
                    "rectangle",
                    "ellipse",
                    "diamond",
                    "hexagon",
                    "capsule",
                ]:
                    nouvelle_forme = "rounded"

                noeud_migration["shape"] = nouvelle_forme
                noeud_migration.setdefault("label", "Élément")
                noeud_migration.setdefault("subtitle", "")
                noeud_migration.setdefault("notes", "")
                noeud_migration.setdefault("categorie", "idee")
                noeud_migration["color"] = mm_couleur_valide(
                    noeud_migration.get("color"),
                    "#F4EBDD",
                )
                noeud_migration["border_color"] = mm_couleur_valide(
                    noeud_migration.get("border_color"),
                    "#9B7740",
                )
                noeud_migration["text_color"] = mm_couleur_valide(
                    noeud_migration.get("text_color"),
                    "#142235",
                )

                if noeud_migration.get("x") is None:
                    noeud_migration["x"] = 340 + (index_noeud_migration % 4) * 250
                    migration_modifiee = True

                if noeud_migration.get("y") is None:
                    noeud_migration["y"] = 220 + (index_noeud_migration // 4) * 150
                    migration_modifiee = True

                noeud_migration["width"] = int(
                    mm_limite_nombre(noeud_migration.get("width"), 110, 420, 190)
                )
                noeud_migration["height"] = int(
                    mm_limite_nombre(noeud_migration.get("height"), 54, 220, 78)
                )
                noeud_migration.setdefault("locked", False)

            for index_liaison_migration, liaison_migration in enumerate(fiche_migration["liaisons"]):
                if not liaison_migration.get("id"):
                    liaison_migration["id"] = f"e{index_liaison_migration + 1}"
                    migration_modifiee = True

                source_ancienne = str(liaison_migration.get("from", ""))
                destination_ancienne = str(liaison_migration.get("to", ""))
                liaison_migration["from"] = correspondance_ids.get(
                    source_ancienne,
                    source_ancienne if source_ancienne.startswith("n") else f"n{source_ancienne}",
                )
                liaison_migration["to"] = correspondance_ids.get(
                    destination_ancienne,
                    destination_ancienne if destination_ancienne.startswith("n") else f"n{destination_ancienne}",
                )
                liaison_migration.setdefault("label", "")
                liaison_migration["color"] = mm_couleur_valide(
                    liaison_migration.get("color"),
                    "#50657D",
                )
                liaison_migration.setdefault("style", "solid")
                liaison_migration.setdefault("arrow", "to")
                liaison_migration.setdefault("width", 2)

        if migration_modifiee:
            sauvegarder_donnees()


        # ---------------------------------------------------------------------
        # DIALOGUES DE GESTION DES FICHES
        # ---------------------------------------------------------------------

        @st.dialog("Créer un diagramme vierge", width="large")
        def mm_dialogue_creer_fiche():
            st.markdown("### Nouveau mind map")
            st.caption("Créez une page blanche, puis ajoutez vos idées et vos liaisons.")

            nom_fiche = st.text_input(
                "Nom du diagramme",
                placeholder="Exemple : Procédure de mélange résine",
                key="mm_creation_nom",
            )
            description_fiche = st.text_area(
                "Description",
                placeholder="Objectif du diagramme, version, responsable...",
                key="mm_creation_description",
            )
            modele_fiche = st.radio(
                "Point de départ",
                ["Page totalement vierge", "Nœud central prêt à compléter"],
                horizontal=True,
                key="mm_creation_modele",
            )

            if st.button(
                "Créer le diagramme",
                type="primary",
                use_container_width=True,
                key="mm_creation_validation",
            ):
                nom_nettoye = nom_fiche.strip()
                if not nom_nettoye:
                    st.error("Le nom du diagramme est obligatoire.")
                    return

                nouvelle_fiche = {
                    "id": mm_id("fiche"),
                    "nom": nom_nettoye,
                    "description": description_fiche.strip(),
                    "orientation": "horizontal",
                    "formes": [],
                    "liaisons": [],
                    "date_creation": mm_maintenant(),
                    "date_modification": mm_maintenant(),
                }

                if modele_fiche == "Nœud central prêt à compléter":
                    nouvelle_fiche["formes"].append(
                        mm_nouveau_noeud(
                            nouvelle_fiche,
                            titre=nom_nettoye,
                            sous_titre="Idée centrale",
                            forme="rounded",
                            categorie="racine",
                            couleur="#142235",
                            bordure="#B38B4D",
                            texte="#FFFEFB",
                            x=720,
                            y=420,
                            largeur=230,
                            hauteur=92,
                        )
                    )

                fiches_m.append(nouvelle_fiche)
                st.session_state.mm_fiche_active_id = nouvelle_fiche["id"]
                st.session_state.mm_select_fiche_active = nouvelle_fiche["id"]
                st.session_state.mm_noeud_selectionne = None
                st.session_state.mm_liaison_selectionnee = None
                sauvegarder_donnees()
                st.rerun()


        @st.dialog("Paramètres du diagramme", width="large")
        def mm_dialogue_parametres_fiche(fiche_id):
            _, fiche_parametres = mm_trouver_fiche(fiche_id)
            if fiche_parametres is None:
                st.error("Diagramme introuvable.")
                return

            nom_modifie = st.text_input(
                "Nom du diagramme",
                value=fiche_parametres.get("nom", ""),
                key=f"mm_param_nom_{fiche_id}",
            )
            description_modifiee = st.text_area(
                "Description",
                value=fiche_parametres.get("description", ""),
                key=f"mm_param_description_{fiche_id}",
            )

            orientations = ["horizontal", "vertical", "radial", "libre"]
            orientation_actuelle = fiche_parametres.get("orientation", "horizontal")
            if orientation_actuelle not in orientations:
                orientation_actuelle = "horizontal"

            orientation_modifiee = st.selectbox(
                "Orientation préférée",
                orientations,
                index=orientations.index(orientation_actuelle),
                format_func=lambda valeur: {
                    "horizontal": "Horizontal",
                    "vertical": "Vertical",
                    "radial": "Radial",
                    "libre": "Libre",
                }[valeur],
                key=f"mm_param_orientation_{fiche_id}",
            )

            if st.button(
                "Enregistrer les paramètres",
                type="primary",
                use_container_width=True,
                key=f"mm_param_save_{fiche_id}",
            ):
                if not nom_modifie.strip():
                    st.error("Le nom du diagramme est obligatoire.")
                    return

                fiche_parametres["nom"] = nom_modifie.strip()
                fiche_parametres["description"] = description_modifiee.strip()
                fiche_parametres["orientation"] = orientation_modifiee
                mm_sauvegarder(fiche_parametres)
                st.rerun()


        @st.dialog("Supprimer le diagramme", width="small")
        def mm_dialogue_supprimer_fiche(fiche_id):
            index_suppression, fiche_suppression = mm_trouver_fiche(fiche_id)
            if fiche_suppression is None:
                st.error("Diagramme introuvable.")
                return

            st.warning(
                f"Le diagramme « {fiche_suppression.get('nom', 'Sans nom')} » "
                "et tous ses éléments seront supprimés définitivement."
            )

            confirmation = st.text_input(
                "Tapez OUI pour confirmer",
                key=f"mm_confirm_delete_fiche_{fiche_id}",
            )

            if st.button(
                "Supprimer définitivement",
                type="primary",
                use_container_width=True,
                disabled=confirmation.strip().upper() != "OUI",
                key=f"mm_delete_fiche_{fiche_id}",
            ):
                item_supprime = fiches_m.pop(index_suppression)
                deplacer_vers_corbeille(
                    "Fiche Méthode", 
                    item_supprime, 
                    identifiant=item_supprime.get('nom', 'Mind Map')
                )
                nouvelle_fiche_active = fiches_m[0].get("id") if fiches_m else None
                st.session_state.mm_fiche_active_id = nouvelle_fiche_active
                st.session_state.mm_select_fiche_active = nouvelle_fiche_active
                st.session_state.mm_noeud_selectionne = None
                st.session_state.mm_liaison_selectionnee = None
                sauvegarder_donnees()
                st.rerun()


        @st.dialog("Importer un diagramme JSON", width="large")
        def mm_dialogue_importer_fiche():
            st.caption(
                "Importez un diagramme précédemment exporté depuis B&V. "
                "L'import crée une nouvelle copie et n'écrase aucune fiche."
            )
            fichier_importe = st.file_uploader(
                "Fichier JSON",
                type=["json"],
                key="mm_import_json_file",
            )

            if fichier_importe is not None:
                try:
                    contenu_importe = json.loads(
                        fichier_importe.getvalue().decode("utf-8-sig")
                    )
                    if not isinstance(contenu_importe, dict):
                        raise ValueError("Le fichier doit contenir un objet JSON.")

                    st.success(
                        f"Diagramme détecté : {contenu_importe.get('nom', 'Sans nom')}"
                    )

                    if st.button(
                        "Importer comme nouvelle fiche",
                        type="primary",
                        use_container_width=True,
                        key="mm_import_confirm",
                    ):
                        copie_importee = copy.deepcopy(contenu_importe)
                        copie_importee["id"] = mm_id("fiche")
                        copie_importee["nom"] = (
                            str(copie_importee.get("nom", "Diagramme importé")).strip()
                            + " — Import"
                        )
                        copie_importee.setdefault("description", "")
                        copie_importee.setdefault("orientation", "libre")
                        copie_importee.setdefault("formes", [])
                        copie_importee.setdefault("liaisons", [])
                        copie_importee["date_creation"] = mm_maintenant()
                        copie_importee["date_modification"] = mm_maintenant()

                        ids_importes = set()
                        for numero_import, noeud_importe in enumerate(
                            copie_importee["formes"],
                            start=1,
                        ):
                            ancien_id = str(noeud_importe.get("id", f"n{numero_import}"))
                            nouvel_id = f"n{numero_import}"
                            ids_importes.add((ancien_id, nouvel_id))
                            noeud_importe["id"] = nouvel_id

                        mapping_import = dict(ids_importes)
                        for numero_liaison, liaison_importee in enumerate(
                            copie_importee["liaisons"],
                            start=1,
                        ):
                            liaison_importee["id"] = f"e{numero_liaison}"
                            liaison_importee["from"] = mapping_import.get(
                                str(liaison_importee.get("from")),
                                str(liaison_importee.get("from")),
                            )
                            liaison_importee["to"] = mapping_import.get(
                                str(liaison_importee.get("to")),
                                str(liaison_importee.get("to")),
                            )

                        fiches_m.append(copie_importee)
                        st.session_state.mm_fiche_active_id = copie_importee["id"]
                        st.session_state.mm_select_fiche_active = copie_importee["id"]
                        sauvegarder_donnees()
                        st.rerun()

                except Exception as erreur_import:
                    st.error(f"Import impossible : {erreur_import}")


        # ---------------------------------------------------------------------
        # DIALOGUES DE CRÉATION DES ÉLÉMENTS
        # ---------------------------------------------------------------------

        @st.dialog("Ajouter un élément au mind map", width="large")
        def mm_dialogue_ajouter_noeud(fiche_id, parent_id=None):
            _, fiche_ajout = mm_trouver_fiche(fiche_id)
            if fiche_ajout is None:
                st.error("Diagramme introuvable.")
                return

            st.markdown("### Contenu de l'élément")

            col_contenu_1, col_contenu_2 = st.columns(2)

            with col_contenu_1:
                titre_noeud = st.text_input(
                    "Titre",
                    placeholder="Exemple : Ajouter le durcisseur",
                    key=f"mm_add_titre_{fiche_id}_{parent_id}",
                )
                sous_titre_noeud = st.text_input(
                    "Sous-titre",
                    placeholder="Exemple : Dosage 2 %",
                    key=f"mm_add_subtitle_{fiche_id}_{parent_id}",
                )
                categorie_noeud = st.selectbox(
                    "Catégorie",
                    ["racine", "idee", "action", "decision", "information", "alerte"],
                    index=1,
                    format_func=lambda valeur: {
                        "racine": "Idée centrale",
                        "idee": "Idée / Sujet",
                        "action": "Action",
                        "decision": "Décision",
                        "information": "Information",
                        "alerte": "Alerte / Contrôle",
                    }[valeur],
                    key=f"mm_add_categorie_{fiche_id}_{parent_id}",
                )

            with col_contenu_2:
                forme_noeud = st.selectbox(
                    "Forme",
                    ["rounded", "rectangle", "ellipse", "diamond", "hexagon", "capsule"],
                    format_func=lambda valeur: {
                        "rounded": "Rectangle arrondi",
                        "rectangle": "Rectangle",
                        "ellipse": "Ellipse",
                        "diamond": "Losange",
                        "hexagon": "Hexagone",
                        "capsule": "Capsule",
                    }[valeur],
                    key=f"mm_add_shape_{fiche_id}_{parent_id}",
                )
                largeur_noeud = st.slider(
                    "Largeur",
                    120,
                    360,
                    190,
                    10,
                    key=f"mm_add_width_{fiche_id}_{parent_id}",
                )
                hauteur_noeud = st.slider(
                    "Hauteur",
                    56,
                    180,
                    78,
                    2,
                    key=f"mm_add_height_{fiche_id}_{parent_id}",
                )

            st.markdown("##### Couleurs")
            col_couleur_1, col_couleur_2, col_couleur_3 = st.columns(3)

            couleurs_categories = {
                "racine": ("#142235", "#B38B4D", "#FFFEFB"),
                "idee": ("#F4EBDD", "#9B7740", "#142235"),
                "action": ("#E8F3EF", "#397D67", "#142235"),
                "decision": ("#FFF5DE", "#A8701E", "#142235"),
                "information": ("#EAF2F8", "#335D82", "#142235"),
                "alerte": ("#FCEBEC", "#BA353B", "#66202E"),
            }
            couleur_defaut, bordure_defaut, texte_defaut = couleurs_categories[categorie_noeud]

            with col_couleur_1:
                couleur_noeud = st.color_picker(
                    "Fond",
                    couleur_defaut,
                    key=f"mm_add_color_{fiche_id}_{parent_id}_{categorie_noeud}",
                )
            with col_couleur_2:
                bordure_noeud = st.color_picker(
                    "Bordure",
                    bordure_defaut,
                    key=f"mm_add_border_{fiche_id}_{parent_id}_{categorie_noeud}",
                )
            with col_couleur_3:
                texte_noeud = st.color_picker(
                    "Texte",
                    texte_defaut,
                    key=f"mm_add_text_{fiche_id}_{parent_id}_{categorie_noeud}",
                )

            notes_noeud = st.text_area(
                "Notes internes",
                placeholder="Informations complémentaires visibles dans l'inspecteur...",
                key=f"mm_add_notes_{fiche_id}_{parent_id}",
            )

            if st.button(
                "Ajouter au diagramme",
                type="primary",
                use_container_width=True,
                key=f"mm_add_validate_{fiche_id}_{parent_id}",
            ):
                if not titre_noeud.strip():
                    st.error("Le titre de l'élément est obligatoire.")
                    return

                mm_memoriser_etat(fiche_ajout)

                position_x = 720
                position_y = 420
                noeud_parent = None

                if parent_id:
                    _, noeud_parent = mm_trouver_noeud(fiche_ajout, parent_id)

                if noeud_parent:
                    nombre_enfants = sum(
                        1
                        for liaison in fiche_ajout.get("liaisons", [])
                        if str(liaison.get("from")) == str(parent_id)
                    )
                    position_x = float(noeud_parent.get("x", 480)) + 285
                    position_y = float(noeud_parent.get("y", 320)) + (nombre_enfants * 115) - 55
                elif fiche_ajout.get("formes"):
                    nombre_noeuds = len(fiche_ajout["formes"])
                    position_x = 360 + (nombre_noeuds % 4) * 250
                    position_y = 220 + (nombre_noeuds // 4) * 145

                nouveau_noeud = mm_nouveau_noeud(
                    fiche_ajout,
                    titre=titre_noeud,
                    sous_titre=sous_titre_noeud,
                    forme=forme_noeud,
                    categorie=categorie_noeud,
                    couleur=couleur_noeud,
                    bordure=bordure_noeud,
                    texte=texte_noeud,
                    x=position_x,
                    y=position_y,
                    largeur=largeur_noeud,
                    hauteur=hauteur_noeud,
                )
                nouveau_noeud["notes"] = notes_noeud.strip()
                fiche_ajout["formes"].append(nouveau_noeud)

                if noeud_parent:
                    fiche_ajout["liaisons"].append(
                        mm_nouvelle_liaison(
                            fiche_ajout,
                            source=parent_id,
                            destination=nouveau_noeud["id"],
                        )
                    )

                st.session_state.mm_noeud_selectionne = nouveau_noeud["id"]
                st.session_state.mm_liaison_selectionnee = None
                mm_sauvegarder(fiche_ajout)
                st.rerun()


        @st.dialog("Créer une liaison", width="large")
        def mm_dialogue_ajouter_liaison(fiche_id, source_preselectionnee=None):
            _, fiche_liaison = mm_trouver_fiche(fiche_id)
            if fiche_liaison is None:
                st.error("Diagramme introuvable.")
                return

            noeuds_disponibles = fiche_liaison.get("formes", [])
            if len(noeuds_disponibles) < 2:
                st.warning("Il faut au moins deux éléments pour créer une liaison.")
                return

            ids_disponibles = [str(noeud.get("id")) for noeud in noeuds_disponibles]
            labels_noeuds = {
                str(noeud.get("id")): noeud.get("label", "Élément")
                for noeud in noeuds_disponibles
            }

            index_source = 0
            if str(source_preselectionnee) in ids_disponibles:
                index_source = ids_disponibles.index(str(source_preselectionnee))

            col_liaison_1, col_liaison_2 = st.columns(2)
            with col_liaison_1:
                source_liaison = st.selectbox(
                    "Depuis",
                    ids_disponibles,
                    index=index_source,
                    format_func=lambda valeur: labels_noeuds.get(valeur, valeur),
                    key=f"mm_link_source_{fiche_id}_{source_preselectionnee}",
                )
            with col_liaison_2:
                destinations = [
                    noeud_id for noeud_id in ids_disponibles if noeud_id != source_liaison
                ]
                destination_liaison = st.selectbox(
                    "Vers",
                    destinations,
                    format_func=lambda valeur: labels_noeuds.get(valeur, valeur),
                    key=f"mm_link_target_{fiche_id}_{source_preselectionnee}_{source_liaison}",
                )

            libelle_liaison = st.text_input(
                "Libellé de la liaison",
                placeholder="Exemple : puis, si oui, contient...",
                key=f"mm_link_label_{fiche_id}_{source_preselectionnee}",
            )

            col_style_1, col_style_2, col_style_3 = st.columns(3)
            with col_style_1:
                style_liaison = st.selectbox(
                    "Style",
                    ["solid", "dashed", "dotted"],
                    format_func=lambda valeur: {
                        "solid": "Trait continu",
                        "dashed": "Tirets",
                        "dotted": "Pointillés",
                    }[valeur],
                    key=f"mm_link_style_{fiche_id}_{source_preselectionnee}",
                )
            with col_style_2:
                fleche_liaison = st.selectbox(
                    "Flèche",
                    ["to", "both", "none"],
                    format_func=lambda valeur: {
                        "to": "Vers la destination",
                        "both": "Dans les deux sens",
                        "none": "Sans flèche",
                    }[valeur],
                    key=f"mm_link_arrow_{fiche_id}_{source_preselectionnee}",
                )
            with col_style_3:
                couleur_liaison = st.color_picker(
                    "Couleur",
                    "#50657D",
                    key=f"mm_link_color_{fiche_id}_{source_preselectionnee}",
                )

            if st.button(
                "Créer la liaison",
                type="primary",
                use_container_width=True,
                key=f"mm_link_validate_{fiche_id}_{source_preselectionnee}",
            ):
                doublon = any(
                    str(liaison.get("from")) == str(source_liaison)
                    and str(liaison.get("to")) == str(destination_liaison)
                    for liaison in fiche_liaison.get("liaisons", [])
                )
                if doublon:
                    st.error("Cette liaison existe déjà.")
                    return

                mm_memoriser_etat(fiche_liaison)
                nouvelle_liaison = mm_nouvelle_liaison(
                    fiche_liaison,
                    source_liaison,
                    destination_liaison,
                    libelle_liaison,
                    couleur_liaison,
                    style_liaison,
                    fleche_liaison,
                )
                fiche_liaison["liaisons"].append(nouvelle_liaison)
                st.session_state.mm_liaison_selectionnee = nouvelle_liaison["id"]
                st.session_state.mm_noeud_selectionne = None
                mm_sauvegarder(fiche_liaison)
                st.rerun()


        # ---------------------------------------------------------------------
        # TRAITEMENT DES ACTIONS ÉMISES PAR LE CANVAS INTERACTIF
        # ---------------------------------------------------------------------

        action_canvas = str(st.query_params.get("mm_action", ""))
        fiche_canvas_id = str(st.query_params.get("mm_fiche", ""))

        if action_canvas and fiche_canvas_id:
            _, fiche_canvas = mm_trouver_fiche(fiche_canvas_id)

            if fiche_canvas is not None:
                try:
                    if action_canvas == "move":
                        noeud_canvas_id = str(st.query_params.get("mm_node", ""))
                        _, noeud_canvas = mm_trouver_noeud(fiche_canvas, noeud_canvas_id)
                        if noeud_canvas is not None and not noeud_canvas.get("locked", False):
                            nouvelle_x = mm_limite_nombre(
                                st.query_params.get("mm_x"),
                                -5000,
                                5000,
                                noeud_canvas.get("x", 0),
                            )
                            nouvelle_y = mm_limite_nombre(
                                st.query_params.get("mm_y"),
                                -5000,
                                5000,
                                noeud_canvas.get("y", 0),
                            )
                            mm_memoriser_etat(fiche_canvas)
                            noeud_canvas["x"] = round(nouvelle_x, 2)
                            noeud_canvas["y"] = round(nouvelle_y, 2)
                            mm_sauvegarder(fiche_canvas)
                            st.session_state.mm_noeud_selectionne = noeud_canvas_id
                            st.session_state.mm_liaison_selectionnee = None

                    elif action_canvas == "select_node":
                        st.session_state.mm_noeud_selectionne = str(
                            st.query_params.get("mm_node", "")
                        )
                        st.session_state.mm_liaison_selectionnee = None

                    elif action_canvas == "select_edge":
                        st.session_state.mm_liaison_selectionnee = str(
                            st.query_params.get("mm_edge", "")
                        )
                        st.session_state.mm_noeud_selectionne = None

                    elif action_canvas == "add_at":
                        nouvelle_x = mm_limite_nombre(
                            st.query_params.get("mm_x"), -5000, 5000, 720
                        )
                        nouvelle_y = mm_limite_nombre(
                            st.query_params.get("mm_y"), -5000, 5000, 420
                        )
                        mm_memoriser_etat(fiche_canvas)
                        noeud_ajoute_canvas = mm_nouveau_noeud(
                            fiche_canvas,
                            titre="Nouvelle idée",
                            x=nouvelle_x,
                            y=nouvelle_y,
                        )
                        fiche_canvas["formes"].append(noeud_ajoute_canvas)
                        st.session_state.mm_noeud_selectionne = noeud_ajoute_canvas["id"]
                        st.session_state.mm_liaison_selectionnee = None
                        mm_sauvegarder(fiche_canvas)

                    elif action_canvas == "connect":
                        source_canvas = str(st.query_params.get("mm_from", ""))
                        destination_canvas = str(st.query_params.get("mm_to", ""))
                        _, source_existe = mm_trouver_noeud(fiche_canvas, source_canvas)
                        _, destination_existe = mm_trouver_noeud(
                            fiche_canvas,
                            destination_canvas,
                        )
                        doublon_canvas = any(
                            str(liaison.get("from")) == source_canvas
                            and str(liaison.get("to")) == destination_canvas
                            for liaison in fiche_canvas.get("liaisons", [])
                        )
                        if (
                            source_existe is not None
                            and destination_existe is not None
                            and source_canvas != destination_canvas
                            and not doublon_canvas
                        ):
                            mm_memoriser_etat(fiche_canvas)
                            fiche_canvas["liaisons"].append(
                                mm_nouvelle_liaison(
                                    fiche_canvas,
                                    source_canvas,
                                    destination_canvas,
                                )
                            )
                            mm_sauvegarder(fiche_canvas)

                    elif action_canvas == "duplicate":
                        noeud_canvas_id = str(st.query_params.get("mm_node", ""))
                        _, noeud_canvas = mm_trouver_noeud(fiche_canvas, noeud_canvas_id)
                        if noeud_canvas is not None:
                            mm_memoriser_etat(fiche_canvas)
                            copie_noeud = copy.deepcopy(noeud_canvas)
                            copie_noeud["id"] = f"n{mm_prochain_numero_noeud(fiche_canvas)}"
                            copie_noeud["label"] = f"{copie_noeud.get('label', 'Élément')} — copie"
                            copie_noeud["x"] = float(copie_noeud.get("x", 0)) + 36
                            copie_noeud["y"] = float(copie_noeud.get("y", 0)) + 36
                            fiche_canvas["formes"].append(copie_noeud)
                            st.session_state.mm_noeud_selectionne = copie_noeud["id"]
                            st.session_state.mm_liaison_selectionnee = None
                            mm_sauvegarder(fiche_canvas)

                except Exception as erreur_canvas:
                    st.session_state.mm_derniere_erreur_canvas = str(erreur_canvas)

            st.query_params.clear()
            st.rerun()


        # ---------------------------------------------------------------------
        # EN-TÊTE ET BARRE DE GESTION DES DIAGRAMMES
        # ---------------------------------------------------------------------

        st.markdown(
            """
            <div style="
                display:flex;
                align-items:flex-start;
                justify-content:space-between;
                gap:18px;
                margin:2px 0 18px 0;
                padding:18px 20px;
                background:linear-gradient(135deg, rgba(20,34,53,.97), rgba(32,52,77,.94));
                border:1px solid rgba(200,165,107,.35);
                border-radius:14px;
                box-shadow:0 14px 32px rgba(16,26,39,.12);
            ">
                <div>
                    <div style="color:#D9BF91;font-size:11px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;">
                        Atelier de conception visuelle
                    </div>
                    <div style="color:#FFFEFB;font-family:Georgia,serif;font-size:27px;line-height:1.15;margin-top:6px;">
                        Mind Map — Fiches Méthode
                    </div>
                    <div style="color:rgba(255,254,251,.68);font-size:13px;margin-top:7px;max-width:760px;">
                        Créez, reliez, déplacez et documentez vos éléments sur une page blanche interactive.
                        Chaque modification est enregistrée dans la base B&V.
                    </div>
                </div>
                <div style="
                    flex:0 0 auto;
                    color:#142235;
                    background:#D9BF91;
                    padding:7px 11px;
                    border-radius:999px;
                    font-size:11px;
                    font-weight:800;
                    letter-spacing:.04em;
                ">
                    ENREGISTREMENT JSON
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        barre_fiche_1, barre_fiche_2, barre_fiche_3, barre_fiche_4, barre_fiche_5 = st.columns(
            [1.1, 1.1, 1.1, 1.1, 1.1]
        )

        with barre_fiche_1:
            if st.button(
                "➕ Nouveau diagramme",
                type="primary",
                use_container_width=True,
                key="mm_top_new",
            ):
                mm_dialogue_creer_fiche()

        with barre_fiche_2:
            if st.button(
                "📥 Importer JSON",
                use_container_width=True,
                key="mm_top_import",
            ):
                mm_dialogue_importer_fiche()

        if not fiches_m:
            st.markdown(
                """
                <div style="
                    min-height:430px;
                    display:flex;
                    flex-direction:column;
                    align-items:center;
                    justify-content:center;
                    text-align:center;
                    padding:38px;
                    background:rgba(255,254,251,.82);
                    border:1px dashed rgba(155,119,64,.48);
                    border-radius:16px;
                    box-shadow:0 10px 26px rgba(16,26,39,.06);
                ">
                    <div style="font-size:48px;margin-bottom:12px;">◇</div>
                    <div style="font-family:Georgia,serif;color:#142235;font-size:25px;">
                        Votre espace de conception est vide
                    </div>
                    <div style="color:#6D7F91;font-size:14px;max-width:570px;margin-top:9px;line-height:1.7;">
                        Créez un premier diagramme vierge. Vous pourrez ensuite ajouter des idées,
                        des actions, des décisions et des liaisons, puis déplacer librement chaque élément.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.stop()

        ids_fiches = [str(fiche.get("id")) for fiche in fiches_m]
        noms_fiches = {
            str(fiche.get("id")): fiche.get("nom", "Sans nom")
            for fiche in fiches_m
        }

        fiche_active_id = st.session_state.get("mm_fiche_active_id")
        if fiche_active_id not in ids_fiches:
            fiche_active_id = ids_fiches[0]

        if st.session_state.get("mm_select_fiche_active") not in ids_fiches:
            st.session_state.mm_select_fiche_active = fiche_active_id

        with barre_fiche_3:
            fiche_active_id = st.selectbox(
                "Diagramme actif",
                ids_fiches,
                format_func=lambda valeur: noms_fiches.get(valeur, valeur),
                label_visibility="collapsed",
                key="mm_select_fiche_active",
            )
            st.session_state.mm_fiche_active_id = fiche_active_id

        index_fiche_active, fiche_active = mm_trouver_fiche(fiche_active_id)

        with barre_fiche_4:
            if st.button(
                "⚙️ Paramètres",
                use_container_width=True,
                key=f"mm_top_settings_{fiche_active_id}",
            ):
                mm_dialogue_parametres_fiche(fiche_active_id)

        with barre_fiche_5:
            if st.button(
                "🗑️ Supprimer la fiche",
                use_container_width=True,
                key=f"mm_top_delete_{fiche_active_id}",
            ):
                mm_dialogue_supprimer_fiche(fiche_active_id)

        # Deuxième ligne d'actions : duplication, historique et export.
        action_fiche_1, action_fiche_2, action_fiche_3, action_fiche_4, action_fiche_5 = st.columns(
            [1, 1, 1, 1, 1.25]
        )

        with action_fiche_1:
            if st.button(
                "⧉ Dupliquer la fiche",
                use_container_width=True,
                key=f"mm_duplicate_fiche_{fiche_active_id}",
            ):
                copie_fiche = copy.deepcopy(fiche_active)
                copie_fiche["id"] = mm_id("fiche")
                copie_fiche["nom"] = f"{fiche_active.get('nom', 'Diagramme')} — Copie"
                copie_fiche["date_creation"] = mm_maintenant()
                copie_fiche["date_modification"] = mm_maintenant()
                fiches_m.append(copie_fiche)
                st.session_state.mm_fiche_active_id = copie_fiche["id"]
                st.session_state.mm_select_fiche_active = copie_fiche["id"]
                sauvegarder_donnees()
                st.rerun()

        with action_fiche_2:
            historique_disponible = bool(
                st.session_state.get(mm_cle_historique(fiche_active), [])
            )
            if st.button(
                "↶ Annuler",
                use_container_width=True,
                disabled=not historique_disponible,
                key=f"mm_undo_{fiche_active_id}",
            ):
                if mm_annuler(fiche_active):
                    st.rerun()

        with action_fiche_3:
            retablir_disponible = bool(
                st.session_state.get(mm_cle_retablir(fiche_active), [])
            )
            if st.button(
                "↷ Rétablir",
                use_container_width=True,
                disabled=not retablir_disponible,
                key=f"mm_redo_{fiche_active_id}",
            ):
                if mm_retablir(fiche_active):
                    st.rerun()

        with action_fiche_4:
            export_fiche = json.dumps(
                fiche_active,
                ensure_ascii=False,
                indent=2,
            ).encode("utf-8")
            nom_export = re.sub(
                r"[^a-zA-Z0-9_-]+",
                "_",
                fiche_active.get("nom", "fiche_methode"),
            ).strip("_")
            st.download_button(
                "⬇️ Exporter JSON",
                data=export_fiche,
                file_name=f"{nom_export or 'fiche_methode'}.json",
                mime="application/json",
                use_container_width=True,
                key=f"mm_export_{fiche_active_id}",
            )

        with action_fiche_5:
            st.markdown(
                f"""
                <div style="
                    min-height:42px;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    color:#344A63;
                    background:rgba(255,254,251,.72);
                    border:1px solid rgba(20,34,53,.13);
                    border-radius:8px;
                    font-size:12px;
                    font-weight:700;
                ">
                    {len(fiche_active.get('formes', []))} éléments&nbsp;&nbsp;•&nbsp;&nbsp;
                    {len(fiche_active.get('liaisons', []))} liaisons
                </div>
                """,
                unsafe_allow_html=True,
            )

        if fiche_active.get("description"):
            st.caption(fiche_active.get("description"))


        # ---------------------------------------------------------------------
        # ESPACE DE TRAVAIL : BIBLIOTHÈQUE + CANVAS + INSPECTEUR
        # ---------------------------------------------------------------------

        colonne_bibliotheque, colonne_canvas, colonne_inspecteur = st.columns(
            [1.05, 3.55, 1.2],
            gap="medium",
        )

        # ---------------------------------------------------------------------
        # COLONNE GAUCHE — CRÉATION ET STRUCTURE
        # ---------------------------------------------------------------------

        with colonne_bibliotheque:
            st.markdown("#### Bibliothèque")
            st.caption("Ajoutez des éléments puis reliez-les sur le canvas.")

            if st.button(
                "＋ Ajouter un élément",
                type="primary",
                use_container_width=True,
                key=f"mm_add_node_main_{fiche_active_id}",
            ):
                mm_dialogue_ajouter_noeud(fiche_active_id)

            if st.button(
                "↗ Créer une liaison",
                use_container_width=True,
                disabled=len(fiche_active.get("formes", [])) < 2,
                key=f"mm_add_edge_main_{fiche_active_id}",
            ):
                mm_dialogue_ajouter_liaison(fiche_active_id)

            with st.expander("Disposition automatique", expanded=True):
                st.caption("Réorganise tous les éléments sans modifier leur contenu.")

                if st.button(
                    "Arbre horizontal",
                    use_container_width=True,
                    key=f"mm_layout_h_{fiche_active_id}",
                ):
                    mm_memoriser_etat(fiche_active)
                    mm_disposition_automatique(fiche_active, "horizontal")
                    fiche_active["orientation"] = "horizontal"
                    mm_sauvegarder(fiche_active)
                    st.rerun()

                if st.button(
                    "Arbre vertical",
                    use_container_width=True,
                    key=f"mm_layout_v_{fiche_active_id}",
                ):
                    mm_memoriser_etat(fiche_active)
                    mm_disposition_automatique(fiche_active, "vertical")
                    fiche_active["orientation"] = "vertical"
                    mm_sauvegarder(fiche_active)
                    st.rerun()

                if st.button(
                    "Carte radiale",
                    use_container_width=True,
                    key=f"mm_layout_r_{fiche_active_id}",
                ):
                    mm_memoriser_etat(fiche_active)
                    mm_disposition_automatique(fiche_active, "radial")
                    fiche_active["orientation"] = "radial"
                    mm_sauvegarder(fiche_active)
                    st.rerun()

            with st.expander("Liste des éléments", expanded=True):
                filtre_noeuds = st.text_input(
                    "Rechercher",
                    placeholder="Nom ou sous-titre...",
                    label_visibility="collapsed",
                    key=f"mm_search_nodes_{fiche_active_id}",
                ).strip().lower()

                noeuds_filtres = []
                for noeud_liste in fiche_active.get("formes", []):
                    contenu_recherche = (
                        f"{noeud_liste.get('label', '')} "
                        f"{noeud_liste.get('subtitle', '')} "
                        f"{noeud_liste.get('categorie', '')}"
                    ).lower()
                    if not filtre_noeuds or filtre_noeuds in contenu_recherche:
                        noeuds_filtres.append(noeud_liste)

                if not noeuds_filtres:
                    st.info("Aucun élément à afficher.")

                for noeud_liste in noeuds_filtres[:80]:
                    identifiant_liste = str(noeud_liste.get("id"))
                    selection_liste = (
                        str(st.session_state.get("mm_noeud_selectionne"))
                        == identifiant_liste
                    )
                    libelle_bouton = (
                        f"{'●' if selection_liste else '○'} "
                        f"{noeud_liste.get('label', 'Élément')}"
                    )
                    if st.button(
                        libelle_bouton,
                        use_container_width=True,
                        key=f"mm_list_node_{fiche_active_id}_{identifiant_liste}",
                    ):
                        st.session_state.mm_noeud_selectionne = identifiant_liste
                        st.session_state.mm_liaison_selectionnee = None
                        st.rerun()

        # ---------------------------------------------------------------------
        # COLONNE CENTRALE — CANVAS SVG INTERACTIF SANS DÉPENDANCE EXTERNE
        # ---------------------------------------------------------------------

        with colonne_canvas:
            noeuds_canvas = copy.deepcopy(fiche_active.get("formes", []))
            liaisons_canvas = copy.deepcopy(fiche_active.get("liaisons", []))

            donnees_noeuds_json = json.dumps(
                noeuds_canvas,
                ensure_ascii=False,
            ).replace("</", "<\\/")
            donnees_liaisons_json = json.dumps(
                liaisons_canvas,
                ensure_ascii=False,
            ).replace("</", "<\\/")
            fiche_id_json = json.dumps(str(fiche_active_id), ensure_ascii=False)
            nom_fiche_json = json.dumps(
                str(fiche_active.get("nom", "Mind Map")),
                ensure_ascii=False,
            )
            noeud_selection_canvas_json = json.dumps(
                str(st.session_state.get("mm_noeud_selectionne") or ""),
                ensure_ascii=False,
            )
            liaison_selection_canvas_json = json.dumps(
                str(st.session_state.get("mm_liaison_selectionnee") or ""),
                ensure_ascii=False,
            )

            canvas_html = r"""
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
    :root {
        --ink: #142235;
        --ink-soft: #50657D;
        --ivory: #FFFEFB;
        --paper: #FCFAF5;
        --gold: #B38B4D;
        --gold-soft: #D9BF91;
        --line: rgba(20, 34, 53, .14);
        --shadow: 0 18px 50px rgba(16, 26, 39, .14);
    }

    * {
        box-sizing: border-box;
    }

    html,
    body {
        width: 100%;
        height: 100%;
        margin: 0;
        overflow: hidden;
        color: var(--ink);
        background: transparent;
        font-family: Inter, "Segoe UI", Arial, sans-serif;
        user-select: none;
    }

    #shell {
        position: relative;
        width: 100%;
        height: 760px;
        overflow: hidden;
        background: var(--paper);
        border: 1px solid rgba(155, 119, 64, .32);
        border-radius: 14px;
        box-shadow: var(--shadow);
    }

    #topbar {
        position: absolute;
        z-index: 20;
        top: 12px;
        left: 12px;
        right: 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        pointer-events: none;
    }

    .toolbar,
    .statusbar {
        display: flex;
        align-items: center;
        gap: 5px;
        padding: 6px;
        background: rgba(255, 254, 251, .92);
        border: 1px solid rgba(20, 34, 53, .14);
        border-radius: 10px;
        box-shadow: 0 8px 22px rgba(16, 26, 39, .11);
        backdrop-filter: blur(12px);
        pointer-events: auto;
    }

    .statusbar {
        max-width: 44%;
        padding: 8px 11px;
        color: var(--ink-soft);
        font-size: 11px;
        font-weight: 700;
        letter-spacing: .02em;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .tool {
        min-width: 34px;
        height: 32px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 0 9px;
        color: var(--ink);
        background: transparent;
        border: 1px solid transparent;
        border-radius: 7px;
        font-family: inherit;
        font-size: 12px;
        font-weight: 800;
        cursor: pointer;
        transition: .16s ease;
    }

    .tool:hover {
        color: #FFFEFB;
        background: var(--ink);
        border-color: var(--ink);
        transform: translateY(-1px);
    }

    .tool.active {
        color: var(--ink);
        background: var(--gold-soft);
        border-color: var(--gold);
    }

    .separator {
        width: 1px;
        height: 22px;
        margin: 0 2px;
        background: rgba(20, 34, 53, .13);
    }

    #workspace {
        width: 100%;
        height: 100%;
        display: block;
        cursor: grab;
        touch-action: none;
    }

    #workspace.panning,
    #workspace.dragging {
        cursor: grabbing;
    }

    .edge-visible {
        fill: none;
        stroke-linecap: round;
        stroke-linejoin: round;
        transition: stroke-width .12s ease, opacity .12s ease;
    }

    .edge-hit {
        fill: none;
        stroke: transparent;
        stroke-width: 16;
        cursor: pointer;
        pointer-events: stroke;
    }

    .edge-group:hover .edge-visible,
    .edge-group.selected .edge-visible {
        stroke-width: 4 !important;
        opacity: .96;
        filter: drop-shadow(0 0 4px rgba(179, 139, 77, .34));
    }

    .node {
        cursor: move;
        filter: drop-shadow(0 7px 12px rgba(16, 26, 39, .10));
        transition: filter .15s ease;
    }

    .node:hover {
        filter: drop-shadow(0 11px 16px rgba(16, 26, 39, .18));
    }

    .node.selected .node-shape {
        stroke: #B38B4D !important;
        stroke-width: 4 !important;
        filter: drop-shadow(0 0 7px rgba(179, 139, 77, .30));
    }

    .node.connect-source .node-shape {
        stroke: #397D67 !important;
        stroke-width: 4 !important;
        stroke-dasharray: 8 5;
    }

    .node-shape {
        transition: stroke-width .12s ease, stroke .12s ease;
    }

    .node-title {
        font-family: Inter, "Segoe UI", Arial, sans-serif;
        font-size: 14px;
        font-weight: 800;
        line-height: 1.18;
        text-align: center;
        overflow-wrap: anywhere;
    }

    .node-subtitle {
        margin-top: 5px;
        font-family: Inter, "Segoe UI", Arial, sans-serif;
        font-size: 11px;
        font-weight: 600;
        line-height: 1.2;
        text-align: center;
        opacity: .66;
        overflow-wrap: anywhere;
    }

    .edge-label-bg {
        fill: rgba(255, 254, 251, .96);
        stroke: rgba(20, 34, 53, .12);
        stroke-width: 1;
    }

    .edge-label {
        fill: #344A63;
        font-size: 11px;
        font-weight: 700;
        text-anchor: middle;
        dominant-baseline: middle;
        pointer-events: none;
    }

    #emptyState {
        position: absolute;
        z-index: 10;
        inset: 0;
        display: none;
        align-items: center;
        justify-content: center;
        pointer-events: none;
    }

    #emptyState > div {
        max-width: 430px;
        padding: 24px 28px;
        color: #50657D;
        background: rgba(255, 254, 251, .88);
        border: 1px dashed rgba(155, 119, 64, .45);
        border-radius: 14px;
        text-align: center;
        box-shadow: 0 12px 30px rgba(16, 26, 39, .08);
        backdrop-filter: blur(9px);
    }

    #emptyState strong {
        display: block;
        margin-bottom: 7px;
        color: #142235;
        font-family: Georgia, serif;
        font-size: 20px;
        font-weight: 500;
    }

    #minimap {
        position: absolute;
        z-index: 15;
        right: 12px;
        bottom: 12px;
        width: 150px;
        height: 94px;
        overflow: hidden;
        background: rgba(255, 254, 251, .90);
        border: 1px solid rgba(20, 34, 53, .14);
        border-radius: 9px;
        box-shadow: 0 8px 22px rgba(16, 26, 39, .10);
        pointer-events: none;
    }

    #minimap svg {
        width: 100%;
        height: 100%;
    }

    #help {
        position: absolute;
        z-index: 16;
        left: 12px;
        bottom: 12px;
        padding: 8px 10px;
        color: rgba(20, 34, 53, .66);
        background: rgba(255, 254, 251, .84);
        border: 1px solid rgba(20, 34, 53, .11);
        border-radius: 8px;
        font-size: 10px;
        font-weight: 700;
        box-shadow: 0 7px 18px rgba(16, 26, 39, .08);
        backdrop-filter: blur(8px);
        pointer-events: none;
    }

    @media (max-width: 760px) {
        #shell {
            height: 650px;
        }

        .statusbar,
        #minimap,
        #help {
            display: none;
        }

        .tool span {
            display: none;
        }
    }
</style>
</head>
<body>
<div id="shell">
    <div id="topbar">
        <div class="toolbar">
            <button class="tool" id="zoomOut" title="Zoom arrière">−</button>
            <button class="tool" id="zoomIn" title="Zoom avant">＋</button>
            <button class="tool" id="fit" title="Adapter à l'écran">Ajuster</button>
            <button class="tool" id="center" title="Recentrer">Centrer</button>
            <div class="separator"></div>
            <button class="tool" id="linkMode" title="Créer une liaison entre deux éléments">↗ <span>Lier</span></button>
            <button class="tool" id="toggleGrid" title="Afficher ou masquer la grille"># <span>Grille</span></button>
            <div class="separator"></div>
            <button class="tool" id="exportSvg" title="Télécharger en SVG">SVG</button>
            <button class="tool" id="exportPng" title="Télécharger en PNG">PNG</button>
            <button class="tool" id="fullscreen" title="Plein écran">⛶</button>
        </div>
        <div class="statusbar" id="status">Double-cliquez sur le fond pour créer une idée.</div>
    </div>

    <svg id="workspace" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <pattern id="smallGrid" width="24" height="24" patternUnits="userSpaceOnUse">
                <path d="M 24 0 L 0 0 0 24" fill="none" stroke="rgba(20,34,53,.055)" stroke-width="1" />
            </pattern>
            <pattern id="grid" width="120" height="120" patternUnits="userSpaceOnUse">
                <rect width="120" height="120" fill="url(#smallGrid)" />
                <path d="M 120 0 L 0 0 0 120" fill="none" stroke="rgba(155,119,64,.11)" stroke-width="1.25" />
            </pattern>
            <marker id="arrowDefault" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
                <path d="M0,0 L0,6 L9,3 z" fill="#50657D" />
            </marker>
            <marker id="arrowStart" markerWidth="10" markerHeight="10" refX="1" refY="3" orient="auto-start-reverse" markerUnits="strokeWidth">
                <path d="M9,0 L9,6 L0,3 z" fill="#50657D" />
            </marker>
        </defs>

        <g id="viewport">
            <rect id="gridRect" x="-6000" y="-6000" width="12000" height="12000" fill="url(#grid)" />
            <g id="edgesLayer"></g>
            <g id="nodesLayer"></g>
        </g>
    </svg>

    <div id="emptyState">
        <div>
            <strong>Page blanche</strong>
            Double-cliquez n'importe où pour créer un premier élément,
            ou utilisez le bouton « Ajouter un élément » dans la bibliothèque.
        </div>
    </div>

    <div id="minimap"><svg id="miniSvg"></svg></div>
    <div id="help">Molette : zoom · Glisser le fond : déplacer · Double-clic : créer</div>
</div>

<script>
(() => {
    const NODES = __NODES__;
    const EDGES = __EDGES__;
    const FICHE_ID = __FICHE_ID__;
    const FICHE_NAME = __FICHE_NAME__;
    const INITIAL_SELECTED_NODE = __SELECTED_NODE__;
    const INITIAL_SELECTED_EDGE = __SELECTED_EDGE__;

    const shell = document.getElementById('shell');
    const svg = document.getElementById('workspace');
    const viewport = document.getElementById('viewport');
    const nodesLayer = document.getElementById('nodesLayer');
    const edgesLayer = document.getElementById('edgesLayer');
    const emptyState = document.getElementById('emptyState');
    const status = document.getElementById('status');
    const gridRect = document.getElementById('gridRect');
    const miniSvg = document.getElementById('miniSvg');

    const nodeMap = new Map(NODES.map(node => [String(node.id), node]));
    const nodeElementMap = new Map();
    const edgeElementMap = new Map();

    let scale = 1;
    let panX = 0;
    let panY = 0;
    let isPanning = false;
    let panStart = null;
    let dragState = null;
    let movedDuringDrag = false;
    let selectedNode = null;
    let selectedEdge = null;
    let linkMode = false;
    let linkSource = null;
    let gridVisible = true;

    function escapeHtml(value) {
        return String(value ?? '')
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#039;');
    }

    function safeFileName(value) {
        return String(value || 'mind-map')
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .replace(/[^a-zA-Z0-9_-]+/g, '_')
            .replace(/^_+|_+$/g, '') || 'mind-map';
    }

    function sendAction(action, params = {}) {
        const url = new URL(window.parent.location.href);
        const keys = [
            'mm_action', 'mm_fiche', 'mm_node', 'mm_edge',
            'mm_x', 'mm_y', 'mm_from', 'mm_to'
        ];
        keys.forEach(key => url.searchParams.delete(key));
        url.searchParams.set('mm_action', action);
        url.searchParams.set('mm_fiche', FICHE_ID);
        Object.entries(params).forEach(([key, value]) => {
            url.searchParams.set(`mm_${key}`, String(value));
        });
        try {
            window.parent.location.href = url.toString();
        } catch (error) {
            window.open(url.toString(), '_top');
        }
    }

    function applyTransform() {
        viewport.setAttribute('transform', `translate(${panX} ${panY}) scale(${scale})`);
        renderMinimap();
    }

    function screenToWorld(clientX, clientY) {
        const point = svg.createSVGPoint();
        point.x = clientX;
        point.y = clientY;
        const matrix = viewport.getScreenCTM();
        if (!matrix) return { x: 0, y: 0 };
        const transformed = point.matrixTransform(matrix.inverse());
        return { x: transformed.x, y: transformed.y };
    }

    function shapeMarkup(node) {
        const width = Number(node.width || 190);
        const height = Number(node.height || 78);
        const halfW = width / 2;
        const halfH = height / 2;
        const fill = node.color || '#F4EBDD';
        const stroke = node.border_color || '#9B7740';
        const common = `class="node-shape" fill="${fill}" stroke="${stroke}" stroke-width="2"`;

        if (node.shape === 'ellipse') {
            return `<ellipse cx="0" cy="0" rx="${halfW}" ry="${halfH}" ${common} />`;
        }
        if (node.shape === 'diamond') {
            return `<polygon points="0,${-halfH} ${halfW},0 0,${halfH} ${-halfW},0" ${common} />`;
        }
        if (node.shape === 'hexagon') {
            const cut = Math.min(38, width * .22);
            return `<polygon points="${-halfW + cut},${-halfH} ${halfW - cut},${-halfH} ${halfW},0 ${halfW - cut},${halfH} ${-halfW + cut},${halfH} ${-halfW},0" ${common} />`;
        }
        if (node.shape === 'capsule') {
            return `<rect x="${-halfW}" y="${-halfH}" width="${width}" height="${height}" rx="${halfH}" ${common} />`;
        }
        if (node.shape === 'rectangle') {
            return `<rect x="${-halfW}" y="${-halfH}" width="${width}" height="${height}" rx="2" ${common} />`;
        }
        return `<rect x="${-halfW}" y="${-halfH}" width="${width}" height="${height}" rx="14" ${common} />`;
    }

    function renderNodes() {
        nodesLayer.innerHTML = '';
        nodeElementMap.clear();

        NODES.forEach(node => {
            const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            group.setAttribute('class', 'node');
            group.setAttribute('data-node-id', String(node.id));
            group.setAttribute('transform', `translate(${Number(node.x || 0)} ${Number(node.y || 0)})`);

            const width = Number(node.width || 190);
            const height = Number(node.height || 78);
            const textColor = node.text_color || '#142235';
            const padding = Math.max(12, width * .08);
            const contentWidth = Math.max(70, width - padding * 2);
            const contentHeight = Math.max(40, height - 14);

            group.innerHTML = `
                ${shapeMarkup(node)}
                <foreignObject x="${-contentWidth / 2}" y="${-contentHeight / 2}" width="${contentWidth}" height="${contentHeight}" pointer-events="none">
                    <div xmlns="http://www.w3.org/1999/xhtml" style="
                        width:100%;
                        height:100%;
                        display:flex;
                        flex-direction:column;
                        align-items:center;
                        justify-content:center;
                        color:${textColor};
                        padding:4px;
                    ">
                        <div class="node-title">${escapeHtml(node.label || 'Élément')}</div>
                        ${node.subtitle ? `<div class="node-subtitle">${escapeHtml(node.subtitle)}</div>` : ''}
                    </div>
                </foreignObject>
            `;

            group.addEventListener('pointerdown', event => beginNodeDrag(event, node));
            group.addEventListener('click', event => onNodeClick(event, node));
            group.addEventListener('dblclick', event => {
                event.stopPropagation();
                sendAction('select_node', { node: node.id });
            });

            nodesLayer.appendChild(group);
            nodeElementMap.set(String(node.id), group);
        });

        emptyState.style.display = NODES.length ? 'none' : 'flex';
    }

    function nodeAnchor(source, target) {
        const sx = Number(source.x || 0);
        const sy = Number(source.y || 0);
        const tx = Number(target.x || 0);
        const ty = Number(target.y || 0);
        const dx = tx - sx;
        const dy = ty - sy;
        const distance = Math.hypot(dx, dy) || 1;
        const ux = dx / distance;
        const uy = dy / distance;
        const sw = Number(source.width || 190) / 2;
        const sh = Number(source.height || 78) / 2;
        const tw = Number(target.width || 190) / 2;
        const th = Number(target.height || 78) / 2;
        const sourceRadius = Math.min(
            Math.abs(sw / (ux || .0001)),
            Math.abs(sh / (uy || .0001))
        );
        const targetRadius = Math.min(
            Math.abs(tw / (ux || .0001)),
            Math.abs(th / (uy || .0001))
        );

        return {
            x1: sx + ux * Math.min(sourceRadius, Math.max(sw, sh)),
            y1: sy + uy * Math.min(sourceRadius, Math.max(sw, sh)),
            x2: tx - ux * Math.min(targetRadius, Math.max(tw, th)),
            y2: ty - uy * Math.min(targetRadius, Math.max(tw, th)),
        };
    }

    function edgePath(edge) {
        const source = nodeMap.get(String(edge.from));
        const target = nodeMap.get(String(edge.to));
        if (!source || !target) return null;

        const point = nodeAnchor(source, target);
        const dx = point.x2 - point.x1;
        const dy = point.y2 - point.y1;
        const horizontal = Math.abs(dx) >= Math.abs(dy);
        const curve = Math.max(42, Math.min(150, Math.hypot(dx, dy) * .34));

        let c1x = point.x1;
        let c1y = point.y1;
        let c2x = point.x2;
        let c2y = point.y2;

        if (horizontal) {
            c1x += Math.sign(dx || 1) * curve;
            c2x -= Math.sign(dx || 1) * curve;
        } else {
            c1y += Math.sign(dy || 1) * curve;
            c2y -= Math.sign(dy || 1) * curve;
        }

        return {
            d: `M ${point.x1} ${point.y1} C ${c1x} ${c1y}, ${c2x} ${c2y}, ${point.x2} ${point.y2}`,
            mx: (point.x1 + point.x2) / 2,
            my: (point.y1 + point.y2) / 2,
        };
    }

    function dashFor(style) {
        if (style === 'dashed') return '10 7';
        if (style === 'dotted') return '2 7';
        return '';
    }

    function renderEdges() {
        edgesLayer.innerHTML = '';
        edgeElementMap.clear();

        EDGES.forEach(edge => {
            const geometry = edgePath(edge);
            if (!geometry) return;

            const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            group.setAttribute('class', 'edge-group');
            group.setAttribute('data-edge-id', String(edge.id));

            const color = edge.color || '#50657D';
            const width = Number(edge.width || 2);
            const dash = dashFor(edge.style);
            const markerEnd = edge.arrow === 'none' ? '' : 'url(#arrowDefault)';
            const markerStart = edge.arrow === 'both' ? 'url(#arrowStart)' : '';

            group.innerHTML = `
                <path class="edge-visible" d="${geometry.d}" stroke="${color}" stroke-width="${width}" stroke-dasharray="${dash}" marker-end="${markerEnd}" marker-start="${markerStart}" />
                <path class="edge-hit" d="${geometry.d}" />
                ${edge.label ? `
                    <g transform="translate(${geometry.mx} ${geometry.my})" pointer-events="none">
                        <rect class="edge-label-bg" x="-58" y="-13" width="116" height="26" rx="7" />
                        <text class="edge-label" x="0" y="1">${escapeHtml(edge.label).slice(0, 30)}</text>
                    </g>
                ` : ''}
            `;

            const hit = group.querySelector('.edge-hit');
            hit.addEventListener('click', event => {
                event.stopPropagation();
                selectEdgeLocally(String(edge.id));
                sendAction('select_edge', { edge: edge.id });
            });

            edgesLayer.appendChild(group);
            edgeElementMap.set(String(edge.id), group);
        });
    }

    function updateNodePosition(node) {
        const element = nodeElementMap.get(String(node.id));
        if (element) {
            element.setAttribute('transform', `translate(${node.x} ${node.y})`);
        }
        renderEdges();
        renderMinimap();
    }

    function beginNodeDrag(event, node) {
        if (event.button !== 0) return;
        event.stopPropagation();

        if (linkMode) return;
        if (node.locked) {
            status.textContent = 'Cet élément est verrouillé.';
            return;
        }

        const world = screenToWorld(event.clientX, event.clientY);
        dragState = {
            node,
            offsetX: world.x - Number(node.x || 0),
            offsetY: world.y - Number(node.y || 0),
        };
        movedDuringDrag = false;
        svg.classList.add('dragging');
        event.currentTarget.setPointerCapture?.(event.pointerId);
    }

    function onNodeClick(event, node) {
        event.stopPropagation();
        if (movedDuringDrag) return;

        if (linkMode) {
            if (!linkSource) {
                linkSource = String(node.id);
                nodeElementMap.get(linkSource)?.classList.add('connect-source');
                status.textContent = `Source sélectionnée : ${node.label}. Cliquez sur la destination.`;
                return;
            }

            if (linkSource === String(node.id)) {
                nodeElementMap.get(linkSource)?.classList.remove('connect-source');
                linkSource = null;
                status.textContent = 'Liaison annulée. Sélectionnez une nouvelle source.';
                return;
            }

            sendAction('connect', { from: linkSource, to: node.id });
            return;
        }

        selectNodeLocally(String(node.id));
        sendAction('select_node', { node: node.id });
    }

    function selectNodeLocally(nodeId) {
        selectedNode = nodeId;
        selectedEdge = null;
        nodeElementMap.forEach((element, id) => {
            element.classList.toggle('selected', id === nodeId);
        });
        edgeElementMap.forEach(element => element.classList.remove('selected'));
    }

    function selectEdgeLocally(edgeId) {
        selectedNode = null;
        selectedEdge = edgeId;
        nodeElementMap.forEach(element => element.classList.remove('selected'));
        edgeElementMap.forEach((element, id) => {
            element.classList.toggle('selected', id === edgeId);
        });
    }

    function clearSelection() {
        selectedNode = null;
        selectedEdge = null;
        nodeElementMap.forEach(element => element.classList.remove('selected'));
        edgeElementMap.forEach(element => element.classList.remove('selected'));
    }

    function beginPan(event) {
        if (event.button !== 0) return;
        if (event.target.closest?.('.node')) return;
        if (event.target.closest?.('.edge-group')) return;

        isPanning = true;
        panStart = {
            clientX: event.clientX,
            clientY: event.clientY,
            panX,
            panY,
        };
        svg.classList.add('panning');
        svg.setPointerCapture?.(event.pointerId);
        clearSelection();
    }

    function onPointerMove(event) {
        if (dragState) {
            const world = screenToWorld(event.clientX, event.clientY);
            const nextX = world.x - dragState.offsetX;
            const nextY = world.y - dragState.offsetY;
            if (
                Math.abs(nextX - Number(dragState.node.x || 0)) > .5 ||
                Math.abs(nextY - Number(dragState.node.y || 0)) > .5
            ) {
                movedDuringDrag = true;
            }
            dragState.node.x = nextX;
            dragState.node.y = nextY;
            updateNodePosition(dragState.node);
            status.textContent = `Position : ${Math.round(nextX)} × ${Math.round(nextY)}`;
            return;
        }

        if (isPanning && panStart) {
            panX = panStart.panX + (event.clientX - panStart.clientX);
            panY = panStart.panY + (event.clientY - panStart.clientY);
            applyTransform();
        }
    }

    function endPointer(event) {
        if (dragState) {
            const node = dragState.node;
            const shouldSave = movedDuringDrag;
            dragState = null;
            svg.classList.remove('dragging');

            if (shouldSave) {
                sendAction('move', {
                    node: node.id,
                    x: Number(node.x).toFixed(2),
                    y: Number(node.y).toFixed(2),
                });
            }
        }

        isPanning = false;
        panStart = null;
        svg.classList.remove('panning');
    }

    function zoomAt(factor, clientX, clientY) {
        const rect = svg.getBoundingClientRect();
        const px = clientX ?? (rect.left + rect.width / 2);
        const py = clientY ?? (rect.top + rect.height / 2);
        const before = screenToWorld(px, py);
        const oldScale = scale;
        scale = Math.max(.18, Math.min(3.4, scale * factor));
        const ratio = scale / oldScale;
        panX = px - rect.left - (px - rect.left - panX) * ratio;
        panY = py - rect.top - (py - rect.top - panY) * ratio;
        applyTransform();
        status.textContent = `Zoom : ${Math.round(scale * 100)} %`;
    }

    function fitView() {
        if (!NODES.length) {
            scale = 1;
            panX = svg.clientWidth / 2 - 720;
            panY = svg.clientHeight / 2 - 420;
            applyTransform();
            return;
        }

        const minX = Math.min(...NODES.map(node => Number(node.x || 0) - Number(node.width || 190) / 2));
        const maxX = Math.max(...NODES.map(node => Number(node.x || 0) + Number(node.width || 190) / 2));
        const minY = Math.min(...NODES.map(node => Number(node.y || 0) - Number(node.height || 78) / 2));
        const maxY = Math.max(...NODES.map(node => Number(node.y || 0) + Number(node.height || 78) / 2));
        const contentWidth = Math.max(180, maxX - minX);
        const contentHeight = Math.max(120, maxY - minY);
        const padding = 125;

        scale = Math.max(
            .22,
            Math.min(
                1.35,
                (svg.clientWidth - padding * 2) / contentWidth,
                (svg.clientHeight - padding * 2) / contentHeight
            )
        );

        panX = svg.clientWidth / 2 - ((minX + maxX) / 2) * scale;
        panY = svg.clientHeight / 2 - ((minY + maxY) / 2) * scale;
        applyTransform();
        status.textContent = 'Diagramme ajusté à la zone de travail.';
    }

    function centerView() {
        scale = 1;
        panX = svg.clientWidth / 2 - 720;
        panY = svg.clientHeight / 2 - 420;
        applyTransform();
        status.textContent = 'Canvas recentré.';
    }

    function renderMinimap() {
        if (!NODES.length) {
            miniSvg.innerHTML = '';
            return;
        }

        const minX = Math.min(...NODES.map(node => Number(node.x || 0) - 80));
        const maxX = Math.max(...NODES.map(node => Number(node.x || 0) + 80));
        const minY = Math.min(...NODES.map(node => Number(node.y || 0) - 50));
        const maxY = Math.max(...NODES.map(node => Number(node.y || 0) + 50));
        const width = Math.max(300, maxX - minX);
        const height = Math.max(180, maxY - minY);

        miniSvg.setAttribute('viewBox', `${minX - 30} ${minY - 30} ${width + 60} ${height + 60}`);
        miniSvg.innerHTML = `
            <rect x="${minX - 30}" y="${minY - 30}" width="${width + 60}" height="${height + 60}" fill="#FCFAF5" />
            ${EDGES.map(edge => {
                const source = nodeMap.get(String(edge.from));
                const target = nodeMap.get(String(edge.to));
                if (!source || !target) return '';
                return `<line x1="${source.x}" y1="${source.y}" x2="${target.x}" y2="${target.y}" stroke="#98A5B2" stroke-width="5" />`;
            }).join('')}
            ${NODES.map(node => `
                <rect x="${Number(node.x || 0) - 36}" y="${Number(node.y || 0) - 18}" width="72" height="36" rx="8" fill="${node.color || '#F4EBDD'}" stroke="${node.border_color || '#9B7740'}" stroke-width="3" />
            `).join('')}
        `;
    }

    function cloneSvgForExport() {
        const clone = svg.cloneNode(true);
        clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
        clone.setAttribute('width', '1600');
        clone.setAttribute('height', '1000');

        if (NODES.length) {
            const minX = Math.min(...NODES.map(node => Number(node.x || 0) - Number(node.width || 190) / 2)) - 100;
            const maxX = Math.max(...NODES.map(node => Number(node.x || 0) + Number(node.width || 190) / 2)) + 100;
            const minY = Math.min(...NODES.map(node => Number(node.y || 0) - Number(node.height || 78) / 2)) - 100;
            const maxY = Math.max(...NODES.map(node => Number(node.y || 0) + Number(node.height || 78) / 2)) + 100;
            clone.setAttribute('viewBox', `${minX} ${minY} ${maxX - minX} ${maxY - minY}`);
            clone.querySelector('#viewport')?.removeAttribute('transform');
        }
        return clone;
    }

    function downloadBlob(blob, fileName) {
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = fileName;
        document.body.appendChild(link);
        link.click();
        link.remove();
        setTimeout(() => URL.revokeObjectURL(link.href), 1000);
    }

    function exportSvg() {
        const clone = cloneSvgForExport();
        const source = new XMLSerializer().serializeToString(clone);
        const blob = new Blob([source], { type: 'image/svg+xml;charset=utf-8' });
        downloadBlob(blob, `${safeFileName(FICHE_NAME)}.svg`);
        status.textContent = 'Export SVG généré.';
    }

    function exportPng() {
        const clone = cloneSvgForExport();
        const source = new XMLSerializer().serializeToString(clone);
        const blob = new Blob([source], { type: 'image/svg+xml;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const image = new Image();

        image.onload = () => {
            const canvas = document.createElement('canvas');
            canvas.width = 2200;
            canvas.height = 1400;
            const context = canvas.getContext('2d');
            context.fillStyle = '#FCFAF5';
            context.fillRect(0, 0, canvas.width, canvas.height);
            context.drawImage(image, 0, 0, canvas.width, canvas.height);
            canvas.toBlob(pngBlob => {
                if (pngBlob) downloadBlob(pngBlob, `${safeFileName(FICHE_NAME)}.png`);
                URL.revokeObjectURL(url);
            }, 'image/png', .95);
        };

        image.src = url;
        status.textContent = 'Préparation de l’export PNG...';
    }

    svg.addEventListener('pointerdown', beginPan);
    window.addEventListener('pointermove', onPointerMove);
    window.addEventListener('pointerup', endPointer);
    window.addEventListener('pointercancel', endPointer);

    svg.addEventListener('wheel', event => {
        event.preventDefault();
        zoomAt(event.deltaY < 0 ? 1.11 : .90, event.clientX, event.clientY);
    }, { passive: false });

    svg.addEventListener('dblclick', event => {
        if (event.target.closest?.('.node')) return;
        if (event.target.closest?.('.edge-group')) return;
        const point = screenToWorld(event.clientX, event.clientY);
        sendAction('add_at', {
            x: point.x.toFixed(2),
            y: point.y.toFixed(2),
        });
    });

    document.getElementById('zoomIn').addEventListener('click', () => zoomAt(1.18));
    document.getElementById('zoomOut').addEventListener('click', () => zoomAt(.84));
    document.getElementById('fit').addEventListener('click', fitView);
    document.getElementById('center').addEventListener('click', centerView);

    document.getElementById('linkMode').addEventListener('click', event => {
        linkMode = !linkMode;
        linkSource = null;
        nodeElementMap.forEach(element => element.classList.remove('connect-source'));
        event.currentTarget.classList.toggle('active', linkMode);
        status.textContent = linkMode
            ? 'Mode liaison : cliquez sur la source, puis sur la destination.'
            : 'Mode déplacement activé.';
    });

    document.getElementById('toggleGrid').addEventListener('click', event => {
        gridVisible = !gridVisible;
        gridRect.style.display = gridVisible ? '' : 'none';
        event.currentTarget.classList.toggle('active', !gridVisible);
    });

    document.getElementById('exportSvg').addEventListener('click', exportSvg);
    document.getElementById('exportPng').addEventListener('click', exportPng);

    document.getElementById('fullscreen').addEventListener('click', async () => {
        try {
            if (!document.fullscreenElement) {
                await shell.requestFullscreen();
            } else {
                await document.exitFullscreen();
            }
            setTimeout(fitView, 180);
        } catch (error) {
            status.textContent = 'Le plein écran est bloqué par le navigateur.';
        }
    });

    window.addEventListener('keydown', event => {
        if (event.key === 'Escape') {
            linkMode = false;
            linkSource = null;
            document.getElementById('linkMode').classList.remove('active');
            nodeElementMap.forEach(element => element.classList.remove('connect-source'));
            clearSelection();
            status.textContent = 'Sélection annulée.';
        }

        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'd' && selectedNode) {
            event.preventDefault();
            sendAction('duplicate', { node: selectedNode });
        }
    });

    renderNodes();
    renderEdges();
    if (INITIAL_SELECTED_NODE && nodeElementMap.has(String(INITIAL_SELECTED_NODE))) {
        selectNodeLocally(String(INITIAL_SELECTED_NODE));
    } else if (INITIAL_SELECTED_EDGE && edgeElementMap.has(String(INITIAL_SELECTED_EDGE))) {
        selectEdgeLocally(String(INITIAL_SELECTED_EDGE));
    }
    applyTransform();
    requestAnimationFrame(() => requestAnimationFrame(fitView));
})();
</script>
</body>
</html>
            """

            canvas_html = canvas_html.replace("__NODES__", donnees_noeuds_json)
            canvas_html = canvas_html.replace("__EDGES__", donnees_liaisons_json)
            canvas_html = canvas_html.replace("__FICHE_ID__", fiche_id_json)
            canvas_html = canvas_html.replace("__FICHE_NAME__", nom_fiche_json)
            canvas_html = canvas_html.replace(
                "__SELECTED_NODE__",
                noeud_selection_canvas_json,
            )
            canvas_html = canvas_html.replace(
                "__SELECTED_EDGE__",
                liaison_selection_canvas_json,
            )

            components.html(
                canvas_html,
                height=780,
                scrolling=False,
            )

        # ---------------------------------------------------------------------
        # COLONNE DROITE — INSPECTEUR DE PROPRIÉTÉS
        # ---------------------------------------------------------------------

        with colonne_inspecteur:
            st.markdown("#### Inspecteur")
            st.caption("Sélectionnez un élément ou une liaison.")

            noeud_selectionne_id = st.session_state.get("mm_noeud_selectionne")
            liaison_selectionnee_id = st.session_state.get("mm_liaison_selectionnee")

            index_noeud_selectionne, noeud_selectionne = mm_trouver_noeud(
                fiche_active,
                noeud_selectionne_id,
            )
            index_liaison_selectionnee, liaison_selectionnee = mm_trouver_liaison(
                fiche_active,
                liaison_selectionnee_id,
            )

            if noeud_selectionne is not None:
                st.markdown(
                    f"""
                    <div style="
                        padding:12px 13px;
                        margin-bottom:10px;
                        background:{noeud_selectionne.get('color', '#F4EBDD')};
                        border:2px solid {noeud_selectionne.get('border_color', '#9B7740')};
                        border-radius:10px;
                    ">
                        <div style="color:{noeud_selectionne.get('text_color', '#142235')};font-size:14px;font-weight:800;">
                            {html_lib.escape(str(noeud_selectionne.get('label', 'Élément')))}
                        </div>
                        <div style="color:{noeud_selectionne.get('text_color', '#142235')};opacity:.68;font-size:11px;margin-top:4px;">
                            {html_lib.escape(str(noeud_selectionne.get('subtitle', '')))}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                action_noeud_1, action_noeud_2 = st.columns(2)
                with action_noeud_1:
                    if st.button(
                        "＋ Enfant",
                        use_container_width=True,
                        key=f"mm_child_{fiche_active_id}_{noeud_selectionne_id}",
                    ):
                        mm_dialogue_ajouter_noeud(
                            fiche_active_id,
                            parent_id=noeud_selectionne_id,
                        )

                    if st.button(
                        "⧉ Dupliquer",
                        use_container_width=True,
                        key=f"mm_duplicate_node_{fiche_active_id}_{noeud_selectionne_id}",
                    ):
                        mm_memoriser_etat(fiche_active)
                        copie_noeud = copy.deepcopy(noeud_selectionne)
                        copie_noeud["id"] = f"n{mm_prochain_numero_noeud(fiche_active)}"
                        copie_noeud["label"] = f"{copie_noeud.get('label', 'Élément')} — copie"
                        copie_noeud["x"] = float(copie_noeud.get("x", 0)) + 36
                        copie_noeud["y"] = float(copie_noeud.get("y", 0)) + 36
                        fiche_active["formes"].append(copie_noeud)
                        st.session_state.mm_noeud_selectionne = copie_noeud["id"]
                        mm_sauvegarder(fiche_active)
                        st.rerun()

                with action_noeud_2:
                    if st.button(
                        "↗ Lier",
                        use_container_width=True,
                        disabled=len(fiche_active.get("formes", [])) < 2,
                        key=f"mm_link_node_{fiche_active_id}_{noeud_selectionne_id}",
                    ):
                        mm_dialogue_ajouter_liaison(
                            fiche_active_id,
                            source_preselectionnee=noeud_selectionne_id,
                        )

                    confirmation_suppression_noeud = st.checkbox(
                        "Confirmer",
                        key=f"mm_delete_node_confirm_{fiche_active_id}_{noeud_selectionne_id}",
                    )
                    if st.button(
                        "🗑️ Supprimer",
                        use_container_width=True,
                        disabled=not confirmation_suppression_noeud,
                        key=f"mm_delete_node_{fiche_active_id}_{noeud_selectionne_id}",
                    ):
                        mm_memoriser_etat(fiche_active)
                        mm_supprimer_noeud(fiche_active, noeud_selectionne_id)
                        st.session_state.mm_noeud_selectionne = None
                        mm_sauvegarder(fiche_active)
                        st.rerun()

                with st.form(
                    f"mm_inspector_node_form_{fiche_active_id}_{noeud_selectionne_id}",
                    clear_on_submit=False,
                ):
                    titre_inspecteur = st.text_input(
                        "Titre",
                        value=noeud_selectionne.get("label", ""),
                    )
                    sous_titre_inspecteur = st.text_input(
                        "Sous-titre",
                        value=noeud_selectionne.get("subtitle", ""),
                    )
                    notes_inspecteur = st.text_area(
                        "Notes",
                        value=noeud_selectionne.get("notes", ""),
                        height=100,
                    )

                    formes_inspecteur = [
                        "rounded",
                        "rectangle",
                        "ellipse",
                        "diamond",
                        "hexagon",
                        "capsule",
                    ]
                    forme_actuelle_inspecteur = noeud_selectionne.get("shape", "rounded")
                    if forme_actuelle_inspecteur not in formes_inspecteur:
                        forme_actuelle_inspecteur = "rounded"

                    forme_inspecteur = st.selectbox(
                        "Forme",
                        formes_inspecteur,
                        index=formes_inspecteur.index(forme_actuelle_inspecteur),
                        format_func=lambda valeur: {
                            "rounded": "Rectangle arrondi",
                            "rectangle": "Rectangle",
                            "ellipse": "Ellipse",
                            "diamond": "Losange",
                            "hexagon": "Hexagone",
                            "capsule": "Capsule",
                        }[valeur],
                    )

                    categories_inspecteur = [
                        "racine",
                        "idee",
                        "action",
                        "decision",
                        "information",
                        "alerte",
                    ]
                    categorie_actuelle = noeud_selectionne.get("categorie", "idee")
                    if categorie_actuelle not in categories_inspecteur:
                        categorie_actuelle = "idee"

                    categorie_inspecteur = st.selectbox(
                        "Catégorie",
                        categories_inspecteur,
                        index=categories_inspecteur.index(categorie_actuelle),
                    )

                    col_dimensions_1, col_dimensions_2 = st.columns(2)
                    with col_dimensions_1:
                        largeur_inspecteur = st.number_input(
                            "Largeur",
                            min_value=110,
                            max_value=420,
                            value=int(noeud_selectionne.get("width", 190)),
                            step=10,
                        )
                    with col_dimensions_2:
                        hauteur_inspecteur = st.number_input(
                            "Hauteur",
                            min_value=54,
                            max_value=220,
                            value=int(noeud_selectionne.get("height", 78)),
                            step=2,
                        )

                    col_position_1, col_position_2 = st.columns(2)
                    with col_position_1:
                        x_inspecteur = st.number_input(
                            "Position X",
                            value=float(noeud_selectionne.get("x", 0)),
                            step=10.0,
                        )
                    with col_position_2:
                        y_inspecteur = st.number_input(
                            "Position Y",
                            value=float(noeud_selectionne.get("y", 0)),
                            step=10.0,
                        )

                    couleur_inspecteur = st.color_picker(
                        "Fond",
                        mm_couleur_valide(noeud_selectionne.get("color"), "#F4EBDD"),
                    )
                    bordure_inspecteur = st.color_picker(
                        "Bordure",
                        mm_couleur_valide(
                            noeud_selectionne.get("border_color"),
                            "#9B7740",
                        ),
                    )
                    texte_inspecteur = st.color_picker(
                        "Texte",
                        mm_couleur_valide(
                            noeud_selectionne.get("text_color"),
                            "#142235",
                        ),
                    )
                    verrouille_inspecteur = st.checkbox(
                        "Verrouiller la position",
                        value=bool(noeud_selectionne.get("locked", False)),
                    )

                    enregistrer_noeud = st.form_submit_button(
                        "Enregistrer l'élément",
                        type="primary",
                        use_container_width=True,
                    )

                    if enregistrer_noeud:
                        if not titre_inspecteur.strip():
                            st.error("Le titre est obligatoire.")
                        else:
                            mm_memoriser_etat(fiche_active)
                            noeud_selectionne.update(
                                {
                                    "label": titre_inspecteur.strip(),
                                    "subtitle": sous_titre_inspecteur.strip(),
                                    "notes": notes_inspecteur.strip(),
                                    "shape": forme_inspecteur,
                                    "categorie": categorie_inspecteur,
                                    "width": int(largeur_inspecteur),
                                    "height": int(hauteur_inspecteur),
                                    "x": float(x_inspecteur),
                                    "y": float(y_inspecteur),
                                    "color": couleur_inspecteur,
                                    "border_color": bordure_inspecteur,
                                    "text_color": texte_inspecteur,
                                    "locked": verrouille_inspecteur,
                                }
                            )
                            mm_sauvegarder(fiche_active)
                            st.rerun()

            elif liaison_selectionnee is not None:
                labels_par_id = {
                    str(noeud.get("id")): noeud.get("label", "Élément")
                    for noeud in fiche_active.get("formes", [])
                }

                st.markdown("##### Liaison sélectionnée")
                st.caption(
                    f"{labels_par_id.get(str(liaison_selectionnee.get('from')), 'Source')} "
                    f"→ {labels_par_id.get(str(liaison_selectionnee.get('to')), 'Destination')}"
                )

                with st.form(
                    f"mm_inspector_edge_form_{fiche_active_id}_{liaison_selectionnee_id}"
                ):
                    libelle_inspecteur_liaison = st.text_input(
                        "Libellé",
                        value=liaison_selectionnee.get("label", ""),
                    )

                    styles_liaisons = ["solid", "dashed", "dotted"]
                    style_actuel = liaison_selectionnee.get("style", "solid")
                    if style_actuel not in styles_liaisons:
                        style_actuel = "solid"

                    style_inspecteur_liaison = st.selectbox(
                        "Style",
                        styles_liaisons,
                        index=styles_liaisons.index(style_actuel),
                    )

                    fleches_liaisons = ["to", "both", "none"]
                    fleche_actuelle = liaison_selectionnee.get("arrow", "to")
                    if fleche_actuelle not in fleches_liaisons:
                        fleche_actuelle = "to"

                    fleche_inspecteur_liaison = st.selectbox(
                        "Flèche",
                        fleches_liaisons,
                        index=fleches_liaisons.index(fleche_actuelle),
                        format_func=lambda valeur: {
                            "to": "Destination",
                            "both": "Double sens",
                            "none": "Aucune",
                        }[valeur],
                    )

                    couleur_inspecteur_liaison = st.color_picker(
                        "Couleur",
                        mm_couleur_valide(
                            liaison_selectionnee.get("color"),
                            "#50657D",
                        ),
                    )
                    largeur_inspecteur_liaison = st.slider(
                        "Épaisseur",
                        1,
                        6,
                        int(liaison_selectionnee.get("width", 2)),
                    )

                    enregistrer_liaison = st.form_submit_button(
                        "Enregistrer la liaison",
                        type="primary",
                        use_container_width=True,
                    )

                    if enregistrer_liaison:
                        mm_memoriser_etat(fiche_active)
                        liaison_selectionnee.update(
                            {
                                "label": libelle_inspecteur_liaison.strip(),
                                "style": style_inspecteur_liaison,
                                "arrow": fleche_inspecteur_liaison,
                                "color": couleur_inspecteur_liaison,
                                "width": int(largeur_inspecteur_liaison),
                            }
                        )
                        mm_sauvegarder(fiche_active)
                        st.rerun()

                confirmer_suppression_liaison = st.checkbox(
                    "Confirmer la suppression",
                    key=f"mm_delete_edge_confirm_{fiche_active_id}_{liaison_selectionnee_id}",
                )
                if st.button(
                    "🗑️ Supprimer la liaison",
                    use_container_width=True,
                    disabled=not confirmer_suppression_liaison,
                    key=f"mm_delete_edge_{fiche_active_id}_{liaison_selectionnee_id}",
                ):
                    mm_memoriser_etat(fiche_active)
                    fiche_active["liaisons"] = [
                        liaison
                        for liaison in fiche_active.get("liaisons", [])
                        if str(liaison.get("id")) != str(liaison_selectionnee_id)
                    ]
                    st.session_state.mm_liaison_selectionnee = None
                    mm_sauvegarder(fiche_active)
                    st.rerun()

            else:
                st.markdown(
                    """
                    <div style="
                        padding:18px 14px;
                        color:#6D7F91;
                        background:rgba(255,254,251,.70);
                        border:1px dashed rgba(155,119,64,.36);
                        border-radius:10px;
                        text-align:center;
                        font-size:12px;
                        line-height:1.6;
                    ">
                        Cliquez sur un élément ou une liaison pour afficher ses propriétés.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.markdown("##### Raccourcis du canvas")
                st.markdown(
                    """
                    - **Double-clic sur le fond** : créer une idée
                    - **Glisser un élément** : modifier sa position
                    - **Glisser le fond** : déplacer la vue
                    - **Molette** : zoomer ou dézoomer
                    - **Lier** : cliquer sur une source puis une destination
                    - **Échap** : annuler le mode liaison
                    - **Ctrl + D** : dupliquer l'élément sélectionné
                    """
                )

        st.caption(
            f"Dernière modification : {fiche_active.get('date_modification', '-')} "
            "• Sauvegarde automatique dans donnees_bos2.json"
        )

    # ========================================================================
    # SECTION 6 — COMPARAISON INTERACTIVE
    # ========================================================================
    elif choix_section == "⚖️ Comparaison":
        pro_entete_section(
            "Analyse comparative",
            "Comparaison côte à côte",
            "Sélectionnez 2 objets ou plus (couleurs, éléments, codes RAL, mélanges) pour comparer visuellement leurs teintes et leurs caractéristiques techniques.",
            [
                ("Couleurs", len(liste_couleurs)),
                ("Éléments", len(liste_additifs)),
                ("Codes RAL", len(RAL_DICT) + len(st.session_state.processus_db["preparation_melanges"].get("base_rals", []))),
                ("Mélanges", len(liste_melanges)),
            ],
            "OUTIL COMPARATIF",
        )

        # 1. Construction du dictionnaire global des objets comparables
        options_comparaison = {}

        # --- Couleurs du nuancier ---
        for c in liste_couleurs:
            ref_c = c.get('ref', '-')
            nom_c = c.get('nom_actuel') or ref_c
            label = f"🎨 [Couleur] {nom_c} ({ref_c})"
            options_comparaison[label] = {"kind": "couleur", "data": c}

        # --- Éléments du catalogue ---
        for e in liste_additifs:
            code_e = e.get('code') or 'sans code'
            nom_e = e.get('nom', '-')
            label = f"🧪 [Élément] {nom_e} ({code_e})"
            options_comparaison[label] = {"kind": "element", "data": e}

        # --- Codes RAL Officiels ---
        for code_ral, hex_ral in RAL_DICT.items():
            label = f"🔢 [RAL Officiel] RAL {code_ral}"
            options_comparaison[label] = {
                "kind": "ral",
                "data": {"code": code_ral, "nom": f"Teinte RAL CLASSIC {code_ral}", "visuel": hex_ral, "origine": "Officiel"}
            }

        # --- Codes RAL Personnalisés ---
        for r_p in st.session_state.processus_db["preparation_melanges"].get("base_rals", []):
            if r_p.get("code"):
                label = f"🔢 [RAL Perso] RAL {r_p.get('code')} — {r_p.get('nom', '')}"
                options_comparaison[label] = {
                    "kind": "ral",
                    "data": {"code": r_p.get('code'), "nom": r_p.get('nom', ''), "visuel": r_p.get('visuel', '#FFFFFF'), "origine": "Personnalisé"}
                }

        # --- Formulations de Mélanges ---
        for m in liste_melanges:
            ref_m = m.get('ref', '-')
            nom_m = m.get('nom', '-')
            label = f"⚗️ [Mélange] {nom_m} ({ref_m})"
            options_comparaison[label] = {"kind": "melange", "data": m}

        # 2. Sélecteur d'objets à comparer
        cles_disponibles = list(options_comparaison.keys())
        defaut_selection = cles_disponibles[:2] if len(cles_disponibles) >= 2 else cles_disponibles

        selection_comparaison = st.multiselect(
            "🔍 Choisissez 2 éléments ou plus à comparer côte à côte :",
            options=cles_disponibles,
            default=defaut_selection,
            key="multiselect_comparaison_interactive"
        )

        if len(selection_comparaison) < 2:
            st.info("💡 Veuillez sélectionner au moins 2 éléments dans le champ ci-dessus pour afficher le tableau comparatif.")
        else:
            colonnes = st.columns(len(selection_comparaison))
            
            for index_col, item_key in enumerate(selection_comparaison):
                item_info = options_comparaison[item_key]
                kind = item_info["kind"]
                data = item_info["data"]

                with colonnes[index_col]:
                    st.markdown(f"#### {item_key.split('] ')[-1]}")

                    # =========================================================
                    # 🖼️ APERÇU VISUEL GRAND FORMAT
                    # =========================================================
                    st.markdown("##### 👁 Aperçu Grand Format")
                    
                    if kind in ["couleur", "ral"]:
                        hex_val = pro_couleur_valide(data.get("visuel"), "#D8DEE4")
                        st.markdown(
                            f"""
                            <div style="
                                height: 190px;
                                background: {hex_val};
                                border: 3px solid #142235;
                                border-radius: 14px;
                                box-shadow: 0 10px 25px rgba(0,0,0,0.18);
                                display: flex;
                                align-items: flex-end;
                                padding: 12px;
                                margin-bottom: 15px;
                            ">
                                <span style="
                                    background: rgba(255,255,255,0.92);
                                    padding: 4px 10px;
                                    border-radius: 6px;
                                    font-weight: 800;
                                    font-size: 13px;
                                    color: #142235;
                                    border: 1px solid #142235;
                                ">{hex_val}</span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    elif kind == "melange":
                        if data.get("image_rendu"):
                            afficher_image_base64(data["image_rendu"].get("data"))
                        else:
                            st.markdown(
                                """
                                <div style="
                                    height: 190px;
                                    background: #F1F5F9;
                                    border: 2px dashed #94A3B8;
                                    border-radius: 14px;
                                    display: flex;
                                    flex-direction: column;
                                    align-items: center;
                                    justify-content: center;
                                    color: #64748B;
                                    font-size: 13px;
                                    font-weight: 700;
                                    margin-bottom: 15px;
                                ">
                                    <div style="font-size: 32px; margin-bottom: 6px;">⚗️</div>
                                    Aucune image associée
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                    elif kind == "element":
                        is_danger = data.get("danger") == "Oui"
                        danger_flag = "🔴 Risque déclaré" if is_danger else "✅ Pas de danger majeur"
                        bg_color = "#FEF2F2" if is_danger else "#F0FDF4"
                        border_color = "#EF4444" if is_danger else "#22C55E"
                        st.markdown(
                            f"""
                            <div style="
                                height: 190px;
                                background: {bg_color};
                                border: 2px solid {border_color};
                                border-radius: 14px;
                                display: flex;
                                flex-direction: column;
                                align-items: center;
                                justify-content: center;
                                padding: 15px;
                                text-align: center;
                                margin-bottom: 15px;
                                box-shadow: 0 8px 20px rgba(0,0,0,0.06);
                            ">
                                <div style="font-size: 40px; margin-bottom: 6px;">🧪</div>
                                <div style="font-weight: 800; font-size: 15px; color: #142235;">{html_lib.escape(data.get('nature', 'Matière'))}</div>
                                <div style="font-size: 12px; margin-top: 6px; font-weight: 700; color: {'#991B1B' if is_danger else '#166534'};">{danger_flag}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    # =========================================================
                    # 📋 DÉTAILS ET CARACTÉRISTIQUES EN BAS
                    # =========================================================
                    st.markdown("##### 📋 Caractéristiques")
                    
                    if kind == "couleur":
                        st.write(f"**Catégorie :** 🎨 Couleur du nuancier")
                        st.write(f"**Référence :** `{data.get('ref', '-')}`")
                        st.write(f"**Nom actuel :** {data.get('nom_actuel', '-')}")
                        st.write(f"**Futur nom :** {data.get('nom_futur', '-')}")
                        st.write(f"**Code RAL :** {data.get('ral', '-') or '-'}")
                        st.write(f"**Société / Client :** {data.get('societe', '-')}")
                        st.write(f"**Type :** {data.get('type', '-')}")
                        st.write(f"**Commentaire :** {data.get('commentaire', '-')}")
                        if data.get("has_ft"):
                            if st.button("📄 Télécharger FT PDF", key=f"comp_btn_ft_col_{index_col}_{data.get('ref')}", use_container_width=True):
                                ouvrir_visualisation_ft_couleur(data)

                    elif kind == "element":
                        st.write(f"**Catégorie :** 🧪 Élément / Additif")
                        st.write(f"**Nom :** `{data.get('nom', '-')}`")
                        st.write(f"**Code :** `{data.get('code', '-')}`")
                        st.write(f"**Désignation :** {data.get('designation', '-')}")
                        st.write(f"**Fournisseur :** {data.get('fournisseur', '-')}")
                        st.write(f"**Nature :** {data.get('nature', '-')}")
                        st.write(f"**Danger :** {data.get('danger', '-')}")
                        if data.get('danger') == 'Oui' and data.get('danger_texte'):
                            st.caption(f"⚠️ Précision : {data.get('danger_texte')}")
                        st.write(f"**Compartiments :** {', '.join(data.get('compartiments', [])) or '-'}")
                        st.write(f"**Sous-groupe :** {data.get('sous_groupe', 'Général')}")
                        st.write(f"**Commentaire :** {data.get('commentaire', '-')}")
                        if data.get("has_ft"):
                            if st.button("📄 Télécharger FT PDF", key=f"comp_btn_ft_elem_{index_col}_{data.get('code')}", use_container_width=True):
                                ouvrir_visualisation_ft_additif(data)

                    elif kind == "ral":
                        st.write(f"**Catégorie :** 🔢 Référentiel RAL")
                        st.write(f"**Code RAL :** `{data.get('code', '-')}`")
                        st.write(f"**Désignation :** {data.get('nom', '-')}")
                        st.write(f"**Origine :** {data.get('origine', '-')}")
                        st.write(f"**Hexadécimal :** `{data.get('visuel', '-')}`")

                    elif kind == "melange":
                        st.write(f"**Catégorie :** ⚗️ Formulation de Mélange")
                        st.write(f"**Référence :** `{data.get('ref', '-')}`")
                        st.write(f"**Nom :** {data.get('nom', '-')}")
                        st.write(f"**Type :** {data.get('categorie_choisie', '-')}")
                        st.write(f"**Ateliers :** {', '.join(data.get('ateliers', [])) or '-'}")
                        st.write(f"**Emplacement :** {data.get('emplacement', '-')}")
                        st.write(f"**Commentaire :** {data.get('commentaire', '-')}")
                        
                        st.markdown("**Composants & Dosages :**")
                        composants = data.get("couleurs_associees", [])
                        if not composants:
                            st.caption("Aucun composant")
                        else:
                            for c_item in composants:
                                st.caption(f"• **{c_item.get('nom')}** : {c_item.get('dosage')}")
                        
                        if data.get("has_ft"):
                            if st.button("📄 Télécharger FT PDF", key=f"comp_btn_ft_mix_{index_col}_{data.get('ref')}", use_container_width=True):
                                ouvrir_visualisation_ft(data)

                    # --- Affichage des spécifications physico-chimiques dynamiques ---
                    ft_dict = data.get("fiche_technique", {})
                    specs_dyn = ft_dict.get("specs_dynamiques", {})
                    if specs_dyn:
                        with st.expander("🔬 Spécifications Physico-Chimiques", expanded=False):
                            for spec_nom, spec_valeur in specs_dyn.items():
                                if str(spec_valeur).strip():
                                    st.write(f"• **{spec_nom} :** {spec_valeur}")

# =============================================================================
# MODULE 2 — CORBEILLE ET HISTORIQUE DES SUPPRESSIONS
# =============================================================================

elif G_ACTIF == "corbeille":
    st.title("🗑️ Corbeille — Historique des Suppressions")
    st.caption("Consultez les éléments supprimés, affichez leurs détails, téléchargez leurs FT, modifiez-les ou restaurez-les.")

    corbeille = st.session_state.processus_db.get("preparation_melanges", {}).get("corbeille", [])

    # -------------------------------------------------------------------------
    # DIALOGUES DE MODIFICATION DÉDIÉS AUX ÉLÉMENTS EN CORBEILLE
    # -------------------------------------------------------------------------
    @st.dialog("Modifier une couleur (Corbeille)", width="large")
    def ouvrir_modif_couleur_corbeille(idx_corbeille, couleur_data):
        st.markdown(f"### {couleur_data.get('nom_actuel') or couleur_data.get('ref')} (Corbeille)")
        c_ref = st.text_input("Référence *", value=couleur_data.get("ref", ""), key=f"trash_edit_color_ref_{idx_corbeille}")
        c_actuel = st.text_input("Nom actuel", value=couleur_data.get("nom_actuel", ""), key=f"trash_edit_color_actuel_{idx_corbeille}")
        c_futur = st.text_input("Futur nom", value=couleur_data.get("nom_futur", ""), key=f"trash_edit_color_futur_{idx_corbeille}")
        c_societe = st.text_input("Société", value=couleur_data.get("societe", ""), key=f"trash_edit_color_societe_{idx_corbeille}")
        c_comm = st.text_area("Commentaire global / FT", value=couleur_data.get("commentaire_global", ""), key=f"trash_edit_color_comm_{idx_corbeille}")
        
        if st.button("Enregistrer dans la corbeille", type="primary", use_container_width=True, key=f"trash_edit_color_save_{idx_corbeille}"):
            ref_clean = c_ref.strip()
            if not ref_clean:
                st.error("La référence est obligatoire.")
                return
            couleur_data["ref"] = ref_clean
            couleur_data["nom_actuel"] = c_actuel.strip()
            couleur_data["nom_futur"] = c_futur.strip()
            couleur_data["societe"] = c_societe.strip()
            couleur_data["commentaire_global"] = c_comm.strip()
            
            # MÀJ de l'identifiant d'affichage dans la corbeille
            corbeille[idx_corbeille]["identifiant"] = f"{c_actuel.strip()} ({ref_clean})"
            sauvegarder_donnees()
            afficher_animation_validation("Couleur modifiée dans la corbeille")
            st.session_state.pop("dialog_actif", None)
            st.rerun()

    @st.dialog("Modifier un élément (Corbeille)", width="large")
    def ouvrir_modif_element_corbeille(idx_corbeille, element_data):
        st.markdown(f"### {element_data.get('nom', 'Élément')} (Corbeille)")
        e_nom = st.text_input("Nom *", value=element_data.get("nom", ""), key=f"trash_edit_elem_nom_{idx_corbeille}")
        e_code = st.text_input("Code", value=element_data.get("code", ""), key=f"trash_edit_elem_code_{idx_corbeille}")
        e_des = st.text_input("Désignation", value=element_data.get("designation", ""), key=f"trash_edit_elem_des_{idx_corbeille}")
        e_fourn = st.text_input("Fournisseur", value=element_data.get("fournisseur", ""), key=f"trash_edit_elem_fourn_{idx_corbeille}")
        e_comm = st.text_area("Commentaires généraux (FT)", value=element_data.get("commentaire_global", ""), key=f"trash_edit_elem_comm_{idx_corbeille}")

        if st.button("Enregistrer dans la corbeille", type="primary", use_container_width=True, key=f"trash_edit_elem_save_{idx_corbeille}"):
            nom_clean = e_nom.strip()
            if not nom_clean:
                st.error("Le nom est obligatoire.")
                return
            element_data["nom"] = nom_clean
            element_data["code"] = e_code.strip()
            element_data["designation"] = e_des.strip()
            element_data["fournisseur"] = e_fourn.strip()
            element_data["commentaire_global"] = e_comm.strip()

            corbeille[idx_corbeille]["identifiant"] = f"{nom_clean} ({e_code.strip() or '-'})"
            sauvegarder_donnees()
            afficher_animation_validation("Élément modifié dans la corbeille")
            st.session_state.pop("dialog_actif", None)
            st.rerun()

    @st.dialog("Modifier un mélange (Corbeille)", width="large")
    def ouvrir_modif_melange_corbeille(idx_corbeille, melange_data):
        st.markdown(f"### {melange_data.get('nom', 'Mélange')} (Corbeille)")
        m_ref = st.text_input("Référence *", value=melange_data.get("ref", ""), key=f"trash_edit_mix_ref_{idx_corbeille}")
        m_nom = st.text_input("Nom *", value=melange_data.get("nom", ""), key=f"trash_edit_mix_nom_{idx_corbeille}")
        m_emp = st.text_input("Emplacement", value=melange_data.get("emplacement", ""), key=f"trash_edit_mix_emp_{idx_corbeille}")
        m_comm = st.text_area("Commentaires généraux (FT)", value=melange_data.get("commentaire_global", ""), key=f"trash_edit_mix_comm_{idx_corbeille}")

        if st.button("Enregistrer dans la corbeille", type="primary", use_container_width=True, key=f"trash_edit_mix_save_{idx_corbeille}"):
            ref_clean = m_ref.strip()
            nom_clean = m_nom.strip()
            if not ref_clean or not nom_clean:
                st.error("La référence et le nom sont obligatoires.")
                return
            melange_data["ref"] = ref_clean
            melange_data["nom"] = nom_clean
            melange_data["emplacement"] = m_emp.strip()
            melange_data["commentaire_global"] = m_comm.strip()

            corbeille[idx_corbeille]["identifiant"] = f"{nom_clean} ({ref_clean})"
            sauvegarder_donnees()
            afficher_animation_validation("Mélange modifié dans la corbeille")
            st.session_state.pop("dialog_actif", None)
            st.rerun()

    # -------------------------------------------------------------------------
    # BARRE D'ENTÊTE ET VIDAGE
    # -------------------------------------------------------------------------
    col_info, col_vider = st.columns([3, 1])
    with col_info:
        st.info(f"Éléments présents en corbeille : **{len(corbeille)}**")
    with col_vider:
        if corbeille:
            if st.button("🚨 Vider la corbeille", type="primary", use_container_width=True, key="btn_clear_trash"):
                st.session_state.confirm_clear_trash = True
            
            if st.session_state.get("confirm_clear_trash", False):
                st.warning("⚠️ Supprimer DÉFINITIVEMENT tout le contenu ? Cette action est irréversible.")
                c_oui, c_non = st.columns(2)
                if c_oui.button("Oui, tout vider", key="yes_clear_trash"):
                    st.session_state.processus_db["preparation_melanges"]["corbeille"] = []
                    st.session_state.confirm_clear_trash = False
                    sauvegarder_donnees()
                    afficher_animation_validation("Corbeille vidée")
                    st.rerun()
                if c_non.button("Annuler", key="no_clear_trash"):
                    st.session_state.confirm_clear_trash = False
                    st.rerun()

    if not corbeille:
        st.success("La corbeille est vide. Aucun élément supprimé.")
    else:
        # Barre de recherche et filtres
        f_col1, f_col2 = st.columns([2, 1])
        with f_col1:
            recherche_corbeille = st.text_input("Rechercher dans la corbeille", placeholder="Identifiant, nom, date...", key="input_search_corbeille").strip().lower()
        with f_col2:
            types_existants = ["Tous"] + sorted(list({item.get("type", "Inconnu") for item in corbeille}))
            filtre_type_corbeille = st.selectbox("Filtrer par type", types_existants, key="select_type_corbeille")

        st.markdown("---")
        
        # En-tête du tableau
        col_h1, col_h2, col_h3, col_h4 = st.columns([1.0, 2.2, 1.5, 3.3])
        col_h1.markdown("**Type**")
        col_h2.markdown("**Identifiant / Nom**")
        col_h3.markdown("**Date suppression**")
        col_h4.markdown("**Actions (Détails / FT / Modif / Restauration)**")
        st.markdown("<hr style='margin:4px 0;border-width:2px;border-color:#142235;'>", unsafe_allow_html=True)

        # Affichage inversé (plus récents en premier)
        for index_reel, item in enumerate(reversed(corbeille)):
            index_original = len(corbeille) - 1 - index_reel
            item_type = item.get("type", "Autre")
            identifiant = item.get("identifiant", "-")
            date_suppression = item.get("date_suppression", "-")
            data_obj = item.get("data", {})

            if recherche_corbeille and (recherche_corbeille not in identifiant.lower() and recherche_corbeille not in item_type.lower() and recherche_corbeille not in date_suppression.lower()):
                continue
            if filtre_type_corbeille != "Tous" and item_type != filtre_type_corbeille:
                continue

            r_col1, r_col2, r_col3, r_col4 = st.columns([1.0, 2.2, 1.5, 3.3])
            
            icones_type = {"Couleur": "🎨", "Élément": "🧪", "Mélange": "⚗️", "Code RAL": "🔢", "Fiche Méthode": "📐"}
            icone = icones_type.get(item_type, "📄")
            
            r_col1.write(f"{icone} {item_type}")
            r_col2.write(f"**{identifiant}**")
            r_col3.write(date_suppression)

            # --- BOUTONS D'ACTIONSS COMPLETES ---
            b_voir, b_ft, b_edit, b_resto, b_del = r_col4.columns([0.8, 0.8, 0.8, 1.1, 0.9])

            # 1. 👁 VOIR DÉTAILS
            if b_voir.button("👁", key=f"trash_view_{index_original}", help="Voir le détail de l'élément"):
                if item_type == "Couleur":
                    ouvrir_details_couleur(data_obj)
                elif item_type == "Élément":
                    ouvrir_details_element(data_obj)
                elif item_type == "Mélange":
                    ouvrir_details_melange(data_obj)
                else:

                    st.json(data_obj)

            # 2. 📄 FT (TELECHARGER / VISUALISER FT PDF)
            has_ft = data_obj.get("has_ft", True)
            if has_ft and item_type in ["Couleur", "Élément", "Mélange"]:
                if b_ft.button("📄", key=f"trash_ft_{index_original}", help="Télécharger / Voir la Fiche Technique PDF"):
                    if item_type == "Couleur":
                        ouvrir_visualisation_ft_couleur(data_obj)
                    elif item_type == "Élément":
                        ouvrir_visualisation_ft_additif(data_obj)
                    elif item_type == "Mélange":
                        ouvrir_visualisation_ft(data_obj)
            else:
                b_ft.write("")

            # 3. ✎ MODIFIER DIRECTEMENT DANS LA CORBEILLE
            if b_edit.button("✎", key=f"trash_edit_{index_original}", help="Modifier l'élément archivé"):
                st.session_state.dialog_actif = {"type": f"edit_trash_{item_type}", "index": index_original}
                st.rerun()

            # 4. 🔄 RESTAURER
            if b_resto.button("🔄", key=f"trash_resto_{index_original}", help="Restaurer l'élément à sa place d'origine"):
                prep = st.session_state.processus_db["preparation_melanges"]
                if item_type == "Couleur":
                    prep.setdefault("couleurs", []).append(data_obj)
                elif item_type == "Élément":
                    prep.setdefault("additifs", []).append(data_obj)
                elif item_type == "Mélange":
                    prep.setdefault("melanges", []).append(data_obj)
                elif item_type == "Code RAL":
                    prep.setdefault("base_rals", []).append(data_obj)
                elif item_type == "Fiche Méthode":
                    prep.setdefault("fiches_methode", []).append(data_obj)

                corbeille.pop(index_original)
                sauvegarder_donnees()
                afficher_animation_validation(f"Restauré : {identifiant}")
                st.rerun()

            # 5. 🗑 SUPPRIMER DÉFINITIVEMENT
            if b_del.button("🗑️", key=f"trash_del_{index_original}", help="Supprimer définitivement"):
                corbeille.pop(index_original)
                sauvegarder_donnees()
                st.rerun()

            st.markdown("<hr style='margin:4px 0;opacity:.15;'>", unsafe_allow_html=True)

# Seul et unique appel du routeur à la toute fin du fichier :
gerer_affichage_dialogues()

