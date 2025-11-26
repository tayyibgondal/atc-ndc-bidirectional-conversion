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


def download_all_ndc_with_search_strategy(total_available: int) -> Dict[str, Dict]:
    """
    Download ALL NDC codes using search strategy to bypass 25K skip limit.
    
    Strategy: 
    1. Split by product type
    2. For large types (>25K), further split by generic_name first letter
    3. Get any remaining codes
    """
    ndc_mapping = {}
    
    # Small product types (< 25K each)
    small_types = [
        'BULK INGREDIENT',
        'DRUG FOR FURTHER PROCESSING',
        'NON-STANDARDIZED ALLERGENIC',
        'STANDARDIZED ALLERGENIC',
        'PLASMA DERIVATIVE',
        'CELLULAR THERAPY',
        'VACCINE',
    ]
    
    # Large product types (> 25K each) - need alphabet split
    large_types = [
        'HUMAN PRESCRIPTION DRUG',
        'HUMAN OTC DRUG',
    ]
    
    print(f"\n🔄 Using multi-query strategy to download all {total_available:,} codes")
    print(f"📊 Strategy: Split by product type + alphabet for large categories\n")
    
    overall_pbar = tqdm(total=total_available, desc="Overall progress", unit="codes")
    
    # Download small product types
    for product_type in small_types:
        search_query = f'product_type:"{product_type}"'
        print(f"\n📦 Downloading: {product_type}")
        
        type_codes = download_with_search(search_query, max_skip=25000)
        
        for ndc, info in type_codes.items():
            if ndc not in ndc_mapping:
                ndc_mapping[ndc] = info
                overall_pbar.update(1)
    
    # Download large product types with alphabet splitting
    for product_type in large_types:
        print(f"\n📦 Downloading: {product_type} (with alphabet split)")
        
        # Split by first letter of generic name (A-Z plus numbers/special)
        for letter in list('ABCDEFGHIJKLMNOPQRSTUVWXYZ') + ['0-9']:
            if letter == '0-9':
                # Get products starting with numbers
                search_query = f'product_type:"{product_type}" AND generic_name:[0 TO 9]'
            else:
                # Get products starting with this letter
                search_query = f'product_type:"{product_type}" AND generic_name:{letter}*'
            
            type_codes = download_with_search(search_query, max_skip=25000, silent=True)
            
            for ndc, info in type_codes.items():
                if ndc not in ndc_mapping:
                    ndc_mapping[ndc] = info
                    overall_pbar.update(1)
            
            # Show progress every few letters
            if len(letter) == 1 and ord(letter) % 3 == 0:
                overall_pbar.set_postfix_str(f"{product_type[:20]}... letter {letter}")
    
    # Get any remaining codes not captured by product_type
    print(f"\n📦 Downloading: Remaining codes without product_type")
    remaining = download_simple_batch(skip=0, limit=25000, existing_codes=set(ndc_mapping.keys()))
    
    for ndc, info in remaining.items():
        if ndc not in ndc_mapping:
            ndc_mapping[ndc] = info
            overall_pbar.update(1)
    
    overall_pbar.close()
    
    print(f"\n✅ Downloaded {len(ndc_mapping):,} unique NDC codes")
    print(f"📊 Coverage: {len(ndc_mapping)/total_available*100:.1f}% of available codes")
    
    return ndc_mapping


def download_with_search(search_query: str, max_skip: int = 25000, silent: bool = False) -> Dict[str, Dict]:
    """Download NDC codes using a search query."""
    ndc_mapping = {}
    skip = 0
    batch_size = 1000
    
    while skip < max_skip:
        try:
            url = f"https://api.fda.gov/drug/ndc.json?search={search_query}&skip={skip}&limit={batch_size}"
            response = requests.get(url, timeout=30)
            
            if response.status_code != 200:
                if not silent:
                    print(f"  ⚠️  API returned status {response.status_code}")
                break
            
            data = response.json()
            results = data.get('results', [])
            
            if not results:
                break
            
            # Process results
            for record in results:
                ndc_code = normalize_ndc_code(record.get('product_ndc', '').strip())
                if ndc_code:
                    ndc_mapping[ndc_code] = extract_product_info(record)
            
            skip += len(results)
            time.sleep(0.5)
            
            if len(results) < batch_size:
                break
                
        except Exception as e:
            if not silent:
                print(f"  ⚠️  Error at skip={skip}: {e}")
            break
    
    if not silent and ndc_mapping:
        print(f"  ✓ Got {len(ndc_mapping):,} codes")
    
    return ndc_mapping


