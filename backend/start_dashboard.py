#!/usr/bin/env python3
"""
Analytics Dashboard Launcher

Simple launcher script to start both the analytics API backend
and serve the frontend dashboard simultaneously.

Features:
- Starts FastAPI analytics backend on port 8001
- Serves HTML dashboard frontend on port 8002
- Handles graceful shutdown of both services

Author: Vermont Deer Prediction System
Version: 1.0.0
"""

import asyncio
import threading
import time
import logging
import sys
import signal
from pathlib import Path
import http.server
import socketserver

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DashboardHTTPHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler for dashboard frontend"""
    
    def __init__(self, *args, **kwargs):
        # Set the directory to serve files from
        self.dashboard_dir = Path(__file__).parent.parent / "frontend" / "dashboard"
        super().__init__(*args, directory=str(self.dashboard_dir), **kwargs)
    
    def end_headers(self):
        # Add CORS headers for API communication
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def log_message(self, format, *args):
        # Custom logging format
        logger.info(f"Dashboard: {format % args}")

class AnalyticsDashboardLauncher:
    """Launcher for analytics dashboard with API backend and frontend"""
    
    def __init__(self):
        self.api_task = None
        self.frontend_server = None
        self.frontend_thread = None
        self.running = False
        
        # Ports
        self.api_port = 8001
        self.frontend_port = 8002
        
    def start_frontend_server(self):
        """Start the frontend HTTP server"""
        try:
            handler = DashboardHTTPHandler
            self.frontend_server = socketserver.TCPServer(
                ("", self.frontend_port), 
                handler
            )
            
            logger.info(f"🌐 Frontend dashboard server starting on http://localhost:{self.frontend_port}")
            
            # Start server in thread
            self.frontend_thread = threading.Thread(
                target=self.frontend_server.serve_forever,
                daemon=True,
                name="DashboardFrontend"
            )
            self.frontend_thread.start()
            
            logger.info(f"✅ Frontend dashboard available at http://localhost:{self.frontend_port}")
            
        except Exception as e:
            logger.error(f"Failed to start frontend server: {e}")
            raise
    
    async def start_api_server(self):
        """Start the analytics API server"""
        try:
            import uvicorn
            from analytics.dashboard_api import app
            
            # Configure uvicorn
            config = uvicorn.Config(
                app,
                host="0.0.0.0",
                port=self.api_port,
                log_level="info",
                access_log=True
            )
            
            server = uvicorn.Server(config)
            
            logger.info(f"🚀 Analytics API server starting on http://localhost:{self.api_port}")
            
            # Start server
            await server.serve()
            
        except Exception as e:
            logger.error(f"Failed to start API server: {e}")
            raise
    
    async def start_dashboard(self):
        """Start both frontend and API servers"""
        try:
            self.running = True
            
            logger.info("🎯 Starting Vermont Deer Prediction Analytics Dashboard")
            logger.info("=" * 60)
            
            # Start frontend server
            self.start_frontend_server()
            
            # Give frontend a moment to start
            await asyncio.sleep(1)
            
            # Start API server (this will block)
            await self.start_api_server()
            
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
            await self.shutdown()
        except Exception as e:
            logger.error(f"Error starting dashboard: {e}")
            await self.shutdown()
            raise
    
    async def shutdown(self):
        """Gracefully shutdown both servers"""
        logger.info("🛑 Shutting down analytics dashboard...")
        
        self.running = False
        
        # Shutdown frontend server
        if self.frontend_server:
            try:
                self.frontend_server.shutdown()
                self.frontend_server.server_close()
                logger.info("✅ Frontend server stopped")
            except Exception as e:
                logger.error(f"Error stopping frontend server: {e}")
        
        # API server shutdown handled by uvicorn
        logger.info("✅ Dashboard shutdown complete")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum):
            logger.info(f"Received signal {signum}")
            # Create new event loop if needed
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            if loop.is_running():
                loop.create_task(self.shutdown())
            else:
                loop.run_until_complete(self.shutdown())
            
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)

async def main():
    """Main launcher function"""
    launcher = AnalyticsDashboardLauncher()
    launcher.setup_signal_handlers()
    
    try:
        await launcher.start_dashboard()
    except Exception as e:
        logger.error(f"Dashboard startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🦌 Vermont Deer Prediction Analytics Dashboard")
    print("=" * 50)
    print("Starting integrated analytics dashboard...")
    print()
    print("Services:")
    print("- Analytics API:    http://localhost:8001")
    print("- Dashboard UI:     http://localhost:8002")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        # Check if we can import required modules
        import uvicorn
        
        # Run the dashboard
        asyncio.run(main())
        
    except ImportError as e:
        print(f"❌ Missing required packages: {e}")
        print("Please install required packages:")
        print("pip install fastapi uvicorn psutil")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
        sys.exit(0)
