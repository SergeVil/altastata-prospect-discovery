"""
Main script to run the AltaStata prospect discovery workflow
"""
import json
import pandas as pd
from datetime import datetime
from workflow import AISecurityPaperWorkflow
import config

def generate_prospects_files(results: dict, good_filename: str, other_filename: str, timestamp: str):
    """Generate separate markdown files for good prospects (with LinkedIn) and other prospects"""
    prospects = results.get('generated_emails', [])
    
    if not prospects:
        print("No prospects found to generate files")
        return
    
    # Separate prospects into good (all prospects) and other (papers without individual authors)
    good_prospects = prospects  # All prospects are "good prospects"
    
    # Get all papers from the analysis to find the "other" papers (without individual authors)
    all_papers = results.get('papers_analyzed', [])
    other_prospects = []
    
    for paper_analysis in all_papers:
        paper_metadata = paper_analysis.get('paper_metadata', {})
        author_info = paper_metadata.get('author_info', {})
        all_authors = author_info.get('all_authors', [])
        
        # Check if any of the authors are individual
        has_individual_author = False
        for author in all_authors:
            if author.get('is_individual', False):
                has_individual_author = True
                break
        
        # If no individual authors found, add to other prospects
        if not has_individual_author:
            other_prospect = {
                'paper_title': paper_metadata.get('title', ''),
                'paper_url': paper_metadata.get('url', ''),
                'paper_source': paper_metadata.get('display_url', ''),
                'author_info': author_info,
                'compatibility_analysis': author_info.get('compatibility_analysis', '')
            }
            other_prospects.append(other_prospect)
    
    # Generate good prospects file
    with open(good_filename, 'w', encoding='utf-8') as f:
        f.write("# 🎯 Good Prospects - All Individual Authors Found\n")
        f.write(f"## Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n")
        
        f.write("## 📊 **All Prospects with Individual Authors**\n\n")
        f.write(f"**Total: {len(good_prospects)} prospects with individual authors**\n\n")
        
        for i, prospect in enumerate(good_prospects, 1):
            author_info = prospect.get('author_info', {})
            author_name = author_info.get('name', 'Unknown')
            author_title = author_info.get('title', 'Professional')
            author_company = author_info.get('company', 'Not specified')
            linkedin_profile = author_info.get('linkedin_profile', 'Not found')
            email = author_info.get('email', '')
            paper_title = prospect.get('paper_title', '')
            paper_url = prospect.get('paper_url', '')
            paper_source = prospect.get('paper_source', '')
            linkedin_messages = prospect.get('linkedin_messages', {})
            
            f.write(f"### **✅ Prospect {i}: {author_name}**\n")
            f.write(f"- **Name:** {author_name}\n")
            f.write(f"- **Title:** {author_title}\n")
            f.write(f"- **Company:** {author_company}\n")
            f.write(f"- **LinkedIn Profile:** {linkedin_profile}\n")
            f.write(f"- **Email:** {email}\n")
            f.write(f"- **Paper:** \"{paper_title}\"\n")
            f.write(f"- **Paper URL:** {paper_url}\n")
            f.write(f"- **Source:** {paper_source}\n\n")
            
            # Add LinkedIn messages (generate if missing)
            if not linkedin_messages or not linkedin_messages.get('connection_request'):
                # Generate LinkedIn messages since they're missing
                author_name = author_info.get('name', '')
                paper_title = prospect.get('paper_title', '')
                paper_url = prospect.get('paper_url', '')
                
                # Extract key points for connection request
                points = []
                if "encryption" in compatibility.lower():
                    points.append("encryption")
                if "zero-trust" in compatibility.lower() or "zero trust" in compatibility.lower():
                    points.append("Zero Trust")
                if "data integrity" in compatibility.lower():
                    points.append("data integrity")
                
                # Get first name only
                first_name = author_name.split()[0] if author_name else author_name
                
                # Generate connection request (under 300 chars)
                if points:
                    points_text = ", ".join(points[:2])
                    connection_request = f"Hi {first_name}, I read your article on {paper_title} - your insights on {points_text} resonated with me. I'm working with AltaStata, an MIT-founded startup focused on AI data security. Would love to connect and exchange ideas. Best, Serge"
                else:
                    connection_request = f"Hi {first_name}, I read your article on {paper_title} - really insightful points about AI security. I'm working with AltaStata, an MIT-founded startup focused on AI data security. Would love to connect and exchange ideas. Best, Serge"
                
                # Ensure under 300 characters
                if len(connection_request) > 300:
                    connection_request = f"Hi {first_name}, I read your article on {paper_title} - your insights resonated with me. I'm working with AltaStata, an MIT-founded startup focused on AI data security. Would love to connect. Best, Serge"
                
                # Generate follow-up message
                company = author_info.get('company', 'your company')
                if not company or company == 'Not specified':
                    company = 'your organization'
                
                follow_up_message = f"""Hi {first_name},

Thanks for connecting! I read your article on "{paper_title}" - really insightful points about AI security challenges.

{compatibility}

What resonated with me is how your recommendations align perfectly with what we're building at AltaStata. We're an MIT-founded startup that helps companies implement exactly the security framework you outlined.

Would you be open to a brief 15-minute call to discuss how we're addressing the same AI security challenges you outlined in your article?

Best,
Serge

P.S. I'd love to hear your thoughts on how companies like {company} are implementing these AI security recommendations in practice."""

                linkedin_messages = {
                    'connection_request': connection_request,
                    'follow_up_message': follow_up_message
                }
            
            # Now write the LinkedIn messages
            if linkedin_messages:
                f.write("**🔗 LinkedIn Connection Request:**\n")
                f.write(f"```\n{linkedin_messages.get('connection_request', 'Not generated')}\n```\n\n")
                
                f.write("**📧 LinkedIn Follow-up Message:**\n")
                f.write(f"```\n{linkedin_messages.get('follow_up_message', 'Not generated')}\n```\n\n")
            
            
            f.write("---\n\n")
        
        f.write(f"\nGenerated from search run: {timestamp}\n")
    
    # Generate other prospects file
    with open(other_filename, 'w', encoding='utf-8') as f:
        f.write("# 📋 Other Papers - No Individual Authors Found\n")
        f.write(f"## Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n")
        
        f.write("## 📊 **Papers Without Individual Authors**\n\n")
        f.write(f"**Total: {len(other_prospects)} papers without individual authors**\n\n")
        
        for i, paper in enumerate(other_prospects, 1):
            paper_title = paper.get('paper_title', '')
            paper_url = paper.get('paper_url', '')
            paper_source = paper.get('paper_source', '')
            author_info = paper.get('author_info', {})
            author_name = author_info.get('name', 'No individual author found')
            compatibility_analysis = paper.get('compatibility_analysis', '')
            
            f.write(f"### **📄 Paper {i}: {paper_title[:60]}...**\n")
            f.write(f"- **Paper Title:** {paper_title}\n")
            f.write(f"- **Paper URL:** {paper_url}\n")
            f.write(f"- **Source:** {paper_source}\n")
            f.write(f"- **Author:** {author_name}\n")
            f.write(f"- **Status:** No individual author identified\n\n")
            
            
            f.write("---\n\n")
        
        f.write(f"\nGenerated from search run: {timestamp}\n")
    
    print(f"Good prospects file generated: {good_filename}")
    print(f"Other prospects file generated: {other_filename}")

