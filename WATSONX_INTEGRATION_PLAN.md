# watsonx.ai Integration Plan for UQ Classification

## 🎯 Overview

This document outlines the integration strategy for exporting UQ classification results to **watsonx.ai** for scoring and **watsonx.governance** for metrics tracking. The Streamlit app generates standardized CSV/PT files that can be directly uploaded to IBM Cloud services.

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Streamlit Training UI                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Configure    │→ │ Train Model  │→ │ Generate     │          │
│  │ Experiment   │  │ & Evaluate   │  │ watsonx Files│          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Export Package (ZIP)                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 📁 watsonx_export_{timestamp}/                           │   │
│  │   ├── 📄 model_checkpoint.pt          (PyTorch weights)  │   │
│  │   ├── 📄 model_config.json            (Architecture)     │   │
│  │   ├── 📄 train_embeddings.pt          (Training data)    │   │
│  │   ├── 📄 eval_embeddings.pt           (Evaluation data)  │   │
│  │   ├── 📄 per_sample_signals.csv       (7 UQ signals)     │   │
│  │   ├── 📄 evaluation_metadata.csv      (Labels + preds)   │   │
│  │   ├── 📄 auroc_results.csv            (Binary metrics)   │   │
│  │   ├── 📄 experiment_config.yaml       (Full config)      │   │
│  │   └── 📄 README.txt                   (Usage guide)      │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    IBM Cloud Services                            │
│  ┌──────────────────┐              ┌──────────────────┐         │
│  │  watsonx.ai      │              │ watsonx.gov      │         │
│  │  ┌────────────┐  │              │  ┌────────────┐  │         │
│  │  │ Deploy     │  │              │  │ Track      │  │         │
│  │  │ Model      │  │              │  │ Metrics    │  │         │
│  │  └────────────┘  │              │  └────────────┘  │         │
│  │  ┌────────────┐  │              │  ┌────────────┐  │         │
│  │  │ Batch      │  │              │  │ Monitor    │  │         │
│  │  │ Scoring    │  │              │  │ Drift      │  │         │
│  │  └────────────┘  │              │  └────────────┘  │         │
│  └──────────────────┘              └──────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

## 📦 Export File Specifications

### 1. **model_checkpoint.pt** (~500 KB)
PyTorch model weights for deployment

**Contents:**
- `model_state_dict`: Trained model parameters
- `optimizer_state_dict`: Optimizer state (optional)
- `epoch`: Final training epoch
- `loss`: Final training loss

### 2. **model_config.json** (~2 KB)
Model architecture specification

```json
{
  "model_type": "EmbeddingDropoutMLP",
  "input_dim": 768,
  "hidden_dim": 256,
  "num_classes": 10,
  "dropout": 0.2,
  "dinov2_backbone": "dinov2_vitb14",
  "training_config": {...}
}
```

### 3. **train_embeddings.pt** (~10 MB for 5000 samples)
Training DINOv2 embeddings for model retraining

**Contents:**
- `embeddings`: [N_train, 768] DINOv2 features
- `labels`: Training labels (may be noisy)
- `noisy_labels`: Original noisy labels
- `is_noisy`: Boolean mask for noisy samples
- `indices`: Original dataset indices

**Use cases:**
- Model retraining in watsonx.ai
- Transfer learning to new tasks
- Analyzing training data distribution

### 4. **eval_embeddings.pt** (~1.8 MB for 300 samples)
Evaluation DINOv2 embeddings for testing

**Contents:**
- `embeddings`: [N_eval, 768] DINOv2 features
- `clean_labels`: Ground truth labels
- `noisy_labels`: Noisy labels (if applicable)
- `is_noisy`: Boolean mask
- `group_labels`: 0=clean, 1=aleatoric, 2=epistemic
- `indices`: Original dataset indices

**Use cases:**
- Reproducing evaluation results
- Testing model performance
- Comparing model versions

### 5. **per_sample_signals.csv** (~45 KB)
All uncertainty signals per evaluation sample

