import logging
import sys
from flask import Flask, jsonify
from keep_alive import keep_alive

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route("/")
def index():
    logger.info("Index endpoint called")
    return jsonify({"message": "AurumBot Dashboard"})

@app.route("/health")
def health_check():
    """Keep-alive endpoint"""
    logger.info("Health check endpoint called")
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    try:
        # Start the keep-alive server in a separate thread
        keep_alive()
        logger.info("Starting main Flask application on port 3000")

        # Start the main application
        app.run(
            host="0.0.0.0", 
            port=3000,
            debug=False
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)