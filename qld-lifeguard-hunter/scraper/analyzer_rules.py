"""
Analyseur 100% déterministe. Aucune API, aucun coût, aucune boîte noire.

Chaque score est reconstructible à la main en relisant les règles ci-dessous.
Ce module reproduit sous forme de règles explicites la grille de lecture utilisée
pour évaluer une offre de lifeguard par rapport au profil de Youssef :
type de poste, zone géographique, certifications, niveau d'expérience,
salaire, prérequis, environnement (privé/international).

Limite assumée : c'est du pattern-matching sur texte, pas de la compréhension.
Sur une annonce bien structurée (la norme pour ce secteur), le résultat est
très correct. Sur une annonce très atypique ou mal rédigée, il sera plus
rigide qu'une vraie lecture humaine.
"""
import re

# ---------------------------------------------------------------------------
# Vocabulaire de référence — à enrichir librement au fil du temps, c'est le
# seul endroit à toucher pour affiner le comportement.
# ---------------------------------------------------------------------------

JOB_TYPE_KEYWORDS = {
    "ocean_lifeguard": [
        "ocean lifeguard", "beach lifeguard", "surf lifeguard", "lifesaver",
        "surf life saving", "beach patrol",
    ],
    "pool_lifeguard": [
        "pool lifeguard", "pool attendant", "aquatic lifeguard",
        "swim centre lifeguard", "aquatic centre lifeguard", "aquatics officer",
    ],
    "aquatic_private": [
        "resort lifeguard", "hotel lifeguard", "waterpark lifeguard",
        "water park lifeguard", "camp lifeguard", "recreation attendant",
    ],
    "swim_instructor": [
        "swim instructor", "swimming teacher", "swim teacher",
        "learn to swim", "swim coach",
    ],
}

# Si un de ces indices apparaît à côté d'une offre swim instructor, on ne
# l'écarte pas d'office (le profil accepte une reconversion sans exigence
# d'expérience préalable).
SWIM_INSTRUCTOR_ESCAPE_HATCH = [
    "no experience necessary", "no experience required", "training provided",
    "trainee", "will train",
]

# Termes signalant un rôle senior/lead, cohérent avec l'expérience de
# superviseur/chef d'équipe du candidat -> bonus de score.
LEAD_ROLE_KEYWORDS = [
    "team leader", "supervisor", "head lifeguard", "duty manager",
    "lead lifeguard", "senior lifeguard", "shift leader",
]

# Zone géographique -> (points de score, libellé canonique)
LOCATION_SCORES = [
    (["gold coast"], 25, "Gold Coast"),
    (["brisbane"], 22, "Brisbane"),
    (["sunshine coast"], 14, "Sunshine Coast"),
    (["queensland", "qld"], 8, "Queensland (zone large)"),
]

# Certifications que le candidat détient déjà ou vise activement (voir profile.py).
# Si l'annonce les mentionne comme requises, c'est un match positif.
CERTS_CANDIDATE_COVERS = [
    "bronze medallion", "certificate ii in public safety", "hltaid011",
    "first aid", "cpr", "aed", "aquatic rescue", "surf rescue certificate",
]

# Si l'annonce exige l'un de ces éléments *déjà en poche à la candidature*
# (pas obtenable à l'arrivée), c'est un vrai frein -> pénalité forte.
HARD_BLOCKER_PHRASES = [
    "must currently hold a blue card", "must already hold a working with children",
    "must have current australian work rights" ,  # WHV couvre ça, donc pas un vrai blocker,
    # laissé ici à titre d'exemple si jamais le libellé exact posait souci -
    # retiré du calcul de pénalité pour ne pas générer de faux négatif.
]
REAL_HARD_BLOCKERS = [
    "must currently hold a blue card",
    "blue card required prior to application",
    "must already hold working with children check",
    "must have prior australian lifeguard experience",
    "australian citizens only", "permanent residents only",
]

