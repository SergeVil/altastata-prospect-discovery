"""
Analysis Agent for extracting insights from papers and websites
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from langchain_google_vertexai import VertexAI
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import config

class AnalysisAgent:
    def __init__(self):
        # Explicitly set the project to override gcloud defaults
        import os
        os.environ["GOOGLE_CLOUD_PROJECT"] = config.GOOGLE_CLOUD_PROJECT
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config.GOOGLE_APPLICATION_CREDENTIALS
        
        self.llm = VertexAI(
            model_name="gemini-2.5-flash",
            project=config.GOOGLE_CLOUD_PROJECT,
            location=config.VERTEX_AI_LOCATION,
            temperature=0.2
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=4000,
            chunk_overlap=200
        )
    
    def extract_paper_content(self, paper_url: str) -> Optional[str]:
        """Extract text content from paper URL"""
        try:
            response = requests.get(paper_url, timeout=30)
            response.raise_for_status()
            
            # For PDFs, we'd need additional processing
            # For now, handle HTML content
            if 'text/html' in response.headers.get('content-type', ''):
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Extract text
                text = soup.get_text()
                lines = (line.strip() for line in text.splitlines())
                text = '\n'.join(line for line in lines if line)
                
                return text
            
            return None
        except Exception as e:
            print(f"Error extracting content from {paper_url}: {e}")
            return None
    
    def analyze_paper_for_security_themes(self, paper: Dict[str, Any], content: Optional[str] = None) -> Dict[str, Any]:
        """Analyze paper for AI security themes"""
        if not content:
            content = self.extract_paper_content(paper['url'])
        
        if not content:
            content = f"{paper['title']} {paper['snippet']}"
        
        # Limit content for analysis
        if len(content) > 8000:
            chunks = self.text_splitter.split_text(content)
            content = chunks[0] if chunks else content[:8000]
        
        analysis_prompt = f"""
        Analyze this business/industry paper for AI data security themes. Focus on practical business challenges.
        
        Paper Title: {paper['title']}
        Source: {paper['display_url']}
        Content: {content[:6000]}
        
        Extract information about these specific security challenges:
        
        1. EXTERNAL PARTNERS TRUST:
        - Does the paper discuss sending data to external partners or AI data centers?
        - What concerns about data confidentiality and integrity are mentioned?
        - Are there mentions of losing control over data when using external services?
        
        2. AI DATA INTEGRITY:
        - Does it discuss dataset poisoning or data quality issues?
        - Are there mentions of model tampering or replacement risks?
        - What about training data security and validation?
        
        3. EFFICIENT AI USE:
        - Does it address balancing security with performance?
        - Are there discussions about usability vs security trade-offs?
        - What about practical implementation challenges?
        
        For each theme found, provide:
        - Relevance score (0-10)
        - Key quotes or concepts
        - Business impact mentioned
        - Specific problems or pain points discussed
        
        Also identify:
        - Company/organization behind the paper
        - Author information if available
        - Target audience (technical/business)
        - Practical solutions or recommendations mentioned
        
        Format as JSON with clear structure.
        """
        
        try:
            response = self.llm.invoke(analysis_prompt)
            return self._parse_analysis_response(response, paper)
        except Exception as e:
            print(f"Analysis error for paper {paper['title']}: {e}")
            return self._create_fallback_analysis(paper)
    
    def analyze_altastata_solutions(self, url: str = config.ALTASTATA_URL) -> Dict[str, Any]:
        """Analyze AltaStata website to understand their solutions"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            content = '\n'.join(line for line in lines if line)
            
            analysis_prompt = f"""
            Analyze AltaStata's website content to understand their AI data security solutions.
            
            Website Content: {content[:8000]}
            
            Extract information about:
            1. Core security solutions offered
            2. How they address External Partners Trust issues
            3. How they handle AI Data Integrity challenges  
            4. How they ensure Efficient AI Use (performance + security)
            5. Target market and use cases
            6. Key value propositions
            7. Competitive advantages
            8. Technical approach overview
            
            Format as JSON with clear structure for email generation.
            """
            
            response = self.llm.invoke(analysis_prompt)
            return self._parse_altastata_analysis(response)
            
        except Exception as e:
            print(f"Error analyzing AltaStata website: {e}")
            return self._create_fallback_altastata_analysis()
    
    def _parse_analysis_response(self, response: str, paper: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM analysis response"""
        try:
            # Try to extract JSON from response
            import json
            import re
            
            # Look for JSON-like structure
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed = json.loads(json_str)
                return {**parsed, 'paper_metadata': paper}
            
        except Exception:
            pass
        
        # Fallback: create structured response from text
        return {
            'external_partners_trust': {'relevance_score': 5, 'content': response[:500]},
            'ai_data_integrity': {'relevance_score': 5, 'content': response[500:1000]},
            'efficient_ai_use': {'relevance_score': 5, 'content': response[1000:1500]},
            'paper_metadata': paper,
            'raw_analysis': response
        }
    
    def _parse_altastata_analysis(self, response: str) -> Dict[str, Any]:
        """Parse AltaStata analysis response"""
        return {
            'solutions_overview': response[:1000],
            'external_partners_trust_solution': response[1000:1500],
            'ai_data_integrity_solution': response[1500:2000],
            'efficient_ai_use_solution': response[2000:2500],
            'value_propositions': response[2500:3000],
            'target_market': response[3000:3500],
            'raw_analysis': response
        }
    
    def _create_fallback_analysis(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback analysis when LLM fails"""
        return {
            'external_partners_trust': {'relevance_score': 3, 'content': paper['snippet']},
            'ai_data_integrity': {'relevance_score': 3, 'content': paper['snippet']},
            'efficient_ai_use': {'relevance_score': 3, 'content': paper['snippet']},
            'paper_metadata': paper,
            'analysis_status': 'fallback'
        }
    
    def _create_fallback_altastata_analysis(self) -> Dict[str, Any]:
        """Create fallback AltaStata analysis"""
        return {
            'solutions_overview': 'AltaStata provides AI data security solutions',
            'external_partners_trust_solution': 'Secure data sharing with partners',
            'ai_data_integrity_solution': 'Data and model integrity protection',
            'efficient_ai_use_solution': 'Performance-optimized security',
            'value_propositions': 'Enterprise-grade AI security',
            'target_market': 'Enterprise businesses using AI',
            'analysis_status': 'fallback'
        }
