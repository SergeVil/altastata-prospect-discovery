#!/usr/bin/env python3
"""
LinkedIn HTML Parser - Extract Real Contributors from Saved HTML
Parses the saved LinkedIn advice post HTML to extract all real contributors
"""

import re
import json
from typing import List, Dict, Any
from datetime import datetime

class LinkedInHTMLParser:
    def __init__(self, html_file_path: str):
        self.html_file_path = html_file_path
        self.contributors = []
    
    def parse_html_file(self) -> List[Dict[str, Any]]:
        """Parse the HTML file and extract all contributors with precise boundary detection"""
        print("🔍 Parsing LinkedIn HTML file for real contributors...")
        
        try:
            with open(self.html_file_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
            print(f"📄 HTML file read successfully, length: {len(html_content)}")
        except Exception as e:
            print(f"❌ Error reading HTML file: {e}")
            return []
        
        import re
        
        # Find all contributor patterns more precisely using LinkedIn profile links
        contributor_pattern = r'<a[^>]*href="[^"]*linkedin\.com/in/([^?"]+)[^"]*"[^>]*>([^<]+?)(?:&#[0-9]+;|⚡)?Follow</a>'
        
        matches = list(re.finditer(contributor_pattern, html_content))
        print(f"🔍 Found {len(matches)} contributor profiles with precise boundary detection")
        
        for i, match in enumerate(matches):
            linkedin_id = match.group(1)
            contributor_name = match.group(2)
            match_start = match.start()
                
            if i <= 3:  # Debug first 3 contributors
                print(f"🔍 Processing contributor {i+1}: {contributor_name}")
                print(f"📄 LinkedIn ID: {linkedin_id}")
            
            # Find the content that belongs to this specific contributor
            # Look for content between this contributor and the next one
            next_match_start = len(html_content)  # Default to end of file
            if i + 1 < len(matches):
                next_match_start = matches[i + 1].start()
            
            # Extract the section for this contributor only
            contributor_section = html_content[match_start:next_match_start]
            
            # Extract contributor data using precise section boundaries
            contributor = self._extract_contributor_from_precise_section(
                contributor_section, contributor_name, linkedin_id, i+1
            )
            
            if contributor:
                self.contributors.append(contributor)
                print(f"✅ Extracted contributor {len(self.contributors)}: {contributor['name']}")
            else:
                if i <= 3:  # Only show debug for first 3
                    print(f"❌ Failed to extract contributor {i+1}: {contributor_name}")
        
        # Remove duplicates based on LinkedIn profile URL (for cases where same person appears multiple times)
        unique_contributors = self._remove_duplicates(self.contributors)
        
        print(f"✅ Successfully extracted {len(self.contributors)} real contributors")
        print(f"📊 Unique contributors after deduplication: {len(unique_contributors)}")
        return unique_contributors
    
    def _extract_contributor_from_precise_section(self, section: str, contributor_name: str, linkedin_id: str, index: int) -> Dict[str, Any]:
        """Extract contributor information from a precisely bounded section"""
        try:
            # Clean up contributor name
            import re
            import html
            
            # Decode HTML entities and clean up name
            clean_name = html.unescape(contributor_name)
            clean_name = re.sub(r'[🌟⭐💼🔒🔐📊🚀🛠️📜🔄]', '', clean_name).strip()
            clean_name = re.sub(r'\s+', ' ', clean_name).strip()
            
            # Construct LinkedIn profile URL
            linkedin_profile = f"https://linkedin.com/in/{linkedin_id}"
            
            # Extract title/position from the section
            title = self._extract_title_from_section(section)
            
            # Clean title - decode HTML entities and remove artifacts
            clean_title = html.unescape(title)
            clean_title = re.sub(r'[🌟⭐💼🔒🔐📊🚀🛠️📜🔄]', '', clean_title).strip()
            clean_title = re.sub(r'\s+', ' ', clean_title).strip()
            
            # Extract answer using precise boundaries
            answer = self._extract_answer(section)
            
            # Extract engagement metrics
            likes = self._extract_likes(section)
            replies = self._extract_replies(section)
            
            # Create contributor data with clean title for priority detection
            contributor = {
                'name': clean_name,
                'title': clean_title,
                'linkedin_profile': linkedin_profile,
                'answer': answer,
                'likes': likes,
                'replies': replies,
                'is_high_priority': self._is_high_priority(clean_title),  # Use clean title
                'is_business_developer': self._is_business_developer(clean_title),  # Use clean title
                'mentions_encryption': 'encryption' in answer.lower() or 'encrypt' in answer.lower(),
                'index': index,
                'source': 'precise_extraction'
            }
            
            return contributor
            
        except Exception as e:
            print(f"❌ Error extracting contributor from precise section: {e}")
            return None
    
    def _extract_contributor_from_section(self, section: str, index: int) -> Dict[str, Any]:
        """Extract contributor information from a section"""
        try:
            # Extract LinkedIn profile URL from Google redirect
            linkedin_url_match = re.search(r'https://[a-z]{2}\.linkedin\.com/in/[a-zA-Z0-9\-]+', section)
            if not linkedin_url_match:
                linkedin_url_match = re.search(r'https://www\.linkedin\.com/in/[a-zA-Z0-9\-]+', section)
            
            linkedin_url = linkedin_url_match.group(0) if linkedin_url_match else ""
            
            # Extract name from the section - handle different HTML structures
            name = ""
            
            # Try to find name in LinkedIn profile link first - look for the pattern we see in the HTML
            name_match = re.search(r'<a[^>]*href="[^"]*linkedin\.com/in/[^"]*"[^>]*>([^<]+)</a>', section)
            if name_match:
                name = name_match.group(1).strip()
            else:
                # Look for plain text names after "Contributor profile photo"
                name_match = re.search(r'Contributor profile photo\s*\n([A-Za-z][A-Za-z\s\.\-,&🌟⭐💼🔒🔐📊🚀🛠️📜🔄]+[A-Za-z])', section)
                if name_match:
                    name = name_match.group(1).strip()
                else:
                    # Fallback: look for any text that looks like a name (starts with capital letter)
                    name_match = re.search(r'\n([A-Z][A-Za-z\s\.\-,&🌟⭐💼🔒🔐📊🚀🛠️📜🔄]+[A-Za-z])\n', section)
                    if name_match:
                        name = name_match.group(1).strip()
                    else:
                        return None
            
            if not name or len(name) < 2:
                return None
            
            # Additional cleanup - remove any remaining HTML artifacts
            name = re.sub(r'&[^;]+;', '', name)  # Remove HTML entities
            name = re.sub(r'<[^>]+>', '', name)  # Remove any remaining HTML tags
            name = re.sub(r'\s+', ' ', name).strip()  # Clean up whitespace
            
            # Clean up name (remove emojis and extra characters)
            name = re.sub(r'[🌟⭐💼🔒🔐📊🚀🛠️📜🔄]', '', name).strip()
            
            # Extract title/position from the section
            title = self._extract_title_from_section(section)
            
            # If title is too long (likely answer content), try to extract from the answer itself
            if len(title) > 200:
                # Look for job title patterns in the title
                job_title_patterns = [
                    r'(Top AI Voice[^.]*)',
                    r'(Patent Filed[^.]*)',
                    r'(Founder[^.]*)',
                    r'(CEO[^.]*)',
                    r'(CTO[^.]*)',
                    r'(CFO[^.]*)',
                    r'(COO[^.]*)',
                    r'(President[^.]*)',
                    r'(Executive[^.]*)',
                    r'(Senior[^.]*)',
                    r'(Lead[^.]*)',
                    r'(Principal[^.]*)',
                    r'(Chief[^.]*)',
                    r'(VP[^.]*)',
                    r'(Director[^.]*)',
                    r'(Manager[^.]*)',
                    r'(Digital transformation[^.]*)',
                    r'(Author[^.]*)',
                    r'(keynote speaker[^.]*)'
                ]
                
                for pattern in job_title_patterns:
                    match = re.search(pattern, title, re.IGNORECASE)
                    if match:
                        title = match.group(1).strip()
                        break
                else:
                    # If no job title found, use a generic title
                    title = "Professional"
            
            # Extract answer content
            answer = self._extract_answer(section)
            
            # Extract engagement metrics
            likes = self._extract_likes(section)
            replies = self._extract_replies(section)
            
            # Determine if high priority
            is_high_priority = self._is_high_priority(title)
            is_business_dev = self._is_business_developer(title)
            mentions_encryption = 'encryption' in answer.lower() or 'encrypt' in answer.lower()
            
            return {
                'name': name,
                'title': title,
                'linkedin_profile': linkedin_url,
                'answer': answer,
                'likes': likes,
                'replies': replies,
                'is_high_priority': is_high_priority,
                'is_business_developer': is_business_dev,
                'mentions_encryption': mentions_encryption,
                'index': index
            }
            
        except Exception as e:
            print(f"⚠️  Error extracting contributor {index}: {e}")
            return None
    
    def _extract_title_from_section(self, section: str) -> str:
        """Extract title from section"""
        # Look for the actual job title, not the answer content
        # The title usually appears right after the name in a specific HTML structure
        
        # First, try to find the title in the HTML structure - look for text after the name
        # Pattern: Look for text that contains job-related keywords and is substantial
        title_patterns = [
            r'<span[^>]*>([^<]*(?:Top AI Voice|Patent Filed|Founder|CEO|CTO|CFO|COO|President|Executive|Senior|Lead|Principal|Chief|VP|Director|Manager|Analyst|Engineer|Developer|Consultant|Advisor|Specialist|Expert|Architect|Scientist|Researcher|Professor|Digital transformation|Author|keynote speaker)[^<]*)</span>',
            r'<p[^>]*>([^<]*(?:Top AI Voice|Patent Filed|Founder|CEO|CTO|CFO|COO|President|Executive|Senior|Lead|Principal|Chief|VP|Director|Manager|Analyst|Engineer|Developer|Consultant|Advisor|Specialist|Expert|Architect|Scientist|Researcher|Professor|Digital transformation|Author|keynote speaker)[^<]*)</p>',
            r'>([^<]*(?:Top AI Voice|Patent Filed|Founder|CEO|CTO|CFO|COO|President|Executive|Senior|Lead|Principal|Chief|VP|Director|Manager|Analyst|Engineer|Developer|Consultant|Advisor|Specialist|Expert|Architect|Scientist|Researcher|Professor|Digital transformation|Author|keynote speaker)[^<]*)<'
        ]
        
        for pattern in title_patterns:
            matches = re.findall(pattern, section, re.IGNORECASE)
            for match in matches:
                match = match.strip()
                # Skip if it's just a name or very short, or contains HTML artifacts
                if (len(match) > 15 and 
                    not match.lower().startswith(('well said', 'spot on', 'thanks', 'agree', 'exactly')) and
                    not 'jpg"' in match and
                    not 'rotate(' in match and
                    not 'translateZ' in match):
                    return match
        
        # Fallback: look for any substantial text that looks like a title
        lines = section.split('\n')
        for line in lines:
            line = line.strip()
            if (len(line) > 20 and len(line) < 300 and  # Reasonable title length
                not 'jpg"' in line and
                not 'rotate(' in line and
                not 'translateZ' in line):
                if any(keyword in line.lower() for keyword in ['senior', 'lead', 'principal', 'chief', 'vp', 'director', 'manager', 'ceo', 'cto', 'cfo', 'coo', 'founder', 'president', 'executive', 'analyst', 'engineer', 'developer', 'consultant', 'advisor', 'specialist', 'expert', 'architect', 'scientist', 'researcher', 'professor', '@', '|', 'top ai voice', 'patent filed', 'digital transformation', 'author', 'keynote speaker']):
                    return line
        
        return "Professional"
    
    def _extract_title_from_lines(self, lines: List[str]) -> str:
        """Extract title from lines array"""
        # Look for the line that contains the title (usually after "Follow")
        for i, line in enumerate(lines):
            if 'Follow' in line and i + 1 < len(lines):
                return lines[i + 1]
        
        # Fallback: look for lines that look like titles
        for line in lines:
            if len(line) > 10 and any(keyword in line.lower() for keyword in ['senior', 'lead', 'chief', 'vp', 'director', 'manager', 'ceo', 'cto', 'founder', 'president', 'executive', 'analyst', 'engineer', 'developer', 'consultant', 'advisor', 'specialist', 'expert', 'architect', 'scientist', 'researcher', 'professor']):
                return line
        
        return "Professional"
    
    def _extract_title(self, section: str) -> str:
        """Extract job title from section"""
        # Look for common title patterns
        title_patterns = [
            r'(Senior|Lead|Principal|Chief|VP|Director|Manager|Head of|CEO|CTO|CFO|COO|Founder|Co-founder|President|Executive|Analyst|Engineer|Developer|Consultant|Advisor|Specialist|Expert|Architect|Scientist|Researcher|Professor|Dr\.|PhD|MBA|MSc|BSc)',
            r'@[A-Za-z0-9\s&]+',  # Company names after @
            r'\|[^|]+',  # Content after |
        ]
        
        for pattern in title_patterns:
            matches = re.findall(pattern, section)
            if matches:
                return ' '.join(matches[:3])  # Take first 3 matches
        
        # Fallback: look for lines that look like titles
        lines = section.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if len(line) > 10 and any(keyword in line.lower() for keyword in ['senior', 'lead', 'chief', 'vp', 'director', 'manager', 'ceo', 'cto', 'founder', 'president', 'executive', 'analyst', 'engineer', 'developer', 'consultant', 'advisor', 'specialist', 'expert', 'architect', 'scientist', 'researcher', 'professor']):
                return line
        
        return "Professional"
    
    def _extract_linkedin_url(self, section: str) -> str:
        """Extract LinkedIn profile URL"""
        # Look for LinkedIn URLs
        linkedin_patterns = [
            r'https://[a-z]{2}\.linkedin\.com/in/[a-zA-Z0-9\-]+',
            r'https://www\.linkedin\.com/in/[a-zA-Z0-9\-]+',
            r'linkedin\.com/in/[a-zA-Z0-9\-]+'
        ]
        
        for pattern in linkedin_patterns:
            matches = re.findall(pattern, section)
            if matches:
                url = matches[0]
                if not url.startswith('http'):
                    url = 'https://' + url
                return url
        
        return ""
    
    def _extract_answer(self, section: str) -> str:
        """Extract the contributor's answer - preserve complete content"""
        import re
        import html
        
        # First, look for structured content in <p class="c3"><span class="c6"> and <li class="c8 c3 li-bullet-0"><span class="c6">
        content_patterns = [
            r'<p class="c3"><span class="c6">(.*?)</span></p>',
            r'<li class="c8 c3 li-bullet-0"><span class="c6">(.*?)</span></li>'
        ]
        
        answer_parts = []
        
        # Find the contributor's name in this section first
        contributor_name_match = re.search(r'<a[^>]*>([^<]+?)(?:&#[0-9]+;|⚡)?Follow</a>', section)
        contributor_section_end = None
        
        if contributor_name_match:
            # Look for the next contributor or section boundary after this contributor
            name_end_pos = contributor_name_match.end()
            # Look for next "Contributor profile photo" or similar boundary
            next_contributor = re.search(r'Contributor profile photo|<img[^>]*alt="Contributor profile photo"', section[name_end_pos:])
            if next_contributor:
                contributor_section_end = name_end_pos + next_contributor.start()
        
        for pattern in content_patterns:
            matches = re.findall(pattern, section, re.DOTALL)
            for match in matches:
                # If we found a boundary, only include content before it
                if contributor_section_end:
                    match_pos = section.find(match)
                    if match_pos > contributor_section_end:
                        continue  # Skip content after this contributor's section
                
                # Decode HTML entities (like &#128269; for 🔍)
                decoded_text = html.unescape(match.strip())
                if len(decoded_text) > 10:  # Substantial content
                    # Skip obvious non-answer content (use more specific patterns)
                    skip_patterns = [
                        'replies from', 'copy link', 'report contribution', 'profile photo',
                        'contributor profile', 'google.com/url', 'Very professional structure',
                        'replied:', 'src=', 'img alt', 'protecting ai models: summary',
                        'model security', 'emerging techniques', 'like this post', 'follow me',
                        'celebrate this', 'support this', 'love this', 'insightful post'
                    ]
                    
                    if not any(skip in decoded_text.lower() for skip in skip_patterns):
                        answer_parts.append(decoded_text)
        
        # If we found structured content, use it (but limit to reasonable amount)
        if answer_parts:
            # Take only the first few parts to avoid mixed content
            limited_parts = answer_parts[:3]  # Limit to first 3 content blocks
            return ' '.join(limited_parts)
        
        # Fallback: General text extraction with better boundaries
        section_to_parse = section
        if contributor_section_end:
            section_to_parse = section[:contributor_section_end]
        
        # Remove HTML tags but preserve structure
        clean_text = re.sub(r'<[^>]+>', ' ', section_to_parse)
        
        # Decode HTML entities
        clean_text = html.unescape(clean_text)
        
        # Remove HTML artifacts and CSS properties
        clean_text = re.sub(r'[0-9]+rad\) translateZ\([0-9]+px\)', '', clean_text)
        clean_text = re.sub(r'[0-9]+\.[0-9]+px', '', clean_text)
        clean_text = re.sub(r'[0-9]+\.[0-9]+rad', '', clean_text)
        clean_text = re.sub(r'title=""', '', clean_text)
        clean_text = re.sub(r'style="[^"]*"', '', clean_text)
        clean_text = re.sub(r'width:|height:|margin-|transform:|webkit-|border:|display:|overflow:', '', clean_text)
        clean_text = re.sub(r'jpg"', '', clean_text)
        clean_text = re.sub(r'rotate\([^)]*\)', '', clean_text)
        clean_text = re.sub(r'translateZ\([^)]*\)', '', clean_text)
        
        # Clean up whitespace but preserve line breaks
        clean_text = re.sub(r'[ \t]+', ' ', clean_text)  # Multiple spaces/tabs to single space
        clean_text = re.sub(r'\n\s*\n', '\n', clean_text)  # Multiple newlines to single
        
        # Split into lines and filter meaningful content
        lines = [line.strip() for line in clean_text.split('\n')]
        answer_lines = []
        
        for line in lines:
            if len(line) > 15:  # Substantial content
                # Skip obvious non-answer content and summaries
                skip_patterns = [
                    'follow', 'like', 'celebrate', 'support', 'love', 'insightful', 'funny',
                    'replies from', 'copy link', 'report contribution', 'src=', 'style=',
                    'width:', 'height:', 'margin-', 'transform:', 'webkit-', 'border:',
                    'display:', 'overflow:', 'img alt', 'class=', 'translatez', 'px', 'rad',
                    'profile photo', 'contributor profile', 'google.com/url',
                    'protecting ai models: summary', 'model security', 'emerging techniques'
                ]
                
                if not any(skip in line.lower() for skip in skip_patterns):
                    # This looks like actual answer content
                    answer_lines.append(line)
        
        # Join meaningful lines with proper spacing, but limit length
        if answer_lines:
            # Take first few lines to avoid mixed content
            limited_lines = answer_lines[:5]  # Limit to first 5 lines
            full_answer = ' '.join(limited_lines)
            
            # Clean up any remaining artifacts
            full_answer = re.sub(r'\s+', ' ', full_answer)  # Normalize spaces
            full_answer = full_answer.strip()
            
            return full_answer if full_answer else "Contributor to AI security discussion"
        else:
            return "Contributor to AI security discussion"
    
    def _extract_likes(self, section: str) -> str:
        """Extract number of likes"""
        like_match = re.search(r'(\d+)\s*Like', section)
        return like_match.group(1) if like_match else "0"
    
    def _extract_replies(self, section: str) -> str:
        """Extract replies content"""
        # Look for various reply patterns
        reply_patterns = [
            r'Replies from ([^:]+): (.+)',
            r'Replies from ([^:]+) and more: (.+)',
            r'([^:]+) replied: (.+)',
            r'([^:]+) replied: (.+)',
        ]
        
        for pattern in reply_patterns:
            reply_match = re.search(pattern, section)
            if reply_match:
                return f"Replies from {reply_match.group(1)}: {reply_match.group(2)}"
        
        return ""
    
    def _extract_additional_contributors_from_replies(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract additional contributors from reply threads"""
        additional_contributors = []
        
        # Look for reply patterns that contain contributor information
        reply_patterns = [
            r'Replies from ([^:]+) and more: (.+?)(?=Contributor profile photo|$)',
            r'([^:]+) replied: (.+?)(?=Contributor profile photo|$)',
        ]
        
        for pattern in reply_patterns:
            matches = re.finditer(pattern, html_content, re.DOTALL)
            for match in matches:
                reply_author = match.group(1).strip()
                reply_content = match.group(2).strip()
                
                # Extract LinkedIn URL from the reply section
                linkedin_url_match = re.search(r'https://[a-z]{2}\.linkedin\.com/in/[a-zA-Z0-9\-]+', match.group(0))
                if not linkedin_url_match:
                    linkedin_url_match = re.search(r'https://www\.linkedin\.com/in/[a-zA-Z0-9\-]+', match.group(0))
                
                linkedin_url = linkedin_url_match.group(0) if linkedin_url_match else ""
                
                # Create contributor from reply
                contributor = {
                    'name': reply_author,
                    'title': "Professional (from reply thread)",
                    'linkedin_profile': linkedin_url,
                    'answer': reply_content[:200] + "..." if len(reply_content) > 200 else reply_content,
                    'likes': "0",
                    'replies': "",
                    'is_high_priority': self._is_high_priority(reply_author),
                    'is_business_developer': self._is_business_developer(reply_author),
                    'mentions_encryption': 'encryption' in reply_content.lower() or 'encrypt' in reply_content.lower(),
                    'index': len(additional_contributors) + 1000,  # Offset to distinguish from main contributors
                    'source': 'reply_thread'
                }
                
                additional_contributors.append(contributor)
        
        return additional_contributors
    
    def _remove_duplicates(self, contributors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate contributors and merge their comments"""
        contributor_map = {}  # Map core_url to contributor data
        
        for contributor in contributors:
            linkedin_url = contributor.get('linkedin_profile', '')
            
            # Extract the core LinkedIn profile ID (after /in/)
            core_url = ""
            if linkedin_url:
                url_match = re.search(r'/in/([a-zA-Z0-9\-]+)', linkedin_url)
                if url_match:
                    core_url = url_match.group(1)
            
            if core_url:
                if core_url in contributor_map:
                    # Merge with existing contributor
                    existing = contributor_map[core_url]
                    existing['comment_count'] = existing.get('comment_count', 1) + 1
                    existing['all_comments'].append(contributor.get('answer', ''))
                    existing['all_likes'] += int(contributor.get('likes', '0'))
                    existing['all_replies'].append(contributor.get('replies', ''))
                    
                    # Update engagement metrics
                    existing['total_engagement'] = existing.get('total_engagement', 0) + int(contributor.get('likes', '0'))
                    
                    # Keep the most detailed title
                    if len(contributor.get('title', '')) > len(existing.get('title', '')):
                        existing['title'] = contributor.get('title', '')
                    
                    # Update encryption mentions
                    if contributor.get('mentions_encryption', False):
                        existing['mentions_encryption'] = True
                        
                else:
                    # First time seeing this contributor
                    contributor['comment_count'] = 1
                    contributor['all_comments'] = [contributor.get('answer', '')]
                    contributor['all_likes'] = int(contributor.get('likes', '0'))
                    contributor['all_replies'] = [contributor.get('replies', '')]
                    contributor['total_engagement'] = int(contributor.get('likes', '0'))
                    contributor_map[core_url] = contributor
            else:
                # No LinkedIn URL, keep as is
                contributor['comment_count'] = 1
                contributor['all_comments'] = [contributor.get('answer', '')]
                contributor['all_likes'] = int(contributor.get('likes', '0'))
                contributor['all_replies'] = [contributor.get('replies', '')]
                contributor['total_engagement'] = int(contributor.get('likes', '0'))
                contributor_map[f"no_url_{len(contributor_map)}"] = contributor
        
        # Convert back to list and update the main answer field
        unique_contributors = []
        for contributor in contributor_map.values():
            # Combine all comments into the main answer field with proper spacing
            all_comments = [c for c in contributor.get('all_comments', []) if c and c != "Contributor to AI security discussion"]
            if all_comments:
                # Clean and separate comments with clear breaks
                cleaned_comments = []
                for comment in all_comments[:3]:  # Take first 3 comments
                    # Clean HTML artifacts and extra whitespace
                    cleaned = re.sub(r'<[^>]+>', '', comment)  # Remove HTML tags
                    cleaned = re.sub(r'\s+', ' ', cleaned)  # Normalize whitespace
                    cleaned = cleaned.strip()
                    if cleaned and len(cleaned) > 10:  # Only keep substantial comments
                        cleaned_comments.append(cleaned)
                
                # Join with clear separators
                if cleaned_comments:
                    contributor['answer'] = '\n\n---\n\n'.join(cleaned_comments)
                else:
                    contributor['answer'] = "Contributor to AI security discussion"
            else:
                contributor['answer'] = "Contributor to AI security discussion"
            
            # Update likes to show total
            contributor['likes'] = str(contributor.get('total_engagement', 0))
            
            # Add activity level indicator
            comment_count = contributor.get('comment_count', 1)
            if comment_count >= 3:
                contributor['activity_level'] = "Very Active"
            elif comment_count == 2:
                contributor['activity_level'] = "Active"
            else:
                contributor['activity_level'] = "Single Comment"
            
            unique_contributors.append(contributor)
        
        return unique_contributors
    
    def _is_high_priority(self, title: str) -> bool:
        """Check if contributor is high priority (C-level, VPs, Directors, Founders)"""
        title_lower = title.lower()
        high_priority_keywords = [
            'ceo', 'cto', 'cfo', 'coo', 'cdo', 'cpo', 'cmo', 'ciso', 'cso', 'chief',
            'president', 'founder', 'co-founder', 'vp', 'vice president', 'director',
            'head of', 'lead of', 'executive', 'manager', 'senior', 'principal',
            'board member', 'advisor', 'consultant'
        ]
        return any(keyword in title_lower for keyword in high_priority_keywords)
    
    def _is_business_developer(self, title: str) -> bool:
        """Check if contributor is in business development"""
        title_lower = title.lower()
        business_dev_keywords = [
            'business development', 'business dev', 'partnership', 'partnerships',
            'strategic', 'sales', 'marketing', 'growth', 'revenue', 'commercial',
            'client', 'customer', 'account', 'relationship', 'alliance'
        ]
        return any(keyword in title_lower for keyword in business_dev_keywords)
    
    def sort_by_relevance(self, contributors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort contributors by relevance - high-level positions and business developers first"""
        
        def relevance_score(contributor):
            title = contributor['title'].lower()
            
            # PRIMARY SORT: High priority first (1000+ points vs 0-999)
            if contributor.get('is_high_priority', False):
                base_score = 1000  # HIGH PRIORITY BASE
                
                # Further differentiate within high priority
                if any(keyword in title for keyword in ['ceo', 'cto', 'cfo', 'coo', 'chief', 'president']):
                    base_score = 1100  # C-level
                elif any(keyword in title for keyword in ['founder', 'co-founder']):
                    base_score = 1090  # Founders
                elif any(keyword in title for keyword in ['vp', 'vice president', 'director']):
                    base_score = 1080  # VPs/Directors
                elif any(keyword in title for keyword in ['manager', 'senior', 'principal']):
                    base_score = 1070  # Senior roles
                else:
                    base_score = 1050  # Other high priority
            else:
                base_score = 500   # NON-HIGH PRIORITY BASE
            
            # SECONDARY SORT: Business developers
            if contributor.get('is_business_developer', False):
                base_score += 20
            
            # TERTIARY SORT: Encryption mentions 
            encryption_bonus = 15 if contributor.get('mentions_encryption', False) else 0
            
            # QUATERNARY SORT: Activity level
            activity_level = contributor.get('activity_level', 'Single Comment')
            activity_bonus = 0
            if activity_level == "Very Active":
                activity_bonus = 10
            elif activity_level == "Active":
                activity_bonus = 5
            
            return base_score + encryption_bonus + activity_bonus
        
        return sorted(contributors, key=relevance_score, reverse=True)
    
    def generate_connection_message(self, contributor: Dict[str, Any]) -> str:
        """Generate personalized connection message (under 300 characters)"""
        name = contributor['name']
        
        # Extract first name only, clean up any extra characters
        first_name = name.split()[0] if name.split() else name
        # Remove any "Follow" or other LinkedIn artifacts
        first_name = re.sub(r'Follow$', '', first_name).strip()
        
        message = f"Dear {first_name}, I read your response to 'Your AI models face data privacy risks from external vendors. How can you protect their integrity?' - your insights resonated with me. I'm founder of AltaStata, an MIT startup focused on AI data security. Would love to connect. Best, Serge"
        
        # Ensure under 300 characters
        if len(message) > 300:
            message = f"Dear {first_name}, I read your response to the AI data privacy question - your insights resonated with me. I'm founder of AltaStata, an MIT startup focused on AI data security. Would love to connect. Best, Serge"
        
        return message
    
    def generate_follow_up_message(self, contributor: Dict[str, Any]) -> str:
        """Generate detailed follow-up message based on their actual comments"""
        name = contributor['name']
        title = contributor['title']
        answer = contributor['answer']
        
        # Extract first name only, clean up any extra characters
        first_name = name.split()[0] if name.split() else name
        first_name = re.sub(r'Follow$', '', first_name).strip()
        
        # Extract specific insights from their actual comments
        insights = self._extract_specific_insights(answer)
        
        # Create personalized message based on their actual content
        follow_up = f"""Dear {first_name},

Thanks for connecting! Your response to the AI data privacy question really resonated with me.

What particularly caught my attention was your emphasis on:
{insights}

Your insights align perfectly with what we're building at AltaStata, an MIT startup with cutting-edge patented encryption approach for AI data security.

We specifically address the challenges you mentioned, ensuring end-to-end data protection.

I'd love to get your perspective on the AI data security landscape.

Would you be open to a 15-minute call?

Best,
Serge"""
        
        return follow_up
    
    def _extract_specific_insights(self, answer: str) -> str:
        """Extract specific insights from the contributor's actual comments using AI analysis"""
        from langchain_google_vertexai import ChatVertexAI
        
        # Split by comment separators to get individual comments
        comments = [c.strip() for c in answer.split('---') if c.strip()]
        
        # Combine all comments into one text for AI analysis
        combined_text = ' '.join(comments)
        
        # Clean the text
        clean_text = re.sub(r'[^\w\s.,!?-]', '', combined_text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        if len(clean_text) < 20:
            return "• AI data security insights"
        
        try:
            # Initialize AI model for intelligent analysis
            llm = ChatVertexAI(
                model_name="gemini-2.5-flash",
                temperature=0.1,
                max_output_tokens=1000
            )
            
            # Use AI to understand and extract technical approaches
            prompt = f"""Extract ALL technical approaches mentioned in this text:

{clean_text[:1000]}

IMPORTANT: 
1. List encryption-related approaches FIRST
2. Then list all other technical approaches  
3. RESPECT "and" connectors (e.g., "data at rest and in transit" = keep as one approach)
4. AVOID duplicates and overly granular splits
5. Use this EXACT format:
• approach one
• approach two
• approach three
• etc.

RULES:
- When concepts are connected with "and" (e.g., "at rest and in transit"), keep them as ONE bullet point
- When concepts are mentioned separately, keep them as separate bullets
- Combine "assessments" and "compliance checks" into single "compliance monitoring" approach  
- Group similar vendor-related activities together
- Avoid repeating the same concept with slight word variations
- Do NOT use bold, italic, asterisks, colons, or explanatory text

Extract meaningful, distinct approaches only."""

            response = llm.invoke(prompt)
            ai_insights = response.content.strip()
            
            # Return the AI response directly (no post-processing needed)
            if ai_insights and len(ai_insights) > 10:
                return ai_insights
            else:
                return "• AI data security insights"
                
        except Exception as e:
            print(f"❌ AI insight extraction failed for text: {clean_text[:50]}... Error: {e}")
            return "• AI data security insights"
    
    def create_sorted_markdown(self, contributors: List[Dict[str, Any]], timestamp: str) -> str:
        """Create sorted markdown file with all contributors"""
        from datetime import datetime
        import os
        date_str = datetime.now().strftime("%Y-%m-%d")
        results_dir = f"results/{date_str}"
        os.makedirs(results_dir, exist_ok=True)
        filename = f"{results_dir}/linkedin_real_contributors_sorted_{timestamp}.md"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# LinkedIn Advice Post Contributors - Real Data (Sorted by Relevance)\n\n")
            f.write(f"**Source:** https://www.linkedin.com/advice/3/your-ai-models-face-data-privacy-risks-9hxfc\n")
            f.write(f"**Question:** Your AI models face data privacy risks from external vendors. How can you protect their integrity?\n")
            f.write(f"**Total Contributors:** {len(contributors)} (sorted by relevance - high-level positions first)\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            
            # Priority summary
            high_priority = len([c for c in contributors if c.get('is_high_priority', False)])
            business_dev = len([c for c in contributors if c.get('is_business_developer', False)])
            encryption_mentions = len([c for c in contributors if c.get('mentions_encryption', False)])
            
            f.write("## 🎯 Priority Summary\n\n")
            f.write(f"**High-Priority Contributors (C-level, VPs, Directors, Founders):** {high_priority}\n")
            f.write(f"**Business Developers & Consultants:** {business_dev}\n")
            f.write(f"**Contributors Mentioning Encryption:** {encryption_mentions}\n")
            f.write(f"**Total Contributors:** {len(contributors)}\n\n")
            
            # Individual contributors
            for i, contributor in enumerate(contributors, 1):
                priority_emoji = "🔥 HIGH PRIORITY" if contributor.get('is_high_priority', False) else "💼 BUSINESS DEV" if contributor.get('is_business_developer', False) else ""
                
                f.write(f"## Contributor {i}: {contributor['name']} {priority_emoji}\n\n")
                f.write(f"**LinkedIn Profile:** {contributor['linkedin_profile']}\n\n")
                f.write(f"**Title:** {contributor['title']}\n\n")
                f.write(f"**Engagement:** {contributor['likes']} likes\n\n")
                f.write(f"**Activity Level:** {contributor.get('activity_level', 'Single Comment')} ({contributor.get('comment_count', 1)} comments)\n\n")
                
                if contributor.get('mentions_encryption', False):
                    f.write("**🔐 Encryption Focus:** This contributor specifically mentioned encryption in their response\n\n")
                
                f.write("### 💬 Their Answer\n\n")
                f.write(f"> {contributor['answer']}\n\n")
                
                f.write("### 📨 Initial Connection Message\n\n")
                f.write("```\n")
                f.write(f"{self.generate_connection_message(contributor)}\n")
                f.write("```\n\n")
                
                f.write("### 📧 Follow-up Message (After Connection)\n\n")
                f.write("```\n")
                f.write(f"{self.generate_follow_up_message(contributor)}\n")
                f.write("```\n\n")
                f.write("---\n\n")
        
        return filename
    
    def create_csv_tracking_file(self, contributors: List[Dict[str, Any]], timestamp: str) -> str:
        """Create CSV tracking file for communication status"""
        from datetime import datetime
        import os
        date_str = datetime.now().strftime("%Y-%m-%d")
        results_dir = f"results/{date_str}"
        os.makedirs(results_dir, exist_ok=True)
        filename = f"{results_dir}/linkedin_real_contributors_tracking_{timestamp}.csv"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("Name,Title,LinkedIn Profile,Priority,Encryption Focus,Engagement,Activity Level,Comment Count,Connection Status,Follow-up Status,Notes\n")
            
            for contributor in contributors:
                priority = "HIGH" if contributor.get('is_high_priority', False) else "BUSINESS DEV" if contributor.get('is_business_developer', False) else "STANDARD"
                encryption_focus = "YES" if contributor.get('mentions_encryption', False) else "NO"
                activity_level = contributor.get('activity_level', 'Single Comment')
                comment_count = contributor.get('comment_count', 1)
                
                f.write(f'"{contributor["name"]}","{contributor["title"]}","{contributor["linkedin_profile"]}","{priority}","{encryption_focus}","{contributor["likes"]} likes","{activity_level}","{comment_count}","","",""\n')
        
        return filename


def main():
    """Main function to parse HTML and generate files"""
    print("🤖 LinkedIn HTML Parser - Extract Real Contributors")
    print("=" * 60)
    
    # Initialize parser
    parser = LinkedInHTMLParser("linkedin_advice_post.html")
    
    # Parse HTML file
    contributors = parser.parse_html_file()
    
    if not contributors:
        print("❌ No contributors found in HTML file")
        return
    
    # Sort by relevance
    sorted_contributors = parser.sort_by_relevance(contributors)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create sorted markdown file
    markdown_filename = parser.create_sorted_markdown(sorted_contributors, timestamp)
    
    # Create CSV tracking file
    csv_filename = parser.create_csv_tracking_file(sorted_contributors, timestamp)
    
    print(f"\n🎯 REAL CONTRIBUTORS SUMMARY:")
    print(f"   Contributors extracted: {len(sorted_contributors)}")
    print(f"   High-priority contributors: {len([c for c in sorted_contributors if c.get('is_high_priority', False)])}")
    print(f"   Business developers: {len([c for c in sorted_contributors if c.get('is_business_developer', False)])}")
    print(f"   Encryption mentions: {len([c for c in sorted_contributors if c.get('mentions_encryption', False)])}")
    print(f"   Markdown file: {markdown_filename}")
    print(f"   CSV tracking file: {csv_filename}")
    
    print(f"\n✅ REAL CONTRIBUTORS EXTRACTED AND SORTED BY RELEVANCE!")
    print(f"📖 High-priority contributors (C-level, VPs, Business Devs) are listed first!")
    print(f"📊 CSV file ready for tracking your communication status!")
    print(f"🚀 Ready for your prioritized LinkedIn outreach campaign!")


    def test_precise_extraction(self) -> None:
        """Test the precise extraction method for Akshay Sajeev specifically"""
        try:
            with open(self.html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            import re
            
            # Find all contributor patterns more precisely
            contributor_pattern = r'<a[^>]*href="[^"]*linkedin\.com/in/([^?"]+)[^"]*"[^>]*>([^<]+?)(?:&#[0-9]+;|⚡)?Follow</a>'
            
            matches = list(re.finditer(contributor_pattern, html_content))
            
            print(f"🔍 Found {len(matches)} contributor profiles with precise method")
            
            # Find Akshay specifically
            for i, match in enumerate(matches):
                linkedin_id = match.group(1)
                contributor_name = match.group(2)
                
                if 'akshay' in contributor_name.lower() and 'sajeev' in contributor_name.lower():
                    match_start = match.start()
                    match_end = match.end()
                    
                    print(f"\\n=== FOUND AKSHAY WITH PRECISE METHOD ===")
                    print(f"Contributor: {contributor_name}")
                    print(f"LinkedIn ID: {linkedin_id}")
                    print(f"Match position: {match_start} to {match_end}")
                    
                    # Find the content that belongs to this specific contributor
                    # Look for content between this contributor and the next one
                    next_match_start = len(html_content)  # Default to end of file
                    if i + 1 < len(matches):
                        next_match_start = matches[i + 1].start()
                        next_contributor = matches[i + 1].group(2)
                        print(f"Next contributor: {next_contributor} at position {next_match_start}")
                    
                    # Extract the section for this contributor only
                    contributor_section = html_content[match_start:next_match_start]
                    print(f"Section length: {len(contributor_section)} chars")
                    
                    # Extract answer from this precise section
                    answer = self._extract_answer(contributor_section)
                    print(f"Extracted answer length: {len(answer)} chars")
                    print(f"Answer: {answer[:300]}...")
                    print("=" * 60)
            
        except Exception as e:
            print(f"❌ Error in precise extraction test: {e}")

if __name__ == "__main__":
    main()
