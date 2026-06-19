# Architecture-Aware Refactoring Skill

**Skill Name**: `architecture-aware-refactoring`  
**Version**: 1.0.0  
**Created**: 2026-06-18

## Purpose

Systematically analyze codebases with **architectural awareness**, checking domain boundaries, frontend/backend separation, repository patterns, and automatically identifying refactoring opportunities. Enforces modularity, reusability, and design patterns, with automatic triggers for files >800 LoC.

## Automatic Triggers

This skill **automatically activates** when:
- 📏 **File >800 LoC**: Automatic refactoring analysis
- 🔄 **Duplicate code detected**: 3+ similar code blocks
- 🏗️ **Architecture violation**: Cross-boundary dependencies
- 📦 **Missing abstraction**: Direct database/API calls in UI
- 🎯 **Pattern opportunity**: Code that matches known patterns

## Phase 1: Architecture Discovery

### Step 1.1: Identify Project Structure

**Check these directories systematically**:

```bash
# 1. Frontend structure
ls -la frontend/src/
ls -la frontend/src/components/
ls -la frontend/src/pages/
ls -la frontend/src/services/
ls -la frontend/src/hooks/
ls -la frontend/src/utils/

# 2. Backend structure
ls -la backend/
ls -la backend/app/
ls -la backend/app/api/
ls -la backend/app/models/
ls -la backend/app/services/
ls -la backend/app/repositories/
ls -la backend/app/domain/

# 3. Shared/Common
ls -la src/shared/
ls -la src/common/
ls -la src/core/

# 4. Domain modules
ls -la src/*/domain/
ls -la src/*/models/
ls -la src/*/services/
```

### Step 1.2: Map Architecture Layers

**Identify the architecture pattern**:

```
┌─────────────────────────────────────┐
│         Presentation Layer          │
│  (UI, Controllers, API Endpoints)   │
├─────────────────────────────────────┤
│         Application Layer           │
│    (Use Cases, Services, DTOs)      │
├─────────────────────────────────────┤
│           Domain Layer              │
│  (Entities, Value Objects, Logic)   │
├─────────────────────────────────────┤
│       Infrastructure Layer          │
│  (Repositories, External Services)  │
└─────────────────────────────────────┘
```

**Check for**:
- ✅ Clear layer separation
- ✅ Dependency direction (outer → inner)
- ❌ Layer violations (inner → outer)
- ❌ Cross-cutting concerns not abstracted

### Step 1.3: Identify Domain Boundaries

**Map bounded contexts**:

```bash
# Find domain modules
find . -type d -name "domain" -o -name "domains"

# Check for domain models
rg "class.*Model|class.*Entity|class.*ValueObject" --type py

# Identify aggregates
rg "class.*Aggregate|class.*Root" --type py
```

**Questions to ask**:
- 🤔 Are domains clearly separated?
- 🤔 Do domains have their own models/services/repos?
- 🤔 Are there shared kernels or anti-corruption layers?
- 🤔 Is there domain logic in presentation layer?

## Phase 2: Technical Analysis

### Step 2.1: File Size Analysis (Automatic)

**Trigger**: Any file >800 LoC

```bash
# Find large files
find . -name "*.py" -exec wc -l {} \; | awk '$1 > 800' | sort -rn

# Analyze each large file
for file in $(find . -name "*.py" -exec wc -l {} \; | awk '$1 > 800 {print $2}'); do
    echo "=== Analyzing: $file ==="
    wc -l "$file"
    rg "^class |^def " "$file" | wc -l  # Count classes/functions
    rg "^    def " "$file" | wc -l      # Count methods
done
```

**For each file >800 LoC, check**:
1. **Single Responsibility**: Does it do one thing?
2. **Cohesion**: Are functions related?
3. **Coupling**: How many imports/dependencies?
4. **Extractable modules**: Can parts be separated?

### Step 2.2: Reusability Check

**Search for reusable patterns**:

```bash
# 1. Find duplicate code blocks
rg -A 10 "def process_|def handle_|def calculate_" --type py | \
    sort | uniq -c | sort -rn | head -20

# 2. Find similar function signatures
rg "^def \w+\([^)]*\):" --type py | \
    sed 's/def \([^(]*\).*/\1/' | sort | uniq -c | sort -rn

# 3. Find hardcoded values that should be constants
rg '"[^"]{20,}"' --type py  # Long strings
rg '\b\d{3,}\b' --type py   # Magic numbers

# 4. Find repeated imports
rg "^from .* import" --type py | sort | uniq -c | sort -rn | head -20
```

