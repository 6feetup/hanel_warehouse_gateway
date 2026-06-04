#!/usr/bin/env python3
"""CLI tool for manual testing of HanelWarehouseGateway against the mock server."""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys

from hanel_warehouse_gateway import (
    GatewayConfig,
    HanelGatewayError,
    HanelWarehouseGateway,
    MovementLine,
)

OPERATIONS = {
    "register_article",
    "send_movement_order",
    "get_completed_movements",
    "cancel_order",
}


def build_config(args: argparse.Namespace) -> GatewayConfig:
    overrides: dict[str, object] = {}
    if args.endpoint:
        overrides["endpoint_url"] = args.endpoint
    if args.test_mode:
        overrides["test_mode"] = True
    return GatewayConfig.from_env(overrides if overrides else None)


def run(operation: str, data: dict, gw: HanelWarehouseGateway) -> object:
    if operation == "register_article":
        return gw.register_article(
            data["article_number"],
            data["article_name"],
            data.get("batch_number"),
        )
    if operation == "send_movement_order":
        positions = [MovementLine(**p) for p in data["positions"]]
        return gw.send_movement_order(data["order_number"], positions)
    if operation == "get_completed_movements":
        return [dataclasses.asdict(r) for r in gw.get_completed_movements()]
    if operation == "cancel_order":
        return gw.cancel_order(data["order_number"])
    raise ValueError(f"Unknown operation: {operation}")


def load_input(args: argparse.Namespace) -> dict:
    if args.input:
        with open(args.input) as f:
            return json.load(f)
    if not sys.stdin.isatty():
        raw = sys.stdin.read().strip()
        return json.loads(raw) if raw else {}
    return {}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Hanel gateway CLI — manual testing tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="See scripts/README.md for examples and JSON schemas.",
    )
    parser.add_argument("operation", choices=sorted(OPERATIONS))
    parser.add_argument("--input", metavar="FILE", help="JSON file with operation parameters (default: stdin)")
    parser.add_argument("--endpoint", metavar="URL", help="Override HANEL_ENDPOINT_URL from .env")
    parser.add_argument("--test-mode", action="store_true", help="Enable test_mode (prepends test prefix to order numbers)")
    args = parser.parse_args()

    data = load_input(args)

    try:
        gw = HanelWarehouseGateway(build_config(args))
        result = run(args.operation, data, gw)
        print(json.dumps({"ok": True, "result": result}, indent=2, default=str))
    except HanelGatewayError as exc:
        print(json.dumps({"ok": False, "error": str(exc), "type": type(exc).__name__}, indent=2))
        sys.exit(1)
    except KeyError as exc:
        print(json.dumps({"ok": False, "error": f"Missing required field: {exc}", "type": "KeyError"}, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