def generate_linkedin_prospects_file(results: dict, filename: str, timestamp: str):
    """Legacy function - kept for compatibility"""
    # This function is now deprecated, use generate_prospects_files instead
    pass

def save_results_to_files(results: dict, timestamp: str):
    """Save results to JSON and CSV files in date-organized directories"""
    import os
    from datetime import datetime
    
    # Create date-based directory structure
    date_str = datetime.now().strftime("%Y-%m-%d")
    date_dir = f"results/{date_str}"
    os.makedirs(date_dir, exist_ok=True)
    
    # Save complete results as JSON
    json_filename = f"{date_dir}/ai_security_analysis_{timestamp}.json"
    
    # Clean circular references before JSON serialization
    def clean_for_json(obj):
        if isinstance(obj, dict):
            cleaned = {}
            for key, value in obj.items():
                # Skip circular references
                if key == 'all_authors':
                    # Convert all_authors to a simple list without circular refs
                    if isinstance(value, list):
                        cleaned[key] = [
                            {
                                'name': author.get('name', ''),
                                'title': author.get('title', ''),
                                'company': author.get('company', ''),
                                'linkedin_profile': author.get('linkedin_profile', ''),
                                'email': author.get('email', ''),
                                'profile_summary': author.get('profile_summary', ''),
                                'compatibility_analysis': author.get('compatibility_analysis', ''),
                                'is_individual': author.get('is_individual', False)
                            }
                            for author in value if isinstance(author, dict)
                        ]
                    else:
                        cleaned[key] = []
                else:
                    cleaned[key] = clean_for_json(value)
            return cleaned
        elif isinstance(obj, list):
            return [clean_for_json(item) for item in obj]
        else:
            return obj
    
    cleaned_results = clean_for_json(results)
    
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(cleaned_results, f, indent=2, ensure_ascii=False)
    print(f"📄 Complete results saved to: {json_filename}")
    
    # Save prospects as CSV for easy review
    if results.get('generated_emails'):  # Keep the same key for compatibility
        prospects_data = []
        for prospect in results['generated_emails']:
            author_info = prospect.get('author_info', {})
            linkedin_messages = prospect.get('linkedin_messages', {})
            
            # Generate LinkedIn messages if missing
            if not linkedin_messages or not linkedin_messages.get('connection_request'):
                author_name = author_info.get('name', '')
                paper_title = prospect.get('paper_title', '')
                compatibility = prospect.get('compatibility_analysis', '')
                
                # Handle compatibility as string
                if isinstance(compatibility, list):
                    compatibility = ' '.join(str(x) for x in compatibility)
                elif not isinstance(compatibility, str):
                    compatibility = str(compatibility)
                
                # Extract key points for connection request
                points = []
                if "encryption" in compatibility.lower():
                    points.append("encryption")
                if "zero-trust" in compatibility.lower() or "zero trust" in compatibility.lower():
                    points.append("Zero Trust")
                if "data integrity" in compatibility.lower():
                    points.append("data integrity")
                
                # Get first name only
                first_name = author_name.split()[0] if author_name else author_name
                
                # Generate connection request (under 300 chars)
                if points:
                    points_text = ", ".join(points[:2])
                    connection_request = f"Hi {first_name}, I read your article on {paper_title} - your insights on {points_text} resonated with me. I'm working with AltaStata, an MIT-founded startup focused on AI data security. Would love to connect and exchange ideas. Best, Serge"
                else:
                    connection_request = f"Hi {first_name}, I read your article on {paper_title} - really insightful points about AI security. I'm working with AltaStata, an MIT-founded startup focused on AI data security. Would love to connect and exchange ideas. Best, Serge"
                
                # Ensure under 300 characters
                if len(connection_request) > 300:
                    connection_request = f"Hi {first_name}, I read your article on {paper_title} - your insights resonated with me. I'm working with AltaStata, an MIT-founded startup focused on AI data security. Would love to connect. Best, Serge"
                
                # Generate follow-up message
                company = author_info.get('company', 'your company')
                follow_up_message = f"""Hi {first_name},

Thanks for connecting! I read your article on "{paper_title}" - really insightful points about AI security challenges.

{compatibility}

What resonated with me is how your recommendations align perfectly with what we're building at AltaStata. We're an MIT-founded startup that helps companies implement exactly the security framework you outlined.

Would you be open to a brief 15-minute call to discuss how we're addressing the same AI security challenges you outlined in your article?

Best,
Serge

P.S. I'd love to hear your thoughts on how companies like {company} are implementing these AI security recommendations in practice."""

                linkedin_messages = {
                    'connection_request': connection_request,
                    'follow_up_message': follow_up_message
                }
            
            prospects_data.append({
                'author_name': author_info.get('name', ''),
                'author_title': author_info.get('title', ''),
                'author_company': author_info.get('company', ''),
                'linkedin_profile': author_info.get('linkedin_profile', ''),
                'email': author_info.get('email', ''),
                'paper_title': prospect.get('paper_title', ''),
                'paper_source': prospect.get('paper_source', ''),
                'paper_url': prospect.get('paper_url', ''),
                'compatibility_analysis': prospect.get('compatibility_analysis', ''),
                'linkedin_connection_request': linkedin_messages.get('connection_request', ''),
                'linkedin_follow_up_message': linkedin_messages.get('follow_up_message', '')
            })
        
        if prospects_data:
            df = pd.DataFrame(prospects_data)
            csv_filename = f"{date_dir}/prospects_{timestamp}.csv"
            df.to_csv(csv_filename, index=False, encoding='utf-8')
            print(f"📊 Prospects CSV saved to: {csv_filename}")
            
            # Generate ONLY the enhanced version with LinkedIn messages
            prospects_filename = f"{date_dir}/good_prospects_with_messages_{timestamp}.md"
            generate_enhanced_prospects_file(results, prospects_filename)
            print(f"✨ Prospects with LinkedIn messages saved to: {prospects_filename}")
            
            # Generate other prospects file (papers without individual authors)
            other_prospects_filename = f"{date_dir}/other_prospects_ready_{timestamp}.md"
            generate_other_prospects_file(results, other_prospects_filename, timestamp)
            print(f"📋 Other prospects (need manual research) saved to: {other_prospects_filename}")

