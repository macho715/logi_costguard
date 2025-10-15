# HVDC Invoice Audit - Clean File Structure

**Last Updated**: 2025-10-13
**Cleanup Date**: 2025-10-13
**Files Archived**: 35

---

## Active File Structure

### Root Level

```
HVDC_Invoice_Audit/
├── FILE_INVENTORY.xlsx              [Inventory] Complete file listing
├── DUPLICATE_ANALYSIS.xlsx          [Analysis] Duplicate detection results
├── LEGACY_FILES_REPORT.xlsx         [Analysis] Legacy files analysis
├── CLEAN_FILE_STRUCTURE.md          [Doc] This file
├── FILE_CLEANUP_REPORT.md           [Doc] Cleanup summary
├── README.md                        [Doc] Project overview
├── QUICK_START.md                   [Doc] Getting started guide
└── create_file_inventory.py         [Utility] File scanner
```

---

## 01_DSV_SHPT (Shipment System)

### Core Systems (ACTIVE)

```
01_DSV_SHPT/Core_Systems/
├── shpt_sept_2025_enhanced_audit.py    [CORE] Main execution script
├── shpt_audit_system.py                [CORE] Core validation logic
├── run_shpt_sept2025.py                [CORE] Runner script
└── test_contract_validation.py         [TEST] Contract validation tests
```

### Data

```
01_DSV_SHPT/Data/DSV 202509/
├── SCNT SHIPMENT DRAFT INVOICE (SEPT 2025).xlsm    [DATA] Main invoice
├── SCNT Import (Sept 2025) - Supporting Documents/ [DATA] Evidence files
└── SCNT Domestic (Sept 2025) - Supporting Documents/ [DATA] Evidence files
```

### Results (Latest 3 Runs Only)

```
01_DSV_SHPT/Results/Sept_2025/
├── CSV/
│   └── shpt_sept_2025_enhanced_result_20251012_123701.csv
├── JSON/
│   └── shpt_sept_2025_enhanced_result_20251012_123701.json
├── Logs/
│   └── shpt_sept_2025_enhanced_audit.log
└── Reports/
    ├── SHPT_SEPT_2025_CONTRACT_IMPROVED_REPORT.md
    └── SHPT_CONTRACT_VALIDATION_REPORT.xlsx
```

### Documentation

```
01_DSV_SHPT/Documentation/
├── CONTRACT_ANALYSIS_SUMMARY.md
├── SHPT_SYSTEM_UPDATE_SUMMARY.md
└── SYSTEM_ARCHITECTURE_FINAL.md
```

---

## 02_DSV_DOMESTIC (Inland Transportation System)

### Core Systems (ACTIVE)

```
02_DSV_DOMESTIC/Core_Systems/
├── domestic_sept_2025_audit.py          [CORE] Main execution script
├── domestic_audit_system.py             [CORE] Core validation logic (PATCH applied)
├── run_domestic_sept2025.py             [CORE] Runner script
├── create_domestic_excel_report.py      [UTILITY] Report generator
├── create_improvement_report.py         [UTILITY] Improvement report
├── create_final_nocode_report.py        [UTILITY] NoCode solution report
└── analyze_critical_16.py               [UTILITY] CRITICAL analysis
```

### Data

```
02_DSV_DOMESTIC/
├── DOMESTIC_with_distances.xlsx         [DATA] Reference data (124 lanes)
└── Data/DSV 202509/
    ├── SCNT HVDC DRAFT INVOICE FOR DOMESTIC DELIVERY SEPTEMBER 2025.xlsx
    └── SCNT Domestic (Sept 2025) - Supporting Documents/
```

### Results (Latest 3 Runs Only)

```
02_DSV_DOMESTIC/Results/Sept_2025/
├── CSV/
│   ├── domestic_sept_2025_result_20251013_012914.csv (100 lanes)
│   ├── domestic_sept_2025_result_20251013_013624.csv (7-step patch)
│   └── domestic_sept_2025_interpolated_20251013_015906.csv (distance interp)
├── JSON/
│   └── (Latest 3 runs)
├── Logs/
│   └── (Latest 3 runs)
└── Reports/
    ├── DOMESTIC_IMPROVEMENT_COMPLETE_REPORT.xlsx
    ├── DISTANCE_SOLUTION_COMPLETE_REPORT.xlsx
    ├── VENDOR_DISTANCE_REQUEST_SEPT2025.xlsx
    ├── CRITICAL_16_TRIAGE.xlsx
    └── ApprovedLaneMap_ENHANCED.xlsx
```

### Configuration

```
02_DSV_DOMESTIC/
├── config_domestic_v2.json              [CONFIG] v2 configuration
└── config_domestic_enhanced.json        [CONFIG] Enhanced configuration
```

### Documentation

```
02_DSV_DOMESTIC/
├── DOMESTIC_SYSTEM_DOCUMENTATION.md
├── PATCH2-1.MD                          [Doc] Patch guide
├── PATCH_7STEPS_APPLIED.md              [Doc] 7-step patch log
├── PATCH_RESULTS_ANALYSIS.md            [Doc] Patch results
├── NOCODE_APPROACH_COMPLETE_SUMMARY.md  [Doc] NoCode summary
└── DISTANCE_INTERPOLATION_FINAL_ANALYSIS.md [Doc] Distance solution
```

---

## Rate Data (Shared)

