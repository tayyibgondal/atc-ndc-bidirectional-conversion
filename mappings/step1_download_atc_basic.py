#!/usr/bin/env python3
"""
Download and parse ATC and NDC mapping files.

This script downloads public mapping data from FDA and other sources,
then creates easy-to-use JSON mapping files.

Usage:
    python download_mappings.py --ndc          # Download NDC mappings only
    python download_mappings.py --atc          # Download ATC mappings only  
    python download_mappings.py --all          # Download both
"""

import argparse
import json
import os
import sys
import zipfile
from pathlib import Path
from typing import Dict
import urllib.request
import csv


def download_file(url: str, output_path: str) -> bool:
    """Download a file from URL to output_path."""
    try:
        print(f"⬇️  Downloading {url}...")
        urllib.request.urlretrieve(url, output_path)
        print(f"✅ Downloaded to {output_path}")
        return True
    except Exception as e:
        print(f"❌ Error downloading {url}: {e}")
        return False


def extract_zip(zip_path: str, extract_to: str) -> bool:
    """Extract a ZIP file."""
    try:
        print(f"📦 Extracting {zip_path}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"✅ Extracted to {extract_to}")
        return True
    except Exception as e:
        print(f"❌ Error extracting {zip_path}: {e}")
        return False


def download_ndc_mappings(data_dir: Path) -> Dict[str, str]:
    """
    Download FDA NDC database and create NDC → description mapping.
    
    Returns:
        Dictionary mapping NDC codes to descriptions
    """
    ndc_dir = data_dir / "ndc"
    ndc_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*80)
    print("📋 DOWNLOADING NDC MAPPINGS FROM FDA")
    print("="*80)
    
    # FDA NDC file URLs (these may change - check FDA website)
    # Note: These are example URLs. FDA periodically updates them.
    product_url = "https://www.fda.gov/media/151379/download"
    package_url = "https://www.fda.gov/media/151380/download"
    
    product_zip = ndc_dir / "product.zip"
    package_zip = ndc_dir / "package.zip"
    
    # Download product file
    if not product_zip.exists():
        if not download_file(product_url, str(product_zip)):
            print("⚠️  Failed to download product file. Check FDA website for current link:")
            print("   https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory")
            return {}
    
    # Extract product file
    if not (ndc_dir / "product.txt").exists():
        extract_zip(str(product_zip), str(ndc_dir))
    
    # Parse product.txt to create mapping
    print("\n📊 Parsing NDC product file...")
    ndc_mapping = {}
    product_file = ndc_dir / "product.txt"
    
    if not product_file.exists():
        print(f"❌ Product file not found: {product_file}")
        return {}
    
    try:
        with open(product_file, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                ndc_code = row.get('PRODUCTNDC', '').strip()
                if not ndc_code:
                    continue
                
                # Build description
                proprietary = row.get('PROPRIETARYNAME', '').strip()
                nonproprietary = row.get('NONPROPRIETARYNAME', '').strip()
                dosage_form = row.get('DOSAGEFORMNAME', '').strip()
                route = row.get('ROUTENAME', '').strip()
                substance = row.get('SUBSTANCENAME', '').strip()
                labeler = row.get('LABELERNAME', '').strip()
                
                description = f"{proprietary or nonproprietary}"
                if dosage_form:
                    description += f" - {dosage_form}"
                if route:
                    description += f" ({route})"
                if substance:
                    description += f" [{substance}]"
                if labeler:
                    description += f" | {labeler}"
                
                ndc_mapping[ndc_code] = description.strip()
        
        print(f"✅ Parsed {len(ndc_mapping):,} NDC codes")
        
        # Save to JSON
        output_file = data_dir / "ndc_mapping.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(ndc_mapping, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved NDC mapping to: {output_file}")
        
        # Show sample
        print("\n📝 Sample NDC mappings:")
        for ndc, desc in list(ndc_mapping.items())[:5]:
            print(f"   {ndc}: {desc}")
        
        return ndc_mapping
        
    except Exception as e:
        print(f"❌ Error parsing NDC file: {e}")
        return {}


