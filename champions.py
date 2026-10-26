#!/usr/bin/env python3
"""
Pronósticos Champions Elo — genera data.json para el widget del blog.

Mismo motor que pronosticosfutbolelo (Elo con K, ventaja de campo, multiplicador por
diferencia de goles y probabilidades 1X2 calibradas con el histórico), pero alimentado
con la API pública de ESPN, que trae ligas nacionales y copas europeas con los mismos
identificadores de equipo. Así el Elo de equipos de ligas distintas es comparable.

1. Descarga resultados (3 temporadas) de ligas nacionales y competiciones UEFA.
   Los meses ya cerrados se guardan en results.json y no se vuelven a descargar.
2. Calcula el Elo de cada equipo.
3. Pronostica los próximos partidos de la Champions (1X2, doble oportunidad, marcador).
4. Calcula la clasificación de la fase liga y simula el resto del torneo
   (probabilidad de top 8, de playoff, de eliminación y de ganar la Champions).
5. Guarda los pronósticos y los liquida cuando se juegan (aciertos).

Solo usa la librería estándar de Python.
"""
import bisect
import json
import math
import os
import random
import sys
import time
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

API = "https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard?limit=500&dates={ym}"
OUT_DIR = os.environ.get("OUT_DIR", os.path.dirname(os.path.abspath(__file__)))
LOCAL_DIR = os.environ.get("LOCAL_DATA")      # pruebas sin internet: <code>_<YYYYMM>.json
TODAY_OVERRIDE = os.environ.get("TODAY")       # pruebas: fija la fecha de "hoy" (YYYY-MM-DD)
SIMS = int(os.environ.get("SIMS", "10000"))

CL = "uefa.champions"
# Competiciones UEFA (todas conectan ligas entre sí)
UEFA = {
    "uefa.champions": "Champions League", "uefa.champions_qual": "Previa de Champions",
    "uefa.europa": "Europa League", "uefa.europa_qual": "Previa de Europa League",
    "uefa.europa.conf": "Conference League", "uefa.europa.conf_qual": "Previa de Conference",
    "uefa.super_cup": "Supercopa de Europa",
}
# Ligas nacionales -> (nombre, bandera ISO, Elo inicial de un equipo nuevo)
LEAGUES = {
    "eng.1": ("Premier League", "gb-eng", 1620), "esp.1": ("LaLiga", "es", 1610),
    "ger.1": ("Bundesliga", "de", 1600), "ita.1": ("Serie A", "it", 1600),
    "fra.1": ("Ligue 1", "fr", 1570), "por.1": ("Liga Portugal", "pt", 1500),
    "ned.1": ("Eredivisie", "nl", 1500), "bel.1": ("Pro League", "be", 1480),
    "tur.1": ("Süper Lig", "tr", 1480), "sco.1": ("Premiership", "gb-sct", 1440),
    "gre.1": ("Super League", "gr", 1450), "aut.1": ("Bundesliga", "at", 1450),
    "den.1": ("Superliga", "dk", 1440), "nor.1": ("Eliteserien", "no", 1420),
    "swe.1": ("Allsvenskan", "se", 1410), "rus.1": ("Premier League", "ru", 1450),
    "eng.2": ("Championship", "gb-eng", 1480), "esp.2": ("Segunda", "es", 1460),
    "ger.2": ("2. Bundesliga", "de", 1460), "ita.2": ("Serie B", "it", 1440),
    "fra.2": ("Ligue 2", "fr", 1430),
}
UEFA_START = 1400.0          # equipo que solo aparece en Europa (ligas sin datos)

# Parámetros del modelo (los mismos que el blog de ligas, con K europeo algo mayor
# para que los cruces entre ligas pesen más al conectar los niveles de cada país)
K = 20.0
K_EURO = 30.0
HOME_ADV = 60.0
SEASONS_BACK = 3
AVG_GOALS = 2.75
HISTORY_KEEP = 1500
KO_ROUNDS = ["knockout-round-playoffs", "round-of-16", "quarterfinals", "semifinals", "final"]
ROUND_ES = {"league-phase": "Fase liga", "knockout-round-playoffs": "Playoff",
            "round-of-16": "Octavos", "quarterfinals": "Cuartos", "semifinals": "Semifinales",
            "final": "Final"}

