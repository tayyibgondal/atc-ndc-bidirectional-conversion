#!/usr/bin/env python3
"""
Download ENHANCED ATC and NDC mappings with full hierarchical information.

ATC: All 5 levels (Anatomical → Therapeutic → Pharmacological → Chemical → Substance)
NDC: All 3 segments (Labeler → Product → Package)

Usage:
    python download_enhanced_mappings.py --atc
    python download_enhanced_mappings.py --ndc
    python download_enhanced_mappings.py --all
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple
import requests


def fetch_atc_with_substances() -> Dict[str, Dict]:
    """
    Fetch ATC codes with all 5 levels including substance names.
    
    Returns:
        Dictionary with ATC codes and their full hierarchy
    """
    print("\n" + "="*80)
    print("🔬 DOWNLOADING ENHANCED ATC MAPPINGS (ALL 5 LEVELS)")
    print("="*80)
    
    atc_enhanced = {}
    
    # Step 1: Get ATC1-4 from RxClass
    print("\n📊 Step 1: Fetching ATC Levels 1-4 from RxClass API...")
    url = "https://rxnav.nlm.nih.gov/REST/rxclass/allClasses.json?classTypes=ATC1-4"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        classes = data.get('rxclassMinConceptList', {}).get('rxclassMinConcept', [])
        
        for item in classes:
            atc_code = item.get('classId', '').strip()
            atc_name = item.get('className', '').strip()
            
            if atc_code and atc_name:
                atc_enhanced[atc_code] = {
                    'code': atc_code,
                    'name': atc_name,
                    'level': len(atc_code),
                    'hierarchy': build_atc_hierarchy(atc_code, atc_name, {})
                }
        
        print(f"✅ Fetched {len(atc_enhanced):,} ATC codes (Levels 1-4)")
        
    except Exception as e:
        print(f"❌ Error fetching ATC1-4: {e}")
        return {}
    
    # Step 2: Try to get Level 5 (substances) from RxNorm ingredients
    print("\n📊 Step 2: Fetching ATC Level 5 (Substances) from RxNorm...")
    
    # Get all ingredients and their ATC codes
    ingredients_with_atc = fetch_ingredients_with_atc()
    
    # Add substance-level entries
    substance_count = 0
    for rxcui, ing_data in ingredients_with_atc.items():
        for atc_code in ing_data.get('atc_codes', []):
            if len(atc_code) == 7:  # Level 5 substance code
                substance_count += 1
                atc_enhanced[atc_code] = {
                    'code': atc_code,
                    'name': ing_data['name'],
                    'level': 5,
                    'hierarchy': build_atc_hierarchy(atc_code, ing_data['name'], atc_enhanced),
                    'rxcui': rxcui
                }
    
    print(f"✅ Found {substance_count} substance-level (Level 5) ATC codes")
    
    return atc_enhanced


def build_atc_hierarchy(code: str, name: str, atc_map: Dict) -> Dict:
    """Build full hierarchy for an ATC code."""
    hierarchy = {}
    
    if len(code) >= 1:
        hierarchy['level1'] = {'code': code[0], 'name': atc_map.get(code[0], {}).get('name', '')}
    if len(code) >= 3:
        hierarchy['level2'] = {'code': code[:3], 'name': atc_map.get(code[:3], {}).get('name', '')}
    if len(code) >= 4:
        hierarchy['level3'] = {'code': code[:4], 'name': atc_map.get(code[:4], {}).get('name', '')}
    if len(code) >= 5:
        hierarchy['level4'] = {'code': code[:5], 'name': atc_map.get(code[:5], {}).get('name', '')}
    if len(code) == 7:
        hierarchy['level5'] = {'code': code, 'name': name}
    
    return hierarchy


def fetch_ingredients_with_atc() -> Dict[str, Dict]:
    """
    Fetch ingredients from RxNorm and their associated ATC codes.
    
    Returns:
        Dictionary of rxcui -> {name, atc_codes}
    """
    ingredients = {}
    
    # We'll query for common drug classes and get their ingredients
    common_classes = [
        'C10AA',  # Statins
        'N02BE',  # Analgesics
        'J01CA',  # Penicillins
        'A02BC',  # PPIs
        'C09AA',  # ACE inhibitors
        'N05AH',  # Antipsychotics
        'N06AB',  # SSRIs
    ]
    
    for atc_class in common_classes:
        try:
            # Get drugs in this class
            url = f"https://rxnav.nlm.nih.gov/REST/rxclass/classMembers.json?classId={atc_class}&relaSource=ATC"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                members = data.get('drugMemberGroup', {}).get('drugMember', [])
                
                for member in members[:10]:  # Limit to avoid too many requests
                    rxcui = member.get('minConcept', {}).get('rxcui')
                    name = member.get('minConcept', {}).get('name', '')
                    
                    if rxcui and name:
                        # Get full ATC codes for this ingredient
                        atc_codes = get_atc_codes_for_rxcui(rxcui)
                        
                        ingredients[rxcui] = {
                            'name': name,
                            'atc_codes': atc_codes
                        }
                
                time.sleep(0.3)  # Rate limiting
                
        except Exception as e:
            print(f"  ⚠️  Error fetching {atc_class}: {e}")
            continue
    
    return ingredients


def get_atc_codes_for_rxcui(rxcui: str) -> List[str]:
    """Get all ATC codes (including Level 5) for an RxCUI."""
    try:
        url = f"https://rxnav.nlm.nih.gov/REST/rxclass/class/byRxcui.json?rxcui={rxcui}&relaSource=ATC"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            drug_info_list = data.get('rxclassDrugInfoList', {}).get('rxclassDrugInfo', [])
            
            atc_codes = []
            for info in drug_info_list:
                code = info.get('rxclassMinConceptItem', {}).get('classId', '')
                if code:
                    atc_codes.append(code)
            
            return atc_codes
    except:
        pass
    
    return []


def fetch_ndc_with_segments(limit: int = 5000) -> Dict[str, Dict]:
    """
    Fetch NDC codes with all 3 segments explained.
    
    Returns:
        Dictionary with NDC codes and segment breakdown
    """
    print("\n" + "="*80)
    print("💊 DOWNLOADING ENHANCED NDC MAPPINGS (ALL 3 SEGMENTS)")
    print("="*80)
    print(f"🎯 Target: {limit:,} NDC codes\n")
    
    ndc_enhanced = {}
    skip = 0
    batch_size = 1000
    
    while skip < limit:
        remaining = limit - skip
        current_batch_size = min(batch_size, remaining)
        
        print(f"⬇️  Fetching batch {skip:,} to {skip + current_batch_size:,}...", end=" ")
        
        # Fetch from FDA API
        url = "https://api.fda.gov/drug/ndc.json"
        params = {'skip': skip, 'limit': current_batch_size}
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            results = data.get('results', [])
            
            if not results:
                print("❌ No results")
                break
            
            print(f"✅ Got {len(results)}")
            
            # Process each record
            for record in results:
                product_ndc = record.get('product_ndc', '').strip()
                
                # Get package NDCs (which have all 3 segments)
                packages = record.get('packaging', [])
                
                for pkg in packages:
                    package_ndc = pkg.get('package_ndc', '').strip()
                    
                    if package_ndc:
                        # Parse segments
                        segments = parse_ndc_segments(package_ndc)
                        
                        # Build enhanced entry
                        ndc_enhanced[package_ndc] = {
                            'ndc': package_ndc,
                            'segments': segments,
                            'product_info': {
                                'brand_name': record.get('brand_name', ''),
                                'generic_name': record.get('generic_name', ''),
                                'dosage_form': record.get('dosage_form', ''),
                                'route': ', '.join(record.get('route', [])),
                                'labeler': record.get('labeler_name', ''),
                                'product_type': record.get('product_type', '')
                            },
                            'active_ingredients': [
                                {
                                    'name': ing.get('name', ''),
                                    'strength': ing.get('strength', '')
                                }
                                for ing in record.get('active_ingredients', [])
                            ],
                            'description': build_ndc_description(record)
                        }
                
                # Also add product-level NDC
                if product_ndc and product_ndc not in ndc_enhanced:
                    segments = parse_ndc_segments(product_ndc)
                    ndc_enhanced[product_ndc] = {
                        'ndc': product_ndc,
                        'segments': segments,
                        'product_info': {
                            'brand_name': record.get('brand_name', ''),
                            'generic_name': record.get('generic_name', ''),
                            'dosage_form': record.get('dosage_form', ''),
                            'route': ', '.join(record.get('route', [])),
                            'labeler': record.get('labeler_name', ''),
                            'product_type': record.get('product_type', '')
                        },
                        'active_ingredients': [
                            {
                                'name': ing.get('name', ''),
                                'strength': ing.get('strength', '')
                            }
                            for ing in record.get('active_ingredients', [])
                        ],
                        'description': build_ndc_description(record)
                    }
            
            skip += len(results)
            time.sleep(0.5)  # Rate limiting
            
            if len(results) < current_batch_size:
                break
                
        except Exception as e:
            print(f"❌ Error: {e}")
            break
    
    print(f"\n✅ Downloaded {len(ndc_enhanced):,} NDC codes with segment details")
    return ndc_enhanced


def parse_ndc_segments(ndc: str) -> Dict:
    """
    Parse NDC into its 3 segments and explain each.
    
    NDC formats:
    - 4-4-2 (labeler-product-package)
    - 5-3-2 (labeler-product-package)
    - 5-4-1 (labeler-product-package)
    - 5-4-2 (labeler-product-package) - most common
    """
    # Remove hyphens for parsing
    ndc_clean = ndc.replace('-', '')
    
    # Detect format based on hyphen positions in original
    if '-' in ndc:
        parts = ndc.split('-')
        if len(parts) == 3:
            labeler, product, package = parts
        else:
            # Fallback: assume 5-4-2
            if len(ndc_clean) == 11:
                labeler = ndc_clean[:5]
                product = ndc_clean[5:9]
                package = ndc_clean[9:]
            elif len(ndc_clean) == 10:
                labeler = ndc_clean[:5]
                product = ndc_clean[5:8]
                package = ndc_clean[8:]
            else:
                labeler = product = package = ''
    else:
        # No hyphens, assume 11-digit or 10-digit
        if len(ndc_clean) == 11:
            labeler = ndc_clean[:5]
            product = ndc_clean[5:9]
            package = ndc_clean[9:]
        elif len(ndc_clean) == 10:
            labeler = ndc_clean[:4]
            product = ndc_clean[4:8]
            package = ndc_clean[8:]
        else:
            labeler = product = package = ''
    
    return {
        'segment1_labeler': {
            'code': labeler,
            'description': 'Manufacturer/Labeler identifier'
        },
        'segment2_product': {
            'code': product,
            'description': 'Product identifier (drug, strength, dosage form)'
        },
        'segment3_package': {
            'code': package,
            'description': 'Package size and type identifier'
        },
        'formatted': f"{labeler}-{product}-{package}" if labeler and product and package else ndc
    }


def build_ndc_description(record: Dict) -> str:
    """Build a descriptive string for an NDC."""
    brand = record.get('brand_name', '')
    generic = record.get('generic_name', '')
    dosage = record.get('dosage_form', '')
    route = ', '.join(record.get('route', []))
    
    desc = brand or generic or "Unknown Product"
    if dosage:
        desc += f" - {dosage}"
    if route:
        desc += f" ({route})"
    
    return desc


def main():
    parser = argparse.ArgumentParser(
        description='Download enhanced ATC and NDC mappings with full hierarchical information',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--atc', action='store_true', help='Download ATC mappings (all 5 levels)')
    parser.add_argument('--ndc', action='store_true', help='Download NDC mappings (3 segments)')
    parser.add_argument('--all', action='store_true', help='Download both (default)')
    parser.add_argument('--ndc-limit', type=int, default=5000, help='NDC codes limit (default: 5000)')
    parser.add_argument('--data-dir', default='data', help='Output directory')
    
    args = parser.parse_args()
    
    if not (args.atc or args.ndc or args.all):
        args.all = True
    
    data_dir = Path(args.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*80)
    print("🗂️  ENHANCED ATC/NDC MAPPING DOWNLOADER")
    print("="*80)
    print(f"\nOutput directory: {data_dir.absolute()}\n")
    
    # Download ATC
    if args.atc or args.all:
        atc_enhanced = fetch_atc_with_substances()
        
        if atc_enhanced:
            output_file = data_dir / "atc_mapping_enhanced.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(atc_enhanced, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Saved enhanced ATC mapping to: {output_file}")
            
            # Show sample
            print("\n📝 Sample ATC entries:")
            for code, info in list(atc_enhanced.items())[:3]:
                print(f"\n  {code}: {info['name']} (Level {info['level']})")
                if info.get('hierarchy'):
                    for level, data in info['hierarchy'].items():
                        print(f"    {level}: {data['code']} = {data['name']}")
    
    # Download NDC
    if args.ndc or args.all:
        ndc_enhanced = fetch_ndc_with_segments(limit=args.ndc_limit)
        
        if ndc_enhanced:
            output_file = data_dir / "ndc_mapping_enhanced.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(ndc_enhanced, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Saved enhanced NDC mapping to: {output_file}")
            
            # Show sample
            print("\n📝 Sample NDC entries:")
            for ndc, info in list(ndc_enhanced.items())[:3]:
                print(f"\n  {ndc}: {info['description']}")
                segments = info['segments']
                print(f"    Segment 1 (Labeler): {segments['segment1_labeler']['code']}")
                print(f"    Segment 2 (Product): {segments['segment2_product']['code']}")
                print(f"    Segment 3 (Package): {segments['segment3_package']['code']}")
    
    print("\n" + "="*80)
    print("✅ DOWNLOAD COMPLETE")
    print("="*80)
    print(f"\nEnhanced mapping files saved to: {data_dir.absolute()}")
    print("\n")


if __name__ == "__main__":
    main()

