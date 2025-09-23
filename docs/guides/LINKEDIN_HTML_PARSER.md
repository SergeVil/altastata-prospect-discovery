# LinkedIn HTML Parser

Extract all contributors from LinkedIn advice posts and generate personalized outreach messages with AI-powered insight analysis.

## Overview

The LinkedIn HTML Parser (`linkedin_html_parser.py`) processes saved LinkedIn advice post HTML files to extract all contributors, analyze their comments using AI, and generate personalized connection and follow-up messages.

## Features

- **Comprehensive Extraction**: Extracts all contributors from saved LinkedIn advice post HTML
- **AI-Powered Insights**: Uses Gemini 2.5 Flash to analyze each contributor's comments and extract specific technical approaches
- **Smart Prioritization**: Ranks contributors by relevance (C-level, VPs, Directors, Founders first)
- **Deduplication**: Merges duplicate contributors and combines their comments
- **Activity Tracking**: Tracks how many times each contributor commented
- **Encryption Focus**: Highlights contributors who specifically mention encryption
- **Personalized Messages**: Generates connection messages (<300 chars) and detailed follow-up messages

## Usage

### Step 1: Save LinkedIn Advice Post as HTML

1. Navigate to the LinkedIn advice post in your browser
2. Save the page as HTML (Ctrl/Cmd + S)
3. Name it `linkedin_advice_post.html` and place in the project root

### Step 2: Run the Parser

```bash
python3 linkedin_html_parser.py
```

### Step 3: Review Results

Check `results/YYYY-MM-DD/` for:
- `linkedin_real_contributors_sorted_*.md` - Complete analysis with messages
- `linkedin_real_contributors_tracking_*.csv` - CSV file for tracking outreach

## Output Structure

### Markdown File
Each contributor includes:
- **Profile Information**: Name, title, LinkedIn URL
- **Engagement Metrics**: Likes, activity level, comment count
- **Priority Indicators**: HIGH PRIORITY, BUSINESS DEV flags
- **Complete Comments**: All their responses with clear separators
- **AI-Generated Insights**: Specific technical approaches they mentioned
- **Personalized Messages**: Connection message and follow-up message

### CSV Tracking File
Columns for tracking outreach:
- Name, Title, LinkedIn Profile
- Priority, Encryption Focus, Engagement
- Activity Level, Comment Count
- Connection Status, Follow-up Status, Notes

## AI Insight Analysis

The system uses Gemini 2.5 Flash to analyze each contributor's comments and extract:
- **Specific Technical Approaches**: Not generic terms but detailed methodologies
- **AWS Services**: Recognizes specific cloud services (KMS, IAM, CloudTrail, etc.)
- **Security Frameworks**: Identifies compliance and security standards
- **Implementation Details**: Captures how they actually implement solutions

### Example AI Insights

For a contributor mentioning AWS security:
```
• Implement Strict Access Controls and Least Privilege: Enforce least privilege access using IAM, MFA, and RBAC
• Encrypt and Protect Sensitive Data: Encrypt data with AWS KMS and classify/protect sensitive data with Amazon Macie  
• Automate Monitoring, Threat Detection, and Compliance: Monitor activity with CloudTrail, detect threats with GuardDuty
```

## Prioritization Algorithm

Contributors are ranked by:
1. **C-level Executives** (100 points): CEO, CTO, CFO, etc.
2. **Founders** (95 points): Founder, Co-founder
3. **VPs and Directors** (90 points): VP, Director, Head of
4. **Business Developers** (85 points): Partnership, Sales roles
5. **Senior Technical** (70 points): Senior, Lead, Principal
6. **Standard Technical** (50 points): Engineer, Developer, Analyst

Plus bonuses for:
- **Encryption mentions** (+20 points)
- **High activity** (+15 points for Very Active, +10 for Active)

## Requirements

- Python 3.8+
- Google Cloud authentication (for Gemini AI)
- Required packages: `langchain-google-vertexai`, `google-cloud-aiplatform`

## Tips

- **Save Complete HTML**: Ensure the HTML file includes all "View more answers" content
- **Check File Size**: HTML should be substantial (>500KB for full content)
- **Review High Priority**: Focus on contributors marked with 🔥 HIGH PRIORITY
- **Encryption Focus**: Pay special attention to contributors with 🔐 Encryption Focus
- **Activity Levels**: "Very Active" contributors are often more responsive

## Troubleshooting

**No contributors found**: Verify HTML file exists and contains "Contributor profile photo" text
**AI timeouts**: The system has built-in error handling and will continue processing
**Incomplete insights**: Check Google Cloud authentication for Gemini access

## Integration

This tool complements the main prospect discovery system (`main.py`) by providing:
- **Different Source**: LinkedIn advice posts vs. research papers
- **Higher Volume**: 100+ contributors vs. 7 prospects
- **Community Focus**: Discussion participants vs. paper authors
- **Engagement Data**: Comments and activity vs. publication metrics
