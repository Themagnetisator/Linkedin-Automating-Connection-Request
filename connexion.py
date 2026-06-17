from playwright.sync_api import sync_playwright
import time

EMAIL        = "teamceleritasracing@gmail.com"
MOT_DE_PASSE = "@TheGreatestTeamTeamWILD67"

def connecter_linkedin():

    with sync_playwright() as p:

        navigateur = p.chromium.launch(headless=False, slow_mo=600)
        page = navigateur.new_page()

        print("Ouverture de LinkedIn...")
        page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")

        time.sleep(4)

        print("Recherche du champ email...")
        champ_email = None
        for inp in page.locator("input").all():
            try:
                if inp.is_visible():
                    champ_email = inp
                    print("Champ email trouvé.")
                    break
            except:
                continue

        if champ_email is None:
            print("Champ email non trouvé.")
            input()
            navigateur.close()
            return

        champ_email.click()
        time.sleep(0.5)
        champ_email.type(EMAIL, delay=80)
        print("Email rempli.")

        time.sleep(2)

        print("Recherche du champ mot de passe...")
        champ_mdp = None
        for inp in page.locator("input").all():
            try:
                if inp.is_visible() and inp.get_attribute("type") == "password":
                    champ_mdp = inp
                    print("Champ mot de passe trouvé.")
                    break
            except:
                continue

        if champ_mdp is None:
            inputs_visibles = []
            for inp in page.locator("input").all():
                try:
                    if inp.is_visible():
                        inputs_visibles.append(inp)
                except:
                    continue
            if len(inputs_visibles) >= 2:
                champ_mdp = inputs_visibles[1]
                print("Deuxième champ visible utilisé pour le mot de passe.")
            else:
                print("Champ mot de passe non trouvé.")
                input()
                navigateur.close()
                return

        champ_mdp.click()
        time.sleep(0.5)
        champ_mdp.type(MOT_DE_PASSE, delay=80)
        print("Mot de passe rempli.")

        time.sleep(1)

        print("Recherche du bouton S'identifier...")
        bouton_clique = False

        for btn in page.locator("button").all():
            try:
                if btn.is_visible():
                    texte = btn.inner_text().strip()
                    print(f"  Bouton visible : '{texte}'")
                    mots_exclus = ["apple", "google"]
                    if any(mot in texte.lower() for mot in mots_exclus):
                        print("  → Bouton ignoré (connexion tierce partie)")
                        continue
                    mots_cibles = ["s'identifier", "sign in", "se connecter", "login"]
                    if any(mot in texte.lower() for mot in mots_cibles):
                        btn.click()
                        print(f"Bouton cliqué : '{texte}'")
                        bouton_clique = True
                        break
            except:
                continue

        if not bouton_clique:
            print("Bouton non trouvé. Appui sur ENTRÉE dans le champ mot de passe...")
            champ_mdp.press("Enter")
            print("Touche ENTRÉE pressée.")

        time.sleep(5)
        print("Terminé. Appuyez sur ENTRÉE pour fermer le navigateur.")
        input()
        navigateur.close()

if __name__ == "__main__":
    connecter_linkedin()