def download_simple_batch(skip: int, limit: int, existing_codes: set) -> Dict[str, Dict]:
    """Download a simple batch without search."""
    ndc_mapping = {}
    current_skip = skip
    batch_size = 1000
    
    while current_skip < limit:
        results = fetch_ndc_batch(skip=current_skip, limit=batch_size)
        
        if not results:
            break
        
        for record in results:
            ndc_code = normalize_ndc_code(record.get('product_ndc', '').strip())
            if ndc_code and ndc_code not in existing_codes:
                ndc_mapping[ndc_code] = extract_product_info(record)
        
        current_skip += len(results)
        time.sleep(0.5)
        
        if len(results) < batch_size:
            break
    
    return ndc_mapping


def extract_product_info(record: Dict) -> Dict:
    """Extract product information from FDA record."""
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
    
    return {
        'description': description,
        'brand_name': brand_name,
        'generic_name': generic_name,
        'dosage_form': dosage_form,
        'route': route,
        'active_ingredients': active_ingredients,
        'labeler': labeler,
        'product_type': record.get('product_type', '')
    }


def normalize_ndc_code(ndc_code: str) -> str:
    """
    Normalize NDC code to FDA standard format.
    
    Converts to 5-4-2 (11 digits) for full codes or 5-4 (9 digits) for product-level.
    
    Examples:
        "0299-3847" (4-4) → "00299-3847" (5-4)
        "63187-794" (5-3) → "63187-0794" (5-4)
        "12345-6789-0" (5-4-1) → "12345-6789-00" (5-4-2)
        "0299-3847-12" (4-4-2) → "00299-3847-12" (5-4-2)
    
    Args:
        ndc_code: NDC code in any format
    
    Returns:
        Normalized NDC code in 5-4-2 or 5-4 format
    """
    if not ndc_code:
        return ndc_code
    
    # Remove extra spaces
    ndc_code = ndc_code.strip()
    
    # Check if it has hyphens
    if '-' not in ndc_code:
        # No hyphens - can't reliably determine format, return as-is
        return ndc_code
    
    parts = ndc_code.split('-')
    
    if len(parts) == 2:
        # Product-level code: labeler-product
        labeler, product = parts
        # Normalize to 5-4 format
        labeler = labeler.zfill(5)  # Pad to 5 digits
        product = product.zfill(4)  # Pad to 4 digits
        return f"{labeler}-{product}"
    
    elif len(parts) == 3:
        # Full NDC: labeler-product-package
        labeler, product, package = parts
        # Normalize to 5-4-2 format
        labeler = labeler.zfill(5)  # Pad to 5 digits
        product = product.zfill(4)  # Pad to 4 digits
        package = package.zfill(2)  # Pad to 2 digits
        return f"{labeler}-{product}-{package}"
    
    # If format is unexpected, return as-is
    return ndc_code


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
    
    # Check if we need to download ALL codes
    if total_limit == -1:
        # First, get the total count
        try:
            response = requests.get("https://api.fda.gov/drug/ndc.json?limit=1", timeout=10)
            data = response.json()
            total_available = data.get('meta', {}).get('results', {}).get('total', 100000)
            print(f"📊 Total NDC codes available: {total_available:,}")
            print(f"⚠️  FDA API has skip limit of 25,000")
            print(f"📍 Using search strategy to download all {total_available:,} codes...")
            
            # Use search strategy to get all codes
            return download_all_ndc_with_search_strategy(total_available)
            
        except Exception as e:
            print(f"⚠️  Error: {e}")
            print("⚠️  Falling back to simple download (25,000 limit)")
            total_limit = 25000
    
    # Simple download for limited requests (up to 25K due to FDA skip limit)
    print(f"🎯 Target: Download {min(total_limit, 25000):,} NDC codes")
    print(f"⚠️  Note: FDA API has 25K skip limit\n")
    
    skip = 0
    batch_size = 1000  # FDA API max per request
    max_skip = min(total_limit, 25000)  # FDA API skip limit
    
    # Create progress bar
    pbar = tqdm(total=max_skip, desc="Downloading NDC codes", unit="codes", 
                bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]')
    
    while skip < max_skip:
        remaining = max_skip - skip
        current_batch_size = min(batch_size, remaining)
        
        results = fetch_ndc_batch(skip=skip, limit=current_batch_size)
        
        if not results:
            pbar.write("⚠️  No more results available")
            break
        
        # Process results
        for record in results:
            # Get NDC code (various formats in FDA data)
            product_ndc = record.get('product_ndc', '').strip()
            
            if not product_ndc:
                continue
            
            # Normalize NDC code to FDA standard format (5-4-2 or 5-4)
            ndc_code = normalize_ndc_code(product_ndc)
            
            if ndc_code:
                ndc_mapping[ndc_code] = extract_product_info(record)
        
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

