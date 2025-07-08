# Cookie Files for Enhanced Video Download

This directory contains cookie files that can improve video download success, especially for platforms like Instagram that require authentication.

## Instagram Cookies Setup

Instagram has tightened authentication requirements. To improve download success:

### Option 1: Browser Cookie Extraction (Automatic)
The application will automatically try to extract cookies from installed browsers:
- Chrome
- Firefox  
- Chromium
- Edge

**Requirements**: Browser must be installed in the Docker/production environment.

### Option 2: Manual Cookie File (Recommended for Production)

1. **Extract cookies from your browser** using a browser extension like "Get cookies.txt LOCALLY":
   - Visit https://www.instagram.com and log in
   - Use the extension to export cookies
   - Save as `instagram_cookies.txt` in this directory

2. **Alternative method** - Export using browser developer tools:
   ```javascript
   // In browser console on instagram.com
   copy(document.cookie)
   ```

### File Naming Convention

- `instagram_cookies.txt` - Instagram-specific cookies (highest priority)
- `youtube_cookies.txt` - Generic cookies (fallback)

### Environment Variable Override

Set `YTDLP_COOKIE_FILE` environment variable to specify a custom cookie file path:
```bash
export YTDLP_COOKIE_FILE="/path/to/your/cookies.txt"
```

## Security Notes

⚠️ **Important**: Cookie files contain authentication tokens. Keep them secure:

- Never commit cookie files to version control
- Regenerate cookies if compromised
- Use environment-specific cookie files for different deployments

## Troubleshooting

### Instagram Download Failures

If Instagram downloads fail with "login required" errors:

1. Check if cookie files exist: `ls -la cookies/`
2. Verify cookie file format (Netscape/Mozilla format)
3. Ensure cookies are recent (Instagram sessions expire)
4. Check logs for browser detection status

### Cookie File Format

Cookies should be in Netscape format:
```
# Netscape HTTP Cookie File
.instagram.com	TRUE	/	TRUE	1234567890	sessionid	abc123...
.instagram.com	TRUE	/	FALSE	1234567890	csrftoken	def456...
```

## Testing

Test cookie functionality:
```bash
# Check if cookies are detected
docker logs meme-maker-worker | grep "cookie"

# Test Instagram URL
curl -X POST http://localhost:8000/api/v1/metadata \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.instagram.com/reel/YOUR_REEL_ID/"}'
``` 