NAMES_ES = {
    "Bayern Munich": "Bayern Múnich", "Inter Milan": "Inter de Milán", "Internazionale": "Inter de Milán",
    "Atlético Madrid": "Atlético de Madrid", "Atletico Madrid": "Atlético de Madrid",
    "Paris Saint-Germain": "PSG", "Sporting CP": "Sporting de Portugal", "Club Brugge": "Brujas",
    "Napoli": "Nápoles", "Porto": "Oporto", "FC Porto": "Oporto", "AEK Athens": "AEK Atenas",
    "FC Copenhagen": "Copenhague", "Copenhagen": "Copenhague", "Red Star Belgrade": "Estrella Roja",
    "Crvena Zvezda": "Estrella Roja", "Dinamo Zagreb": "Dinamo de Zagreb", "Monaco": "Mónaco",
    "AS Monaco": "Mónaco", "Marseille": "Olympique de Marsella", "Lyon": "Olympique de Lyon",
    "Eintracht Frankfurt": "Eintracht de Fráncfort", "Sparta Prague": "Sparta de Praga",
    "Slavia Prague": "Slavia de Praga", "Basel": "Basilea", "FC Basel": "Basilea",
    "Bodo/Glimt": "Bodø/Glimt", "Bodø/Glimt": "Bodø/Glimt", "Qarabag": "Qarabağ",
    "Qarabag FK": "Qarabağ", "Fenerbahce": "Fenerbahçe", "Besiktas": "Beşiktaş",
    "Red Bull Salzburg": "RB Salzburgo", "RB Salzburg": "RB Salzburgo", "Shakhtar Donetsk": "Shakhtar",
    "Tottenham Hotspur": "Tottenham", "Newcastle United": "Newcastle", "Real Betis": "Betis",
    "PSV Eindhoven": "PSV", "Union St.-Gilloise": "Union Saint-Gilloise", "Olympiacos": "Olympiacos",
    "Ferencvaros": "Ferencváros", "Legia Warsaw": "Legia de Varsovia", "Lech Poznan": "Lech Poznań",
    "Steaua Bucuresti": "FCSB", "FCSB": "FCSB", "Kairat Almaty": "Kairat Almaty",
    "Manchester United": "Manchester United", "Manchester City": "Manchester City",
    "VfB Stuttgart": "Stuttgart", "Bayer Leverkusen": "Bayer Leverkusen", "Lazio": "Lazio",
    "Athletic Club": "Athletic Club", "Celtic": "Celtic", "Rangers": "Rangers",
}
COUNTRY_ISO = {
    "England": "gb-eng", "Scotland": "gb-sct", "Wales": "gb-wls", "Northern Ireland": "gb-nir",
    "Spain": "es", "Germany": "de", "Italy": "it", "France": "fr", "Portugal": "pt",
    "Netherlands": "nl", "Belgium": "be", "Turkey": "tr", "Türkiye": "tr", "Greece": "gr",
    "Austria": "at", "Switzerland": "ch", "Denmark": "dk", "Norway": "no", "Sweden": "se",
    "Finland": "fi", "Iceland": "is", "Ireland": "ie", "Republic of Ireland": "ie",
    "Czech Republic": "cz", "Czechia": "cz", "Slovakia": "sk", "Poland": "pl", "Hungary": "hu",
    "Romania": "ro", "Bulgaria": "bg", "Serbia": "rs", "Croatia": "hr", "Slovenia": "si",
    "Bosnia and Herzegovina": "ba", "Montenegro": "me", "North Macedonia": "mk", "Albania": "al",
    "Kosovo": "xk", "Ukraine": "ua", "Belarus": "by", "Moldova": "md", "Russia": "ru",
    "Georgia": "ge", "Armenia": "am", "Azerbaijan": "az", "Kazakhstan": "kz", "Israel": "il",
    "Cyprus": "cy", "Malta": "mt", "Luxembourg": "lu", "Lithuania": "lt", "Latvia": "lv",
    "Estonia": "ee", "Faroe Islands": "fo", "Gibraltar": "gi", "Andorra": "ad",
    "San Marino": "sm", "Liechtenstein": "li", "Monaco": "mc",
}

# Equipos que juegan en campo neutral de otro país (guerra, sanciones…)
TEAM_COUNTRY = {
    "Shakhtar Donetsk": "ua", "Dynamo Kyiv": "ua", "Dnipro-1": "ua", "Zorya Luhansk": "ua",
    "Maccabi Tel-Aviv": "il", "Maccabi Haifa": "il", "Hapoel Be'er Sheva": "il", "Maccabi Tel Aviv": "il",
    "Qarabag": "az", "Qarabag FK": "az", "Sheriff Tiraspol": "md",
}

# ---------------------------------------------------------------- utilidades
def log(*a):
    print(*a, file=sys.stderr, flush=True)


def today_utc():
    if TODAY_OVERRIDE:
        return date.fromisoformat(TODAY_OVERRIDE)
    return datetime.now(timezone.utc).date()


def fetch_events(code, ym):
    """Eventos de una competición en un mes (YYYYMM). Devuelve None si falla la descarga."""
    if LOCAL_DIR:
        fp = os.path.join(LOCAL_DIR, f"{code}_{ym}.json")
        if not os.path.exists(fp):
            return []
        with open(fp, encoding="utf-8") as f:
            return json.load(f).get("events", [])
    url = API.format(code=code, ym=ym)
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 champions-elo"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8")).get("events", [])
        except urllib.error.HTTPError as e:
            if e.code == 400:      # la API responde 400 si no hay calendario ese mes
                return []
            err = e
        except Exception as e:  # noqa
            err = e
        time.sleep(1.5 * (attempt + 1))
    log("  ! no se pudo descargar", code, ym, err)
    return None


