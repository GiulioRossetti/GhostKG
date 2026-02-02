# Visualization Server 403 Error and Output Path Fix

## Problem Statement

Two issues were reported with the visualization CLI:

1. **HTTP 403 Error**: Server returned "Access to localhost was denied" when accessing the visualization
2. **Wrong Output Path**: JSON file was generated in package directory (`ghost_kg/templates/`) instead of current working directory

## Root Causes

### Issue 1: HTTP 403 Error

The Flask application was configured with:
```python
app = Flask(__name__, static_folder=str(templates_dir))

@app.route('/')
def index():
    return send_from_directory(str(templates_dir), 'index.html')
```

This configuration can cause permission issues on some systems because:
- `static_folder` sets up Flask's static file handling
- `send_from_directory()` performs additional security checks
- The combination can lead to access denied errors depending on file permissions and system configuration

### Issue 2: Wrong Output Path

The default output path was hardcoded to the package templates directory:
```python
if not output_file:
    templates_dir = Path(__file__).parent / "templates"
    output_file = str(templates_dir / "simulation_history.json")
```

This resulted in:
- Data files mixed with code files
- Users needing to navigate to package directory
- Unexpected behavior (CLI commands typically output to current directory)

## Solutions Implemented

### Fix 1: Flask Server Configuration

**Changed Flask Setup:**
```python
# Removed static_folder configuration
app = Flask(__name__)

@app.route('/')
def index():
    index_path = templates_dir / 'index.html'
    return send_file(index_path, mimetype='text/html')

@app.route('/style.css')
def style():
    css_path = templates_dir / 'style.css'
    return send_file(css_path, mimetype='text/css')

@app.route('/app.js')
def app_js():
    js_path = templates_dir / 'app.js'
    return send_file(js_path, mimetype='application/javascript')
```

**Benefits:**
- `send_file()` is simpler and more direct
- Explicit MIME types ensure correct content handling
- No static folder security checks that could fail
- More reliable across different systems

### Fix 2: Output Path

**Changed Default Output:**
```python
if not output_file:
    # Default to simulation_history.json in current working directory
    output_file = str(Path.cwd() / "simulation_history.json")
```

**Benefits:**
- Output goes to current directory (expected CLI behavior)
- Package stays clean (no data files)
- Better separation of code and data
- More intuitive for users

### Error Handling

Added better error messages:
```python
try:
    from ghost_kg.visualization import export_history
except ImportError as e:
    print("❌ Error: Required dependencies are missing.")
    print(f"   {e}")
    print("   Install with: pip install -e .")
    sys.exit(1)
```

## Testing

### Server Access
✅ HTML served correctly with text/html MIME type
✅ CSS served correctly with text/css MIME type
✅ JS served correctly with application/javascript MIME type
✅ JSON data served from arbitrary path
✅ No 403 errors on any route

### Output Path
✅ Without `--output`: Creates `./simulation_history.json` in current directory
✅ With `--output path.json`: Creates file at specified path
✅ Help text shows: `(default: ./simulation_history.json)`

### Workflow
```bash
# Export creates file in current directory
$ cd /my/project
$ ghostkg export --database mydb.db --serve --browser
# Creates: /my/project/simulation_history.json

# Server starts and serves the visualization
🚀 Ghost KG Visualization Server
   JSON file: /my/project/simulation_history.json
   Server: http://localhost:5000
   Opening browser...

# Browser opens and shows visualization without 403 error
```

## Files Changed

1. **ghost_kg/cli.py**:
   - Fixed Flask configuration (removed static_folder)
   - Changed from `send_from_directory()` to `send_file()`
   - Added explicit MIME types
   - Changed default output to `Path.cwd()`
   - Updated help text
   - Added better error handling

2. **docs/VISUALIZATION.md**:
   - Updated default output path in documentation

3. **docs/summaries/DEV_MODE_SUMMARY.md**:
   - Updated example commands to use current directory paths

## Impact

### User Experience
- ✅ Visualization server works reliably across different systems
- ✅ Files appear in expected location (current directory)
- ✅ Clear error messages when dependencies missing
- ✅ Intuitive CLI behavior

### Code Quality
- ✅ Simpler Flask configuration
- ✅ Clearer intent with explicit MIME types
- ✅ Better separation of concerns (code vs data)
- ✅ More maintainable

### Backward Compatibility
- ⚠️ **Minor Breaking Change**: Default output location changed
- ✅ Mitigation: Users can specify `--output` for custom paths
- ✅ Most users will prefer new behavior (current directory)

## Recommendations

For users who prefer the old behavior:
```bash
# Explicitly specify output path
ghostkg export --database db.db --output ghost_kg/templates/simulation_history.json
```

For developers:
- Keep visualization templates in package (code)
- Generate data files in user directories (data)
- Use `send_file()` for simple file serving
- Use explicit MIME types for clarity

## Conclusion

Both issues resolved:
1. ✅ Server returns proper HTTP responses (no 403 errors)
2. ✅ Output files go to current directory (expected behavior)

The fixes are minimal, focused, and improve user experience while maintaining code quality.
