#!/usr/bin/env python3
"""
Quick code lookup - Get description for any ATC or NDC code.

Usage:
    python lookup_code.py C10AA07              # Look up ATC code
    python lookup_code.py 47335-0985-60        # Look up NDC code
    python lookup_code.py C10AA                # Works with any ATC level
    
Returns a formatted string description.
"""

import json
import sys
from pathlib import Path


def load_mappings():
    """Load ATC and NDC mapping files."""
    # Try both possible locations
    data_dir = Path(__file__).parent / "data"
    if not data_dir.exists():
        data_dir = Path(__file__).parent.parent / "data"
    
    mappings = {}
    
    # Load ATC complete mapping
    atc_file = data_dir / "atc_mapping_complete.json"
    if atc_file.exists():
        with open(atc_file, 'r', encoding='utf-8') as f:
            mappings['atc'] = json.load(f)
    else:
        mappings['atc'] = {}
    
    # Load NDC simple mapping
    ndc_simple_file = data_dir / "ndc_mapping_simple.json"
    if ndc_simple_file.exists():
        with open(ndc_simple_file, 'r', encoding='utf-8') as f:
            mappings['ndc_simple'] = json.load(f)
    else:
        mappings['ndc_simple'] = {}
    
    # Load NDC full mapping
    ndc_full_file = data_dir / "ndc_mapping.json"
    if ndc_full_file.exists():
        with open(ndc_full_file, 'r', encoding='utf-8') as f:
            mappings['ndc_full'] = json.load(f)
    else:
        mappings['ndc_full'] = {}
    
    return mappings


def is_atc_code(code):
    """Check if code looks like an ATC code."""
    code = code.strip().upper()
    # ATC codes are 1, 3, 4, 5, or 7 characters
    # Start with a letter
    if len(code) in [1, 3, 4, 5, 7] and code[0].isalpha():
        return True
    return False


def is_ndc_code(code):
    """Check if code looks like an NDC code."""
    # NDC codes contain digits and possibly hyphens
    # Can be 8-11 digits (various formats)
    code_clean = code.replace('-', '').replace(' ', '')
    if code_clean.isdigit() and 8 <= len(code_clean) <= 11:
        return True
    # Also check if it has NDC hyphen pattern (digits-digits-digits)
    if '-' in code and all(part.isdigit() for part in code.split('-')):
        return True
    return False


def format_atc_description(code, atc_data):
    """Format ATC code info as a string."""
    code = code.strip().upper()
    
    # Try to find exact match first
    if code not in atc_data:
        # Try fallback to higher levels by progressively removing last character
        # Stop as soon as we find a match (closest parent level)
        current = code
        while len(current) > 0:
            current = current[:-1]  # Remove last character
            if current in atc_data:
                info = atc_data[current]
                lines = []
                lines.append(f"⚠️  Exact code '{code}' not found. Showing parent level:")
                lines.append("")
                lines.append(f"ATC Code: {info['code']}")
                lines.append(f"Name: {info['name']}")
                
                # Add hierarchy if available
                if 'hierarchy' in info and info['hierarchy']:
                    lines.append("Complete Hierarchy:")
                    for level_key in ['level1', 'level2', 'level3', 'level4', 'level5']:
                        if level_key in info['hierarchy']:
                            level_data = info['hierarchy'][level_key]
                            level_num = level_key[-1]
                            lines.append(f"Level {level_num}: {level_data['code']} → {level_data['name']}  ({level_data['description']})")
                
                return '\n'.join(lines)
        
        return f"❌ ATC code '{code}' not found in database (no parent levels found)"
    
    info = atc_data[code]
    
    # Build description
    lines = []
    lines.append(f"ATC Code: {info['code']}")
    lines.append(f"Name: {info['name']}")
    
    # Add hierarchy if available
    if 'hierarchy' in info and info['hierarchy']:
        lines.append("Complete Hierarchy:")
        for level_key in ['level1', 'level2', 'level3', 'level4', 'level5']:
            if level_key in info['hierarchy']:
                level_data = info['hierarchy'][level_key]
                level_num = level_key[-1]
                lines.append(f"Level {level_num}: {level_data['code']} → {level_data['name']}  ({level_data['description']})")
    
    return '\n'.join(lines)