```csv
group,clean_label,is_noisy,msp_uncertainty,predictive_entropy,mutual_info,inverse_coherence,dominance,inverse_mass,inverse_logit_magnitude
clean,0,False,0.123,0.456,0.789,0.234,0.567,0.890,0.345
aleatoric,2,True,0.678,0.901,0.234,0.567,0.890,0.123,0.456
epistemic,4,False,0.901,0.234,0.567,0.890,0.123,0.456,0.789
```

**Signal Descriptions:**
- **Epistemic (Model Uncertainty):**
  - `mutual_info`: Information gain from model parameters
  - `inverse_coherence`: Inconsistency in attribution patterns
  - `dominance`: Concentration of attributions

- **Aleatoric (Data Uncertainty):**
  - `msp_uncertainty`: 1 - max(softmax)
  - `predictive_entropy`: Shannon entropy of predictions

- **Hybrid Signals:**
  - `inverse_mass`: Inverse of total attribution magnitude
  - `inverse_logit_magnitude`: Inverse of logit vector norm

### 6. **evaluation_metadata.csv** (~28 KB)
Sample-level predictions and ground truth

```csv
sample_id,original_index,group_label,clean_label,noisy_label,is_noisy,predicted_class,confidence
0,12345,0,0,0,False,0,0.95
1,23456,1,2,5,True,2,0.67
2,34567,2,4,4,False,8,0.42
```

### 7. **auroc_results.csv** (~1 KB)
Binary AUROC scores for each signal

```csv
signal_name,aleatoric_auroc,epistemic_auroc
msp_uncertainty,0.7230,0.6450
predictive_entropy,0.7560,0.6780
mutual_info,0.8120,0.7340
inverse_coherence,0.6890,0.8230
dominance,0.7340,0.8670
inverse_mass,0.7010,0.8450
inverse_logit_magnitude,0.6780,0.8010
```

**Interpretation:**
- Values range from 0.5 (random) to 1.0 (perfect)
- `aleatoric_auroc`: Ability to detect noisy labels
- `epistemic_auroc`: Ability to detect under-supported classes

### 8. **experiment_config.yaml** (~2 KB)
Complete experiment configuration

```yaml
seed: 42
device: cuda
data:
  noise_type: worst_label
  under_supported_classes: [3, 5]
  under_train_per_class: 50
  regular_train_per_class: 300
  eval_per_group: 100
model:
  dinov2_model: dinov2_vitb14
  hidden_dim: 256
  dropout: 0.2
training:
  epochs: 12
  learning_rate: 0.001
  weight_decay: 0.0001
```

### 9. **README.txt** (~3 KB)
Deployment instructions and usage guide

## 🚀 Deployment Workflow

### Step 1: Train Model in Streamlit
1. Configure experiment parameters
2. Click "🚀 Start Training"
3. Wait for training to complete
4. Review results and metrics

### Step 2: Generate Export Package
1. Scroll to "📤 Export for watsonx.ai" section
2. Click "🎁 Create Export Package"
3. Wait for file generation (~5-10 seconds)
4. Click "⬇️ Download Export Package"
5. Save ZIP file locally

### Step 3: Deploy to watsonx.ai
1. Log in to IBM Cloud
2. Navigate to watsonx.ai
3. Create new model deployment
4. Upload `model_checkpoint.pt`
5. Configure using `model_config.json`
6. Test with `eval_embeddings.pt`

### Step 4: Configure watsonx.governance
1. Navigate to watsonx.governance
2. Create new model entry
3. Upload `per_sample_signals.csv`
4. Set monitoring thresholds from `auroc_results.csv`
5. Enable drift detection

### Step 5: Monitor Production
1. Send new embeddings to scoring endpoint
2. Collect predictions and uncertainty scores
3. Log to watsonx.governance
4. Monitor AUROC metrics over time
5. Alert on drift or degradation

## 💡 Implementation Details

### Embedding Flow

**Training Phase:**
```
CIFAR-10N Images → DINOv2 Backbone → 768-dim Embeddings → MLP Classifier → Predictions
```

**Evaluation Phase:**
```
Eval Images → DINOv2 Backbone → 768-dim Embeddings → Trained MLP → Predictions + Uncertainty
```

**Production Inference:**
```
New Images → DINOv2 Backbone → 768-dim Embeddings → watsonx.ai Endpoint → Predictions
```

