// Popup script to handle user interactions
let extractedData = null;
const API_BASE_URL = API_CONFIG.getBaseURL();

document.addEventListener('DOMContentLoaded', async () => {
  // Get current tab and detect platform
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  
  // Detect platform
  chrome.tabs.sendMessage(tab.id, { action: 'detectPlatform' }, (response) => {
    if (response && response.platform) {
      document.getElementById('current-platform').textContent = 
        `Platform: ${response.platform.charAt(0).toUpperCase() + response.platform.slice(1)}`;
    }
  });
  
  // Extract button handler
  document.getElementById('extract-btn').addEventListener('click', async () => {
    const options = {
      includeSystem: document.getElementById('include-system').checked,
      compressOlder: document.getElementById('compress-context').checked,
      recentCount: parseInt(document.getElementById('recent-count').value)
    };
    
    setStatus('Extracting context...', 'loading');
    
    chrome.tabs.sendMessage(tab.id, { 
      action: 'extract',
      options: options 
    }, (response) => {
      if (response && response.success) {
        extractedData = response;
        
        // Update UI
        setStatus(`Extracted ${response.count} messages`, 'success');
        document.getElementById('message-count').textContent = `(${response.count} messages)`;
        
        // Show extracted content preview
        document.getElementById('extracted-content').style.display = 'block';
        document.getElementById('summary').textContent = response.summary || 'No summary available';
        document.getElementById('context-preview').textContent = 
          response.formatted.substring(0, 500) + '...';
        
        // Enable action buttons
        document.getElementById('copy-btn').disabled = false;
        document.getElementById('inject-btn').disabled = false;
        
        // Store in chrome.storage for cross-tab access
        chrome.storage.local.set({ 
          lastExtracted: {
            data: response,
            timestamp: new Date().toISOString()
          }
        });
      } else {
        setStatus('Extraction failed: ' + (response?.error || 'Unknown error'), 'error');
      }
    });
  });
  
  // Copy to clipboard handler
  document.getElementById('copy-btn').addEventListener('click', async () => {
    if (!extractedData) return;
    
    try {
      // Create a more comprehensive context transfer
      const contextTransfer = `# Context Transfer from ${extractedData.platform}
Date: ${new Date().toLocaleString()}
Messages: ${extractedData.count}

${extractedData.formatted}

---
Transferred using AI Context Bridge`;
      
      await navigator.clipboard.writeText(contextTransfer);
      setStatus('Copied to clipboard!', 'success');
      
      // Flash button for feedback
      const btn = document.getElementById('copy-btn');
      btn.style.backgroundColor = '#10b981';
      setTimeout(() => {
        btn.style.backgroundColor = '';
      }, 1000);
    } catch (err) {
      setStatus('Failed to copy: ' + err.message, 'error');
    }
  });
  
  // Inject context handler
  document.getElementById('inject-btn').addEventListener('click', async () => {
    if (!extractedData) return;
    
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    chrome.tabs.sendMessage(tab.id, { 
      action: 'inject',
      context: extractedData.formatted
    }, (response) => {
      if (response && response.success) {
        setStatus('Context injected!', 'success');
      } else {
        setStatus('Injection failed - make sure you\'re on a supported AI platform', 'error');
      }
    });
  });
  
  // Check for previously extracted data
  chrome.storage.local.get(['lastExtracted'], (result) => {
    if (result.lastExtracted) {
      const timeDiff = Date.now() - new Date(result.lastExtracted.timestamp).getTime();
      const hoursDiff = timeDiff / (1000 * 60 * 60);
      
      if (hoursDiff < 1) { // If less than 1 hour old
        extractedData = result.lastExtracted.data;
        document.getElementById('copy-btn').disabled = false;
        document.getElementById('inject-btn').disabled = false;
        setStatus('Previous extraction loaded', 'info');
        
        if (extractedData.count) {
          document.getElementById('message-count').textContent = 
            `(${extractedData.count} messages from previous extraction)`;
        }
      }
    }
  });

  // Save to cloud button handler
  document.getElementById('save-cloud-btn')?.addEventListener('click', async () => {
    if (!extractedData) {
      setStatus('No extracted data to save', 'error');
      return;
    }

    try {
      setStatus('Saving to cloud...', 'loading');
      const result = await saveToCloud(extractedData);
      setStatus(`Saved to cloud! AI Summary: ${result.ai_summary || 'N/A'}`, 'success');

      // Store cloud context ID
      chrome.storage.local.set({
        lastCloudContextId: result.context_id
      });
    } catch (error) {
      setStatus('Cloud save failed: ' + error.message, 'error');
    }
  });

  // Load from cloud button handler
  document.getElementById('load-cloud-btn')?.addEventListener('click', async () => {
    // Get the last saved context ID
    chrome.storage.local.get(['lastCloudContextId'], async (result) => {
      if (!result.lastCloudContextId) {
        setStatus('No cloud context ID found', 'error');
        return;
      }

      try {
        setStatus('Loading from cloud...', 'loading');
        const context = await loadFromCloud(result.lastCloudContextId);

        // Convert to extractedData format
        extractedData = {
          success: true,
          platform: context.platform,
          messages: context.messages,
          formatted: context.formatted,
          summary: context.summary,
          count: context.message_count
        };

        // Update UI
        setStatus(`Loaded ${context.message_count} messages from cloud`, 'success');
        document.getElementById('message-count').textContent = `(${context.message_count} messages)`;
        document.getElementById('summary').textContent = context.summary || 'No summary available';
        document.getElementById('context-preview').textContent =
          context.formatted.substring(0, 500) + '...';
        document.getElementById('extracted-content').style.display = 'block';
        document.getElementById('copy-btn').disabled = false;
        document.getElementById('inject-btn').disabled = false;
      } catch (error) {
        setStatus('Cloud load failed: ' + error.message, 'error');
      }
    });
  });
});

// Cloud storage functions
async function saveToCloud(extractedData) {
  try {
    const response = await fetch(`${API_BASE_URL}/contexts`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        platform: extractedData.platform,
        messages: extractedData.messages,
        formatted: extractedData.formatted,
        summary: extractedData.summary,
        generate_ai_summary: true,
        source_metadata: {
          browser: 'Chrome',
          extension_version: chrome.runtime.getManifest().version,
          saved_at: new Date().toISOString()
        }
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to save to cloud:', error);
    throw error;
  }
}

async function loadFromCloud(contextId) {
  try {
    const response = await fetch(`${API_BASE_URL}/contexts/${contextId}`);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Context not found');
      }
      throw new Error(`HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to load from cloud:', error);
    throw error;
  }
}

function setStatus(message, type = 'info') {
  const statusEl = document.getElementById('status');
  statusEl.textContent = message;
  statusEl.className = `status status-${type}`;
  
  // Auto-clear error/success messages
  if (type === 'success' || type === 'error') {
    setTimeout(() => {
      statusEl.className = 'status';
      statusEl.textContent = 'Ready';
    }, 3000);
  }
}