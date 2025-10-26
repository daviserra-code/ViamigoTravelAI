#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
UA = "ItalyAttractionsCollector/1.2 (+https://example.com/contact) wdqs-retry"

def sess():
    s=requests.Session()
    r=Retry(total=6,connect=3,read=3,backoff_factor=0.8,status_forcelist=[429,500,502,503,504],allowed_methods=["GET","HEAD","POST"],raise_on_status=False)
    a=HTTPAdapter(max_retries=r,pool_maxsize=20)
    s.mount("https://",a); s.mount("http://",a); s.headers.update({"User-Agent":UA}); return s
S=sess()
log=lambda m:print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {m}",flush=True)

def db():
    url=os.getenv("DATABASE_URL"); 
    if not url: raise RuntimeError("DATABASE_URL not set")
    c=psycopg2.connect(url); c.autocommit=True; return c

SCHEMA="""
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
INS="""
INSERT INTO attraction_images (
  source, source_id, attraction_qid, city, attraction_name, license, license_url, creator,
  attribution, original_url, thumb_url, img_bytes, mime_type, width, height, sha256
) VALUES (
  %(source)s, %(source_id)s, %(attraction_qid)s, %(city)s, %(attraction_name)s, %(license)s, %(license_url)s, %(creator)s,
  %(attribution)s, %(original_url)s, %(thumb_url)s, %(img_bytes)s, %(mime_type)s, %(width)s, %(height)s, %(sha256)s
)
ON CONFLICT ON CONSTRAINT uq_qid DO NOTHING
"""
GET=lambda url,**kw:S.get(url,timeout=45,allow_redirects=True,**kw).raise_for_status() or S.get(url,timeout=45,allow_redirects=True,**kw)
POST=lambda url,**kw:S.post(url,timeout=120,**kw).raise_for_status() or S.post(url,timeout=120,**kw)

def city_qid(name:str)->Optional[str]:
    d=GET(WIKIDATA_SEARCH,params={"action":"wbsearchentities","search":name,"language":"it","format":"json","type":"item","limit":10}).json()
    for e in d.get("search",[]) or []:
        desc=(e.get("description") or "").lower()
        if any(t in desc for t in ["italia","italian","comune","città","metropolitana di"]): return e["id"]
    return (d.get("search") or [{}])[0].get("id")

def build_query(qid:str,limit:int,require_image:bool)->str:
    return f"""SELECT ?item ?itemLabel ?image ?coord WHERE {{
  ?item wdt:P31/wdt:P279* wd:Q570116;
        wdt:P131* wd:{qid};
        wdt:P625 ?coord.
  OPTIONAL {{ ?item wdt:P18 ?image. }}
  {'FILTER EXISTS { ?item wdt:P18 ?image }' if require_image else ''}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "it,en". }}
}} LIMIT {limit}"""

def run_wdqs(qid:str,start:int)->List[Dict]:
    limits=[start,max(200,start//2),200,150,100]
    for reqimg in (False,True):
        for L in limits:
            try:
                time.sleep(1.0)
                r=POST(WIKIDATA_SPARQL,data={"query":build_query(qid,L,reqimg)},headers={"Accept":"application/sparql-results+json","User-Agent":UA})
                rows=r.json().get("results",{}).get("bindings",[])
                log(f"  WDQS ok L={L} reqimg={reqimg} rows={len(rows)}"); return rows
            except requests.RequestException as e:
                log(f"  WDQS retry L={L} reqimg={reqimg}: {e}"); time.sleep(2.0)
    raise RuntimeError("WDQS failed after retries")

def file_title(v:str)->Optional[str]:
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

def commons_info(title:str,width:int=1280)->Optional[Dict]:
    d=GET(COMMONS_API,params={"action":"query","format":"json","prop":"imageinfo","titles":title,"iiprop":"url|mime|size|extmetadata","iiurlwidth":width,"redirects":1,"origin":"*"}).json()
    for _,page in (d.get("query",{}).get("pages",{}) or {}).items():
        ii=page.get("imageinfo",[]) or []
        if not ii: continue
        info=ii[0]; ext=info.get("extmetadata",{}) or {}
        creator=(ext.get("Artist",{}) or {}).get("value") or ""
        lic=(ext.get("LicenseShortName",{}) or {}).get("value") or ""
        licu=(ext.get("LicenseUrl",{}) or {}).get("value") or ""
        credit=(ext.get("Credit",{}) or {}).get("value") or ""
        attr=f"{creator} – {lic}".strip(" –") if (creator or lic) else (credit or "")
        return {"original_url":info.get("url"),"thumb_url":info.get("thumburl") or info.get("url"),
                "mime_type":info.get("mime"),"width":info.get("thumbwidth") or info.get("width"),
                "height":info.get("thumbheight") or info.get("height"),"creator":creator,"license":lic,
                "license_url":licu,"attribution":attr}
    return None

def download(url:str)->Tuple[bytes,Optional[str]]:
    r=GET(url,stream=True); buf=io.BytesIO()
    for ch in r.iter_content(65536):
        if ch: buf.write(ch)
    return buf.getvalue(), r.headers.get("Content-Type")

def ensure_schema(conn):
    with conn.cursor() as cur: cur.execute(SCHEMA)

def insert_row(conn,row:Dict)->bool:
    try:
        with conn.cursor() as cur: cur.execute(INS,row); return True
    except Exception as e:
        log(f"Insert skipped/failed {row.get('attraction_qid')} ({row.get('source_id')}): {e}"); return False

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--cities",type=str,default=",".join(DEFAULT_CITIES))
    ap.add_argument("--cities-file",type=str,default=None)
    ap.add_argument("--limit",type=int,default=500)
    ap.add_argument("--thumb-width",type=int,default=1280)
    a=ap.parse_args()

    cities=[c.strip() for c in (open(a.cities_file,"r",encoding="utf-8").read().splitlines() if (a.cities_file and os.path.exists(a.cities_file)) else a.cities.split(",")) if c.strip()]
    if not cities: log("No cities"); sys.exit(1)

    conn=db(); ensure_schema(conn)
    total=0
    for city in cities:
        log(f"Resolve QID: {city}")
        try: qid=city_qid(city)
        except Exception as e: log(f"  QID error {city}: {e}"); continue
        if not qid: log(f"  no QID for {city}"); continue
        log(f"  {city} -> {qid}")

        try: rows=run_wdqs(qid, a.limit)
        except Exception as e: log(f"  SPARQL error for {city}: {e}"); continue
        log(f"  attractions: {len(rows)}")

        for b in rows:
            q=b["item"]["value"].rsplit("/",1)[-1]
            label=b.get("itemLabel",{}).get("value","")
            ft=file_title(b.get("image",{}).get("value",""))
            if not ft: continue
            info=commons_info(ft,a.thumb_width)
            if not info: continue
            url=info.get("thumb_url") or info.get("original_url")
            if not url: continue
            try: data, mime = download(url)
            except requests.HTTPError:
                if info.get("original_url"):
                    try: data, mime = download(info["original_url"])
                    except Exception as e: log(f"  download fail {ft}: {e}"); continue
                else: continue
            except Exception as e: log(f"  download fail {ft}: {e}"); continue

            row={"source":"wikimedia","source_id":ft,"attraction_qid":q,"city":city,"attraction_name":label,
                 "license":info.get("license"),"license_url":info.get("license_url"),"creator":info.get("creator"),
                 "attribution":info.get("attribution"),"original_url":info.get("original_url"),"thumb_url":info.get("thumb_url"),
                 "img_bytes":psycopg2.Binary(data),"mime_type":info.get("mime_type") or mime,"width":info.get("width"),
                 "height":info.get("height"),"sha256":hashlib.sha256(data).hexdigest()}
            if insert_row(conn,row):
                total+=1
                if total % 25 == 0: log(f"Inserted so far: {total}")
        log(f"Done {city} — total: {total}")
    log(f"ALL DONE — inserted: {total}")

if __name__=="__main__": main()
