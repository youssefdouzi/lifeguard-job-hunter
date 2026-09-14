"""
Un scraper par source. Chaque fonction retourne une liste de dicts:
{title, company, location, url, snippet, source}

Design volontairement défensif: si une source change son HTML ou bloque la requête,
la fonction log l'erreur et retourne une liste vide plutôt que de faire planter tout le run.
"""
import time
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

SEARCH_TERMS = ["lifeguard", "pool lifeguard", "ocean lifeguard", "aquatic lifeguard"]


def _safe_get(url, params=None, timeout=20):
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=timeout)
        r.raise_for_status()
        return r
    except Exception as e:
        print(f"[warn] échec requête {url}: {e}")
        return None


def fetch_job_page_text(url, max_chars=4000):
    """
    Va chercher le contenu réel de la page d'annonce (description, prérequis, salaire
    s'il est affiché) pour donner à l'analyse IA de quoi extraire un vrai résumé,
    plutôt que de deviner à partir du seul titre.
    """
    r = _safe_get(url)
    if not r:
        return ""
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    text = " ".join(text.split())
    return text[:max_chars]


def scrape_seek(location="Gold Coast QLD"):
    results = []
    for term in SEARCH_TERMS:
        r = _safe_get(
            "https://www.seek.com.au/{}-jobs/in-{}".format(
                term.replace(" ", "-"), location.replace(" ", "-").replace(",", "")
            )
        )
        if not r:
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select("article")
        for c in cards:
            title_el = c.find("a", attrs={"data-automation": "jobTitle"})
            if not title_el:
                continue
            company_el = c.find(attrs={"data-automation": "jobCompany"})
            loc_el = c.find(attrs={"data-automation": "jobLocation"})
            href = title_el.get("href", "")
            url = "https://www.seek.com.au" + href if href.startswith("/") else href
            results.append({
                "title": title_el.get_text(strip=True),
                "company": company_el.get_text(strip=True) if company_el else "N/A",
                "location": loc_el.get_text(strip=True) if loc_el else location,
                "url": url,
                "snippet": "",
                "source": "Seek",
            })
        time.sleep(1.5)
    return results


def scrape_indeed(location="Gold Coast QLD"):
    results = []
    for term in SEARCH_TERMS:
        r = _safe_get(
            "https://au.indeed.com/jobs",
            params={"q": term, "l": location},
        )
        if not r:
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select("div.job_seen_beacon") or soup.select("a.tapItem")
        for c in cards:
            title_el = c.select_one("h2.jobTitle span") or c.select_one("span[title]")
            company_el = c.select_one("span.companyName")
            loc_el = c.select_one("div.companyLocation")
            link_el = c.select_one("a") if c.name != "a" else c
            href = link_el.get("href", "") if link_el else ""
            if href and href.startswith("/"):
                url = "https://au.indeed.com" + href
            else:
                url = href
            if not title_el or not url:
                continue
            results.append({
                "title": title_el.get_text(strip=True),
                "company": company_el.get_text(strip=True) if company_el else "N/A",
                "location": loc_el.get_text(strip=True) if loc_el else location,
                "url": url,
                "snippet": "",
                "source": "Indeed",
            })
        time.sleep(1.5)
    return results


