// API Configuration for AI Context Bridge Extension
const API_CONFIG = {
  // Development
  DEV_BASE_URL: "http://localhost:8000/api/v1",

  // Production (update this after deploying to Google Cloud)
  PROD_BASE_URL: "https://ai-context-api-508048026030.us-central1.run.app/api/v1",

  // Get the appropriate base URL based on environment
  getBaseURL: function () {
    // Using production Cloud Run API
    // Change back to DEV_BASE_URL for local development
    return this.PROD_BASE_URL;
  },
};

// Export for use in other scripts
if (typeof module !== "undefined" && module.exports) {
  module.exports = API_CONFIG;
}
