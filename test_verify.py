#!/usr/bin/env python3
"""Quick verification test for ContractVersionRegistry and CompatibilityResolver"""

from main import ContractVersionRegistry, CompatibilityResolver

# Test 1: Register and query
reg = ContractVersionRegistry()
reg.register(
    tool_id="json_formatter",
    versions=["1.0", "1.1", "2.0"],
    deprecation={"1.0": "EOL 2026-01-01"}
)

assert reg.get_supported_versions("json_formatter") == ["1.0", "1.1", "2.0"]
print("✓ Registration works")

# Test 2: Deprecation
assert reg.is_deprecated("json_formatter", "1.0") == True
assert reg.get_deprecation_info("json_formatter", "1.0") == "EOL 2026-01-01"
assert reg.is_deprecated("json_formatter", "2.0") == False
print("✓ Deprecation tracking works")

# Test 3: Version matching
assert reg.find_best_match("json_formatter", "1.0") == "1.0"
assert reg.find_best_match("json_formatter", "1.1") == "1.1"
assert reg.find_best_match("json_formatter", "2.0") == "2.0"
print("✓ Exact version matching works")

# Test 4: Unknown version returns None
assert reg.find_best_match("json_formatter", "3.0") is None
print("✓ Unknown version returns None")

# Test 5: Unknown tool returns None
assert reg.find_best_match("unknown_tool", "1.0") is None
print("✓ Unknown tool returns None")

# Test 6: Shims
reg.register(
    tool_id="api_client",
    versions=["2.0"],
    shims={"1.0->2.0": lambda x: {"transformed": True, "data": x}}
)
assert reg.find_best_match("api_client", "1.0") == "2.0"
shim = reg.get_shim("api_client", "1.0", "2.0")
assert shim is not None
assert shim({"test": "data"}) == {"transformed": True, "data": {"test": "data"}}
print("✓ Shim handling works")

# Test 7: List tools
tools = reg.list_tools()
assert "json_formatter" in tools
assert "api_client" in tools
print("✓ Tool listing works")

print("\nAll tests passed! ✓")

# Test 8: CompatibilityResolver - direct call
reg = ContractVersionRegistry()
reg.register(tool_id="test_tool", versions=["1.0", "2.0"])
resolver = CompatibilityResolver(reg)

result = resolver.resolve("test_tool", "1.0", None)
assert result['action'] == 'call'
assert result['version'] == '1.0'
print("✓ Resolver direct call works")

# Test 9: CompatibilityResolver - shim path
reg.register(
    tool_id="legacy_tool",
    versions=["2.0"],
    shims={"1.0->2.0": lambda x: {"v2": x}}
)
result = resolver.resolve("legacy_tool", "1.0", ["2.0"])
assert result['action'] == 'shim'
assert result['version'] == '2.0'
assert result['shim'] is not None
print("✓ Resolver shim handling works")

# Test 10: CompatibilityResolver - reject unknown tool
result = resolver.resolve("unknown", "1.0", None)
assert result['action'] == 'reject'
assert 'not registered' in result['reason']
print("✓ Resolver rejects unknown tool")

# Test 11: CompatibilityResolver - reject no compatible version
reg.register(tool_id="v3_only", versions=["3.0"])
result = resolver.resolve("v3_only", "1.0", None)
assert result['action'] == 'reject'
assert 'No compatible' in result['reason']
print("✓ Resolver rejects incompatible version")
