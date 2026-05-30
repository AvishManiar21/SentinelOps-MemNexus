/* ==============================================================================
   SentinelOps API Configuration
   Automatically detects environment and sets API endpoint
   ============================================================================== */

const Config = {
    // Detect environment
    isLocal: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1',
    isGitHubPages: window.location.hostname.includes('github.io'),

    // API endpoint configuration (matches app.js logic)
    get API_BASE() {
        // If running locally, use localhost
        if (this.isLocal) {
            return 'http://localhost:5000';
        }
        // Otherwise use Cloud Run production URL
        return 'https://sentinelops-api-782741881130.us-central1.run.app';
    },
    
    // Feature flags
    features: {
        liveDatabaseConnection: true,
        chatSimulation: false,  // Set to true to use mock responses when API unavailable
    },
    
    // App metadata
    app: {
        name: 'SentinelOps',
        version: '1.0.0',
        githubRepo: 'https://github.com/AvishManiar21/SentinelOps-MemNexus'
    }
};

// Make config globally available
window.SentinelOpsConfig = Config;

// Log configuration on load (for debugging)
console.log('🚨 SentinelOps Configuration Loaded');
console.log('Environment:', Config.isGitHubPages ? 'GitHub Pages' : 'Local');
console.log('API Endpoint:', Config.API_BASE);
