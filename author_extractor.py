#!/usr/bin/env python3

import re
import logging
from typing import Dict, List, Any
from urllib.parse import urlparse
from langchain_google_vertexai import ChatVertexAI
import json
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class AuthorExtractor:
    def __init__(self):
        # Initialize AI model for intelligent author extraction
        self.llm = ChatVertexAI(
            model_name="gemini-2.5-flash",
            temperature=0.1,
            max_output_tokens=2000
        )

    def extract_author_info(self, url: str, title: str, snippet: str) -> Dict[str, Any]:
        """Extract all authors information using AI"""
        try:
            # Get the full HTML content for AI to analyze
            content = self._get_page_content(url)
            
            # Use AI to extract all authors from the content
            authors_result = self._extract_all_authors_with_ai(url, title, content)
            
            # If no authors found with new method, fall back to single author extraction
            if not authors_result:
                logger.debug("No authors found with multi-author extraction, trying single author")
                single_author_result = self._extract_with_ai(url, title, content)
                if single_author_result.get('name'):
                    authors_result = [single_author_result]
            
            # Process each author and add LinkedIn profiles if missing
            processed_authors = []
            for author_info in authors_result:
                author_name = author_info.get('name', '')
                if author_name and self._is_individual_author(author_name):
                    logger.debug("AI successfully extracted author: %s", author_name)
                    
                    # If no LinkedIn profile found, try to search for it
                    # But only if we have a valid author name to search for
                    if (not author_info.get('linkedin_profile') or author_info.get('linkedin_profile') == 'not found') and author_name.strip():
                        logger.debug("No LinkedIn profile found on page, searching for %s", author_name)
                        linkedin_profile = self._search_linkedin_profile(
                            author_name, 
                            author_info.get('company', ''), 
                            author_info.get('title', '')
                        )
                        if linkedin_profile and linkedin_profile != 'not found':
                            author_info['linkedin_profile'] = linkedin_profile
                            logger.debug("Found LinkedIn profile via search: %s", linkedin_profile)
                        else:
                            logger.debug("LinkedIn search failed for: %s", author_name)
                    
                    # Add source and is_individual flag
                    author_info['source'] = urlparse(url).netloc.lower()
                    author_info['is_individual'] = True
                    processed_authors.append(author_info)
                else:
                    logger.debug("AI did not find a valid individual author: %s", author_name)
            
            # Return the first author for backward compatibility, but with all authors info
            if processed_authors:
                first_author = processed_authors[0]
                first_author['all_authors'] = processed_authors  # Include all authors
                return first_author
            else:
                return {
                    'name': '',
                    'title': '',
                    'company': '',
                    'linkedin_profile': '',
                    'email': '',
                    'profile_summary': '',
                    'source': urlparse(url).netloc.lower(),
                    'is_individual': False,
                    'all_authors': []
                }
                
        except Exception as e:
            logger.debug("Error extracting author info from %s: %s", url, e)
            return {
                'name': '',
                'title': '',
                'company': '',
                'linkedin_profile': '',
                'email': '',
                'profile_summary': '',
                'source': urlparse(url).netloc.lower(),
                'is_individual': False,
                'all_authors': []
            }

    def _search_linkedin_profile(self, author_name: str, company: str = "", title: str = "") -> str:
        """Search for LinkedIn profile using multiple methods"""
        try:
            # Method 1: Try web search first (more reliable)
            linkedin_url = self._search_linkedin_via_web(author_name, company)
            if linkedin_url and linkedin_url != "not found":
                return linkedin_url
            
            # Method 2: Fall back to AI search
            linkedin_url = self._search_linkedin_via_ai(author_name, company, title)
            if linkedin_url and linkedin_url != "not found":
                return linkedin_url
            
            return "not found"
            
        except Exception as e:
            logger.debug("Error searching for LinkedIn profile: %s", e)
            return "not found"
    
    def _search_linkedin_via_web(self, author_name: str, company: str = "") -> str:
        """Search for LinkedIn profile using web search with multiple strategies"""
        try:
            from agents.search_agent import SearchAgent
            search_agent = SearchAgent()
            
            # Strategy 1: Quoted name + site restriction (most precise)
            search_query1 = f'"{author_name}" site:linkedin.com/in/'
            if company:
                search_query1 += f' "{company}"'
            
            logger.debug("LinkedIn search strategy 1: %s", search_query1)
            results1 = search_agent.search_linkedin_profiles(search_query1)
            
            # Check results from strategy 1 - prioritize URLs with the person's name
            name_parts = author_name.lower().split()
            best_match = None
            
            for result in results1:
                url = result.get('url', '')
                title = result.get('title', '').lower()
                
                if 'linkedin.com/in/' in url and 'linkedin.com/company/' not in url:
                    url_lower = url.lower()
                    
                    # Prioritize URLs that contain the person's name
                    if len(name_parts) >= 2:
                        first_name = name_parts[0]
                        last_name = name_parts[-1]
                        
                        # Perfect match: both names in URL
                        if first_name in url_lower and last_name in url_lower:
                            logger.debug("Found perfect LinkedIn match via strategy 1: %s", url)
                            return url
                        # Good match: last name in URL
                        elif last_name in url_lower:
                            best_match = url
                    
                    # Only use as fallback if it's a reasonable match (reject obviously wrong profiles)
                    if not best_match:
                        # Check if the URL or title contains any part of the author's name
                        if any(name_part in url_lower or name_part in title for name_part in name_parts):
                            best_match = url
            
            # Return best match if found
            if best_match:
                logger.debug("Found LinkedIn profile via strategy 1: %s", best_match)
                return best_match
            
            # Strategy 2: Broader search without site restriction (no quotes for better results)
            search_query2 = f'{author_name} linkedin'
            if company:
                search_query2 += f' "{company}"'
            
            logger.debug("LinkedIn search strategy 2: %s", search_query2)
            results2 = search_agent.search_linkedin_profiles(search_query2)
            
            # Check results from strategy 2 for LinkedIn profile URLs
            for result in results2:
                url = result.get('url', '')
                title = result.get('title', '').lower()
                snippet = result.get('snippet', '').lower()
                
                if 'linkedin.com/in/' in url and 'linkedin.com/company/' not in url:
                    logger.debug("Found LinkedIn profile via strategy 2: %s", url)
                    return url
            
            # Strategy 3: Last name first search (for cases like "Philip A. Dursey")
            name_parts = author_name.split()
            if len(name_parts) >= 2:
                last_first_name = f"{name_parts[-1]} {name_parts[0]}"
                search_query3 = f'{last_first_name} linkedin'
                
                logger.debug("LinkedIn search strategy 3: %s", search_query3)
                results3 = search_agent.search_linkedin_profiles(search_query3)
                
                for result in results3:
                    url = result.get('url', '')
                    title = result.get('title', '').lower()
                    snippet = result.get('snippet', '').lower()
                    
                    if 'linkedin.com/in/' in url and 'linkedin.com/company/' not in url:
                        logger.debug("Found LinkedIn profile via strategy 3: %s", url)
                        return url
            
            # Strategy 4: Try concatenated name search (for cases like "Rosa Merced" -> "rosamerced")
            if len(name_parts) >= 2:
                concatenated_name = ''.join(name_parts).lower()
                search_query4 = f'{concatenated_name} linkedin'
                
                logger.debug("LinkedIn search strategy 4: %s", search_query4)
                results4 = search_agent.search_linkedin_profiles(search_query4)
                
                for result in results4:
                    url = result.get('url', '')
                    title = result.get('title', '').lower()
                    snippet = result.get('snippet', '').lower()
                    
                    if 'linkedin.com/in/' in url and 'linkedin.com/company/' not in url:
                        # Check if the concatenated name appears in the URL
                        if concatenated_name in url.lower():
                            logger.debug("Found LinkedIn profile via concatenated name strategy: %s", url)
                            return url
            
            logger.debug("No LinkedIn profile found via web search")
            return "not found"
            
        except Exception as e:
            logger.debug("Error in web search for LinkedIn profile: %s", e)
            return "not found"
    
    def _search_linkedin_via_ai(self, author_name: str, company: str = "", title: str = "") -> str:
        """Use AI to search for LinkedIn profile when not found on page"""
        try:
            # Build search query
            search_query = author_name
            if company:
                search_query += f" {company}"
            if title:
                search_query += f" {title}"
            
            # Create prompt for AI to search for LinkedIn profile
            prompt = f"""
            Search for the LinkedIn profile of this person: {search_query}
            
            Please provide the LinkedIn profile URL if you can find it, or "not found" if you cannot.
            
            Only return valid LinkedIn profile URLs that follow the pattern: linkedin.com/in/username
            Do not return LinkedIn company pages or other LinkedIn URLs.
            
            If you find the profile, return the full URL starting with https://
            If you cannot find it, return exactly: not found
            
            Example of what to return:
            https://www.linkedin.com/in/john-doe-123456789
            or
            not found
            """
            
            # Call AI model to search
            result = self.llm.invoke(prompt)
            
            # Extract LinkedIn URL from response
            linkedin_url = self._extract_linkedin_url_from_ai_response(str(result))
            
            return linkedin_url if linkedin_url else "not found"
            
        except Exception as e:
            logger.debug("Error in AI search for LinkedIn profile: %s", e)
            return "not found"
    
    def _extract_linkedin_url_from_ai_response(self, response: str) -> str:
        """Extract LinkedIn URL from AI response"""
        import re
        
        # Look for LinkedIn profile URLs in the response
        linkedin_pattern = r'https://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9\-]+'
        matches = re.findall(linkedin_pattern, response)
        
        if matches:
            return matches[0]  # Return the first match
        
        # If no URL found, check if response contains "not found"
        if "not found" in response.lower():
            return "not found"
        
        return ""

    def _extract_all_authors_with_ai(self, url: str, title: str, content: str) -> List[Dict[str, str]]:
        """Use AI to extract ALL authors from the article"""
        try:
            # Create a comprehensive prompt for the AI to extract ALL authors
            prompt = f"""
            Analyze this article and extract ALL individual authors AND create an AltaStata compatibility analysis.

            ARTICLE DETAILS:
            Title: {title}
            URL: {url}
            Content: {content[:6000]}...

            IMPORTANT FOR LINKEDIN ARTICLES:
            - Look for ALL author names in the HTML content, especially in author sections, bylines, or profile areas
            - For LinkedIn pulse URLs like "linkedin.com/pulse/article-title-author-name-xyz/", the author name might be in the URL
            - Look for LinkedIn profile URLs (linkedin.com/in/...) in the content - these are often in <a> tags with href attributes
            - Look for author titles and company information in the article metadata or content
            - Pay special attention to any URLs that contain "linkedin.com/in/" as these are the author's profile URLs
            - CRITICAL: Use the EXACT LinkedIn URLs from the LINKEDIN_URLS_FOUND section - do not generate or modify them
            - IMPORTANT: Extract ALL authors, not just the first one. Look for multiple authors, co-authors, contributors, etc.

            ALTASTATA COMPANY PROFILE:
            - Company: AltaStata
            - Tagline: "Data Security for AI"
            - Mission: To empower innovators on their AI journey through cutting-edge, patented technology
            - Core Solutions:
              * End-to-end encryption for AI data
              * Zero-Trust Data Security model
              * Data integrity verification
              * Fortified Data Lake concept
              * Clean room collaboration for partners
              * AI supply chain security
              * Data poisoning prevention
              * Enterprise AI security solutions

            TASKS:
            1. Extract ALL individual author information (not organizations, companies, or generic terms)
            2. Find actual LinkedIn profile URLs in the content (linkedin.com/in/ URLs) - check the LINKEDIN_URLS_FOUND section
            3. Extract author title and company information for EACH author
            4. Create a detailed AltaStata compatibility analysis
            
            EXAMPLE: If LINKEDIN_URLS_FOUND contains ['https://ca.linkedin.com/in/purnimabihari', 'https://linkedin.com/in/john-doe'], 
            then use these EXACT URLs as the linkedin_profile values for the respective authors.

            Return ONLY a JSON array with this exact structure for EACH author:
            [
                {{
                    "name": "Full Name of Individual Author 1",
                    "title": "Author's Job Title",
                    "company": "Author's Company",
                    "linkedin_profile": "EXACT LinkedIn profile URL from LINKEDIN_URLS_FOUND section (do not generate or construct URLs)",
                    "email": "Author's email address",
                    "profile_summary": "Brief author bio",
                }},
                {{
                    "name": "Full Name of Individual Author 2",
                    "title": "Author's Job Title",
                    "company": "Author's Company",
                    "linkedin_profile": "EXACT LinkedIn profile URL from LINKEDIN_URLS_FOUND section (do not generate or construct URLs)",
                    "email": "Author's email address",
                    "profile_summary": "Brief author bio",
                }}
            ]

            If no individual authors are found, return an empty array: []

            IMPORTANT: 
            - Extract ALL authors, not just the first one
            - Only return individual person names, not organizations, companies, or generic terms
            - Look for actual linkedin.com/in/ URLs in the content, not the article URL itself
            - For LinkedIn pulse articles, check both the URL pattern and the HTML content for author information
            - Do NOT construct or generate LinkedIn URLs - only extract real ones from the content
            - Each author should have their own entry in the array
            """

            # Call AI model
            result = self.llm.invoke(prompt)
            
            # Parse JSON response
            import json
            try:
                # Find JSON in the response
                response_text = str(result)
                json_start = response_text.find('[')
                json_end = response_text.rfind(']') + 1
                
                if json_start != -1 and json_end != -1:
                    json_str = response_text[json_start:json_end]
                    authors_list = json.loads(json_str)
                    
                    # Validate and clean up each author
                    valid_authors = []
                    for author in authors_list:
                        if isinstance(author, dict) and author.get('name', '').strip():
                            # Ensure all required fields exist
                            clean_author = {
                                'name': author.get('name', '').strip(),
                                'title': author.get('title', '').strip(),
                                'company': author.get('company', '').strip(),
                                'linkedin_profile': author.get('linkedin_profile', '').strip(),
                                'email': author.get('email', '').strip(),
                                'profile_summary': author.get('profile_summary', '').strip(),
                            }
                            valid_authors.append(clean_author)
                    
                    return valid_authors
                else:
                    logger.debug("No valid JSON array found in AI response")
                    return []
                    
            except json.JSONDecodeError as e:
                logger.debug("Error parsing JSON from AI response: %s", e)
                return []
                
        except Exception as e:
            logger.debug("Error in AI extraction of all authors: %s", e)
            return []

    def _get_page_content(self, url: str) -> str:
        """Get page content for AI analysis"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Get text content
            text_content = soup.get_text()
            
            # Look for LinkedIn profile URLs specifically
            linkedin_links = soup.find_all('a', href=lambda x: x and 'linkedin.com/in/' in x)
            linkedin_urls = [link.get('href') for link in linkedin_links]
            
            # Also get some HTML structure for better context
            html_snippet = str(soup)[:3000]  # First 3000 chars of HTML
            
            return f"HTML: {html_snippet}\n\nTEXT: {text_content[:3000]}\n\nLINKEDIN_URLS_FOUND: {linkedin_urls}"
            
        except Exception as e:
            logger.debug("Error getting page content: %s", e)
            return ""


    def _extract_with_ai(self, url: str, title: str, content: str) -> Dict[str, str]:
        """Use AI to intelligently extract author information and AltaStata compatibility"""
        author_info = {
            'name': '',
            'title': '',
            'company': '',
            'linkedin_profile': '',
            'email': '',
            'profile_summary': '',
        }
        
        try:
            # Create a comprehensive prompt for the AI to do everything
            prompt = f"""
            Analyze this article and extract author information AND create an AltaStata compatibility analysis.

            ARTICLE DETAILS:
            Title: {title}
            URL: {url}
            Content: {content[:6000]}...

            IMPORTANT FOR LINKEDIN ARTICLES:
            - Look for author names in the HTML content, especially in author sections, bylines, or profile areas
            - For LinkedIn pulse URLs like "linkedin.com/pulse/article-title-author-name-xyz/", the author name might be in the URL
            - Look for LinkedIn profile URLs (linkedin.com/in/...) in the content - these are often in <a> tags with href attributes
            - Look for author titles and company information in the article metadata or content
            - Pay special attention to any URLs that contain "linkedin.com/in/" as these are the author's profile URLs
            - CRITICAL: Use the EXACT LinkedIn URLs from the LINKEDIN_URLS_FOUND section - do not generate or modify them

            ALTASTATA COMPANY PROFILE:
            - Company: AltaStata
            - Tagline: "Data Security for AI"
            - Mission: To empower innovators on their AI journey through cutting-edge, patented technology
            - Core Solutions:
              * End-to-end encryption for AI data
              * Zero-Trust Data Security model
              * Data integrity verification
              * Fortified Data Lake concept
              * Clean room collaboration for partners
              * AI supply chain security
              * Data poisoning prevention
              * Enterprise AI security solutions

            TASKS:
            1. Extract individual author information (not organizations, companies, or generic terms)
            2. Find actual LinkedIn profile URLs in the content (linkedin.com/in/ URLs) - check the LINKEDIN_URLS_FOUND section
            3. Extract author title and company information
            4. Create a detailed AltaStata compatibility analysis
            
            EXAMPLE: If LINKEDIN_URLS_FOUND contains ['https://ca.linkedin.com/in/purnimabihari'], 
            then use "https://ca.linkedin.com/in/purnimabihari" as the linkedin_profile value.

            Return ONLY a JSON object with this exact structure:
            {{
                "name": "Full Name of Individual Author",
                "title": "Author's Job Title",
                "company": "Author's Company",
                "linkedin_profile": "EXACT LinkedIn profile URL from LINKEDIN_URLS_FOUND section (do not generate or construct URLs)",
                "email": "Author's email address",
                "profile_summary": "Brief author bio",
            }}

            If no individual author is found, return:
            {{
                "name": "",
                "title": "",
                "company": "",
                "linkedin_profile": "",
                "email": "",
                "profile_summary": "",
                "compatibility_analysis": ""
            }}

            IMPORTANT: 
            - Only return individual person names, not organizations, companies, or generic terms
            - Look for actual linkedin.com/in/ URLs in the content, not the article URL itself
            - For LinkedIn pulse articles, check both the URL pattern and the HTML content for author information
            - Do NOT construct or generate LinkedIn URLs - only extract real ones from the content
            - Use the exact LinkedIn URLs found in the LINKEDIN_URLS_FOUND section
            - Keep the compatibility analysis concise and focused on key pain points
            """
            
            response = self.llm.invoke(prompt)
            
            # Parse the AI response
            try:
                # Extract JSON from the response
                response_text = response.content.strip()
                logger.debug("AI response length: %d", len(response_text))
                logger.debug("AI response preview: %s", response_text[:500])
                
                # Find JSON in the response
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                
                if json_start != -1 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    logger.debug("JSON string: %s", json_str)
                    ai_result = json.loads(json_str)
                    logger.debug("Parsed AI result: %s", ai_result)
                    
                    # Update author_info with AI results
                    author_info.update(ai_result)
                    
                    # If AI didn't find LinkedIn profile but we have one, use it
                    if not ai_result.get('linkedin_profile') and 'LINKEDIN_URLS_FOUND:' in content:
                        # Extract LinkedIn URLs from content
                        linkedin_section = content.split('LINKEDIN_URLS_FOUND:')[1].split('\n')[0].strip()
                        if linkedin_section and linkedin_section != '[]':
                            # Parse the LinkedIn URLs
                            import ast
                            try:
                                linkedin_urls = ast.literal_eval(linkedin_section)
                                if linkedin_urls and len(linkedin_urls) > 0:
                                    # Use the first LinkedIn URL (usually the profile, not activity)
                                    profile_url = linkedin_urls[0]
                                    if '/recent-activity/' not in profile_url:  # Skip activity URLs
                                        author_info['linkedin_profile'] = profile_url
                                        logger.debug("Added LinkedIn profile from content: %s", profile_url)
                                        
                                        # If AI didn't find author name, try to extract from LinkedIn profile URL
                                        if not ai_result.get('name'):
                                            import re
                                            match = re.search(r'linkedin\.com/in/([^/?]+)', profile_url)
                                            if match:
                                                profile_name = match.group(1).replace('-', ' ').title()
                                                # Clean up the name (remove numbers, etc.)
                                                profile_name = re.sub(r'\d+', '', profile_name).strip()
                                                if profile_name and len(profile_name.split()) >= 2:  # At least first and last name
                                                    author_info['name'] = profile_name
                                                    logger.debug("Extracted author name from LinkedIn profile: %s", profile_name)
                            except:
                                pass
                    
                    # Validate that we got a real individual author
                    if ai_result.get('name') and self._is_individual_author(ai_result['name']):
                        logger.debug("AI extracted author: %s", ai_result['name'])
                    else:
                        logger.debug("AI did not find a valid individual author: %s", ai_result.get('name'))
                        
            except (json.JSONDecodeError, KeyError) as e:
                logger.debug("Failed to parse AI response: %s", e)
                logger.debug("Response was: %s", response_text[:500])
                
        except Exception as e:
            logger.debug("AI author extraction failed: %s", e)
        
        return author_info

    def analyze_altastata_compatibility(self, paper_title: str, paper_content: str) -> str:
        """Use AI to analyze how the paper relates to AltaStata's solutions"""
        try:
            prompt = f"""
            Analyze how this article relates to AltaStata's solutions and create a compatibility analysis.

            AltaStata Company Profile:
            - Company: AltaStata
            - Tagline: "Data Security for AI"
            - Mission: To empower innovators on their AI journey through cutting-edge, patented technology
            - Core Solutions:
              * End-to-end encryption for AI data
              * Zero-Trust Data Security model
              * Data integrity verification
              * Fortified Data Lake concept
              * Clean room collaboration for partners
              * AI supply chain security
              * Data poisoning prevention
              * Enterprise AI security solutions

            Article Title: {paper_title}
            Article Content: {paper_content[:2000]}...

            Analyze the compatibility and create a concise analysis that includes:
            1. Key pain points mentioned that AltaStata could solve
            2. How AltaStata's encryption and data security solutions would help
            3. Target audience alignment

            Return a brief analysis with 2-3 bullet points using simple dashes (-), focusing on the most relevant connections. Do not use asterisks (*) or bold formatting (**).
            """
            
            response = self.llm.invoke(prompt)
            return response.content.strip()
            
        except Exception as e:
            logger.debug("AI compatibility analysis failed: %s", e)
            return "- General AI Security: Paper discusses AI security topics that could benefit from AltaStata's encryption and data integrity solutions"

    def _is_individual_author(self, name: str) -> bool:
        """Use AI to check if a name is an individual person rather than an organization"""
        if not name or len(name.strip()) < 2:
            return False

        try:
            prompt = f"""
            Determine if this is the name of an individual person or an organization/company/generic term.

            Name: "{name}"

            Return ONLY "true" if it's an individual person's name, or "false" if it's an organization, company, or generic term.

            Examples of individual persons: "John Smith", "Sarah Johnson", "Dr. Michael Brown"
            Examples of organizations/companies: "Cisco Systems", "Amazon Web Services", "Gannon University", "Department of Technology"
            Examples of generic terms: "bigdata", "admin", "support", "team", "staff"

            Answer: """
            
            response = self.llm.invoke(prompt)
            result = response.content.strip().lower()
            
            return result == "true"
            
        except Exception as e:
            logger.debug("AI author validation failed: %s", e)
            # Fallback to basic check
            return len(name.split()) >= 2 and name.replace(' ', '').isalpha()