"""Ventaw sandbox backend for Open SWE."""

import logging
import os
import time

import ventaw
from deepagents.backends.protocol import ExecuteResponse
from ventaw.resources.sandbox import Sandbox

logger = logging.getLogger(__name__)

SANDBOX_READY_TIMEOUT = 120  # seconds
SANDBOX_POLL_INTERVAL = 3  # seconds


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


def _wait_for_sandbox_ready(sandbox: Sandbox) -> Sandbox:
    """Wait for a sandbox to reach 'running' state."""
    elapsed = 0.0
    while elapsed < SANDBOX_READY_TIMEOUT:
        sandbox.refresh()
        if sandbox.state == "running":
            logger.info("Sandbox %s is ready (state=running)", sandbox.id)
            return sandbox
        if sandbox.state == "error":
            raise RuntimeError(
                f"Sandbox {sandbox.id} entered error state during startup"
            )
        logger.debug(
            "Waiting for sandbox %s (state=%s, elapsed=%.0fs)",
            sandbox.id, sandbox.state, elapsed,
        )
        time.sleep(SANDBOX_POLL_INTERVAL)
        elapsed += SANDBOX_POLL_INTERVAL

    raise TimeoutError(
        f"Sandbox {sandbox.id} did not become ready within {SANDBOX_READY_TIMEOUT}s "
        f"(last state: {sandbox.state})"
    )


def create_ventaw_sandbox(sandbox_id: str | None = None) -> VentawBackend:
    """Create or reconnect to a Ventaw sandbox.

    Environment variables:
        VENTAW_API_KEY: API key for Ventaw
        VENTAW_API_URL: Base URL (optional)
        VENTAW_SANDBOX_TEMPLATE: Template name (default: "nextjs")
        VENTAW_SANDBOX_NAME: Sandbox name (default: "open-swe-sandbox")
        VENTAW_SANDBOX_ID: Reuse an existing sandbox instead of creating a new one

    Args:
        sandbox_id: Optional existing sandbox ID to reconnect to.

    Returns:
        VentawBackend implementing SandboxBackendProtocol.
    """
    ventaw.api_key = os.environ.get("VENTAW_API_KEY")
    base_url = os.environ.get("VENTAW_API_URL")
    if base_url:
        ventaw.api_base = base_url

    # Check for env var override
    env_sandbox_id = os.environ.get("VENTAW_SANDBOX_ID")
    effective_id = sandbox_id or env_sandbox_id

    if effective_id:
        logger.info("Reconnecting to existing Ventaw sandbox: %s", effective_id)
        sandbox = Sandbox.get(effective_id)
        if sandbox.state != "running":
            logger.info("Sandbox %s is %s, starting...", effective_id, sandbox.state)
            sandbox.start()
            sandbox = _wait_for_sandbox_ready(sandbox)
    else:
        template = os.environ.get("VENTAW_SANDBOX_TEMPLATE", "nextjs")
        name = os.environ.get("VENTAW_SANDBOX_NAME", "open-swe-sandbox")
        vcpu = int(os.environ.get("VENTAW_SANDBOX_VCPU", "2"))
        memory = int(os.environ.get("VENTAW_SANDBOX_MEMORY", "4096"))
        logger.info(
            "Creating new Ventaw sandbox: template=%s name=%s vcpu=%d memory=%d",
            template, name, vcpu, memory,
        )
        sandbox = Sandbox.create(template, name, vcpu, memory)
        sandbox = _wait_for_sandbox_ready(sandbox)

    return VentawBackend(sandbox)
