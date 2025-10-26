#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Italy Attractions Image Ingestor (v3_fixed - NO WDQS + robust downloads)
------------------------------------------------------------------------
- Evita WDQS (usa solo le API MediaWiki di Wikidata).
- Pescaggio item con `haswbstatement` per P131 (città) + P31 (classe).
- Prelievo P18 via wbgetentities.
- Download thumbs 1280px da Commons con retry/backoff e fallback all'originale.
- Flag --debug per loggare URL e status in chiaro.
- Supporto proxy via env (HTTP_PROXY/HTTPS_PROXY) e timeout configurabili.

Esempio:
  export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
  python italy_attractions_to_postgres_v3_fixed.py --cities "Roma" --per-class-limit 300 --debug
"""
import os
import io
import time
import argparse
import sys
import hashlib
from typing import Dict, List, Optional, Tuple
import requests
from requests.adapters import HTTPAdapter, Retry
import psycopg2
import psycopg2.extras

WIKIDATA_API = "https://www.wikidata.org/w/api.php"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
DEFAULT_CITIES = ["Roma", "Milano", "Napoli", "Torino", "Palermo", "Genova", "Bologna", "Firenze", "Venezia",
                  "Verona", "Siena", "Pisa", "Bari", "Catania", "Trieste", "Parma", "Modena", "Ravenna", "Perugia", "Lecce"]
DEFAULT_CLASSES = ["Q570116", "Q33506", "Q34627",
                   "Q839954", "Q4989906", "Q23413", "Q207694"]
UA = "ItalyAttractionsCollector/3.1-no-wdqs (+https://example.com/contact) mw-search"


def make_session(connect_timeout: int, read_timeout: int) -> requests.Session:
    s = requests.Session()
    retries = Retry(
        total=6, connect=3, read=3, backoff_factor=0.8,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD", "POST"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries, pool_maxsize=20)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    s.headers.update({"User-Agent": UA})
    # timeouts
    s.request = _timeout_wrapper(
        s.request, connect_timeout, read_timeout)  # type: ignore
    return s


def _timeout_wrapper(fn, connect_timeout, read_timeout):
    def wrapped(method, url, **kwargs):
        timeout = kwargs.get("timeout", (connect_timeout, read_timeout))
        if isinstance(timeout, (int, float)):
            timeout = (timeout, timeout)
        kwargs["timeout"] = timeout
        return fn(method, url, **kwargs)
    return wrapped


def log(msg: str):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def db_connect() -> psycopg2.extensions.connection:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL not set")
    conn = psycopg2.connect(url)
    conn.autocommit = True
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS attraction_images (
  id BIGSERIAL PRIMARY KEY,
  source VARCHAR(32) NOT NULL,
  source_id TEXT,
  attraction_qid TEXT,
  city TEXT,
  attraction_name TEXT,
  license TEXT,
  license_url TEXT,
  creator TEXT,
  attribution TEXT,
  original_url TEXT,
  thumb_url TEXT,
  fetched_at TIMESTAMPTZ DEFAULT now(),
  img_bytes BYTEA,
  mime_type TEXT,
  width INT,
  height INT,
  sha256 TEXT
);
CREATE INDEX IF NOT EXISTS idx_city ON attraction_images (LOWER(city));
CREATE UNIQUE INDEX IF NOT EXISTS uq_source_sid ON attraction_images (source, source_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_qid ON attraction_images (attraction_qid);
"""

INS = """
INSERT INTO attraction_images (
  source, source_id, attraction_qid, city, attraction_name, license, license_url, creator,
  attribution, original_url, thumb_url, img_bytes, mime_type, width, height, sha256
) VALUES (
  %(source)s, %(source_id)s, %(attraction_qid)s, %(city)s, %(attraction_name)s, %(license)s, %(license_url)s, %(creator)s,
  %(attribution)s, %(original_url)s, %(thumb_url)s, %(img_bytes)s, %(mime_type)s, %(width)s, %(height)s, %(sha256)s
)
ON CONFLICT DO NOTHING
"""


def city_qid(sess: requests.Session, name: str, debug=False) -> Optional[str]:
    r = sess.get(WIKIDATA_API, params={
        "action": "wbsearchentities", "search": name, "language": "it", "format": "json", "type": "item", "limit": 10
    }, allow_redirects=True)
    r.raise_for_status()
    data = r.json()
    for e in data.get("search", []) or []:
        desc = (e.get("description") or "").lower()
        if any(t in desc for t in ["italia", "italian", "comune", "città", "metropolitana di"]):
            return e["id"]
    return (data.get("search") or [{}])[0].get("id")


