# Progressive App Quick Start Guide

## 🚀 Get Started in 3 Minutes

### Prerequisites
- FastAPI backend running on `http://localhost:8000`
- Python environment with Streamlit installed

### Launch the App

```bash
cd uqlab-streamlit
streamlit run streamlit_app_progressive.py
```

The app will open in your browser at `http://localhost:8501`

## 📝 Your First Experiment

### Step 1: Choose Dataset (30 seconds)
1. Select **cifar10** from dropdown
2. Choose noise type: **worse_label** (or **none** for clean data)
3. Review dataset statistics
4. Click **"✓ Continue to Training Setup"**

### Step 2: Configure Training (1 minute)
**Option A - Train New Model:**
1. Keep default: **dinov2-small**
2. Set epochs: **12** (or fewer for quick test)
3. Click **"✓ Continue to Uncertainty Configuration"**

**Option B - Use Checkpoint:**
1. Select **"Use existing checkpoint"**
2. Choose a completed experiment
3. Click **"✓ Continue to Uncertainty Configuration"**

### Step 3: Set Uncertainty Parameters (1 minute)
**Epistemic (Left Column):**
1. Check **"Enable dataset size sweep"**
2. Select **"Random selection"**
3. Set **2** under-supported classes
4. Under-supported samples: **50**
5. Regular samples: **300**

**Aleatoric (Right Column):**
1. Check **"Use dataset noise"** (if you selected worse_label)
   - OR check **"Add custom label noise"** and set rate

Click **"✓ Continue to Evaluation Setup"**

### Step 4: Configure Evaluation (30 seconds)
1. Samples per group: **100**
2. MC dropout passes: **20**
3. Select signals (defaults are good):
   - ✅ inverse_mass
   - ✅ dominance
   - ✅ inverse_logit_magnitude
   - ✅ inverse_coherence
   - ✅ msp_uncertainty
   - ✅ predictive_entropy

Click **"✓ Review & Launch Experiment"**

### Step 5: Launch! (10 seconds)
1. Review configuration summary
2. Optionally rename experiment
3. Click **"🚀 Launch Experiment"**

✅ Done! Your experiment is now running.

## 🎯 What Happens Next?

After launching:
1. Experiment is created in the backend
2. Training begins (if training new model)
3. Evaluation runs with uncertainty quantification
4. Results appear in the original Streamlit app (`streamlit_app.py`)

## 💡 Pro Tips

### Quick Test Configuration
For fastest results (testing only):
- **Epochs**: 1-2
- **Under-supported samples**: 50
- **Regular samples**: 100
- **Eval per group**: 50
- **MC passes**: 5

### Production Configuration
For real experiments:
- **Epochs**: 12-20
- **Under-supported samples**: 50-100
- **Regular samples**: 300-500
- **Eval per group**: 100-200
- **MC passes**: 20-30

### Editing Previous Steps
- Click **"Edit"** button on any completed step
- Modify settings
- Click **"Continue"** to proceed
- All subsequent steps remain intact

### Starting Over
- Click **"🔄 Start Over"** in sidebar
- OR click **"← Start Over"** in Step 5
- All configuration is reset

## 🔍 Understanding the Results

After experiment completes, view results in `streamlit_app.py`:

1. **Per-sample Signals**: See uncertainty for each test sample
2. **Signal Diagnostics**: Validate signal quality with UDE scores
3. **Hypothesis Validation**: Check if signals correctly identify uncertainty sources

## 🐛 Troubleshooting

### "Failed to fetch dataset stats"
**Problem**: Backend not running
**Solution**: 
```bash
cd uqlab-streamlit/backend
uvicorn app.main:app --reload
```

### "No completed experiments found"
**Problem**: No checkpoints available for Step 2
**Solution**: Choose "Train new model" instead

### Configuration lost after refresh
**Problem**: Browser refresh clears session state
**Solution**: This is normal - complete workflow before refreshing

## 📚 Learn More

- **Full Documentation**: `PROGRESSIVE_APP_README.md`
- **UX Specification**: `STREAMLIT_PROGRESSIVE_UX_SPEC.md`
- **Architecture**: `STREAMLIT_REDESIGN_PLAN.md`

## 🎓 Example Workflows

### Workflow 1: Epistemic Uncertainty Only
```
Step 1: CIFAR-10, no noise
Step 2: dinov2-small, 12 epochs
Step 3: Epistemic enabled, Aleatoric disabled
Step 4: 100 samples/group, 20 MC passes
Step 5: Launch
```
**Tests**: Model uncertainty from limited training data

### Workflow 2: Aleatoric Uncertainty Only
```
Step 1: CIFAR-10, worse_label noise
Step 2: dinov2-small, 12 epochs
Step 3: Epistemic disabled, Aleatoric enabled (use dataset noise)
Step 4: 100 samples/group, 20 MC passes
Step 5: Launch
```
**Tests**: Data uncertainty from noisy labels

### Workflow 3: Both Uncertainties
```
Step 1: CIFAR-10, worse_label noise
Step 2: dinov2-small, 12 epochs
Step 3: Both enabled
Step 4: 100 samples/group, 20 MC passes
Step 5: Launch
```
**Tests**: Full uncertainty disentanglement

## ⏱️ Expected Runtimes

| Configuration | Training Time | Evaluation Time | Total |
|--------------|---------------|-----------------|-------|
| Quick test (1 epoch) | ~2 min | ~1 min | ~3 min |
| Standard (12 epochs) | ~20 min | ~5 min | ~25 min |
| Full (20 epochs) | ~35 min | ~10 min | ~45 min |

*Times are approximate and depend on hardware (GPU recommended)*

## 🎉 Success Indicators

You'll know it's working when:
- ✅ Each step shows green checkmark after completion
- ✅ Progress tracker in sidebar updates
- ✅ Configuration summaries appear as collapsed boxes
- ✅ Final step shows complete configuration review
- ✅ Backend returns experiment ID after launch

---

**Ready to start?** Run `streamlit run streamlit_app_progressive.py` and follow the steps above!