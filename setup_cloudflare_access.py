#!/usr/bin/env python3
"""
Cloudflare Access Application Setup Script
Automates the creation of Access application for deer hunting app
"""

import json
import sys

def generate_cloudflare_access_config():
    """Generate the configuration for Cloudflare Access application"""
    
    config = {
        "application": {
            "name": "Deer Hunting Intelligence App",
            "domain": "app.deerpredictapp.org",
            "type": "self_hosted",
            "cors_headers": {
                "allow_all_origins": True,
                "allow_all_methods": True,
                "allow_all_headers": True,
                "allow_credentials": True
            },
            "policies": [
                {
                    "name": "Authorized Hunters",
                    "action": "allow",
                    "rules": [
                        {
                            "include": [
                                {
                                    "email": {
                                        "email": "rtrem1121@gmail.com"  # Replace with your email
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        "instructions": [
            "1. Go to Cloudflare Dashboard → Zero Trust → Access → Applications",
            "2. Click 'Add an application'",
            "3. Select 'Self-hosted'",
            "4. Application name: 'Deer Hunting Intelligence App'",
            "5. Subdomain: 'app'",
            "6. Domain: 'deerpredictapp.org'", 
            "7. Select the 'Authorized Hunters' policy we created",
            "8. Save the application"
        ]
    }
    
    return config

if __name__ == "__main__":
    config = generate_cloudflare_access_config()
    
    print("🛡️ CLOUDFLARE ACCESS CONFIGURATION")
    print("=====================================")
    print()
    print("📋 MANUAL SETUP INSTRUCTIONS:")
    for i, instruction in enumerate(config["instructions"], 1):
        print(f"{i}. {instruction}")
    
    print()
    print("📊 APPLICATION CONFIGURATION:")
    print(json.dumps(config["application"], indent=2))
    
    print()
    print("🎯 REMINDER: PRIMARY OBJECTIVE")
    print("Secure deer hunting app so unauthorized users cannot access it")
    print("Current method: Cloudflare Access (Plan B)")
    print("Fallback: IP whitelisting if this fails")
