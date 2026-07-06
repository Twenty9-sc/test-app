import streamlit as st
import json
import os
import base64
from PIL import Image
import io
import re

# Configuration de la page
st.set_page_config(page_title="BOS2 - Gestion Industrielle", layout="wide")

FICHIER_SAUVEGARDE = "donnees_bos2.json"

# --- FONCTION ENCODAGE SÉCURISÉE POUR LES LOGOS INTERNES ---
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

# --- INJECTION CSS POUR L'ARRIÈRE-PLAN ---
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


# --- FONCTIONS DE CONVERSION ET RENDU ---
def encoder_fichier_local(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.read()
        base64_encoded = base64.b64encode(bytes_data).decode("utf-8")
        return {
            "nom": uploaded_file.name,
            "type": uploaded_file.type,
            "data": base64_encoded
        }
    return None

def afficher_image_base64(base64_string, width="stretch"):
    try:
        img_data = base64.b64decode(base64_string)
        image = Image.open(io.BytesIO(img_data))
        st.image(image, width=width)
    except Exception:
        st.error("Impossible d'afficher l'image locale.")

def afficher_pdf_base64(base64_string, height=500):
    try:
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_string}" width="100%" height="{height}px" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    except Exception:
        st.error("Impossible d'afficher le document PDF intégré.")

def generer_lien_telechargement(fichier_dict):
    if fichier_dict:
        try:
            valeur_bytes = base64.b64decode(fichier_dict["data"])
            st.download_button(
                label=f"📄 Ouvrir/Télécharger : {fichier_dict['nom']}",
                data=valeur_bytes,
                file_name=fichier_dict["nom"],
                mime=fichier_dict["type"]
            )
        except Exception:
            st.error("Erreur lors de la génération du lien de téléchargement.")

def interpreter_texte_avec_images(texte, images_en_ligne):
    """Analyse le texte et remplace les balises [IMAGE_X] par le rendu HTML correspondant"""
    if not texte:
        return ""
    
    # Sécuriser les dictionnaires d'images manquants
    if not images_en_ligne or not isinstance(images_en_ligne, dict):
        st.markdown(texte, unsafe_allow_html=True)
        return

    # Découpage du texte pour injecter les balises d'images proprement
    parties = re.split(r'(\[IMAGE_\d+\])', texte)
    for partie in parties:
        match = re.match(r'\[IMAGE_(\d+)\]', partie)
        if match:
            idx_img = match.group(1)
            if idx_img in images_en_ligne:
                try:
                    img_b64 = images_en_ligne[idx_img]["data"]
                    st.markdown(f'<img src="data:image/png;base64,{img_b64}" style="max-width:100%; margin:10px 0; border-radius:5px;"/>', unsafe_allow_html=True)
                except Exception:
                    st.caption("*(Image intégrée introuvable)*")
        else:
            st.markdown(partie, unsafe_allow_html=True)


