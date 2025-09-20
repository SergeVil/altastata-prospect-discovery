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
                    paper = {
                        'title': item.get('title', ''),
                        'url': item.get('link', ''),
                        'snippet': item.get('snippet', ''),
                        'display_url': item.get('displayLink', ''),
                        'meta_info': item.get('pagemap', {}),
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
        """Search for business papers on AI security themes - let CSE find best sources"""
        # Simple query that focuses on the theme and encryption
        # Let the Custom Search Engine find the best sources naturally
        query = f"\"{theme}\" encryption"
        
        return self.search_papers(query, num_results=config.MAX_SEARCH_RESULTS)
    
    def search_linkedin_profiles(self, query: str) -> List[Dict[str, Any]]:
        """Search specifically for LinkedIn profiles - no modification to query"""
        return self.search_papers(query, num_results=config.MAX_SEARCH_RESULTS)
    
    def extract_company_domains(self, papers: List[Dict[str, Any]]) -> List[str]:
        """Extract unique company domains from paper sources"""
        domains = set()
        for paper in papers:
            display_url = paper.get('display_url', '')
            if display_url and '.' in display_url:
                # Extract domain, filtering out academic domains
                domain = display_url.lower()
                if not any(academic in domain for academic in ['.edu', 'arxiv', 'researchgate', 'scholar.google']):
                    domains.add(domain)
        return list(domains)
    
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
    
