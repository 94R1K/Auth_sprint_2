from .config import settings


LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": LOG_FORMAT,
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": (
                "%(levelprefix)s %(client_addr)s - '%(request_line)s' %(status_code)s"
            ),
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "verbose",
            "stream": "ext://sys.stdout",
        },
        "access": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "access",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "uvicorn.error": {
            "level": "INFO",
        },
        "uvicorn.access": {
            "handlers": ["access"],
            "level": "INFO",
            "propagate": False,
        },
        "sqlalchemy.engine": {
            "handlers": [],
            "level": settings.sqlalchemy_log_level,
            "propagate": True,
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
}
