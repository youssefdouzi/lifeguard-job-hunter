import json
import os
from datetime import datetime, timezone

from sources import collect_all_jobs, fetch_job_page_text
from notifier import send_telegram_message, format_notification
from profile import NOTIFY_SCORE_THRESHOLD

# "rules" = moteur déterministe gratuit (défaut). "llm" = analyse via API Anthropic
# (nécessite ANTHROPIC_API_KEY, voir README pour le coût).
ANALYSIS_ENGINE = os.environ.get("ANALYSIS_ENGINE", "rules")
if ANALYSIS_ENGINE == "llm":
    from analyzer import analyze_jobs
else:
    from analyzer_rules import analyze_jobs

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
SEEN_FILE = os.path.join(DATA_DIR, "seen_jobs.json")
DASHBOARD_DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "docs", "data.json")


def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_seen(seen):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(seen, f, ensure_ascii=False, indent=2)


def update_dashboard(new_analyzed_jobs):
    """Fusionne les nouvelles offres analysées avec l'historique déjà affiché,
    pour que le dashboard garde la mémoire des runs précédents."""
    os.makedirs(os.path.dirname(DASHBOARD_DATA_FILE), exist_ok=True)
    previous_jobs = []
    if os.path.exists(DASHBOARD_DATA_FILE):
        with open(DASHBOARD_DATA_FILE, "r", encoding="utf-8") as f:
            previous_jobs = json.load(f).get("jobs", [])

    merged = {j["url"]: j for j in previous_jobs}
    for j in new_analyzed_jobs:
        merged[j["url"]] = j  # la version la plus récente écrase l'ancienne

    payload = {
        "last_run": datetime.now(timezone.utc).isoformat(),
        "jobs": sorted(merged.values(), key=lambda j: -j["score"]),
    }
    with open(DASHBOARD_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def main():
    seen = load_seen()

    print("Scraping en cours...")
    raw_jobs = collect_all_jobs()
    print(f"{len(raw_jobs)} offre(s) brute(s) trouvée(s).")

    # Dédup par URL avant même d'appeler l'IA, pour économiser des appels API
    unique_jobs = {}
    for j in raw_jobs:
        if j["url"] and j["url"] not in unique_jobs:
            unique_jobs[j["url"]] = j
    unique_jobs = list(unique_jobs.values())

    print(f"{len(unique_jobs)} offre(s) unique(s), récupération du contenu des annonces...")
    for j in unique_jobs:
        if j["url"] not in seen:  # on ne re-télécharge pas les annonces déjà vues/analysées
            j["snippet"] = fetch_job_page_text(j["url"])

    print("Analyse IA en cours...")
    analyzed = analyze_jobs(unique_jobs)

    new_matches = [
        j for j in analyzed
        if j["url"] not in seen and j["is_relevant"] and j["score"] >= NOTIFY_SCORE_THRESHOLD
    ]

    if new_matches:
        message = format_notification(new_matches)
        send_telegram_message(message)
        print(f"{len(new_matches)} nouvelle(s) offre(s) notifiée(s).")
    else:
        print("Rien de nouveau au-dessus du seuil cette fois-ci.")

    # Marquer toutes les offres vues (même sous le seuil) pour ne jamais re-notifier
    for j in analyzed:
        seen[j["url"]] = {
            "title": j["title"],
            "score": j["score"],
            "first_seen": seen.get(j["url"], {}).get(
                "first_seen", datetime.now(timezone.utc).isoformat()
            ),
        }
    save_seen(seen)

    # Le dashboard affiche l'ensemble des offres jamais vues, triées par score
    all_known_jobs = list({j["url"]: j for j in analyzed}.values())
    update_dashboard(all_known_jobs)
    print("Dashboard mis à jour.")


if __name__ == "__main__":
    main()
