# ==============================================================================
# SCRIPT DE WEB SCRAPING POUR LA TRADUCTION DE DARIJA
# ==============================================================================
#
# OBJECTIF :
# Ce script automatise la collecte de traductions depuis le site learnmoroccan.com.
# Il lit des phrases en français et en anglais depuis des fichiers Excel,
# pilote un navigateur web pour soumettre ces phrases au traducteur du site,
# et sauvegarde les paires de traduction obtenues dans un fichier JSON unifié.
#
# TECHNOLOGIE CLÉ :
# - Playwright : Bibliothèque d'automatisation de navigateur moderne et robuste,
#   choisie pour sa capacité à gérer le contenu web dynamique et les interactions complexes.
# - Pandas : Utilisé pour lire efficacement les fichiers Excel sources.
#
# COMPÉTENCE RNCP VALIDÉE :
# - C1 : Automatiser l’extraction de données depuis une page web (scraping).
#
# ==============================================================================

from playwright.sync_api import sync_playwright
import json
import time
import os
import pandas as pd

# ------------------------------------------------------------------------------
# SECTION 1 : FONCTIONS DE BAS NIVEAU (INTERACTIONS UNITAIRES)
# ------------------------------------------------------------------------------

def se_connecter(page):
    """
    Automatise le processus de connexion au site.
    Cette fonction encapsule la séquence d'actions nécessaire pour s'authentifier,
    rendant le code principal plus lisible.

    Args:
        page: L'objet 'Page' de Playwright sur lequel effectuer les actions.

    Returns:
        bool: True si la connexion semble avoir réussi, False en cas d'erreur.
    """
    try:
        # L'utilisation de sélecteurs XPath est parfois nécessaire
        # lorsque les éléments n'ont pas d'ID ou de classes uniques et stables.
        print("Clic sur le bouton 'Se connecter'...")
        page.locator("xpath=/html/body/header/div/div[2]/div/a[2]/button").click()
        page.wait_for_timeout(2000) # Attente explicite pour laisser le temps à la page de se charger

        print("Saisie de l'identifiant...")
        page.locator("xpath=/html/body/section[1]/div/form/div[1]/input").fill("faridigouti@gmail.com")
        page.wait_for_timeout(1000)

        print("Saisie du mot de passe...")
        page.locator("xpath=/html/body/section[1]/div/form/div[2]/input").fill("34635263")
        page.wait_for_timeout(1000)

        print("Clic sur le bouton de validation...")
        page.locator("xpath=/html/body/section[1]/div/form/button").click()
        page.wait_for_timeout(3000) # Attente post-connexion
        
        return True
    except Exception as e:
        print(f"Erreur lors de la connexion : {e}")
        return False

# ------------------------------------------------------------------------------
# SECTION 2 : FONCTIONS DE HAUT NIVEAU (PROCESSUS COMPLEXES)
# ------------------------------------------------------------------------------

def configurer_page_traduction(page, source_lang="fr"):
    """
    Prépare la page du traducteur for une session de scraping.
    Cette fonction gère la navigation initiale, la connexion et la configuration
    de l'interface du traducteur (ex: sélection de la langue source).

    Args:
        page: L'objet 'Page' de Playwright à configurer.
        source_lang (str): La langue source à sélectionner ('fr' ou 'en').

    Returns:
        bool: True si la configuration a réussi, False sinon.
    """
    try:
        url_base="https://www.learnmoroccan.com/fr"
        
        # Étape 1 : Connexion
        print("Accès à la page d'accueil pour connexion...")
        page.goto(url_base)
        page.wait_for_timeout(2000)
        if not se_connecter(page):
            # Si la connexion échoue, le scraping ne peut pas continuer.
            return False

        # Étape 2 : Navigation vers le traducteur
        url_traducteur = f"{url_base}/translator"
        print(f"Accès à la page du traducteur : {url_traducteur}")
        page.goto(url_traducteur)
        page.wait_for_timeout(2000)

        # Étape 3 : Configuration de l'interface du traducteur
        # Le site peut avoir un état par défaut qu'il faut inverser.
        # Le bloc try/except rend le script plus résilient
        # aux changements mineurs de l'interface. Si le bouton n'est pas là,
        # le script continue au lieu de planter.
        try:
            bouton_selector = "button[aria-label='échanger les langues']"
            page.wait_for_selector(bouton_selector, state="visible", timeout=5000)
            page.locator(bouton_selector).click()
            page.wait_for_timeout(1000)
        except Exception as e:
            print(f"Info : Le bouton initial d'inversion n'a pas été trouvé ou cliqué ({e}), poursuite du script.")

        # Sélection de la langue source en fonction du paramètre
        langue = "Français" if source_lang == "fr" else "Anglais"
        print(f"Sélection de la langue {langue}...")
        page.locator("xpath=/html/body/div/div[2]/div[2]/div[1]/div[1]").click()
        page.wait_for_timeout(1000)
        page.locator(f"div:has-text('{langue}')").first.click()
        print(f"Langue {langue} sélectionnée")
        page.wait_for_timeout(1000)

        # Activer une option spécifique de l'interface (toggle)
        page.locator("xpath=/html/body/div/div[2]/div[3]/div/label/div/div").click()
        page.wait_for_timeout(1000)

        return True
    except Exception as e:
        print(f"Erreur critique lors de la configuration de la page : {e}")
        return False

