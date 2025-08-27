#!/usr/bin/env python3
"""
Docker GEE Integration Validation
Validates that all Docker configurations are correct for GEE integration
"""

import os
import json
import yaml
from pathlib import Path

def validate_docker_setup():
    """Validate Docker GEE integration setup"""
    print("🐳 Validating Docker GEE Integration Setup")
    print("=" * 50)
    
    issues = []
    success = []
    
    # Check docker-compose.yml
    compose_file = Path("docker-compose.yml")
    if compose_file.exists():
        try:
            with open(compose_file, 'r') as f:
                compose_data = yaml.safe_load(f)
            
            backend_service = compose_data.get('services', {}).get('backend', {})
            environment = backend_service.get('environment', [])
            volumes = backend_service.get('volumes', [])
            
            # Convert environment list to strings for checking
            env_strings = []
            if isinstance(environment, list):
                env_strings = environment
            elif isinstance(environment, dict):
                env_strings = [f"{k}={v}" for k, v in environment.items()]
            
            # Check environment variables
            gee_project_found = any('GEE_PROJECT_ID' in env for env in env_strings)
            google_creds_found = any('GOOGLE_APPLICATION_CREDENTIALS' in env for env in env_strings)
            
            if gee_project_found:
                gee_value = next((env.split('=', 1)[1] for env in env_strings if env.startswith('GEE_PROJECT_ID=')), 'configured')
                success.append(f"✅ GEE_PROJECT_ID configured: {gee_value}")
            else:
                issues.append("❌ GEE_PROJECT_ID not configured in docker-compose.yml")
            
            if google_creds_found:
                creds_value = next((env.split('=', 1)[1] for env in env_strings if env.startswith('GOOGLE_APPLICATION_CREDENTIALS=')), 'configured')
                success.append(f"✅ GOOGLE_APPLICATION_CREDENTIALS configured: {creds_value}")
            else:
                issues.append("❌ GOOGLE_APPLICATION_CREDENTIALS not configured in docker-compose.yml")
            
            # Check volumes
            credentials_volume = any('./credentials:/app/credentials' in str(vol) for vol in volumes)
            if credentials_volume:
                success.append("✅ Credentials volume mount configured")
            else:
                issues.append("❌ Credentials volume mount not configured")
                
        except Exception as e:
            issues.append(f"❌ Error reading docker-compose.yml: {e}")
    else:
        issues.append("❌ docker-compose.yml not found")
    
    # Check requirements.txt
    requirements_file = Path("requirements.txt")
    if requirements_file.exists():
        try:
            with open(requirements_file, 'r') as f:
                requirements = f.read()
            
            if 'earthengine-api' in requirements:
                success.append("✅ earthengine-api in requirements.txt")
            else:
                issues.append("❌ earthengine-api not in requirements.txt")
                
        except Exception as e:
            issues.append(f"❌ Error reading requirements.txt: {e}")
    else:
        issues.append("❌ requirements.txt not found")
    
    # Check credentials directory
    credentials_dir = Path("credentials")
    if credentials_dir.exists():
        success.append("✅ Credentials directory exists")
        
        readme_file = credentials_dir / "README.md"
        if readme_file.exists():
            success.append("✅ Credentials README.md exists")
        else:
            issues.append("❌ Credentials README.md missing")
        
        service_account_file = credentials_dir / "gee-service-account.json"
        if service_account_file.exists():
            try:
                with open(service_account_file, 'r') as f:
                    credentials = json.load(f)
                
                if credentials.get('type') == 'service_account':
                    success.append("✅ Valid service account credentials file found")
                else:
                    issues.append("❌ Invalid service account credentials format")
                    
            except Exception as e:
                issues.append(f"❌ Error reading service account file: {e}")
        else:
            issues.append("⚠️  Service account file not found (expected for initial setup)")
            
    else:
        issues.append("❌ Credentials directory not found")
    
    # Check GEE setup module
    gee_setup_file = Path("gee_docker_setup.py")
    if gee_setup_file.exists():
        success.append("✅ GEE Docker setup module exists")
    else:
        issues.append("❌ GEE Docker setup module missing")
    
    # Summary
    print("\n📋 Validation Results:")
    print("-" * 25)
    
    for item in success:
        print(item)
    
    for item in issues:
        print(item)
    
    print(f"\n📊 Summary: {len(success)} successes, {len(issues)} issues")
    
    if not issues:
        print("\n🎉 Docker GEE integration setup is complete!")
        print("Next steps:")
        print("1. Create service account in Google Cloud Console")
        print("2. Download JSON key as credentials/gee-service-account.json")
        print("3. Test with: docker-compose run backend python gee_docker_setup.py")
    else:
        print("\n🔧 Please address the issues above before proceeding")
    
    return len(issues) == 0

if __name__ == "__main__":
    validate_docker_setup()
