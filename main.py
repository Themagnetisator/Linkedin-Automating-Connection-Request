from playwright.sync_api import sync_playwright
from connexion import connecter_linkedin
from recherche_et_connexion import lancer_recherche_et_connexion
import time
import os

# Dossier où le profil du navigateur sera sauvegardé entre les sessions.
# Cela permet à LinkedIn de reconnaître un navigateur "habituel" avec
# des cookies, un historique et une session persistante.
DOSSIER_PROFIL = os.path.join(os.path.dirname(__file__), "profil_navigateur")

def main():
    with sync_playwright() as p:

        print("Lancement du navigateur avec profil persistant...")

        contexte = p.chromium.launch_persistent_context(
            user_data_dir=DOSSIER_PROFIL,
            headless=False,
            slow_mo=400,
            args=[
                # Supprime le flag automation détectable par les sites
                "--disable-blink-features=AutomationControlled",
            ],
            # Imite un vrai navigateur Chrome sur macOS
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            locale="fr-FR",
        )

        page = contexte.new_page()

        # Masquer la propriété JavaScript window.navigator.webdriver
        # que LinkedIn utilise pour détecter l'automatisation
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        # Étape 1 : Connexion
        succes = connecter_linkedin(page)
        if not succes:
            print("Échec de la connexion. Arrêt.")
            contexte.close()
            return

        print("\nConnexion réussie. Démarrage de l'automatisation dans 3 secondes...")
        time.sleep(3)

        # Étape 2 : Recherche et connexions
        lancer_recherche_et_connexion(page)

        print("\nProgramme terminé. Appuyez sur ENTRÉE pour fermer le navigateur.")
        input()
        contexte.close()

if __name__ == "__main__":
    main()