"""
Email Agent for generating personalized outreach emails
"""
from typing import Dict, Any, List
from langchain_google_vertexai import VertexAI
import config

class EmailAgent:
    def __init__(self):
        # Explicitly set the project to override gcloud defaults
        import os
        os.environ["GOOGLE_CLOUD_PROJECT"] = config.GOOGLE_CLOUD_PROJECT
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config.GOOGLE_APPLICATION_CREDENTIALS
        
        self.llm = VertexAI(
            model_name="gemini-2.5-flash",
            project=config.GOOGLE_CLOUD_PROJECT,
            location=config.VERTEX_AI_LOCATION,
            temperature=0.7  # Higher temperature for more creative emails
        )
    
    def generate_personalized_email(
        self, 
        paper_analysis: Dict[str, Any], 
        altastata_analysis: Dict[str, Any],
        target_contact: Dict[str, Any] = None
    ) -> Dict[str, str]:
        """Generate personalized email based on paper analysis and AltaStata solutions"""
        
        paper_metadata = paper_analysis.get('paper_metadata', {})
        
        email_prompt = f"""
        Generate a personalized business outreach email based on the following information:
        
        PAPER ANALYSIS:
        Title: {paper_metadata.get('title', 'Unknown')}
        Source: {paper_metadata.get('display_url', 'Unknown')}
        
        Security Theme Relevance:
        - External Partners Trust: {paper_analysis.get('external_partners_trust', {}).get('relevance_score', 0)}/10
        - AI Data Integrity: {paper_analysis.get('ai_data_integrity', {}).get('relevance_score', 0)}/10  
        - Efficient AI Use: {paper_analysis.get('efficient_ai_use', {}).get('relevance_score', 0)}/10
        
        Key Insights from Paper:
        {paper_analysis.get('external_partners_trust', {}).get('content', '')[:300]}
        {paper_analysis.get('ai_data_integrity', {}).get('content', '')[:300]}
        {paper_analysis.get('efficient_ai_use', {}).get('content', '')[:300]}
        
        ALTASTATA SOLUTIONS:
        Overview: {altastata_analysis.get('solutions_overview', '')[:400]}
        External Partners Trust Solution: {altastata_analysis.get('external_partners_trust_solution', '')[:300]}
        AI Data Integrity Solution: {altastata_analysis.get('ai_data_integrity_solution', '')[:300]}
        Efficient AI Use Solution: {altastata_analysis.get('efficient_ai_use_solution', '')[:300]}
        Value Propositions: {altastata_analysis.get('value_propositions', '')[:300]}
        
        EMAIL REQUIREMENTS:
        Use this PROVEN LINKEDIN MESSAGE STYLE that worked to connect with a Google researcher:
        
        SUCCESSFUL EXAMPLE:
        "Hi [Name],
        
        We're a startup founded by MIT researchers, focused on data security for AI.
        
        I read your piece on "[Paper Title]"—very insightful. I'd love to connect and explore the opportunity to exchange ideas.
        
        Looking forward to staying in touch,
        
        Best,
        Serge"
        
        REQUIREMENTS:
        1. Keep it ultra-short (50-80 words maximum)
        2. Lead with MIT credibility: "startup founded by MIT researchers"
        3. Specific paper reference: exact title 
        4. Focus on THEIR RESEARCH, not our solutions
        5. Ask thoughtful questions about their work
        6. Express genuine interest in their insights
        7. Simple call-to-action: "exchange ideas" or "discuss further"
        8. No product pitches or AltaStata solution details
        
        Generate:
        1. Subject line
        2. Email body
        3. Brief rationale for the approach
        
        Format as JSON with keys: subject, body, rationale
        """
        
        try:
            response = self.llm.invoke(email_prompt)
            return self._parse_email_response(response, paper_analysis, altastata_analysis)
        except Exception as e:
            print(f"Email generation error: {e}")
            return self._create_fallback_email(paper_analysis, altastata_analysis)
    
    def generate_follow_up_email(
        self, 
        original_email: Dict[str, str], 
        paper_analysis: Dict[str, Any],
        altastata_analysis: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate follow-up email with different angle"""
        
        paper_metadata = paper_analysis.get('paper_metadata', {})
        
        followup_prompt = f"""
        Generate a follow-up email with a different angle based on:
        
        ORIGINAL EMAIL:
        Subject: {original_email.get('subject', '')}
        Body: {original_email.get('body', '')[:500]}
        
        PAPER: {paper_metadata.get('title', '')}
        SOURCE: {paper_metadata.get('display_url', '')}
        
        For the follow-up:
        1. Take a different approach (focus on different security theme)
        2. Add new value proposition or insight
        3. Reference industry trends or recent developments
        4. Shorter and more direct
        5. Different call-to-action
        
        Generate subject and body for follow-up email.
        Format as JSON with keys: subject, body, approach_difference
        """
        
        try:
            response = self.llm.invoke(followup_prompt)
            return self._parse_email_response(response, paper_analysis, altastata_analysis)
        except Exception as e:
            print(f"Follow-up email generation error: {e}")
            return self._create_fallback_followup_email(paper_analysis)
    
    def batch_generate_emails(
        self, 
        paper_analyses: List[Dict[str, Any]], 
        altastata_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate emails for multiple papers"""
        emails = []
        
        for i, paper_analysis in enumerate(paper_analyses):
            print(f"Generating email {i+1}/{len(paper_analyses)}...")
            
            email = self.generate_personalized_email(paper_analysis, altastata_analysis)
            
            result = {
                'paper_title': paper_analysis.get('paper_metadata', {}).get('title', ''),
                'paper_url': paper_analysis.get('paper_metadata', {}).get('url', ''),
                'paper_source': paper_analysis.get('paper_metadata', {}).get('display_url', ''),
                'email': email,
                'analysis_summary': self._create_analysis_summary(paper_analysis),
                'author_info': paper_analysis.get('paper_metadata', {}).get('author_info', {})
            }
            
            emails.append(result)
        
        return emails
    
    def _parse_email_response(
        self, 
        response: str, 
        paper_analysis: Dict[str, Any], 
        altastata_analysis: Dict[str, Any]
    ) -> Dict[str, str]:
        """Parse LLM email response"""
        try:
            import json
            import re
            
            # Look for JSON-like structure
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed = json.loads(json_str)
                return parsed
            
        except Exception:
            pass
        
        # Fallback: extract from text
        lines = response.split('\n')
        subject = next((line for line in lines if 'subject' in line.lower()), "Subject: Collaboration Opportunity - AI Data Security")
        
        return {
            'subject': subject.split(':', 1)[-1].strip().strip('"'),
            'body': response[:800],
            'rationale': 'Extracted from LLM response'
        }
    
    def _create_fallback_email(
        self, 
        paper_analysis: Dict[str, Any], 
        altastata_analysis: Dict[str, Any]
    ) -> Dict[str, str]:
        """Create fallback email when generation fails"""
        paper_metadata = paper_analysis.get('paper_metadata', {})
        
        return {
            'subject': f"AI Security Insights - {paper_metadata.get('display_url', 'Your Research')}",
            'body': f"""
I came across your paper "{paper_metadata.get('title', 'your research')}" and found the insights on AI data security particularly relevant.

Your work on challenges like data integrity and external partner trust aligns closely with what we're solving at AltaStata. We'd love to discuss how our approach might complement your research.

Would you be interested in a brief conversation about practical AI security implementation?

Best regards,
[Your name]
""".strip(),
            'rationale': 'Fallback template used due to generation error'
        }
    
    def _create_fallback_followup_email(self, paper_analysis: Dict[str, Any]) -> Dict[str, str]:
        """Create fallback follow-up email"""
        return {
            'subject': "Quick follow-up on AI security collaboration",
            'body': "Following up on my previous message about AI security solutions. Would love to connect briefly if you're interested in exploring this further.",
            'approach_difference': 'Shorter and more direct approach'
        }
    
    def _create_analysis_summary(self, paper_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of paper analysis for reference"""
        return {
            'themes_identified': [
                theme for theme in ['external_partners_trust', 'ai_data_integrity', 'efficient_ai_use']
                if paper_analysis.get(theme, {}).get('relevance_score', 0) > 5
            ],
            'highest_relevance_score': max([
                paper_analysis.get(theme, {}).get('relevance_score', 0)
                for theme in ['external_partners_trust', 'ai_data_integrity', 'efficient_ai_use']
            ]),
            'business_score': paper_analysis.get('paper_metadata', {}).get('business_score', 0)
        }