### Why Export Both Train + Eval Embeddings?

**Training Embeddings:**
- Enable model retraining in watsonx.ai
- Support transfer learning
- Allow data distribution analysis
- Size: ~10 MB for 5000 samples

**Evaluation Embeddings:**
- Reproduce exact evaluation results
- Test model performance
- Compare model versions
- Size: ~1.8 MB for 300 samples

**Total Package Size:** ~12-15 MB (compressed to ~8 MB in ZIP)

### Streamlit Integration

**New UI Section:**
```python
st.subheader("📤 Export for watsonx.ai")

if experiment_results:
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("Generate deployment package for IBM Cloud")
        if st.button("🎁 Create Export Package"):
            with st.spinner("Generating files..."):
                export_dir, zip_path = export_all_for_watsonx(...)
                st.success(f"Package created: {zip_path.name}")
    
    with col2:
        st.metric("Package Size", "~12 MB")
        st.metric("Files Included", "9")
        st.metric("Ready for", "watsonx.ai + governance")
    
    # Download button
    if zip_path.exists():
        with open(zip_path, "rb") as f:
            st.download_button(
                label="⬇️ Download Export Package",
                data=f,
                file_name=zip_path.name,
                mime="application/zip"
            )
```

## 📊 Value Proposition

### For Data Scientists
- ✅ **One-click export** - No manual file preparation
- ✅ **Standardized format** - Compatible with watsonx APIs
- ✅ **Complete package** - All files needed for deployment
- ✅ **Reproducible** - Full config included

### For MLOps Engineers
- ✅ **Ready for CI/CD** - Automated deployment pipeline
- ✅ **Version control** - Track model lineage
- ✅ **Monitoring ready** - Pre-computed metrics
- ✅ **Governance compliant** - Audit trail included

### For Business Stakeholders
- ✅ **Faster deployment** - Minutes instead of hours
- ✅ **Lower risk** - Standardized process
- ✅ **Better monitoring** - Track model performance
- ✅ **Compliance** - Built-in governance

## 🔍 Example Use Cases

### Use Case 1: A/B Testing
1. Train two models with different configs
2. Export both packages
3. Deploy to watsonx.ai as separate endpoints
4. Compare performance in watsonx.governance
5. Promote winner to production

### Use Case 2: Continuous Retraining
1. Train model on new data weekly
2. Auto-generate export package
3. Deploy to staging environment
4. Validate metrics in governance
5. Auto-promote if metrics improve

### Use Case 3: Multi-Region Deployment
1. Train model once in Streamlit
2. Generate export package
3. Deploy to multiple watsonx.ai regions
4. Centralized monitoring in governance
5. Consistent performance globally

## 📝 Module Documentation

### `watsonx_export.py`
Functions for generating export files:
- `export_model_checkpoint()` - Save PyTorch weights
- `export_model_config()` - Save architecture JSON
- `export_train_embeddings()` - Save training data
- `export_eval_embeddings()` - Save evaluation data
- `export_per_sample_signals()` - Save uncertainty CSV
- `export_evaluation_metadata()` - Save predictions CSV
- `export_auroc_results()` - Save metrics CSV
- `export_experiment_config()` - Save YAML config
- `create_readme()` - Generate usage instructions
- `create_watsonx_package()` - Bundle into ZIP
- `export_all_for_watsonx()` - Complete export workflow

### `watsonx_scoring.py`
Classes for watsonx.ai integration:
- `WatsonxScoringClient` - API client for scoring
- `WatsonxGovernanceLogger` - Metrics logging
- `create_mock_scoring_client()` - Local testing

## 🔗 References

- [watsonx.ai Documentation](https://www.ibm.com/docs/en/watsonx-as-a-service)
- [watsonx.governance Documentation](https://www.ibm.com/docs/en/watsonx/governance)
- [PyTorch Model Export Guide](https://pytorch.org/tutorials/beginner/saving_loading_models.html)
- [DINOv2 Documentation](https://github.com/facebookresearch/dinov2)

---

**Generated:** 2026-05-15  
**Version:** 1.0  
**Status:** Ready for Implementation