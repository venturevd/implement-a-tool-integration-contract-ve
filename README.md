# Tool Integration Contract Version Router

Routes agent→tool calls to the appropriate contract version using ContractVersionRegistry.

Python 3 only; no external dependencies.

```python
from main import ContractVersionRegistry, CompatibilityResolver

registry = ContractVersionRegistry()
registry.register("my_tool", ["1.0","2.0"], shims={"1.0->2.0": lambda p: p})
resolver = CompatibilityResolver(registry)
result = resolver.resolve("my_tool","1.0",None)

if result['action']=='call':
    call_tool(result['version'])
elif result['action']=='shim':
    call_tool(result['version'], result['shim'](payload))
else:
    raise RuntimeError(result['reason'])
```

## CLI

```bash
python3 main.py --help
python3 main.py register my_tool 1.0 2.0
python3 main.py list
python3 main.py check my_tool 1.0
```