```
Rate/
├── air_cargo_rates (1).json
├── bulk_cargo_rates (1).json
├── container_cargo_rates (1).json
└── inland_trucking_reference_rates_clean (2).json
```

---

## 00_Shared (Utilities - if exists)

```
00_Shared/
├── rate_loader.py                       [CORE] Unified rate loader
├── test_rate_loader.py                  [TEST] Rate loader tests
├── validate_rate_json.py                [UTILITY] Rate validation
└── analyze_md_files.py                  [UTILITY] MD file analysis
```

---

## Archive (Moved Files)

```
Archive/20251013_Before_Cleanup/
├── Backups/                             [3 files]
│   ├── DOMESTIC_with_distances_BACKUP_20251013_014933.xlsx
│   ├── domestic_audit_system.py.backup
│   └── ApprovedLaneMap_BACKUP_20251013_014905.xlsx
├── Legacy/                              [5 files]
│   ├── audit_runner.py
│   ├── audit_runner_improved.py
│   ├── audit_runner_enhanced.py
│   ├── advanced_audit_runner.py
│   └── parse_sept_2025_and_validate.py
├── Superseded/                          [1 file]
│   └── domestic_validator_patched.py
├── Old_Results/                         [26 files]
│   └── (Results older than latest 3 runs)
└── ARCHIVE_MANIFEST.xlsx                [Rollback manifest]
```

---

## File Dependency Map

### SHPT System Dependencies

```
shpt_sept_2025_enhanced_audit.py (Main)
  └── imports: shpt_audit_system
      └── uses: Rate/ JSON files (via UnifiedRateLoader)

run_shpt_sept2025.py
  └── executes: shpt_sept_2025_enhanced_audit.py
```

### DOMESTIC System Dependencies

```
domestic_sept_2025_audit.py (Main)
  └── imports: domestic_audit_system
      └── uses: DOMESTIC_with_distances.xlsx (ApprovedLaneMap 124 lanes)

Utilities:
- create_domestic_excel_report.py → Reads: Results/Sept_2025/CSV/*.csv
- create_improvement_report.py → Reads: Results/Sept_2025/CSV/*.csv
- apply_distance_interpolation.py → Reads: Results + DOMESTIC_with_distances.xlsx
```

---

## Recommended Workflow

### SHPT Invoice Validation

```bash
cd 01_DSV_SHPT/Core_Systems
python shpt_sept_2025_enhanced_audit.py
```

**Output**:
- `Results/Sept_2025/CSV/shpt_sept_2025_enhanced_result_*.csv`
- `Results/Sept_2025/Reports/SHPT_CONTRACT_VALIDATION_REPORT.xlsx`

### DOMESTIC Invoice Validation

```bash
cd 02_DSV_DOMESTIC/Core_Systems
python domestic_sept_2025_audit.py
```

**Output**:
- `Results/Sept_2025/CSV/domestic_sept_2025_result_*.csv`
- `Results/Sept_2025/domestic_sept_2025_result_*.xlsx`

### Generate Reports

```bash
# DOMESTIC improvement report
cd 02_DSV_DOMESTIC/Core_Systems
python create_improvement_report.py

# DOMESTIC Excel report
python create_domestic_excel_report.py

# Distance interpolation (if needed)
cd ../
python apply_distance_interpolation.py
```

---

## File Naming Conventions

### Active Files (Keep)

- **Main scripts**: `{system}_sept_2025_audit.py` or `{system}_sept_2025_enhanced_audit.py`
- **Core modules**: `{system}_audit_system.py`
- **Latest results**: Files from last 3 runs
- **Reference data**: `DOMESTIC_with_distances.xlsx` (124 lanes)
- **Final reports**: `*_COMPLETE_REPORT.xlsx`, `*_FINAL_REPORT.md`

### Archived Files (Moved)

- **Backups**: `*_BACKUP_*.xlsx`, `*.backup`
- **Old versions**: `*_v1.py`, `*_improved.py` (when _enhanced exists)
- **Old results**: Results older than latest 3 runs
- **Legacy**: Files in Legacy/ folders
- **Superseded**: Old scripts replaced by newer versions

---

## Active File Count

**Total Active Files**: ~450 (485 - 35 archived)

**By Category**:
- Documentation: ~190 (PDF evidence files + MD docs)
- Core Scripts: ~20
- Utilities: ~18
- Data Files: ~13
- Results (recent): ~40
- Configuration: ~10

---

## Rollback Instructions

If needed, restore files from archive:

```bash
# View archived files
cd Archive/20251013_Before_Cleanup
cat ARCHIVE_MANIFEST.xlsx

# Restore specific file
# Check manifest for original location
# Copy back manually
```

---

## Maintenance Guidelines

### Weekly

- Review new result files
- Archive results older than 3 runs
- Update this documentation if structure changes

### Monthly

- Review Archive/ folder
- Permanently delete archives older than 30 days (after verification)
- Update file count statistics

### Per Project Phase

- Create new Archive snapshot before major changes
- Document any structural changes
- Update dependency map

---

## Summary Statistics

**Before Cleanup**:
- Total files: 485
- Duplicates identified: 320+ (filename)
- Hash duplicates: 314

**After Cleanup**:
- Active files: ~450
- Archived files: 35
- Clean structure: ✅

**Space Saved**: ~5-10 MB (mostly old results and backups)

**System Status**: ✅ Both SHPT and DOMESTIC systems verified and working

---

**Document Version**: 1.0
**Maintained By**: HVDC Audit Team
**Next Review**: 2025-10-20