def months_between(d1, d2):
    y, m = d1.year, d1.month
    while (y, m) <= (d2.year, d2.month):
        yield f"{y}{m:02d}"
        m += 1
        if m == 13:
            y, m = y + 1, 1


def month_end(ym):
    y, m = int(ym[:4]), int(ym[4:])
    nxt = date(y + (m == 12), 1 if m == 12 else m + 1, 1)
    return nxt - timedelta(days=1)


def season_start(d):
    """Año en que empieza la temporada europea en curso (julio-junio)."""
    return d.year if d.month >= 7 else d.year - 1


def team_info(teams, t, venue_country=None):
    tid = str(t["id"])
    cur = teams.get(tid) or {}
    name = t.get("displayName") or t.get("shortDisplayName") or cur.get("full") or tid
    teams[tid] = {
        "full": name,
        "n": NAMES_ES.get(name, name),
        "s": t.get("shortDisplayName") or name,
        "a": t.get("abbreviation") or "",
        "logo": t.get("logo") or cur.get("logo", ""),
        "c": cur.get("c", ""),
        "vc": cur.get("vc") or (venue_country or ""),
    }
    return tid


def parse_event(ev, code, teams):
    """Convierte un evento de ESPN en un partido compacto (o None)."""
    try:
        comp = ev["competitions"][0]
        cs = comp["competitors"]
        home = next(c for c in cs if c.get("homeAway") == "home")
        away = next(c for c in cs if c.get("homeAway") == "away")
    except (KeyError, IndexError, StopIteration):
        return None
    st = ev.get("status", {}).get("type", {})
    country = ((comp.get("venue") or {}).get("address") or {}).get("country")
    hid = team_info(teams, home["team"], country)
    aid = team_info(teams, away["team"])
    slug = (ev.get("season") or {}).get("slug", "")
    m = {
        "id": str(ev.get("id")), "code": code, "date": ev.get("date", ""),
        "h": hid, "a": aid, "slug": slug, "year": (ev.get("season") or {}).get("year"),
        "neutral": bool(comp.get("neutralSite")) or slug == "final",
        "done": bool(st.get("completed")), "state": st.get("state", ""),
        "status": st.get("name", ""),
    }
    if m["done"]:
        try:
            m["hg"], m["ag"] = int(home.get("score")), int(away.get("score"))
        except (TypeError, ValueError):
            return None
        if home.get("shootoutScore") is not None and away.get("shootoutScore") is not None:
            m["pens"] = [int(home["shootoutScore"]), int(away["shootoutScore"])]
        m["hw"] = bool(home.get("winner"))
        m["aw"] = bool(away.get("winner"))
    tv = []
    for b in comp.get("broadcasts") or []:
        tv += b.get("names") or []
    m["venue"] = (comp.get("venue") or {}).get("fullName", "")
    m["tv"] = tv
    return m


# ---------------------------------------------------------------- carga de datos
def load_all(today):
    """Resultados de todas las competiciones (con caché de meses cerrados) + CL completa."""
    cache_path = os.path.join(OUT_DIR, "results.json")
    cache = {"months": {}, "teams": {}}
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            cache = json.load(f)
    teams = cache.get("teams", {})
    months = cache.get("months", {})
    start = date(season_start(today) - (SEASONS_BACK - 1), 7, 1)
    end = today + timedelta(days=75)            # partidos programados de la Champions
    codes = list(LEAGUES) + list(UEFA)
    fetched = failed = 0
    for code in codes:
        for ym in months_between(start, end):
            key = f"{code}|{ym}"
            closed = month_end(ym) < today - timedelta(days=4)
            if key in months and closed:
                continue
            if code != CL and int(ym) > int(today.strftime("%Y%m")):
                continue                        # el futuro solo hace falta en la Champions
            evs = fetch_events(code, ym)
            if evs is None:
                failed += 1
                continue
            fetched += 1
            rows = []
            for ev in evs:
                m = parse_event(ev, code, teams)
                if m:
                    rows.append(m)
            if code in LEAGUES:                  # el país del equipo sale de su liga
                for m in rows:
                    for t in (m["h"], m["a"]):
                        teams[t]["c"] = LEAGUES[code][1]
            # en caché solo se guarda lo necesario
            months[key] = [{k: v for k, v in m.items() if k not in ("venue", "tv", "state", "status")}
                           if code != CL else m for m in rows]
    log(f"  meses descargados: {fetched} (fallidos: {failed})")
    cache = {"v": 1, "updated": datetime.now(timezone.utc).isoformat(timespec="minutes"),
             "teams": teams, "months": months}
    matches = []
    seen = set()
    for key, rows in months.items():
        for m in rows:
            if m["id"] in seen:
                continue
            seen.add(m["id"])
            matches.append(m)
    matches.sort(key=lambda m: m["date"])
    return matches, teams, cache, cache_path, failed


# ---------------------------------------------------------------- modelo Elo
def g_mult(gd):
    gd = abs(gd)
    if gd <= 1:
        return 1.0
    if gd == 2:
        return 1.5
    return (11 + gd) / 8.0


