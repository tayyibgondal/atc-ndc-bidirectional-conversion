# NDC to ATC Converter

Convert National Drug Code (NDC) codes to Anatomical Therapeutic Chemical (ATC) codes using the RxNorm API.

## Overview

This module converts US-specific drug product identifiers (NDC) to international drug classification codes (ATC).

**Conversion Process:**
```
NDC Code → RxNorm API → RxCUI → Ingredient → ATC Codes
```

## Quick Start

```bash
# Single conversion
python ndc_to_atc_converter.py 47335098560

# Multiple codes (with hyphens or without)
python ndc_to_atc_converter.py 47335-0985-60 00310-7590-30

# Save results
python ndc_to_atc_converter.py 47335098560 --output results
```

## Usage

### Command Line

```bash
# Basic usage
python ndc_to_atc_converter.py <NDC_CODE>

# NDC codes can be in any format:
#   47335098560      (11-digit)
#   47335-0985-60    (5-4-2 format)
#   4733509856       (10-digit, will be padded)

# Options:
#   -v, --verbose        Show detailed processing info
#   -o, --output PREFIX  Save to JSON and CSV files
#   --json-only          Save only JSON output
#   --csv-only           Save only CSV output
```

### Python Library

```python
from ndc_to_atc_converter import NDCtoATCConverter

converter = NDCtoATCConverter(verbose=False)
result = converter.convert('47335098560')

print(f"Drug: {result.drug_name}")
print(f"Found {len(result.atc_codes)} ATC codes")
for atc in result.atc_codes:
    print(f"  - {atc['atc_code']}: {atc['class_name']}")
```

## Example Output

```
================================================================================
NDC CODE: 47335-0985-60
================================================================================
RxCUI: 2167563
Drug Name: rosuvastatin 10 MG Oral Capsule [Ezallor]

Found 1 ATC code(s):
--------------------------------------------------------------------------------
  1. C10AA      - HMG CoA reductase inhibitors
      Type: ATC1-4
================================================================================
```

## Common Test Codes

| NDC Code | Drug Name | Expected ATC |
|----------|-----------|--------------|
| 47335098560 | Rosuvastatin 10mg | C10AA |
| 00310759030 | Rosuvastatin 40mg | C10AA |
| 50090406300 | Acetaminophen 500mg | N02BE |
| 00781150610 | Amoxicillin 500mg | J01CA |

## Output Formats

### Console
Human-readable output with ATC classification details

### JSON
```json
{
  "ndc_code": "47335098560",
  "ndc_formatted": "47335-0985-60",
  "rxcui": "2167563",
  "drug_name": "rosuvastatin 10 MG Oral Capsule [Ezallor]",
  "atc_codes": [
    {
      "atc_code": "C10AA",
      "class_name": "HMG CoA reductase inhibitors",
      "class_type": "ATC1-4"
    }
  ],
  "atc_count": 1
}
```

### CSV
```csv
NDC_Code,NDC_Formatted,RxCUI,Drug_Name,ATC_Code,ATC_Class_Name,ATC_Class_Type
47335098560,47335-0985-60,2167563,rosuvastatin 10 MG Oral Capsule [Ezallor],C10AA,HMG CoA reductase inhibitors,ATC1-4
```

## API Information

- **API**: RxNorm REST API + RxClass API
- **Base URL**: https://rxnav.nlm.nih.gov/REST
- **Authentication**: None required
- **Rate Limits**: Respectful usage recommended

## Understanding Results

### ATC Code Levels
ATC codes returned may be at different levels:
- **ATC1-4**: Therapeutic class (e.g., C10AA - HMG CoA reductase inhibitors)
- **ATC5**: Specific substance (e.g., C10AA07 - Rosuvastatin)

Most NDC codes map to ATC1-4 level (therapeutic class) rather than ATC5 (specific substance).

### Why No ATC Codes Found?
- ATC classification not assigned in RxNorm
- Drug is too new or specialized
- Product-level NDC without ingredient mapping
- Incomplete mapping data

### NDC Format Normalization
The converter automatically normalizes NDC codes:
- Removes hyphens
- Pads to 11 digits if needed
- Formats output as 5-4-2 standard

## Technical Details

**Requirements:**
- Python 3.7+
- requests library
- Internet connection

**Key Functions:**
- `normalize_ndc()` - Standardize NDC format
- `get_rxcui_from_ndc()` - Get RxCUI from NDC
- `get_drug_name()` - Get drug name
- `get_atc_codes_from_rxcui()` - Get ATC codes from RxCUI
- `get_related_ingredients()` - Find ingredient-level RxCUIs
- `convert()` - Main conversion function
- `convert_batch()` - Batch processing

**Conversion Strategy:**
1. Convert NDC → RxCUI (product level)
2. Try to get ATC codes at product level
3. If not found, get ingredient-level RxCUIs
4. Get ATC codes from ingredient level
5. Return all unique ATC classifications

## Documentation

See `docs/` folder for:
- Research paper on NDC-ATC conversion methodology
- Technical implementation details

## Support

For issues or questions, refer to:
- RxNorm API documentation: https://lhncbc.nlm.nih.gov/RxNav/APIs/
- RxClass API documentation: https://lhncbc.nlm.nih.gov/RxNav/APIs/RxClassAPIs.html
- FDA NDC Directory: https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory

---

**Module**: ndc_to_atc  
**Version**: 1.0  
**Date**: October 2025

