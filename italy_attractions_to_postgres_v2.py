#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Italy Attractions Image Ingestor (v2 - hardened)
------------------------------------------------
Fixes & improvements:
- Robust handling of Wikidata P18 values (Special:FilePath, /File:, Unicode, spaces).
- MediaWiki API now called with redirects & normalization.
- HTTP session with retries/backoff and Wikimedia-friendly headers.
- Fallback to original URL if thumbnail 404.
- Better city QID resolution inside Italy (filtering by country).
- Graceful handling of SVG/TIFF (thumbnail still requested).
"""
import os, io, re, time, argparse, sys, hashlib
from typing import Dict, List, Optional, Tuple
import requests
from requests.adapters import HTTPAdapter, Retry
import psycopg2, psycopg2.extras
from urllib.parse import unquote

WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
WIKIDATA_SEARCH = "https://www.wikidata.org/w/api.php"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"

DEFAULT_CITIES = ["Roma","Milano","Napoli","Torino","Palermo","Genova","Bologna","Firenze","Venezia","Verona","Siena","Pisa","Bari","Catania","Trieste","Parma","Modena","Ravenna","Perugia","Lecce"]

USER_AGENT = ("ItalyAttractionsCollector/1.1 (+https://example.com/contact) requests-retry; purpose=educational")

def session():
    s = requests.Session()
    retries = Retry(total=6, connect=3, read=3, backoff_factor=0.8,
                    status_forcelist=[429,500,502,503,504], allowed_methods=["GET","HEAD"], raise_on_status=False)
    adapter = HTTPAdapter(max_retries=retries, pool_maxsize=20)
    s.mount("https://", adapter); s.mount("http://", adapter)
    s.headers.update({"User-Agent": USER_AGENT})
    return s
S = session()

def log(m): print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {m}", flush=True)

def db():
    url = os.getenv("DATABASE_URL")
    if not url: raise RuntimeError("DATABASE_URL not set")
    c = psycopg2.connect(url); c.autocommit = True; return c

SCHEMA = r"""
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

INS = r"""
INSERT INTO attraction_images (
  source, source_id, attraction_qid, city, attraction_name, license, license_url, creator,
  attribution, original_url, thumb_url, img_bytes, mime_type, width, height, sha256
) VALUES (
  %(source)s, %(source_id)s, %(attraction_qid)s, %(city)s, %(attraction_name)s, %(license)s, %(license_url)s, %(creator)s,
  %(attribution)s, %(original_url)s, %(thumb_url)s, %(img_bytes)s, %(mime_type)s, %(width)s, %(height)s, %(sha256)s
)
ON CONFLICT ON CONSTRAINT uq_qid DO NOTHING
"""

def GET(url, params=None, headers=None, stream=False):
    r = S.get(url, params=params, headers=headers or {}, timeout=45, stream=stream, allow_redirects=True)
    r.raise_for_status(); return r

def qid_for_city(name:str)->Optional[str]:
    p={"action":"wbsearchentities","search":name,"language":"it","format":"json","type":"item","limit":10}
    try:
        d=GET(WIKIDATA_SEARCH,params=p).json()
        for ent in d.get("search",[]) or []:
            desc=(ent.get("description") or "").lower()
            if any(t in desc for t in ["italia","italian","comune","città","metropolitana di"]):
                return ent["id"]
        if d.get("search"): return d["search"][0]["id"]
    except Exception as e: log(f"qid_for_city error {name}: {e}")
    return None

def sparql(city_qid:str, limit:int)->str:
    return f"""
SELECT ?item ?itemLabel ?image ?coord WHERE {{
  ?item wdt:P31/wdt:P279* wd:Q570116;
        wdt:P131* wd:{city_qid};
        wdt:P625 ?coord.
  OPTIONAL {{ ?item wdt:P18 ?image. }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "it,en". }}
}}
LIMIT {limit}
"""

def run_sparql(q:str)->List[Dict]:
    h={"Accept":"application/sparql-results+json","User-Agent":USER_AGENT}
    r=S.get(WIKIDATA_SPARQL,params={"query":q},headers=h,timeout=60); r.raise_for_status()
    return r.json().get("results",{}).get("bindings",[])

def file_title_from_p18(v:str)->Optional[str]:
    if not v: return None
    v=v.strip()
    if v.startswith("File:"): return v.replace(" ","_")
    if v.startswith("http"):
        u=unquote(v)
        m=re.search(r"/File:([^?#]+)",u,re.I)
        if m: return "File:"+m.group(1).replace(" ","_")
        m=re.search(r"/Special:FilePath/([^?#]+)",u,re.I)
        if m: return "File:"+m.group(1).replace(" ","_")
    return None

