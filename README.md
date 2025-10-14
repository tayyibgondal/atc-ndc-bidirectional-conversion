# ATC <-> NDC Convertors

Note: Paper implemented <> [Link](https://data.lhncbc.nlm.nih.gov/public/mor/pubs/alum/2022-oyarzun.pdf)

Bidirectional conversion between ATC (Anatomical Therapeutic Chemical) and NDC (National Drug Code) systems using the RxNorm API.

---

## Project Structure

```
atc-ndc/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
│
├── atc_to_ndc/              # ATC → NDC Conversion Module
│   ├── atc_to_ndc_converter.py
│   ├── README.md
│   ├── docs/
│   │   └── ndc-atc conversion.pdf
│   └── output/
│
└── ndc_to_atc/              # NDC → ATC Conversion Module
    ├── ndc_to_atc_converter.py
    ├── README.md
    ├── docs/
    │   └── ndc-atc conversion.pdf
    └── output/
```

---

## Code Systems Explained

### ATC (Anatomical Therapeutic Chemical Classification)

- **Maintained by:** WHO (World Health Organization)
- **Purpose:** International drug classification by therapeutic use
- **Format:** 7 characters (e.g., `C10AA07`)
- **Hierarchy:** 5 levels from organ system to chemical substance

**Example Structure:**
- `C` = Cardiovascular system (Level 1)
- `C10` = Lipid modifying agents (Level 2)
- `C10A` = Lipid modifying agents, plain (Level 3)
- `C10AA` = HMG CoA reductase inhibitors (Level 4)
- `C10AA07` = Rosuvastatin (Level 5)

### NDC (National Drug Code)

- **Maintained by:** FDA (US Food and Drug Administration)
- **Purpose:** Unique identifier for drug products in the US
- **Format:** 10-11 digits, displayed as `5-4-2` (e.g., `47335-0985-60`)

**Segments:**
1. **Labeler** (manufacturer): `47335`
2. **Product** (drug, strength, form): `0985`
3. **Package** (size and type): `60`

### The Conversion Challenge

**ATC → NDC (One-to-Many):**
- One ATC code maps to many NDC codes
- Different manufacturers, strengths, and packages
- Example: `C10AA07` → 100+ different NDC products

**NDC → ATC (Many-to-One):**
- One NDC code typically maps to one ATC classification
- May return class-level (C10AA) rather than substance-level (C10AA07)
- ATC codes are assigned at ingredient level in RxNorm

---


## Modules Overview

### Module 1: ATC → NDC Converter

**Location:** `atc_to_ndc/`

Converts ATC codes (WHO international classification) to NDC codes (FDA US product identifiers).

- **Input:** ATC code (e.g., `C10AA07`)
- **Output:** List of NDC codes (e.g., `47335-0985-60`, `00310-7590-30`, ...)
- **Relationship:** One-to-many (1 ATC → 20-100+ NDCs)

**Features:**
- ✅ Single and batch conversion
- ✅ Related drug forms discovery
- ✅ JSON and CSV export
- ✅ Command-line and library API
- ✅ NDC code formatting (5-4-2)

**Use Cases:**
- Finding all US products for a drug class
- Market analysis by therapeutic category
- Cross-system drug database integration

[📖 Full Documentation](atc_to_ndc/README.md)

### Module 2: NDC → ATC Converter

**Location:** `ndc_to_atc/`

Converts NDC codes (FDA US product identifiers) to ATC codes (WHO international classification).

- **Input:** NDC code (e.g., `47335098560` or `47335-0985-60`)
- **Output:** ATC classification (e.g., `C10AA - HMG CoA reductase inhibitors`)
- **Relationship:** Many-to-one (1 NDC → 1-8 ATC classes)

**Features:**
- ✅ Single and batch conversion
- ✅ Ingredient-level ATC resolution
- ✅ NDC format normalization
- ✅ JSON and CSV export
- ✅ Command-line and library API

**Use Cases:**
- Classifying US products by therapeutic category
- Regulatory compliance reporting
- International drug database integration

[📖 Full Documentation](ndc_to_atc/README.md)

---


## Quick Start

### Installation (1 minute)

```bash
cd atc-ndc-bidirectional-conversion
pip install -r requirements.txt
```

### ATC → NDC Conversion

Convert international drug codes to US product codes:

```bash
cd atc_to_ndc
python atc_to_ndc_converter.py C10AA07
```

**Example Output:**
```
ATC CODE: C10AA07
Drug Name: rosuvastatin
Found 26 NDC codes
```

### NDC → ATC Conversion

Convert US product codes to international drug classifications:

```bash
cd ndc_to_atc
python ndc_to_atc_converter.py 47335098560
```

**Example Output:**
```
NDC CODE: 47335-0985-60
Drug Name: rosuvastatin 10 MG Oral Capsule [Ezallor]
Found 1 ATC code: C10AA - HMG CoA reductase inhibitors
```

### Common Options

```bash
# Save results to files (JSON and CSV)
python converter.py CODE --output results

# Verbose mode (see detailed API calls)
python converter.py CODE --verbose

# Multiple codes at once
python converter.py CODE1 CODE2 CODE3
```

---

## (Detailed) Usage Examples

### Command Line Interface

```bash
# ATC to NDC - single code
cd atc_to_ndc
python atc_to_ndc_converter.py C10AA07

# ATC to NDC - multiple codes with output
python atc_to_ndc_converter.py C10AA07 N02BE01 --output results

# NDC to ATC - single code
cd ndc_to_atc
python ndc_to_atc_converter.py 47335098560

# NDC to ATC - with verbose logging
python ndc_to_atc_converter.py 47335-0985-60 --verbose
```

### Python Library

```python
# ATC to NDC
from atc_to_ndc.atc_to_ndc_converter import ATCtoNDCConverter

converter = ATCtoNDCConverter()
result = converter.convert('C10AA07')

print(f"Drug: {result.drug_name}")
print(f"Found {len(result.ndc_codes)} NDC codes")
for ndc in result.ndc_codes[:5]:
    print(f"  - {ndc}")

# NDC to ATC
from ndc_to_atc.ndc_to_atc_converter import NDCtoATCConverter

converter = NDCtoATCConverter()
result = converter.convert('47335098560')

print(f"Drug: {result.drug_name}")
for atc in result.atc_codes:
    print(f"  - {atc['atc_code']}: {atc['class_name']}")
```

### Batch Processing

```python
# Convert multiple codes at once
atc_codes = ['C10AA07', 'N02BE01', 'J01CA04']
results = converter.convert_batch(atc_codes)

for result in results:
    print(f"{result.atc_code}: {len(result.ndc_codes)} NDCs")
```

---

## Technical Details

### Requirements

- **Python:** 3.7 or higher
- **Dependencies:** `requests>=2.31.0`
- **Internet:** Required for RxNorm API access
- **API:** Free RxNorm REST API (no authentication)

### API Information

**RxNorm REST API:**
- **Provider:** US National Library of Medicine (NLM)
- **Base URL:** https://rxnav.nlm.nih.gov/REST
- **Authentication:** None required
- **Cost:** Free
- **Status:** Production-ready, maintained by NIH

**Endpoints Used:**
- `/rxcui.json` - Code conversion
- `/rxcui/{rxcui}/properties.json` - Drug information
- `/rxcui/{rxcui}/ndcs.json` - NDC retrieval
- `/rxclass/class/byRxcui.json` - ATC classification
- `/rxcui/{rxcui}/related.json` - Related concepts

---

## Available Output Formats

### Console Output

Human-readable formatted output with:
- Drug names and RxCUI identifiers
- Formatted NDC codes (5-4-2)
- ATC classification details
- Informative error messages

### JSON Format

```json
{
  "atc_code": "C10AA07",
  "rxcui": "301542",
  "drug_name": "rosuvastatin",
  "ndc_codes": ["47335098560", "47335098660", ...],
  "ndc_count": 26
}
```

### CSV Format

```csv
ATC_Code,RxCUI,Drug_Name,NDC_Code,NDC_Formatted
C10AA07,301542,rosuvastatin,47335098560,47335-0985-60
```

---
## Architecture Summary

### Design Principles

1. **Separation of Concerns:** Independent modules
2. **Professional Code:** Clean, documented, type-annotated
3. **Error Handling:** Comprehensive exception management
4. **Flexibility:** CLI and library usage
5. **Multiple Outputs:** Console, JSON, CSV

### Workflow

**ATC → NDC:**
```
1. Receive ATC code
2. Query RxNorm to get RxCUI
3. Get drug name and information
4. Retrieve all associated NDC codes
5. Find related drug forms (optional)
6. Return consolidated NDC list
```

**NDC → ATC:**
```
1. Receive NDC code
2. Normalize NDC format
3. Query RxNorm to get product RxCUI
4. Try to get ATC at product level
5. If not found, get ingredient RxCUI
6. Query RxClass for ATC classifications
7. Return ATC codes with details
```

---


## ⚠️ Important Notes

### Data Completeness
- Not all ATC codes have NDC codes (US market only)
- Not all NDC codes have ATC classifications assigned
- Mappings depend on RxNorm database updates

### ATC Code Levels
- NDC→ATC often returns class-level (C10AA) rather than specific substance (C10AA07)
- This is expected: ATC codes are assigned at ingredient level in RxNorm

### NDC Format
- NDC codes can be 10 or 11 digits
- Converter normalizes all formats automatically
- Output formatted as standard 5-4-2

### API Usage
- Be respectful of the free RxNorm API
- Consider caching for repeated queries
- Implement delays for large batch operations (>100 codes)

---

## External sources

### Research Paper Used
- Mapping NDC Codes to ATC Classification: https://data.lhncbc.nlm.nih.gov/public/mor/pubs/alum/2022-oyarzun.pdf

### External Resources
- **RxNorm API:** https://lhncbc.nlm.nih.gov/RxNav/APIs/
- **WHO ATC Index:** https://www.whocc.no/atc_ddd_index/
- **FDA NDC Directory:** https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory

---


## Contributing

Any contributions are welcome.

