"""
Notification Telegram. Choisi plutôt que l'email car zéro configuration serveur:
un bot Telegram + ton chat_id suffisent (voir README pour la création du bot en 2 min).
"""
import os
import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def send_telegram_message(text: str):
    if not BOT_TOKEN or not CHAT_ID:
        print("[warn] TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID manquant, notif ignorée.")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    # Telegram limite un message à 4096 caractères
    for chunk_start in range(0, len(text), 3800):
        chunk = text[chunk_start:chunk_start + 3800]
        try:
            requests.post(url, data={
                "chat_id": CHAT_ID,
                "text": chunk,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }, timeout=15)
        except Exception as e:
            print(f"[warn] envoi Telegram échoué: {e}")


def format_notification(new_matches: list) -> str:
    if not new_matches:
        return ""
    lines = [f"🦈 <b>{len(new_matches)} nouvelle(s) offre(s) lifeguard QLD</b>\n"]
    for job in sorted(new_matches, key=lambda j: -j["score"]):
        prereqs = ", ".join(job.get("prerequis", []) or []) or "non précisé"
        lines.append(
            f"\n<b>{job['title']}</b> — score {job['score']}/100\n"
            f"{job['company']} · {job['location']} · via {job['source']}\n"
            f"💰 {job.get('salaire', 'non précisé')}\n"
            f"📋 {prereqs}\n"
            f"{job.get('resume_offre', '')}\n"
            f"→ {job['action_recommandee']}\n"
            f"{job['url']}"
        )
    return "\n".join(lines)
