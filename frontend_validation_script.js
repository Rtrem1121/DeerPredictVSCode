// Frontend Validation Script for Tinmouth Bedding Zones
// Copy and paste into browser console at localhost:8501

console.log('Starting Tinmouth Bedding Zone Frontend Validation');

// Function to check for map elements
function checkMapElements() {
    const mapContainer = document.querySelector('.deckgl-container');
    const layers = document.querySelectorAll('[data-testid*="layer"]');
    
    console.log('Map Container:', mapContainer ? 'Found' : 'Missing');
    console.log('Map Layers:', layers.length, 'found');
    
    return {
        mapPresent: !!mapContainer,
        layerCount: layers.length
    };
}

// Function to simulate coordinate input
function inputCoordinates() {
    const latInput = document.querySelector('input[placeholder*="lat" i]');
    const lonInput = document.querySelector('input[placeholder*="lon" i]');
    
    if (latInput && lonInput) {
        latInput.value = '43.3144';
        lonInput.value = '-73.2182';
        
        // Trigger input events
        latInput.dispatchEvent(new Event('input', { bubbles: true }));
        lonInput.dispatchEvent(new Event('input', { bubbles: true }));
        
        console.log('Coordinates entered:', latInput.value, lonInput.value);
        return true;
    } else {
        console.log('Coordinate inputs not found');
        return false;
    }
}

// Function to check for bedding zones after prediction
function checkBeddingZones() {
    setTimeout(() => {
        const beddingElements = document.querySelectorAll('[data-testid*="bedding"], .bedding-pin, [style*="green"]');
        const standElements = document.querySelectorAll('[data-testid*="stand"], .stand-pin, [style*="red"]');
        
        console.log('Bedding Elements Found:', beddingElements.length);
        console.log('Stand Elements Found:', standElements.length);
        
        if (beddingElements.length >= 3) {
            console.log('SUCCESS: Bedding zones rendered on frontend');
        } else {
            console.log('ISSUE: Insufficient bedding zones on frontend');
        }
        
        if (standElements.length >= 1) {
            console.log('SUCCESS: Stand sites rendered on frontend');
        } else {
            console.log('ISSUE: No stand sites on frontend');
        }
        
        return {
            beddingZones: beddingElements.length,
            standSites: standElements.length
        };
    }, 3000); // Wait 3 seconds for rendering
}

// Run validation
console.log('Step 1: Checking map elements...');
const mapCheck = checkMapElements();

console.log('Step 2: Entering Tinmouth coordinates...');
const coordsEntered = inputCoordinates();

console.log('Step 3: Run prediction and wait 3 seconds...');
console.log('Step 4: Checking for bedding zones...');
checkBeddingZones();

console.log('Frontend validation script complete. Check results above.');
