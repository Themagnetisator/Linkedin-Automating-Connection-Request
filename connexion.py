from playwright.sync_api import sync_playwright
import time
import json
import os
import signal
import sys

# ─────────────────────────────────────────────
# CONFIGURATION — Edit these values
# ─────────────────────────────────────────────

EMAIL        = "teamceleritasracing@gmail.com"
MOT_DE_PASSE = "@TheGreatestTeamTeamWILD67"

KEYWORDS = [
    "ingénieur mécanique",
    "chef de projet",
    "directeur technique",
    # Add as many keywords as you want
]

NOTE_TEXT = (
    "Bonjour, je souhaite rejoindre votre réseau professionnel. "
    "N'hésitez pas à me contacter si vous souhaitez échanger."
)

PROGRESS_FILE = os.path.join(os.path.dirname(__file__), "progress.json")

# ─────────────────────────────────────────────
# STATE MANAGEMENT
# ─────────────────────────────────────────────

def load_progress():
    """Load saved progress from disk, or return a fresh start state."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            data = json.load(f)
            print(f"[RESUME] Reprise à partir du mot-clé #{data['keyword_index']} "
                  f"({KEYWORDS[data['keyword_index']]}), "
                  f"page {data['page']}, profil #{data['profile_index']}")
            return data
    return {"keyword_index": 0, "page": 1, "profile_index": 0}

def save_progress(state):
    """Persist current progress to disk."""
    with open(PROGRESS_FILE, "w") as f:
        json.dump(state, f, indent=2)

def reset_progress():
    """Called when the entire list has been completed."""
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)
    print("[DONE] Tous les mots-clés ont été traités. Progression réinitialisée.")

# ─────────────────────────────────────────────
# GRACEFUL SHUTDOWN
# ─────────────────────────────────────────────

# This global holds a reference to the current state so the signal
# handler can save it even when triggered from outside the main loop.
_current_state = None
_navigateur    = None

def handle_interrupt(sig, frame):
    """
    Called when the user presses Ctrl+C.
    Saves progress and closes the browser cleanly before exiting.
    """
    print("\n[INTERRUPTION] Arrêt propre en cours...")
    if _current_state is not None:
        save_progress(_current_state)
        print(f"[SAVED] Progression sauvegardée : {_current_state}")
    if _navigateur is not None:
        try:
            _navigateur.close()
        except Exception:
            pass
    print("[EXIT] Programme arrêté proprement. Relancez lancer.sh pour reprendre.")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_interrupt)

# ─────────────────────────────────────────────
# LINKEDIN LOGIN
# ─────────────────────────────────────────────

def connecter_linkedin(page):
    print("Ouverture de LinkedIn...")
    page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
    time.sleep(3)

    # ── Detect if already logged in via persistent session ─────────────────
    # When a saved session exists, LinkedIn redirects away from /login
    # to the feed, jobs, or network page. In that case, no login is needed.
    urls_post_connexion = ["/feed", "/mynetwork", "/jobs", "/notifications", "/messaging"]
    if any(segment in page.url for segment in urls_post_connexion):
        print("[OK] Session persistante détectée — déjà connecté.")
        return True

    # ── Fill in email ───────────────────────────────────────────────────────
    print("Attente du champ email...")
    try:
        page.wait_for_selector("input#username", state="visible", timeout=10000)
    except:
        print("[ERREUR] Champ email introuvable après 10 secondes.")
        return False

    page.fill("input#username", EMAIL)
    print("Email rempli.")
    time.sleep(1)

    # ── Fill in password ────────────────────────────────────────────────────
    print("Attente du champ mot de passe...")
    try:
        page.wait_for_selector("input#password", state="visible", timeout=10000)
    except:
        print("[ERREUR] Champ mot de passe introuvable après 10 secondes.")
        return False

    page.fill("input#password", MOT_DE_PASSE)
    print("Mot de passe rempli.")
    time.sleep(1)

    # ── Click Sign In ───────────────────────────────────────────────────────
    print("Clic sur le bouton S'identifier...")
    try:
        page.wait_for_selector("button[type='submit']", state="visible", timeout=10000)
        page.click("button[type='submit']")
    except:
        print("[ERREUR] Bouton de connexion introuvable.")
        return False

    # ── Wait for successful redirect ────────────────────────────────────────
    print("Attente de la confirmation de connexion...")
    try:
        page.wait_for_url("**linkedin.com/feed**", timeout=20000)
        print("[OK] Connexion réussie.")
        return True
    except:
        current_url = page.url
        print(f"[ATTENTION] URL inattendue : {current_url}")
        print("Une vérification manuelle est peut-être requise dans le navigateur.")
        input("Complétez la vérification puis appuyez sur ENTRÉE pour continuer...")
        return True
# ─────────────────────────────────────────────
# SEARCH + FILTER
# ─────────────────────────────────────────────

def rechercher_et_filtrer(page, keyword, page_number):
    """
    Searches for a keyword on LinkedIn, filters by People + Location France,
    and navigates to the correct page number.
    """
    print(f"[SEARCH] Recherche : '{keyword}' — Page {page_number}")

    # Navigate to search results with filters baked into the URL
    # 'geoUrn' 105015875 = France on LinkedIn
    url = (
        f"https://www.linkedin.com/search/results/people/"
        f"?keywords={keyword.replace(' ', '%20')}"
        f"&geoUrn=%5B%22105015875%22%5D"
        f"&origin=FACETED_SEARCH"
        f"&page={page_number}"
    )
    page.goto(url, wait_until="domcontentloaded")
    time.sleep(4)

# ─────────────────────────────────────────────
# CONNECT TO PROFILES ON A SINGLE PAGE
# ─────────────────────────────────────────────

def traiter_page(page, state):
    """
    Iterates over all visible Connect buttons on the current search results page.
    Starts from state['profile_index'] to support mid-page resumption.
    Updates state after each successful send.
    Returns True if the page was fully processed, False if interrupted.
    """
    global _current_state
    time.sleep(2)

    # Collect all Connect buttons visible on the page
    connect_buttons = []
    for btn in page.locator("button").all():
        try:
            if btn.is_visible() and "connect" in btn.inner_text().strip().lower():
                connect_buttons.append(btn)
        except:
            continue

    print(f"  → {len(connect_buttons)} bouton(s) 'Connect' trouvé(s) sur cette page.")

    start_index = state["profile_index"]

    for i, btn in enumerate(connect_buttons):
        if i < start_index:
            continue  # Skip already-processed profiles

        try:
            print(f"  [PROFIL {i}] Clic sur Connect...")
            btn.click()
            time.sleep(2)

            # Click "Add a note"
            add_note_btn = page.locator("button:has-text('Add a note')")
            if add_note_btn.count() > 0:
                add_note_btn.first.click()
                time.sleep(1.5)

                # Type the note
                note_field = page.locator("textarea")
                if note_field.count() > 0:
                    note_field.first.fill(NOTE_TEXT)
                    time.sleep(1)

            # Click Send
            send_btn = page.locator("button:has-text('Send')")
            if send_btn.count() > 0:
                send_btn.first.click()
                print(f"  [OK] Invitation envoyée (profil {i}).")
                time.sleep(2)
            else:
                # Dismiss the modal if Send is not found
                dismiss = page.locator("button:has-text('Done'), button:has-text('Dismiss')")
                if dismiss.count() > 0:
                    dismiss.first.click()
                print(f"  [SKIP] Bouton Send introuvable pour le profil {i}.")

            # Save progress after each successful profile
            state["profile_index"] = i + 1
            _current_state = state.copy()
            save_progress(state)

        except Exception as e:
            print(f"  [ERREUR] Profil {i} : {e}")
            continue

    # Page fully processed — reset profile index for the next page
    state["profile_index"] = 0
    return True

# ─────────────────────────────────────────────
# DETECT LAST PAGE
# ─────────────────────────────────────────────

def est_derniere_page(page):
    """Returns True if there is no 'Next' pagination button available."""
    try:
        next_btn = page.locator("button[aria-label='Next']")
        return next_btn.count() == 0 or not next_btn.first.is_enabled()
    except:
        return True

# ─────────────────────────────────────────────
# MAIN ORCHESTRATOR
# ─────────────────────────────────────────────

def main():
    global _navigateur, _current_state

    state = load_progress()
    _current_state = state.copy()

    with sync_playwright() as p:
        _navigateur = p.chromium.launch(headless=False, slow_mo=400)
        page = _navigateur.new_page()

        # Step 1 — Log in
        if not connecter_linkedin(page):
            _navigateur.close()
            return

        # Step 2 — Iterate over keywords starting from saved position
        for k_idx in range(state["keyword_index"], len(KEYWORDS)):
            keyword = KEYWORDS[k_idx]
            state["keyword_index"] = k_idx
            _current_state = state.copy()

            print(f"\n[MOT-CLÉ {k_idx}] '{keyword}'")

            # Iterate over pages
            current_page = state["page"] if k_idx == state["keyword_index"] else 1

            while True:
                state["page"] = current_page
                _current_state = state.copy()
                save_progress(state)

                rechercher_et_filtrer(page, keyword, current_page)
                traiter_page(page, state)

                if est_derniere_page(page):
                    print(f"  [FIN] Dernière page atteinte pour '{keyword}'.")
                    break

                current_page += 1
                state["page"] = current_page
                state["profile_index"] = 0

            # Move to next keyword and reset page/profile counters
            state["page"] = 1
            state["profile_index"] = 0

        # All keywords processed — clean up state file
        reset_progress()
        print("\n[TERMINÉ] Toutes les invitations ont été envoyées.")
        _navigateur.close()

if __name__ == "__main__":
    main()