EXPERIENCE_PATTERNS = {
    "aucune": [r"no experience necessary", r"no experience required", r"entry level", r"training provided"],
    "confirmée": [r"\d+\+?\s?years?\s?(of)?\s?experience", r"proven experience", r"\bsenior\b", r"minimum \d+ years"],
}

SALARY_REGEX = re.compile(
    r"\$\s?\d{2,3}(?:[.,]\d{2})?\s?(?:-|to)\s?\$?\s?\d{2,3}(?:[.,]\d{2})?\s?(?:/|per)\s?(?:hr|hour)"
    r"|\$\s?\d{2,3}(?:[.,]\d{2})?\s?(?:/|per)\s?(?:hr|hour)"
    r"|AUD\s?\$?\s?\d{2,3}(?:[.,]\d{2})?",
    re.IGNORECASE,
)

REQUIREMENT_SECTION_HEADERS = [
    "requirements", "essential criteria", "you will need", "about you",
    "what you'll need", "selection criteria", "key requirements", "qualifications",
]

INTERNATIONAL_CLIENTELE_KEYWORDS = [
    "resort", "hotel", "international guests", "tourists", "theme park",
    "waterpark", "water park", "guest experience", "family resort",
]

CONTRACT_KEYWORDS = {
    "casual": ["casual"],
    "permanent": ["permanent"],
    "temps partiel": ["part-time", "part time"],
    "temps plein": ["full-time", "full time"],
    "saisonnier": ["seasonal", "fixed term"],
}


def _find_any(text: str, terms: list) -> bool:
    return any(term in text for term in terms)


def _count_matches(text: str, terms: list) -> int:
    return sum(1 for term in terms if term in text)


def classify_job_type(full_text: str, title: str) -> str:
    scores = {}
    for job_type, keywords in JOB_TYPE_KEYWORDS.items():
        # Le titre pèse 3x plus que le reste du texte
        title_hits = _count_matches(title, keywords) * 3
        body_hits = _count_matches(full_text, keywords)
        scores[job_type] = title_hits + body_hits
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "autre"
    return best


def detect_location(full_text: str) -> tuple:
    for keywords, points, label in LOCATION_SCORES:
        if _find_any(full_text, keywords):
            return points, label
    return 0, "non identifiée"


def detect_experience(full_text: str) -> str:
    for level, patterns in EXPERIENCE_PATTERNS.items():
        if any(re.search(p, full_text) for p in patterns):
            return level
    return "inconnue"


def detect_contract_type(full_text: str) -> str:
    for label, keywords in CONTRACT_KEYWORDS.items():
        if _find_any(full_text, keywords):
            return label
    return "non précisé"


def extract_salary(full_text: str) -> str:
    match = SALARY_REGEX.search(full_text)
    return match.group(0) if match else "non précisé"


def extract_requirements(full_text: str, max_items: int = 5) -> list:
    lowered = full_text.lower()
    start = -1
    for header in REQUIREMENT_SECTION_HEADERS:
        idx = lowered.find(header)
        if idx != -1 and (start == -1 or idx < start):
            start = idx
    if start == -1:
        # Pas de section identifiable: on cherche des phrases-signal
        sentences = re.split(r"(?<=[.!?])\s+", full_text)
        candidates = [
            s.strip() for s in sentences
            if re.search(r"\b(must|require|essential|need to|certificate|licence|license)\b", s, re.IGNORECASE)
            and "$" not in s and "per hour" not in s.lower()
        ]
        return [c[:120] for c in candidates[:max_items]]

    chunk = full_text[start:start + 500]
    # Coupe le chunk avant toute mention de salaire pour ne pas la faire passer pour un prérequis
    salary_cut = SALARY_REGEX.search(chunk)
    if salary_cut:
        chunk = chunk[:salary_cut.start()]
    parts = re.split(r"[•\-\u2022]\s*|(?<=[.!?])\s+", chunk)
    parts = [
        p.strip(" :\n\t") for p in parts
        if len(p.strip()) > 14 and "pay rate" not in p.lower() and "salary" not in p.lower()
    ]
    return [p[:120] for p in parts[1:max_items + 1]]  # on saute le titre de section