def _generate_linkedin_messages_inline(author_name: str, paper_title: str, compatibility_analysis: str, author_info: dict) -> dict:
    """Generate LinkedIn connection and follow-up messages based on paper content"""
    from workflow import AISecurityPaperWorkflow
    
    # Handle both string and list formats for compatibility_analysis
    if isinstance(compatibility_analysis, list):
        compatibility_analysis = ' '.join(str(x) for x in compatibility_analysis)
    
    # Create a workflow instance to use the proper LinkedIn message generation
    workflow = AISecurityPaperWorkflow()
    
    # Use the original sophisticated LinkedIn message generation
    try:
        return workflow._generate_linkedin_messages(author_name, paper_title, compatibility_analysis, author_info)
    except Exception as e:
        print(f"Error generating LinkedIn messages for {author_name}: {e}")
        # Fallback to simpler version if workflow method fails
        first_name = author_name.split()[0] if author_name else 'there'
        
        connection_request = f"Hi {first_name}, I read your article on {paper_title} - really insightful points about AI security. I'm working with AltaStata, an MIT-founded startup focused on AI data security. Would love to connect and exchange ideas. Best, Serge"
        
        if len(connection_request) > 300:
            connection_request = f"Hi {first_name}, I read your article on {paper_title} - your insights resonated with me. I'm working with AltaStata, an MIT-founded startup focused on AI data security. Would love to connect. Best, Serge"
        
        company = author_info.get('company', 'your company')
        if not company or company == 'Not specified':
            company = 'your organization'
        
        follow_up_message = f"""Hi {first_name},

Thanks for connecting! I read your article on "{paper_title}" - really insightful points about AI security challenges.

{compatibility_analysis}

What resonated with me is how your recommendations align perfectly with what we're building at AltaStata. We're an MIT-founded startup that helps companies implement exactly the security framework you outlined.

Would you be open to a brief 15-minute call to discuss how we're addressing the same AI security challenges you outlined in your article?

Best,
Serge

P.S. I'd love to hear your thoughts on how companies like {company} are implementing these AI security recommendations in practice."""

        return {
            'connection_request': connection_request,
            'follow_up_message': follow_up_message
        }

