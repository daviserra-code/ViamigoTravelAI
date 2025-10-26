# -*- coding: utf-8 -*-
import os, io, re, json, hashlib, asyncio, time
from typing import Dict, List, Optional, Tuple
import requests
from bs4 import BeautifulSoup
from apify import Actor
try:
    import psycopg2, psycopg2.extras
except Exception:
    psycopg2=None

USER_AGENT="ApifyActor-TourismIT/0.1 (educational)"
S=requests.Session(); S.headers.update({"User-Agent":USER_AGENT})
TIMEOUT=45
OVERPASS_URL="https://overpass-api.de/api/interpreter"
WIKIDATA_SPARQL="https://query.wikidata.org/sparql"
COMMONS_API="https://commons.wikimedia.org/w/api.php"

def log(m): Actor.log.info(m)
def GET(u, **k): k.setdefault("timeout",TIMEOUT); r=S.get(u, **k); r.raise_for_status(); return r
def POST(u, **k): k.setdefault("timeout",TIMEOUT); r=S.post(u, **k); r.raise_for_status(); return r

def overpass_query(city, t=60, lim=500):
    return f"""
[out:json][timeout:{t}];
area["name"="{city}"]["is_in:country"="Italy"]->.a;
(node["tourism"](area.a); way["tourism"](area.a); rel["tourism"](area.a););
out center {lim};
"""

def run_overpass(city, t, lim):
    d={"data": overpass_query(city,t,lim)}
    return POST(OVERPASS_URL, data=d).json().get("elements", [])

def qid_from_tags(tags):
    if not tags: return None
    if "wikidata" in tags and re.match(r"^Q\d+$", tags["wikidata"]): return tags["wikidata"]
    if "wikipedia" in tags and ":" in tags["wikipedia"]:
        lang,title=tags["wikipedia"].split(":",1)
        try:
            r=GET(f"https://{lang}.wikipedia.org/w/api.php", params={"action":"query","format":"json","prop":"pageprops","ppprop":"wikibase_item","titles":title})
            for _,p in (r.json().get("query",{}).get("pages",{}) or {}).items():
                if "pageprops" in p and "wikibase_item" in p["pageprops"]: return p["pageprops"]["wikibase_item"]
        except Exception: return None
    return None

def wd_enrich(qid):
    out={"qid":qid}
    try:
        q=f"""
SELECT ?item ?itemLabel ?itemDescription ?image WHERE {{
  VALUES ?item {{ wd:{qid} }}
  OPTIONAL {{ ?item wdt:P18 ?image. }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "it,en". }}
}}
"""
        r=GET(WIKIDATA_SPARQL, params={"query":q}, headers={"Accept":"application/sparql-results+json","User-Agent":USER_AGENT})
        b=(r.json().get("results",{}).get("bindings",[]) or [])
        if b:
            b=b[0]
            out["label"]=b.get("itemLabel",{}).get("value","")
            out["description"]=b.get("itemDescription",{}).get("value","")
            out["p18"]=b.get("image",{}).get("value","")
    except Exception as e: log(f"wd_enrich {qid}: {e}")
    return out

def norm_title(v):
    if not v: return None
    v=v.strip()
    if v.startswith("File:"): return v.replace(" ","_")
    if v.startswith("http"):
        from urllib.parse import unquote
        u=unquote(v)
        import re
        m=re.search(r"/File:([^?#]+)",u,re.I)
        if m: return "File:"+m.group(1).replace(" ","_")
        m=re.search(r"/Special:FilePath/([^?#]+)",u,re.I)
        if m: return "File:"+m.group(1).replace(" ","_")
    return None

def commons_info(title, width=1280):
    try:
        r=GET(COMMONS_API, params={"action":"query","format":"json","prop":"imageinfo","titles":title,"iiprop":"url|mime|size|extmetadata","iiurlwidth":width,"redirects":1,"origin":"*"})
        for _,page in (r.json().get("query",{}).get("pages",{}) or {}).items():
            ii=page.get("imageinfo",[]) or []
            if not ii: continue
            info=ii[0]; ext=info.get("extmetadata",{}) or {}
            creator=(ext.get("Artist",{}) or {}).get("value") or ""
            lic=(ext.get("LicenseShortName",{}) or {}).get("value") or ""
            licu=(ext.get("LicenseUrl",{}) or {}).get("value") or ""
            credit=(ext.get("Credit",{}) or {}).get("value") or ""
            attr=f"{creator} – {lic}".strip(" –") if (creator or lic) else (credit or "")
            return {"original_url":info.get("url"),"thumb_url":info.get("thumburl") or info.get("url"),"mime_type":info.get("mime"),"width":info.get("thumbwidth") or info.get("width"),"height":info.get("thumbheight") or info.get("height"),"creator":creator,"license":lic,"license_url":licu,"attribution":attr}
    except Exception as e: log(f"commons_info {title}: {e}")
    return None

