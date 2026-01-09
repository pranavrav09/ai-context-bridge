// Background service worker for handling extension-wide tasks

// Listen for installation
chrome.runtime.onInstalled.addListener(() => {
    console.log('AI Context Bridge installed successfully');
    
    // Set default settings
    chrome.storage.local.set({
      settings: {
        maxMessages: 100,
        autoCompress: true,
        recentMessageCount: 10
      }
    });
  
    // Create context menu if permission is available
    if (chrome.contextMenus) {
      chrome.contextMenus.create({
        id: 'extract-context',
        title: 'Extract AI Context',
        contexts: ['page'],
        documentUrlPatterns: [
          'https://chat.openai.com/*',
          'https://chatgpt.com/*',
          'https://claude.ai/*',
          'https://gemini.google.com/*',
          'https://poe.com/*'
        ]
      });
    }
  });
  
  // Listen for tab updates to show/hide the extension icon
  chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete') {
      const supportedSites = [
        'chat.openai.com',
        'chatgpt.com',
        'claude.ai',
        'gemini.google.com',
        'poe.com'
      ];
      
      const isSupported = supportedSites.some(site => 
        tab.url && tab.url.includes(site)
      );
      
      if (isSupported) {
        chrome.action.enable(tabId);
      } else {
        chrome.action.disable(tabId);
      }
    }
  });
  
  // Handle context menu clicks only if the API is available
  if (chrome.contextMenus) {
    chrome.contextMenus.onClicked.addListener((info, tab) => {
      if (info.menuItemId === 'extract-context') {
        chrome.tabs.sendMessage(tab.id, { 
          action: 'extract',
          options: {
            includeSystem: true,
            compressOlder: true,
            recentCount: 10
          }
        }, (response) => {
          if (response && response.success) {
            // Store the extracted data
            chrome.storage.local.set({ 
              lastExtracted: {
                data: response,
                timestamp: new Date().toISOString()
              }
            });
            
            // Notify user
            chrome.action.setBadgeText({ text: '✓', tabId: tab.id });
            chrome.action.setBadgeBackgroundColor({ color: '#10b981' });
            
            // Clear badge after 3 seconds
            setTimeout(() => {
              chrome.action.setBadgeText({ text: '', tabId: tab.id });
            }, 3000);
          }
        });
      }
    });
  }
  
  // Handle messages from content scripts
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'getStoredContext') {
      chrome.storage.local.get(['lastExtracted'], (result) => {
        sendResponse(result.lastExtracted || null);
      });
      return true; // Keep channel open for async response
    }
  });