**Questions**:
- 🤔 Is this code used in multiple places?
- 🤔 Could this be a shared utility?
- 🤔 Should this be in a base class?
- 🤔 Is there a design pattern that fits?

### Step 2.3: Frontend/Backend Separation Check

**For full-stack projects**:

```bash
# Check for backend code in frontend
rg "import.*backend|from.*backend" frontend/

# Check for frontend code in backend
rg "import.*frontend|from.*frontend" backend/

# Check for direct database access in frontend
rg "SELECT|INSERT|UPDATE|DELETE|\.query\(|\.execute\(" frontend/

# Check for UI code in backend
rg "render|template|html|css|style" backend/app/domain/ backend/app/services/
```

**Violations to fix**:
- ❌ Database queries in frontend → Use API calls
- ❌ UI logic in backend domain → Move to presentation
- ❌ Business logic in frontend → Move to backend service
- ❌ Direct model access across boundary → Use DTOs

### Step 2.4: Repository Pattern Check

**Check if repository pattern is used**:

```bash
# Find repository classes
rg "class.*Repository" --type py

# Find direct database access outside repositories
rg "session\.query|session\.add|session\.commit" --type py | \
    grep -v "repository" | grep -v "repo"

# Find direct ORM usage in services
rg "from.*models import|from.*orm import" backend/app/services/
```

**Should be**:
```python
# ✅ GOOD: Repository pattern
class UserRepository:
    def find_by_id(self, user_id: int) -> User:
        return self.session.query(User).filter_by(id=user_id).first()

class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    def get_user(self, user_id: int) -> UserDTO:
        user = self.user_repo.find_by_id(user_id)
        return UserDTO.from_entity(user)
```

**Not**:
```python
# ❌ BAD: Direct database access in service
class UserService:
    def get_user(self, user_id: int):
        return session.query(User).filter_by(id=user_id).first()
```

## Phase 3: Pattern Detection & Application

### Step 3.1: Detect Applicable Patterns

**Check for these patterns**:

#### 1. **Strategy Pattern** (Multiple algorithms)
```bash
# Find if/elif chains that could be strategies
rg "if.*==.*:|elif.*==.*:" --type py -A 5 | grep -c "elif" | \
    awk '$1 > 3 {print "Consider Strategy Pattern"}'
```

#### 2. **Factory Pattern** (Object creation)
```bash
# Find complex object creation
rg "if.*type.*==|if.*kind.*==|if.*mode.*==" --type py -A 3 | \
    grep "= .*\(" | head -10
```

#### 3. **Repository Pattern** (Data access)
```bash
# Find direct database access
rg "session\.query|\.filter|\.all\(\)|\.first\(\)" --type py | \
    grep -v "repository"
```

#### 4. **Dependency Injection** (Loose coupling)
```bash
# Find tight coupling
rg "= .*\(\)" --type py | grep -v "__init__" | head -20
```

#### 5. **Observer Pattern** (Event handling)
```bash
# Find event-like code
rg "on_|handle_|notify|subscribe|publish" --type py
```

### Step 3.2: Modularity Opportunities

**Check for extractable modules**:

```python
# Analyze a large file
def analyze_file_modularity(filepath: str):
    """
    Check if file can be split into modules.
    
    Triggers:
    - >800 LoC
    - >10 classes
    - >50 functions
    - Multiple unrelated responsibilities
    """
    
    # 1. Count classes/functions
    classes = count_classes(filepath)
    functions = count_functions(filepath)
    lines = count_lines(filepath)
    
    # 2. Analyze imports (coupling)
    imports = analyze_imports(filepath)
    
    # 3. Identify cohesive groups
    groups = cluster_by_cohesion(filepath)
    
    # 4. Suggest splits
    if len(groups) > 1:
        suggest_module_split(groups)
```

**Common splits**:
- **By responsibility**: `user_service.py` → `user_creation.py`, `user_authentication.py`
- **By layer**: `handlers.py` → `api/handlers.py`, `domain/handlers.py`
- **By domain**: `models.py` → `user/models.py`, `product/models.py`
- **By pattern**: `utils.py` → `validators.py`, `formatters.py`, `converters.py`

## Phase 4: Refactoring Execution

### Step 4.1: Extract to Shared Module

**When**: Code used in 2+ places

**Process**:
1. **Identify common code**
2. **Choose location** (see decision tree below)
3. **Extract to module**
4. **Update imports**
5. **Remove duplicates**
6. **Test**

