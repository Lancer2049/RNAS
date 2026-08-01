"""Structured JSON logging — zero external dependencies.

Configures the root 'rnas-api' logger to emit newline-delimited JSON so
logs can be piped to Loki/ELK. A request id is threaded through via a
ContextVar and attached to each record when set.
"""

import json
import logging
import os
import sys
import time
import uuid
from contextvars import ContextVar

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": request_id_ctx.get(),
        }
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        for k, v in getattr(record, "extra_fields", {}).items():
            entry[k] = v
        return json.dumps(entry, ensure_ascii=False)


def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    if os.environ.get("RNAS_ENV") == "development":
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s %(message)s"))
    else:
        handler.setFormatter(JsonFormatter())
    root = logging.getLogger("rnas-api")
    root.handlers[:] = [handler]
    root.setLevel(logging.INFO)


def get_logger(name: str = "rnas-api"):
    return logging.getLogger(name)