def dl(url):
    r=GET(url, stream=True); import io
    b=io.BytesIO()
    for ch in r.iter_content(65536):
        if ch: b.write(ch)
    return b.getvalue(), r.headers.get("Content-Type")

def sha256(b): import hashlib; return hashlib.sha256(b).hexdigest()

async def run():
    await Actor.init()
    try:
        inp = await Actor.get_input() or {}
        cities = inp.get("cities") or ["Roma","Milano","Firenze"]
        limit = int(inp.get("limitPerCity") or 300)
        tmo = int(inp.get("overpassTimeoutSec") or 60)
        do_img = bool(inp.get("downloadImages", True))
        thumb = int(inp.get("thumbWidth") or 1280)
        do_pg = bool(inp.get("saveToPostgres", False))

        ds = await Actor.open_dataset()
        kv = await Actor.open_key_value_store()

        pg = None
        if do_pg and os.getenv("DATABASE_URL") and psycopg2 is not None:
            try:
                pg = psycopg2.connect(os.getenv("DATABASE_URL")); pg.autocommit=True
                with pg.cursor() as cur:
                    cur.execute("""
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
CREATE UNIQUE INDEX IF NOT EXISTS uq_qid ON attraction_images (attraction_qid);
""")
                log("Postgres ready")
            except Exception as e:
                log(f"PG connect fail: {e}"); pg=None

        total=0
        for city in cities:
            log(f"Overpass: {city}")
            try:
                els = run_overpass(city, tmo, limit)
            except Exception as e:
                log(f"Overpass fail {city}: {e}"); continue
            log(f"{city}: {len(els)} elements")

            for el in els:
                tags = el.get("tags",{}) or {}
                rawname = tags.get("name") or tags.get("name:it") or tags.get("name:en") or ""
                lat = el.get("lat") or (el.get("center") or {}).get("lat")
                lon = el.get("lon") or (el.get("center") or {}).get("lon")
                tour = tags.get("tourism")

                qid = qid_from_tags(tags)
                label, desc, p18 = rawname, "", None
                if qid:
                    wd = wd_enrich(qid)
                    label = wd.get("label") or label
                    desc  = wd.get("description") or ""
                    p18   = wd.get("p18")

                meta=None
                if p18:
                    ft = norm_title(p18)
                    if ft: meta = commons_info(ft, thumb)

                img_url = meta.get("thumb_url") if meta else None
                img_ori = meta.get("original_url") if meta else None

                kv_key = None
                if do_img and (img_url or img_ori):
                    try:
                        url = img_url or img_ori
                        b, mime = dl(url)
                        kv_key = f"img_{sha256(b)[:16]}"
                        await kv.set_value(kv_key, b, {"contentType": mime or "application/octet-stream"})
                    except Exception as e:
                        log(f"KV image fail: {e}")

                item = {
                    "city": city,
                    "name": label or rawname,
                    "rawName": rawname,
                    "coords": {"lat": lat, "lon": lon},
                    "tourism": tour,
                    "osmId": el.get("id"),
                    "osmType": el.get("type"),
                    "wikidata": qid,
                    "wikipedia": tags.get("wikipedia"),
                    "description": desc,
                    "image": {
                        "thumbUrl": img_url,
                        "originalUrl": img_ori,
                        "creator": meta.get("creator") if meta else None,
                        "license": meta.get("license") if meta else None,
                        "licenseUrl": meta.get("license_url") if meta else None,
                        "attribution": meta.get("attribution") if meta else None,
                        "kvKey": kv_key,
                    },
                    "source": {"osm": True, "wikidata": bool(qid), "commons": bool(meta)}
                }
                await ds.push_data(item)

                if pg and qid and (img_url or img_ori) and kv_key:
                    try:
                        val = await kv.get_value(kv_key)
                        if isinstance(val,(bytes,bytearray)):
                            b=bytes(val); sh=sha256(b)
                            with pg.cursor() as cur:
                                cur.execute("""
INSERT INTO attraction_images
(source, source_id, attraction_qid, city, attraction_name, license, license_url, creator,
 attribution, original_url, thumb_url, img_bytes, mime_type, width, height, sha256)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
ON CONFLICT (attraction_qid) DO NOTHING
""",("wikimedia", p18 if p18 else None, qid, city, label or rawname,
       meta.get("license") if meta else None, meta.get("license_url") if meta else None,
       meta.get("creator") if meta else None, meta.get("attribution") if meta else None,
       img_ori, img_url, psycopg2.Binary(b) if psycopg2 else None, "application/octet-stream",
       meta.get("width") if meta else None, meta.get("height") if meta else None, sh))
                    except Exception as e:
                        log(f"PG insert fail: {e}")

                total+=1
                if total % 50 == 0: log(f"Processed: {total}")
        log(f"ALL DONE total={total}")
    finally:
        await Actor.exit()

if __name__=="__main__":
    asyncio.run(run())
