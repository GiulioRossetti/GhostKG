"""
Ghost KG Command Line Interface

Provides CLI commands for visualization and history export.
"""

import argparse
import sys
import os
from pathlib import Path


def serve_command(args):
    """Serve the visualization web interface."""
    try:
        from flask import Flask, send_file, jsonify
        import json
    except ImportError:
        print("❌ Error: Flask is required for the serve command.")
        print("   Install with: pip install ghost_kg[viz]")
        sys.exit(1)
    
    # Determine paths
    templates_dir = Path(__file__).parent / "templates"
    
    # Check if JSON file exists
    json_path = Path(args.json_file).resolve()
    if not json_path.exists():
        print(f"❌ Error: JSON file not found: {json_path}")
        sys.exit(1)
    
    # Create Flask app
    app = Flask(__name__)
    
    # Add request logging for debugging
    @app.before_request
    def log_request():
        from flask import request
        if args.debug:
            print(f"[DEBUG] {request.method} {request.path} from {request.remote_addr}")
    
    @app.route('/')
    def index():
        """Serve the main HTML page."""
        index_path = templates_dir / 'index.html'
        if not index_path.exists():
            return f"Error: Template file not found: {index_path}", 404
        return send_file(index_path, mimetype='text/html')
    
    @app.route('/style.css')
    def style():
        """Serve the CSS stylesheet."""
        css_path = templates_dir / 'style.css'
        if not css_path.exists():
            return f"Error: CSS file not found: {css_path}", 404
        return send_file(css_path, mimetype='text/css')
    
    @app.route('/app.js')
    def app_js():
        """Serve the JavaScript application."""
        js_path = templates_dir / 'app.js'
        if not js_path.exists():
            return f"Error: JavaScript file not found: {js_path}", 404
        return send_file(js_path, mimetype='application/javascript')
    
    @app.route('/simulation_history.json')
    def data():
        """Serve the specified JSON file as simulation_history.json."""
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            return jsonify(data)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.errorhandler(403)
    def forbidden(e):
        """Handle 403 Forbidden errors."""
        return f"403 Forbidden: {e}", 403
    
    @app.errorhandler(404)
    def not_found(e):
        """Handle 404 Not Found errors."""
        return f"404 Not Found: {e}", 404
    
    @app.errorhandler(500)
    def internal_error(e):
        """Handle 500 Internal Server errors."""
        return f"500 Internal Server Error: {e}", 500
    
    # Print startup message
    host = args.host
    port = args.port
    # Use 127.0.0.1 instead of localhost for URL to avoid DNS issues
    display_host = '127.0.0.1' if host in ['localhost', '127.0.0.1'] else host
    url = f"http://{display_host}:{port}"
    
    print("=" * 70)
    print("🚀 Ghost KG Visualization Server")
    print("=" * 70)
    print(f"   JSON file: {json_path}")
    print(f"   Server: {url}")
    if args.debug:
        print(f"   Debug mode: ON")
    print(f"   Press Ctrl+C to stop")
    print("=" * 70)
    
    # Verify template files exist
    for file, desc in [('index.html', 'HTML'), ('style.css', 'CSS'), ('app.js', 'JavaScript')]:
        file_path = templates_dir / file
        if not file_path.exists():
            print(f"⚠️  Warning: {desc} file not found: {file_path}")
    
    # Open browser if requested (in a separate thread to avoid blocking)
    if args.browser:
        import webbrowser
        import threading
        import time
        
        def open_browser():
            time.sleep(2)  # Give server more time to start
            print(f"   Opening browser at {url}...")
            webbrowser.open(url)
        
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
    
    # Run server with threading enabled for better concurrency
    try:
        # Use use_reloader=False to avoid issues with threading
        app.run(host=host, port=port, debug=args.debug, threaded=True, use_reloader=False)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except OSError as e:
        if 'Address already in use' in str(e):
            print(f"\n❌ Error: Port {port} is already in use")
            print(f"   Try a different port with --port <number>")
        else:
            print(f"\n❌ Error starting server: {e}")
        sys.exit(1)