def search_items(sess: requests.Session, city_qid: str, class_qid: str, max_results: int, debug=False) -> List[str]:
    q = f'haswbstatement:P131={city_qid} haswbstatement:P31={class_qid}'
    qids: List[str] = []
    sroff = 0
    while len(qids) < max_results:
        r = sess.get(WIKIDATA_API, params={
            "action": "query", "format": "json", "list": "search", "srsearch": q, "srlimit": 50, "sroffset": sroff
        }, allow_redirects=True)
        r.raise_for_status()
        j = r.json()
        hits = j.get("query", {}).get("search", []) or []
        if not hits:
            break
        for h in hits:
            title = h.get("title", "")
            if title.startswith("Q"):
                qids.append(title)
                if len(qids) >= max_results:
                    break
        if "continue" in j and "sroffset" in j["continue"]:
            sroff = j["continue"]["sroffset"]
        else:
            break
        time.sleep(0.25)
    if debug:
        log(f"    search {class_qid} -> {len(qids)} QIDs")
    return qids


def chunked(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i+n]


def get_entities(sess: requests.Session, qids: List[str], debug=False) -> Dict[str, Dict]:
    result: Dict[str, Dict] = {}
    for chunk in chunked(qids, 50):
        r = sess.get(WIKIDATA_API, params={
            "action": "wbgetentities", "format": "json", "ids": "|".join(chunk), "props": "labels|claims"
        }, allow_redirects=True)
        r.raise_for_status()
        ents = r.json().get("entities", {}) or {}
        result.update(ents)
        time.sleep(0.2)
    if debug:
        log(f"    fetched entities: {len(result)}")
    return result


def label_it_or_en(entity: Dict) -> str:
    labels = entity.get("labels", {})
    return (labels.get("it") or labels.get("en") or {}).get("value", "")


def p18_titles(entity: Dict) -> List[str]:
    claims = (entity.get("claims", {}) or {}).get("P18", []) or []
    titles: List[str] = []
    for c in claims:
        val = ((c.get("mainsnak", {}) or {}).get(
            "datavalue", {}) or {}).get("value")
        if isinstance(val, str):
            titles.append("File:" + val.replace(" ", "_"))
    return titles


def commons_info(sess: requests.Session, title: str, width: int = 1280, debug=False) -> Optional[Dict]:
    r = sess.get(COMMONS_API, params={
        "action": "query", "format": "json", "prop": "imageinfo", "titles": title,
        "iiprop": "url|mime|size|extmetadata", "iiurlwidth": width, "redirects": 1, "origin": "*"
    }, allow_redirects=True)
    r.raise_for_status()
    j = r.json()
    pages = j.get("query", {}).get("pages", {}) or {}
    for _, page in pages.items():
        ii = page.get("imageinfo", []) or []
        if not ii:
            continue
        info = ii[0]
        ext = info.get("extmetadata", {}) or {}
        creator = (ext.get("Artist", {}) or {}).get("value") or ""
        lic = (ext.get("LicenseShortName", {}) or {}).get("value") or ""
        licu = (ext.get("LicenseUrl", {}) or {}).get("value") or ""
        credit = (ext.get("Credit", {}) or {}).get("value") or ""
        attr = f"{creator} – {lic}".strip(" –") if (
            creator or lic) else (credit or "")
        out = {
            "original_url": info.get("url"),
            "thumb_url": info.get("thumburl") or info.get("url"),
            "mime_type": info.get("mime"),
            "width": info.get("thumbwidth") or info.get("width"),
            "height": info.get("thumbheight") or info.get("height"),
            "creator": creator, "license": lic, "license_url": licu, "attribution": attr
        }
        if debug:
            log(
                f"    commons {title} -> thumb={out['thumb_url']} orig={out['original_url']}")
        return out
    return None


def download_with_retry(sess: requests.Session, url: str, debug=False) -> Tuple[bytes, Optional[str]]:
    # Try GET (thumb); on 404 or other errors, bubble up to caller
    if debug:
        log(f"    download: GET {url}")
    r = sess.get(url, stream=True, allow_redirects=True)
    if debug:
        log(f"    status: {r.status_code}")
    r.raise_for_status()
    buf = io.BytesIO()
    for ch in r.iter_content(65536):
        if ch:
            buf.write(ch)
    return buf.getvalue(), r.headers.get("Content-Type")


