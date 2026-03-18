"""Pairly task update tool for Open SWE agents."""

import os

import httpx


async def pairly_update(
    action: str,
    task_id: str = "",
    status: str = "",
    comment: str = "",
) -> str:
    """Update a Pairly task status or add a comment.

    Use this tool to keep Pairly tickets in sync with your progress.
    Call it when you start work, hit milestones, or complete tasks.

    Args:
        action: "update_status" or "add_comment"
        task_id: The Pairly task ID to update
        status: New status (for update_status): "todo", "in_progress", "done"
        comment: Comment text (for add_comment)

    Returns:
        Confirmation message
    """
    api_key = os.environ.get("PAIRLY_API_KEY")
    if not api_key:
        return "Error: PAIRLY_API_KEY not set"

    base_url = os.environ.get("PAIRLY_API_URL", "https://mcp.pairly.dev")
    project_id = os.environ.get("PAIRLY_PROJECT_ID", "")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "project-id": project_id,
    }

    try:
        async with httpx.AsyncClient(base_url=base_url, headers=headers, timeout=30.0) as client:
            if action == "update_status":
                if not task_id or not status:
                    return "Error: task_id and status are required for update_status"
                resp = await client.patch(f"/api/tasks/{task_id}", json={"status": status})
                resp.raise_for_status()
                return f"Task {task_id} status updated to '{status}'"

            elif action == "add_comment":
                if not task_id or not comment:
                    return "Error: task_id and comment are required for add_comment"
                resp = await client.post(
                    f"/api/tasks/{task_id}/comments",
                    json={"content": comment},
                )
                resp.raise_for_status()
                return f"Comment added to task {task_id}"

            else:
                return f"Error: unknown action '{action}'. Use 'update_status' or 'add_comment'"

    except httpx.HTTPStatusError as e:
        return f"Error: Pairly API returned {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return f"Error calling Pairly: {e}"