def normalize_ndc_to_variants(code):
    """
    Generate NDC code variants normalized to 5-4 format (product level).
    
    The NDC mapping uses 5-4 format (labeler-product), so we normalize all inputs to that.
    
    NDC formats:
    - 11 digits (5-4-2): strip package segment → 5-4
    - 10 digits: could be 4-4-2, 5-3-2, or 5-4-1 → normalize to 5-4
    - 9 digits: pad to get 5-4
    """
    variants = set()
    code_clean = code.replace('-', '').replace(' ', '').strip()
    
    # Add original format
    variants.add(code)
    
    if len(code_clean) == 11:
        # 11-digit NDC (5-4-2 format) → extract 5-4 (product level)
        variants.add(f"{code_clean[:5]}-{code_clean[5:9]}")  # 5-4 product level
        
    elif len(code_clean) == 10:
        # 10-digit NDC - three possible formats, all should normalize to 5-4
        
        # Format 1: 4-4-2 → pad first segment to get 5-4
        variants.add(f"0{code_clean[:4]}-{code_clean[4:8]}")  # 5-4
        
        # Format 2: 5-3-2 → pad second segment to get 5-4
        variants.add(f"{code_clean[:5]}-0{code_clean[5:8]}")  # 5-4
        
        # Format 3: 5-4-1 → extract first 5-4
        variants.add(f"{code_clean[:5]}-{code_clean[5:9]}")  # 5-4
        
    elif len(code_clean) == 9:
        # 9-digit NDC - try padding appropriately
        # Could be 4-4-1 → pad to 5-4
        variants.add(f"0{code_clean[:4]}-{code_clean[4:8]}")  # 5-4
        # Could be 5-3-1 → pad to 5-4
        variants.add(f"{code_clean[:5]}-0{code_clean[5:8]}")  # 5-4
        
    # Also try the code as-is in case it's already in 5-4 format with dashes
    if '-' in code:
        variants.add(code)
    
    return list(variants)


