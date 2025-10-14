#!/usr/bin/env python3
"""
ATC to NDC Code Converter

This program converts Anatomical Therapeutic Chemical (ATC) codes to 
National Drug Code (NDC) codes using the RxNorm API.

Author: Generated for ATC-NDC conversion project
Date: October 2025

Usage:
    python atc_to_ndc_converter.py <ATC_CODE>
    or import and use the ATCtoNDCConverter class
"""

import requests
import json
import sys
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class DrugInfo:
    """Stores information about a drug and its codes"""
    atc_code: str
    rxcui: Optional[str]
    drug_name: Optional[str]
    ndc_codes: List[str]
    
    def __str__(self):
        return f"ATC: {self.atc_code}, RxCUI: {self.rxcui}, Drug: {self.drug_name}, NDCs: {len(self.ndc_codes)}"


class ATCtoNDCConverter:
    """
    Converts ATC codes to NDC codes using the RxNorm API.
    
    The conversion process:
    1. Query RxNorm with ATC code to get RxCUI (RxNorm Concept Unique Identifier)
    2. Query RxNorm with RxCUI to get all associated NDC codes
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
    
    def get_rxcui_from_atc(self, atc_code: str) -> List[str]:
        """
        Get RxCUI(s) from an ATC code.
        
        Args:
            atc_code: The ATC code (e.g., 'C10AA07')
            
        Returns:
            List of RxCUI identifiers
        """
        self._log(f"Looking up RxCUI for ATC code: {atc_code}")
        
        url = f"{self.BASE_URL}/rxcui.json?idtype=ATC&id={atc_code}"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extract RxCUI from response
            rxcuis = data.get('idGroup', {}).get('rxnormId', [])
            
            if rxcuis:
                self._log(f"Found {len(rxcuis)} RxCUI(s): {rxcuis}")
            else:
                self._log(f"No RxCUI found for ATC code: {atc_code}")
                
            return rxcuis
            
        except requests.exceptions.RequestException as e:
            print(f"Error querying RxNorm API: {e}")
            return []
    
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
    
    def get_ndcs_from_rxcui(self, rxcui: str) -> List[str]:
        """
        Get all NDC codes associated with an RxCUI.
        
        Args:
            rxcui: The RxNorm Concept Unique Identifier
            
        Returns:
            List of NDC codes
        """
        self._log(f"Looking up NDC codes for RxCUI: {rxcui}")
        
        url = f"{self.BASE_URL}/rxcui/{rxcui}/ndcs.json"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extract NDC codes from response
            ndc_list = data.get('ndcGroup', {}).get('ndcList', {}).get('ndc', [])
            
            if ndc_list:
                self._log(f"Found {len(ndc_list)} NDC code(s)")
            else:
                self._log(f"No NDC codes found for RxCUI: {rxcui}")
                
            return ndc_list
            
        except requests.exceptions.RequestException as e:
            print(f"Error querying RxNorm API: {e}")
            return []
    
    def get_related_rxcuis(self, rxcui: str) -> List[str]:
        """
        Get related RxCUIs that might have additional NDC codes.
        This includes different dose forms and strengths.
        
        Args:
            rxcui: The RxNorm Concept Unique Identifier
            
        Returns:
            List of related RxCUI identifiers
        """
        self._log(f"Looking up related RxCUIs for: {rxcui}")
        
        url = f"{self.BASE_URL}/rxcui/{rxcui}/related.json?tty=SCD+SBD+GPCK+BPCK"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            related = []
            concept_group = data.get('relatedGroup', {}).get('conceptGroup', [])
            
            for group in concept_group:
                properties = group.get('conceptProperties', [])
                for prop in properties:
                    related_rxcui = prop.get('rxcui')
                    if related_rxcui and related_rxcui != rxcui:
                        related.append(related_rxcui)
            
            if related:
                self._log(f"Found {len(related)} related RxCUI(s)")
                
            return related
            
        except requests.exceptions.RequestException as e:
            self._log(f"Error getting related RxCUIs: {e}")
            return []
    
    def convert(self, atc_code: str, include_related: bool = True) -> DrugInfo:
        """
        Convert an ATC code to NDC codes.
        
        Args:
            atc_code: The ATC code to convert (e.g., 'C10AA07')
            include_related: If True, also search related drug forms for additional NDCs
            
        Returns:
            DrugInfo object containing the conversion results
        """
        # Normalize ATC code (uppercase, no spaces)
        atc_code = atc_code.strip().upper()
        
        self._log(f"Starting conversion for ATC code: {atc_code}")
        
        # Step 1: Get RxCUI(s) from ATC code
        rxcuis = self.get_rxcui_from_atc(atc_code)
        
        if not rxcuis:
            return DrugInfo(
                atc_code=atc_code,
                rxcui=None,
                drug_name=None,
                ndc_codes=[]
            )
        
        # Use the first RxCUI as primary
        primary_rxcui = rxcuis[0]
        
        # Step 2: Get drug name
        drug_name = self.get_drug_name(primary_rxcui)
        
        # Step 3: Get NDC codes
        all_ndc_codes = []
        
        # Get NDCs for all returned RxCUIs
        for rxcui in rxcuis:
            ndcs = self.get_ndcs_from_rxcui(rxcui)
            all_ndc_codes.extend(ndcs)
        
        # Step 4: Optionally get NDCs from related drug forms
        if include_related:
            related_rxcuis = self.get_related_rxcuis(primary_rxcui)
            for rxcui in related_rxcuis[:10]:  # Limit to 10 related to avoid too many results
                ndcs = self.get_ndcs_from_rxcui(rxcui)
                all_ndc_codes.extend(ndcs)
        
        # Remove duplicates while preserving order
        all_ndc_codes = list(dict.fromkeys(all_ndc_codes))
        
        return DrugInfo(
            atc_code=atc_code,
            rxcui=primary_rxcui,
            drug_name=drug_name,
            ndc_codes=all_ndc_codes
        )
    
    def convert_batch(self, atc_codes: List[str], include_related: bool = True) -> List[DrugInfo]:
        """
        Convert multiple ATC codes to NDC codes.
        
        Args:
            atc_codes: List of ATC codes to convert
            include_related: If True, also search related drug forms for additional NDCs
            
        Returns:
            List of DrugInfo objects
        """
        results = []
        for i, atc_code in enumerate(atc_codes, 1):
            self._log(f"\n--- Processing {i}/{len(atc_codes)} ---")
            result = self.convert(atc_code, include_related)
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
    print(f"ATC CODE: {drug_info.atc_code}")
    print("="*80)
    
    if drug_info.rxcui:
        print(f"RxCUI: {drug_info.rxcui}")
        if drug_info.drug_name:
            print(f"Drug Name: {drug_info.drug_name}")
        
        if drug_info.ndc_codes:
            print(f"\nFound {len(drug_info.ndc_codes)} NDC code(s):")
            print("-" * 80)
            
            for i, ndc in enumerate(drug_info.ndc_codes, 1):
                formatted_ndc = format_ndc(ndc)
                if detailed:
                    print(f"{i:3d}. {formatted_ndc} (raw: {ndc})")
                else:
                    print(f"{i:3d}. {formatted_ndc}")
        else:
            print("\n⚠️  No NDC codes found for this ATC code.")
            print("This might mean:")
            print("  - The drug is not marketed in the US")
            print("  - The drug is classified at a higher level (ingredient level)")
            print("  - The mapping data is incomplete")
    else:
        print("\n❌ No RxCUI found for this ATC code.")
        print("This might mean:")
        print("  - The ATC code is invalid")
        print("  - The drug is not in the RxNorm database")
        print("  - The ATC classification is not yet mapped")
    
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
            'atc_code': info.atc_code,
            'rxcui': info.rxcui,
            'drug_name': info.drug_name,
            'ndc_codes': info.ndc_codes,
            'ndc_count': len(info.ndc_codes)
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
        writer.writerow(['ATC_Code', 'RxCUI', 'Drug_Name', 'NDC_Code', 'NDC_Formatted'])
        
        for info in results:
            if info.ndc_codes:
                for ndc in info.ndc_codes:
                    writer.writerow([
                        info.atc_code,
                        info.rxcui or '',
                        info.drug_name or '',
                        ndc,
                        format_ndc(ndc)
                    ])
            else:
                writer.writerow([
                    info.atc_code,
                    info.rxcui or '',
                    info.drug_name or '',
                    '',
                    ''
                ])
    
    print(f"\n✅ Results saved to: {filename}")


def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Convert ATC codes to NDC codes using RxNorm API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s C10AA07                    # Convert single ATC code
  %(prog)s C10AA07 N02BE01            # Convert multiple ATC codes
  %(prog)s C10AA07 --output results   # Save results to JSON and CSV
  %(prog)s C10AA07 --verbose          # Show detailed processing info
  %(prog)s C10AA07 --no-related       # Only direct matches, no related forms

Common ATC codes for testing:
  C10AA07 - Rosuvastatin (cholesterol medication)
  N02BE01 - Paracetamol (pain reliever)
  J01CA04 - Amoxicillin (antibiotic)
  C09AA02 - Enalapril (blood pressure medication)
  A10BA02 - Metformin (diabetes medication)
        """
    )
    
    parser.add_argument(
        'atc_codes',
        nargs='+',
        help='One or more ATC codes to convert'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show verbose output during conversion'
    )
    
    parser.add_argument(
        '--no-related',
        action='store_true',
        help='Do not include related drug forms in search'
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
    converter = ATCtoNDCConverter(verbose=args.verbose)
    
    # Convert codes
    if len(args.atc_codes) == 1:
        # Single code conversion
        result = converter.convert(
            args.atc_codes[0],
            include_related=not args.no_related
        )
        print_results(result)
        results = [result]
    else:
        # Batch conversion
        results = converter.convert_batch(
            args.atc_codes,
            include_related=not args.no_related
        )
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

