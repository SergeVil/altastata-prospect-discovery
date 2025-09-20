# 🚀 AltaStata Prospect Discovery - Complete User Guide

## 📋 **Quick Start Summary**

The AltaStata Prospect Discovery system finds high-quality AI security business content from premium sources (Gartner, LinkedIn, Forbes, Deloitte, etc.) and generates research-focused LinkedIn messages for prospect outreach.

**🎯 End Result:** LinkedIn-ready messages targeting executives who write about AI security challenges.

---

## ⚡ **Quick Commands**

```bash
# Test the system configuration
python test_search.py

# Run full prospect discovery
python main.py

# Run web interface
streamlit run streamlit_app.py

# Validate premium sources
python validate_sources.py
```

---

## 🔧 **Prerequisites & Setup**

### **1. Required Accounts & APIs**
- ✅ **Google Cloud Project** with Vertex AI enabled
- ✅ **Google Custom Search Engine** configured
- ✅ **Service Account** with Vertex AI permissions

### **2. Required Files**
- ✅ `credentials.json` - Google Cloud service account key
- ✅ All Python dependencies installed (`pip install -r requirements.txt`)

### **3. Google Cloud Authentication**
```bash
# Authenticate with Google Cloud (required first time)
gcloud auth login

# Set the correct project (required)
gcloud config set project altastata-social-media-agent

# Verify project is set correctly
gcloud config get-value project
```

### **4. Environment Variables (Optional)**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="./credentials.json"
export GOOGLE_CLOUD_PROJECT="altastata-social-media-agent"
export GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY_HERE"
export GOOGLE_CSE_ID="b5a45e4ce99ac4243"
```

---

## 🚀 **Running the System**

### **Step 1: Install Dependencies**
```bash
pip install -r requirements.txt
```

### **Step 2: Configure Google Cloud**
1. **Create Service Account:**
   - Go to Google Cloud Console
   - Navigate to IAM & Admin > Service Accounts
   - Create new service account with Vertex AI User role
   - Download JSON key file as `credentials.json`

2. **Enable APIs:**
   - Vertex AI API
   - Custom Search API

3. **Set up Custom Search Engine:**
   - Go to [Google Custom Search](https://cse.google.com/)
   - Create new search engine
   - Add sites to search (see `docs/reference/premium_sources_list.txt`)
   - Get your Custom Search Engine ID

### **Step 3: Run the System**
```bash
python main.py
```

---

## 📊 **Expected Results**

### **Typical Output:**
- **30 papers** analyzed across AI security themes
- **8-10 prospects** with LinkedIn profiles found
- **Processing time:** ~3 minutes
- **Personalized messages** for each prospect

### **Output Files:**
```
results/YYYY-MM-DD/
├── good_prospects_with_messages_*.md    # Main LinkedIn outreach file
├── prospects_*.csv                      # Spreadsheet format
├── ai_security_analysis_*.json          # Complete analysis
└── other_prospects_ready_*.md           # Additional prospects
```

---

## 🔍 **System Architecture**

### **Core Components:**
- **Search Agent** - Google Custom Search API integration
- **Analysis Agent** - Paper content analysis with Vertex AI
- **Author Extractor** - AI-powered LinkedIn profile discovery
- **Email Agent** - Personalized message generation
- **Workflow Orchestrator** - LangGraph-based coordination

### **AI Security Themes:**
1. AI External Partners Trust
2. AI Data Integrity
3. Efficient AI Security
4. AI Supply Chain Security
5. AI Model Governance
6. AI Privacy Compliance
7. AI Third Party Risk
8. AI Vendor Security
9. AI Data Lineage

---

## 🛠️ **Troubleshooting**

### **Common Issues:**

#### **1. Authentication Failed**
```bash
# Re-authenticate with Google Cloud
gcloud auth login
gcloud auth application-default login
```

#### **2. Vertex AI API Error**
```bash
# Verify project is set correctly
gcloud config set project altastata-social-media-agent
gcloud config get-value project
```

#### **3. Import Errors**
```bash
# Install missing dependencies
pip install -r requirements.txt
```

#### **4. No Prospects Found**
- Check Google Custom Search Engine configuration
- Verify premium sources are included in CSE
- Check API quotas and limits

---

## 📈 **Performance Optimization**

### **Search Optimization:**
- **10 results per theme** (90 total searches)
- **Premium source targeting** (business publications)
- **Parallel processing** (6 workers)

### **Quality Filters:**
- **Individual author validation** (no organizations)
- **LinkedIn profile requirement**
- **Business relevance scoring**

---

## 🔒 **Security Best Practices**

### **Credentials Management:**
- ✅ Never commit `credentials.json` to git
- ✅ Use environment variables for API keys
- ✅ Rotate keys regularly
- ✅ Use least-privilege service accounts

### **API Security:**
- ✅ Enable API key restrictions
- ✅ Monitor usage and billing
- ✅ Set up abuse alerts

---

## 📞 **Support & Resources**

### **Documentation:**
- `README.md` - Project overview
- `docs/guides/setup_guide.md` - Quick setup
- `docs/operations/linkedin_outreach_targets.md` - Outreach best practices

### **Configuration:**
- `config.py` - All system settings
- `requirements.txt` - Python dependencies
- `.gitignore` - Git exclusions

### **Utilities:**
- `scripts/manage_results.py` - Clean up old results
- `scripts/verify_setup.py` - Validate configuration

---

## 🎯 **Success Metrics**

### **Typical Performance:**
- **Prospect Discovery Rate:** 8-10 prospects per run
- **Processing Time:** 2-3 minutes
- **LinkedIn Profile Success:** 95%+
- **Message Personalization:** 100%

### **Quality Indicators:**
- ✅ Individual authors (no organizations)
- ✅ LinkedIn profiles found
- ✅ Paper-specific insights extracted
- ✅ Professional message tone

---

## 🚀 **Advanced Usage**

### **Custom Configuration:**
1. **Modify Security Themes** in `config.py`
2. **Adjust Search Parameters** (results per theme)
3. **Customize Message Templates** in workflow
4. **Add Premium Sources** to Custom Search Engine

### **Integration Options:**
- **Web Interface** via Streamlit
- **API Integration** for automated workflows
- **Scheduled Runs** via cron jobs
- **Batch Processing** for multiple campaigns

---

**🎉 Ready to discover high-quality AI security prospects!**
