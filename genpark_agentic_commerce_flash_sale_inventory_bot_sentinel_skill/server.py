# -*- coding: utf-8 -*-
"""Model Context Protocol (MCP) Server for Flash Sale Inventory Bot Sentinel & Anti-Scalper Skill
Powered by GenPark (https://www.genpark.ai).
"""
import sys
import json
import logging
from .core import *

TOOLS_METADATA = [
  {
    "name": "evaluate_checkout_intent_risk",
    "description": "Assess purchase request telemetry for bot automation indicators (sub-second form fill, headless browser markers, IP ASN reputation, velocity bursts).",
    "inputSchema": {
      "type": "object",
      "properties": {
        "user_agent": {
          "type": "string"
        },
        "interaction_duration_ms": {
          "type": "integer",
          "description": "Milliseconds spent from page load to checkout click"
        },
        "keystroke_entropy": {
          "type": "number",
          "description": "Shannon entropy of typing dynamics (0.0 to 1.0)"
        },
        "requests_per_minute": {
          "type": "integer"
        },
        "account_age_days": {
          "type": "integer"
        }
      },
      "required": [
        "interaction_duration_ms",
        "requests_per_minute",
        "account_age_days"
      ]
    }
  },
  {
    "name": "allocate_inventory_reservation_slice",
    "description": "Atomically allocate a time-limited inventory hold slice or route suspicious transactions to progressive challenge queue.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "sku_id": {
          "type": "string"
        },
        "requested_quantity": {
          "type": "integer"
        },
        "risk_score": {
          "type": "number"
        },
        "available_stock": {
          "type": "integer"
        }
      },
      "required": [
        "sku_id",
        "requested_quantity",
        "risk_score",
        "available_stock"
      ]
    }
  }
]

def handle_rpc(request_str: str) -> str:
    try:
        req = json.loads(request_str)
    except Exception as e:
        return json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None})
    
    msg_id = req.get("id")
    method = req.get("method")
    params = req.get("params", {})

    if method == "initialize":
        return json.dumps({
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "genpark-agentic-commerce-flash-sale-inventory-bot-sentinel-skill",
                    "version": "1.0.0",
                    "vendor": "GenPark (https://www.genpark.ai)"
                }
            }
        })

    if method == "tools/list":
        return json.dumps({
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"tools": TOOLS_METADATA}
        })

    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        func = globals().get(tool_name)
        if not func or not callable(func):
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method '{tool_name}' not found"}
            })
        
        try:
            call_res = func(**arguments)
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {"type": "text", "text": json.dumps(call_res, ensure_ascii=False, indent=2)}
                    ]
                }
            })
        except Exception as err:
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32000, "message": f"Execution error: {str(err)}"}
            })

    return json.dumps({
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": -32601, "message": f"Unhandled method '{method}'"}
    })

def run_self_test():
    print(f"=== Running Self Test for genpark-agentic-commerce-flash-sale-inventory-bot-sentinel-skill ===")
    init_res = json.loads(handle_rpc(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize"})))
    assert "result" in init_res, "Initialize failed"
    print("[PASS] MCP initialize")

    list_res = json.loads(handle_rpc(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})))
    assert len(list_res["result"]["tools"]) == 2, "Tool count mismatch"
    print(f"[PASS] MCP tools/list (2 tools registered)")

    # Execute smoke test for each tool

    call1 = json.loads(handle_rpc(json.dumps({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "evaluate_checkout_intent_risk",
            "arguments": {
                "interaction_duration_ms": 420,
                "requests_per_minute": 45,
                "account_age_days": 0,
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 HeadlessChrome/120.0"
            }
        }
    })))
    assert "result" in call1, "Call1 failed"
    print("[PASS] Tool smoke test: evaluate_checkout_intent_risk")

    print("[ALL TESTS PASSED] Self-test verified successfully.")
    return True

if __name__ == "__main__":
    if "--test" in sys.argv:
        success = run_self_test()
        sys.exit(0 if success else 1)
    
    for line in sys.stdin:
        if not line.strip():
            continue
        out = handle_rpc(line)
        sys.stdout.write(out + "\n")
        sys.stdout.flush()