def download_atc_mappings_from_rxnorm(data_dir: Path) -> Dict[str, str]:
    """
    Attempt to download ATC mappings using RxNorm API.
    
    Note: Full ATC database requires WHO data or UMLS license.
    This provides a basic set via RxClass API.
    
    Returns:
        Dictionary mapping ATC codes to descriptions
    """
    print("\n" + "="*80)
    print("🔬 DOWNLOADING ATC MAPPINGS VIA RXNORM API")
    print("="*80)
    
    import requests
    
    atc_mapping = {}
    
    # We'll fetch a set of common ATC classes via RxClass API
    print("\n⚠️  Note: Complete ATC database requires:")
    print("   - WHO ATC/DDD Index: https://www.whocc.no/atc_ddd_index/")
    print("   - Or UMLS RxNorm Full: https://www.nlm.nih.gov/research/umls/rxnorm/")
    print("\nFetching available ATC classes from RxClass API...")
    
    try:
        # Get all ATC classes from RxClass
        url = "https://rxnav.nlm.nih.gov/REST/rxclass/allClasses.json?classTypes=ATC1-4"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        classes = data.get('rxclassMinConceptList', {}).get('rxclassMinConcept', [])
        
        for item in classes:
            atc_code = item.get('classId', '').strip()
            atc_name = item.get('className', '').strip()
            if atc_code and atc_name:
                atc_mapping[atc_code] = atc_name
        
        print(f"✅ Fetched {len(atc_mapping):,} ATC class codes")
        
        # Save to JSON
        output_file = data_dir / "atc_mapping.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(atc_mapping, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved ATC mapping to: {output_file}")
        
        # Show sample
        print("\n📝 Sample ATC mappings:")
        for atc, desc in list(atc_mapping.items())[:5]:
            print(f"   {atc}: {desc}")
        
        return atc_mapping
        
    except Exception as e:
        print(f"❌ Error fetching ATC codes: {e}")
        return {}


def main():
    parser = argparse.ArgumentParser(
        description='Download and parse ATC and NDC mapping files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --ndc           # Download NDC mappings only
  %(prog)s --atc           # Download ATC mappings only
  %(prog)s --all           # Download both (default)

Output:
  data/ndc_mapping.json    # NDC code → description
  data/atc_mapping.json    # ATC code → description
        """
    )
    
    parser.add_argument('--ndc', action='store_true', help='Download NDC mappings')
    parser.add_argument('--atc', action='store_true', help='Download ATC mappings')
    parser.add_argument('--all', action='store_true', help='Download all mappings')
    parser.add_argument('--data-dir', default='data', help='Output directory (default: data/)')
    
    args = parser.parse_args()
    
    # Default to --all if no specific flag
    if not (args.ndc or args.atc or args.all):
        args.all = True
    
    data_dir = Path(args.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*80)
    print("🗂️  ATC/NDC MAPPING DOWNLOADER")
    print("="*80)
    print(f"\nOutput directory: {data_dir.absolute()}\n")
    
    # Download NDC mappings
    if args.ndc or args.all:
        ndc_map = download_ndc_mappings(data_dir)
        if not ndc_map:
            print("\n⚠️  NDC download failed. Manual steps:")
            print("   1. Visit: https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory")
            print("   2. Download product.zip")
            print("   3. Extract to data/ndc/")
            print("   4. Re-run this script")
    
    # Download ATC mappings
    if args.atc or args.all:
        atc_map = download_atc_mappings_from_rxnorm(data_dir)
        if not atc_map:
            print("\n⚠️  ATC download incomplete. For complete ATC data:")
            print("   Option 1 - WHO ATC Index:")
            print("      https://www.whocc.no/atc_ddd_index/")
            print("   Option 2 - RxNorm Full (requires UMLS account):")
            print("      https://www.nlm.nih.gov/research/umls/rxnorm/")
    
    print("\n" + "="*80)
    print("✅ DOWNLOAD COMPLETE")
    print("="*80)
    print(f"\nMapping files saved to: {data_dir.absolute()}")
    print("\nUsage in Python:")
    print("  import json")
    print(f"  ndc_map = json.load(open('{data_dir}/ndc_mapping.json'))")
    print(f"  atc_map = json.load(open('{data_dir}/atc_mapping.json'))")
    print("\n")


if __name__ == "__main__":
    main()

