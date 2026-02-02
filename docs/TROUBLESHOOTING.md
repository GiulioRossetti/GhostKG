# Troubleshooting Guide

This guide helps resolve common issues with GhostKG.

## Visualization Server Issues

### HTTP 403 Forbidden Error

**Symptom:** Browser shows "Access to localhost was denied" or "HTTP ERROR 403"

**The Flask server is proven to work correctly.** If you're seeing 403 errors, it's likely a browser or system configuration issue.

#### Quick Fixes

1. **Try a different browser**
   ```bash
   # Let the browser open automatically
   ghostkg serve --json history.json --browser
   ```
   Test with Chrome, Firefox, Safari, or Edge.

2. **Manually open the URL**
   ```bash
   # Start server without auto-opening browser
   ghostkg serve --json history.json
   
   # Then manually navigate to http://127.0.0.1:5000 in your browser
   ```

3. **Try a different port**
   ```bash
   ghostkg serve --json history.json --port 8080 --browser
   ```

4. **Clear browser cache**
   - Press Ctrl+Shift+Delete (or Cmd+Shift+Delete on Mac)
   - Clear cached images and files
   - Try again

5. **Use incognito/private mode**
   - Opens browser without extensions or cache
   - Helps identify if extensions are causing issues

#### Detailed Diagnostics

**Step 1: Test with curl**

Test if the server is actually responding:

```bash
# In one terminal
ghostkg serve --json history.json

# In another terminal
curl http://127.0.0.1:5000/
```

If curl shows HTML content, the server works and it's a browser issue.

**Step 2: Enable debug mode**

See exactly what requests are received:

```bash
ghostkg serve --json history.json --debug
```

Look for log messages like:
```
[DEBUG] GET / from 127.0.0.1
127.0.0.1 - - [timestamp] "GET / HTTP/1.1" 200 -
```

If you don't see any requests, the browser isn't reaching the server.

**Step 3: Check browser console**

1. Open browser developer tools (F12)
2. Go to Console tab
3. Look for errors (red text)
4. Common issues:
   - CORS errors
   - Mixed content warnings
   - Extension blocking requests

**Step 4: Check for port conflicts**

```bash
# On macOS/Linux
lsof -i :5000

# On Windows
netstat -ano | findstr :5000
```

If another process is using port 5000, use a different port:
```bash
ghostkg serve --json history.json --port 8080
```

#### Common Causes

**1. Browser Security Settings**
- Some browsers block localhost access in certain security modes
- Try disabling strict security settings temporarily
- Check if "Enhanced protection" or similar features are blocking requests

**2. Firewall/Antivirus**
- Some security software blocks local server connections
- Add exception for Python or the specific port
- Try temporarily disabling to test

**3. VPN or Proxy**
- VPNs can interfere with localhost access
- Try disconnecting VPN temporarily
- Check proxy settings in browser

**4. Browser Extensions**
- Ad blockers or privacy extensions might block requests
- Try disabling extensions
- Use incognito mode (extensions disabled by default)

**5. System Hosts File**
- Incorrect hosts file configuration
- Check `/etc/hosts` (Mac/Linux) or `C:\Windows\System32\drivers\etc\hosts` (Windows)
- Ensure `127.0.0.1 localhost` entry exists

#### Platform-Specific Issues

**macOS:**
- Gatekeeper might block Python from network access
- Go to System Preferences > Security & Privacy > Firewall > Firewall Options
- Allow Python to accept incoming connections

**Windows:**
- Windows Firewall might block Python
- Go to Windows Defender Firewall > Allow an app
- Add Python to allowed apps

**Linux:**
- Check iptables or firewall rules
- Ensure localhost traffic is allowed

### Server Won't Start

**Symptom:** Error when starting server

**Address already in use:**
```
❌ Error: Port 5000 is already in use
   Try a different port with --port <number>
```

**Solution:** Use a different port:
```bash
ghostkg serve --json history.json --port 8080
```

**Flask not installed:**
```
❌ Error: Flask is required for the serve command.
   Install with: pip install ghost_kg[viz]
```

**Solution:** Install visualization dependencies:
```bash
pip install ghost_kg[viz]
```

### JSON File Not Found

**Symptom:** 
```
❌ Error: JSON file not found: /path/to/file.json
```

