#!/usr/bin/env python3
"""
NDC to ATC Code Converter

This program converts National Drug Code (NDC) codes to 
Anatomical Therapeutic Chemical (ATC) codes using the RxNorm API.

Author: Generated for ATC-NDC conversion project
Date: October 2025

Usage:
    python ndc_to_atc_converter.py <NDC_CODE>
    or import and use the NDCtoATCConverter class
"""

import requests
import json
import sys
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class DrugInfo:
    """Stores information about a drug and its codes"""
    ndc_code: str
    rxcui: Optional[str]
    drug_name: Optional[str]
    atc_codes: List[Dict[str, str]]
    
    def __str__(self):
        return f"NDC: {self.ndc_code}, RxCUI: {self.rxcui}, Drug: {self.drug_name}, ATCs: {len(self.atc_codes)}"


class NDCtoATCConverter:
    """
    Converts NDC codes to ATC codes using the RxNorm API.
    
    The conversion process:
    1. Query RxNorm with NDC code to get RxCUI (RxNorm Concept Unique Identifier)
    2. Query RxClass API with RxCUI to get all associated ATC codes
    3. Optionally get drug names and additional information
    """
    
    BASE_URL = "https://rxnav.nlm.nih.gov/REST"
    
    def __init__(self, verbose: bool = False):
        """
        Initialize the converter.
        
        Args:
            verbose: If True, print detailed information during conversion
        """
        self.verbose = verbose
        self.session = requests.Session()
        
    def _log(self, message: str):
        """Print message if verbose mode is enabled"""
        if self.verbose:
            print(f"[INFO] {message}")
    
    def normalize_ndc(self, ndc: str) -> str:
        """
        Normalize NDC code by removing hyphens and padding to 11 digits.
        
        Args:
            ndc: The NDC code in any format
            
        Returns:
            Normalized 11-digit NDC code
        """
        # Remove hyphens and spaces
        ndc_clean = ndc.replace('-', '').replace(' ', '')
        
        # Pad to 11 digits if needed
        if len(ndc_clean) == 10:
            # Most common: need to pad first segment
            # Split based on common patterns and pad appropriately
            ndc_clean = '0' + ndc_clean
        
        return ndc_clean
    
    def get_rxcui_from_ndc(self, ndc_code: str) -> Optional[str]:
        """
        Get RxCUI from an NDC code.
        
        Args:
            ndc_code: The NDC code (e.g., '00093-7570-98' or '00093757098')
            
        Returns:
            RxCUI identifier or None if not found
        """
        # Normalize NDC code
        ndc_normalized = self.normalize_ndc(ndc_code)
        self._log(f"Looking up RxCUI for NDC code: {ndc_code} (normalized: {ndc_normalized})")
        
        url = f"{self.BASE_URL}/rxcui.json?idtype=NDC&id={ndc_normalized}"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extract RxCUI from response
            rxcuis = data.get('idGroup', {}).get('rxnormId', [])
            
            if rxcuis:
                rxcui = rxcuis[0]
                self._log(f"Found RxCUI: {rxcui}")
                return rxcui
            else:
                self._log(f"No RxCUI found for NDC code: {ndc_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Error querying RxNorm API: {e}")
            return None
    
    def get_drug_name(self, rxcui: str) -> Optional[str]:
        """
        Get the drug name for an RxCUI.
        
        Args:
            rxcui: The RxNorm Concept Unique Identifier
            
        Returns:
            Drug name or None if not found
        """
        url = f"{self.BASE_URL}/rxcui/{rxcui}/properties.json"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            properties = data.get('properties', {})
            name = properties.get('name')
            
            if name:
                self._log(f"Drug name for RxCUI {rxcui}: {name}")
                
            return name
            
        except requests.exceptions.RequestException as e:
            self._log(f"Error getting drug name: {e}")
            return None
    
    def get_atc_codes_from_rxcui(self, rxcui: str) -> List[Dict[str, str]]:
        """
        Get all ATC codes associated with an RxCUI.
        
        Args:
            rxcui: The RxNorm Concept Unique Identifier
            
        Returns:
            List of dictionaries containing ATC code information
            Each dict contains: {'atc_code', 'class_name', 'class_type'}
        """
        self._log(f"Looking up ATC codes for RxCUI: {rxcui}")
        
        url = f"{self.BASE_URL}/rxclass/class/byRxcui.json?rxcui={rxcui}&relaSource=ATC"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            atc_list = []
            
            # Extract ATC codes from rxclassDrugInfoList
            drug_info_list = data.get('rxclassDrugInfoList', {}).get('rxclassDrugInfo', [])
            
            for drug_info in drug_info_list:
                rx_class_item = drug_info.get('rxclassMinConceptItem', {})
                atc_code = rx_class_item.get('classId', '')
                class_name = rx_class_item.get('className', '')
                class_type = rx_class_item.get('classType', '')
                
                if atc_code:
                    atc_list.append({
                        'atc_code': atc_code,
                        'class_name': class_name,
                        'class_type': class_type
                    })
            
            if atc_list:
                self._log(f"Found {len(atc_list)} ATC code(s)")
            else:
                self._log(f"No ATC codes found for RxCUI: {rxcui}")
                
            return atc_list
            
        except requests.exceptions.RequestException as e:
            print(f"Error querying RxClass API: {e}")
            return []
    
    def get_related_ingredients(self, rxcui: str) -> List[str]:
        """
        Get ingredient-level RxCUIs from a product RxCUI.
        ATC codes are typically assigned at ingredient level, not product level.
        
        Args:
            rxcui: The RxNorm Concept Unique Identifier
            
        Returns:
            List of ingredient RxCUI identifiers
        """
        self._log(f"Looking up related ingredients for RxCUI: {rxcui}")
        
        url = f"{self.BASE_URL}/rxcui/{rxcui}/related.json?tty=IN"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            ingredients = []
            concept_group = data.get('relatedGroup', {}).get('conceptGroup', [])
            
            for group in concept_group:
                if group.get('tty') == 'IN':  # Ingredient
                    properties = group.get('conceptProperties', [])
                    for prop in properties:
                        ing_rxcui = prop.get('rxcui')
                        if ing_rxcui:
                            ingredients.append(ing_rxcui)
            
            if ingredients:
                self._log(f"Found {len(ingredients)} ingredient(s)")
            else:
                self._log(f"No ingredients found for RxCUI: {rxcui}")
                
            return ingredients
            
        except requests.exceptions.RequestException as e:
            self._log(f"Error getting related ingredients: {e}")
            return []
    
    def convert(self, ndc_code: str) -> DrugInfo:
        """
        Convert an NDC code to ATC codes.
        
        Args:
            ndc_code: The NDC code to convert (e.g., '00093-7570-98' or '00093757098')
            
        Returns:
            DrugInfo object containing the conversion results
        """
        # Normalize NDC code
        ndc_code = ndc_code.strip()
        
        self._log(f"Starting conversion for NDC code: {ndc_code}")
        
        # Step 1: Get RxCUI from NDC code
        rxcui = self.get_rxcui_from_ndc(ndc_code)
        
        if not rxcui:
            return DrugInfo(
                ndc_code=ndc_code,
                rxcui=None,
                drug_name=None,
                atc_codes=[]
            )
        
        # Step 2: Get drug name
        drug_name = self.get_drug_name(rxcui)
        
        # Step 3: Get ATC codes - first try the product RxCUI
        atc_codes = self.get_atc_codes_from_rxcui(rxcui)
        
        # Step 4: If no ATC codes found, try ingredient-level RxCUIs
        # ATC codes are often assigned at ingredient level, not product level
        if not atc_codes:
            self._log("No ATC codes at product level, checking ingredient level")
            ingredients = self.get_related_ingredients(rxcui)
            for ingredient_rxcui in ingredients:
                ing_atc_codes = self.get_atc_codes_from_rxcui(ingredient_rxcui)
                atc_codes.extend(ing_atc_codes)
        
        # Remove duplicates based on atc_code
        if atc_codes:
            seen = set()
            unique_atc_codes = []
            for atc in atc_codes:
                if atc['atc_code'] not in seen:
                    seen.add(atc['atc_code'])
                    unique_atc_codes.append(atc)
            atc_codes = unique_atc_codes
        
        return DrugInfo(
            ndc_code=ndc_code,
            rxcui=rxcui,
            drug_name=drug_name,
            atc_codes=atc_codes
        )
    
    def convert_batch(self, ndc_codes: List[str]) -> List[DrugInfo]:
        """
        Convert multiple NDC codes to ATC codes.
        
        Args:
            ndc_codes: List of NDC codes to convert
            
        Returns:
            List of DrugInfo objects
        """
        results = []
        for i, ndc_code in enumerate(ndc_codes, 1):
            self._log(f"\n--- Processing {i}/{len(ndc_codes)} ---")
            result = self.convert(ndc_code)
            results.append(result)
        return results