def traduire_texte_dans_page(page, phrase, max_retries=3, source_lang="fr"):
    """
    Orchestre la traduction d'une seule phrase sur une page déjà configurée.
    Cette fonction est le cœur de la boucle de scraping. Elle gère la saisie,
    la soumission, et surtout l'attente et l'extraction de la traduction.

    Args:
        page: L'objet 'Page' de Playwright.
        phrase (str): Le texte à traduire.
        max_retries (int): Le nombre de tentatives en cas d'échec.
        source_lang (str): La langue source.

    Returns:
        str or None: La traduction extraite, ou None si toutes les tentatives échouent.
    """
    for retry in range(max_retries):
        try:
            # En cas de nouvelle tentative, on reconfigure la page pour la réinitialiser.
            if retry > 0:
                print(f"\n🔄 Tentative {retry + 1}/{max_retries} - Réinitialisation de la page...")
                if not configurer_page_traduction(page, source_lang=source_lang):
                    continue

            # Étape 1 : Saisie du texte
            textarea_selector = "textarea[placeholder*='écrivez quelque chose']"
            page.fill(textarea_selector, "") # Vider le champ au cas où
            page.wait_for_timeout(500)
            page.fill(textarea_selector, phrase)
            page.wait_for_timeout(1000)
            
            # Étape 2 : Clic sur le bouton de traduction
            # L'utilisation de page.evaluate avec du JavaScript pour cliquer est
            # une technique de contournement robuste lorsque les clics standards
            # de Playwright sont interceptés par d'autres éléments.
            try:
                page.evaluate("document.querySelector('button.font-normal.shadow-sm').click()")
                print("✅ Bouton de traduction cliqué")
                page.wait_for_timeout(5000)
            except Exception as e:
                print(f"❌ Erreur lors du clic sur le bouton de traduction : {e}")
                continue
            
            # Étape 3 : Attente et extraction du résultat
            # DÉFI TECHNIQUE : Le résultat de la traduction est chargé de manière asynchrone.
            # SOLUTION : Une boucle d'attente intelligente qui vérifie périodiquement
            # si le contenu de la zone de résultat a changé et contient du texte arabe.
            print("Attente de la traduction (processus asynchrone)...")
            max_attempts = 15
            for attempt in range(max_attempts):
                page.wait_for_timeout(1000) # Attendre 1 seconde entre chaque vérification
                
                # Exécution d'un script JS côté navigateur pour inspecter le DOM
                script_js_extraction = """
                () => {
                    const container = document.evaluate("/html/body/div/div[2]/div[4]", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                    if (!container) return null; // Le conteneur n'existe pas encore
                    const paragraphs = Array.from(container.querySelectorAll('p'));
                    for (const p of paragraphs) {
                        // Critère 1 : Le texte contient des caractères arabes
                        const hasArabic = Array.from(p.textContent).some(c => c.charCodeAt(0) >= 0x0600);
                        // Critère 2 : Le texte n'est pas un mot par défaut comme "Marocain"
                        if (hasArabic && p.textContent.trim() !== "Marocain") {
                            return p.textContent.trim();
                        }
                    }
                    return null; // Pas encore de traduction valide trouvée
                }
                """
                traduction_arabe = page.evaluate(script_js_extraction)

                if traduction_arabe:
                    print(f"✅ Traduction trouvée : {traduction_arabe}")
                    return traduction_arabe # Succès, on retourne le résultat

            print("❌ Délai d'attente dépassé, aucune traduction valide trouvée.")
            
        except Exception as e:
            print(f"Erreur lors de la tentative de traduction : {e}")
    
    print("❌ Toutes les tentatives ont échoué.")
    return None

# ------------------------------------------------------------------------------
# SECTION 3 : ORCHESTRATION DU SCRIPT
# ------------------------------------------------------------------------------

