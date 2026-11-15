from ipaddress import ip_address
from typing import Annotated

from fastapi import Depends, Request


def get_client_ip(request: Request) -> str:
    return (
        ip_address(request.client.host).compressed
        if request.client is not None
        else "unknown"
    )


def get_user_agent(request: Request) -> str | None:
    return request.headers.get("user-agent")


def get_endpoint_key(request: Request) -> str:
    route = request.scope.get("route")

    if route is None:
        return f"{request.method}:unknown"

    endpoint = getattr(route, "path", request.url.path)

    return f"{request.method}:{endpoint}"


ClientIPDependency = Annotated[
    str,
    Depends(get_client_ip),
]

UserAgentDependency = Annotated[
    str | None,
    Depends(get_user_agent),
]

EndpointKeyDependency = Annotated[
    str,
    Depends(get_endpoint_key)
]
