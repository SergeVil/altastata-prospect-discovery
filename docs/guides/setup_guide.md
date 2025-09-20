# 🚀 Quick Setup Guide

## Step-by-Step Configuration

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Google Cloud Setup

#### Create Project (if needed)
```bash
gcloud projects create altastata-ai-agent-project
gcloud config set project altastata-ai-agent-project
```

#### Authenticate (Required First Time)
```bash
gcloud auth login
gcloud config set project altastata-social-media-agent
```

#### Enable APIs
```bash
gcloud services enable customsearch.googleapis.com
gcloud services enable aiplatform.googleapis.com
```

#### Create Service Account
```bash
gcloud iam service-accounts create altastata-agent \
  --description="AltaStata AI Agent Service Account" \
  --display-name="AltaStata Agent"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:altastata-agent@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

gcloud iam service-accounts keys create credentials.json \
  --iam-account=altastata-agent@PROJECT_ID.iam.gserviceaccount.com
```

### 3. Custom Search Engine

1. Go to https://cse.google.com/
2. Click "Add" to create new search engine
3. In "Sites to search", add: `*.com` (or specific business domains)
4. Name it "AltaStata Prospect Discovery"
5. Click "Create"
6. Go to "Setup" → "Basics" and copy your **Search Engine ID**
7. Go to "Setup" → "Advanced" → enable "Image search" and "Safe search"

### 4. Get Google API Key

1. Go to https://console.cloud.google.com/apis/credentials
2. Click "Create Credentials" → "API Key"
3. Copy the API key
4. Restrict the key to "Custom Search API"

### 5. Environment Configuration

Create `.env` file:

```env
# Replace with your actual values
GOOGLE_APPLICATION_CREDENTIALS=./credentials.json
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CSE_ID=your-search-engine-id
GOOGLE_API_KEY=your-api-key
VERTEX_AI_LOCATION=us-central1
```

### 6. Test Configuration

```bash
python example_usage.py
```

### 7. Run the Application

```bash
# Command line
python main.py

# Web interface
streamlit run streamlit_app.py
```

## 💡 Pro Tips

### Cost Optimization
- Custom Search API: 100 free queries/day, then $5/1000 queries
- Vertex AI: Pay-per-use, typically $0.002-0.02 per request
- Set `PAPERS_PER_BATCH = 3` for testing

### Search Optimization
- Add specific company domains to your Custom Search Engine
- Use site-specific searches: `site:microsoft.com AI security`
- Focus on PDF file types for academic/business papers

### Business Targeting
- Target company blogs, whitepapers, and technical documentation
- Look for authors with corporate email addresses
- Focus on recent publications (last 2-3 years)

## 🔧 Troubleshooting

### Common Issues

**"No papers found"**
- Check Custom Search Engine configuration
- Verify API key permissions
- Try broader search terms

**"Vertex AI authentication error"**
- Verify service account key file path
- Check IAM permissions
- Ensure project ID is correct
- Run: `gcloud auth login` and `gcloud config set project altastata-social-media-agent`

**"Vertex AI API has not been used in project altastata-coco"**
- Wrong project configured in gcloud
- Run: `gcloud config set project altastata-social-media-agent`

**"Rate limit exceeded"**
- Reduce `PAPERS_PER_BATCH` in config.py
- Add delays between requests
- Check API quotas in Google Cloud Console

### Debug Mode

Set debug flags in `config.py`:

```python
DEBUG_MODE = True
VERBOSE_LOGGING = True
```

## 📊 Expected Results

With proper configuration, you should see:
- 10-20 papers found per theme
- 3-5 high-quality papers analyzed
- 2-4 personalized emails generated
- Processing time: 2-5 minutes for full workflow

## 🎯 Next Steps

1. Review generated emails for quality
2. Customize email templates in `email_agent.py`
3. Add specific company domains to target
4. Set up automated scheduling for regular runs
5. Build contact database integration
