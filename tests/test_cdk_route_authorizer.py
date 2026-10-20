from __future__ import annotations

import importlib.util
import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from aws_cdk import App
from aws_cdk.assertions import Template

ROOT = Path(__file__).resolve().parents[1]
_PUBLIC_ROUTE_KEY = "GET /health"
_AUTHORIZER_TYPES = frozenset({"AWS_IAM", "CUSTOM", "JWT"})


def _synthesized_routes() -> Mapping[str, Mapping[str, Any]]:
    spec = importlib.util.spec_from_file_location(
        "exclusao_cdk_app",
        ROOT / "cdk" / "app.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to load cdk/app.py")
    module = importlib.util.module_from_spec(spec)
    previous = Path.cwd()
    os.chdir(ROOT)
    try:
        spec.loader.exec_module(module)
        context = json.loads((ROOT / "cdk.json").read_text(encoding="utf-8")).get(
            "context", {}
        )
        app = App(context=context)
        stack = module.ExclusaoClienteStack(app, "ExclusaoClienteStack")
        template = Template.from_stack(stack)
    finally:
        os.chdir(previous)
    return template.find_resources("AWS::ApiGatewayV2::Route")


def test_every_http_route_has_authorizer_except_get_health() -> None:
    routes = _synthesized_routes()
    assert routes, "CDK synth produced no AWS::ApiGatewayV2::Route resources"

    offenders: list[str] = []
    for logical_id, resource in sorted(routes.items()):
        props = resource.get("Properties", {})
        route_key = props.get("RouteKey")
        if route_key == _PUBLIC_ROUTE_KEY:
            continue
        auth_type = props.get("AuthorizationType")
        missing_id = auth_type in {"CUSTOM", "JWT"} and "AuthorizerId" not in props
        if auth_type not in _AUTHORIZER_TYPES or missing_id:
            shown = route_key if isinstance(route_key, str) else "<non-literal RouteKey>"
            offenders.append(f"{logical_id}: {shown} AuthorizationType={auth_type!r}")

    assert not offenders, (
        "Every API route needs an authorizer except GET /health. Offenders:\n"
        + "\n".join(offenders)
    )
