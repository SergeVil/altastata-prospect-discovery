"""
LangGraph workflow for AI security paper analysis and email generation
"""
from typing import Dict, Any, List, TypedDict
from langgraph.graph import StateGraph, END
from agents.search_agent import SearchAgent
from agents.analysis_agent import AnalysisAgent
from agents.email_agent import EmailAgent
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import random
import config

class WorkflowState(TypedDict):
    """State for the workflow"""
    search_queries: List[str]
    papers_found: List[Dict[str, Any]]
    papers_analyzed: List[Dict[str, Any]]
    altastata_analysis: Dict[str, Any]
    generated_emails: List[Dict[str, Any]]
    current_step: str
    error_message: str

class AISecurityPaperWorkflow:
    def __init__(self):
        self.search_agent = SearchAgent()
        self.analysis_agent = AnalysisAgent()
        self.email_agent = EmailAgent()
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow"""
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        workflow.add_node("search_papers", self._search_papers_node)
        workflow.add_node("analyze_altastata", self._analyze_altastata_node)
        workflow.add_node("analyze_papers", self._analyze_papers_node)
        workflow.add_node("finalize_results", self._finalize_results_node)
        
        # Define the workflow edges
        workflow.set_entry_point("search_papers")
        workflow.add_edge("search_papers", "analyze_altastata")
        workflow.add_edge("analyze_altastata", "analyze_papers")
        workflow.add_edge("analyze_papers", "finalize_results")
        workflow.add_edge("finalize_results", END)
        
        return workflow.compile()
    
    def _search_papers_node(self, state: WorkflowState) -> WorkflowState:
        """Search for relevant papers on AI security themes"""
        print("🔍 Searching for AI security papers...")
        
        try:
            all_papers = []
            
            # Search for each security theme focusing on business sources with authors
            for theme in config.SECURITY_THEMES:
                print(f"  Searching for papers on: {theme}")
                papers = self.search_agent.search_general_security_papers(theme)
                all_papers.extend(papers)
            
            # Remove duplicates based on URL
            seen_urls = set()
            unique_papers = []
            for paper in all_papers:
                if paper['url'] not in seen_urls:
                    seen_urls.add(paper['url'])
                    unique_papers.append(paper)
            
            # Rank by business relevance
            ranked_papers = self.search_agent.rank_papers_by_business_relevance(unique_papers)
            
            # Take top papers
            top_papers = ranked_papers[:config.PAPERS_PER_BATCH]
            
            print(f"  Found {len(top_papers)} relevant papers")
            
            state["papers_found"] = top_papers
            state["current_step"] = "search_completed"
            
        except Exception as e:
            print(f"Error in search phase: {e}")
            state["error_message"] = f"Search error: {e}"
            state["papers_found"] = []
        
        return state
    
    def _analyze_altastata_node(self, state: WorkflowState) -> WorkflowState:
        """Analyze AltaStata website to understand their solutions"""
        print("🏢 Analyzing AltaStata solutions...")
        
        try:
            altastata_analysis = self.analysis_agent.analyze_altastata_solutions()
            state["altastata_analysis"] = altastata_analysis
            state["current_step"] = "altastata_analyzed"
            print("  AltaStata analysis completed")
            
        except Exception as e:
            print(f"Error analyzing AltaStata: {e}")
            state["error_message"] = f"AltaStata analysis error: {e}"
            state["altastata_analysis"] = self.analysis_agent._create_fallback_altastata_analysis()
        
        return state
    
    def _analyze_papers_node(self, state: WorkflowState) -> WorkflowState:
        """Analyze papers for security themes and extract author information"""
        print("📊 Analyzing papers for security themes...")
        
        papers_found = state.get("papers_found", [])
        analyzed_papers = []
        
        try:
            # Use parallel processing for author extraction
            max_workers = min(6, len(papers_found))  # Increased to 6 workers to test performance vs stability
            print(f"  Processing {len(papers_found)} papers with {max_workers} parallel workers...")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all papers for parallel processing
                future_to_paper = {
                    executor.submit(self._process_paper_parallel, paper): paper 
                    for paper in papers_found
                }
                
                # Process completed papers as they finish
                completed_count = 0
                for future in as_completed(future_to_paper):
                    completed_count += 1
                    paper = future_to_paper[future]
                    
                    try:
                        processed_paper = future.result()
                        print(f"  ✅ Completed {completed_count}/{len(papers_found)}: {processed_paper['title'][:60]}...")
                        
                        # Show author info if found
                        author_info = processed_paper.get('author_info', {})
                        author_name = author_info.get('name', '')
                        if author_name:
                            print(f"     👤 Found author: {author_name} ({author_info.get('title', 'Professional')})")
                        
                        # Simplified analysis - just pass through the paper data with basic structure
                        analysis = {
                            "paper_metadata": processed_paper,
                            "ai_data_integrity": {"relevance_score": 5, "discussion_points": {}},
                            "external_partners_trust": {"relevance_score": 5, "discussion_points": {}},
                            "efficient_ai_use": {"relevance_score": 5, "discussion_points": {}}
                        }
                        analyzed_papers.append(analysis)
                        
                    except Exception as e:
                        print(f"  ❌ Error processing {paper['title'][:60]}: {e}")
                        print(f"     URL: {paper.get('url', 'No URL')}")
                        import traceback
                        print(f"     Full error: {traceback.format_exc()}")
                        # Still add the paper with empty author info
                        paper['author_info'] = {}
                        analysis = {
                            "paper_metadata": paper,
                            "ai_data_integrity": {"relevance_score": 5, "discussion_points": {}},
                            "external_partners_trust": {"relevance_score": 5, "discussion_points": {}},
                            "efficient_ai_use": {"relevance_score": 5, "discussion_points": {}}
                        }
                        analyzed_papers.append(analysis)
            
            state["papers_analyzed"] = analyzed_papers
            state["current_step"] = "papers_analyzed"
            print(f"  Completed analysis of {len(analyzed_papers)} papers")
            
        except Exception as e:
            print(f"Error in paper analysis: {e}")
            state["error_message"] = f"Paper analysis error: {e}"
            state["papers_analyzed"] = analyzed_papers  # Keep partial results
        
        return state
    
    def _generate_emails_node(self, state: WorkflowState) -> WorkflowState:
        """Generate personalized emails based on paper analysis"""
        print("✉️ Generating personalized emails...")
        
        papers_analyzed = state.get("papers_analyzed", [])
        altastata_analysis = state.get("altastata_analysis", {})
        
        try:
            # Take all papers for email generation
            relevant_papers = papers_analyzed
            
            print(f"  Generating emails for {len(relevant_papers)} relevant papers")
            
            generated_emails = []
            
            for i, paper_analysis in enumerate(relevant_papers):
                print(f"  Processing paper {i+1}/{len(relevant_papers)}: {paper_analysis.get('paper_metadata', {}).get('title', '')[:60]}...")
                
                # Extract paper details
                paper_metadata = paper_analysis.get('paper_metadata', {})
                paper_title = paper_metadata.get('title', '')
                paper_url = paper_metadata.get('url', '')
                paper_source = paper_metadata.get('display_url', '')
                # Get all authors from the paper
                author_info = paper_metadata.get('author_info', {})
                all_authors = author_info.get('all_authors', [])
                
                # If no all_authors field, fall back to single author
                if not all_authors:
                    author_name = author_info.get('name', '')
                    if author_name and self.search_agent.author_extractor._is_individual_author(author_name):
                        all_authors = [author_info]
                
                # Process each author
                for author_data in all_authors:
                    author_name = author_data.get('name', '')
                    
                    # Skip if no individual author name
                    if not author_name:
                        print(f"    Skipping - no individual author name found")
                        continue
                    
                    # Use the author extractor's validation method
                    if not self.search_agent.author_extractor._is_individual_author(author_name):
                        print(f"    Skipping - not an individual author: {author_name}")
                        continue
                    
                    # Extract compatibility analysis from author info (already done by AI)
                    compatibility = author_data.get('compatibility_analysis', '')
                    
                    # Generate LinkedIn messages
                    try:
                        messages = self._generate_linkedin_messages(
                            author_name, paper_title, compatibility, author_data
                        )
                        print(f"       LinkedIn messages generated: {bool(messages.get('connection_request'))}")
                    except Exception as e:
                        print(f"       ERROR generating LinkedIn messages: {e}")
                        messages = {
                            'connection_request': f"Hi {author_name}, I read your article on {paper_title} - would love to connect and discuss AI security challenges. Best, Serge",
                            'follow_up_message': f"Hi {author_name}, thanks for connecting! I read your article on {paper_title} and would love to discuss AI security challenges. Best, Serge"
                        }
                    
                    # Create result
                    result = {
                        'paper_title': paper_title,
                        'paper_url': paper_url,
                        'paper_source': paper_source,
                        'author_info': author_data,
                        'compatibility_analysis': compatibility,
                        'linkedin_messages': messages
                    }
                    generated_emails.append(result)
                    
                    # Output result immediately
                    print(f"    ✅ Found prospect: {author_name} ({author_data.get('title', 'Professional')})")
                    print(f"       Company: {author_data.get('company', 'Not specified')}")
                    print(f"       LinkedIn: {author_data.get('linkedin_profile', 'Not found - needs manual search')}")
                    print(f"       Source: {paper_source}")
                    print()
            
            state["generated_emails"] = generated_emails
            state["current_step"] = "emails_generated"
            print(f"  Generated {len(generated_emails)} personalized emails")
            
        except Exception as e:
            print(f"Error in email generation: {e}")
            state["error_message"] = f"Email generation error: {e}"
            state["generated_emails"] = []
        
        return state
    
    def _generate_linkedin_messages(self, author_name: str, paper_title: str, 
                                   compatibility_analysis: str, author_info: Dict[str, Any]) -> Dict[str, str]:
        """Generate personalized LinkedIn connection request and follow-up messages"""
        try:
            # Extract key compatibility points from the analysis
            compatibility_points = self._extract_compatibility_points(compatibility_analysis)
            
            # Generate connection request message (under 300 characters)
            connection_request = self._generate_connection_request(
                author_name, paper_title, compatibility_points
            )
            
            # Generate follow-up message (under 8000 characters)
            follow_up_message = self._generate_follow_up_message(
                author_name, paper_title, compatibility_analysis, compatibility_points, author_info
            )
            
            return {
                'connection_request': connection_request,
                'follow_up_message': follow_up_message
            }
            
        except Exception as e:
            print(f"Error generating LinkedIn messages for {author_name}: {e}")
            return {
                'connection_request': f"Hi {author_name}, I read your article on {paper_title} - would love to connect and discuss AI security challenges. Best, Serge",
                'follow_up_message': f"Hi {author_name}, thanks for connecting! I read your article on {paper_title} and would love to discuss AI security challenges. Best, Serge"
            }
    
    def _extract_compatibility_points(self, compatibility_analysis: str) -> List[str]:
        """Extract key compatibility points from the analysis using AI"""
        try:
            # Use AI to extract specific, unique insights from the compatibility analysis
            prompt = f"""
            Extract 3 specific, unique insights from this AltaStata compatibility analysis. 
            Focus on the most relevant and specific points that relate to the paper's content.
            
            Compatibility Analysis: {compatibility_analysis}
            
            Return ONLY 3 specific bullet points that are:
            1. Unique to this paper's content
            2. Specific to the challenges mentioned
            3. Directly relevant to AltaStata's solutions
            4. Written as short, impactful phrases (not generic terms)
            
            Format as a simple list, one per line:
            - [specific insight 1]
            - [specific insight 2] 
            - [specific insight 3]
            """
            
            response = self.search_agent.llm.invoke(prompt)
            # Handle both string and object responses
            if hasattr(response, 'content'):
                content = response.content.strip()
            else:
                content = str(response).strip()
            
            # Parse the response into a list
            points = []
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('- '):
                    points.append(line[2:].strip())
                elif line and not line.startswith('#'):
                    points.append(line.strip())
            
            # Return up to 3 points, or fallback if AI extraction fails
            if len(points) >= 2:
                return points[:3]
            
        except Exception as e:
            print(f"Error extracting compatibility points with AI: {e}")
        
        # Fallback to simple keyword extraction if AI fails
        points = []
        analysis_lower = compatibility_analysis.lower()
        
        # Look for specific, unique phrases rather than generic terms
        if "vendor risk" in analysis_lower:
            points.append("vendor risk mitigation")
        if "multi-source" in analysis_lower:
            points.append("multi-source data integrity")
        if "supply chain" in analysis_lower:
            points.append("AI supply chain security")
        if "privacy compliance" in analysis_lower:
            points.append("AI privacy compliance")
        if "model governance" in analysis_lower:
            points.append("AI model governance")
        if "data poisoning" in analysis_lower:
            points.append("data poisoning prevention")
        if "zero trust" in analysis_lower:
            points.append("Zero Trust implementation")
        if "encryption" in analysis_lower and "transit" in analysis_lower:
            points.append("end-to-end encryption")
        
        # If still no specific points, use the first few sentences as insights
        if not points:
            sentences = compatibility_analysis.split('.')[:3]
            for sentence in sentences:
                if sentence.strip() and len(sentence.strip()) > 20:
                    points.append(sentence.strip()[:80] + "..." if len(sentence.strip()) > 80 else sentence.strip())
        
        return points[:3]
    
    def _generate_connection_request(self, author_name: str, paper_title: str, 
                                   compatibility_points: List[str]) -> str:
        """Generate connection request message under 300 characters"""
        # Extract first name only
        first_name = author_name.split()[0] if author_name else "there"
        
        # Build the message with complete title and very concise wording
        if compatibility_points:
            points_text = ", ".join(compatibility_points[:2])  # Use top 2 points
            message = f"Dear {first_name}, I read your article '{paper_title}' - your insights on {points_text} resonated with me. I'm the founder of AltaStata, an MIT startup focused on AI data security. Would love to connect. Best, Serge"
        else:
            message = f"Dear {first_name}, I read your article '{paper_title}' - insightful points about AI security. I'm the founder of AltaStata, an MIT startup focused on AI data security. Would love to connect. Best, Serge"
        
        # Ensure it's under 300 characters with even more concise wording
        if len(message) > 300:
            message = f"Dear {first_name}, I read your article '{paper_title}' - your insights resonated with me. I'm the founder of AltaStata, an MIT startup focused on AI data security. Would love to connect. Best, Serge"
        
        return message
    
    def _generate_follow_up_message(self, author_name: str, paper_title: str, 
                                  compatibility_analysis: str, compatibility_points: List[str],
                                  author_info: Dict[str, Any]) -> str:
        """Generate follow-up message under 8000 characters"""
        
        # Extract company info
        company = author_info.get('company', 'your company')
        title = author_info.get('title', 'Professional')
        
        # Extract first name only
        first_name = author_name.split()[0] if author_name else "there"
        
        # Extract author's specific insights from their paper using AI
        author_insights = self._extract_author_insights_from_paper(paper_title, compatibility_analysis)
        
        # Build the follow-up message
        message = f"""Dear {first_name},

