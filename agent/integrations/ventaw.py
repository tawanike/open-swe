"""Ventaw sandbox backend for Open SWE."""

import os

import ventaw
from deepagents.backends.protocol import ExecuteResponse
from ventaw.resources.sandbox import Sandbox


class VentawBackend:
    """Ventaw sandbox backend implementing SandboxBackendProtocol."""

    def __init__(self, sandbox: Sandbox):
        self._sandbox = sandbox

    @property
    def id(self) -> str:
        return self._sandbox.id

    def execute(self, command: str, *, timeout: int | None = None) -> ExecuteResponse:
        result = self._sandbox.execute(command, "bash")
        stdout = result.get("stdout", "") if isinstance(result, dict) else str(result)
        stderr = result.get("stderr", "") if isinstance(result, dict) else ""
        exit_code = result.get("exit_code", 1) if isinstance(result, dict) else 1
        output = stdout
        if stderr:
            output = f"{stdout}\n{stderr}" if stdout else stderr
        return ExecuteResponse(
            output=output,
            exit_code=exit_code,
            truncated=False,
        )


def create_ventaw_sandbox(sandbox_id: str | None = None) -> VentawBackend:
    """Create or reconnect to a Ventaw sandbox.

    Environment variables:
        VENTAW_API_KEY: API key for Ventaw
        VENTAW_API_URL: Base URL (optional)
        VENTAW_SANDBOX_TEMPLATE: Template name (default: "python")
        VENTAW_SANDBOX_NAME: Sandbox name (default: "open-swe-sandbox")

    Args:
        sandbox_id: Optional existing sandbox ID to reconnect to.

    Returns:
        VentawBackend implementing SandboxBackendProtocol.
    """
    ventaw.api_key = os.environ.get("VENTAW_API_KEY")
    base_url = os.environ.get("VENTAW_API_URL")
    if base_url:
        ventaw.api_base = base_url

    if sandbox_id:
        sandbox = Sandbox.get(sandbox_id)
    else:
        template = os.environ.get("VENTAW_SANDBOX_TEMPLATE", "python")
        name = os.environ.get("VENTAW_SANDBOX_NAME", "open-swe-sandbox")
        vcpu = int(os.environ.get("VENTAW_SANDBOX_VCPU", "2"))
        memory = int(os.environ.get("VENTAW_SANDBOX_MEMORY", "4096"))
        sandbox = Sandbox.create(template, name, vcpu, memory)

    return VentawBackend(sandbox)
