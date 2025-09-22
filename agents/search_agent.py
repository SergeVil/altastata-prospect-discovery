"""
Search Agent for finding business-oriented AI security papers
"""
from typing import List, Dict, Any
from googleapiclient.discovery import build
from langchain_google_vertexai import VertexAI
import config
from author_extractor import AuthorExtractor

class SearchAgent:
    def __init__(self):
        self.llm = VertexAI(
            model_name="gemini-2.5-flash",
            project=config.GOOGLE_CLOUD_PROJECT,
            location=config.VERTEX_AI_LOCATION,
            temperature=0.1
        )
        self.search_service = build(
            "customsearch", "v1", 
            developerKey=config.GOOGLE_API_KEY
        )
        self.author_extractor = AuthorExtractor()
    
    def _clean_paper_title(self, title: str) -> str:
        """Clean paper title by removing publication suffixes using intelligent pattern matching."""
        if not title:
            return title
        
        import re
        
        # Pattern-based approach to remove publication suffixes
        # This handles various separators and publication name patterns
        patterns = [
            # Pattern 1: " | [Publication Name]" - most common
            r'\s*\|\s*[A-Z][A-Za-z\s&\.]+$',
            
            # Pattern 2: " - [Publication Name]" 
            r'\s*-\s*[A-Z][A-Za-z\s&\.]+$',
            
            # Pattern 3: " :: [Publication Name]"
            r'\s*::\s*[A-Z][A-Za-z\s&\.]+$',
            
            # Pattern 4: " ([Publication Name])" - sometimes titles end with publication in parentheses
            r'\s*\([A-Z][A-Za-z\s&\.]+\)$'
        ]
        
        cleaned_title = title.strip()
        
        for pattern in patterns:
            match = re.search(pattern, cleaned_title)
            if match:
                # Extract the potential publication name
                suffix = match.group().strip()
                potential_pub = re.sub(r'^[\|\-::\(\)]\s*', '', suffix).strip('()')
                
                # Only remove if it looks like a publication name (not part of the actual title)
                # Publications are usually short (1-6 words) and often contain certain keywords
                words = potential_pub.split()
                
                # Check if it's a known publication (even if longer)
                is_known_publication = any(known_pub in potential_pub for known_pub in [
                    'IBM', 'CIO', 'Forbes', 'Reuters', 'Bloomberg', 'Wired', 'LinkedIn', 'Medium', 
                    'Nature', 'Science', 'IEEE', 'ACM', 'McKinsey', 'Deloitte', 'PwC', 
                    'Gartner', 'Forrester', 'IDC', 'Harvard Business Review', 'MIT Technology Review'
                ])
                
                # Check if it contains publication keywords
                has_pub_keywords = any(keyword in potential_pub.lower() for keyword in [
                    'magazine', 'review', 'journal', 'news', 'times', 'post', 'blog',
                    'research', 'institute', 'university', 'press', 'media', 'network',
                    'today', 'weekly', 'daily', 'online', 'digital', 'tech', 'business'
                ])
                
                # Check publication patterns
                has_pub_patterns = (potential_pub.isupper() or '&' in potential_pub)
                
                if (len(words) <= 6 and 
                    (is_known_publication or has_pub_keywords or has_pub_patterns)):
                    
                    cleaned_title = cleaned_title[:match.start()].strip()
                    break
        
        return cleaned_title
    
    def _extract_useful_metadata(self, pagemap: dict) -> dict:
        """Extract only useful metadata fields, ignoring bloat"""
        useful_metadata = {}
        
        # Get metatags if they exist
        metatags = pagemap.get('metatags', [])
        if metatags and isinstance(metatags, list) and len(metatags) > 0:
            meta = metatags[0]  # Usually first element contains the main metadata
            
            # Extract useful fields only
            if 'author' in meta:
                useful_metadata['author'] = meta['author']
            
            if 'article:author' in meta:
                useful_metadata['author_url'] = meta['article:author']
                
            if 'article:published_time' in meta:
                useful_metadata['published_date'] = meta['article:published_time']
            elif 'dcterms.date' in meta:
                useful_metadata['published_date'] = meta['dcterms.date']
                
            if 'og:description' in meta:
                useful_metadata['description'] = meta['og:description']
            elif 'twitter:description' in meta:
                useful_metadata['description'] = meta['twitter:description']
                
            if 'twitter:data1' in meta and 'read' in meta['twitter:data1'].lower():
                useful_metadata['reading_time'] = meta['twitter:data1']
                
            # Extract organization/site name for context
            if 'og:site_name' in meta:
                useful_metadata['site_name'] = meta['og:site_name']
        
        return useful_metadata
    
    def _clean_title_with_author_context(self, title: str, author_info: dict) -> str:
        """Clean title considering author's company - remove company name if it matches publication"""
        if not title or not author_info:
            return title
        
        author_company = author_info.get('company', '').strip()
        if not author_company or author_company.lower() in ['not specified', 'unknown', '']:
            return title
        
        import re
        
        # Pattern to match company name at the end of title with separators
        patterns = [
            rf'\s*\|\s*{re.escape(author_company)}\s*$',
            rf'\s*-\s*{re.escape(author_company)}\s*$', 
            rf'\s*::\s*{re.escape(author_company)}\s*$',
            rf'\s*\({re.escape(author_company)}\)\s*$'
        ]
        
        cleaned_title = title
        for pattern in patterns:
            if re.search(pattern, cleaned_title, re.IGNORECASE):
                cleaned_title = re.sub(pattern, '', cleaned_title, flags=re.IGNORECASE).strip()
                break
        
        return cleaned_title
    
    def search_papers(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """Search for papers using Google Custom Search"""
        try:
            result = self.search_service.cse().list(
                q=query,
                cx=config.GOOGLE_CSE_ID,
                num=num_results
            ).execute()
            
            papers = []
            if 'items' in result:
                for item in result['items']:
                    raw_title = item.get('title', '')
                    cleaned_title = self._clean_paper_title(raw_title)
                    # Extract only useful metadata
                    useful_metadata = self._extract_useful_metadata(item.get('pagemap', {}))
                    
                    paper = {
                        'title': cleaned_title,
                        'url': item.get('link', ''),
                        'snippet': item.get('snippet', ''),
                        'display_url': item.get('displayLink', ''),
                        'metadata': useful_metadata,
                        'author_info': {}  # Will be populated later during analysis
                    }
                    papers.append(paper)
            
            return papers
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def search_company_papers(self, company_domain: str, security_theme: str) -> List[Dict[str, Any]]:
        """Search for papers from specific company domain about security themes"""
        query = f"site:{company_domain} \"{security_theme}\" AI security data privacy"
        return self.search_papers(query, num_results=5)
    
    def search_general_security_papers(self, theme: str) -> List[Dict[str, Any]]:
        """Search for business papers on AI security themes - MUST contain encryption"""
        # Search ONLY for pages that contain "encryption" - more restrictive
        # This ensures we get encryption-focused content relevant to AltaStata
        query = f"encryption \"{theme}\" AI"
        
        return self.search_papers(query, num_results=config.MAX_SEARCH_RESULTS)
    
    def search_linkedin_profiles(self, query: str) -> List[Dict[str, Any]]:
        """Search specifically for LinkedIn profiles - no modification to query"""
        return self.search_papers(query, num_results=config.MAX_SEARCH_RESULTS)
    
    
    def rank_papers_by_business_relevance(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank papers by business relevance using LLM"""
        if not papers:
            return []
        
        
        try:
            # Parse the ranking response and reorder papers
            # For now, return papers as-is with business keyword scoring
            return self._score_business_relevance(papers)
        except Exception as e:
            print(f"Ranking error: {e}")
            return self._score_business_relevance(papers)
    
    def _score_business_relevance(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Simple scoring based on business keywords"""
        for paper in papers:
            score = 0
            text = f"{paper['title']} {paper['snippet']}".lower()
            
            for keyword in config.BUSINESS_KEYWORDS:
                if keyword in text:
                    score += 1
            
            for theme in config.SECURITY_THEMES:
                if theme.lower() in text:
                    score += 2
            
            paper['business_score'] = score
        
        return sorted(papers, key=lambda x: x.get('business_score', 0), reverse=True)
    
