# backend/app/similarity/copyleaks_service.py

import httpx
import json
from typing import Dict, Any, List, Optional
from backend.app.config import settings

def get_copyleaks_token() -> Optional[str]:
    """
    Authenticates with the CopyLeaks Identity API and returns the access token.
    Ref: https://api.copyleaks.com/documentation/v3/identity/login
    """
    if not settings.COPYLEAKS_EMAIL or not settings.COPYLEAKS_API_KEY:
        print("CopyLeaks credentials are not fully configured in settings.")
        return None
        
    url = "https://id.copyleaks.com/v2/usr/login/api"
    headers = {"Content-Type": "application/json"}
    payload = {
        "email": settings.COPYLEAKS_EMAIL,
        "key": settings.COPYLEAKS_API_KEY
    }
    
    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        else:
            print(f"CopyLeaks Authentication failed: Status {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Failed to connect to CopyLeaks Identity Server: {e}")
        return None

def submit_text_scan(token: str, scan_id: str, text: str) -> bool:
    """
    Submits a text block to CopyLeaks for similarity scanning.
    Note: CopyLeaks usually processes scans asynchronously and posts back to a webhook.
    """
    url = f"https://api.copyleaks.com/v3/scans/submit/text/{scan_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "text56": text,  # CopyLeaks standard text payload parameter
        "properties": {
            "sandbox": True,  # Use sandbox mode for testing to avoid consuming credits
            "webhooks": {
                # In production, this would be our public endpoint
                "status": f"https://yourdomain.com/api/v1/copyleaks/webhook/{scan_id}"
            }
        }
    }
    
    try:
        response = httpx.put(url, headers=headers, json=payload, timeout=10.0)
        # 201 Created indicates successful submission
        if response.status_code in [200, 201, 202]:
            print(f"Successfully submitted text block {scan_id} to CopyLeaks.")
            return True
        else:
            print(f"CopyLeaks scan submission failed: Status {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error submitting scan to CopyLeaks: {e}")
        return False

def check_text_similarity(text: str) -> Dict[str, Any]:
    """
    Simulates or polls CopyLeaks scan response. 
    Because CopyLeaks API is asynchronous (requires webhook endpoints), when running in a 
    local/offline development environment, we query the API sandbox or fall back to local TF-IDF,
    enhancing the results with a CopyLeaks indicator.
    """
    token = get_copyleaks_token()
    if not token:
        # Fallback signifier
        return {"status": "fallback", "reason": "No credentials or authentication failed"}
        
    import uuid
    scan_id = str(uuid.uuid4())
    
    submitted = submit_text_scan(token, scan_id, text)
    if not submitted:
        return {"status": "fallback", "reason": "Submission failed"}
        
    # Since webhooks are async, we return a success status indicator.
    # The analyzer will combine the CopyLeaks verification status with its local TF-IDF score.
    return {
        "status": "success",
        "scan_id": scan_id,
        "api_provider": "CopyLeaks Sandbox Mode"
    }
