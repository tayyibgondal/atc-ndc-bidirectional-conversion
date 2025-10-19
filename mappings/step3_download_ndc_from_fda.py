#!/usr/bin/env python3
"""
Download NDC mappings using the FDA OpenFDA API.

This is a more reliable alternative to downloading the ZIP files,
since the FDA API is stable and provides structured JSON data.

Usage:
    python download_ndc_via_api.py --limit 1000     # Download 1000 NDC codes
    python download_ndc_via_api.py --limit 10000    # Download 10000 NDC codes
    python download_ndc_via_api.py --full           # Download ALL available (can take time)
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List
import requests
from tqdm import tqdm


def fetch_ndc_batch(skip: int = 0, limit: int = 100) -> List[Dict]:
    """
    Fetch a batch of NDC codes from FDA API.
    
    Args:
        skip: Number of results to skip
        limit: Number of results to fetch (max 1000 per request)
    
    Returns:
        List of NDC product records
    """
    url = "https://api.fda.gov/drug/ndc.json"
    params = {
        'skip': skip,
        'limit': min(limit, 1000)  # API max is 1000 per request
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get('results', [])
    except Exception as e:
        print(f"⚠️  Error fetching batch at skip={skip}: {e}")
        return []


def download_ndc_mappings(total_limit: int = 10000) -> Dict[str, Dict]:
    """
    Download NDC mappings from FDA API.
    
    Args:
        total_limit: Total number of NDC codes to download (use -1 for all)
    
    Returns:
        Dictionary mapping NDC codes to product information
    """
    print("\n" + "="*80)
    print("📋 DOWNLOADING NDC MAPPINGS FROM FDA API")
    print("="*80)
    
    ndc_mapping = {}
    skip = 0
    batch_size = 1000  # FDA API max per request
    
    # Determine total to fetch
    if total_limit == -1:
        # First, get the total count
        try:
            response = requests.get("https://api.fda.gov/drug/ndc.json?limit=1", timeout=10)
            data = response.json()
            total_available = data.get('meta', {}).get('results', {}).get('total', 100000)
            total_limit = total_available
            print(f"📊 Total NDC codes available: {total_available:,}")
        except:
            total_limit = 100000  # Fallback
            print("⚠️  Could not determine total, will fetch up to 100,000")
    
    print(f"🎯 Target: Download {total_limit:,} NDC codes\n")
    
    # Create progress bar
    pbar = tqdm(total=total_limit, desc="Downloading NDC codes", unit="codes", 
                bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]')
    
    while skip < total_limit:
        remaining = total_limit - skip
        current_batch_size = min(batch_size, remaining)
        
        results = fetch_ndc_batch(skip=skip, limit=current_batch_size)
        
        if not results:
            pbar.write("⚠️  No more results available")
            break
        
        # Process results
        for record in results:
            # Get NDC code (various formats in FDA data)
            product_ndc = record.get('product_ndc', '').strip()
            package_ndc = record.get('packaging', [{}])[0].get('package_ndc', '').strip() if record.get('packaging') else ''
            ndc_code = product_ndc or package_ndc
            
            if not ndc_code:
                continue
            
            # Extract product information
            brand_name = record.get('brand_name', '')
            generic_name = record.get('generic_name', '')
            dosage_form = record.get('dosage_form', '')
            route = ', '.join(record.get('route', [])) if record.get('route') else ''
            
            # Get active ingredients
            active_ingredients = []
            if record.get('active_ingredients'):
                for ing in record.get('active_ingredients', []):
                    name = ing.get('name', '')
                    strength = ing.get('strength', '')
                    if name:
                        active_ingredients.append(f"{name} {strength}".strip())
            
            # Get manufacturer
            labeler = record.get('labeler_name', '')
            
            # Build description
            description = brand_name or generic_name or "Unknown Product"
            if dosage_form:
                description += f" - {dosage_form}"
            if route:
                description += f" ({route})"
            
            # Store full info
            ndc_mapping[ndc_code] = {
                'description': description,
                'brand_name': brand_name,
                'generic_name': generic_name,
                'dosage_form': dosage_form,
                'route': route,
                'active_ingredients': active_ingredients,
                'labeler': labeler,
                'product_type': record.get('product_type', '')
            }
        
        skip += len(results)
        pbar.update(len(results))
        
        # Rate limiting - be nice to FDA API
        time.sleep(0.5)
        
        # Stop if we got fewer results than expected (end of data)
        if len(results) < current_batch_size:
            pbar.write(f"✅ Reached end of available data at {skip:,} records")
            break
    
    pbar.close()
    print(f"\n✅ Downloaded {len(ndc_mapping):,} unique NDC codes")
    return ndc_mapping


def main():
    parser = argparse.ArgumentParser(
        description='Download NDC mappings using FDA OpenFDA API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --limit 1000       # Download 1,000 NDC codes (quick test)
  %(prog)s --limit 10000      # Download 10,000 NDC codes (recommended)
  %(prog)s --full             # Download ALL available (can take 30+ mins)

Output:
  data/ndc_mapping.json       # Full NDC information
  data/ndc_mapping_simple.json # Just code → description

Note: FDA API rate limit is 240 requests/minute (1000/request)
      Full download may take 20-30 minutes for ~100k codes
        """
    )
    
    parser.add_argument('--limit', type=int, default=10000,
                       help='Number of NDC codes to download (default: 10000)')
    parser.add_argument('--full', action='store_true',
                       help='Download all available NDC codes')
    parser.add_argument('--data-dir', default='data',
                       help='Output directory (default: data/)')
    
    args = parser.parse_args()
    
    data_dir = Path(args.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Set limit
    limit = -1 if args.full else args.limit
    
    # Download
    ndc_mapping = download_ndc_mappings(total_limit=limit)
    
    if not ndc_mapping:
        print("\n❌ Failed to download NDC mappings")
        sys.exit(1)
    
    # Save full mapping
    output_file = data_dir / "ndc_mapping.json"
    print(f"\n💾 Saving full mapping to: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(ndc_mapping, f, indent=2, ensure_ascii=False)
    
    # Save simple mapping (just code → description)
    simple_mapping = {code: info['description'] for code, info in ndc_mapping.items()}
    simple_file = data_dir / "ndc_mapping_simple.json"
    print(f"💾 Saving simple mapping to: {simple_file}")
    with open(simple_file, 'w', encoding='utf-8') as f:
        json.dump(simple_mapping, f, indent=2, ensure_ascii=False)
    
    # Show sample
    print("\n" + "="*80)
    print("📝 SAMPLE NDC MAPPINGS")
    print("="*80)
    for i, (ndc, info) in enumerate(list(ndc_mapping.items())[:5]):
        print(f"\n{i+1}. NDC: {ndc}")
        print(f"   Description: {info['description']}")
        print(f"   Brand: {info['brand_name']}")
        print(f"   Generic: {info['generic_name']}")
        if info['active_ingredients']:
            print(f"   Ingredients: {', '.join(info['active_ingredients'][:3])}")
    
    print("\n" + "="*80)
    print("✅ DOWNLOAD COMPLETE")
    print("="*80)
    print(f"\nFiles created:")
    print(f"  - {output_file} (full data)")
    print(f"  - {simple_file} (simple mapping)")
    print(f"\nTotal NDC codes: {len(ndc_mapping):,}")
    print("\nUsage in Python:")
    print("  import json")
    print(f"  ndc_full = json.load(open('{output_file}'))")
    print(f"  ndc_simple = json.load(open('{simple_file}'))")
    print("\n")


if __name__ == "__main__":
    main()

