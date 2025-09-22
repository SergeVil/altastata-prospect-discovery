# AltaStata Prospect Discovery System

AI-powered prospect discovery system that finds high-quality LinkedIn prospects from AI security papers and generates personalized outreach messages.

## 🚀 Quick Start

1. **Setup Google Cloud credentials** (see `docs/guides/setup_guide.md`)
2. **Run the system**: `python main.py`
3. **Get your prospects**: Check `results/YYYY-MM-DD/good_prospects_with_messages_*.md`

## 📁 Essential Files

### Core System
- **`main.py`** - Main entry point, run this to start prospect discovery
- **`workflow.py`** - LangGraph workflow orchestration
- **`config.py`** - Configuration settings (Google Cloud, API keys, themes)
- **`author_extractor.py`** - AI-powered author extraction and LinkedIn discovery

### AI Agents
- **`agents/search_agent.py`** - Google Custom Search API integration
- **`agents/analysis_agent.py`** - Paper content analysis

### Documentation
- **`docs/guides/HOW_TO_RUN.md`** - Complete setup and run instructions
- **`docs/guides/setup_guide.md`** - Quick setup guide
- **`docs/operations/linkedin_outreach_targets.md`** - LinkedIn outreach best practices
- **`docs/reference/premium_sources_list.txt`** - Target publication sources

### Utilities
- **`scripts/manage_results.py`** - Clean up old result files
- **`requirements.txt`** - Python dependencies

## 📊 Output Files

Results are saved in `results/YYYY-MM-DD/`:
- **`good_prospects_with_messages_*.md`** - Main LinkedIn outreach file (ready to use)
- **`prospects_*.csv`** - Same data in spreadsheet format
- **`ai_security_analysis_*.json`** - Complete system analysis
- **`other_prospects_ready_*.md`** - Additional prospects for manual research

## 🎯 Typical Results

- **30 papers** analyzed per run
- **7 high-quality prospects** with LinkedIn profiles found
- **Personalized messages** generated for each prospect
- **LinkedIn advice posts** flagged for manual review
- **Processing time**: ~3 minutes

## ✨ Recent Improvements

### **Quality Enhancements:**
- **Fake name filtering** - Automatically removes "John Doe", "Jane Smith", etc.
- **LinkedIn profile validation** - Ensures profile usernames match author names
- **Special advice post handling** - LinkedIn advice posts flagged for manual review
- **Inaccessible article handling** - Gracefully skips 403/404 errors
- **Co-author references** - Shows relationships between prospects from same paper

### **Code Quality:**
- **15% code reduction** - Removed 12 unused functions
- **Cleaner architecture** - Deleted entire unused email_agent.py
- **Better error handling** - More robust extraction process
- **Improved maintainability** - Streamlined codebase

## 🔧 Configuration

Key settings in `config.py`:
- Google Cloud project ID
- API keys and credentials
- AI security themes (9 themes)
- Search parameters

## 📞 Support

For setup issues, see `docs/guides/setup_guide.md`
For detailed instructions, see `docs/guides/HOW_TO_RUN.md`