# --- CHARGEMENT / SAUVEGARDE ---
def charger_donnees():
    if os.path.exists(FICHIER_SAUVEGARDE):
        try:
            with open(FICHIER_SAUVEGARDE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            st.error("Erreur de lecture du fichier JSON.")
    return {"Chaise en bois": {"etapes": [], "ressources": []}}

def sauvegarder_donnees():
    with open(FICHIER_SAUVEGARDE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.processus_db, f, ensure_ascii=False, indent=4)

if "processus_db" not in st.session_state:
    st.session_state.processus_db = charger_donnees()


# --- MODALE GRANDE TAILLE POUR LA CRÉATION ---
@st.dialog("➕ Créer une nouvelle étape de fabrication", width="large")
def ouvrir_formulaire_etape(produit):
    st.markdown("Configurez les détails de l'étape et insérez des images dans votre texte si nécessaire.")
    
    # Initialisation d'une mémoire tampon pour les images du texte
    if "temp_inline_images" not in st.session_state:
        st.session_state.temp_inline_images = {}

    # Zone d'importation pour les images "dans le texte"
    uploaded_inlines = st.file_uploader("🖼️ Zone de dépôt des images pour le texte (Optionnel)", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True, key="inline_uploader_create")
    
    if uploaded_inlines:
        st.session_state.temp_inline_images = {}
        for idx, f in enumerate(uploaded_inlines, start=1):
            st.session_state.temp_inline_images[str(idx)] = encoder_fichier_local(f)
        
        st.info("💡 **Images disponibles pour votre texte :** Copiez-collez les codes ci-dessous dans la zone d'instructions Word pour insérer l'image à cet endroit précis :")
        cols = st.columns(len(st.session_state.temp_inline_images))
        for i, (cle, val) in enumerate(st.session_state.temp_inline_images.items()):
            with cols[i]:
                st.code(f"[IMAGE_{cle}]", language="markdown")
                st.caption(f"Fichier : {val['nom']}")

    with st.form("form_etape_modal", clear_on_submit=True):
        titre_etape = st.text_input("Nom de l'étape (ex: Alignement laser)")
        desc_etape = st.text_area("Instructions explicatives (Collez vos codes [IMAGE_1] ici pour insérer vos images au milieu du texte)", height=200)
        
        st.markdown("---")
        st.markdown("**Média d'illustration principal (Volet de droite)**")
        source_media = st.radio("Source du visuel principal :", ["Depuis mon PC (Image ou PDF)", "Lien Internet (Image/Vidéo/PDF)"])
        uploaded_file = st.file_uploader("Sélectionner le fichier principal", type=["png", "jpg", "jpeg", "webp", "pdf"])
        url_media = st.text_input("Lien URL Internet")
        type_media = st.selectbox("Type de média internet", ["Image", "Vidéo", "PDF"])
        
        if st.form_submit_button("Enregistrer l'étape", type="primary"):
            if not titre_etape:
                st.error("Le nom de l'étape est obligatoire.")
            else:
                nouvelle_etape = {
                    "titre": titre_etape,
                    "description": desc_etape,
                    "media": None,
                    "type": "Image",
                    "is_local": False,
                    "media_data": None,
                    "inline_images": st.session_state.temp_inline_images.copy() # Sauvegarde des images en ligne
                }
                
                if "Depuis mon PC" in source_media and uploaded_file:
                    nouvelle_etape["is_local"] = True
                    nouvelle_etape["media_data"] = encoder_fichier_local(uploaded_file)
                    if uploaded_file.type == "application/pdf":
                            if st.button("Enregistrer la formulation", type="primary"):
            if m_ref and m_nom:
                comp = []
                for k, v in st.session_state.tmp_form_state.items():
                    couleur_trouvee = next((x for x in liste_teintes if x["ref"] == k), None)
                    nom_c = couleur_trouvee["nom_actuel"] if couleur_trouvee else f"Inconnu ({k})"
                    visuel_c = couleur_trouvee["visuel"] if couleur_trouvee else "#CCCCCC"
                    comp.append({"ref": k, "nom": nom_c, "visuel": visuel_c, "dosage": v})
                    
                st.session_state.processus_db["preparation_melanges"]["melanges"].append({
                    "ref": m_ref, "nom": m_nom, "emplacement": m_emp, "commentaire": m_comm, "couleurs_associees": comp
                })
                st.session_state.tmp_form_state = {}
                sauvegarder_donnees()
                st.rerun()
                
                st.session_state.processus_db[produit]["etapes"].append(nouvelle_etape)
                st.session_state.temp_inline_images = {} # Reset
                sauvegarder_donnees()
                st.rerun()


# --- MODALE GRANDE TAILLE POUR LA MODIFICATION ---
@st.dialog("✏️ Modifier l'étape de fabrication", width="large")
def ouvrir_modification_etape(produit, i, etape):
    st.markdown("Ajustez l'ensemble des paramètres et gérez les images intégrées au texte.")
    
    # Récupération ou initialisation des images en ligne existantes
    if "mod_inline_images" not in st.session_state:
        st.session_state.mod_inline_images = etape.get("inline_images", {}).copy()

    # Zone d'ajout de nouvelles images textuelles
    uploaded_inlines_mod = st.file_uploader("🖼️ Ajouter ou modifier les images du texte", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True, key=f"inline_uploader_mod_{i}")
    
    if uploaded_inlines_mod:
        st.session_state.mod_inline_images = {}
        for idx, f in enumerate(uploaded_inlines_mod, start=1):
            st.session_state.mod_inline_images[str(idx)] = encoder_fichier_local(f)

    if st.session_state.mod_inline_images:
        st.info("💡 Codes images disponibles pour vos instructions :")
        cols = st.columns(len(st.session_state.mod_inline_images))
        for idx_c, (cle, val) in enumerate(st.session_state.mod_inline_images.items()):
            with cols[idx_c]:
                st.code(f"[IMAGE_{cle}]", language="markdown")
                st.caption(f"Fichier : {val['nom']}")

    with st.form(f"form_mod_modal_{i}", clear_on_submit=False):
        st.markdown("**Paramètres généraux**")
        n_titre = st.text_input("Titre", value=etape['titre'])
        n_desc = st.text_area("Instructions (Insérez vos codes [IMAGE_1] où vous le souhaitez)", value=etape['description'], height=200)
        
        st.markdown("---")
        st.markdown("**Paramètres du média d'illustration principal (Volet de droite)**")
        index_src_defaut = 0 if etape.get("is_local") else 1
        n_source = st.radio("Changer de source :", ["Depuis mon PC (Image ou PDF)", "Lien Internet (Image/Vidéo/PDF)"], index=index_src_defaut)
        n_file = st.file_uploader("Téléverser un nouveau fichier principal", type=["png", "jpg", "jpeg", "webp", "pdf"])
        
        anc_url = etape.get("media") if etape.get("media") else ""
        n_url = st.text_input("Nouveau lien URL", value=anc_url)
        index_type_defaut = ["Image", "Vidéo", "PDF"].index(etape.get("type", "Image"))
        n_type_media = st.selectbox("Type du média internet", ["Image", "Vidéo", "PDF"], index=index_type_defaut)
        
        if st.form_submit_button("Mettre à jour l'étape", type="primary"):
            if not n_titre:
                st.error("Le nom de l'étape est obligatoire.")
            else:
                st.session_state.processus_db[produit]["etapes"][i]["titre"] = n_titre
                st.session_state.processus_db[produit]["etapes"][i]["description"] = n_desc
                st.session_state.processus_db[produit]["etapes"][i]["inline_images"] = st.session_state.mod_inline_images.copy()
                
                if "Depuis mon PC" in n_source:
                    if n_file:
                        st.session_state.processus_db[produit]["etapes"][i]["is_local"] = True
                        st.session_state.processus_db[produit]["etapes"][i]["media_data"] = encoder_fichier_local(n_file)
                        st.session_state.processus_db[produit]["etapes"][i]["media"] = None
                        if n_file.type == "application/pdf":
                            st.session_state.processus_db[produit]["etapes"][i]["type"] = "PDF"
                        else:
                            st.session_state.processus_db[produit]["etapes"][i]["type"] = "Image"
                else:
                    st.session_state.processus_db[produit]["etapes"][i]["is_local"] = False
                    st.session_state.processus_db[produit]["etapes"][i]["media_data"] = None
                    st.session_state.processus_db[produit]["etapes"][i]["media"] = n_url
                    st.session_state.processus_db[produit]["etapes"][i]["type"] = n_type_media
                    
                if "mod_inline_images" in st.session_state:
                    del st.session_state.mod_inline_images
                sauvegarder_donnees()
                st.rerun()


# --- BARRE LATÉRALE (SIDEBAR) ---
if LOGO_SIDEBAR_BASE64:
    try:
        img_logo_side = base64.b64decode(LOGO_SIDEBAR_BASE64)
        st.sidebar.image(Image.open(io.BytesIO(img_logo_side)), width=100)
    except Exception:
        pass

st.sidebar.title("⚙️ BOS2")
recherche = st.sidebar.text_input("🔍 Rechercher un processus...", "").strip()

liste_produits = sorted(list(st.session_state.processus_db.keys()))
if recherche:
    liste_produits = [p for p in liste_produits if recherche.lower() in p.lower()]
    liste_produits = sorted(liste_produits)

st.sidebar.subheader("📦 Sélection du Produit")
if liste_produits:
    produit_selectionne = st.sidebar.selectbox("Choisir un processus actif :", liste_produits)
else:
    produit_selectionne = None
    st.sidebar.warning("Aucun processus trouvé.")

st.sidebar.markdown("---")
st.sidebar.subheader("➕ Nouveau Processus")
nouveau_produit = st.sidebar.text_input("Nom du nouveau produit", key="new_prod_input")
if st.sidebar.button("Créer le produit"):
    if nouveau_produit and nouveau_produit not in st.session_state.processus_db:
        st.session_state.processus_db[nouveau_produit] = {"etapes": [], "ressources": []}
        sauvegarder_donnees()
        st.rerun()


# --- ZONE CENTRALE (CONTENU) ---
if produit_selectionne:
    
    if "mode_grand_ecran" not in st.session_state:
        st.session_state.mode_grand_ecran = False

    col_titre, col_btn_mode = st.columns([3, 1])
    with col_titre:
        st.title(f"📦 Processus : {produit_selectionne}")
    with col_btn_mode:
        if st.button("🖥️ Basculer Mode Grand Écran (Style PDF)", type="secondary"):
            st.session_state.mode_grand_ecran = not st.session_state.mode_grand_ecran
            st.rerun()

    # Normalisation structurelle
    if produit_selectionne in st.session_state.processus_db:
        if isinstance(st.session_state.processus_db[produit_selectionne], list):
            st.session_state.processus_db[produit_selectionne] = {
                "etapes": st.session_state.processus_db[produit_selectionne],
                "ressources": []
            }
        elif "etapes" not in st.session_state.processus_db[produit_selectionne]:
            st.session_state.processus_db[produit_selectionne]["etapes"] = []
        if "ressources" not in st.session_state.processus_db[produit_selectionne]:
            st.session_state.processus_db[produit_selectionne]["ressources"] = []

    etapes = st.session_state.processus_db[produit_selectionne]["etapes"]
    ressources = st.session_state.processus_db[produit_selectionne]["ressources"]

    # ---------------------------------------------------------
    # MODE GRAND ÉCRAN
    # ---------------------------------------------------------
    if st.session_state.mode_grand_ecran:
        st.info("💡 Mode lecture seule grand format activé.")
        if not etapes:
            st.warning("Aucune étape à afficher en grand.")
        else:
            for i, etape in enumerate(etapes):
                st.markdown(f"## 🛑 Étape {i+1} : {etape['titre']}")
                
                # Rendu intelligent du texte enrichi d'images
                interpreter_texte_avec_images(etape['description'], etape.get("inline_images", {}))
                
                if etape.get("is_local") and etape.get("media_data"):
                    if etape.get("type") == "PDF":
                        afficher_pdf_base64(etape["media_data"]["data"], height=600)
                    else:
                        afficher_image_base64(etape["media_data"]["data"], width="stretch")
                elif etape.get("media"):
                    if etape['type'] == "Vidéo":
                        st.video(etape['media'])
                    elif etape['type'] == "PDF":
                        st.markdown(f'<iframe src="{etape["media"]}" width="100%" height="600px"></iframe>', unsafe_allow_html=True)
                    else:
                        st.image(etape['media'], width="stretch")
                st.markdown("---")
        
        if ressources:
            st.markdown("### 📄 Ressources Associées")
            for res in ressources:
                generer_lien_telechargement(res)

    # ---------------------------------------------------------
    # MODE STANDARD
    # ---------------------------------------------------------
    else:
        col_btn_creer, _ = st.columns([1, 3])
        with col_btn_creer:
            if st.button("➕ Créer une étape", type="primary", use_container_width=True):
                ouvrir_formulaire_etape(produit_selectionne)

        with st.expander("🛠️ Options d'administration du produit"):
            col_mod1, col_mod2 = st.columns(2)
            with col_mod1:
                nouveau_nom_prod = st.text_input("Modifier le nom du produit", value=produit_selectionne)
                if st.button("Enregistrer le nouveau nom"):
                    if nouveau_nom_prod and nouveau_nom_prod != produit_selectionne:
                        st.session_state.processus_db[nouveau_nom_prod] = st.session_state.processus_db.pop(produit_selectionne)
                        sauvegarder_donnees()
                        st.success("Produit renommé !")
                        st.rerun()
            with col_mod2:
                if f"confirm_del_prod_{produit_selectionne}" not in st.session_state:
                    st.session_state[f"confirm_del_prod_{produit_selectionne}"] = False
                
                if not st.session_state[f"confirm_del_prod_{produit_selectionne}"]:
                    if st.button("❌ Supprimer définitivement ce produit", type="secondary"):
                        st.session_state[f"confirm_del_prod_{produit_selectionne}"] = True
                        st.rerun()
                else:
                    st.warning("⚠️ Confirmation requise.")
                    col_sub_1, col_sub_2 = st.columns(2)
                    with col_sub_1:
                        if st.button("🔴 Confirmer la suppression", type="primary"):
                            del st.session_state.processus_db[produit_selectionne]
                            st.session_state[f"confirm_del_prod_{produit_selectionne}"] = False
                            sauvegarder_donnees()
                            st.rerun()
                    with col_sub_2:
                        if st.button("Annuler"):
                            st.session_state[f"confirm_del_prod_{produit_selectionne}"] = False
                            st.rerun()

        with st.expander("📂 Documents joints & Ressources", expanded=False):
            if ressources:
                for r_idx, res in enumerate(list(ressources)):
                    c_res_file, c_res_del = st.columns([4, 1])
                    with c_res_file:
                        generer_lien_telechargement(res)
                    with c_res_del:
                        key_res_state = f"confirm_del_res_{produit_selectionne}_{r_idx}"
                        if key_res_state not in st.session_state:
                            st.session_state[key_res_state] = False
                        if not st.session_state[key_res_state]:
                            if st.button("🗑️ Enlever", key=f"btn_res_del_{r_idx}"):
                                st.session_state[key_res_state] = True
                                st.rerun()
                        else:
                            if st.button("💥 Valider", key=f"btn_res_ok_{r_idx}", type="primary"):
                                st.session_state.processus_db[produit_selectionne]["ressources"].pop(r_idx)
                                st.session_state[key_res_state] = False
                                sauvegarder_donnees()
                                st.rerun()
                            if st.button("Annuler", key=f"btn_res_cancel_{r_idx}"):
                                st.session_state[key_res_state] = False
                                st.rerun()
            
            uploaded_res = st.file_uploader("Ajouter un document (PDF, XLSX...)", type=["pdf", "xlsx", "xls", "docx", "doc", "txt"], key="upload_ressource")
            if st.button("📎 Joindre le document aux ressources"):
                if uploaded_res:
                    file_dict = encoder_fichier_local(uploaded_res)
                    st.session_state.processus_db[produit_selectionne]["ressources"].append(file_dict)
                    sauvegarder_donnees()
                    st.success("Document rattaché !")
                    st.rerun()

        st.markdown("---")
        st.subheader("📋 Étapes de fabrication")
        
        if not etapes:
            st.info("Aucune étape pour le moment.")
        else:
            for i, etape in enumerate(list(etapes)):
                with st.expander(f"🛑 Étape {i+1} : {etape['titre']}", expanded=False):
                    col_txt, col_med = st.columns([1, 1])
                    
                    with col_txt:
                        # Rendu textuel dynamique contenant du texte + des images imbriquées
                        interpreter_texte_avec_images(etape['description'], etape.get("inline_images", {}))
                        st.markdown("---")
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("✏️ Modifier l'étape", key=f"btn_open_mod_{i}", type="secondary"):
                                ouvrir_modification_etape(produit_selectionne, i, etape)
                        with c2:
                            key_etape_state = f"confirm_del_etp_{produit_selectionne}_{i}"
                            if key_etape_state not in st.session_state:
                                st.session_state[key_etape_state] = False
                                
                            if not st.session_state[key_etape_state]:
                                if st.button("🗑️ Supprimer", key=f"del_{i}", type="secondary"):
                                    st.session_state[key_etape_state] = True
                                    st.rerun()
                            else:
                                st.error("Confirmer ?")
                                if st.button("⚠️ Oui, supprimer", key=f"del_ok_{i}", type="primary"):
                                    st.session_state.processus_db[produit_selectionne]["etapes"].pop(i)
                                    st.session_state[key_etape_state] = False
                                    sauvegarder_donnees()
                                    st.rerun()
                                if st.button("Annuler", key=f"del_cancel_{i}"):
                                    st.session_state[key_etape_state] = False
                                    st.rerun()
                                
                    with col_med:
                        if etape.get("is_local") and etape.get("media_data"):
                            if etape.get("type") == "PDF":
                                afficher_pdf_base64(etape["media_data"]["data"], height=400)
                            else:
                                afficher_image_base64(etape["media_data"]["data"])
                        elif etape.get("media"):
                            try:
                                if etape['type'] == "Vidéo":
                                    st.video(etape['media'])
                                elif etape['type'] == "PDF":
                                    st.markdown(f'<iframe src="{etape["media"]}" width="100%" height="400px"></iframe>', unsafe_allow_html=True)
                                else:
                                    st.image(etape['media'], width="stretch")
                            except Exception:
                                st.error("Média distant indisponible.")
                        else:
                            st.caption("Aucun visuel principal.")
else:
    st.title("Bienvenue dans BOS2")
    st.info("Sélectionnez ou créez un produit dans la barre latérale pour démarrer.")