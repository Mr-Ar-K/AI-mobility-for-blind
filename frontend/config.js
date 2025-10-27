// Backend Configuration
// This file manages the backend URL for all API calls

const BACKEND_CONFIG = {
  // Primary backend URL (from dev tunnel or production)
  PRIMARY: 'https://cjcf4dl2-8000.inc1.devtunnels.ms',
  // Fallback to localhost
  FALLBACK: 'http://localhost:8000',
  // Current active URL
  active: null,
  // Test timeout in milliseconds
  TEST_TIMEOUT: 3000
};

// Function to test if a backend URL is reachable
async function testBackendUrl(url) {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), BACKEND_CONFIG.TEST_TIMEOUT);
    
    const response = await fetch(`${url}/`, {
      method: 'GET',
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    return response.ok;
  } catch (error) {
    console.warn(`Backend URL ${url} is not reachable:`, error.message);
    return false;
  }
}

// Function to get the active backend URL
async function getBackendUrl() {
  // Return cached value if already determined
  if (BACKEND_CONFIG.active) {
    return BACKEND_CONFIG.active;
  }

  // Try primary URL first
  const primaryWorks = await testBackendUrl(BACKEND_CONFIG.PRIMARY);
  if (primaryWorks) {
    BACKEND_CONFIG.active = BACKEND_CONFIG.PRIMARY;
    console.log('Using primary backend:', BACKEND_CONFIG.PRIMARY);
    return BACKEND_CONFIG.PRIMARY;
  }

  // Fallback to localhost
  const fallbackWorks = await testBackendUrl(BACKEND_CONFIG.FALLBACK);
  if (fallbackWorks) {
    BACKEND_CONFIG.active = BACKEND_CONFIG.FALLBACK;
    console.log('Using fallback backend:', BACKEND_CONFIG.FALLBACK);
    return BACKEND_CONFIG.FALLBACK;
  }

  // If both fail, use primary anyway and let the app handle errors
  BACKEND_CONFIG.active = BACKEND_CONFIG.PRIMARY;
  console.error('Neither backend URL is reachable. Using primary URL:', BACKEND_CONFIG.PRIMARY);
  return BACKEND_CONFIG.PRIMARY;
}

// Function to make API calls with automatic backend URL resolution
async function apiCall(endpoint, options = {}) {
  const backendUrl = await getBackendUrl();
  const url = `${backendUrl}${endpoint}`;
  
  try {
    const response = await fetch(url, options);
    return response;
  } catch (error) {
    console.error(`API call failed to ${url}:`, error);
    throw error;
  }
}

// Export for use in other scripts
if (typeof window !== 'undefined') {
  window.BackendAPI = {
    getUrl: getBackendUrl,
    call: apiCall,
    config: BACKEND_CONFIG
  };
}