def run_elo(matches):
    elo, games = {}, defaultdict(int)
    trend = defaultdict(list)
    hist = defaultdict(list)          # evolución del Elo (para gráficos): [fecha, elo]
    calib = []
    pre = {}                          # Elo de los dos equipos justo antes de cada partido de Champions
    for m in matches:
        if not m.get("done"):
            continue
        h, a = m["h"], m["a"]
        if m["code"] in LEAGUES:
            start = float(LEAGUES[m["code"]][2])
        else:
            start = UEFA_START
        rh, ra = elo.get(h, start), elo.get(a, start)
        if m["code"] == CL:
            pre[m["id"]] = (rh, ra)
        dr = rh + (0 if m["neutral"] else HOME_ADV) - ra
        exp_h = 1.0 / (1.0 + 10 ** (-dr / 400.0))
        res = 1.0 if m["hg"] > m["ag"] else (0.5 if m["hg"] == m["ag"] else 0.0)
        if games[h] >= 10 and games[a] >= 10:
            calib.append((dr, "H" if res == 1 else ("D" if res == 0.5 else "A")))
        k = K_EURO if m["code"] in UEFA else K
        delta = k * g_mult(m["hg"] - m["ag"]) * (res - exp_h)
        elo[h], elo[a] = rh + delta, ra - delta
        for t, d in ((h, delta), (a, -delta)):
            trend[t] = (trend[t] + [d])[-5:]
            games[t] += 1
            hist[t].append((m["date"][:10], round(elo[t])))
    return elo, games, trend, hist, calib, pre