**Location Decision Tree**:
```
What type of code is it?
├─ Domain logic → domain/
├─ Data access → repositories/
├─ Business rules → services/
├─ API handling → api/
├─ UI components → components/
├─ Utilities → utils/
├─ Configuration → config/
└─ Types/Models → models/ or types/
```

### Step 4.2: Apply Repository Pattern

**When**: Direct database access in services

**Before**:
```python
# services/user_service.py
class UserService:
    def get_user(self, user_id: int):
        return db.session.query(User).filter_by(id=user_id).first()
```

**After**:
```python
# repositories/user_repository.py
class UserRepository:
    def __init__(self, session):
        self.session = session
    
    def find_by_id(self, user_id: int) -> Optional[User]:
        return self.session.query(User).filter_by(id=user_id).first()
    
    def find_all(self) -> List[User]:
        return self.session.query(User).all()
    
    def save(self, user: User) -> User:
        self.session.add(user)
        self.session.commit()
        return user

# services/user_service.py
class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    def get_user(self, user_id: int) -> UserDTO:
        user = self.user_repo.find_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        return UserDTO.from_entity(user)
```

### Step 4.3: Split Large Files (>800 LoC)

**Process**:
1. **Analyze cohesion**: Group related functions/classes
2. **Identify boundaries**: Find natural split points
3. **Create new modules**: One per cohesive group
4. **Move code**: Extract to new files
5. **Update imports**: Fix all references
6. **Create __init__.py**: Re-export if needed

**Example Split**:
```python
# Before: user_management.py (1200 LoC)
class UserService:
    def create_user(...): ...
    def authenticate_user(...): ...
    def update_profile(...): ...
    def delete_user(...): ...
    def send_welcome_email(...): ...
    def verify_email(...): ...
    def reset_password(...): ...

# After: Split into focused modules
# user/creation.py (200 LoC)
class UserCreationService:
    def create_user(...): ...
    def send_welcome_email(...): ...

# user/authentication.py (250 LoC)
class UserAuthenticationService:
    def authenticate_user(...): ...
    def reset_password(...): ...
    def verify_email(...): ...

# user/profile.py (150 LoC)
class UserProfileService:
    def update_profile(...): ...
    def delete_user(...): ...

# user/__init__.py
from .creation import UserCreationService
from .authentication import UserAuthenticationService
from .profile import UserProfileService
```

### Step 4.4: Frontend/Backend Separation

**When**: Mixed concerns detected

**Backend** (API/Services):
```python
# backend/app/api/users.py
@router.get("/users/{user_id}")
async def get_user(user_id: int, service: UserService = Depends()):
    return service.get_user(user_id)

# backend/app/services/user_service.py
class UserService:
    def get_user(self, user_id: int) -> UserDTO:
        # Business logic here
        pass
```

**Frontend** (API Client):
```typescript
// frontend/src/services/userService.ts
export class UserService {
    async getUser(userId: number): Promise<User> {
        const response = await fetch(`/api/users/${userId}`);
        return response.json();
    }
}

// frontend/src/components/UserProfile.tsx
function UserProfile({ userId }: Props) {
    const [user, setUser] = useState<User | null>(null);
    
    useEffect(() => {
        userService.getUser(userId).then(setUser);
    }, [userId]);
    
    return <div>{user?.name}</div>;
}
```

## Phase 5: Verification & Documentation

### Step 5.1: Architecture Compliance Check

```bash
# 1. Check layer dependencies
python scripts/check_architecture.py

# 2. Verify no circular dependencies
python -m pydeps src/ --show-cycles

# 3. Check import violations
rg "from.*domain.*import" src/api/ src/ui/  # Should be empty

# 4. Verify repository pattern
rg "session\.query" src/services/  # Should be empty
```

### Step 5.2: Metrics

**Track these metrics**:

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| **Avg file size** | 650 LoC | 350 LoC | <500 LoC |
| **Files >800 LoC** | 12 | 0 | 0 |
| **Code duplication** | 15% | 3% | <5% |
| **Cyclomatic complexity** | 25 | 12 | <15 |
| **Coupling** | High | Low | Low |
| **Cohesion** | 0.6 | 0.9 | >0.8 |

### Step 5.3: Documentation

**Create these artifacts**:

1. **Architecture Decision Record (ADR)**
```markdown
# ADR-001: Extract User Management to Separate Modules

## Status
Accepted

## Context
user_management.py was 1200 LoC with multiple responsibilities

## Decision
Split into creation, authentication, and profile modules

## Consequences
+ Better separation of concerns
+ Easier to test
+ Clearer responsibilities
- More files to navigate
```