def commons_info(file_title:str, width:int=1280)->Optional[Dict]:
    p={"action":"query","format":"json","prop":"imageinfo","titles":file_title,
       "iiprop":"url|mime|size|extmetadata","iiurlwidth":width,"redirects":1,"origin":"*"}
    try:
        d=GET(COMMONS_API,params=p).json()
        for _,page in (d.get("query",{}).get("pages",{}) or {}).items():
            ii=page.get("imageinfo",[]) or []
            if not ii: continue
            info=ii[0]; ext=info.get("extmetadata",{}) or {}
            creator=(ext.get("Artist",{}) or {}).get("value") or ""
            lic=(ext.get("LicenseShortName",{}) or {}).get("value") or ""
            licu=(ext.get("LicenseUrl",{}) or {}).get("value") or ""
            credit=(ext.get("Credit",{}) or {}).get("value") or ""
            attr=f"{creator} – {lic}".strip(" –") if (creator or lic) else (credit or "")
            return {
                "original_url":info.get("url"),
                "thumb_url":info.get("thumburl") or info.get("url"),
                "mime_type":info.get("mime"),
                "width":info.get("thumbwidth") or info.get("width"),
                "height":info.get("thumbheight") or info.get("height"),
                "creator":creator,"license":lic,"license_url":licu,"attribution":attr
            }
    except Exception as e:
        log(f"commons_info error {file_title}: {e}")
    return None

def download(url:str)->Tuple[bytes,Optional[str]]:
    r=GET(url,stream=True); buf=io.BytesIO()
    for ch in r.iter_content(65536):
        if ch: buf.write(ch)
    return buf.getvalue(), r.headers.get("Content-Type")

def sha256(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def ensure_schema(conn):
    with conn.cursor() as cur: cur.execute(SCHEMA)

def insert_row(conn,row:Dict)->bool:
    try:
        with conn.cursor() as cur: cur.execute(INS,row)
        return True
    except Exception as e:
        log(f"Insert skipped/failed {row.get('attraction_qid')} ({row.get('source_id')}): {e}")
        return False

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--cities",type=str,default=",".join(DEFAULT_CITIES))
    ap.add_argument("--cities-file",type=str,default=None)
    ap.add_argument("--limit",type=int,default=500)
    ap.add_argument("--thumb-width",type=int,default=1280)
    a=ap.parse_args()

    if a.cities_file and os.path.exists(a.cities_file):
        with open(a.cities_file,"r",encoding="utf-8") as f:
            cities=[ln.strip() for ln in f if ln.strip()]
    else:
        cities=[c.strip() for c in a.cities.split(",") if c.strip()]
    if not cities: log("No cities"); sys.exit(1)

    conn=db(); ensure_schema(conn)
    total=0
    for city in cities:
        log(f"Resolve QID: {city}")
        qid=qid_for_city(city)
        if not qid: log(f"  no QID for {city}"); continue
        log(f"  {city} -> {qid}")
        try:
            rows=run_sparql(sparql(qid,a.limit))
        except Exception as e:
            log(f"  SPARQL error {city}: {e}"); continue
        log(f"  attractions: {len(rows)}")

        for b in rows:
            q=b["item"]["value"].rsplit("/",1)[-1]
            label=b.get("itemLabel",{}).get("value","")
            ft=file_title_from_p18(b.get("image",{}).get("value",""))
            if not ft: continue
            info=commons_info(ft,a.thumb_width)
            if not info: continue
            url=info.get("thumb_url") or info.get("original_url")
            if not url: continue

            try:
                bytes_, mime = download(url)
            except requests.HTTPError:
                if info.get("original_url"):
                    try: bytes_, mime = download(info["original_url"])
                    except Exception as e: log(f"  download fail {ft}: {e}"); continue
                else:
                    continue
            except Exception as e:
                log(f"  download fail {ft}: {e}"); continue

            row={
                "source":"wikimedia",
                "source_id":ft,
                "attraction_qid":q,
                "city":city,
                "attraction_name":label,
                "license":info.get("license"),
                "license_url":info.get("license_url"),
                "creator":info.get("creator"),
                "attribution":info.get("attribution"),
                "original_url":info.get("original_url"),
                "thumb_url":info.get("thumb_url"),
                "img_bytes":psycopg2.Binary(bytes_),
                "mime_type":info.get("mime_type") or mime,
                "width":info.get("width"),
                "height":info.get("height"),
                "sha256":sha256(bytes_),
            }
            if insert_row(conn,row):
                total+=1
                if total % 25 == 0: log(f"Inserted so far: {total}")
        log(f"Done {city} — total: {total}")
    log(f"ALL DONE — inserted: {total}")

if __name__=="__main__":
    main()
