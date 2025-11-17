"""
Cloudflare Challenge Solver Demo
Solves Cloudflare Challenge (5-second shield) using CapSolver API

Requirements:
- Static or Sticky proxy (MANDATORY - rotating proxies won't work)
- TLS fingerprinting, matching headers, header order, and User-Agent
- Chrome User-Agent recommended

Returns: cf_clearance cookie and token
"""

import requests
import time

# ============== CONFIGURATION ==============
# Your CapSolver API key from https://dashboard.capsolver.com
CAPSOLVER_API_KEY = "YOUR_API_KEY_HERE"

# Target website URL showing Cloudflare challenge ("Just a moment...")
WEBSITE_URL = "https://www.example.com"

# MANDATORY: Static or Sticky proxy (format: ip:port:user:pass or http://user:pass@host:port)
PROXY = "ip:port:user:pass"

# Optional: User-Agent (only Chrome is supported)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

# Optional: HTML content of the challenge page (helps with some websites)
# Scrape this using your sticky proxy - should contain "Just a moment..." with 403 status
HTML_CONTENT = ""  # Leave empty if not needed
# ============================================


def create_task(api_key, task_data):
    """
    Create a task on CapSolver
    """
    payload = {
        "clientKey": api_key,
        "task": task_data
    }
    
    response = requests.post("https://api.capsolver.com/createTask", json=payload)
    return response.json()


def get_task_result(api_key, task_id):
    """
    Get the result of a task from CapSolver
    """
    payload = {
        "clientKey": api_key,
        "taskId": task_id
    }
    
    response = requests.post("https://api.capsolver.com/getTaskResult", json=payload)
    return response.json()


def solve_cloudflare_challenge(api_key, website_url, proxy, user_agent=None, html=None):
    """
    Solve Cloudflare Challenge using CapSolver
    
    Args:
        api_key: CapSolver API key
        website_url: Target website URL
        proxy: Static/Sticky proxy (REQUIRED)
        user_agent: Chrome User-Agent (optional)
        html: Page HTML content (optional, helps with some sites)
    
    Returns:
        dict: Solution containing cf_clearance cookie, token, and userAgent
    """
    print("=" * 60)
    print("Cloudflare Challenge Solver")
    print("=" * 60)
    
    # Validate required parameters
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        raise ValueError("Please set your CapSolver API key")
    
    if not website_url:
        raise ValueError("Please set the target website URL")
    
    if not proxy:
        raise ValueError("Proxy is MANDATORY for Cloudflare Challenge. Use Static or Sticky proxy.")
    
    # Build task data
    task_data = {
        "type": "AntiCloudflareTask",
        "websiteURL": website_url,
        "proxy": proxy
    }
    
    # Add optional parameters
    if user_agent:
        task_data["userAgent"] = user_agent
    
    if html:
        task_data["html"] = html
    
    print(f"\n[1/3] Creating task...")
    print(f"  Website: {website_url}")
    print(f"  Proxy: {proxy[:20]}..." if len(proxy) > 20 else f"  Proxy: {proxy}")
    print(f"  User-Agent: {'Custom' if user_agent else 'Default'}")
    print(f"  HTML provided: {'Yes' if html else 'No'}")
    
    # Create task
    result = create_task(api_key, task_data)
    
    if result.get("errorId") != 0:
        raise Exception(f"Failed to create task: {result.get('errorDescription', 'Unknown error')}")
    
    task_id = result.get("taskId")
    print(f"  ✓ Task created: {task_id}")
    
    # Poll for result
    print(f"\n[2/3] Waiting for solution...")
    print("  This may take 2-20 seconds depending on the website and proxy...")
    
    max_attempts = 60
    attempt = 0
    
    while attempt < max_attempts:
        time.sleep(2)  # Check every 2 seconds
        attempt += 1
        
        result = get_task_result(api_key, task_id)
        status = result.get("status")
        
        if status == "ready":
            print(f"  ✓ Solution received after {attempt * 2} seconds!")
            return result.get("solution", {})
        
        elif status == "failed":
            error_desc = result.get("errorDescription", "Unknown error")
            raise Exception(f"Task failed: {error_desc}")
        
        elif status == "processing":
            print(f"  ... Processing (attempt {attempt}/{max_attempts})")
    
    raise Exception("Timeout: Failed to get solution within maximum time")


def print_important_notes():
    """
    Print critical information about using cf_clearance cookie
    """
    print("\n" + "=" * 70)
    print("IMPORTANT: Using cf_clearance Cookie")
    print("=" * 70)
    print("""
⚠️  CRITICAL REQUIREMENTS for using the cf_clearance cookie:

1. TLS Fingerprinting:
   - Use TLS client libraries (curl_cffi, tls-client, etc.)
   - Match Chrome browser TLS fingerprint
   - Standard requests library will likely fail

2. HTTP Headers:
   - Use realistic browser headers
   - Match the User-Agent returned by CapSolver (EXACT match)
   - Include common headers: Accept, Accept-Language, Accept-Encoding, etc.

3. Header Order:
   - Headers must be sent in browser-like order
   - Cloudflare checks header ordering
   - Use libraries that preserve header order

4. User-Agent Matching:
   - MUST use the EXACT User-Agent returned in solution
   - Don't modify or use a different User-Agent
   - Case-sensitive match required

5. Cookie Format:
   - Send as: Cookie: cf_clearance=VALUE
   - Include other cookies if present
   - Maintain cookie throughout session

Recommended Libraries:
  Python: curl_cffi, tls-client, httpx with custom TLS
  Node.js: tls-client, node-curl-impersonate
  Go: http2, cycletls

Without proper TLS fingerprinting and header matching,
the cf_clearance cookie will be rejected by Cloudflare.
""")


def extract_sitekey_guide():
    """
    Print a guide on how to extract the Turnstile sitekey (for reference)
    """
    print("\n" + "=" * 60)
    print("HOW TO FIND THE TURNSTILE SITEKEY")
    print("=" * 60)
    print("""
1. Open the target website in your browser
2. Right-click and select "Inspect" or press F12
3. Go to the "Elements" or "Inspector" tab
4. Press Ctrl+F (or Cmd+F on Mac) to search
5. Search for "cf-turnstile" or "turnstile"
6. Look for an element like:
   <div class="cf-turnstile" data-sitekey="0x4AAAAAAA..."></div>
7. Copy the value of data-sitekey attribute

Alternative method:
- View page source (Ctrl+U or Cmd+U)
- Search for "0x4" or "turnstile"
- Find the sitekey starting with "0x4"

The sitekey should look like:
  0x4AAAAAAABnKLw-gqLrKWEL (example)
""")


def main():
    try:
        # Solve the Cloudflare Challenge
        solution = solve_cloudflare_challenge(
            api_key=CAPSOLVER_API_KEY,
            website_url=WEBSITE_URL,
            proxy=PROXY,
            user_agent=USER_AGENT,
            html=HTML_CONTENT if HTML_CONTENT else None
        )
        
        # Print solution details
        print("\n" + "=" * 60)
        print("SOLUTION DETAILS")
        print("=" * 60)
        
        cf_clearance = solution.get("cookies", {}).get("cf_clearance")
        token = solution.get("token")
        user_agent = solution.get("userAgent")
        
        print(f"\ncf_clearance cookie:")
        print(f"  {cf_clearance}")
        
        print(f"\nToken:")
        print(f"  {token}")
        
        print(f"\nUser-Agent:")
        print(f"  {user_agent}")
        
        print_important_notes()
        
        print("\n" + "=" * 60)
        print("COMPLETE")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
