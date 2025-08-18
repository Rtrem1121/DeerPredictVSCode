# Google Earth Engine Credentials for Docker

This directory contains service account credentials for Google Earth Engine integration in Docker.

## Complete Setup Instructions:

### 1. Google Cloud Console Setup
```bash
# Go to: https://console.cloud.google.com/
# Select project: deer-predict-app (or create it)
```

### 2. Enable Required APIs
- Google Earth Engine API
- Cloud Resource Manager API

### 3. Create Service Account
```
Navigation: IAM & Admin → Service Accounts → Create Service Account
Name: deer-prediction-gee
Description: Service account for deer prediction app GEE access
```

### 4. Grant Required Permissions
Add these roles to the service account:
- Earth Engine Resource Viewer
- Earth Engine Resource Writer (if needed for advanced features)
- Service Account User

### 5. Create and Download Key
```
1. Click on the created service account
2. Go to "Keys" tab
3. Click "Add Key" → "Create new key"
4. Select "JSON" format
5. Download the key file
```

### 6. Place Credentials File
```bash
# Place the downloaded JSON file here as:
credentials/gee-service-account.json
```

### 7. Register with Earth Engine
The service account email needs to be registered with Google Earth Engine:
```
1. Go to: https://code.earthengine.google.com/
2. Click on "Assets" tab
3. Click "NEW" → "Cloud Project"
4. Add your service account email: [service-account-name]@deer-predict-app.iam.gserviceaccount.com
```

### 8. Test Setup
```bash
# Run the Docker-compatible test:
python gee_docker_setup.py

# Or test in Docker container:
docker-compose run backend python gee_docker_setup.py
```

## Security Notes:
- The credentials file is mounted read-only in Docker
- Never commit the JSON file to version control
- Rotate credentials periodically for security

## Environment Variables:
- `GEE_PROJECT_ID`: deer-predict-app
- `GOOGLE_APPLICATION_CREDENTIALS`: /app/credentials/gee-service-account.json

## File Structure:
```
credentials/
├── README.md (this file)
└── gee-service-account.json (you need to add this)
```

## Troubleshooting:
If authentication fails:
1. Verify the service account has Earth Engine access
2. Check that the JSON file is valid
3. Ensure the project ID matches in Google Cloud Console
4. Confirm Earth Engine API is enabled for the project
