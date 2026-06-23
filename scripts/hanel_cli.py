#!/usr/bin/env python3
"""CLI tool for manual testing of HanelWarehouseGateway against the mock server."""

from __future__ import annotations

import argparse
import dataclasses
import json
import logging
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
    "get_all_orders",
    "get_inventory",
    "cancel_order",
    "ping",
}


def build_config(args: argparse.Namespace) -> GatewayConfig:
    overrides: dict[str, object] = {}
    if args.endpoint:
        overrides["endpoint_url"] = args.endpoint
    if args.test_mode is not None:
        overrides["test_mode"] = args.test_mode
    if args.test_prefix is not None:
        overrides["test_prefix"] = args.test_prefix
    if args.lot_management is not None:
        overrides["lot_management_enabled"] = args.lot_management
    # --verbose is a shortcut; explicit --log-* flags below override it.
    if args.verbose:
        overrides["log_level"] = "DEBUG"
        overrides["log_soap_payloads"] = True
    if args.log_level is not None:
        overrides["log_level"] = args.log_level
    if args.log_soap_payloads is not None:
        overrides["log_soap_payloads"] = args.log_soap_payloads
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
    if operation == "get_all_orders":
        return [dataclasses.asdict(r) for r in gw.get_all_orders()]
    if operation == "get_inventory":
        return [dataclasses.asdict(r) for r in gw.get_inventory()]
    if operation == "cancel_order":
        return gw.cancel_order(data["order_number"])
    if operation == "ping":
        return gw.ping()
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
    parser.add_argument(
        "--test-mode",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Override HANEL_TEST_MODE (prepends test prefix to order/article numbers)",
    )
    parser.add_argument("--test-prefix", metavar="STR", help="Override HANEL_TEST_PREFIX from .env")
    parser.add_argument(
        "--lot-management",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Override HANEL_LOT_MANAGEMENT_ENABLED (V02/V03/V04 ops with batch_number)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Override HANEL_LOG_LEVEL from .env",
    )
    parser.add_argument(
        "--log-soap-payloads",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Override HANEL_LOG_SOAP_PAYLOADS from .env",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Shortcut for --log-level DEBUG --log-soap-payloads",
    )
    args = parser.parse_args()

    data = load_input(args)

    try:
        config = build_config(args)
        # Install a stderr handler so the library logs become visible. The level
        # honors HANEL_LOG_LEVEL from .env; --verbose forces DEBUG (and payload
        # logging) via build_config, overriding the .env values.
        logging.basicConfig(
            stream=sys.stderr,
            level=getattr(logging, config.log_level, logging.INFO),
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
        gw = HanelWarehouseGateway(config)
        result = run(args.operation, data, gw)
        print(json.dumps({"ok": True, "result": result}, indent=2, default=str))
    except HanelGatewayError as exc:
        error: dict[str, object] = {"ok": False, "type": type(exc).__name__}
        # Surface every diagnostic attribute the exception carries (operation,
        # detail, timestamp, fault_code/fault_string/fault_detail, http_status,
        # return_value, field/value) instead of just the summary message.
        error.update(vars(exc))
        print(json.dumps(error, indent=2, default=str))
        sys.exit(1)
    except KeyError as exc:
        print(json.dumps({"ok": False, "error": f"Missing required field: {exc}", "type": "KeyError"}, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
