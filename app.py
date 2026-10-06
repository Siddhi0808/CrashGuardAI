# Forwarding launcher for CrashGuard AI Web Application
import sys, os
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from web.app import app

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5001))
    # Debug mode exposes the Werkzeug debugger; enable only locally with FLASK_DEBUG=1
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug, host=host, port=port)