def generate_enhanced_prospects_file(results: dict, filename: str):
    """Generate enhanced markdown file with guaranteed LinkedIn messages"""
    
    prospects = results.get('generated_emails', [])
    
    if not prospects:
        print("No prospects found for enhanced file!")
        return
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("# 🎯 Good Prospects - With LinkedIn Messages\n")
        f.write(f"## Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n")
        f.write(f"**Total: {len(prospects)} prospects with individual authors**\n\n")
        
        for i, prospect in enumerate(prospects, 1):
            author_info = prospect.get('author_info', {})
            author_name = author_info.get('name', 'Unknown')
            paper_title = prospect.get('paper_title', '')
            paper_url = prospect.get('paper_url', '')
            paper_source = prospect.get('paper_source', '')
            compatibility_analysis = prospect.get('compatibility_analysis', '')
            
            # Generate LinkedIn messages inline
            linkedin_messages = _generate_linkedin_messages_inline(author_name, paper_title, compatibility_analysis, author_info)
            
            f.write(f"### **✅ Prospect {i}: {author_name}**\n")
            f.write(f"- **Name:** {author_name}\n")
            f.write(f"- **Title:** {author_info.get('title', '')}\n")
            f.write(f"- **Company:** {author_info.get('company', '')}\n")
            f.write(f"- **LinkedIn Profile:** {author_info.get('linkedin_profile', 'Not found')}\n")
            f.write(f"- **Email:** {author_info.get('email', '')}\n")
            f.write(f"- **Paper:** \"{paper_title}\"\n")
            f.write(f"- **Paper URL:** {paper_url}\n")
            f.write(f"- **Source:** {paper_source}\n\n")
            
            
            # Add LinkedIn messages
            f.write("**🔗 LinkedIn Connection Request:**\n")
            f.write(f"```\n{linkedin_messages['connection_request']}\n```\n\n")
            
            f.write("**📧 LinkedIn Follow-up Message:**\n")
            f.write(f"```\n{linkedin_messages['follow_up_message']}\n```\n\n")
            
            f.write("---\n\n")

