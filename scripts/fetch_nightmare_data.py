#!/usr/bin/env python3
"""
fetch_nightmare_data.py
Harvests complex, multi-column clinical PDFs from the Europe PMC RESTful Articles API
to build our custom ground-truth 'nightmare scenario' evaluation corpus for Surya OCR v1 vs v2.
"""

import hashlib
import time
import requests
from pathlib import Path

# Anchor output path to project root/corpus/nightmares
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "corpus" / "nightmares"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Europe PMC Articles RESTful Search API Endpoint
API_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
# Articles ?pdf=render is Cloudflare-blocked; getPdf is the actual binary endpoint.
PDF_URL_TEMPLATE = "https://europepmc.org/api/getPdf?pmcid={pmcid}"

# Identifiable client header; EBI often rejects default python-requests User-Agent.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

def get_sha256(file_path: Path) -> str:
    """Computes SHA256 cryptographic hash for file integrity verification."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_nightmare_corpus(max_docs: int = 10):
    # Restrict to OA records Europe PMC flags as having a PDF binary.
    query = "clinical trial randomized controlled trial OPEN_ACCESS:Y HAS_PDF:Y"
    
    params = {
        "query": query,
        "format": "json",
        "resultType": "core",
        "pageSize": 50,
    }
    
    print(f"[*] Querying Europe PMC REST API: {API_URL}")
    print(f"[*] Target Query: {query}")
    
    response = requests.get(API_URL, params=params, headers=HEADERS, timeout=30)
    response.raise_for_status()
    data = response.json()
    
    results = data.get("resultList", {}).get("result", [])
    print(f"[+] Retrieved {len(results)} candidate records. Filtering for valid PMCID full-texts...")
    
    downloaded = 0
    for idx, item in enumerate(results):
        if downloaded >= max_docs:
            break
            
        pmcid = item.get("pmcid")
        title = item.get("title", f"doc_{idx}")
        is_oa = item.get("isOpenAccess", "N")
        has_pdf = item.get("hasPDF", "N")

        # Skip if no PMCID, not OA, or Europe PMC has no PDF binary
        if not pmcid or is_oa != "Y" or has_pdf != "Y":
            continue
            
        pdf_url = PDF_URL_TEMPLATE.format(pmcid=pmcid)
        file_path = OUTPUT_DIR / f"{pmcid}.pdf"

        print(f"[{downloaded+1}/{max_docs}] Fetching {pmcid} -> {title[:50]}...")
        try:
            pdf_res = requests.get(
                pdf_url, headers=HEADERS, stream=True, timeout=30
            )
            content_type = pdf_res.headers.get("Content-Type", "")

            if pdf_res.status_code != 200 or "application/pdf" not in content_type:
                print(
                    f"    -> Skipped: Expected PDF but got Status "
                    f"{pdf_res.status_code}, Content-Type: {content_type}"
                )
                time.sleep(1)
                continue

            with open(file_path, "wb") as f:
                for chunk in pdf_res.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            size = file_path.stat().st_size
            with open(file_path, "rb") as f:
                magic = f.read(4)

            if size <= 50000 or magic != b"%PDF":
                file_path.unlink(missing_ok=True)
                print(
                    f"    -> Skipped: Downloaded file is not a valid PDF "
                    f"(size={size} bytes, magic={magic!r})."
                )
                time.sleep(1)
                continue

            file_hash = get_sha256(file_path)
            print(f"    -> Secured at {file_path} [SHA256: {file_hash[:12]}...]")
            downloaded += 1
        except Exception as e:
            print(f"    -> Connection error on {pmcid}: {e}")

        time.sleep(1)

    print(f"Corpus lockdown complete. Successfully locked in {downloaded} nightmare PDFs under {OUTPUT_DIR}/.")

if __name__ == "__main__":
    fetch_nightmare_corpus()