def format_ndc(ndc: str) -> str:
    """
    Format NDC code in standard 5-4-2 format.
    
    Args:
        ndc: Raw NDC code
        
    Returns:
        Formatted NDC code
    """
    # Remove any existing hyphens
    ndc_clean = ndc.replace('-', '')
    
    # Try to format as 5-4-2 (most common format)
    if len(ndc_clean) == 11:
        return f"{ndc_clean[:5]}-{ndc_clean[5:9]}-{ndc_clean[9:]}"
    elif len(ndc_clean) == 10:
        # Pad to 11 digits then format
        return f"0{ndc_clean[:4]}-{ndc_clean[4:8]}-{ndc_clean[8:]}"
    else:
        return ndc


def print_results(drug_info: DrugInfo, detailed: bool = True):
    """
    Print the conversion results in a readable format.
    
    Args:
        drug_info: DrugInfo object containing conversion results
        detailed: If True, print detailed information
    """
    print("\n" + "="*80)
    print(f"NDC CODE: {format_ndc(drug_info.ndc_code)}")
    print("="*80)
    
    if drug_info.rxcui:
        print(f"RxCUI: {drug_info.rxcui}")
        if drug_info.drug_name:
            print(f"Drug Name: {drug_info.drug_name}")
        
        if drug_info.atc_codes:
            print(f"\nFound {len(drug_info.atc_codes)} ATC code(s):")
            print("-" * 80)
            
            for i, atc in enumerate(drug_info.atc_codes, 1):
                if detailed:
                    print(f"{i:3d}. {atc['atc_code']:10s} - {atc['class_name']}")
                    if atc['class_type']:
                        print(f"      Type: {atc['class_type']}")
                else:
                    print(f"{i:3d}. {atc['atc_code']:10s} - {atc['class_name']}")
        else:
            print("\n⚠️  No ATC codes found for this NDC code.")
            print("This might mean:")
            print("  - The ATC classification is not assigned in RxNorm")
            print("  - The drug is too new or specialized")
            print("  - The mapping data is incomplete")
    else:
        print("\n❌ No RxCUI found for this NDC code.")
        print("This might mean:")
        print("  - The NDC code is invalid or formatted incorrectly")
        print("  - The drug is not in the RxNorm database")
        print("  - The NDC has been discontinued or delisted")
    
    print("="*80)