# Pages carrières à vérifier: on cherche juste la présence de mots-clés lifeguard.
# Ces pages changent souvent de structure -> on remonte le lien vers la page elle-même
# pour qu'Anakin (ou l'analyse IA) vérifie à la main plutôt que de parser un HTML fragile.
# Organisé par catégorie pour être facile à compléter au fil du temps.
CAREERS_PAGES_TO_CHECK = [
    # --- Organismes officiels de sauvetage ---
    ("Surf Life Saving Queensland", "https://www.lifesaving.com.au/careers/"),
    ("Australian Lifeguard Service QLD", "https://www.lifesaving.com.au/als/"),
    ("RLSSA Queensland", "https://www.royallifesaving.com.au/qld/about-us/careers"),

    # --- Councils / centres aquatiques municipaux ---
    ("City of Gold Coast jobs", "https://jobs.goldcoast.qld.gov.au/search/?q=lifeguard"),
    ("Brisbane City Council jobs", "https://careers.brisbane.qld.gov.au/search/?q=lifeguard"),
    ("Belgravia Leisure (gère de nombreuses piscines QLD)", "https://belgravialeisure.com.au/careers/"),
    ("YMCA Queensland (centres aquatiques)", "https://ymcabrisbane.org/careers"),

    # --- Parcs aquatiques ---
    ("Village Roadshow (Wet'n'Wild, Sea World, Movie World)", "https://careers.villageroadshow.com.au/"),
    ("Dreamworld / WhiteWater World", "https://www.dreamworld.com.au/careers"),

    # --- Grandes chaînes hôtelières / resorts (Gold Coast + Brisbane) ---
    ("Accor careers ANZ", "https://careers.accor.com/global/en/search-results?location=Queensland"),
    ("Marriott careers", "https://careers.marriott.com/?location=Gold%20Coast"),
    ("Hilton careers", "https://jobs.hilton.com/apac/en/search-results?keywords=lifeguard"),
    ("Sea World Resort", "https://www.seaworld.com.au/careers"),
    ("QT Gold Coast / Event Hospitality", "https://careers.evt.com/search/?q=lifeguard"),
    ("Voco / RACV / Star Gold Coast", "https://www.star.com.au/careers"),

    # --- Camps, écoles, resorts familiaux avec piscine ---
    ("Currumbin Wildlife Sanctuary (piscine/plage privée)", "https://www.cws.org.au/careers"),
    ("Sanctuary Cove Resort", "https://www.sanctuarycove.com/careers"),
]


def scrape_careers_pages():
    results = []
    for name, url in CAREERS_PAGES_TO_CHECK:
        r = _safe_get(url)
        if not r:
            continue
        text = r.text.lower()
        if "lifeguard" in text or "sauveteur" in text or "pool attendant" in text:
            results.append({
                "title": f"Page carrières à vérifier - {name}",
                "company": name,
                "location": "Queensland",
                "url": url,
                "snippet": "Un mot-clé lifeguard/pool attendant apparaît sur cette page à date du scan.",
                "source": name,
            })
    return results


# Plusieurs requêtes ciblées pour élargir le filet au-delà des gros job boards:
# petits hôtels indépendants, resorts familiaux, piscines privées, camps, etc.
WEB_FALLBACK_QUERIES = [
    "lifeguard job {loc} site:facebook.com OR site:gumtree.com.au",
    "pool attendant OR lifeguard hotel resort {loc} careers apply",
    "aquatic centre lifeguard casual {loc} hiring",
    "waterpark lifeguard {loc} vacancy",
]


def scrape_web_fallback(location="Gold Coast Queensland"):
    """
    Recherche best-effort via DuckDuckGo HTML (pas d'API key nécessaire) pour attraper
    des offres publiées ailleurs: pages Facebook publiques, petits sites d'hôtels/resorts,
    parcs aquatiques indépendants, forums locaux. Moins fiable que Seek/Indeed,
    mais élargit nettement le filet vers le secteur privé.
    """
    results = []
    for template in WEB_FALLBACK_QUERIES:
        query = template.format(loc=location)
        r = _safe_get("https://html.duckduckgo.com/html/", params={"q": query})
        if not r:
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        for link in soup.select("a.result__a")[:10]:
            results.append({
                "title": link.get_text(strip=True),
                "company": "Inconnu (source web)",
                "location": location,
                "url": link.get("href", ""),
                "snippet": "",
                "source": "Recherche web (secteur privé, best-effort)",
            })
        time.sleep(1)
    return results


def collect_all_jobs():
    all_jobs = []
    for location in ["Gold Coast QLD", "Brisbane QLD"]:
        all_jobs += scrape_seek(location)
        all_jobs += scrape_indeed(location)
        all_jobs += scrape_web_fallback(location)
    all_jobs += scrape_careers_pages()

    # Si rien trouvé sur Gold Coast + Brisbane, on élargit (règle demandée par Anakin)
    if len(all_jobs) == 0:
        for location in ["Sunshine Coast QLD", "Queensland"]:
            all_jobs += scrape_seek(location)
            all_jobs += scrape_indeed(location)

    return all_jobs
