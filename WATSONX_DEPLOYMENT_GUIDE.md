# watsonx.ai Deployment Guide for UQ Classification

## 🎯 What is watsonx.ai?

**watsonx.ai** is IBM's enterprise AI platform for deploying and managing machine learning models. It's **NOT** the LLM/generative AI part (that's watsonx.ai foundation models). For your UQ classification model, you'll use:

- **watsonx.ai Model Deployment** - Deploy your PyTorch model as a REST API
- **watsonx.governance** - Track metrics, monitor drift, ensure compliance

Think of it as: **MLflow + Model Serving + Governance** all in one IBM Cloud service.

## 🚫 What You DON'T Need

- ❌ **Cloud Pak for Data** - Old on-premise platform (being phased out)
- ❌ **watsonx.ai Foundation Models** - LLM stuff (Llama, Granite, etc.)
- ❌ **Watson Studio** - Jupyter notebooks environment (optional, not required)
- ❌ **Watson Machine Learning (WML)** - Legacy service (replaced by watsonx.ai)

## ✅ What You DO Need

1. **IBM Cloud Account** - Free tier available
2. **watsonx.ai Service** - Model deployment platform
3. **watsonx.governance** - Metrics tracking (optional but recommended)
4. **Your Export Package** - Generated from Streamlit (9 files in ZIP)

---

## 📋 Step-by-Step Deployment

### **Step 1: Set Up IBM Cloud Account**

1. Go to https://cloud.ibm.com
2. Sign up for free account (no credit card for trial)
3. Verify email and log in

**Cost:** Free tier includes:
- 20 capacity unit hours/month for model deployment
- Enough for testing and small-scale production

---

### **Step 2: Create watsonx.ai Service**

1. In IBM Cloud dashboard, click **"Create resource"**
2. Search for **"watsonx.ai"**
3. Select **"watsonx.ai"** (NOT "watsonx.ai foundation models")
4. Choose:
   - **Plan:** Lite (free) or Standard
   - **Region:** Dallas, Frankfurt, or Tokyo
   - **Resource group:** Default
5. Click **"Create"**
6. Wait 2-3 minutes for provisioning

**What you get:**
- Model deployment environment
- REST API endpoints
- Monitoring dashboard
- 20 CUH/month free

---

### **Step 3: Create Deployment Space**

A "deployment space" is where your models live. Think of it as a project folder.

1. In watsonx.ai dashboard, click **"Deployments"** in left menu
2. Click **"New deployment space"**
3. Fill in:
   - **Name:** `uq-classification-prod`
   - **Description:** `Uncertainty quantification for CIFAR-10N`
   - **Machine learning service:** Select your watsonx.ai instance
   - **Storage service:** Create new Cloud Object Storage (free tier)
4. Click **"Create"**

**What you get:**
- Isolated environment for your models
- Separate spaces for dev/staging/prod
- Access control and versioning

---

### **Step 4: Upload Your Model**

Now you'll upload the files from your Streamlit export package.

#### 4.1 Extract Your ZIP File
```bash
unzip watsonx_export_20260515_142030.zip
cd watsonx_export_20260515_142030/
```

You should see:
```
model_checkpoint.pt
model_config.json
train_embeddings.pt
eval_embeddings.pt
per_sample_signals.csv
evaluation_metadata.csv
auroc_results.csv
experiment_config.yaml
README.txt
```

#### 4.2 Upload Model to watsonx.ai

1. In your deployment space, click **"Assets"** tab
2. Click **"Import assets"**
3. Select **"Model"**
4. Choose **"From file"**
5. Upload **`model_checkpoint.pt`**
6. Fill in metadata:
   - **Name:** `uq-classifier-v1`
   - **Description:** `Uncertainty quantification classifier with MC Dropout`
   - **Model type:** PyTorch
   - **Framework version:** 2.0+
   - **Input schema:** See below
   - **Output schema:** See below

**Input Schema (JSON):**
```json
{
  "type": "array",
  "items": {
    "type": "array",
    "items": {
      "type": "number"
    },
    "minItems": 768,
    "maxItems": 768
  }
}
```

**Output Schema (JSON):**
```json
{
  "type": "array",
  "items": {
    "type": "array",
    "items": {
      "type": "number"
    },
    "minItems": 10,
    "maxItems": 10
  }
}
```

7. Click **"Import"**

---

### **Step 5: Create Deployment**

Now make your model accessible via REST API.

1. In **"Assets"** tab, find your model `uq-classifier-v1`
2. Click the **⋮** menu → **"Deploy"**
3. Choose **"Online"** deployment (real-time API)
4. Fill in:
   - **Name:** `uq-classifier-prod`
   - **Description:** `Production endpoint for UQ classification`
   - **Hardware:** Small (1 vCPU, 4GB RAM) - enough for your model
5. Click **"Create"**
6. Wait 2-3 minutes for deployment

**What you get:**
- REST API endpoint URL
- API key for authentication
- Swagger documentation
- Monitoring dashboard

---

### **Step 6: Test Your Deployment**

#### 6.1 Get API Credentials

1. In deployment details, click **"API reference"** tab
2. Copy:
   - **Endpoint URL:** `https://us-south.ml.cloud.ibm.com/ml/v4/deployments/{deployment_id}/predictions`
   - **API Key:** Your IBM Cloud API key
   - **Space ID:** Your deployment space ID

#### 6.2 Test with eval_embeddings.pt

**Basic Inference:**
```python
import torch
from uq_classification.watsonx_scoring import WatsonxScoringClient

# Load evaluation embeddings
eval_data = torch.load("eval_embeddings.pt")
embeddings = eval_data['embeddings'][:10]

# Create client
client = WatsonxScoringClient(
    api_key="YOUR_IBM_CLOUD_API_KEY",
    scoring_url="YOUR_ENDPOINT_URL",
    space_id="YOUR_SPACE_ID"
)

# Score batch
response = client.score_batch(embeddings, batch_size=10)
predictions, confidences = client.parse_scoring_response(response)

print(f"Predictions: {predictions}")
print(f"Confidences: {confidences}")
```

**Full Uncertainty Classification (All 7 Signals):**
```python
from uq_classification.watsonx_uncertainty import evaluate_watsonx_deployment

# Complete evaluation pipeline
results = evaluate_watsonx_deployment(
    client=client,
    embeddings=eval_data['embeddings'],
    ground_truth=eval_data['clean_labels'],
    group_labels=eval_data['group_labels'],
    mc_passes=20,
    batch_size=32
)

# Access all signals
signals = results['signals']
print(f"Epistemic signals:")
print(f"  - Mutual info: {signals['mutual_info'].mean():.3f}")
print(f"  - Inverse coherence: {signals['inverse_coherence'].mean():.3f}")
print(f"  - Dominance: {signals['dominance'].mean():.3f}")

print(f"\nAleatoric signals:")
print(f"  - MSP uncertainty: {signals['msp_uncertainty'].mean():.3f}")
print(f"  - Predictive entropy: {signals['predictive_entropy'].mean():.3f}")

print(f"\nHybrid signals:")
print(f"  - Inverse mass: {signals['inverse_mass'].mean():.3f}")
print(f"  - Inverse logit magnitude: {signals['inverse_logit_magnitude'].mean():.3f}")

# AUROC results
print(f"\nAUROC Results:")
for signal_name, alea_auc, epis_auc in results['auroc_results']:
    print(f"  {signal_name}: Aleatoric={alea_auc:.3f}, Epistemic={epis_auc:.3f}")

# Accuracy metrics
print(f"\nAccuracy: {results['accuracy']:.2%}")
print(f"Group accuracies: {results['group_accuracies']}")
```

#### 6.3 Test with curl

```bash
curl -X POST \
  "YOUR_ENDPOINT_URL" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -H "ML-Instance-ID: YOUR_SPACE_ID" \
  -d '{
    "input_data": [{
      "fields": ["embedding"],
      "values": [[0.123, 0.456, ..., 0.789]]
    }]
  }'
```

**Expected response:**
```json
{
  "predictions": [{
    "fields": ["probabilities"],
    "values": [[0.05, 0.02, 0.78, 0.01, 0.03, 0.04, 0.02, 0.01, 0.02, 0.02]]
  }]
}
```

---

### **Step 7: Set Up Monitoring (Optional)**

Track model performance over time.

1. In deployment details, click **"Monitor"** tab
2. Enable **"Quality monitoring"**
3. Upload **`evaluation_metadata.csv`** as reference data
4. Set thresholds from **`auroc_results.csv`**:
   - Accuracy drop > 5%
   - Confidence drop > 10%
   - Prediction drift > 15%
5. Configure alerts (email/Slack)

**What you get:**
- Automatic drift detection
- Performance degradation alerts
- Fairness metrics
- Explainability reports

---

### **Step 8: Set Up watsonx.governance (Optional)**

For enterprise compliance and audit trails.

1. In IBM Cloud, create **"watsonx.governance"** service
2. In watsonx.governance dashboard:
   - Click **"Model inventory"**
   - Click **"Add model"**
   - Link to your watsonx.ai deployment
3. Configure:
   - **Model facts:** Upload `model_config.json`
   - **Training data:** Upload `train_embeddings.pt` metadata
   - **Evaluation results:** Upload `auroc_results.csv`
   - **Use case:** Classification with uncertainty
4. Set up **"Model risk assessment"**:
   - Risk level: Medium (not high-stakes decision)
   - Compliance: GDPR, AI Act (if applicable)
   - Review frequency: Monthly

**What you get:**
- Model lineage tracking
- Compliance documentation
- Risk assessment reports
- Audit trail for all predictions

---

## � Production Workflow

### **For New Predictions:**

```python
# 1. Extract DINOv2 embeddings from new images
from torchvision import transforms
import torch

# Load DINOv2 model
dinov2 = torch.hub.load('facebookresearch/dinov2', 'dinov2_vitb14')
dinov2.eval()

# Preprocess image
transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

image_tensor = transform(image).unsqueeze(0)

# Extract embedding
with torch.no_grad():
    embedding = dinov2(image_tensor)  # [1, 768]

# 2. Send to watsonx.ai
client = WatsonxScoringClient(...)
predictions, confidences = client.score_batch(embedding)

# 3. Get uncertainty (if MC Dropout enabled)
predictions, confidences, uncertainties = client.score_with_uncertainty(
    embedding, 
    mc_passes=20
)

print(f"Predicted class: {predictions[0]}")
print(f"Confidence: {confidences[0]:.2f}")
print(f"Epistemic uncertainty: {uncertainties['mutual_info'][0]:.3f}")
print(f"Aleatoric uncertainty: {uncertainties['msp_uncertainty'][0]:.3f}")
```

### **For Batch Processing:**

```python
# Process 1000 images
embeddings = extract_embeddings_batch(images)  # [1000, 768]

# Score in batches of 32
predictions, confidences, uncertainties = client.score_with_uncertainty(
    embeddings,
    mc_passes=20,
    batch_size=32
)

# Log to governance
from uq_classification.watsonx_scoring import WatsonxGovernanceLogger

logger = WatsonxGovernanceLogger(
    api_key="YOUR_API_KEY",
    governance_url="https://api.dataplatform.cloud.ibm.com/v2/governance",
    model_id="uq-classifier-v1"
)

logger.log_predictions(
    predictions=predictions,
    ground_truth=labels,  # if available
    uncertainties=uncertainties,
    metadata={"batch_id": "20260515_001", "source": "production"}
)
```

---

## 💰 Cost Estimation

### **Free Tier (Lite Plan):**
- 20 capacity unit hours (CUH) per month
- 1 CUH = 1 hour of 1 vCPU + 4GB RAM
- **Enough for:** ~600 predictions/day (assuming 2 seconds per prediction)

### **Standard Plan:**
- $0.50 per CUH
- **Example:** 10,000 predictions/day
  - ~5.5 hours/day × 30 days = 165 CUH/month
  - Cost: 165 × $0.50 = **$82.50/month**

### **Storage (Cloud Object Storage):**
- Free tier: 25GB
- Your model + embeddings: ~15 MB
- **Cost:** $0 (well within free tier)

---

## 🆘 Troubleshooting

### **"Model deployment failed"**
- Check PyTorch version compatibility (2.0+)
- Ensure model file < 5GB
- Verify input/output schemas match

### **"Authentication failed"**
- Regenerate API key in IBM Cloud
- Check Space ID is correct
- Ensure API key has deployment space access

### **"Predictions are slow"**
- Increase hardware tier (Medium: 2 vCPU, 8GB RAM)
- Enable batch processing (batch_size=32)
- Consider caching embeddings

### **"Monitoring shows drift"**
- Retrain model with new data
- Update reference dataset
- Adjust thresholds if false alarms

---

## 📚 Key Differences from Other Platforms

| Feature | watsonx.ai | AWS SageMaker | Azure ML | Google Vertex AI |
|---------|-----------|---------------|----------|------------------|
| **Governance** | ✅ Built-in | ❌ Separate service | ⚠️ Limited | ⚠️ Limited |
| **Compliance** | ✅ GDPR, AI Act ready | ⚠️ Manual | ⚠️ Manual | ⚠️ Manual |
| **Free Tier** | ✅ 20 CUH/month | ⚠️ 12 months only | ⚠️ Limited | ⚠️ Limited |
| **PyTorch Support** | ✅ Native | ✅ Native | ✅ Native | ✅ Native |
| **Monitoring** | ✅ Automatic | ⚠️ Manual setup | ⚠️ Manual setup | ⚠️ Manual setup |

---

## 🎓 Summary

**What you're doing:**
1. ✅ Train model in Streamlit (local)
2. ✅ Export package with embeddings + CSVs
3. ✅ Upload to watsonx.ai (IBM Cloud)
4. ✅ Deploy as REST API
5. ✅ Monitor with watsonx.governance

**What you're NOT doing:**
- ❌ Using LLMs or foundation models
- ❌ Installing Cloud Pak for Data
- ❌ Using Watson Studio notebooks
- ❌ Dealing with on-premise infrastructure

**Next steps:**
1. Create IBM Cloud account
2. Set up watsonx.ai service
3. Follow Steps 1-8 above
4. Test with your export package

**Questions?**
- IBM Cloud docs: https://cloud.ibm.com/docs/watsonxai
- watsonx.ai tutorials: https://www.ibm.com/docs/en/watsonx-as-a-service
- Support: https://cloud.ibm.com/unifiedsupport/supportcenter

---

**Generated:** 2026-05-15  
**Version:** 1.0  
**For:** UQ Classification Model Deployment