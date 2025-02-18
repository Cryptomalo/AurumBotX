import logging
from flask import Flask
from threading import Thread
from werkzeug.serving import make_server

logger = logging.getLogger(__name__)

app = Flask(__name__)
server = None
thread = None

@app.route('/')
def index():
    return "AurumBot Trading Platform is online! 🚀"

class ServerThread(Thread):
    def __init__(self, app):
        Thread.__init__(self)
        self.server = make_server('0.0.0.0', 8080, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        logger.info("Starting keep-alive server on port 8080")
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()

def keep_alive():
    global server, thread
    if thread is None or not thread.is_alive():
        try:
            thread = ServerThread(app)
            thread.daemon = True  # Set as daemon so it will be killed when main thread exits
            thread.start()
            logger.info("Keep-alive server started successfully")
        except Exception as e:
            logger.error(f"Failed to start keep-alive server: {e}")