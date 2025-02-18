import logging
from threading import Thread
from flask import Flask

logger = logging.getLogger(__name__)
keep_alive_app = Flask(__name__)

@keep_alive_app.route('/health')
def health_check():
    return "AurumBot Trading Platform is online! 🚀"

def run_keep_alive():
    keep_alive_app.run(host='0.0.0.0', port=8080, debug=False)

def keep_alive():
    thread = Thread(target=run_keep_alive)
    thread.daemon = True
    thread.start()
    logger.info("Keep-alive server started on port 8080")