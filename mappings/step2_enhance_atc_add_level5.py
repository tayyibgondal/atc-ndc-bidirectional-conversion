#!/usr/bin/env python3
"""
Fix ATC mappings to show complete 5-level hierarchy and add substance-level codes.

This script:
1. Loads the existing ATC mapping
2. Fixes hierarchy references
3. Adds known ATC Level 5 substance codes
4. Saves enhanced version with complete hierarchies
"""

import json
import requests
import time
from pathlib import Path
from typing import Dict, List
from tqdm import tqdm


def load_atc_mapping(file_path: str) -> Dict:
    """Load existing ATC mapping."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_complete_hierarchy(code: str, name: str, atc_flat_map: Dict[str, str]) -> Dict:
    """
    Build complete hierarchy for an ATC code using the flat mapping.
    
    Args:
        code: ATC code (e.g., "C10AA" or "C10AA07")
        name: Name for this code
        atc_flat_map: Simple dict of code -> name
    
    Returns:
        Dictionary with all hierarchy levels
    """
    hierarchy = {}
    
    # Level 1: Anatomical (1 character)
    if len(code) >= 1:
        l1_code = code[0]
        hierarchy['level1'] = {
            'code': l1_code,
            'name': atc_flat_map.get(l1_code, 'Unknown'),
            'description': 'Anatomical main group'
        }
    
    # Level 2: Therapeutic (3 characters)
    if len(code) >= 3:
        l2_code = code[:3]
        hierarchy['level2'] = {
            'code': l2_code,
            'name': atc_flat_map.get(l2_code, 'Unknown'),
            'description': 'Therapeutic subgroup'
        }
    
    # Level 3: Pharmacological (4 characters)
    if len(code) >= 4:
        l3_code = code[:4]
        hierarchy['level3'] = {
            'code': l3_code,
            'name': atc_flat_map.get(l3_code, 'Unknown'),
            'description': 'Pharmacological subgroup'
        }
    
    # Level 4: Chemical (5 characters)
    if len(code) >= 5:
        l4_code = code[:5]
        hierarchy['level4'] = {
            'code': l4_code,
            'name': atc_flat_map.get(l4_code, 'Unknown'),
            'description': 'Chemical subgroup'
        }
    
    # Level 5: Substance (7 characters)
    if len(code) == 7:
        hierarchy['level5'] = {
            'code': code,
            'name': name,
            'description': 'Chemical substance'
        }
    
    return hierarchy


def fetch_substance_level_atc() -> List[Dict]:
    """
    Fetch ATC Level 5 (substance) codes by querying RxNorm ingredients.
    
    Returns:
        List of dicts with {code, name, rxcui}
    """
    print("\n🔍 Fetching ATC Level 5 (substance) codes from RxNorm...")
    
    substances = []
    
    # Strategy: Get ingredients from RxNorm and check their ATC codes
    # We'll query by drug classes to find specific ingredients
    
    common_atc_classes = [
        ('C10AA', 'HMG CoA reductase inhibitors'),  # Statins
        ('N02BE', 'Anilides'),  # Acetaminophen, etc.
        ('J01CA', 'Penicillins with extended spectrum'),
        ('A02BC', 'Proton pump inhibitors'),
        ('C09AA', 'ACE inhibitors, plain'),
        ('N06AB', 'Selective serotonin reuptake inhibitors'),
        ('N05AH', 'Diazepines, oxazepines, thiazepines and oxepines'),
        ('C07AB', 'Beta blocking agents, selective'),
        ('C08CA', 'Dihydropyridine derivatives'),
        ('A10BA', 'Biguanides'),
    ]
    
    pbar = tqdm(common_atc_classes, desc="Fetching Level 5 substances", unit="class")
    
    for atc_class, class_name in pbar:
        pbar.set_postfix_str(f"{atc_class}")
        
        try:
            # Get ingredients in this class
            url = f"https://rxnav.nlm.nih.gov/REST/rxclass/classMembers.json?classId={atc_class}&relaSource=ATC&relas=has_ingredient"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                members = data.get('drugMemberGroup', {}).get('drugMember', [])
                
                for member in members:
                    rxcui = member.get('minConcept', {}).get('rxcui')
                    name = member.get('minConcept', {}).get('name', '').strip()
                    
                    if rxcui and name:
                        # Try to get specific ATC5 code for this ingredient
                        atc5_codes = get_atc5_for_ingredient(rxcui)
                        
                        for atc5 in atc5_codes:
                            if len(atc5) == 7:  # Verify it's Level 5
                                substances.append({
                                    'code': atc5,
                                    'name': name,
                                    'rxcui': rxcui
                                })
                                pbar.write(f"    ✓ Found: {atc5} = {name}")
            
            time.sleep(0.5)  # Rate limiting
            
        except Exception as e:
            pbar.write(f"    ⚠️  Error: {e}")
            continue
    
    pbar.close()
    print(f"\n✅ Found {len(substances)} Level 5 substance codes")
    return substances


def get_atc5_for_ingredient(rxcui: str) -> List[str]:
    """Get ATC Level 5 codes for an ingredient RxCUI."""
    try:
        url = f"https://rxnav.nlm.nih.gov/REST/rxclass/class/byRxcui.json?rxcui={rxcui}&relaSource=ATC"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            drug_info_list = data.get('rxclassDrugInfoList', {}).get('rxclassDrugInfo', [])
            
            codes = []
            for info in drug_info_list:
                code = info.get('rxclassMinConceptItem', {}).get('classId', '')
                if code and len(code) == 7:  # Level 5 only
                    codes.append(code)
            
            return codes
    except:
        pass
    
    return []


def add_manual_substance_codes() -> List[Dict]:
    """Add manually curated list of common ATC Level 5 substance codes."""
    # Common substances with their ATC5 codes (from WHO ATC Index)
    return [
        {'code': 'C10AA01', 'name': 'simvastatin'},
        {'code': 'C10AA03', 'name': 'pravastatin'},
        {'code': 'C10AA04', 'name': 'fluvastatin'},
        {'code': 'C10AA05', 'name': 'atorvastatin'},
        {'code': 'C10AA07', 'name': 'rosuvastatin'},
        {'code': 'C10AA08', 'name': 'pitavastatin'},
        {'code': 'N02BE01', 'name': 'paracetamol'},
        {'code': 'N02BA01', 'name': 'acetylsalicylic acid'},
        {'code': 'J01CA04', 'name': 'amoxicillin'},
        {'code': 'A02BC01', 'name': 'omeprazole'},
        {'code': 'A02BC02', 'name': 'pantoprazole'},
        {'code': 'A02BC03', 'name': 'lansoprazole'},
        {'code': 'A02BC04', 'name': 'rabeprazole'},
        {'code': 'A02BC05', 'name': 'esomeprazole'},
        {'code': 'C09AA01', 'name': 'captopril'},
        {'code': 'C09AA02', 'name': 'enalapril'},
        {'code': 'C09AA03', 'name': 'lisinopril'},
        {'code': 'C09AA05', 'name': 'ramipril'},
        {'code': 'N06AB03', 'name': 'fluoxetine'},
        {'code': 'N06AB04', 'name': 'citalopram'},
        {'code': 'N06AB05', 'name': 'paroxetine'},
        {'code': 'N06AB06', 'name': 'sertraline'},
        {'code': 'N06AB10', 'name': 'escitalopram'},
        {'code': 'C07AB02', 'name': 'metoprolol'},
        {'code': 'C07AB03', 'name': 'atenolol'},
        {'code': 'C07AB07', 'name': 'bisoprolol'},
        {'code': 'C08CA01', 'name': 'amlodipine'},
        {'code': 'C08CA02', 'name': 'felodipine'},
        {'code': 'C08CA05', 'name': 'nifedipine'},
        {'code': 'A10BA02', 'name': 'metformin'},
        {'code': 'N05AH03', 'name': 'olanzapine'},
        {'code': 'N05AH04', 'name': 'quetiapine'},
        {'code': 'R03AC02', 'name': 'salbutamol'},
        {'code': 'R06AE07', 'name': 'cetirizine'},
        {'code': 'M01AE01', 'name': 'ibuprofen'},
        {'code': 'M01AE02', 'name': 'naproxen'},
    ]


def main():
    print("\n" + "="*80)
    print("🔧 FIXING ATC HIERARCHY AND ADDING LEVEL 5 SUBSTANCES")
    print("="*80)
    
    data_dir = Path("data")
    
    # Load existing ATC mapping
    input_file = data_dir / "atc_mapping.json"
    if not input_file.exists():
        print(f"❌ File not found: {input_file}")
        print("Run: python download_mappings.py --atc first")
        return
    
    print(f"\n📂 Loading: {input_file}")
    atc_simple = load_atc_mapping(input_file)
    print(f"✅ Loaded {len(atc_simple):,} ATC codes (Levels 1-4)")
    
    # Create flat map for hierarchy lookup
    atc_flat_map = atc_simple
    
    # Initialize enhanced mapping
    atc_enhanced = {}
    
    # Process existing codes (Levels 1-4)
    print("\n🔨 Building complete hierarchies for Levels 1-4...")
    for code, name in atc_simple.items():
        atc_enhanced[code] = {
            'code': code,
            'name': name,
            'level': len(code),
            'hierarchy': build_complete_hierarchy(code, name, atc_flat_map)
        }
    
    print(f"✅ Built hierarchies for {len(atc_enhanced):,} codes")
    
    # Add manual Level 5 substances
    print("\n📚 Adding curated Level 5 (substance) codes...")
    manual_substances = add_manual_substance_codes()
    
    for substance in manual_substances:
        code = substance['code']
        name = substance['name']
        
        atc_enhanced[code] = {
            'code': code,
            'name': name,
            'level': 5,
            'hierarchy': build_complete_hierarchy(code, name, atc_flat_map)
        }
    
    print(f"✅ Added {len(manual_substances)} Level 5 substance codes")
    
    # Try to fetch additional Level 5 codes from RxNorm
    print("\n🌐 Attempting to fetch additional Level 5 codes from RxNorm...")
    print("(This may take a minute...)")
    
    try:
        rxnorm_substances = fetch_substance_level_atc()
        
        for substance in rxnorm_substances:
            code = substance['code']
            if code not in atc_enhanced:  # Don't overwrite manual ones
                name = substance['name']
                atc_enhanced[code] = {
                    'code': code,
                    'name': name,
                    'level': 5,
                    'hierarchy': build_complete_hierarchy(code, name, atc_flat_map),
                    'rxcui': substance.get('rxcui')
                }
        
        print(f"✅ Added {len(rxnorm_substances)} additional Level 5 codes from RxNorm")
    except Exception as e:
        print(f"⚠️  Could not fetch from RxNorm: {e}")
    
    # Save enhanced mapping
    output_file = data_dir / "atc_mapping_complete.json"
    print(f"\n💾 Saving complete ATC mapping to: {output_file}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(atc_enhanced, f, indent=2, ensure_ascii=False)
    
    # Show statistics
    print("\n" + "="*80)
    print("📊 STATISTICS")
    print("="*80)
    
    level_counts = {}
    for code, info in atc_enhanced.items():
        level = info['level']
        level_counts[level] = level_counts.get(level, 0) + 1
    
    print(f"\nTotal ATC codes: {len(atc_enhanced):,}")
    print(f"  Level 1 (Anatomical): {level_counts.get(1, 0):,}")
    print(f"  Level 2 (Therapeutic): {level_counts.get(3, 0):,}")
    print(f"  Level 3 (Pharmacological): {level_counts.get(4, 0):,}")
    print(f"  Level 4 (Chemical): {level_counts.get(5, 0):,}")
    print(f"  Level 5 (Substance): {level_counts.get(7, 0):,}")
    
    # Show sample with full hierarchy
    print("\n" + "="*80)
    print("📝 SAMPLE ENTRIES WITH COMPLETE HIERARCHY")
    print("="*80)
    
    sample_codes = ['C10AA07', 'N02BE01', 'A02BC01']
    for code in sample_codes:
        if code in atc_enhanced:
            info = atc_enhanced[code]
            print(f"\n{code}: {info['name']} (Level {info['level']})")
            print("  Hierarchy:")
            for level_key in ['level1', 'level2', 'level3', 'level4', 'level5']:
                if level_key in info['hierarchy']:
                    level_info = info['hierarchy'][level_key]
                    print(f"    {level_key}: {level_info['code']} = {level_info['name']}")
                    print(f"             ({level_info['description']})")
    
    print("\n" + "="*80)
    print("✅ COMPLETE!")
    print("="*80)
    print(f"\nOutput file: {output_file}")
    print("\nNow you have:")
    print("  ✓ All 5 ATC levels with complete hierarchies")
    print("  ✓ Level 5 substance codes for common drugs")
    print("  ✓ Full hierarchy information for each code")
    print("\n")


if __name__ == "__main__":
    main()