2. **Refactoring Summary**
```markdown
# Refactoring Summary: User Management Module

## Changes Made
- Split user_management.py (1200 LoC) into 3 modules
- Extracted UserRepository from UserService
- Applied dependency injection
- Moved email logic to separate service

## Files Changed
- Created: user/creation.py, user/authentication.py, user/profile.py
- Modified: user/__init__.py, tests/test_user.py
- Deleted: user_management.py

## Impact
- Reduced file size by 75%
- Improved testability
- Clearer domain boundaries
```

## Automatic Checks (Run on Every Commit)

```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Running architecture checks..."

# 1. Check for large files
large_files=$(find . -name "*.py" -exec wc -l {} \; | awk '$1 > 800 {print $2}')
if [ -n "$large_files" ]; then
    echo "❌ Files >800 LoC detected:"
    echo "$large_files"
    echo "Consider refactoring these files"
    exit 1
fi

# 2. Check for code duplication
duplication=$(pylint --disable=all --enable=duplicate-code src/)
if echo "$duplication" | grep -q "Similar lines"; then
    echo "❌ Code duplication detected"
    echo "$duplication"
    exit 1
fi

# 3. Check architecture violations
violations=$(python scripts/check_architecture.py)
if [ $? -ne 0 ]; then
    echo "❌ Architecture violations detected:"
    echo "$violations"
    exit 1
fi

echo "✅ All checks passed"
```

## Decision Trees

### Should I Extract This Code?

```
Is it used in 2+ places?
├─ YES → Extract to shared module
└─ NO → Continue...
    │
    Is it >100 LoC?
    ├─ YES → Consider extraction for clarity
    └─ NO → Continue...
        │
        Does it have a clear responsibility?
        ├─ YES → Consider extraction for SRP
        └─ NO → Keep inline (for now)
```

### Where Should This Code Live?

```
What does it do?
├─ Database access → repositories/
├─ Business logic → services/ or domain/
├─ API handling → api/ or controllers/
├─ UI rendering → components/ or views/
├─ Data transformation → mappers/ or transformers/
├─ Validation → validators/
├─ Configuration → config/
├─ Utilities → utils/ (last resort)
└─ Types/Models → models/ or types/
```

### Should I Apply a Pattern?

```
What's the problem?
├─ Multiple algorithms → Strategy Pattern
├─ Complex object creation → Factory Pattern
├─ Data access scattered → Repository Pattern
├─ Tight coupling → Dependency Injection
├─ Event handling → Observer Pattern
├─ State management → State Pattern
└─ Cross-cutting concerns → Decorator/Middleware
```

## Checklist

### Before Refactoring
- [ ] Understand current architecture
- [ ] Map domain boundaries
- [ ] Identify all dependencies
- [ ] Check for existing patterns
- [ ] Review test coverage
- [ ] Create backup/branch

### During Refactoring
- [ ] Follow architecture layers
- [ ] Maintain domain boundaries
- [ ] Apply appropriate patterns
- [ ] Keep changes atomic
- [ ] Update tests incrementally
- [ ] Document decisions

### After Refactoring
- [ ] All tests pass
- [ ] No architecture violations
- [ ] Code duplication <5%
- [ ] No files >800 LoC
- [ ] Documentation updated
- [ ] Team review completed

## Real-World Example: This Project

### Problem
`uq_benchmarks.py` had hardcoded signal names (lines 267-275)

### Analysis
1. **Architecture check**: Visualization layer (presentation)
2. **Reusability check**: Signal names used in 5+ files
3. **Pattern check**: Constants scattered (SSOT violation)
4. **Domain check**: Belongs in shared/types (domain constants)

### Solution
1. **Centralized**: Moved to `shared/types.py::SIGNAL_NAMES`
2. **Updated imports**: Changed from hardcoded to import
3. **Removed duplicates**: Deleted 4 other definitions
4. **Documented**: Created SIGNAL_NAMES_CENTRALIZATION.md

### Result
- ✅ Single source of truth
- ✅ Reduced maintenance burden
- ✅ Eliminated inconsistency risk
- ✅ Followed architecture principles

---

**Skill Status**: ✅ Active  
**Auto-Trigger**: Files >800 LoC  
**Last Updated**: 2026-06-18

*Systematic architecture-aware refactoring with automatic quality checks*