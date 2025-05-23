from playwright.sync_api import sync_playwright
import json
import time
import os
import pandas as pd


def traduire_texte_traductordarija(phrase, url_base="https://www.learnmoroccan.com/fr"):
    print(f"Tentative de traduction de : '{phrase}'")
    traduction_arabe = None

    try:
        with sync_playwright() as p:
            print("Lancement du navigateur Chromium...")
            browser = p.chromium.launch(
                headless=False,    # Mode visible pour déboguer
                args=['--start-maximized']  # Démarrer en plein écran
            )
            page = browser.new_page(viewport={"width": 1920, "height": 1080})  # Définir une résolution HD

            # Commencer par la page d'accueil pour la connexion
            print("Accès à la page d'accueil pour connexion...")
            page.goto(url_base)
            page.wait_for_timeout(2000)

            # Se connecter
            print("Tentative de connexion...")
            if not se_connecter(page):
                print("La connexion a échoué, tentative de continuer quand même...")

            # Rediriger vers la page du traducteur
            url_traducteur = f"{url_base}/translator"
            print(f"Accès à la page du traducteur : {url_traducteur}")
            page.goto(url_traducteur)
            page.wait_for_timeout(2000)
            print("Page du traducteur chargée")

            # Gérer le bouton initial inversion de langue
            try:
                print("Vérification de la présence du bouton initial d'inversion de langue...")
                bouton_selector = "button.shadow-md.shadow-\\[rgba\\(0\\,0\\,0\\,0\\.01\\)\\].border.border-\\[\\#ECECEC\\].mx-2.p-\\[17px\\].rounded-2xl.bg-white.hover\\:bg-lighter.duration-150[aria-label='échanger les langues'][title='échanger les langues']"
                page.wait_for_selector(bouton_selector, state="visible", timeout=5000)
                print("Bouton initial détecté, clic sur le bouton...")
                page.locator(bouton_selector).click()
                print("Bouton initial cliqué")
                page.wait_for_timeout(1000)
            except Exception as e:
                print(f"Erreur lors de la gestion du bouton initial : {e}, poursuite du script")

            # Sélectionner la langue française depuis le menu déroulant
            print("Gestion du menu déroulant de sélection de langue...")
            print("Ouverture du menu déroulant de langues...")
            page.locator("xpath=/html/body/div/div[2]/div[2]/div[1]/div[1]").click()
            page.wait_for_timeout(1000)
            print("Menu déroulant ouvert")
            print("Sélection de la langue française dans le menu...")
            page.locator("div:has-text('Français'):not(:has(div:has-text('Français')))").first.click()
            print("Langue française sélectionnée")
            page.wait_for_timeout(1000)

            # Activer le bouton toggle
            print("Activation du bouton toggle...")
            page.locator("xpath=/html/body/div/div[2]/div[3]/div/label/div/div").click()
            print("Bouton toggle activé")
            page.wait_for_timeout(1000)

            # Entrer le texte à traduire
            print(f"Saisie du texte : '{phrase}'")
            page.fill("textarea.pl-1.w-full.bg-white.outline-none.overflow-hidden.pt-2.resize-none.min-h-28.sm\\:min-h-48", phrase)
            page.wait_for_timeout(1000)

            # Cliquer sur le bouton de traduction
            print("Clic sur le bouton de traduction")
            try:
                # Attendre que le bouton soit cliquable
                page.wait_for_selector("xpath=/html/body/div/div[2]/button", state="visible", timeout=5000)
                # Attendre un peu avant de cliquer pour s'assurer que la page est prête
                page.wait_for_timeout(2000)
                # Cliquer sur le bouton avec JavaScript pour éviter les problèmes de navigation
                page.evaluate("document.querySelector('button.font-normal.shadow-sm').click()")
                print("✅ Bouton de traduction cliqué")
                # Attendre plus longtemps après le clic pour laisser le temps à la traduction de s'initialiser
                page.wait_for_timeout(5000)
            except Exception as e:
                print(f"❌ Erreur lors du clic sur le bouton de traduction : {e}")
                return None
            
            print("Attente de 8 secondes pour laisser le temps au site de traiter la demande...")
            page.wait_for_timeout(8000)  # 8 secondes d'attente

            # Récupérer directement la traduction en arabe
            print("Récupération directe de la traduction en arabe...")

            script_xpath_exact = """
            () => {
                try {
                    const xpath = "/html/body/div/div[2]/div[4]/p[2]";
                    const result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                    return result ? result.textContent : null;
                } catch (e) {
                    return "Erreur: " + e.message;
                }
            }
            """
            traduction_arabe = page.evaluate(script_xpath_exact)

            if traduction_arabe and not traduction_arabe.startswith("Erreur:") and traduction_arabe != "Marocain":
                print(f"Traduction trouvée avec le XPath exact : {traduction_arabe}")
            else:
                print(f"Le XPath exact a retourné : {traduction_arabe}")
                traduction_arabe = None

                print("Tentative avec d'autres approches...")
                html_content = page.content()
                with open("page_debug.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                print("HTML de la page sauvegardé pour analyse")

                script_all_paragraphs = """
                () => {
                    const paragraphs = Array.from(document.querySelectorAll('p'));
                    return paragraphs.map((p, index) => {
                        return {
                            index: index,
                            text: p.textContent,
                            hasArabic: Array.from(p.textContent).some(c => c.charCodeAt(0) >= 0x0600 && c.charCodeAt(0) <= 0x06FF)
                        };
                    });
                }
                """
                all_paragraphs = page.evaluate(script_all_paragraphs)
                for p in all_paragraphs:
                    if p["hasArabic"] and p["text"] != "Marocain":
                        traduction_arabe = p["text"]
                        print(f"Traduction en arabe trouvée (paragraphe {p['index']}): {traduction_arabe}")
                        break

                if not traduction_arabe:
                    print("Aucune traduction trouvée dans l'analyse des paragraphes, essai avec d'autres XPath...")
                    xpath_options = [
                        "/html/body/div/div[2]/div[4]/p[1]",
                        "//div[contains(@class, 'mt-4')]/p[1]",
                        "//div[contains(@class, 'mt-4')]/p[2]"
                    ]
                    for xpath in xpath_options:
                        script_xpath = f"""
                        () => {{
                            try {{
                                const xpath = "{xpath}";
                                const result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                                return result ? result.textContent : null;
                            }} catch (e) {{
                                return "Erreur: " + e.message;
                            }}
                        }}
                        """
                        result = page.evaluate(script_xpath)
                        if result and not result.startswith("Erreur:") and result != "Marocain" and any(ord(c) >= 0x0600 and ord(c) <= 0x06FF for c in result):
                            traduction_arabe = result
                            print(f"Traduction en arabe trouvée via XPath {xpath}: {traduction_arabe}")
                            break
                        else:
                            print(f"XPath {xpath} a retourné: {result}")

            print("Finalisation de la traduction")
            browser.close()
            return traduction_arabe
    except Exception as e:
        print(f"Erreur lors de la traduction : {e}")
        return None


def sauvegarder_traduction_json(phrase, traduction_arabe, source_lang="fr", fichier_json="translations.json"):
    """
    Sauvegarde la traduction dans un fichier JSON structuré.
    
    Args:
        phrase (str): La phrase à traduire
        traduction_arabe (str): La traduction en caractères arabes
        source_lang (str): La langue source ('fr' pour français, 'en' pour anglais)
        fichier_json (str): Le chemin du fichier JSON où sauvegarder les traductions
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
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Traduction sauvegardée dans {fichier_json}")


def se_connecter(page):
    """
    Effectue la connexion sur le site avec les identifiants fournis.
    
    Args:
        page: L'instance de page Playwright
    
    Returns:
        bool: True si la connexion a réussi, False sinon
    """
    try:
        print("Clic sur le bouton 'Se connecter'...")
        page.locator("xpath=/html/body/header/div/div[2]/div/a[2]/button").click()
        page.wait_for_timeout(2000)
        print("Saisie de l'identifiant...")
        page.locator("xpath=/html/body/section[1]/div/form/div[1]/input").fill("faridigouti@gmail.com")
        page.wait_for_timeout(1000)
        print("Saisie du mot de passe...")
        page.locator("xpath=/html/body/section[1]/div/form/div[2]/input").fill("34635263")
        page.wait_for_timeout(1000)
        print("Clic sur le bouton de validation...")
        page.locator("xpath=/html/body/section[1]/div/form/button").click()
        page.wait_for_timeout(3000)
        return True
    except Exception as e:
        print(f"Erreur lors de la connexion : {e}")
        return False


def configurer_page_traduction(page, url_base="https://www.learnmoroccan.com/fr", source_lang="fr"):
    """
    Configure la page pour la traduction (connexion et paramètres initiaux).
    
    Args:
        page: L'instance de page Playwright
        url_base: L'URL de base du site
        source_lang: La langue source ('fr' pour français, 'en' pour anglais)
    
    Returns:
        bool: True si la configuration a réussi, False sinon
    """
    try:
        print("Accès à la page d'accueil pour connexion...")
        page.goto(url_base)
        page.wait_for_timeout(2000)
        if not se_connecter(page):
            return False
        url_traducteur = f"{url_base}/translator"
        print(f"Accès à la page du traducteur : {url_traducteur}")
        page.goto(url_traducteur)
        page.wait_for_timeout(2000)
        try:
            bouton_selector = "button.shadow-md.shadow-\\[rgba\\(0\\,0\\,0\\,0\\.01\\)\\].border.border-\\[\\#ECECEC\\].mx-2.p-\\[17px\\].rounded-2xl.bg-white.hover\\:bg-lighter.duration-150[aria-label='échanger les langues'][title='échanger les langues']"
            page.wait_for_selector(bouton_selector, state="visible", timeout=5000)
            page.locator(bouton_selector).click()
            page.wait_for_timeout(1000)
        except Exception as e:
            print(f"Erreur lors de la gestion du bouton initial : {e}, poursuite du script")

        # Sélection de la langue source (français ou anglais)
        langue = "Français" if source_lang == "fr" else "Anglais"
        print(f"Sélection de la langue {langue}...")
        page.locator("xpath=/html/body/div/div[2]/div[2]/div[1]/div[1]").click()
        page.wait_for_timeout(1000)
        page.locator(f"div:has-text('{langue}'):not(:has(div:has-text('{langue}')))").first.click()
        print(f"Langue {langue} sélectionnée")
        page.wait_for_timeout(1000)

        # Activer le bouton toggle
        page.locator("xpath=/html/body/div/div[2]/div[3]/div/label/div/div").click()
        page.wait_for_timeout(1000)
        return True
    except Exception as e:
        print(f"Erreur lors de la configuration : {e}")
        return False


def traduire_texte_dans_page(page, phrase, max_retries=3, source_lang="fr"):
    """
    Traduit une phrase en utilisant une page déjà configurée.
    
    Args:
        page: L'instance de page Playwright déjà configurée
        phrase: La phrase à traduire
        max_retries: Nombre maximum de tentatives de traduction
        source_lang: La langue source ('fr' pour français, 'en' pour anglais)
    
    Returns:
        str: La traduction en arabe ou None si échec
    """
    url_base = "https://www.learnmoroccan.com/fr"
    url_traducteur = f"{url_base}/translator"

    for retry in range(max_retries):
        try:
            if retry > 0:
                print(f"\n🔄 Tentative {retry + 1}/{max_retries} - Réinitialisation de la page...")
                # Reconfigurer la page sans passer par la page d'accueil
                if not configurer_page_traduction(page, source_lang=source_lang):
                    print("❌ Échec de la configuration de la page")
                    continue

            # Effacer d'abord le contenu existant
            print("Nettoyage du champ de texte...")
            textarea_selector = "textarea.pl-1.w-full.bg-white.outline-none.overflow-hidden.pt-2.resize-none.min-h-28.sm\\:min-h-48"
            page.fill(textarea_selector, "")
            page.wait_for_timeout(500)

            print(f"Saisie du texte : '{phrase}'")
            page.fill(textarea_selector, phrase)
            page.wait_for_timeout(1000)
            
            print("Clic sur le bouton de traduction")
            try:
                # Attendre que le bouton soit cliquable
                page.wait_for_selector("xpath=/html/body/div/div[2]/button", state="visible", timeout=5000)
                # Attendre un peu avant de cliquer pour s'assurer que la page est prête
                page.wait_for_timeout(2000)
                # Cliquer sur le bouton avec JavaScript pour éviter les problèmes de navigation
                page.evaluate("document.querySelector('button.font-normal.shadow-sm').click()")
                print("✅ Bouton de traduction cliqué")
                # Attendre plus longtemps après le clic pour laisser le temps à la traduction de s'initialiser
                page.wait_for_timeout(5000)
            except Exception as e:
                print(f"❌ Erreur lors du clic sur le bouton de traduction : {e}")
                continue
            
            print("Attente de la traduction...")
            max_attempts = 15  # Augmenter le nombre de tentatives
            attempt = 0
            traduction_arabe = None
            dernier_texte = None
            
            while attempt < max_attempts:
                try:
                    # Attendre que le conteneur de traduction soit visible
                    page.wait_for_selector("xpath=/html/body/div/div[2]/div[4]", state="visible", timeout=3000)
                    
                    # Récupérer tous les paragraphes dans le conteneur de traduction
                    script_all_paragraphs = """
                    () => {
                        const container = document.evaluate("/html/body/div/div[2]/div[4]", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                        if (!container) return [];
                        const paragraphs = Array.from(container.querySelectorAll('p'));
                        return paragraphs.map(p => ({
                            text: p.textContent,
                            hasArabic: Array.from(p.textContent).some(c => c.charCodeAt(0) >= 0x0600 && c.charCodeAt(0) <= 0x06FF)
                        }));
                    }
                    """
                    paragraphs = page.evaluate(script_all_paragraphs)
                    
                    # Chercher le premier paragraphe contenant du texte arabe
                    texte_actuel = None
                    for p in paragraphs:
                        if p["hasArabic"] and p["text"] != "Marocain":
                            texte_actuel = p["text"]
                            break
                        elif "traduction devrait apparaître" in p["text"].lower():
                            texte_actuel = "en_attente"
                            break
                    
                    # Si le texte n'a pas changé depuis la dernière vérification, continuer à attendre
                    if texte_actuel == dernier_texte:
                        print(f"Tentative {attempt + 1}/{max_attempts} - Attente de changement...")
                        page.wait_for_timeout(1000)
                        attempt += 1
                        continue
                    
                    # Si on trouve un nouveau texte arabe valide
                    if texte_actuel and texte_actuel != "en_attente":
                        traduction_arabe = texte_actuel
                        print(f"✅ Traduction trouvée : {traduction_arabe}")
                        return traduction_arabe
                    
                    # Mettre à jour le dernier texte vu
                    dernier_texte = texte_actuel
                    print(f"Tentative {attempt + 1}/{max_attempts} - Attente de la traduction...")
                    page.wait_for_timeout(1000)
                    attempt += 1
                    
                except Exception as e:
                    print(f"Erreur lors de la tentative {attempt + 1} : {e}")
                    attempt += 1
            
            if retry < max_retries - 1:
                print("❌ Échec de la traduction, nouvelle tentative...")
                continue
        except Exception as e:
            print(f"Erreur lors de la traduction : {e}")
            if retry < max_retries - 1:
                continue
    
    print("❌ Toutes les tentatives ont échoué - Impossible d'obtenir une traduction valide")
    return None


def charger_traductions_existantes(fichier_json):
    """
    Charge les traductions existantes depuis le fichier JSON.
    
    Args:
        fichier_json (str): Chemin vers le fichier JSON des traductions
    
    Returns:
        set: Ensemble des phrases déjà traduites
    """
    try:
        with open(fichier_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {(t["source"], t["source_lang"]) for t in data.get("translations", [])}
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def traduire_phrases_excel(chemin_fichier_excel, source_lang="fr"):
    """
    Traduit toutes les phrases d'un fichier Excel.
    
    Args:
        chemin_fichier_excel (str): Chemin vers le fichier Excel contenant les phrases à traduire
        source_lang (str): La langue source ('fr' pour français, 'en' pour anglais)
    """
    try:
        print(f"Lecture du fichier Excel : {chemin_fichier_excel}")
        df = pd.read_excel(chemin_fichier_excel)
        
        # Utiliser le même nom de colonne pour les deux langues
        nom_colonne = 'Questions ou Affirmations'
        
        if nom_colonne not in df.columns:
            raise ValueError(f"❌ La colonne '{nom_colonne}' n'existe pas dans le fichier Excel")
        print(f"✅ Utilisation de la colonne : {nom_colonne}")
        total_phrases = len(df)
        print(f"📊 Nombre total de phrases à traduire : {total_phrases}")

        # Utiliser un seul fichier JSON pour toutes les traductions
        dossier_script = os.path.dirname(os.path.abspath(__file__))
        fichier_json = os.path.join(dossier_script, "translations.json")

        # Charger les traductions existantes
        traductions_existantes = charger_traductions_existantes(fichier_json)
        print(f"📚 Nombre de traductions déjà effectuées : {len(traductions_existantes)}")

        with sync_playwright() as p:
            print("Lancement du navigateur Chromium...")
            browser = p.chromium.launch(
                headless=False,
                args=['--start-maximized']
            )
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            if not configurer_page_traduction(page, source_lang=source_lang):
                raise Exception("Échec de la configuration de la page")
            
            for index, row in df.iterrows():
                phrase = str(row[nom_colonne]).strip()
                if not phrase:
                    continue
                
                # Vérifier si la phrase a déjà été traduite
                if (phrase, source_lang) in traductions_existantes:
                    print(f"\n⏭️ Phrase déjà traduite ({index + 1}/{total_phrases})")
                    print(f"📝 Phrase source ({source_lang}): {phrase}")
                    continue
                
                print(f"\n🔄 Traduction {index + 1}/{total_phrases}")
                print(f"📝 Phrase source ({source_lang}): {phrase}")
                traduction = traduire_texte_dans_page(page, phrase, source_lang=source_lang)
                if traduction:
                    print(f"✅ Traduction : {traduction}")
                    sauvegarder_traduction_json(phrase, traduction, source_lang, fichier_json)
                    # Mettre à jour l'ensemble des traductions existantes
                    traductions_existantes.add((phrase, source_lang))
                else:
                    print(f"❌ Échec de la traduction pour : {phrase}")
                time.sleep(5)
            print("\n✅ Traduction terminée !")
            browser.close()
    except Exception as e:
        print(f"❌ Erreur lors du traitement : {str(e)}")


if __name__ == "__main__":
    print("🚀 Démarrage du script de traduction...")
    print(f"📂 Répertoire de travail : {os.getcwd()}")

    # Définition des chemins des fichiers Excel
    fichier_excel_fr = "../agregation/data_xlsx/questions_fr.xlsx"
    fichier_excel_en = "../agregation/data_xlsx/questions_en.xlsx"

    # Créer un fichier JSON unique pour toutes les traductions
    dossier_script = os.path.dirname(os.path.abspath(__file__))
    fichier_json = os.path.join(dossier_script, "translations.json")
    if not os.path.exists(fichier_json):
        with open(fichier_json, 'w', encoding='utf-8') as f:
            json.dump({"translations": []}, f, ensure_ascii=False, indent=2)

    # 1. Traitement du fichier français
    print("\n🇫🇷 Traitement du fichier français...")
    print(f"📄 Fichier : {fichier_excel_fr}")
    if os.path.exists(fichier_excel_fr):
        traduire_phrases_excel(fichier_excel_fr, source_lang="fr")
    else:
        print(f"❌ Fichier non trouvé : {fichier_excel_fr}")

    # 2. Traitement du fichier anglais
    print("\n🇬🇧 Traitement du fichier anglais...")
    print(f"📄 Fichier : {fichier_excel_en}")
    if os.path.exists(fichier_excel_en):
        traduire_phrases_excel(fichier_excel_en, source_lang="en")
    else:
        print(f"❌ Fichier non trouvé : {fichier_excel_en}")

    print("\n✅ Script terminé - Les deux fichiers ont été traités !")