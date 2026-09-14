"""
Pour chaque offre brute, on demande à Claude une analyse réellement poussée:
raisonnement libre d'abord (comme si tu m'envoyais l'offre en conversation),
accès web pour vérifier ce que le texte scrapé ne dit pas (taux Fair Work,
légitimité d'une structure, détail d'une équivalence), puis extraction structurée.
"""
import json
import os
from anthropic import Anthropic
from profile import CANDIDATE_PROFILE

# Modèle plus capable par défaut car on veut un vrai raisonnement, pas juste
# une extraction mécanique. Surchargeable via variable d'environnement si tu
# veux réduire les coûts (ex: ANALYZER_MODEL=claude-sonnet-5).
MODEL = os.environ.get("ANALYZER_MODEL", "claude-opus-5")

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

ANALYSIS_PROMPT = """Tu es en train d'évaluer une offre d'emploi pour Youssef, un candidat
sauveteur français qui part travailler en Australie (Queensland). Traite cette tâche
exactement comme si Youssef venait de te coller cette offre dans une conversation et te
demandait "est-ce que ça vaut le coup ?". Prends le temps de vraiment réfléchir avant de
conclure.

Voici son profil complet :

{profile}

Voici l'offre trouvée (extrait scrapé de la page d'annonce, peut être incomplet) :

Titre: {title}
Entreprise: {company}
Lieu: {location}
Source: {source}
URL: {url}
Contenu de la page: {snippet}

Tu as accès à la recherche web. Utilise-la activement quand c'est utile, par exemple :
- vérifier le taux horaire minimum Fair Work Australia pour ce type de poste si l'annonce
  ne précise pas de salaire, pour donner un ordre de grandeur réaliste
- vérifier la réputation/légitimité de l'entreprise ou de la structure si elle est peu connue
- clarifier un détail d'équivalence de certification s'il y a un doute
- si le contenu scrapé semble tronqué ou peu clair, chercher l'offre complète ailleurs

Réfléchis d'abord en texte libre (raisonnement visible, quelques phrases suffisent), puis
termine ta réponse par UNIQUEMENT un bloc JSON valide (rien après), avec ce format exact :
{{
  "is_relevant": true ou false,
  "score": nombre entre 0 et 100 (pertinence réelle pour CE candidat précis),
  "job_type": "ocean_lifeguard" | "pool_lifeguard" | "aquatic_private" | "swim_instructor" | "autre",
  "experience_required": "aucune" | "junior" | "confirmée" | "inconnue",
  "reasoning": "2-3 phrases expliquant pourquoi ce score, en français, factuel",
  "action_recommandee": "postuler maintenant" | "à surveiller" | "probablement pas adapté",
  "resume_offre": "2-3 phrases en français résumant concrètement ce que le poste implique
    au quotidien (missions, environnement), dans tes propres mots",
  "prerequis": ["2 à 5 prérequis courts et concrets, ex: 'Bronze Medallion exigé',
    'disponible week-ends' - liste vide si aucun identifiable"],
  "salaire": "montant/fourchette si trouvé dans l'annonce OU estimé via le taux Fair Work
    correspondant (précise alors 'estimation Fair Work' dans le texte), sinon 'non précisé'"
}}

Sois strict : si l'offre exige explicitement un rôle de moniteur de natation confirmé,
score bas. Si l'offre est vague mais dans le bon secteur géographique et le bon métier,
score moyen avec action 'à surveiller'. Si aucune info exploitable même après recherche,
is_relevant=false. Ne jamais inventer un détail que ni la page ni tes recherches ne
confirment.
"""


def _extract_final_json(text: str) -> dict:
    text = text.replace("```json", "").replace("```", "")
    last_brace = text.rfind("{")
    if last_brace == -1:
        raise ValueError("Aucun JSON trouvé dans la réponse du modèle.")
    return json.loads(text[last_brace:])


def analyze_job(job: dict) -> dict:
    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=1500,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[{
                "role": "user",
                "content": ANALYSIS_PROMPT.format(
                    profile=CANDIDATE_PROFILE,
                    title=job.get("title", ""),
                    company=job.get("company", ""),
                    location=job.get("location", ""),
                    source=job.get("source", ""),
                    url=job.get("url", ""),
                    snippet=job.get("snippet", ""),
                )
            }],
        )
        # La réponse peut contenir plusieurs blocs (recherches web + texte).
        # On ne garde que les blocs texte, concaténés dans l'ordre.
        full_text = "\n".join(
            block.text for block in message.content if block.type == "text"
        )
        analysis = _extract_final_json(full_text)
    except Exception as e:
        print(f"[warn] analyse échouée pour {job.get('url')}: {e}")
        analysis = {
            "is_relevant": False,
            "score": 0,
            "job_type": "autre",
            "experience_required": "inconnue",
            "reasoning": "Analyse IA indisponible pour cette offre.",
            "action_recommandee": "à surveiller",
            "resume_offre": "",
            "prerequis": [],
            "salaire": "non précisé",
        }
    return {**job, **analysis}


def analyze_jobs(jobs: list) -> list:
    return [analyze_job(j) for j in jobs]
