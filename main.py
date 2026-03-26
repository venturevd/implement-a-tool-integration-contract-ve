import argparse


class ContractVersionRegistry:
    """Registry for managing tool contract version compatibility.

    Stores supported versions, deprecation information, and compatibility shims
    for each registered tool. Used to route agent tool calls to appropriate
    contract versions at runtime.
    """

    def __init__(self):
        """Initialize an empty contract version registry."""
        self._c = {}

    def register(self, tool_id, versions, deprecation=None, shims=None):
        """Register a tool with its supported contract versions.

        Args:
            tool_id (str): Unique identifier for the tool.
            versions (list): List of supported contract version strings.
            deprecation (dict, optional): Mapping of version -> deprecation info.
            shims (dict, optional): Mapping of "from->to" pairs to transform functions.
        """
        self._c[tool_id] = {'v': versions, 'd': deprecation or {}, 's': shims or {}}

    def get_supported_versions(self, tool_id):
        """Get list of supported versions for a tool.

        Args:
            tool_id (str): Tool identifier.

        Returns:
            list: Supported version strings, or empty list if tool not found.
        """
        c = self._c.get(tool_id)
        return c['v'] if c else []

    def is_deprecated(self, tool_id, version):
        """Check if a specific version is marked as deprecated.

        Args:
            tool_id (str): Tool identifier.
            version (str): Version string to check.

        Returns:
            bool: True if deprecated, False otherwise.
        """
        c = self._c.get(tool_id)
        return version in c['d'] if c else False

    def get_deprecation_info(self, tool_id, version):
        """Get deprecation information for a version.

        Args:
            tool_id (str): Tool identifier.
            version (str): Version string.

        Returns:
            str or None: Deprecation info if available, else None.
        """
        c = self._c.get(tool_id)
        return c['d'].get(version) if c else None

    def get_shim(self, tool_id, frm, to):
        """Retrieve shim/transform function for version conversion.

        Args:
            tool_id (str): Tool identifier.
            frm (str): Source version.
            to (str): Target version.

        Returns:
            callable or None: Shim function if defined, else None.
        """
        c = self._c.get(tool_id)
        return c['s'].get(f"{frm}->{to}") if c else None

    def find_best_match(self, tool_id, version):
        """Find the best compatible version for an agent's required version.

        Matching order:
        1. Exact version match (direct support)
        2. Shim-based transformation to a supported version
        3. None if no compatibility found

        Args:
            tool_id (str): Tool identifier.
            version (str): Required contract version.

        Returns:
            str or None: Compatible version string, or None if no match.
        """
        if tool_id not in self._c:
            return None
        if version in self._c[tool_id]['v']:
            return version
        for v in self._c[tool_id]['v']:
            if self.get_shim(tool_id, version, v):
                return v
        return None

    def list_tools(self):
        """Get all registered tool IDs.

        Returns:
            list: Tool identifier strings.
        """
        return list(self._c.keys())


class CompatibilityResolver:
    """Resolves contract versions for agent→tool calls at runtime.

    Uses a ContractVersionRegistry to determine compatibility and make
    deterministic routing decisions with safe fallbacks.
    """

    def __init__(self, registry):
        """Initialize with a ContractVersionRegistry.

        Args:
            registry: ContractVersionRegistry instance.
        """
        self.registry = registry

    def resolve(self, tool_id, agent_version, tool_capabilities, payload_fingerprint=None):
        """Resolve the appropriate contract version for a tool call.

        Args:
            tool_id (str): Tool identifier.
            agent_version (str): Agent's expected contract version.
            tool_capabilities (list): Tool's supported versions (overrides registry if provided).
            payload_fingerprint (str, optional): Hash of input payload structure.

        Returns:
            dict: Resolution decision with keys:
                - action: "call" | "shim" | "reject"
                - version: resolved contract version string
                - shim: shim function if action=="shim"
                - reason: explanation for reject actions
        """
        if tool_id not in self.registry._c:
            return {'action': 'reject', 'reason': f'Tool not registered: {tool_id}'}

        versions = tool_capabilities or self.registry.get_supported_versions(tool_id)

        if not versions:
            return {'action': 'reject', 'reason': f'No versions available for {tool_id}'}

        if agent_version in versions:
            return {'action': 'call', 'version': agent_version}

        compatible = self.registry.find_best_match(tool_id, agent_version)
        if compatible:
            shim = self.registry.get_shim(tool_id, agent_version, compatible)
            if shim:
                return {'action': 'shim', 'version': compatible, 'shim': shim}
            return {'action': 'call', 'version': compatible}

        return {
            'action': 'reject',
            'reason': f'No compatible contract version. Agent wants {agent_version}, tool supports: {versions}'
        }

def main():
    p = argparse.ArgumentParser(description="Contract Version Registry")
    s = p.add_subparsers(dest='cmd')
    r = s.add_parser('register', help='Register tool'); r.add_argument('tool_id'); r.add_argument('versions', nargs='+'); r.add_argument('--deprecated', nargs='+')
    s.add_parser('list', help='List tools')
    c = s.add_parser('check', help='Check compatibility'); c.add_argument('tool_id'); c.add_argument('version')
    a = p.parse_args()
    if not a.cmd: p.print_help(); return
    reg = ContractVersionRegistry()
    if a.cmd == 'register':
        dep = {v: 'deprecated' for v in a.deprecated or []}; reg.register(a.tool_id, a.versions, dep)
        print(f"Registered {a.tool_id} with versions: {', '.join(a.versions)}")
    elif a.cmd == 'list':
        for t in reg.list_tools(): print(f"{t}: {', '.join(reg.get_supported_versions(t))}")
    elif a.cmd == 'check':
        m = reg.find_best_match(a.tool_id, a.version)
        if m: print(f"Compatible: {m}{' (DEPRECATED)' if reg.is_deprecated(a.tool_id, m) else ''}")
        else: print(f"No compatible version. Tool supports: {', '.join(reg.get_supported_versions(a.tool_id)) if reg.get_supported_versions(a.tool_id) else 'none'}")
if __name__ == "__main__": main()
