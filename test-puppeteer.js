const puppeteer = require('puppeteer');

async function testConnection() {
  let browser;
  try {
    console.log('🚀 Testing Puppeteer connection...');
    
    browser = await puppeteer.launch({ 
      headless: 'new',
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    const page = await browser.newPage();
    
    console.log('📍 Testing localhost:3001...');
    await page.goto('http://localhost:3001', { 
      waitUntil: 'domcontentloaded',
      timeout: 10000,
    });
    
    const title = await page.title();
    console.log('✅ Successfully connected! Page title:', title);
    
  } catch (error) {
    console.error('❌ Connection failed:', error.message);
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

testConnection(); 