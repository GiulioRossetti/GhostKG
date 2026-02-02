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
        from flask import Flask, send_from_directory, jsonify
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
    app = Flask(__name__, static_folder=str(templates_dir))
    
    @app.route('/')
    def index():
        return send_from_directory(str(templates_dir), 'index.html')
    
    @app.route('/style.css')
    def style():
        return send_from_directory(str(templates_dir), 'style.css')
    
    @app.route('/app.js')
    def app_js():
        return send_from_directory(str(templates_dir), 'app.js')
    
    @app.route('/simulation_history.json')
    def data():
        """Serve the specified JSON file as simulation_history.json."""
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            return jsonify(data)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    # Print startup message
    host = args.host
    port = args.port
    url = f"http://{host}:{port}"
    
    print("=" * 70)
    print("🚀 Ghost KG Visualization Server")
    print("=" * 70)
    print(f"   JSON file: {json_path}")
    print(f"   Server: {url}")
    print(f"   Press Ctrl+C to stop")
    print("=" * 70)
    
    # Open browser if requested
    if args.browser:
        import webbrowser
        import time
        print(f"   Opening browser...")
        time.sleep(1)  # Give server time to start
        webbrowser.open(url)
    
    # Run server
    try:
        app.run(host=host, port=port, debug=args.debug)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")


def export_command(args):
    """Export interaction history to JSON."""
    # Import visualization module only when needed
    from ghost_kg.visualization import export_history
    
    # Check if database exists
    db_path = Path(args.database).resolve()
    if not db_path.exists() and not args.database.startswith(('postgresql:', 'mysql:', 'sqlite:')):
        print(f"❌ Error: Database not found: {db_path}")
        sys.exit(1)
    
    # Determine output file
    output_file = args.output
    if not output_file:
        # Default to simulation_history.json in templates directory
        templates_dir = Path(__file__).parent / "templates"
        output_file = str(templates_dir / "simulation_history.json")
    
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
        help='Output JSON file (default: templates/simulation_history.json)'
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
