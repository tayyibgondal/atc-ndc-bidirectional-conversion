# ATC to NDC Converter

Convert Anatomical Therapeutic Chemical (ATC) codes to National Drug Code (NDC) codes using the RxNorm API.

## Overview

This module converts international drug classification codes (ATC) to US-specific product identifiers (NDC).

**Conversion Process:**
```
ATC Code → RxNorm API → RxCUI → NDC Codes
```

## Quick Start

```bash
# Single conversion
python atc_to_ndc_converter.py C10AA07

# Multiple codes
python atc_to_ndc_converter.py C10AA07 N02BE01 J01CA04

# Save results
python atc_to_ndc_converter.py C10AA07 --output results
```

## Usage

### Command Line

```bash
# Basic usage
python atc_to_ndc_converter.py <ATC_CODE>

# Options:
#   -v, --verbose        Show detailed processing info
#   --no-related         Only direct matches, no related forms
#   -o, --output PREFIX  Save to JSON and CSV files
#   --json-only          Save only JSON output
#   --csv-only           Save only CSV output
```

### Python Library

```python
from atc_to_ndc_converter import ATCtoNDCConverter

converter = ATCtoNDCConverter(verbose=False)
result = converter.convert('C10AA07')

print(f"Drug: {result.drug_name}")
print(f"Found {len(result.ndc_codes)} NDC codes")
for ndc in result.ndc_codes:
    print(f"  - {ndc}")
```

## Example Output

```
================================================================================
ATC CODE: C10AA07
================================================================================
RxCUI: 301542
Drug Name: rosuvastatin

Found 26 NDC code(s):
--------------------------------------------------------------------------------
  1. 47335-0985-60 (raw: 47335098560)
  2. 47335-0986-60 (raw: 47335098660)
  ...
================================================================================
```

## Common Test Codes

| ATC Code | Drug Name | Category |
|----------|-----------|----------|
| C10AA07 | Rosuvastatin | Cholesterol medication |
| N02BE01 | Paracetamol | Pain reliever |
| J01CA04 | Amoxicillin | Antibiotic |
| C09AA02 | Enalapril | Blood pressure |
| A10BA02 | Metformin | Diabetes |

## Output Formats

### Console
Human-readable output with formatted NDC codes

### JSON
```json
{
  "atc_code": "C10AA07",
  "rxcui": "301542",
  "drug_name": "rosuvastatin",
  "ndc_codes": ["47335098560", ...],
  "ndc_count": 26
}
```

### CSV
```csv
ATC_Code,RxCUI,Drug_Name,NDC_Code,NDC_Formatted
C10AA07,301542,rosuvastatin,47335098560,47335-0985-60
```

## API Information

- **API**: RxNorm REST API (https://rxnav.nlm.nih.gov/REST)
- **Authentication**: None required
- **Rate Limits**: Respectful usage recommended

## Understanding Results

### Why Multiple NDCs?
One ATC code maps to many NDC codes because:
- Different manufacturers
- Different strengths (5mg, 10mg, 20mg, etc.)
- Different package sizes
- Different formulations

### When No NDCs Found?
- Drug not marketed in the US
- Ingredient-level classification only
- Drug discontinued
- Incomplete mapping data

## Technical Details

**Requirements:**
- Python 3.7+
- requests library
- Internet connection

**Key Functions:**
- `get_rxcui_from_atc()` - Get RxCUI from ATC code
- `get_drug_name()` - Get drug name
- `get_ndcs_from_rxcui()` - Get NDC codes
- `get_related_rxcuis()` - Find related drug forms
- `convert()` - Main conversion function
- `convert_batch()` - Batch processing

## Documentation

See `docs/` folder for:
- Research paper on NDC-ATC conversion methodology
- Technical implementation details

## Support

For issues or questions, refer to:
- RxNorm API documentation: https://lhncbc.nlm.nih.gov/RxNav/APIs/
- WHO ATC Index: https://www.whocc.no/atc_ddd_index/

---

**Module**: atc_to_ndc  
**Version**: 1.0  
**Date**: October 2025