Thanks for connecting! Your article points to real AI security challenges that companies are facing today.

What particularly caught my attention was your emphasis on:
{author_insights}

Your insights align perfectly with what we're building at AltaStata, an MIT startup with cutting-edge patented encryption approaches for AI data security.

I'd love to get your perspective on the AI data security landscape.

Would you be open to a 15-minute call?

Best,
Serge"""
        
        return message
    
    def _extract_author_insights_from_paper(self, paper_title: str, compatibility_analysis: str) -> str:
        """Extract the author's specific insights from their paper, not AltaStata features"""
        try:
            # Use AI to extract the author's specific points from their paper
            prompt = f"""
            Based ONLY on this paper title, extract 3 specific points that the author likely emphasized in their paper.
            
            Paper Title: {paper_title}
            
            These bullet points will be used in this exact context: "What particularly caught my attention was your emphasis on:"
            
            Return ONLY 3 short bullet points (max 15 words each) that complete the sentence "your emphasis on: [bullet point]":
            • [emphasis point 1]
            • [emphasis point 2] 
            • [emphasis point 3]
            
            CRITICAL INSTRUCTIONS:
            - Each bullet point should be ONLY the content that goes after "your emphasis on:"
            - Do NOT include "What particularly caught my attention was your emphasis on:" in the bullet points
            - Do NOT use "the author", "explains", "discusses", "outlines", or "presents"
            - Write direct statements about what was emphasized, not descriptions of what the paper does
            - Focus on the paper's key emphases, NOT on any company solutions
            - Example: If the emphasis was on "data governance", write "• data governance frameworks"
            """
            
            response = self.search_agent.llm.invoke(prompt)
            # Handle both string and object responses
            if hasattr(response, 'content'):
                content = response.content.strip()
            else:
                content = str(response).strip()
            
            # Clean up the response and extract bullet points
            lines = content.split('\n')
            bullet_points = []
            
            for line in lines:
                line = line.strip()
                # Clean up the line - remove any asterisks and extra formatting
                line = line.replace('*', '').replace('  ', ' ').strip()
                
                # Skip the redundant phrase that AI sometimes includes
                if 'what particularly caught my attention was your emphasis on:' in line.lower():
                    continue
                
                # Look for bullet points
                if line.startswith('•'):
                    # Clean up the content after the bullet
                    content_after_bullet = line[1:].strip()
                    if content_after_bullet:
                        bullet_points.append(f"• {content_after_bullet}")
                elif line.startswith('-'):
                    # Convert - to • and clean up
                    content_after_dash = line[1:].strip()
                    if content_after_dash:
                        bullet_points.append(f"• {content_after_dash}")
                # Skip explanatory text and short lines
                elif line and len(line) > 15 and not any(skip in line.lower() for skip in 
                    ['paper title', 'compatibility analysis', 'return only', 'no explanatory', 'no "the author"', 'just the insights', 'what particularly caught', 'your emphasis on']):
                    # If it looks like an insight without bullet, add bullet
                    if not line.startswith('[') and not line.startswith('('):
                        bullet_points.append(f"• {line}")
            
            # Return the formatted insights (max 3 points)
            if bullet_points:
                return '\n'.join(bullet_points[:3])
            
        except Exception as e:
            print(f"Error extracting author insights: {e}")
        
        # Fallback to generic insights
        return """• AI security challenges you outlined
• Data protection strategies you discussed  
• Enterprise AI governance approaches you covered"""
    
    def _process_paper_parallel(self, paper_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single paper in parallel"""
        try:
            paper_title = paper_metadata.get('title', '')
            paper_url = paper_metadata.get('url', '')
            paper_snippet = paper_metadata.get('snippet', '')
            
            # Extract author information
            author_info = self.search_agent.author_extractor.extract_author_info(
                paper_url, paper_title, paper_snippet
            )
            
            # Update paper metadata with author info
            paper_metadata['author_info'] = author_info
            
            return paper_metadata
            
        except Exception as e:
            print(f"    Error processing {paper_metadata.get('title', 'Unknown')}: {e}")
            return paper_metadata
    
    def _finalize_results_node(self, state: WorkflowState) -> WorkflowState:
        """Finalize and format results"""
        print("📋 Finalizing results...")
        
        state["current_step"] = "completed"
        
        # Generate prospects directly from analyzed papers
        papers_analyzed = state.get("papers_analyzed", [])
        prospects = []
        
        for paper_analysis in papers_analyzed:
            paper_metadata = paper_analysis.get('paper_metadata', {})
            author_info = paper_metadata.get('author_info', {})
            author_name = author_info.get('name', '').strip()
            
            # Only include papers with individual person names
            if author_name and author_info.get('is_individual', False):
                prospect = {
                    'paper_title': paper_metadata.get('title', ''),
                    'paper_url': paper_metadata.get('url', ''),
                    'paper_source': paper_metadata.get('display_url', ''),
                    'author_info': author_info,
                    'compatibility_analysis': author_info.get('compatibility_analysis', '')
                }
                prospects.append(prospect)
                print(f"  ✅ Found prospect: {author_name} ({author_info.get('title', 'Professional')})")
                print(f"     Company: {author_info.get('company', 'Not specified')}")
                print(f"     LinkedIn: {author_info.get('linkedin_profile', 'Not found - needs manual search')}")
                print(f"     Source: {paper_metadata.get('display_url', '')}")
                print()
        
        state["generated_emails"] = prospects  # Keep the same key for compatibility
        
        # Add summary statistics
        papers_found = len(state.get("papers_found", []))
        papers_analyzed = len(state.get("papers_analyzed", []))
        prospects_found = len(prospects)
        
        print(f"""
📈 Workflow Summary:
   Papers Found: {papers_found}
   Papers Analyzed: {papers_analyzed}
   Prospects Found: {prospects_found}
   Status: {'⚠️ Completed with errors' if state.get('error_message') else '✅ Completed successfully'}
        """)
        
        return state
    
    def _calculate_max_relevance_score(self, paper_analysis: Dict[str, Any]) -> int:
        """Calculate maximum relevance score across all themes"""
        scores = []
        for theme in ['external_partners_trust', 'ai_data_integrity', 'efficient_ai_use']:
            theme_data = paper_analysis.get(theme, {})
            if isinstance(theme_data, dict):
                scores.append(theme_data.get('relevance_score', 0))
        
        return max(scores) if scores else 0
    
    def _analyze_altastata_compatibility(self, paper_analysis: Dict[str, Any], altastata_analysis: Dict[str, Any]) -> str:
        """Analyze how the paper relates to AltaStata's solutions"""
        paper_metadata = paper_analysis.get('paper_metadata', {})
        paper_title = paper_metadata.get('title', '')
        paper_snippet = paper_metadata.get('snippet', '')
        
        # Simple compatibility analysis based on keywords
        text = f"{paper_title} {paper_snippet}".lower()
        
        compatibility_points = []
        
        # Check for AltaStata core technologies
        if 'encryption' in text:
            compatibility_points.append("- Encryption Focus: Paper discusses encryption, which is AltaStata's core technology")
        
        if 'zero trust' in text:
            compatibility_points.append("- Zero Trust: Paper mentions zero trust security model, which AltaStata implements")
        
        if 'data integrity' in text:
            compatibility_points.append("- Data Integrity: Paper focuses on data integrity, a key AltaStata solution area")
        
        if 'ai security' in text or 'artificial intelligence security' in text:
            compatibility_points.append("- AI Security: Paper is about AI security, AltaStata's target market")
        
        if 'enterprise' in text or 'business' in text:
            compatibility_points.append("- Enterprise Focus: Paper targets enterprise/business audience, AltaStata's target market")
        
        if 'compliance' in text or 'governance' in text:
            compatibility_points.append("- Compliance/Governance: Paper discusses compliance/governance, areas where AltaStata provides solutions")
        
        if not compatibility_points:
            compatibility_points.append("- General AI Security: Paper discusses AI security topics that could benefit from AltaStata's encryption and data integrity solutions")
        
        return "\n".join(compatibility_points)
    
    def run_workflow(self, initial_state: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run the complete workflow"""
        if initial_state is None:
            initial_state = {
                "search_queries": [f"{theme} AI security business" for theme in config.SECURITY_THEMES],
                "papers_found": [],
                "papers_analyzed": [],
                "altastata_analysis": {},
                "generated_emails": [],
                "current_step": "starting",
                "error_message": ""
            }
        
        print("🚀 Starting AI Security Paper Analysis Workflow...")
        
        try:
            final_state = self.workflow.invoke(initial_state)
            return final_state
        except Exception as e:
            print(f"Workflow error: {e}")
            return {
                **initial_state,
                "error_message": f"Workflow failed: {e}",
                "current_step": "failed"
            }
    
    def run_single_company_analysis(self, company_domain: str) -> Dict[str, Any]:
        """Run analysis for a specific company domain"""
        print(f"🏢 Running targeted analysis for: {company_domain}")
        
        # Search for papers from this specific company
        all_papers = []
        for theme in config.SECURITY_THEMES:
            papers = self.search_agent.search_company_papers(company_domain, theme)
            all_papers.extend(papers)
        
        if not all_papers:
            print(f"No papers found for {company_domain}")
            return {"error": f"No papers found for {company_domain}"}
        
        # Run workflow with these specific papers
        initial_state = {
            "search_queries": [f"site:{company_domain}"],
            "papers_found": all_papers,
            "papers_analyzed": [],
            "altastata_analysis": {},
            "generated_emails": [],
            "current_step": "search_completed",
            "error_message": ""
        }
        
        # Skip search step since we already have papers
        state = self._analyze_altastata_node(initial_state)
        state = self._analyze_papers_node(state)
        state = self._generate_emails_node(state)
        state = self._finalize_results_node(state)
        
        return state
