"""
Cloudflare Turnstile Solver Demo
Solves all Cloudflare Turnstile types (Manual, Non-Interactive, Invisible) using CapSolver API

Requirements:
- No proxy required (ProxyLess)
- Website Key (sitekey) - starts with 0x4...

Returns: Solution token
"""

import requests
import time

# ============== CONFIGURATION ==============
# Your CapSolver API key from https://dashboard.capsolver.com
CAPSOLVER_API_KEY = "YOUR_API_KEY_HERE"

# Target website URL containing Turnstile
WEBSITE_URL = "https://www.example.com"

# Turnstile website key (sitekey) - starts with 0x4...
# Find it in the page source: <div class="cf-turnstile" data-sitekey="0x4AAAAAAA..."></div>
WEBSITE_KEY = "0x4XXXXXXXXXXXXXXXXX"

# Optional: Metadata parameters (if present in the Turnstile element)
# data-action attribute value
METADATA_ACTION = ""  # e.g., "login", "submit", etc.

# data-cdata attribute value
METADATA_CDATA = ""  # e.g., "0000-1111-2222-3333-example-cdata"
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


def solve_turnstile(api_key, website_url, website_key, metadata_action=None, metadata_cdata=None):
    """
    Solve Cloudflare Turnstile using CapSolver
    
    Args:
        api_key: CapSolver API key
        website_url: Target website URL
        website_key: Turnstile sitekey (starts with 0x4...)
        metadata_action: Optional action parameter
        metadata_cdata: Optional cdata parameter
    
    Returns:
        dict: Solution containing token and userAgent
    """
    print("=" * 60)
    print("Cloudflare Turnstile Solver")
    print("=" * 60)
    
    # Validate required parameters
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        raise ValueError("Please set your CapSolver API key")
    
    if not website_url:
        raise ValueError("Please set the target website URL")
    
    if not website_key or website_key == "0x4XXXXXXXXXXXXXXXXX":
        raise ValueError("Please set the Turnstile website key (sitekey)")
    
    # Build task data
    task_data = {
        "type": "AntiTurnstileTaskProxyLess",
        "websiteURL": website_url,
        "websiteKey": website_key
    }
    
    # Add optional metadata
    metadata = {}
    if metadata_action:
        metadata["action"] = metadata_action
    if metadata_cdata:
        metadata["cdata"] = metadata_cdata
    
    if metadata:
        task_data["metadata"] = metadata
    
    print(f"\n[1/3] Creating task...")
    print(f"  Website: {website_url}")
    print(f"  Website Key: {website_key}")
    print(f"  Metadata Action: {metadata_action if metadata_action else 'None'}")
    print(f"  Metadata CData: {metadata_cdata if metadata_cdata else 'None'}")
    print(f"  Proxy: Not required (ProxyLess)")
    
    # Create task
    result = create_task(api_key, task_data)
    
    if result.get("errorId") != 0:
        raise Exception(f"Failed to create task: {result.get('errorDescription', 'Unknown error')}")
    
    task_id = result.get("taskId")
    print(f"  ✓ Task created: {task_id}")
    
    # Poll for result
    print(f"\n[2/3] Waiting for solution...")
    print("  This may take 1-20 seconds...")
    
    max_attempts = 40
    attempt = 0
    
    while attempt < max_attempts:
        time.sleep(1)  # Check every 1 second
        attempt += 1
        
        result = get_task_result(api_key, task_id)
        status = result.get("status")
        
        if status == "ready":
            print(f"  ✓ Solution received after {attempt} seconds!")
            return result.get("solution", {})
        
        elif status == "failed":
            error_desc = result.get("errorDescription", "Unknown error")
            raise Exception(f"Task failed: {error_desc}")
        
        elif status == "processing":
            if attempt % 5 == 0:
                print(f"  ... Processing (attempt {attempt}/{max_attempts})")
    
    raise Exception("Timeout: Failed to get solution within maximum time")


def extract_sitekey_guide():
    """
    Print a guide on how to extract the Turnstile sitekey
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
        # Check if sitekey needs to be found
        if WEBSITE_KEY == "0x4XXXXXXXXXXXXXXXXX":
            extract_sitekey_guide()
            print("\nPlease set the WEBSITE_KEY in the configuration section and run again.")
            return 1
        
        # Solve the Turnstile
        solution = solve_turnstile(
            api_key=CAPSOLVER_API_KEY,
            website_url=WEBSITE_URL,
            website_key=WEBSITE_KEY,
            metadata_action=METADATA_ACTION if METADATA_ACTION else None,
            metadata_cdata=METADATA_CDATA if METADATA_CDATA else None
        )
        
        # Print solution details
        print("\n" + "=" * 60)
        print("SOLUTION DETAILS")
        print("=" * 60)
        
        token = solution.get("token")
        user_agent = solution.get("userAgent")
        
        print(f"\nTurnstile Token:")
        print(f"  {token}")
        
        print(f"\nUser-Agent:")
        print(f"  {user_agent}")
        
        print("\n" + "=" * 60)
        print("COMPLETE")
        print("=" * 60)
        print("\nUse the token in your form submission:")
        print('  HTML: <input type="hidden" name="cf-turnstile-response" value="TOKEN">')
        print('  JavaScript: formData.append("cf-turnstile-response", token);')
        print(f'\n  Token: {token}')
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
