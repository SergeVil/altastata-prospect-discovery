#!/usr/bin/env python3

import os

# Google Cloud configuration
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "./credentials.json")
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "altastata-social-media-agent")

# Custom Search API
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID", "b5a45e4ce99ac4243")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "YOUR_GOOGLE_API_KEY_HERE")

# Vertex AI configuration
VERTEX_AI_LOCATION = os.getenv("VERTEX_AI_LOCATION", "us-central1")

# Search configuration
MAX_SEARCH_RESULTS = 10
NUM_PARALLEL_WORKERS = 6

# AI Security themes for prospect discovery
SECURITY_THEMES = [
    "AI External Partners Trust",
    "AI Data Integrity", 
    "Efficient AI Security",
    "AI Supply Chain Security",
    "AI Model Governance",
    "AI Privacy Compliance",
    "AI Third Party Risk",
    "AI Vendor Security",
    "AI Data Lineage"
]

# AltaStata company information
ALTASTATA_URL = "https://altastata.com"
ALTASTATA_COMPANY_NAME = "AltaStata"
ALTASTATA_TAGLINE = "Data Security for AI"

# Output configuration
OUTPUT_DIR = "results"
CSV_FILENAME = "prospects.csv"
JSON_FILENAME = "ai_security_analysis.json"