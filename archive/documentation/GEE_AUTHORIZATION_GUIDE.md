# 🛰️ Google Earth Engine Authorization Guide

## Current Status: **SERVICE ACCOUNT AVAILABLE – NEEDS WIRING**
- ✅ All GEE code is implemented and ready
- ✅ Fallback system is working (synthetic data)
- ✅ Docker environment is configured
- ✅ Service account JSON on hand
- 🔄 **Action:** Point local + Docker runtimes to the JSON

---

## 📋 AUTHORIZATION STEPS

### Step 1: Google Cloud Console Setup (10 minutes)

1. **Go to Google Cloud Console**
   ```
   https://console.cloud.google.com/
   ```

2. **Create New Project**
   ```
   - Click "Select a project" → "New Project"
   - Project name: deer-predict-app
   - Click "Create"
   - Note the Project ID (may have numbers appended)
   ```

3. **Enable APIs**
   ```
   Navigation: APIs & Services → Library
   Search and enable these APIs:
   - Google Earth Engine API
   - Cloud Resource Manager API
   ```

### Step 2: Service Account Creation (5 minutes)

4. **Create Service Account**
   ```
   Navigation: IAM & Admin → Service Accounts
   Click "Create Service Account"
   
   Name: deer-prediction-gee
   Description: Service account for deer prediction satellite analysis
   Click "Create and Continue"
   ```

5. **Grant Permissions**
   ```
   Add these roles:
   - Earth Engine Resource Viewer
   - Earth Engine Resource Writer (optional)
   - Service Account User
   Click "Continue" → "Done"
   ```

6. **Create JSON Key**
   ```
   - Click on the created service account
   - Go to "Keys" tab
   - Click "Add Key" → "Create new key"
   - Select "JSON" format
   - Click "Create"
   - File will download automatically
   ```

### Step 3: Earth Engine Registration (3 minutes)

7. **Register with Earth Engine**
   ```
   - Go to: https://code.earthengine.google.com/
   - Sign in with your Google account
   - Accept terms if prompted
   - Go to "Assets" tab
   - Click "NEW" → "Cloud Project"
   - Enter your project ID from step 2
   ```

8. **Add Service Account**
   ```
   In Earth Engine Code Editor:
   - Go to Assets → Click settings gear
   - Add service account email from step 4
   - Email format: deer-prediction-gee@[PROJECT-ID].iam.gserviceaccount.com
   ```

### Step 4: Install Credentials (1 minute)

9. **Place Credentials File**
    ```bash
    # Rename downloaded file to: gee-service-account.json
    # Copy to: c:\Users\Rich\deer_pred_app\credentials\gee-service-account.json
    # (File is .gitignored – keep it out of source control)
    ```

10. **Set Local Environment Variables (PowerShell)**
      ```powershell
      $env:GOOGLE_APPLICATION_CREDENTIALS="C:\\Users\\Rich\\deer_pred_app\\credentials\\gee-service-account.json"
      $env:GEE_PROJECT_ID="deer-predict-app"
      ```
      _Tip: add these to your PowerShell profile or `.env` so every session picks them up._

11. **Configure Docker Runtime**
      ```yaml
      # docker-compose.yml (backend service excerpt)
      environment:
         - GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/gee-service-account.json
         - GEE_PROJECT_ID=deer-predict-app
      volumes:
         - ./credentials:/app/credentials:ro
      ```
      _Ensure the credentials folder is mounted read-only so containers authenticate automatically._

---

## 🧪 TESTING & ACTIVATION

### Step 5: Test Authorization

Run the verification script _after_ exporting the env vars:
```powershell
cd C:\Users\Rich\deer_pred_app
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\\Users\\Rich\\deer_pred_app\\credentials\\gee-service-account.json"
$env:GEE_PROJECT_ID="deer-predict-app"
python final_satellite_verification.py
```

**Expected Results After Authorization:**
```
✅ Google Earth Engine authenticated
✅ Landsat scenes detected (NDVI printed)
✅ Land-cover + elevation details reported
🎉 SATELLITE DATA INTEGRATION COMPLETE!
```

### Step 6: Activate in Production

Once authorization works:

1. **Test in Docker**
   ```bash
   docker-compose run --rm backend python final_satellite_verification.py
   ```

2. **Run Full Application**
   ```bash
   docker-compose up
   ```

3. **Test Enhanced Predictions**
   ```bash
   # Frontend will automatically use real satellite data
   # API at http://localhost:8000/enhanced-predict
   ```

---

## 🔄 WHAT CHANGES AFTER AUTHORIZATION

### Before (Current - Fallback Mode):
- 📊 Synthetic vegetation data
- 🏔️ Basic terrain analysis
- ⚠️ Limited accuracy

### After (Real Satellite Data):
- 🛰️ **Live NDVI vegetation health**
- 🌿 **Real-time land cover classification**
- 🍃 **Current crop/mast conditions**
- 💧 **Actual water source mapping**
- 📈 **Significantly improved prediction accuracy**

---

## 📊 IMMEDIATE BENEFITS

### Enhanced Accuracy:
- **Food Sources**: Real crop/acorn production data
- **Cover Quality**: Current vegetation density
- **Seasonal Changes**: Live vegetation phenology
- **Water Access**: Accurate water body mapping

### Real-Time Intelligence:
- **Recent Harvest**: Crop cutting detection
- **Browse Pressure**: Vegetation stress analysis
- **Weather Impact**: Drought/flood effects on habitat
- **Seasonal Timing**: Peak vegetation periods

---

## 🎯 READY TO AUTHORIZE?

**Current Setup Status:**
- ✅ All code implemented
- ✅ Docker environment ready
- ✅ Fallback system working
- ✅ Test framework complete

**You just need:**
1. 10 minutes to set up Google Cloud (done!)
2. Download 1 JSON file (done!)
3. Export two environment variables + restart the stack

**Then you'll have:**
- 🛰️ Live satellite vegetation analysis
- 🎯 Enhanced hunting predictions
- 📡 Real-time environmental intelligence

---

Would you like to proceed with the authorization steps now?
