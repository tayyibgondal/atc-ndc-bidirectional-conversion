# ATC & NDC Code Mappings

Download **ALL** ATC and NDC code descriptions with progress bars showing download status.

---

## ONE COMMAND - Downloads Everything!

```bash
cd mappings/
python download_all_mappings.py
```

**This downloads:**
- ✅ **ALL ATC codes** (~1,350 codes with all 5 levels + hierarchies)
- ✅ **ALL NDC codes** (~100,000+ codes from FDA with full details)
- ✅ **Progress bars** showing download status
- ✅ **NO LIMITS** - Complete datasets!

**Time:** ~30-40 minutes (with progress bars showing status)

---

## 📦 What You Get

### Output Files (in `../data/`):

1. **`atc_mapping_complete.json`** (~860 KB)
   - All 1,350+ ATC codes
   - Complete 5-level hierarchy for each code
   - 36+ Level 5 substance codes

2. **`ndc_mapping.json`** (~20-30 MB)
   - All 100,000+ NDC codes
   - Full product details (brand, generic, ingredients, manufacturer)

3. **`ndc_mapping_simple.json`** (~3-5 MB)
   - All 100,000+ NDC codes
   - Simple code → description mapping

---

## 📊 Example Usage

```python
import json

# Load ALL codes
atc = json.load(open('../data/atc_mapping_complete.json'))
ndc = json.load(open('../data/ndc_mapping_simple.json'))

# Look up any code
print(atc['C10AA07'])  
# Returns complete hierarchy for rosuvastatin

print(ndc['47335-0985-60'])  
# Returns: "rosuvastatin 10 MG Oral Capsule [Ezallor] - CAPSULE (ORAL)"

```

---

## 📁 Files in This Folder

### ⭐ Main Script (Use This):
**`download_all_mappings.py`**
- Downloads ALL ATC and NDC codes
- Shows progress bars
- Takes ~30-40 minutes
- No limits - complete datasets

### Individual Step Scripts:
1. **`step1_download_atc_basic.py`** - Download ATC Levels 1-4
2. **`step2_enhance_atc_add_level5.py`** - Add Level 5 + hierarchies
3. **`step3_download_ndc_from_fda.py`** - Download all NDC from FDA
4. **`optional_download_with_segments.py`** - Optional: 3-segment breakdown

---

## Example ATC, NDC Mappings

### ATC Codes:

Each atc code includes **complete hierarchy**:
```json
{
  "C10AA07": {
    "code": "C10AA07",
    "name": "rosuvastatin",
    "level": 5,
    "hierarchy": {
      "level1": {"code": "C", "name": "CARDIOVASCULAR SYSTEM", "description": "Anatomical main group"},
      "level2": {"code": "C10", "name": "LIPID MODIFYING AGENTS", "description": "Therapeutic subgroup"},
      "level3": {"code": "C10A", "name": "LIPID MODIFYING AGENTS, PLAIN", "description": "Pharmacological subgroup"},
      "level4": {"code": "C10AA", "name": "HMG CoA reductase inhibitors", "description": "Chemical subgroup"},
      "level5": {"code": "C10AA07", "name": "rosuvastatin", "description": "Chemical substance"}
    }
  }
}
```

### NDC Codes:
```
✅ ALL active NDC codes from FDA
✅ Full product details
✅ Brand and generic names
✅ Active ingredients with strengths
✅ Dosage forms and routes
✅ Manufacturer information
```

Example:
```json
{
  "47335-0985-60": {
    "brand_name": "Ezallor",
    "generic_name": "rosuvastatin",
    "dosage_form": "CAPSULE",
    "route": "ORAL",
    "labeler": "Althera Pharmaceuticals Inc.",
    "product_type": "HUMAN PRESCRIPTION DRUG",
    "active_ingredients": [
      {"name": "ROSUVASTATIN CALCIUM", "strength": "10 mg/1"}
    ],
    "description": "Ezallor - CAPSULE (ORAL)"
  }
}
```

---

