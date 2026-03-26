from main import ContractVersionRegistry, CompatibilityResolver

# Test the full workflow as shown in the README
registry = ContractVersionRegistry()
registry.register("my_tool", ["1.0", "2.0"], shims={"1.0->2.0": lambda p: p})

resolver = CompatibilityResolver(registry)

# Test exact version match
result = resolver.resolve("my_tool", "1.0", None)
print("Test 1 - Exact version match:")
print(result)
print()

# Test shim version
result = resolver.resolve("my_tool", "1.0", None)
print("Test 2 - Shim version:")
print(result)
print()

# Test unknown tool
result = resolver.resolve("unknown_tool", "1.0", None)
print("Test 3 - Unknown tool:")
print(result)
print()

# Test unsupported version
result = resolver.resolve("my_tool", "3.0", None)
print("Test 4 - Unsupported version:")
print(result)