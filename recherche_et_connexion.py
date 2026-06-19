import time
import random

# ============================================================
# CONFIGURATION — Edit these values to suit your needs
# ============================================================

MOTS_CLES = [
    "Bugatti",
    "Chef de projet",
    "Responsable marketing",
]

NOTE_CONNEXION = """Bonjour, peut-être que vous pouvez m'aider ?
Mon équipe représente la France
dans la plus grande compétition d'ingénierie… de l'histoire !!

Pouvons-nous voir si notre projet éco et éducatif s'aligne avec vos objectifs ?

"""

# Nombre maximum d'invitations envoyées par session
LIMITE_CONNEXIONS_PAR_SESSION = 40

# Délai entre deux invitations consécutives (secondes)
PAUSE_MIN_ENTRE_CONNEXIONS = 8
PAUSE_MAX_ENTRE_CONNEXIONS = 18

# Pause longue périodique pour imiter un comportement humain
# Une pause longue est déclenchée tous les N envois
PAUSE_LONGUE_TOUS_LES_N     = 10
PAUSE_LONGUE_DUREE_MIN      = 45
PAUSE_LONGUE_DUREE_MAX      = 90

# Délai entre deux pages de résultats (secondes)
PAUSE_MIN_ENTRE_PAGES       = 4
PAUSE_MAX_ENTRE_PAGES       = 9

# Délai entre deux mots-clés (secondes)
PAUSE_MIN_ENTRE_MOTS_CLES   = 10
PAUSE_MAX_ENTRE_MOTS_CLES   = 20

# ============================================================


def pause_aleatoire(min_sec, max_sec, raison=""):
    duree = round(random.uniform(min_sec, max_sec), 1)
    if raison:
        print(f"  ⏱  Pause {raison} : {duree}s")
    time.sleep(duree)


def construire_url_recherche(mot_cle, numero_page):
    """
    Construit l'URL LinkedIn People Search avec filtre France.
    geoUrn=105015875 correspond à la France sur LinkedIn.
    """
    mot_encode = mot_cle.replace(" ", "%20")
    return (
        f"https://www.linkedin.com/search/results/people/"
        f"?keywords={mot_encode}"
        f"&geoUrn=%5B%22105015875%22%5D"
        f"&origin=FACETED_SEARCH"
        f"&page={numero_page}"
    )


def scroll_progressif(page):
    """
    Scrolle en utilisant mouse.wheel() qui envoie de vrais événements
    de défilement au navigateur, contrairement à window.scrollTo()
    qui cible l'objet window et non le conteneur de scroll interne de LinkedIn.
    """
    print("  Scroll progressif pour charger tous les profils...")

    # Cliquer au centre de la page pour garantir que le focus
    # est sur le bon conteneur avant de scroller
    try:
        page.mouse.click(640, 400)
        time.sleep(0.5)
    except:
        pass

    # Scroller vers le bas en 10 étapes avec variation aléatoire
    for _ in range(10):
        page.mouse.wheel(0, random.randint(350, 550))
        time.sleep(random.uniform(0.4, 0.9))

    # Attendre que le contenu lazy-loadé finisse de se charger
    time.sleep(2)

    # Remonter en haut pour que tous les boutons soient dans le viewport
    page.evaluate("window.scrollTo(0, 0)")
    time.sleep(0.8)

def get_nombre_pages(page):
    """
    Retourne une valeur sentinelle élevée.
    La vraie fin de pagination est détectée dynamiquement dans la boucle
    via page_a_des_resultats(), ce qui est plus fiable que de prédire un total.
    """
    return 100

def page_a_des_resultats(page):
    """
    Vérifie si la page courante contient des cartes de profil LinkedIn.
    Utilisé pour détecter la fin réelle de la pagination.
    """
    selecteurs = [
        "li.reusable-search__result-container",
        "div.entity-result",
        "li[data-occludable-job-id]",
        "ul.reusable-search__entity-result-list li",
    ]
    for sel in selecteurs:
        try:
            count = page.locator(sel).count()
            if count > 0:
                return True
        except:
            continue

    # Vérifier si LinkedIn affiche un message "Aucun résultat"
    try:
        texte_page = page.inner_text("main") or ""
        mots_vides = [
            "no results", "aucun résultat",
            "we couldn't find", "nous n'avons pas trouvé"
        ]
        if any(mot in texte_page.lower() for mot in mots_vides):
            return False
    except:
        pass

    # Par défaut supposer qu'il y a des résultats
    return True

