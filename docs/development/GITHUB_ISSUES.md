# GitHub Issues to Create

Based on analysis of the codebase, here are the issues to create. **Important:** The original "import errors" don't actually exist - all imports are valid!

---

## Repository 1: `uqlab` (ML Core)
**GitHub:** https://github.com/gigibot-tech/uqlab

### Issue 1: ✅ Test ResNet Training Modes
**Labels:** `testing`, `models`, `high-priority`

**Description:**
Verify ResNet18 works correctly in both training modes after recent refactoring:
- Feature-space mode (frozen backbone)
- End-to-end mode (full training)

**Acceptance Criteria:**
- [ ] Create test experiment with ResNet in feature-space mode
- [ ] Create test experiment with ResNet in end-to-end mode  
- [ ] Both experiments complete successfully
- [ ] Results are saved correctly
- [ ] Document any issues found

**Context:**
Recent refactoring added proper `freeze_backbone` support in [`2_models/resnet.py`](https://github.com/gigibot-tech/uqlab/blob/main/2_models/resnet.py). Need to validate both modes work as expected.

**Priority:** High

---

### Issue 2: 📦 Prepare for PyPI Release
**Labels:** `packaging`, `distribution`, `medium-priority`

**Description:**
Prepare the uqlab package for PyPI distribution to make it pip-installable.

**Acceptance Criteria:**
- [ ] Update `pyproject.toml` with correct metadata
- [ ] Add proper version numbering (semantic versioning)
- [ ] Ensure all dependencies are listed correctly
- [ ] Test local installation: `pip install -e .`
- [ ] Create distribution: `python -m build`
- [ ] Document installation instructions in README
- [ ] Test installation in clean environment

**Context:**
Package is currently only installable via git submodule. Making it pip-installable will improve usability.

**Priority:** Medium

---

### Issue 3: 📚 Improve Documentation
**Labels:** `documentation`, `low-priority`

**Description:**
Update documentation to reflect new uqlab naming and structure.

**Acceptance Criteria:**
- [ ] Update all references from "uqlab" to "uqlab" in docs
- [ ] Add architecture diagrams showing module relationships
- [ ] Document training modes for each model type (DINOv2, ResNet)
- [ ] Add examples for common use cases
- [ ] Document UI components structure
- [ ] Add API reference documentation

**Context:**
Recent rename from "uqlab" to "uqlab" requires documentation updates.

**Priority:** Low

---

## Repository 2: `uqlab-streamlit` (Application)
**GitHub:** https://github.com/gigibot-tech/uqlab-streamlit

### Issue 1: 🧪 End-to-End Testing
**Labels:** `testing`, `integration`, `high-priority`

**Description:**
Test complete workflow from UI to backend to ML training.

**Acceptance Criteria:**
- [ ] Install all dependencies: `pip install -r requirements.txt`
- [ ] Start backend: `uvicorn app.main:app --reload`
- [ ] Start Streamlit: `streamlit run streamlit_app.py`
- [ ] Create single experiment via UI
- [ ] Verify experiment runs successfully
- [ ] Create batch experiment via UI
- [ ] Verify batch experiments complete
- [ ] Check results are displayed correctly
- [ ] Test with both DINOv2 and ResNet models
- [ ] Document any issues found

**Context:**
Need to validate the complete system works end-to-end after recent refactoring.

**Priority:** High

---

### Issue 2: 🏗️ Backend Architecture Decision
**Labels:** `architecture`, `decision`, `high-priority`

**Description:**
Decide on final backend architecture based on Separation of Concerns audit.

**Current State:**
- Backend is in `uqlab-streamlit/backend/`
- Backend has 0 direct imports from uqlab (perfect isolation)
- SoC Score: 9.5/10 (see [`SEPARATION_OF_CONCERNS_AUDIT.md`](https://github.com/gigibot-tech/uqlab-streamlit/blob/main/SEPARATION_OF_CONCERNS_AUDIT.md))

**Options:**
1. **Keep backend in uqlab-streamlit** (recommended)
   - ✅ Optimal for this use case
   - ✅ Perfect separation already achieved
   - ✅ Simpler deployment
   - ✅ Easier development workflow

2. **Move to separate repository** (not recommended)
   - ❌ Overkill for current scope
   - ❌ Adds deployment complexity
   - ❌ No additional benefits given current isolation

**Acceptance Criteria:**
- [ ] Review `SEPARATION_OF_CONCERNS_AUDIT.md`
- [ ] Make architecture decision
- [ ] Document decision with rationale in README
- [ ] Update architecture diagrams if needed

**Recommendation:** Keep backend in uqlab-streamlit

**Priority:** High

---

### Issue 3: 🔧 Environment Setup Improvements
**Labels:** `devops`, `setup`, `medium-priority`

**Description:**
Improve development environment setup and documentation.

**Acceptance Criteria:**
- [ ] Update `.gitignore` to exclude all build artifacts
- [ ] Create `setup.sh` script for easy environment setup
- [ ] Document Python version requirements (3.11+)
- [ ] Add troubleshooting section to README
- [ ] Test setup on fresh clone
- [ ] Document virtual environment setup
- [ ] Add pre-commit hooks configuration

**Context:**
Make it easier for new developers to get started.

**Priority:** Medium

---

### Issue 4: 📱 Test Progressive Streamlit App
**Labels:** `testing`, `streamlit`, `medium-priority`

**Description:**
Test `streamlit_app_progressive.py` runs without errors.

**Current State:**
- File has proper stub functions for unimplemented modules (lines 60-100)
- No code import errors
- Only issue: streamlit package needs to be installed

**Acceptance Criteria:**
- [ ] Install dependencies: `pip install -r streamlit_requirements.txt`
- [ ] Run app: `streamlit run streamlit_app_progressive.py`
- [ ] Verify app starts without errors
- [ ] Test basic functionality (dataset selection, experiment creation)
- [ ] Document any missing features
- [ ] Compare with `streamlit_app.py` to identify differences

**Context:**
Progressive app uses MLflow-inspired UI pattern. Need to validate it works.

**Priority:** Medium

---

### Issue 5: 🚀 Deployment Preparation
**Labels:** `deployment`, `docker`, `low-priority`

**Description:**
Prepare application for production deployment.

**Acceptance Criteria:**
- [ ] Create Docker Compose setup for full stack
- [ ] Add environment variable configuration
- [ ] Document deployment steps
- [ ] Add health check endpoints
- [ ] Create deployment guide
- [ ] Test deployment in Docker
- [ ] Add monitoring/logging configuration

**Context:**
Prepare for production deployment when ready.

**Priority:** Low

---

## Summary

### High Priority Issues (Start Here)
**Total: 4 issues**

**uqlab (1 issue):**
1. ✅ Test ResNet Training Modes

**uqlab-streamlit (3 issues):**
1. 🧪 End-to-End Testing
2. 🏗️ Backend Architecture Decision
3. 📱 Test Progressive Streamlit App

### All Issues
**Total: 8 issues**

**uqlab (3 issues):**
1. ✅ Test ResNet Training Modes (High)
2. 📦 Prepare for PyPI Release (Medium)
3. 📚 Improve Documentation (Low)

**uqlab-streamlit (5 issues):**
1. 🧪 End-to-End Testing (High)
2. 🏗️ Backend Architecture Decision (High)
3. 🔧 Environment Setup Improvements (Medium)
4. 📱 Test Progressive Streamlit App (Medium)
5. 🚀 Deployment Preparation (Low)

---

## Important Note: Import Errors Investigation

**The original "import errors" issue was based on incorrect assumptions!**

After thorough analysis:
- ✅ All imports in `results/__init__.py` are valid
- ✅ All imports in `hypothesis_validation.py` are valid
- ✅ `streamlit_app_progressive.py` has proper stub functions

See [`RESOLUTION.md`](https://github.com/gigibot-tech/uqlab/blob/main/.specify/specs/0001-fix-import-errors/RESOLUTION.md) for full investigation details.

---

## How to Create These Issues

1. Go to each repository on GitHub
2. Click "Issues" → "New Issue"
3. Copy the title, labels, and description from above
4. Submit the issue

Or use GitHub CLI (if authenticated):
```bash
# For uqlab repo
cd uqlab-streamlit/src/uqlab
gh issue create --title "✅ Test ResNet Training Modes" --label "testing,models,high-priority" --body "..."

# For uqlab-streamlit repo
cd uqlab-streamlit
gh issue create --title "🧪 End-to-End Testing" --label "testing,integration,high-priority" --body "..."