def export_command(args):
    """Export interaction history to JSON."""
    # Import visualization module only when needed
    try:
        from ghost_kg.visualization import export_history
    except ImportError as e:
        print("❌ Error: Required dependencies are missing.")
        print(f"   {e}")
        print("   Install with: pip install -e .")
        sys.exit(1)
    
    # Check if database exists
    db_path = Path(args.database).resolve()
    if not db_path.exists() and not args.database.startswith(('postgresql:', 'mysql:', 'sqlite:')):
        print(f"❌ Error: Database not found: {db_path}")
        sys.exit(1)
    
    # Determine output file
    output_file = args.output
    if not output_file:
        # Default to simulation_history.json in current working directory
        output_file = str(Path.cwd() / "simulation_history.json")
    
    # Parse agents list
    agents = None
    if args.agents:
        agents = [a.strip() for a in args.agents.split(',')]
    
    print("=" * 70)
    print("📊 Exporting Ghost KG History")
    print("=" * 70)
    print(f"   Database: {db_path if not args.database.startswith(('postgresql:', 'mysql:', 'sqlite:')) else args.database}")
    print(f"   Output: {output_file}")
    if agents:
        print(f"   Agents: {', '.join(agents)}")
    print("=" * 70)
    
    try:
        history = export_history(
            db_path=str(db_path) if not args.database.startswith(('postgresql:', 'mysql:', 'sqlite:')) else args.database,
            output_file=output_file,
            agents=agents,
            topic=args.topic
        )
        
        print("=" * 70)
        print("✅ Export completed successfully!")
        print("=" * 70)
        
        if args.serve:
            print("\n🚀 Starting visualization server...")
            # Create args object for serve command
            serve_args = argparse.Namespace(
                json_file=output_file,
                host=args.host,
                port=args.port,
                browser=args.browser,
                debug=False
            )
            serve_command(serve_args)
    
    except Exception as e:
        print(f"❌ Error during export: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='ghostkg',
        description='Ghost KG - Command Line Interface',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export history and serve visualization
  ghostkg export --database agent_memory.db --serve --browser
  
  # Export history only
  ghostkg export --database agent_memory.db --output history.json
  
  # Serve existing JSON file
  ghostkg serve --json history.json --browser
  
  # Serve with custom host/port
  ghostkg serve --json history.json --host 0.0.0.0 --port 8080
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Serve command
    serve_parser = subparsers.add_parser(
        'serve',
        help='Start web server for visualization'
    )
    serve_parser.add_argument(
        '--json', '--json-file',
        dest='json_file',
        required=True,
        help='Path to JSON history file'
    )
    serve_parser.add_argument(
        '--host',
        default='localhost',
        help='Host to bind server (default: localhost)'
    )
    serve_parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to bind server (default: 5000)'
    )
    serve_parser.add_argument(
        '--browser',
        action='store_true',
        help='Open browser automatically'
    )
    serve_parser.add_argument(
        '--debug',
        action='store_true',
        help='Run server in debug mode'
    )
    
    # Export command
    export_parser = subparsers.add_parser(
        'export',
        help='Export interaction history to JSON'
    )
    export_parser.add_argument(
        '--database', '--db',
        dest='database',
        required=True,
        help='Path to database file or connection string'
    )
    export_parser.add_argument(
        '--output', '-o',
        help='Output JSON file (default: ./simulation_history.json)'
    )
    export_parser.add_argument(
        '--agents', '-a',
        help='Comma-separated list of agent names (default: auto-detect)'
    )
    export_parser.add_argument(
        '--topic', '-t',
        default='Knowledge Graph Evolution',
        help='Title/topic for visualization'
    )
    export_parser.add_argument(
        '--serve',
        action='store_true',
        help='Start server after export'
    )
    export_parser.add_argument(
        '--browser',
        action='store_true',
        help='Open browser (requires --serve)'
    )
    export_parser.add_argument(
        '--host',
        default='localhost',
        help='Server host (requires --serve)'
    )
    export_parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Server port (requires --serve)'
    )
    
    # Parse args
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Route to appropriate command
    if args.command == 'serve':
        serve_command(args)
    elif args.command == 'export':
        export_command(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