def ensure_schema(conn):
    with conn.cursor() as cur:
        cur.execute(SCHEMA)


def insert_row(conn, row: Dict) -> bool:
    try:
        with conn.cursor() as cur:
            cur.execute(INS, row)
        return True
    except Exception as e:
        log(f"Insert skipped/failed {row.get('attraction_qid')} ({row.get('source_id')}): {e}")
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cities", type=str, default=",".join(DEFAULT_CITIES))
    ap.add_argument("--cities-file", type=str, default=None)
    ap.add_argument("--classes", type=str, default=",".join(DEFAULT_CLASSES))
    ap.add_argument("--per-class-limit", type=int, default=400)
    ap.add_argument("--thumb-width", type=int, default=1280)
    ap.add_argument("--connect-timeout", type=int, default=15)
    ap.add_argument("--read-timeout", type=int, default=60)
    ap.add_argument("--debug", action="store_true")
    a = ap.parse_args()

    sess = make_session(a.connect_timeout, a.read_timeout)

    # cities
    if a.cities_file and os.path.exists(a.cities_file):
        with open(a.cities_file, "r", encoding="utf-8") as f:
            cities = [ln.strip() for ln in f if ln.strip()]
    else:
        cities = [c.strip() for c in a.cities.split(",") if c.strip()]
    classes = [c.strip() for c in a.classes.split(",") if c.strip()]
    if not cities:
        log("No cities")
        sys.exit(1)

    conn = db_connect()
    ensure_schema(conn)
    total = 0

    for city in cities:
        log(f"Resolve QID: {city}")
        try:
            cqid = city_qid(sess, city, debug=a.debug)
        except Exception as e:
            log(f"  city_qid error {city}: {e}")
            continue
        if not cqid:
            log(f"  no QID for {city}")
            continue
        log(f"  {city} -> {cqid}")

        all_qids = set()
        for cls in classes:
            log(f"  search class {cls}")
            try:
                ids = search_items(
                    sess, cqid, cls, max_results=a.per_class_limit, debug=a.debug)
                log(f"    found {len(ids)} items")
                all_qids.update(ids)
            except Exception as e:
                log(f"    search error class {cls}: {e}")
            time.sleep(0.2)

        if not all_qids:
            log(f"  No items found for {city}")
            continue

        ents = get_entities(sess, sorted(all_qids), debug=a.debug)

        for qid, ent in ents.items():
            label = label_it_or_en(ent)
            titles = p18_titles(ent)
            if not titles:
                continue

            ft = titles[0]  # primo P18
            info = commons_info(sess, ft, a.thumb_width, debug=a.debug)
            if not info:
                continue
            url = info.get("thumb_url") or info.get("original_url")
            if not url:
                continue

            # prova thumb → fallback originale
            try:
                data, mime = download_with_retry(sess, url, debug=a.debug)
            except requests.HTTPError as e:
                if a.debug:
                    log(f"    thumb failed: {e}")
                if info.get("original_url"):
                    try:
                        data, mime = download_with_retry(
                            sess, info["original_url"], debug=a.debug)
                    except Exception as e2:
                        log(f"  download fail {ft}: {e2}")
                        continue
                else:
                    continue
            except Exception as e:
                log(f"  download fail {ft}: {e}")
                continue

            row = {
                "source": "wikimedia", "source_id": ft, "attraction_qid": qid, "city": city, "attraction_name": label,
                "license": info.get("license"), "license_url": info.get("license_url"), "creator": info.get("creator"),
                "attribution": info.get("attribution"), "original_url": info.get("original_url"), "thumb_url": info.get("thumb_url"),
                "img_bytes": psycopg2.Binary(data), "mime_type": info.get("mime_type") or mime,
                "width": info.get("width"), "height": info.get("height"),
                "sha256": hashlib.sha256(data).hexdigest()
            }
            ok = insert_row(conn, row)
            if ok:
                total += 1
                if total % 25 == 0:
                    log(f"Inserted so far: {total}")

        log(f"Done {city} — total: {total}")

    log(f"ALL DONE — inserted: {total}")


if __name__ == "__main__":
    main()
