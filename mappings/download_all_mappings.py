#!/usr/bin/env python3
"""
MASTER SCRIPT - Download ALL ATC and NDC Code Descriptions

This single script downloads EVERYTHING:
1. ALL ATC codes (all 5 levels with complete hierarchies) - ~1,350 codes
2. ALL NDC codes (with full product details) - ~100,000+ codes

NO LIMITS - Gets complete datasets!

Usage:
    python download_all_mappings.py

Time: ~30-40 minutes for complete download (shows progress bars)

Output Files (saved to ../data/):
    - atc_mapping.json              # Basic ATC (Levels 1-4)
    - atc_mapping_complete.json     # Complete ATC (All 5 levels + hierarchies)
    - ndc_mapping.json              # NDC full details (ALL codes)
    - ndc_mapping_simple.json       # NDC simple descriptions (ALL codes)
"""

import subprocess
import sys
from pathlib import Path


def run_script(script_name, args=None):
    """Run a Python script and show output."""
    cmd = [sys.executable, script_name]
    if args:
        cmd.extend(args)
    
    print(f"\n{'='*80}")
    print(f"▶️  Running: {script_name}")
    print(f"{'='*80}\n")
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    
    if result.returncode != 0:
        print(f"\n❌ Error running {script_name}")
        return False
    return True


def main():
    print("\n" + "="*80)
    print("📥 DOWNLOADING ALL ATC & NDC CODE DESCRIPTIONS")
    print("="*80)
    print("\n🎯 This will download COMPLETE datasets:")
    print("  ✅ ALL ATC codes (~1,350 codes with all 5 levels)")
    print("  ✅ ALL NDC codes (~100,000+ codes from FDA)")
    print("\n⏱️  Estimated time: 30-40 minutes")
    print("📊 Progress bars will show download status")
    print("\n" + "="*80)
    
    input("\n⏸️  Press ENTER to start download (or Ctrl+C to cancel)...")
    
    # Step 1: Download basic ATC codes
    print("\n📍 STEP 1/3: Downloading ATC codes (Levels 1-4)...")
    print("   Time: ~5 seconds")
    if not run_script('step1_download_atc_basic.py', ['--atc']):
        print("\n❌ Failed at Step 1")
        return 1
    
    # Step 2: Enhance ATC with Level 5 and hierarchies
    print("\n📍 STEP 2/3: Enhancing ATC with Level 5 substances & hierarchies...")
    print("   Time: ~10 seconds")
    if not run_script('step2_enhance_atc_add_level5.py'):
        print("\n❌ Failed at Step 2")
        return 1
    
    # Step 3: Download ALL NDC codes
    print("\n📍 STEP 3/3: Downloading ALL NDC codes from FDA...")
    print("   Time: ~30 minutes (downloading 100,000+ codes)")
    print("   Progress bar will show status...")
    
    if not run_script('step3_download_ndc_from_fda.py', ['--full']):
        print("\n❌ Failed at Step 3")
        return 1
    
    # Success!
    print("\n" + "="*80)
    print("✅ SUCCESS! ALL MAPPINGS DOWNLOADED")
    print("="*80)
    
    print("\n📁 Files Created (in ../data/):")
    print("  1. atc_mapping.json              - Basic ATC codes (Levels 1-4)")
    print("  2. atc_mapping_complete.json     - Complete ATC (all 5 levels, ~1,350 codes)")
    print("  3. ndc_mapping.json              - NDC full details (~100,000+ codes)")
    print("  4. ndc_mapping_simple.json       - NDC simple descriptions (~100,000+ codes)")
    
    print("\n📊 Dataset Statistics:")
    print("  • ATC Codes: ~1,350 (complete hierarchy)")
    print("  • NDC Codes: ~100,000+ (all FDA products)")
    
    print("\n💡 Usage Example:")
    print("  import json")
    print("  atc = json.load(open('../data/atc_mapping_complete.json'))")
    print("  ndc = json.load(open('../data/ndc_mapping_simple.json'))")
    print("  ")
    print("  # Look up codes")
    print("  print(atc['C10AA07'])  # rosuvastatin with full hierarchy")
    print("  print(ndc['47335-0985-60'])  # product description")
    
    print("\n" + "="*80)
    print("🎉 Complete! You now have ALL ATC and NDC code descriptions!")
    print("="*80 + "\n")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Download cancelled by user")
        sys.exit(1)