def generate_other_prospects_file(results: dict, filename: str, timestamp: str):
    """Generate markdown file for papers without individual authors"""
    prospects = results.get('generated_emails', [])
    papers_analyzed = results.get('papers_analyzed', [])
    
    # Find papers without individual authors
    other_prospects = []
    
    for paper in papers_analyzed:
        paper_metadata = paper.get('paper_metadata', {})
        author_info = paper_metadata.get('author_info', {})
        all_authors = author_info.get('all_authors', [])
        
        # Check if any of the authors are individual
        has_individual_author = False
        for author in all_authors:
            if author.get('is_individual', False):
                has_individual_author = True
                break
        
        # If no individual authors found, add to other prospects
        if not has_individual_author:
            other_prospects.append({
                'paper_title': paper_metadata.get('title', ''),
                'paper_url': paper_metadata.get('url', ''),
                'paper_source': paper_metadata.get('display_url', ''),
                'author_info': author_info,
                'compatibility_analysis': author_info.get('compatibility_analysis', '')
            })
    
    if other_prospects:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# 📋 Other Papers (No Individual Authors)\n")
            f.write(f"## Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n")
            f.write(f"**Total: {len(other_prospects)} papers without individual authors**\n\n")
            
            for i, prospect in enumerate(other_prospects, 1):
                author_info = prospect.get('author_info', {})
                
                f.write(f"### **📄 Paper {i}: {prospect.get('paper_title', 'Unknown Title')}**\n")
                f.write(f"- **Author/Organization:** {author_info.get('name', 'Not specified')}\n")
                f.write(f"- **Title:** {author_info.get('title', 'Not specified')}\n")
                f.write(f"- **Company:** {author_info.get('company', 'Not specified')}\n")
                f.write(f"- **Paper URL:** {prospect.get('paper_url', '')}\n")
                f.write(f"- **Source:** {prospect.get('paper_source', '')}\n\n")
                
                
                f.write("---\n\n")

def print_summary(results: dict):
    """Print a summary of the results"""
    print("\n" + "="*60)
    print("📋 WORKFLOW RESULTS SUMMARY")
    print("="*60)
    
    papers_found = len(results.get('papers_found', []))
    papers_analyzed = len(results.get('papers_analyzed', []))
    prospects_found = len(results.get('generated_emails', []))
    
    print(f"Papers Found: {papers_found}")
    print(f"Papers Analyzed: {papers_analyzed}")
    print(f"Prospects Found: {prospects_found}")
    
    if results.get('error_message'):
        print(f"⚠️ Errors: {results['error_message']}")
    
    print("\n🎯 FOUND PROSPECTS:")
    print("-" * 40)
    
    for i, prospect in enumerate(results.get('generated_emails', []), 1):
        author_info = prospect.get('author_info', {})
        linkedin_messages = prospect.get('linkedin_messages', {})
        
        print(f"\n{i}. Author: {author_info.get('name', 'Unknown')}")
        print(f"   Title: {author_info.get('title', 'Professional')}")
        print(f"   Company: {author_info.get('company', 'Not specified')}")
        print(f"   LinkedIn: {author_info.get('linkedin_profile', 'Not found')}")
        print(f"   Paper: {prospect.get('paper_title', '')[:60]}...")
        print(f"   Source: {prospect.get('paper_source', '')}")
        
        # Show LinkedIn messages if available
        if linkedin_messages:
            print(f"   📝 Connection Request: {linkedin_messages.get('connection_request', 'Not generated')[:80]}...")
            print(f"   📧 Follow-up Message: {linkedin_messages.get('follow_up_message', 'Not generated')[:80]}...")
    
    print("\n" + "="*60)

def main():
    """Main function to run the workflow"""
    print("🤖 AltaStata Prospect Discovery")
    print("=" * 50)
    
    # Create results directory
    import os
    os.makedirs('results', exist_ok=True)
    
    # Initialize workflow
    workflow = AISecurityPaperWorkflow()
    
    # Get timestamp for file naming
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Run the workflow
    results = workflow.run_workflow()
    
    # Save results
    save_results_to_files(results, timestamp)
    
    # Print summary
    print_summary(results)
    
    return results

def run_company_specific_analysis(company_domain: str):
    """Run analysis for a specific company"""
    print(f"🏢 Running analysis for: {company_domain}")
    print("=" * 50)
    
    # Create results directory
    import os
    os.makedirs('results', exist_ok=True)
    
    # Initialize workflow
    workflow = AISecurityPaperWorkflow()
    
    # Run company-specific analysis
    results = workflow.run_single_company_analysis(company_domain)
    
    if 'error' in results:
        print(f"❌ {results['error']}")
        return
    
    # Get timestamp for file naming
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save results
    save_results_to_files(results, f"{company_domain}_{timestamp}")
    
    # Print summary
    print_summary(results)
    
    return results

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Company-specific analysis
        company_domain = sys.argv[1]
        results = run_company_specific_analysis(company_domain)
    else:
        # General analysis
        results = main()
    
    print("\n✅ Prospect discovery complete!")
