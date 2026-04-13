import sys
import os
import asyncio
from io import BytesIO

# Limit OpenBLAS threads to avoid resource exhaustion on shared hosting
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

# Ensure the project root and src directory are in the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(script_dir, "src")
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Import the FastAPI application
from src.endpoints.getData import app


class ASGItoWSGI:
    """Convert an ASGI application to WSGI."""

    def __init__(self, asgi_app):
        self.asgi_app = asgi_app

    def __call__(self, environ, start_response):
        """WSGI application interface."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            return loop.run_until_complete(self._handle(environ, start_response))
        finally:
            loop.close()

    async def _handle(self, environ, start_response):
        """Handle the WSGI request by converting it to ASGI."""
        # Build the ASGI scope from WSGI environ
        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": environ.get("SERVER_PROTOCOL", "HTTP/1.0").split("/")[1],
            "method": environ["REQUEST_METHOD"],
            "scheme": environ.get("wsgi.url_scheme", "http"),
            "path": environ.get("PATH_INFO", "/"),
            "query_string": environ.get("QUERY_STRING", "").encode("latin1"),
            "root_path": environ.get("SCRIPT_NAME", ""),
            "headers": self._get_headers(environ),
            "server": (
                environ.get("SERVER_NAME", "localhost"),
                int(environ.get("SERVER_PORT", 80)),
            ),
        }

        # Add client info if available
        if "REMOTE_ADDR" in environ:
            scope["client"] = (
                environ["REMOTE_ADDR"],
                int(environ.get("REMOTE_PORT", 0)),
            )

        # Handle request body safely
        body = b""
        try:
            content_length = int(environ.get("CONTENT_LENGTH", 0))
            if content_length > 0:
                wsgi_input = environ.get("wsgi.input")
                if wsgi_input:
                    body = wsgi_input.read(content_length)
        except (ValueError, TypeError):
            # If content_length is invalid, try to read without size
            wsgi_input = environ.get("wsgi.input")
            if wsgi_input:
                try:
                    body = wsgi_input.read()
                except Exception:
                    body = b""

        # Response storage
        response = {"status": None, "headers": [], "body": []}

        async def receive():
            return {
                "type": "http.request",
                "body": body,
                "more_body": False,
            }

        async def send(message):
            if message["type"] == "http.response.start":
                response["status"] = message["status"]
                response["headers"] = message.get("headers", [])
            elif message["type"] == "http.response.body":
                response["body"].append(message.get("body", b""))

        # Call the ASGI app
        await self.asgi_app(scope, receive, send)

        # Convert response to WSGI format
        status_text = f"{response['status']} OK"
        headers = [
            (k.decode("latin1"), v.decode("latin1")) for k, v in response["headers"]
        ]

        start_response(status_text, headers)
        return [b"".join(response["body"])]

    def _get_headers(self, environ):
        """Extract headers from WSGI environ."""
        headers = []
        for key, value in environ.items():
            if key.startswith("HTTP_"):
                # Convert HTTP_HEADER_NAME to header-name
                header_name = key[5:].replace("_", "-").lower().encode("latin1")
                headers.append((header_name, value.encode("latin1")))
            elif key in ("CONTENT_TYPE", "CONTENT_LENGTH"):
                header_name = key.replace("_", "-").lower().encode("latin1")
                headers.append((header_name, value.encode("latin1")))
        return headers


# Create the WSGI application
application = ASGItoWSGI(app)
