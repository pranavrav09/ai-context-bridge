// Platform detection and extraction logic
class ContextExtractor {
    constructor() {
      this.platform = this.detectPlatform();
      this.extractors = {
        'chatgpt': new ChatGPTExtractor(),
        'claude': new ClaudeExtractor(),
        'gemini': new GeminiExtractor(),
        'poe': new PoeExtractor()
      };
    }
  
    detectPlatform() {
      const hostname = window.location.hostname;
      if (hostname.includes('chat.openai.com') || hostname.includes('chatgpt.com')) {
        return 'chatgpt';
      } else if (hostname.includes('claude.ai')) {
        return 'claude';
      } else if (hostname.includes('gemini.google.com')) {
        return 'gemini';
      } else if (hostname.includes('poe.com')) {
        return 'poe';
      }
      return 'unknown';
    }
  
    async extract() {
      const extractor = this.extractors[this.platform];
      if (!extractor) {
        throw new Error(`Platform ${this.platform} not supported`);
      }
      return await extractor.extract();
    }
  }
  
  // ChatGPT Extractor
  class ChatGPTExtractor {
    extract() {
      const messages = [];
      
      // Try multiple possible selectors for ChatGPT's structure
      const selectors = [
        '[data-testid^="conversation-turn-"]',
        '.group.w-full',
        '[class*="ConversationItem"]'
      ];
      
      let messageElements = null;
      for (const selector of selectors) {
        messageElements = document.querySelectorAll(selector);
        if (messageElements.length > 0) break;
      }
  
      if (!messageElements || messageElements.length === 0) {
        console.log('No messages found with standard selectors');
        return messages;
      }
  
      messageElements.forEach(elem => {
        // Determine role (user or assistant)
        const isUser = elem.querySelector('[data-testid*="user"]') || 
                       elem.textContent.includes('You') ||
                       elem.className.includes('dark:bg-gray-800');
        
        // Extract text content
        const textElement = elem.querySelector('.markdown, .prose, [class*="prose"], .whitespace-pre-wrap');
        const content = textElement ? textElement.innerText : elem.innerText;
        
        if (content && content.trim()) {
          messages.push({
            role: isUser ? 'user' : 'assistant',
            content: content.trim(),
            timestamp: new Date().toISOString()
          });
        }
      });
  
      return messages;
    }
  }
  
  // Claude Extractor
  class ClaudeExtractor {
    extract() {
      const messages = [];
      
      // Claude uses different structure
      const messageElements = document.querySelectorAll('[data-test-render-count], .font-claude-message, [class*="message"]');
      
      messageElements.forEach(elem => {
        // Check for human/assistant indicators
        const isHuman = elem.querySelector('[data-icon="user"]') || 
                        elem.className.includes('human') ||
                        elem.textContent.startsWith('H:');
        
        const textContent = elem.querySelector('.whitespace-pre-wrap, .prose, [class*="text-base"]');
        const content = textContent ? textContent.innerText : elem.innerText;
        
        if (content && content.trim()) {
          messages.push({
            role: isHuman ? 'user' : 'assistant',
            content: content.trim(),
            timestamp: new Date().toISOString()
          });
        }
      });
  
      return messages;
    }
  }
  
  // Gemini Extractor
  class GeminiExtractor {
    extract() {
      const messages = [];
      
      // Gemini/Bard structure
      const messageElements = document.querySelectorAll('.conversation-container message-content, [class*="message"], .model-response-text');
      
      messageElements.forEach((elem, index) => {
        const content = elem.innerText;
        if (content && content.trim()) {
          // Gemini alternates between user and model
          messages.push({
            role: index % 2 === 0 ? 'user' : 'assistant',
            content: content.trim(),
            timestamp: new Date().toISOString()
          });
        }
      });
  
      return messages;
    }
  }
  
  // Poe Extractor
  class PoeExtractor {
    extract() {
      const messages = [];
      
      const messageElements = document.querySelectorAll('[class*="Message_row"], [class*="ChatMessage"]');
      
      messageElements.forEach(elem => {
        const isHuman = elem.className.includes('human') || 
                        elem.querySelector('[class*="UserMessage"]');
        
        const content = elem.querySelector('[class*="Markdown_markdown"], .prose')?.innerText || elem.innerText;
        
        if (content && content.trim()) {
          messages.push({
            role: isHuman ? 'user' : 'assistant',
            content: content.trim(),
            timestamp: new Date().toISOString()
          });
        }
      });
  
      return messages;
    }
  }
  
  // Context compression and formatting
  class ContextFormatter {
    static format(messages, options = {}) {
      const {
        includeSystem = true,
        compressOlder = true,
        recentCount = 10
      } = options;
  
      if (messages.length === 0) {
        return { formatted: '', summary: 'No messages to transfer' };
      }
  
      let formatted = '';
      let summary = '';
  
      if (compressOlder && messages.length > recentCount) {
        // Split messages
        const older = messages.slice(0, -recentCount);
        const recent = messages.slice(-recentCount);
  
        // Create summary of older messages
        summary = this.createSummary(older);
        formatted = `## Previous Context Summary\n${summary}\n\n## Recent Conversation\n`;
        
        // Add recent messages
        recent.forEach(msg => {
          formatted += `\n**${msg.role.toUpperCase()}**: ${msg.content}\n`;
        });
      } else {
        // Include all messages
        formatted = '## Full Conversation\n';
        messages.forEach(msg => {
          formatted += `\n**${msg.role.toUpperCase()}**: ${msg.content}\n`;
        });
      }
  
      return { formatted, summary };
    }
  
    static createSummary(messages) {
      // Simple summary - in production, you might want to use AI for this
      const topics = new Set();
      const questions = [];
      
      messages.forEach(msg => {
        if (msg.role === 'user' && msg.content.includes('?')) {
          questions.push(msg.content.substring(0, 100));
        }
        
        // Extract potential topics (words longer than 5 chars)
        const words = msg.content.split(/\s+/);
        words.forEach(word => {
          if (word.length > 5 && !word.startsWith('http')) {
            topics.add(word.toLowerCase());
          }
        });
      });
  
      return `Discussed ${messages.length} messages covering topics like: ${[...topics].slice(0, 10).join(', ')}. Key questions included: ${questions.slice(0, 3).join('; ')}`;
    }
  }
  
  // Listen for messages from popup
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'extract') {
      const extractor = new ContextExtractor();
      const platform = extractor.detectPlatform();
      
      extractor.extract().then(messages => {
        const formatted = ContextFormatter.format(messages, request.options);
        sendResponse({
          success: true,
          platform: platform,
          messages: messages,
          formatted: formatted.formatted,
          summary: formatted.summary,
          count: messages.length
        });
      }).catch(error => {
        sendResponse({
          success: false,
          error: error.message
        });
      });
      
      return true; // Keep message channel open for async response
    }
    
    if (request.action === 'inject') {
      // Inject context into current page
      const platform = new ContextExtractor().detectPlatform();
      
      if (platform === 'chatgpt') {
        const textarea = document.querySelector('textarea[data-id], #prompt-textarea, textarea');
        if (textarea) {
          textarea.value = request.context;
          textarea.dispatchEvent(new Event('input', { bubbles: true }));
          sendResponse({ success: true });
        }
      } else if (platform === 'claude') {
        const editor = document.querySelector('[contenteditable="true"], .ProseMirror');
        if (editor) {
          editor.textContent = request.context;
          editor.dispatchEvent(new Event('input', { bubbles: true }));
          sendResponse({ success: true });
        }
      }
      // Add more platforms as needed
    }
    
    if (request.action === 'detectPlatform') {
      const extractor = new ContextExtractor();
      sendResponse({ platform: extractor.detectPlatform() });
    }
  });
  
  // Initial platform detection
  console.log('AI Context Bridge loaded on:', new ContextExtractor().detectPlatform());