def save_to_json(results: List[DrugInfo], filename: str):
    """
    Save conversion results to a JSON file.
    
    Args:
        results: List of DrugInfo objects
        filename: Output filename
    """
    data = []
    for info in results:
        data.append({
            'ndc_code': info.ndc_code,
            'ndc_formatted': format_ndc(info.ndc_code),
            'rxcui': info.rxcui,
            'drug_name': info.drug_name,
            'atc_codes': info.atc_codes,
            'atc_count': len(info.atc_codes)
        })
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✅ Results saved to: {filename}")


def save_to_csv(results: List[DrugInfo], filename: str):
    """
    Save conversion results to a CSV file.
    
    Args:
        results: List of DrugInfo objects
        filename: Output filename
    """
    import csv
    
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['NDC_Code', 'NDC_Formatted', 'RxCUI', 'Drug_Name', 'ATC_Code', 'ATC_Class_Name', 'ATC_Class_Type'])
        
        for info in results:
            if info.atc_codes:
                for atc in info.atc_codes:
                    writer.writerow([
                        info.ndc_code,
                        format_ndc(info.ndc_code),
                        info.rxcui or '',
                        info.drug_name or '',
                        atc['atc_code'],
                        atc['class_name'],
                        atc['class_type']
                    ])
            else:
                writer.writerow([
                    info.ndc_code,
                    format_ndc(info.ndc_code),
                    info.rxcui or '',
                    info.drug_name or '',
                    '',
                    '',
                    ''
                ])
    
    print(f"\n✅ Results saved to: {filename}")


def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Convert NDC codes to ATC codes using RxNorm API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 00093-7570-98                  # Convert single NDC code
  %(prog)s 00093757098 00310759030        # Convert multiple NDC codes
  %(prog)s 00093-7570-98 --output results # Save results to JSON and CSV
  %(prog)s 00093-7570-98 --verbose        # Show detailed processing info

Common NDC codes for testing:
  00093-7570-98 - Rosuvastatin Calcium 5mg (cholesterol medication)
  00310-0759-30 - Rosuvastatin Calcium 40mg
  50090-4063-00 - Acetaminophen 500mg (pain reliever)
  00781-1506-10 - Amoxicillin 500mg (antibiotic)
        """
    )
    
    parser.add_argument(
        'ndc_codes',
        nargs='+',
        help='One or more NDC codes to convert'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show verbose output during conversion'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Save results to files (JSON and CSV) with given prefix'
    )
    
    parser.add_argument(
        '--json-only',
        action='store_true',
        help='Save only JSON output (requires --output)'
    )
    
    parser.add_argument(
        '--csv-only',
        action='store_true',
        help='Save only CSV output (requires --output)'
    )
    
    args = parser.parse_args()
    
    # Create converter
    converter = NDCtoATCConverter(verbose=args.verbose)
    
    # Convert codes
    if len(args.ndc_codes) == 1:
        # Single code conversion
        result = converter.convert(args.ndc_codes[0])
        print_results(result)
        results = [result]
    else:
        # Batch conversion
        results = converter.convert_batch(args.ndc_codes)
        for result in results:
            print_results(result, detailed=False)
    
    # Save to files if requested
    if args.output:
        import os
        os.makedirs("output", exist_ok=True)
        if not args.csv_only:
            save_to_json(results, f"output/{args.output}.json")
        if not args.json_only:
            save_to_csv(results, f"output/{args.output}.csv")


if __name__ == "__main__":
    main()

