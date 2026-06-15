# watsonx.ai Quick Start

## What You're Doing

Deploy your trained PyTorch model to IBM Cloud → Get a REST API endpoint → Call it from anywhere.

**This is NOT for LLMs.** This is for YOUR custom classification model.

---

## 3 Steps

### **1. Get Your Files**

In Streamlit after training:
1. Click "Create Export Package"
2. Download ZIP
3. Extract → Find `model_checkpoint.pt`

---

### **2. Set Up watsonx.ai** (one-time, 5 min)

**Create account:**
- Go to https://cloud.ibm.com
- Sign up

**Create service:**
- Click "Catalog"
- Search "watsonx.ai"
- Select "watsonx.ai" (NOT foundation models)
- Click "Create"

**Create deployment space:**
- Click "Deployments" → "New deployment space"
- Name it (e.g., `my-models`)
- Click "Create"

---

### **3. Upload & Deploy** (5 min)

**Upload:**
- In your space: "Assets" → "Import assets" → "Model"
- Upload `model_checkpoint.pt`
- Name: `my-classifier`
- Type: PyTorch
- Click "Import"

**Deploy:**
- Find model → Click ⋮ → "Deploy"
- Choose "Online"
- Name: `my-api`
- Hardware: Small
- Click "Create"
- Wait 2 minutes

**Get credentials:**
- Click deployment → "API reference"
- Copy: Endpoint URL, API Key, Space ID

---

## Test It

### **Basic Inference:**
```python
import torch
from uq_classification.watsonx_scoring import WatsonxScoringClient

# Load test embeddings
eval_data = torch.load("eval_embeddings.pt")
embeddings = eval_data['embeddings'][:5]

# Create client
client = WatsonxScoringClient(
    api_key="your-api-key",
    scoring_url="your-endpoint-url",
    space_id="your-space-id"
)

# Score
predictions, confidences = client.score_batch(embeddings)
print(f"✅ Predictions: {predictions}")
```

### **Full Uncertainty Classification:**
```python
from uq_classification.watsonx_uncertainty import evaluate_watsonx_deployment

# Full evaluation with all 7 UQ signals
results = evaluate_watsonx_deployment(
    client=client,
    embeddings=eval_data['embeddings'],
    ground_truth=eval_data['clean_labels'],
    group_labels=eval_data['group_labels'],
    mc_passes=20
)

# Get all 7 signals (same as Streamlit!)
signals = results['signals']
print(f"✅ Epistemic: {signals['mutual_info'].mean():.3f}")
print(f"✅ Aleatoric: {signals['msp_uncertainty'].mean():.3f}")
print(f"✅ AUROC results: {results['auroc_results']}")
```

---

## Done!

Your model is now live with **full uncertainty classification**:
- ✅ Basic predictions
- ✅ All 7 UQ signals (epistemic, aleatoric, hybrid)
- ✅ AUROC evaluation
- ✅ Same results as Streamlit

**Docs:** https://ibm.com/docs/watsonx-as-a-service

---

Generated: 2026-05-15