def build_summary(job_type: str, location_label: str, contract_type: str, company: str) -> str:
    job_type_fr = {
        "ocean_lifeguard": "poste de sauveteur plage/océan",
        "pool_lifeguard": "poste de sauveteur piscine",
        "aquatic_private": "poste de sauveteur en structure privée (resort/parc aquatique)",
        "swim_instructor": "poste de moniteur de natation",
        "autre": "poste lié à la sécurité aquatique",
    }.get(job_type, "poste lié à la sécurité aquatique")
    return (
        f"{job_type_fr.capitalize()} chez {company}, zone {location_label}. "
        f"Type de contrat détecté: {contract_type}."
    )


def analyze_job(job: dict) -> dict:
    full_text = f"{job.get('title', '')} {job.get('snippet', '')}".lower()
    full_text = " ".join(full_text.split())  # normalise espaces/retours à la ligne
    title_lower = job.get("title", "").lower()

    job_type = classify_job_type(full_text, title_lower)
    location_points, location_label = detect_location(full_text)
    experience = detect_experience(full_text)
    contract_type = detect_contract_type(full_text)
    salaire = extract_salary(full_text)
    prerequis = extract_requirements(full_text)
    is_lead_role = _find_any(full_text, LEAD_ROLE_KEYWORDS)
    international_bonus = _find_any(full_text, INTERNATIONAL_CLIENTELE_KEYWORDS)
    hard_blocker = _find_any(full_text, REAL_HARD_BLOCKERS)
    certs_matched = _count_matches(full_text, CERTS_CANDIDATE_COVERS)

    # --- Calcul du score, plafonné à 100 ---
    score = 0
    reasoning_bits = []

    if job_type == "swim_instructor" and not _find_any(full_text, SWIM_INSTRUCTOR_ESCAPE_HATCH):
        score += 10
        reasoning_bits.append("poste de moniteur de natation confirmé, hors profil sauveteur")
    elif job_type == "swim_instructor":
        score += 35
        reasoning_bits.append("moniteur de natation mais sans expérience préalable exigée, reconversion possible")
    elif job_type in ("ocean_lifeguard", "pool_lifeguard"):
        score += 40
        reasoning_bits.append(f"type de poste directement dans la cible ({job_type})")
    elif job_type == "aquatic_private":
        score += 35
        reasoning_bits.append("poste privé (resort/parc aquatique), cible large du profil")
    else:
        score += 15
        reasoning_bits.append("type de poste non identifié clairement, prudence")

    score += location_points
    reasoning_bits.append(f"zone détectée: {location_label} (+{location_points})")

    if is_lead_role:
        score += 15
        reasoning_bits.append("rôle senior/lead détecté, cohérent avec l'expérience de supervision")

    if international_bonus:
        score += 8
        reasoning_bits.append("clientèle internationale probable, atout multilingue valorisé")

    if certs_matched >= 2:
        score += 10
        reasoning_bits.append("plusieurs certifications exigées déjà couvertes par le profil")
    elif certs_matched == 1:
        score += 5

    if hard_blocker:
        score -= 40
        reasoning_bits.append("condition bloquante détectée (ex: certification déjà active exigée)")

    if experience == "confirmée" and not is_lead_role:
        score -= 10
        reasoning_bits.append("expérience confirmée exigée sans lien clair avec un rôle de lead")

    score = max(0, min(100, score))

    if score >= 65:
        action = "postuler maintenant"
    elif score >= 40:
        action = "à surveiller"
    else:
        action = "probablement pas adapté"

    is_relevant = job_type != "autre" or location_points > 0

    return {
        **job,
        "is_relevant": is_relevant,
        "score": score,
        "job_type": job_type,
        "experience_required": experience,
        "reasoning": " · ".join(reasoning_bits),
        "action_recommandee": action,
        "resume_offre": build_summary(job_type, location_label, contract_type, job.get("company", "")),
        "prerequis": prerequis,
        "salaire": salaire,
    }


def analyze_jobs(jobs: list) -> list:
    return [analyze_job(j) for j in jobs]