class Calibrator:
    """Probabilidades 1X2 según la diferencia de Elo, a partir de lo que pasó en el histórico."""

    def __init__(self, calib):
        self.data = sorted(calib)
        self.n = len(self.data)
        self.cache = {}

    def probs(self, dr):
        key = round(dr / 5) * 5
        if key in self.cache:
            return self.cache[key]
        if self.n < 300:
            e = 1.0 / (1.0 + 10 ** (-dr / 400.0))
            pd = max(0.16, 0.29 - 0.00035 * abs(dr))
            ph = max(0.02, e - pd / 2)
            pa = max(0.02, 1 - ph - pd)
        else:
            i = bisect.bisect_left(self.data, (key, ""))
            w = min(300, self.n // 2)
            lo, hi = max(0, i - w), min(self.n, i + w)
            cnt = {"H": 1.0, "D": 1.0, "A": 1.0}
            bw = max(40.0, abs(self.data[hi - 1][0] - self.data[lo][0]) / 2)
            for d, r in self.data[lo:hi]:
                cnt[r] += math.exp(-((d - key) / bw) ** 2)
            ph, pd, pa = cnt["H"], cnt["D"], cnt["A"]
        s = ph + pd + pa
        out = (ph / s, pd / s, pa / s)
        self.cache[key] = out
        return out


# ---------------------------------------------------------------- goles (Poisson)
def pois(lmb, k):
    return math.exp(-lmb) * lmb ** k / math.factorial(k)


def outcome_from_sup(sup):
    lh, la = max(0.15, (AVG_GOALS + sup) / 2), max(0.15, (AVG_GOALS - sup) / 2)
    ph = pa = 0.0
    for i in range(11):
        for j in range(11):
            p = pois(lh, i) * pois(la, j)
            if i > j:
                ph += p
            elif j > i:
                pa += p
    return ph - pa


SUP_GRID = [(-3.0 + 0.05 * i) for i in range(121)]
SUP_DIFF = [outcome_from_sup(s) for s in SUP_GRID]


def lambdas(ph, pa):
    """Goles esperados de local y visitante que reproducen la diferencia ph - pa."""
    target = ph - pa
    i = bisect.bisect_left(SUP_DIFF, target)
    i = min(max(i, 1), len(SUP_GRID) - 1)
    d0, d1 = SUP_DIFF[i - 1], SUP_DIFF[i]
    s0, s1 = SUP_GRID[i - 1], SUP_GRID[i]
    sup = s0 + (s1 - s0) * ((target - d0) / (d1 - d0) if d1 != d0 else 0)
    return max(0.15, (AVG_GOALS + sup) / 2), max(0.15, (AVG_GOALS - sup) / 2)


def likely_score(lh, la, ph, pd, pa):
    """Marcador más probable coherente con el resultado más probable."""
    best = max((ph, "1"), (pd, "X"), (pa, "2"))[1]
    cands = []
    for i in range(6):
        for j in range(6):
            r = "1" if i > j else ("X" if i == j else "2")
            if r == best:
                cands.append((pois(lh, i) * pois(la, j), i, j))
    _, i, j = max(cands)
    return f"{i}-{j}"


def sample_pois(lmb, rnd):
    lim, k, p = math.exp(-lmb), 0, 1.0
    while True:
        p *= rnd.random()
        if p <= lim:
            return k
        k += 1


# ---------------------------------------------------------------- pronóstico de un partido
class Model:
    def __init__(self, elo, games, cal):
        self.elo, self.games, self.cal = elo, games, cal

    def rating(self, t):
        return self.elo.get(t, UEFA_START)

    def probs(self, h, a, neutral=False):
        dr = self.rating(h) + (0 if neutral else HOME_ADV) - self.rating(a)
        return self.cal.probs(dr)

    def goals(self, h, a, neutral=False):
        ph, pd, pa = self.probs(h, a, neutral)
        return lambdas(ph, pa)


def confidence(p):
    """Confianza 1-10 según la probabilidad del pronóstico."""
    return max(1, min(10, int(round(1 + (p - 0.36) / 0.045))))


def predict(model, m):
    ph, pd, pa = model.probs(m["h"], m["a"], m["neutral"])
    lh, la = lambdas(ph, pa)
    pick, pp = max((("1", ph), ("X", pd), ("2", pa)), key=lambda x: x[1])
    dc, dcp = ("1X", ph + pd) if ph >= pa else ("X2", pa + pd)
    return {
        "prob": [round(100 * ph, 1), round(100 * pd, 1), round(100 * pa, 1)],
        "xg": [round(lh, 2), round(la, 2)],
        "score": likely_score(lh, la, ph, pd, pa),
        "pick": pick, "pick_prob": round(100 * pp, 1),
        "dc": dc, "dc_prob": round(100 * dcp, 1),
        "btts": round(100 * (1 - math.exp(-lh)) * (1 - math.exp(-la)), 1),
        "over25": round(100 * (1 - sum(pois(lh + la, k) for k in range(3))), 1),
        "conf": confidence(pp),
    }


# ---------------------------------------------------------------- fase liga y simulación
def league_table(lp_matches, teams_in):
    tbl = {t: {"t": t, "pj": 0, "g": 0, "e": 0, "p": 0, "gf": 0, "gc": 0, "agf": 0, "pts": 0,
               "form": []} for t in teams_in}
    for m in lp_matches:
        if not m.get("done"):
            continue
        h, a, hg, ag = m["h"], m["a"], m["hg"], m["ag"]
        for t, gf, gc, away in ((h, hg, ag, False), (a, ag, hg, True)):
            r = tbl[t]
            r["pj"] += 1
            r["gf"] += gf
            r["gc"] += gc
            if away:
                r["agf"] += gf
            if gf > gc:
                r["g"] += 1
                r["pts"] += 3
                r["form"].append("V")
            elif gf == gc:
                r["e"] += 1
                r["pts"] += 1
                r["form"].append("E")
            else:
                r["p"] += 1
                r["form"].append("D")
    return tbl


def sort_key(r):
    return (-r["pts"], -(r["gf"] - r["gc"]), -r["gf"], -r["agf"], -r["g"])


def play_tie(model, rnd, first_home, second_home, known=None):
    """Eliminatoria a doble partido (second_home juega la vuelta en casa).
    known: lista de partidos ya jugados de la eliminatoria."""
    agg = {first_home: 0, second_home: 0}
    legs = [(first_home, second_home), (second_home, first_home)]
    known = known or []
    played = {(k["h"], k["a"]): k for k in known if k.get("done")}
    for h, a in legs:
        k = played.get((h, a))
        if k:
            agg[h] += k["hg"]
            agg[a] += k["ag"]
            if k.get("pens"):
                return h if k["pens"][0] > k["pens"][1] else a
            if (h, a) == legs[1]:
                if k.get("hw") and agg[h] == agg[a]:
                    return h
                if k.get("aw") and agg[h] == agg[a]:
                    return a
            continue
        lh, la = model.goals(h, a)
        agg[h] += sample_pois(lh, rnd)
        agg[a] += sample_pois(la, rnd)
    if agg[first_home] != agg[second_home]:
        return first_home if agg[first_home] > agg[second_home] else second_home
    return penalties(model, rnd, second_home, first_home)


def penalties(model, rnd, a, b):
    e = 1.0 / (1.0 + 10 ** (-(model.rating(a) - model.rating(b)) / 400.0))
    return a if rnd.random() < 0.5 + (e - 0.5) * 0.3 else b


def play_single(model, rnd, h, a, neutral=True):
    lh, la = model.goals(h, a, neutral)
    gh, ga = sample_pois(lh, rnd), sample_pois(la, rnd)
    if gh != ga:
        return h if gh > ga else a
    # prórroga (un tercio de partido) y penaltis
    gh += sample_pois(lh / 3, rnd)
    ga += sample_pois(la / 3, rnd)
    if gh != ga:
        return h if gh > ga else a
    return penalties(model, rnd, h, a)


def simulate(model, season_ms, lp_teams, sims, seed=7):
    """Simula el resto de la Champions. Devuelve probabilidades por equipo."""
    rnd = random.Random(seed)
    lp = [m for m in season_ms if m["slug"] == "league-phase"]
    lp_done = [m for m in lp if m.get("done")]
    lp_left = [m for m in lp if not m.get("done")]
    ko = {r: [m for m in season_ms if m["slug"] == r] for r in KO_ROUNDS}
    base = league_table(lp_done, lp_teams)
    pre = {}
    for m in lp_left:
        pre[m["id"]] = model.goals(m["h"], m["a"], m["neutral"])
    cnt = {t: defaultdict(int) for t in lp_teams}
    pos_sum = defaultdict(float)
    pts_sum = defaultdict(float)

    def ties_of(r):
        out = defaultdict(list)
        for m in ko[r]:
            out[frozenset((m["h"], m["a"]))].append(m)
        return out

    for _ in range(sims):
        tbl = {t: dict(v) for t, v in base.items()}
        for m in lp_left:
            lh, la = pre[m["id"]]
            hg, ag = sample_pois(lh, rnd), sample_pois(la, rnd)
            for t, gf, gc, away in ((m["h"], hg, ag, False), (m["a"], ag, hg, True)):
                r = tbl[t]
                r["gf"] += gf
                r["gc"] += gc
                if away:
                    r["agf"] += gf
                if gf > gc:
                    r["pts"] += 3
                    r["g"] += 1
                elif gf == gc:
                    r["pts"] += 1
        order = sorted(tbl.values(), key=lambda r: sort_key(r) + (rnd.random(),))
        seeds = [r["t"] for r in order]
        for i, t in enumerate(seeds):
            pos_sum[t] += i + 1
            pts_sum[t] += tbl[t]["pts"]
            if i < 8:
                cnt[t]["top8"] += 1
            elif i < 24:
                cnt[t]["po"] += 1
        rank = {t: i for i, t in enumerate(seeds)}

        def better(x, y):
            return (x, y) if rank.get(x, 99) <= rank.get(y, 99) else (y, x)

        def play_round(rname, pairs):
            known = ties_of(rname)
            if known:   # eliminatorias reales ya sorteadas: se usan tal cual
                pairs = [better(*tuple(k)) for k in known]
            winners = []
            for top, other in pairs:
                winners.append(play_tie(model, rnd, other, top, known.get(frozenset((top, other)), [])))
            return winners, pairs

        # --- playoff: 9/10 vs 23/24, 11/12 vs 21/22, 13/14 vs 19/20, 15/16 vs 17/18
        po_pairs = []
        for k in range(4):
            hi = [seeds[8 + 2 * k], seeds[9 + 2 * k]]
            lo = [seeds[23 - 2 * k], seeds[22 - 2 * k]]
            rnd.shuffle(lo)
            po_pairs += list(zip(hi, lo))
        po_w, po_pairs = play_round("knockout-round-playoffs", po_pairs)
        slot = defaultdict(list)                 # bloque del cuadro según el cabeza de serie
        for (top, _), w in zip(po_pairs, po_w):
            slot[max(0, min(3, (rank.get(top, 8) - 8) // 2))].append(w)
        # octavos: 1/2 vs bloque 15-18, 3/4 vs 13-20, 5/6 vs 11-22, 7/8 vs 9-24
        r16 = []
        for k in range(4):
            tops = [seeds[2 * k], seeds[2 * k + 1]]
            wins = slot.get(3 - k, [])[:2]
            while len(wins) < 2:                 # por si el sorteo real no encaja con el cuadro
                extra = [w for w in po_w if all(w not in s2 for s2 in slot.values())] or po_w
                wins.append(rnd.choice(extra))
            rnd.shuffle(wins)
            r16 += list(zip(tops, wins))
        for t in seeds[:8]:
            cnt[t]["r16"] += 1
        for w in po_w:
            cnt[w]["r16"] += 1
        pairs = r16
        for rname, key in (("round-of-16", "qf"), ("quarterfinals", "sf"), ("semifinals", "final")):
            winners, _ = play_round(rname, pairs)
            for w in winners:
                cnt[w][key] += 1
            pairs = [better(winners[i], winners[i + 1]) for i in range(0, len(winners) - 1, 2)]
        fa, fb = pairs[0]
        kf = [m for m in ko["final"] if m.get("done") and {m["h"], m["a"]} == {fa, fb}]
        if kf:
            m = kf[0]
            if m.get("pens"):
                champ = m["h"] if m["pens"][0] > m["pens"][1] else m["a"]
            else:
                champ = m["h"] if m["hg"] > m["ag"] else m["a"]
        else:
            champ = play_single(model, rnd, fa, fb, True)
        cnt[champ]["win"] += 1
    res = {}
    for t in lp_teams:
        c = cnt[t]
        res[t] = {k: round(100.0 * c[k] / sims, 1) for k in ("top8", "po", "r16", "qf", "sf", "final", "win")}
        res[t]["out"] = round(100.0 - res[t]["top8"] - res[t]["po"], 1)
        res[t]["pos"] = round(pos_sum[t] / sims, 1)
        res[t]["xpts"] = round(pts_sum[t] / sims, 1)
    return res, base


# ---------------------------------------------------------------- historial
def settle(history, by_id):
    for p in history:
        if p.get("result"):
            continue
        m = by_id.get(p["id"])
        if not m or not m.get("done"):
            continue
        out = "1" if m["hg"] > m["ag"] else ("X" if m["hg"] == m["ag"] else "2")
        p["final"] = f'{m["hg"]}-{m["ag"]}'
        p["result"] = out
        p["win"] = out == p["pick"]
        p["dc_win"] = out in p["dc"]
        p["exact"] = p["final"] == p["score"]


def stats(picks):
    n = len(picks)
    if not n:
        return {"n": 0, "hits": 0, "rate": 0, "dc_rate": 0, "exact": 0}
    hits = sum(1 for p in picks if p["win"])
    dch = sum(1 for p in picks if p.get("dc_win"))
    ex = sum(1 for p in picks if p.get("exact"))
    return {"n": n, "hits": hits, "rate": round(100 * hits / n, 1),
            "dc_hits": dch, "dc_rate": round(100 * dch / n, 1), "exact": ex}


# ---------------------------------------------------------------- principal
def main():
    now = datetime.now(timezone.utc)
    today = today_utc()
    log("Descargando partidos…")
    matches, teams, cache, cache_path, failed = load_all(today)
    done = [m for m in matches if m.get("done")]
    if len(done) < 1500:
        log(f"Muy pocos partidos jugados ({len(done)}); no se actualiza nada.")
        sys.exit(1)
    log(f"Partidos jugados: {len(done)}")
    elo, games, trend, ehist, calib, pre_elo = run_elo(matches)
    cal = Calibrator(calib)
    model = Model(elo, games, cal)

    # temporada actual de la Champions
    season = season_start(today)
    cl = [m for m in matches if m["code"] == CL]
    cl_season = [m for m in cl if m.get("year") == season and m["date"][:10] >= f"{season}-07-01"]
    lp = [m for m in cl_season if m["slug"] == "league-phase"]
    lp_teams = sorted({m["h"] for m in lp} | {m["a"] for m in lp})
    log(f"Champions {season}-{(season + 1) % 100:02d}: {len(cl_season)} partidos, fase liga {len(lp)} ({len(lp_teams)} equipos)")

    # jornada de cada partido de la fase liga = n.º de partido del equipo
    nth = defaultdict(int)
    md = {}
    for m in sorted(lp, key=lambda x: x["date"]):
        nth[m["h"]] += 1
        nth[m["a"]] += 1
        md[m["id"]] = max(nth[m["h"]], nth[m["a"]])

    def team_out(t):
        i = teams.get(t, {})
        return {"id": t, "n": i.get("n", t), "a": i.get("a", ""), "logo": i.get("logo", ""),
                "c": i.get("c") or TEAM_COUNTRY.get(i.get("full", "")) or COUNTRY_ISO.get(i.get("vc", ""), ""),
                "elo": round(model.rating(t)), "tr": arrow(trend.get(t, []))}

    # próximos partidos y pronósticos (21 días)
    hist_path = os.path.join(OUT_DIR, "history.json")
    history = []
    if os.path.exists(hist_path):
        with open(hist_path, encoding="utf-8") as f:
            history = json.load(f)
    by_id = {m["id"]: m for m in cl}
    settle(history, by_id)

    upcoming = []
    limit = (now + timedelta(days=21)).isoformat()
    for m in sorted(cl_season, key=lambda x: x["date"]):
        if m.get("done") or m["state"] == "post" or m["date"] > limit:
            continue
        if m["date"] < (now - timedelta(hours=3)).strftime("%Y-%m-%dT%H:%MZ"):
            continue
        pr = predict(model, m)
        item = {"id": m["id"], "date": m["date"], "round": ROUND_ES.get(m["slug"], m["slug"]),
                "md": md.get(m["id"]), "live": m["state"] == "in",
                "h": team_out(m["h"]), "a": team_out(m["a"]),
                "venue": m.get("venue", ""), "tv": m.get("tv", [])} | pr
        upcoming.append(item)
    log(f"Pronósticos: {len(upcoming)}")

    known = {p["id"] for p in history}
    for u in upcoming:
        rec = {"id": u["id"], "date": u["date"], "round": u["round"], "md": u["md"],
               "h": u["h"]["n"], "a": u["a"]["n"], "hl": u["h"]["logo"], "al": u["a"]["logo"],
               "pick": u["pick"], "pick_prob": u["pick_prob"], "dc": u["dc"], "score": u["score"],
               "conf": u["conf"], "prob": u["prob"]}
        if u["id"] not in known:
            history.append(rec | {"created": now.isoformat(timespec="minutes")})
        else:
            for p in history:
                if p["id"] == u["id"] and not p.get("result") and not u["live"]:
                    p.update(rec)
    # partidos de esta temporada jugados antes de que existiera el historial:
    # se recalculan con el Elo que tenían los equipos justo antes de jugarlos
    known = {p["id"] for p in history}
    for m in cl_season:
        if not m.get("done") or m["id"] in known or m["id"] not in pre_elo:
            continue
        rh, ra = pre_elo[m["id"]]
        ph, pd, pa = cal.probs(rh + (0 if m["neutral"] else HOME_ADV) - ra)
        lh, la = lambdas(ph, pa)
        pick, pp = max((("1", ph), ("X", pd), ("2", pa)), key=lambda x: x[1])
        ti, ta = teams.get(m["h"], {}), teams.get(m["a"], {})
        history.append({"id": m["id"], "date": m["date"], "round": ROUND_ES.get(m["slug"], m["slug"]),
                        "md": md.get(m["id"]), "h": ti.get("n", m["h"]), "a": ta.get("n", m["a"]),
                        "hl": ti.get("logo", ""), "al": ta.get("logo", ""), "pick": pick,
                        "pick_prob": round(100 * pp, 1), "dc": "1X" if ph >= pa else "X2",
                        "score": likely_score(lh, la, ph, pd, pa), "conf": confidence(pp),
                        "prob": [round(100 * ph, 1), round(100 * pd, 1), round(100 * pa, 1)], "retro": True})
    settle(history, by_id)
    history.sort(key=lambda p: p["date"])
    history = history[-HISTORY_KEEP:]
    settled = [p for p in history if p.get("result")]
    strong = [p for p in settled if p["conf"] >= 7]
    cur = [p for p in settled if p["date"][:10] >= f"{season}-07-01"]

    # clasificación y simulación
    table, title = [], []
    if len(lp_teams) >= 24 and len(lp) >= 100:
        sim, base = simulate(model, cl_season, lp_teams, SIMS)
        rows = sorted(base.values(), key=lambda r: sort_key(r) + (-model.rating(r["t"]),))
        for i, r in enumerate(rows):
            t = r["t"]
            nxt = next(({"vs": (m["a"] if m["h"] == t else m["h"]), "home": m["h"] == t, "date": m["date"]}
                        for m in sorted(lp, key=lambda x: x["date"]) if not m.get("done") and t in (m["h"], m["a"])), None)
            if nxt:
                nxt["vs"] = teams.get(nxt["vs"], {}).get("n", nxt["vs"])
            table.append({"pos": i + 1, **team_out(t), "pj": r["pj"], "g": r["g"], "e": r["e"], "p": r["p"],
                          "gf": r["gf"], "gc": r["gc"], "dg": r["gf"] - r["gc"], "pts": r["pts"],
                          "form": r["form"][-5:], "next": nxt, "sim": sim[t]})
        title = sorted(({**team_out(t), **sim[t]} for t in lp_teams), key=lambda x: (-x["win"], -x["elo"]))
    lp_done = sum(1 for m in lp if m.get("done"))

    # resultados recientes de la Champions con su pronóstico
    recent = []
    for p in reversed(settled[-150:]):
        recent.append(p)

    # ranking Elo: equipos de la Champions y top europeo
    def elo_rows(ts, n):
        rows = sorted(((round(model.rating(t)), t) for t in ts if games.get(t, 0) >= 10), reverse=True)[:n]
        out = []
        for e, t in rows:
            d = team_out(t)
            h = ehist.get(t, [])
            # Elo hace ~30 días para ver la tendencia
            ref = next((v for dte, v in reversed(h) if dte <= (today - timedelta(days=30)).isoformat()), None)
            d["d30"] = e - ref if ref is not None else 0
            d["spark"] = [v for _, v in h[-12:]]
            out.append(d)
        return out

    europe_teams = {t for m in done if m["code"] in UEFA and m["date"][:10] >= f"{season - 1}-07-01"
                    for t in (m["h"], m["a"])}
    data = {
        "generated": now.isoformat(timespec="minutes"),
        "season": f"{season}-{(season + 1) % 100:02d}",
        "phase": {"lp_total": len(lp), "lp_done": lp_done,
                  "md_done": max([md[m["id"]] for m in lp if m.get("done")] or [0]),
                  "ko_started": any(m["slug"] in KO_ROUNDS for m in cl_season)},
        "upcoming": upcoming,
        "recent": recent,
        "retro": sum(1 for p in settled if p.get("retro")),
        "stats": {"all": stats(settled[-300:]), "strong": stats(strong[-300:]), "season": stats(cur),
                  "season_strong": stats([p for p in cur if p["conf"] >= 7])},
        "table": table,
        "title": title[:36],
        "elo_cl": elo_rows(lp_teams, 36),
        "elo_europe": elo_rows(europe_teams, 50),
        "model": {"k": K, "k_euro": K_EURO, "home_adv": HOME_ADV, "matches": len(done),
                  "calib": len(calib), "sims": SIMS, "leagues": len(LEAGUES), "failed": failed},
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "data.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    with open(hist_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=0)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, separators=(",", ":"))
    log("OK: data.json, history.json y results.json actualizados")


def arrow(tr):
    s = sum(tr)
    return 1 if s > 8 else (-1 if s < -8 else 0)


if __name__ == "__main__":
    main()