def charger_traductions_existantes(fichier_json):
    """
    Lit le fichier JSON de sortie pour identifier les phrases déjà traduites.
    Permet au script d'être relancé sans refaire le travail déjà accompli.

    Args:
        fichier_json (str): Chemin vers le fichier de sortie.

    Returns:
        set: Un ensemble de tuples (phrase, langue) déjà traités.
    """
    try:
        with open(fichier_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # On crée un 'set' pour une recherche rapide (complexité O(1))
            return {(t["source"], t["source_lang"]) for t in data.get("translations", [])}
    except (FileNotFoundError, json.JSONDecodeError):
        # Si le fichier n'existe pas ou est vide, on part de zéro.
        return set()

def sauvegarder_traduction_json(phrase, traduction_arabe, source_lang, fichier_json):
    """
    Ajoute une nouvelle traduction au fichier JSON de manière sécurisée.
    Lit d'abord le contenu existant, ajoute la nouvelle entrée, puis réécrit tout.

    Args:
        phrase (str): La phrase source.
        traduction_arabe (str): La traduction obtenue.
        source_lang (str): La langue de la phrase source.
        fichier_json (str): Le chemin du fichier JSON.
    """
    nouvelle_traduction = {
        "source_lang": source_lang,
        "source": phrase,
        "target_lang": "darija",
        "target": traduction_arabe if traduction_arabe else "Traduction non disponible"
    }
    try:
        with open(fichier_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"translations": []}

    data["translations"].append(nouvelle_traduction)

    with open(fichier_json, 'w', encoding='utf-8') as f:
        # ensure_ascii=False est crucial pour sauvegarder correctement les caractères arabes.
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Traduction sauvegardée dans {fichier_json}")


def traduire_phrases_excel(chemin_fichier_excel, source_lang="fr"):
    """
    Fonction principale qui orchestre le scraping pour un fichier Excel donné.
    
    Args:
        chemin_fichier_excel (str): Chemin vers le fichier .xlsx source.
        source_lang (str): Langue des phrases dans le fichier ('fr' ou 'en').
    """
    try:
        # Étape 1 : Lecture du fichier source
        df = pd.read_excel(chemin_fichier_excel)
        nom_colonne = 'Questions ou Affirmations'
        if nom_colonne not in df.columns:
            raise ValueError(f"La colonne '{nom_colonne}' est introuvable.")
        
        total_phrases = len(df)
        print(f"📊 {total_phrases} phrases à traiter depuis '{chemin_fichier_excel}'.")

        # Étape 2 : Préparation du fichier de sortie et de la reprise
        fichier_json = "translations.json"
        traductions_existantes = charger_traductions_existantes(fichier_json)
        print(f"📚 {len(traductions_existantes)} traductions déjà présentes dans '{fichier_json}'.")

        # Étape 3 : Initialisation de Playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, args=['--start-maximized'])
            page = browser.new_page(viewport={"width": 1920, "height": 1080})

            # On configure la page une seule fois au début pour la langue donnée
            if not configurer_page_traduction(page, source_lang=source_lang):
                raise Exception("Échec de la configuration initiale de la page.")
            
            # Étape 4 : Boucle principale de traduction
            for index, row in df.iterrows():
                phrase = str(row[nom_colonne]).strip()
                if not phrase:
                    continue
                
                # Vérification pour la reprise sur erreur
                if (phrase, source_lang) in traductions_existantes:
                    print(f"\n⏭️ Phrase déjà traduite ({index + 1}/{total_phrases}).")
                    continue
                
                print(f"\n🔄 Traduction {index + 1}/{total_phrases} ({source_lang}) : '{phrase}'")
                traduction = traduire_texte_dans_page(page, phrase, source_lang=source_lang)

                # Étape 5 : Sauvegarde du résultat
                if traduction:
                    sauvegarder_traduction_json(phrase, traduction, source_lang, fichier_json)
                    traductions_existantes.add((phrase, source_lang)) # Mise à jour pour la reprise
                else:
                    print(f"❌ Échec de la traduction pour : {phrase}")
                
                # Pause de politesse pour ne pas surcharger le serveur du site cible
                time.sleep(5) 

            print("\n✅ Traduction terminée pour ce fichier !")
            browser.close()
    except Exception as e:
        print(f"❌ Une erreur majeure est survenue lors du traitement du fichier {chemin_fichier_excel}: {str(e)}")


# ==============================================================================
# POINT D'ENTRÉE DU SCRIPT
# ==============================================================================
if __name__ == "__main__":
    print("🚀 Démarrage du script de scraping...")

    # Définition des fichiers d'entrée
    fichier_excel_fr = "data/darija_scrapping/data_synthetique/questions_fr_maroc.xlsx"
    fichier_excel_en = "data/darija_scrapping/data_synthetique/questions_en_morocco.xlsx"
    
    # Traitement séquentiel des fichiers
    print("\n--- Traitement du fichier français ---")
    if os.path.exists(fichier_excel_fr):
        traduire_phrases_excel(fichier_excel_fr, source_lang="fr")
    else:
        print(f"❌ Fichier non trouvé : {fichier_excel_fr}")

    print("\n--- Traitement du fichier anglais ---")
    if os.path.exists(fichier_excel_en):
        traduire_phrases_excel(fichier_excel_en, source_lang="en")
    else:
        print(f"❌ Fichier non trouvé : {fichier_excel_en}")

    print("\n🎉 Script terminé !")