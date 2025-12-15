"""
LinkedIn Job Scraper - Main entry point
Scrapes jobs from LinkedIn based on configurable job title and time filter
"""
import json
import time
import argparse
from linkedin_scraper import LinkedInScraper
from job_parser import extract_required_years


def main(job_title="software developer", time_seconds=3600):
    """Main function to orchestrate the LinkedIn job scraping"""
    print("=" * 60)
    print(f"LinkedIn Job Scraper")
    print(f"Job Title: {job_title}")
    print(f"Time Filter: {time_seconds} seconds ({time_seconds // 3600}h {(time_seconds % 3600) // 60}m)")
    print("=" * 60)
    
    scraper = None
    jobs = []
    
    try:
        # Initialize scraper (set headless=True for no browser window)
        print("\n[1/5] Initializing browser...")
        scraper = LinkedInScraper(headless=False, job_title=job_title, time_seconds=time_seconds)
        
        # Login to LinkedIn
        print("\n[2/5] Logging into LinkedIn...")
        if not scraper.login():
            print("ERROR: Failed to login to LinkedIn")
            return
        
        print("\nLogin successful! Waiting a moment before searching...")
        time.sleep(3)
        
        # Navigate to job search
        print(f"\n[3/5] Searching for '{job_title}' jobs...")
        if not scraper.search_jobs():
            print("ERROR: Failed to load job search page")
            return
        
        # Scroll to load all jobs
        print("\n[4/5] Loading all job listings...")
        scraper.scroll_job_list()
        
        # Get job listings
        print("\n[5/5] Extracting job data...")
        job_listings = scraper.get_job_listings()
        
        print(f"\nFound {len(job_listings)} jobs")
        
        # Extract detailed information for each job
        for i, job in enumerate(job_listings):
            print(f"  Processing job {i+1}/{len(job_listings)}: {job.get('job_title', 'Unknown')}")
            
            # Get job description to extract required years
            description = scraper.get_job_details(job['job_id'])
            
            if description:
                job['required_years'] = extract_required_years(description)
            
            # If title is Unknown, try to get it from the job page
            if job.get('job_title') == 'Unknown':
                page_title = scraper.get_job_title_from_page()
                if page_title:
                    job['job_title'] = page_title
                    print(f"    -> Found title: {page_title}")
            
            jobs.append(job)
            
            # Small delay to avoid rate limiting
            time.sleep(1)
        
        # Save to JSON
        output_file = "jobs.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(jobs, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'=' * 60}")
        print(f"SUCCESS! Saved {len(jobs)} jobs to {output_file}")
        print(f"{'=' * 60}")
        
        # Print summary
        print("\nJob Summary:")
        for job in jobs:
            print(f"  - {job['job_title']} | {job['required_years']} | {job['link']}")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if scraper:
            input("\nPress Enter to close the browser...")
            scraper.close()


def test_login_only():
    """Test only the login functionality"""
    print("=" * 60)
    print("Testing LinkedIn Login")
    print("=" * 60)
    
    scraper = None
    try:
        scraper = LinkedInScraper(headless=False)
        success = scraper.login()
        
        if success:
            print("\n=== LOGIN TEST PASSED ===")
            print(f"Current URL: {scraper.driver.current_url}")
        else:
            print("\n=== LOGIN TEST FAILED ===")
            
        return success
        
    except Exception as e:
        print(f"Error: {e}")
        return False
        
    finally:
        if scraper:
            input("\nPress Enter to close the browser...")
            scraper.close()


def test_job_search(job_title="software developer", time_seconds=3600):
    """Test login and job search without extracting all details"""
    print("=" * 60)
    print(f"Testing LinkedIn Job Search: '{job_title}' (last {time_seconds}s)")
    print("=" * 60)
    
    scraper = None
    try:
        scraper = LinkedInScraper(headless=False, job_title=job_title, time_seconds=time_seconds)
        
        # Login
        print("\n[1/3] Logging in...")
        if not scraper.login():
            print("Login failed!")
            return
        
        time.sleep(3)
        
        # Search jobs
        print("\n[2/3] Navigating to job search...")
        if not scraper.search_jobs():
            print("Job search failed!")
            return
        
        # Get listings
        print("\n[3/3] Getting job listings...")
        scraper.scroll_job_list()
        jobs = scraper.get_job_listings()
        
        print(f"\n=== FOUND {len(jobs)} JOBS ===")
        for job in jobs[:10]:  # Show first 10
            print(f"  - {job['job_id']}: {job['job_title']}")
        
        if len(jobs) > 10:
            print(f"  ... and {len(jobs) - 10} more")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if scraper:
            input("\nPress Enter to close the browser...")
            scraper.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="LinkedIn Job Scraper - Scrape jobs based on title and time filter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --title "software developer" --time 3600
  python main.py --title "data engineer" --time 86400
  python main.py login
  python main.py search --title "python developer"
  
Time filter values:
  3600   = 1 hour
  86400  = 24 hours
  604800 = 1 week
        """
    )
    
    parser.add_argument("command", nargs="?", default="run",
                        choices=["run", "login", "search"],
                        help="Command to execute (default: run)")
    parser.add_argument("--title", "-t", type=str, default="software developer",
                        help="Job title to search (default: 'software developer')")
    parser.add_argument("--time", "-s", type=int, default=3600,
                        help="Time filter in seconds (default: 3600 = 1 hour)")
    
    args = parser.parse_args()
    
    if args.command == "login":
        test_login_only()
    elif args.command == "search":
        test_job_search(job_title=args.title, time_seconds=args.time)
    else:
        main(job_title=args.title, time_seconds=args.time)