def trouver_boutons_connect(page):
    """
    Trouve tous les boutons 'Connect' visibles sur la page courante.
    Utilise plusieurs stratégies de sélection car LinkedIn utilise
    des structures HTML complexes avec du texte imbriqué dans des spans.
    """
    boutons_valides = []

    # Stratégie 1 — aria-label contenant "Invite" ou "Connect"
    # LinkedIn nomme souvent ces boutons avec le nom du profil dans l'aria-label
    # ex: aria-label="Invite Jean Dupont to connect"
    try:
        selecteurs_aria = [
            "button[aria-label*='Invite']",
            "button[aria-label*='invite']",
            "button[aria-label*='Connect']",
            "button[aria-label*='connect']",
            "button[aria-label*='Se connecter']",
            "button[aria-label*='connecter']",
        ]
        for selecteur in selecteurs_aria:
            elements = page.locator(selecteur).all()
            for el in elements:
                try:
                    if el.is_visible():
                        # Vérifier que ce n'est pas un bouton "Message" ou "Pending"
                        label = (el.get_attribute("aria-label") or "").lower()
                        if any(mot in label for mot in ["message", "pending", "follow", "unfollow"]):
                            continue
                        boutons_valides.append(el)
                except:
                    continue
    except:
        pass

    # Stratégie 2 — boutons dont le span interne contient "Connect"
    # LinkedIn imbrique le texte dans <span aria-hidden="true"> à l'intérieur du bouton
    if not boutons_valides:
        try:
            tous_boutons = page.locator("button").all()
            for btn in tous_boutons:
                try:
                    if not btn.is_visible():
                        continue
                    # Lire le texte complet incluant les spans enfants
                    texte = btn.inner_text().strip().lower()
                    if texte in ["connect", "se connecter"]:
                        boutons_valides.append(btn)
                    elif texte in ["message", "pending", "en attente", "follow", "following"]:
                        continue
                except:
                    continue
        except:
            pass

    # Dédoublonner par position sur la page
    vus = set()
    resultat = []
    for btn in boutons_valides:
        try:
            boite = btn.bounding_box()
            if boite:
                cle = (round(boite["x"]), round(boite["y"]))
                if cle not in vus:
                    vus.add(cle)
                    resultat.append(btn)
        except:
            resultat.append(btn)

    return resultat