def format_ndc_description(code, ndc_simple, ndc_full):
    """Format NDC code info as a string."""
    code = code.strip()
    
    # Generate all possible variants according to FDA standards
    code_variants = normalize_ndc_to_variants(code)
    
    # Search in simple mapping first
    found_code = None
    for variant in code_variants:
        if variant in ndc_simple:
            found_code = variant
            break
    
    # If not found, try product-level (remove package segment)
    if not found_code:
        # Try removing last segment (package)
        fallback_variants = []
        
        for variant in code_variants:
            if '-' in variant:
                parts = variant.split('-')
                if len(parts) == 3:
                    # Remove package segment
                    fallback_variants.append(f"{parts[0]}-{parts[1]}")
                elif len(parts) == 2:
                    # Already product level, keep it
                    fallback_variants.append(variant)
        
        # Search fallbacks
        for fallback in fallback_variants:
            if fallback in ndc_simple:
                found_code = fallback
                lines = []
                lines.append(f"⚠️  Exact code '{code}' not found. Showing product-level:")
                lines.append("")
                lines.append(f"NDC Code: {found_code}")
                lines.append(f"Description: {ndc_simple[found_code]}")
                
                # Add full details if available
                if found_code in ndc_full:
                    full_info = ndc_full[found_code]
                    lines.append("Product Details:")
                    
                    if full_info.get('brand_name'):
                        lines.append(f"  Brand Name: {full_info['brand_name']}")
                    
                    if full_info.get('generic_name'):
                        lines.append(f"  Generic Name: {full_info['generic_name']}")
                    
                    if full_info.get('dosage_form'):
                        lines.append(f"  Dosage Form: {full_info['dosage_form']}")
                    
                    if full_info.get('route'):
                        lines.append(f"  Route: {full_info['route']}")
                    
                    if full_info.get('labeler'):
                        lines.append(f"  Manufacturer: {full_info['labeler']}")
                    
                    if full_info.get('product_type'):
                        lines.append(f"  Product Type: {full_info['product_type']}")
                    
                    # Add active ingredients
                    if full_info.get('active_ingredients'):
                        lines.append("  Active Ingredients:")
                        for ing in full_info['active_ingredients'][:5]:
                            if isinstance(ing, dict):
                                ing_name = ing.get('name', 'Unknown')
                                ing_strength = ing.get('strength', '')
                                lines.append(f"    • {ing_name} {ing_strength}")
                            else:
                                lines.append(f"    • {ing}")
                
                return '\n'.join(lines)
        
        return f"❌ NDC code '{code}' not found in database (no product-level match found)"
    
    # Build description
    lines = []
    lines.append(f"NDC Code: {found_code}")
    lines.append(f"Description: {ndc_simple[found_code]}")
    
    # Add full details if available
    if found_code in ndc_full:
        full_info = ndc_full[found_code]
        lines.append("Product Details:")
        
        if full_info.get('brand_name'):
            lines.append(f"  Brand Name: {full_info['brand_name']}")
        
        if full_info.get('generic_name'):
            lines.append(f"  Generic Name: {full_info['generic_name']}")
        
        if full_info.get('dosage_form'):
            lines.append(f"  Dosage Form: {full_info['dosage_form']}")
        
        if full_info.get('route'):
            lines.append(f"  Route: {full_info['route']}")
        
        if full_info.get('labeler'):
            lines.append(f"  Manufacturer: {full_info['labeler']}")
        
        if full_info.get('product_type'):
            lines.append(f"  Product Type: {full_info['product_type']}")
        
        # Add active ingredients
        if full_info.get('active_ingredients'):
            lines.append("\n  Active Ingredients:")
            for ing in full_info['active_ingredients'][:5]:  # Show first 5
                if isinstance(ing, dict):
                    ing_name = ing.get('name', 'Unknown')
                    ing_strength = ing.get('strength', '')
                    lines.append(f"    • {ing_name} {ing_strength}")
                else:
                    lines.append(f"    • {ing}")
    
    return '\n'.join(lines)


def lookup_code(code):
    """
    Look up any code (ATC or NDC) and return formatted description.
    
    Args:
        code: ATC or NDC code as string
    
    Returns:
        Formatted string description
    """
    # Load mappings
    mappings = load_mappings()
    
    if not mappings['atc'] and not mappings['ndc_simple']:
        return "❌ Error: Mapping files not found. Run 'python download_all_mappings.py' first."
    
    # Determine code type and format
    if is_atc_code(code):
        return format_atc_description(code, mappings['atc'])
    elif is_ndc_code(code):
        return format_ndc_description(code, mappings['ndc_simple'], mappings['ndc_full'])
    else:
        return f"❌ Could not determine if '{code}' is an ATC or NDC code.\n\nATC codes: 1-7 characters, start with letter (e.g., C10AA07)\nNDC codes: 10-11 digits, may have hyphens (e.g., 47335-0985-60)"


def main():
    if len(sys.argv) < 2:
        print("Usage: python lookup_code.py <CODE>")
        print("\nExamples:")
        print("  python lookup_code.py C10AA07        # ATC code")
        print("  python lookup_code.py C10AA          # ATC class")
        print("  python lookup_code.py 47335-0985-60  # NDC code")
        print("  python lookup_code.py 47335098560    # NDC without hyphens")
        sys.exit(1)
    
    code = sys.argv[1]
    result = lookup_code(code)
    print(result)


if __name__ == "__main__":
    main()

