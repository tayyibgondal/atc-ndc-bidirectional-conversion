#!/usr/bin/env python3
"""
Quick code lookup - Get description for any ATC or NDC code.

Usage:
    python lookup_code.py -atc C10AA07         # Look up ATC code
    python lookup_code.py -ndc 47335-0985-60   # Look up NDC code
    python lookup_code.py -atc C10AA           # Works with any ATC level
    
Returns a formatted string description.
"""

import json
import sys
from pathlib import Path


def load_mappings():
    """Load ATC and NDC mapping files."""
    data_dir = Path(__file__).parent / "data"
    
    mappings = {}
    
    # Load ATC complete mapping
    atc_file = data_dir / "atc_mapping_complete.json"
    with open(atc_file, 'r', encoding='utf-8') as f:
        mappings['atc'] = json.load(f)
    
    # Load NDC simple mapping
    ndc_simple_file = data_dir / "ndc_mapping_simple.json"
    with open(ndc_simple_file, 'r', encoding='utf-8') as f:
        mappings['ndc_simple'] = json.load(f)
    
    # Load NDC full mapping
    ndc_full_file = data_dir / "ndc_mapping.json"
    with open(ndc_full_file, 'r', encoding='utf-8') as f:
        mappings['ndc_full'] = json.load(f)
    
    return mappings


def format_atc_description(code, atc_data):
    """Format ATC code info as a string."""
    code = code.strip().upper()
    
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
    
    if matched_code is None:
        return f"❌ ATC code '{code}' not found in database"
    
    info = atc_data[matched_code]
    
    # Build description
    lines = [
        f"Input Code: {code}",
        f"Matched ATC Code: {info['code']}",
        f"Name: {info['name']}"
    ]
    
    # Add hierarchy if available
    if 'hierarchy' in info and info['hierarchy']:
        lines.append("Complete Hierarchy:")
        for level_key in ['level1', 'level2', 'level3', 'level4', 'level5']:
            if level_key in info['hierarchy']:
                level_data = info['hierarchy'][level_key]
                level_num = level_key[-1]
                lines.append(f"  Level {level_num}: {level_data['code']} → {level_data['name']}  ({level_data['description']})")
    
    return '\n'.join(lines)


def normalize_ndc_to_variants(code):
    """Generate NDC code variants normalized to 5-4 format (product level)."""
    variants = set()
    code_clean = code.replace('-', '').replace(' ', '').strip()
    
    variants.add(code)
    
    if len(code_clean) == 11:
        variants.add(f"{code_clean[:5]}-{code_clean[5:9]}")
    elif len(code_clean) == 10:
        variants.add(f"0{code_clean[:4]}-{code_clean[4:8]}")
        variants.add(f"{code_clean[:5]}-0{code_clean[5:8]}")
        variants.add(f"{code_clean[:5]}-{code_clean[5:9]}")
    elif len(code_clean) == 9:
        variants.add(f"0{code_clean[:4]}-{code_clean[4:8]}")
        variants.add(f"{code_clean[:5]}-0{code_clean[5:8]}")
    
    if '-' in code:
        variants.add(code)
    
    return list(variants)


def format_ndc_description(code, ndc_simple, ndc_full):
    """Format NDC code info as a string."""
    code = code.strip()
    code_variants = normalize_ndc_to_variants(code)
    
    # Search in simple mapping
    found_code = None
    for variant in code_variants:
        if variant in ndc_simple:
            found_code = variant
            break
    
    # Try product-level fallback
    if not found_code:
        for variant in code_variants:
            if '-' in variant:
                parts = variant.split('-')
                if len(parts) == 3:
                    fallback = f"{parts[0]}-{parts[1]}"
                    if fallback in ndc_simple:
                        found_code = fallback
                        break
                elif len(parts) == 2 and variant in ndc_simple:
                    found_code = variant
                    break
        
        if not found_code:
            return f"❌ NDC code '{code}' not found in database"
    
    # Build description
    lines = [f"NDC Code: {found_code}", f"Description: {ndc_simple[found_code]}"]
    
    if found_code in ndc_full:
        full_info = ndc_full[found_code]
        lines.append("Product Details:")
        
        for key, label in [('brand_name', 'Brand Name'), ('generic_name', 'Generic Name'),
                           ('dosage_form', 'Dosage Form'), ('route', 'Route'),
                           ('labeler', 'Manufacturer'), ('product_type', 'Product Type')]:
            if full_info.get(key):
                lines.append(f"  {label}: {full_info[key]}")
        
        if full_info.get('active_ingredients'):
            lines.append("  Active Ingredients:")
            for ing in full_info['active_ingredients'][:5]:
                if isinstance(ing, dict):
                    lines.append(f"    • {ing.get('name', 'Unknown')} {ing.get('strength', '')}")
                else:
                    lines.append(f"    • {ing}")
    
    return '\n'.join(lines)


def lookup_code(code, code_type):
    """Look up a code (ATC or NDC) and return formatted description."""
    mappings = load_mappings()
    
    if not mappings['atc'] and not mappings['ndc_simple']:
        return "❌ Error: Mapping files not found. Run 'python download_all_mappings.py' first."
    
    if code_type == 'atc':
        return format_atc_description(code, mappings['atc'])
    elif code_type == 'ndc':
        return format_ndc_description(code, mappings['ndc_simple'], mappings['ndc_full'])
    else:
        return f"❌ Invalid code type '{code_type}'. Use -atc or -ndc."


def main():
    if len(sys.argv) < 3:
        print("Usage: python lookup_code.py -atc|-ndc <CODE>")
        print("\nExamples:")
        print("  python lookup_code.py -atc C10AA07        # ATC code")
        print("  python lookup_code.py -atc C10AA          # ATC class")
        print("  python lookup_code.py -ndc 47335-0985-60  # NDC code")
        print("  python lookup_code.py -ndc 47335098560    # NDC without hyphens")
        sys.exit(1)
    
    flag = sys.argv[1].lower()
    code = sys.argv[2]
    
    if flag == '-atc':
        code_type = 'atc'
    elif flag == '-ndc':
        code_type = 'ndc'
    else:
        print(f"❌ Unknown flag '{flag}'. Use -atc or -ndc.")
        sys.exit(1)
    
    print(lookup_code(code, code_type))


if __name__ == "__main__":
    main()