def envoyer_connexion(page, compteur_total):
    """
    Scrolle la page, trouve les boutons Connect et envoie les demandes.
    """
    scroll_progressif(page)

    boutons = trouver_boutons_connect(page)
    print(f"  {len(boutons)} bouton(s) 'Connect' trouvé(s).")

    for bouton in boutons:
        if compteur_total >= LIMITE_CONNEXIONS_PAR_SESSION:
            print(f"\n  ⚠️  Limite de {LIMITE_CONNEXIONS_PAR_SESSION} connexions atteinte.")
            return compteur_total

        try:
            # Scroller jusqu'au bouton pour qu'il soit dans le viewport
            bouton.scroll_into_view_if_needed()
            time.sleep(random.uniform(0.5, 1.0))

            if not bouton.is_visible():
                continue

            aria = bouton.get_attribute("aria-label") or bouton.inner_text()
            print(f"\n  → Clic sur : '{aria.strip()[:60]}'")
            bouton.click()
            time.sleep(random.uniform(1.5, 2.5))

            # --- Chercher le bouton "Add a note" dans la modale ---
            bouton_note = None
            selecteurs_note = [
                "button[aria-label='Add a note']",
                "button[aria-label='Ajouter une note']",
                "button:has-text('Add a note')",
                "button:has-text('Ajouter une note')",
            ]
            for sel in selecteurs_note:
                try:
                    el = page.locator(sel)
                    if el.is_visible(timeout=2000):
                        bouton_note = el
                        break
                except:
                    continue

            if bouton_note is None:
                print("    ⚠️  Modale non trouvée ou bouton 'Add a note' absent.")
                # Fermer la modale si elle est ouverte
                try:
                    page.keyboard.press("Escape")
                    time.sleep(0.8)
                except:
                    pass
                continue

            bouton_note.click()
            print("    Note : fenêtre ouverte.")
            time.sleep(random.uniform(1.0, 2.0))

            # --- Champ texte de la note ---
            champ_note = None
            selecteurs_champ = [
                "textarea[name='message']",
                "textarea[name='message-body']",
                "div[role='textbox']",
                "textarea",
            ]
            for sel in selecteurs_champ:
                try:
                    el = page.locator(sel)
                    if el.is_visible(timeout=2000):
                        champ_note = el
                        break
                except:
                    continue

            if champ_note is None:
                print("    ⚠️  Champ texte de la note non trouvé.")
                try:
                    page.keyboard.press("Escape")
                except:
                    pass
                continue

            champ_note.click()
            time.sleep(0.5)
            champ_note.type(NOTE_CONNEXION, delay=random.randint(30, 70))
            print("    Note : texte saisi.")
            time.sleep(random.uniform(0.8, 1.5))

            # --- Bouton Send ---
            bouton_send = None
            selecteurs_send = [
                "button[aria-label='Send now']",
                "button[aria-label='Envoyer maintenant']",
                "button:has-text('Send now')",
                "button:has-text('Send')",
                "button:has-text('Envoyer')",
            ]
            for sel in selecteurs_send:
                try:
                    el = page.locator(sel)
                    if el.is_visible(timeout=2000):
                        bouton_send = el
                        break
                except:
                    continue

            if bouton_send is None:
                print("    ⚠️  Bouton 'Send' non trouvé.")
                try:
                    page.keyboard.press("Escape")
                except:
                    pass
                continue

            bouton_send.click()
            print("    ✅ Demande envoyée avec note.")
            compteur_total += 1

            # --- Pause longue périodique ---
            if compteur_total % PAUSE_LONGUE_TOUS_LES_N == 0:
                duree = round(random.uniform(PAUSE_LONGUE_DUREE_MIN, PAUSE_LONGUE_DUREE_MAX))
                print(f"\n  ☕  Pause longue ({duree}s)...")
                time.sleep(duree)
            else:
                pause_aleatoire(
                    PAUSE_MIN_ENTRE_CONNEXIONS,
                    PAUSE_MAX_ENTRE_CONNEXIONS,
                    "entre connexions"
                )

        except Exception as e:
            print(f"  ⚠️  Erreur : {e}")
            try:
                page.keyboard.press("Escape")
                time.sleep(0.5)
            except:
                pass
            continue

    return compteur_total


def lancer_recherche_et_connexion(page):
    compteur_total = 0

    for index_mot, mot_cle in enumerate(MOTS_CLES):

        if compteur_total >= LIMITE_CONNEXIONS_PAR_SESSION:
            print(f"\n🛑 Limite globale atteinte. Fin du programme.")
            break

        print(f"\n{'='*60}")
        print(f"🔍 Recherche : '{mot_cle}' ({index_mot + 1}/{len(MOTS_CLES)})")
        print(f"{'='*60}")

        url_page_1 = construire_url_recherche(mot_cle, 1)
        page.goto(url_page_1, wait_until="domcontentloaded")
        time.sleep(random.uniform(3, 5))

        nombre_pages = get_nombre_pages(page)

        for numero_page in range(1, nombre_pages + 1):

            if compteur_total >= LIMITE_CONNEXIONS_PAR_SESSION:
                break

            print(f"\n  📄 Page {numero_page}/{nombre_pages} — '{mot_cle}'")

            if numero_page > 1:
                url = construire_url_recherche(mot_cle, numero_page)
                page.goto(url, wait_until="domcontentloaded")
                pause_aleatoire(PAUSE_MIN_ENTRE_PAGES, PAUSE_MAX_ENTRE_PAGES, "entre pages")

            # Arrêt dynamique : si LinkedIn ne retourne plus de résultats,
            # inutile de continuer la pagination pour ce mot-clé
            if not page_a_des_resultats(page):
                print(f"  Aucun résultat sur la page {numero_page}. Fin de la pagination.")
                break

            compteur_total = envoyer_connexion(page, compteur_total)


        if index_mot < len(MOTS_CLES) - 1:
            pause_aleatoire(
                PAUSE_MIN_ENTRE_MOTS_CLES,
                PAUSE_MAX_ENTRE_MOTS_CLES,
                "entre mots-clés"
            )

    print(f"\n✅ Session terminée. Total de demandes envoyées : {compteur_total}")