**Solution:** Check the file path:
```bash
# Use absolute path
ghostkg serve --json /full/path/to/history.json

# Or navigate to directory first
cd /path/to/directory
ghostkg serve --json history.json
```

### Template Files Missing

**Symptom:** Server starts but routes return 404

**Solution:** Reinstall the package:
```bash
pip install --force-reinstall ghost_kg
```

## Database Issues

### SQLAlchemy Import Error

**Symptom:**
```
ModuleNotFoundError: No module named 'sqlalchemy'
```

**Solution:** Install core dependencies:
```bash
pip install ghost_kg
# or
pip install -e .
```

### Database Connection Failed

**For PostgreSQL:**
```
Could not connect to database
```

**Solution:**
1. Install PostgreSQL driver:
   ```bash
   pip install ghost_kg[postgres]
   ```

2. Check connection string format:
   ```python
   agent = GhostAgent("Alice", db_path="postgresql://user:pass@localhost/dbname")
   ```

3. Verify PostgreSQL is running:
   ```bash
   # Check status
   pg_isready
   ```

**For MySQL:**
```
Could not connect to database
```

**Solution:**
1. Install MySQL driver:
   ```bash
   pip install ghost_kg[mysql]
   ```

2. Check connection string format:
   ```python
   agent = GhostAgent("Alice", db_path="mysql+pymysql://user:pass@localhost/dbname")
   ```

3. Verify MySQL is running:
   ```bash
   # Check status
   mysql -u user -p -e "SELECT 1"
   ```

### Sentiment Validation Error

**Symptom:**
```
ValidationError: sentiment must be between -1.0 and 1.0
```

**Solution:** This should be automatically handled now with clamping. If it persists:
1. Update to the latest version
2. Report the issue with the specific text that caused it

## Export Issues

### Database Not Found

**Symptom:**
```
❌ Error: Database not found: /path/to/database.db
```

**Solution:** Check the database path:
```bash
# Use absolute path
ghostkg export --database /full/path/to/database.db

# Or use relative path from current directory
cd /path/to/directory
ghostkg export --database database.db
```

### No Agents Found

**Symptom:** Export completes but visualization is empty

**Solution:** 
1. Check if there are any logs in the database:
   ```python
   from ghost_kg.storage import KnowledgeDB
   db = KnowledgeDB("database.db")
   # Check for logs
   ```

2. Specify agents explicitly:
   ```bash
   ghostkg export --database database.db --agents Alice,Bob
   ```

3. Ensure agents have actually learned some knowledge

## Development Mode Issues

### Dev Script Not Working

**Symptom:**
```
python ghostkg_dev.py: command not found
```

**Solution:** Make sure you're in the repository root:
```bash
cd /path/to/GhostKG
python ghostkg_dev.py --help
```

### Module Import Errors

**Symptom:**
```
ModuleNotFoundError: No module named 'ghost_kg'
```

**Solution:** Install dependencies:
```bash
# Minimal setup
pip install -r requirements/base.txt
pip install flask

# Full setup
pip install -e .
```

## Getting Help

If none of these solutions work:

1. **Check the version:**
   ```bash
   python -c "import ghost_kg; print(ghost_kg.__version__)"
   ```

2. **Run with debug mode:**
   ```bash
   ghostkg serve --json history.json --debug
   ```

3. **Test with curl:**
   ```bash
   curl http://127.0.0.1:5000/
   ```

4. **Check logs:**
   - Look for error messages in terminal output
   - Check browser console (F12)
   - Enable debug mode for detailed logs

5. **Report the issue:**
   - Include version number
   - Include full error message
   - Include steps to reproduce
   - Include debug output if available

## Common Workflows

### Testing Locally

```bash
# Create test data
python examples/use_case_example.py

# Export and visualize
python ghostkg_dev.py export --database examples/use_case_example.db --serve --browser
```

### Production Setup

```bash
# Install with all features
pip install ghost_kg[all]

# Export data
ghostkg export --database production.db --output data.json

# Serve with production WSGI server (recommended)
# Install waitress or gunicorn
pip install waitress
waitress-serve --host=0.0.0.0 --port=5000 ghost_kg.cli:app
```

Note: For production, consider using a proper WSGI server instead of Flask's development server.
