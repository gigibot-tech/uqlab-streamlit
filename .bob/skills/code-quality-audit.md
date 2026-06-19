# Code Quality Audit Skill

**Skill Name**: `code-quality-audit`  
**Version**: 1.0.0  
**Created**: 2026-06-18

## Purpose

Systematically audit codebases for violations of DRY (Don't Repeat Yourself), SSOT (Single Source of Truth), and modularity principles. Identify hardcoded duplicates, scattered constants, and opportunities for centralization.

## When to Use This Skill

- 🔍 **Code Review**: Before merging new code
- 🏗️ **Refactoring**: When improving code quality
- 📊 **Onboarding**: Understanding a new codebase
- 🐛 **Bug Investigation**: Finding inconsistencies
- 📝 **Documentation**: Creating architecture guides

## Skill Workflow

### Phase 1: Discovery

1. **Identify Constants and Patterns**
   ```bash
   # Find hardcoded lists
   rg "CONSTANT_NAME\s*=\s*\[" --type py
   
   # Find string literal patterns
   rg "'pattern1'.*'pattern2'.*'pattern3'" --type py
   
   # Find repeated values
   rg "specific_value" --type py -c | sort -t: -k2 -rn
   ```

2. **Search for Canonical Sources**
   ```bash
   # Look in common locations
   find . -name "types.py" -o -name "constants.py" -o -name "config.py"
   
   # Check shared/common modules
   ls -la src/*/shared/ src/*/common/ src/*/config/
   ```

3. **Map All Occurrences**
   - Create a table of where each constant appears
   - Note if it's a definition or usage
   - Check if values are identical

### Phase 2: Analysis

1. **Categorize Findings**
   
   **✅ Good (Centralized)**:
   - Single definition in shared module
   - All other locations import from it
   - Clear documentation of canonical source
   
   **⚠️ Warning (Duplicated)**:
   - Same constant defined in 2-3 places
   - Values are identical but separate
   - No clear canonical source
   
   **❌ Critical (Scattered)**:
   - Constant defined in 4+ places
   - Values may have drifted
   - High maintenance burden

2. **Assess Impact**
   
   For each duplicate, evaluate:
   - **Frequency**: How many locations?
   - **Consistency**: Are values identical?
   - **Maintenance**: How often does it change?
   - **Risk**: What breaks if inconsistent?

3. **Prioritize Fixes**
   
   **Priority 1 (Fix Now)**:
   - Active code with 3+ duplicates
   - Values that change frequently
   - Critical system constants
   
   **Priority 2 (Plan to Fix)**:
   - Stable code with 2 duplicates
   - Infrequently changed values
   - Non-critical constants
   
   **Priority 3 (Document Only)**:
   - Legacy code
   - Test fixtures
   - Example data

### Phase 3: Centralization

1. **Choose Canonical Location**
   
   **Decision Criteria**:
   - ✅ Already imported in multiple places
   - ✅ Part of shared/common module
   - ✅ Clear, descriptive module name
   - ✅ Appropriate abstraction level
   
   **Common Patterns**:
   ```
   src/
   ├── shared/
   │   ├── types.py          # Type definitions & constants
   │   ├── constants.py      # Application constants
   │   └── config.py         # Configuration values
   ├── common/
   │   └── enums.py          # Enumerated types
   └── core/
       └── settings.py       # System settings
   ```

2. **Implement Centralization**
   
   **Step 1**: Add to canonical source
   ```python
   # File: shared/types.py
   
   # Signal names in canonical order
   # This is the SINGLE SOURCE OF TRUTH for signal names
   # All other code should import from here
   SIGNAL_NAMES = [
       "signal_1",
       "signal_2",
       "signal_3",
   ]
   ```
   
   **Step 2**: Update imports
   ```python
   # File: anywhere_else.py
   
   # ❌ BEFORE (hardcoded)
   signal_names = ["signal_1", "signal_2", "signal_3"]
   
   # ✅ AFTER (imported)
   from shared.types import SIGNAL_NAMES
   for signal in SIGNAL_NAMES:
       process(signal)
   ```
   
   **Step 3**: Remove duplicates
   - Delete hardcoded definitions
   - Add comment pointing to canonical source
   - Update documentation

3. **Verify Consistency**
   ```bash
   # Check all imports work
   python -m pytest tests/
   
   # Verify no hardcoded duplicates remain
   rg "signal_names\s*=\s*\[" --type py
   
   # Confirm all use canonical source
   rg "from.*import.*SIGNAL_NAMES" --type py
   ```

### Phase 4: Documentation

1. **Document Canonical Source**
   ```python
   # File: shared/types.py
   
   # ============================================================================
   # CANONICAL CONSTANTS - Single Source of Truth
   # ============================================================================
   # 
   # These constants are the authoritative definitions used throughout the
   # codebase. DO NOT duplicate these values elsewhere - always import from
   # this module.
   #
   # To add a new signal:
   # 1. Add to SIGNAL_NAMES list below
   # 2. Add display label to SIGNAL_LABELS dict
   # 3. Update tests in tests/test_signals.py
   # 4. Update documentation in docs/signals.md
   # ============================================================================
   
   SIGNAL_NAMES = [...]
   ```

2. **Add Migration Comments**
   ```python
   # File: old_location.py (if kept for compatibility)
   
   # DEPRECATED: This constant has been moved to shared.types
   # Import from there instead:
   #   from shared.types import SIGNAL_NAMES
   # This alias will be removed in version 2.0
   SIGNAL_NAMES = _SIGNAL_NAMES  # Re-export for compatibility
   ```

3. **Create Audit Report**
   ```markdown
   # Code Quality Audit Report
   
   ## Summary
   - **Duplicates Found**: 5
   - **Duplicates Fixed**: 5
   - **Canonical Sources**: 1
   - **Impact**: Reduced maintenance burden by 80%
   
   ## Changes Made
   1. Centralized SIGNAL_NAMES in shared/types.py
   2. Updated 5 files to import from canonical source
   3. Removed hardcoded duplicates
   4. Added documentation
   
   ## Verification
   - ✅ All tests pass
   - ✅ No hardcoded duplicates remain
   - ✅ All imports verified
   ```

## Decision Trees

### Should I Centralize This?

```
Is it used in 2+ files?
├─ NO → Keep it local
└─ YES → Continue...
    │
    Does it define system behavior?
    ├─ YES → CENTRALIZE (Priority 1)
    └─ NO → Continue...
        │
        Is it iterated over?
        ├─ YES → CENTRALIZE (Priority 1)
        └─ NO → Continue...
            │
            Does it change frequently?
            ├─ YES → CENTRALIZE (Priority 2)
            └─ NO → DOCUMENT (Priority 3)
```

### Where Should I Centralize It?

```
What type of constant is it?
├─ Type definition → shared/types.py
├─ Application constant → shared/constants.py
├─ Configuration value → shared/config.py
├─ Enumerated type → common/enums.py
├─ System setting → core/settings.py
└─ Domain-specific → domain/constants.py
```

## Common Patterns to Look For

### Pattern 1: Hardcoded Lists

```python
# ❌ BAD: Hardcoded in multiple files
signal_names = ["a", "b", "c"]  # File 1
signal_names = ["a", "b", "c"]  # File 2
signal_names = ["a", "b", "c"]  # File 3

# ✅ GOOD: Centralized
from shared.types import SIGNAL_NAMES  # All files
```

### Pattern 2: Magic Numbers/Strings

```python
# ❌ BAD: Magic values scattered
if status == "pending":  # File 1
if status == "pending":  # File 2
if status == "pending":  # File 3

# ✅ GOOD: Named constants
from shared.constants import STATUS_PENDING
if status == STATUS_PENDING:  # All files
```

### Pattern 3: Configuration Duplication

```python
# ❌ BAD: Config in multiple places
API_URL = "https://api.example.com"  # File 1
API_URL = "https://api.example.com"  # File 2

# ✅ GOOD: Single config source
from shared.config import API_URL  # All files
```

### Pattern 4: Enum-like Values

```python
# ❌ BAD: String literals everywhere
if mode == "train":  # File 1
if mode == "test":   # File 2
if mode == "eval":   # File 3

# ✅ GOOD: Enum or constants
from common.enums import Mode
if mode == Mode.TRAIN:  # All files
```

## Checklist

### Before Starting
- [ ] Understand the codebase structure
- [ ] Identify common module locations
- [ ] Set up search tools (ripgrep, grep, etc.)
- [ ] Create audit tracking document

### During Audit
- [ ] Search for hardcoded patterns
- [ ] Map all occurrences
- [ ] Categorize by severity
- [ ] Prioritize fixes
- [ ] Choose canonical locations
- [ ] Implement centralization
- [ ] Update all imports
- [ ] Remove duplicates

### After Completion
- [ ] Run all tests
- [ ] Verify no duplicates remain
- [ ] Update documentation
- [ ] Create audit report
- [ ] Add comments pointing to canonical sources
- [ ] Update team guidelines

## Examples from Real Codebases

### Example 1: Signal Names (This Project)

**Problem**: Signal names hardcoded in 5+ locations

**Solution**:
```python
# Canonical source: shared/types.py
SIGNAL_NAMES = [
    "msp_uncertainty",
    "predictive_entropy",
    "mutual_info",
    "inverse_coherence",
    "dominance",
    "inverse_mass",
    "inverse_logit_magnitude",
]

# Usage everywhere:
from shared.types import SIGNAL_NAMES
for signal in SIGNAL_NAMES:
    process(signal)
```

**Impact**: Reduced from 5 definitions to 1, eliminated inconsistency risk

### Example 2: API Endpoints

**Problem**: API URLs scattered across codebase

**Solution**:
```python
# Canonical source: shared/config.py
class APIConfig:
    BASE_URL = "https://api.example.com"
    ENDPOINTS = {
        "users": f"{BASE_URL}/users",
        "posts": f"{BASE_URL}/posts",
        "comments": f"{BASE_URL}/comments",
    }

# Usage:
from shared.config import APIConfig
response = requests.get(APIConfig.ENDPOINTS["users"])
```

**Impact**: Single place to update URLs, easier environment switching

## Anti-Patterns to Avoid

### ❌ Anti-Pattern 1: Over-Centralization

```python
# TOO CENTRALIZED: Everything in one giant file
# shared/constants.py (5000 lines)
USER_CONSTANTS = {...}
API_CONSTANTS = {...}
UI_CONSTANTS = {...}
DB_CONSTANTS = {...}
# ... 50 more categories
```

**Better**: Split by domain
```python
# shared/user_constants.py
# shared/api_constants.py
# shared/ui_constants.py
# shared/db_constants.py
```

### ❌ Anti-Pattern 2: Premature Centralization

```python
# Centralizing before pattern is clear
TEMP_VALUE = 42  # Only used once, might change
```

**Better**: Wait until used 2+ times

### ❌ Anti-Pattern 3: Wrong Abstraction Level

```python
# Too specific for shared module
JOHNS_FAVORITE_COLOR = "blue"  # In shared/constants.py
```

**Better**: Keep in appropriate scope

## Metrics

Track these metrics to measure improvement:

- **Duplication Rate**: `duplicates / total_constants`
- **Centralization Coverage**: `centralized / total_constants`
- **Import Consistency**: `correct_imports / total_imports`
- **Maintenance Burden**: `files_to_update_per_change`

## References

- **DRY Principle**: Don't Repeat Yourself
- **SSOT Principle**: Single Source of Truth
- **Modularity**: Separation of Concerns
- **Clean Code**: Robert C. Martin
- **Refactoring**: Martin Fowler

---

**Skill Status**: ✅ Active  
**Last Updated**: 2026-06-18  
**Maintainer**: Bob

*Use this skill to systematically improve code quality through centralization and modularity*