"""Bound request bodies before multipart parsing can spool to disk."""

from fastapi.responses import JSONResponse
from ..config import settings


class BodyLimit:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] != "POST":
            return await self.app(scope, receive, send)
        maximum = settings.max_upload + 64 * 1024
        headers = dict(scope["headers"])
        try:
            declared = int(headers.get(b"content-length", b"0"))
        except ValueError:
            declared = maximum + 1
        if declared > maximum:
            return await JSONResponse({"detail": "Upload is too large."}, 413)(scope, receive, send)
        chunks = []
        size = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            size += len(message.get("body", b""))
            if size > maximum:
                return await JSONResponse({"detail": "Upload is too large."}, 413)(scope, receive, send)
            chunks.append(message.get("body", b""))
            if not message.get("more_body", False):
                break
        body = b"".join(chunks)
        chunks.clear()
        delivered = False

        async def limited_receive():
            nonlocal delivered, body
            if delivered:
                return await receive()
            delivered = True
            message = {"type": "http.request", "body": body, "more_body": False}
            body = b""
            return message

        await self.app(scope, limited_receive, send)
