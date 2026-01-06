#!/usr/bin/env python3
"""
Build ATC code descriptions map for AHS.

Reads ATC codes from ATC_codes_for_ahs.csv, looks up each code,
and saves the results to data/atc_descriptions_map.json.

Usage:
    python build_atc_descriptions_for_ahs.py
"""

import json
import csv
from pathlib import Path
from tqdm import tqdm


def load_atc_mapping():
    """Load ATC mapping file."""
    data_dir = Path(__file__).parent / "data"
    atc_file = data_dir / "atc_mapping_complete.json"
    
    with open(atc_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_atc_codes(filepath):
    """
    Load ATC codes from a CSV file.
    
    Args:
        filepath: Path to CSV file with ATC_code column
        
    Returns:
        List of unique ATC codes
    """
    codes = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            if row and row[0].strip():
                code = row[0].strip().replace('*', '').replace('"', '')
                if code:
                    codes.append(code)
    # Remove duplicates while preserving order
    return list(dict.fromkeys(codes))


def lookup_atc_code(code, atc_data):
    """
    Look up an ATC code and return structured result with full textual description.
    """
    code = code.strip().upper()
    
    if not code:
        return None
    
    # Try to find exact match first
    matched_code = None
    if code in atc_data:
        matched_code = code
    else:
        # Try fallback to higher levels
        current = code
        while len(current) > 0:
            current = current[:-1]
            if current in atc_data:
                matched_code = current
                break
    
    # No match found
    if matched_code is None:
        return {
            "input_code": code,
            "matched_code": None,
            "name": None,
            "description": f"Code '{code}' not found in database",
            "metadata": {"found": False, "hierarchy": None}
        }
    
    info = atc_data[matched_code]
    
    # Build hierarchy metadata and path
    hierarchy_details = {}
    hierarchy_path_parts = []
    if 'hierarchy' in info and info['hierarchy']:
        for level_key in ['level1', 'level2', 'level3', 'level4', 'level5']:
            if level_key in info['hierarchy']:
                level_data = info['hierarchy'][level_key]
                hierarchy_details[level_key] = {
                    "code": level_data['code'],
                    "name": level_data['name'],
                    "description": level_data['description']
                }
                hierarchy_path_parts.append(f"{level_data['name']} ({level_data['code']})")
    
    # Build comprehensive textual description
    description_parts = [f"Name: {info['name']}", f"ATC Code: {info['code']}"]
    
    if info.get('level'):
        level_names = {
            1: "Anatomical main group", 2: "Therapeutic subgroup",
            3: "Pharmacological subgroup", 4: "Chemical subgroup", 5: "Chemical substance"
        }
        description_parts.append(f"Level: {info['level']} ({level_names.get(info['level'], '')})")
    
    if hierarchy_path_parts:
        description_parts.append(f"Classification Path: {' > '.join(hierarchy_path_parts)}")
    
    return {
        "input_code": code,
        "matched_code": info['code'],
        "name": info['name'],
        "description": " | ".join(description_parts),
        "metadata": {
            "found": True,
            "exact_match": code == matched_code,
            "level": info.get('level'),
            "hierarchy": hierarchy_details
        }
    }


def main():
    print("=" * 60)
    print("ATC Code Description Builder for AHS")
    print("=" * 60)
    
    base_dir = Path(__file__).parent
    data_dir = base_dir / "data"
    
    # Load ATC mapping
    print("\n📂 Loading ATC mapping...")
    atc_data = load_atc_mapping()
    print(f"   Loaded {len(atc_data)} ATC codes")
    
    # Load ATC codes from CSV
    print("\n📄 Loading ATC codes...")
    codes_file = base_dir / "ATC_codes_for_ahs.csv"
    atc_codes = load_atc_codes(codes_file)
    print(f"   Loaded {len(atc_codes)} codes from {codes_file.name}")
    
    # Build descriptions map
    print("\n🔍 Looking up codes...")
    
    descriptions_map = {}
    stats = {"found": 0, "not_found": 0, "exact_match": 0, "parent_match": 0}
    
    for code in tqdm(atc_codes, desc="Processing", unit="code"):
        result = lookup_atc_code(code, atc_data)
        if result:
            descriptions_map[code] = result
            if result["metadata"]["found"]:
                stats["found"] += 1
                if result["metadata"].get("exact_match"):
                    stats["exact_match"] += 1
                else:
                    stats["parent_match"] += 1
            else:
                stats["not_found"] += 1
    
    # Print summary
    print("\n" + "=" * 60)
    print("📈 Summary")
    print("=" * 60)
    print(f"   Total: {len(atc_codes)} | Found: {stats['found']} (exact: {stats['exact_match']}, parent: {stats['parent_match']}) | Not found: {stats['not_found']}")
    
    # Save to data folder
    output_file = data_dir / "atc_descriptions_map.json"
    print(f"\n💾 Saving to {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(descriptions_map, f, indent=2, ensure_ascii=False)
    
    print(f"   Saved {len(descriptions_map)} entries")
    
    # Show sample
    print("\n📋 Sample:")
    for code in list(descriptions_map.keys())[:2]:
        print(f"  {code}: {descriptions_map[code]['name']}")
    
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
