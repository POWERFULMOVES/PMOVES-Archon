#!/usr/bin/env python3
"""
PMOVES Task Tracker - Agent Claim System

Allows agents to claim, update, and query tasks from the distributed roadmap.
Usage:
    python pmoves/scripts/task_tracker.py claim T1-2-002 --agent "Opus 4.5"
    python pmoves/scripts/task_tracker.py update T1-2-002 --status "COMPLETED"
    python pmoves/scripts/task_tracker.py list --agent "Opus 4.5"
    python pmoves/scripts/task_tracker.py ready --for "Sonnet 3.5"
"""

import argparse
import dataclasses
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


ROADMAP_PATH = Path("/home/pmoves/PMOVES.AI/pmoves/docs/DISTRIBUTED_COMPUTE_ROADMAP.md")
STATUS_EMOJI = {
    "BLOCKED": "🔵",
    "CLAIMED": "🟡",
    "COMPLETED": "🟢",
    "UNASSIGNED": "⚪",
    "BLOCKER": "🔴",
    "SKIPPED": "⏭️",
}


@dataclasses.dataclass
class Task:
    id: str
    name: str
    status: str
    agent: Optional[str]
    depends_on: List[str]
    effort: str
    files: List[str]
    description: str

    @property
    def emoji(self) -> str:
        return STATUS_EMOJI.get(self.status, "⚪")

    @property
    def is_ready(self) -> bool:
        return len(self.depends_on) == 0 or all(d in COMPLETED_TASKS for d in self.depends_on)


COMPLETED_TASKS = set()


def parse_roadmap() -> Dict[str, Task]:
    """Parse the roadmap markdown file into tasks."""
    content = ROADMAP_PATH.read_text()
    tasks = {}

    # Track current section context
    current_section = None

    for line in content.splitlines():
        # Section headers
        if line.startswith("## ") or line.startswith("### "):
            current_section = line.strip("# ").strip()
            continue

        # Task definition
        task_match = re.match(r'\s*-\s*id:\s+(\S+)', line)
        if task_match:
            task_id = task_match.group(1)
            tasks[task_id] = Task(
                id=task_id,
                name="",
                status="UNASSIGNED",
                agent=None,
                depends_on=[],
                effort="",
                files=[],
                description=""
            )
            continue

        if not tasks:
            continue

        # Get the most recent task
        task = list(tasks.values())[-1]

        # Parse task fields
        if "name:" in line:
            task.name = line.split("name:", 1)[1].strip()
        elif "status:" in line:
            task.status = line.split("status:", 1)[1].strip()
        elif "agent:" in line:
            agent = line.split("agent:", 1)[1].strip()
            task.agent = agent if agent != "none" else None
        elif "depends_on:" in line:
            deps_str = line.split("depends_on:", 1)[1].strip()
            if deps_str.startswith("["):
                deps = re.findall(r'[\w-]+', deps_str)
                task.depends_on = deps
            elif deps_str == "[]":
                task.depends_on = []
        elif "effort:" in line:
            task.effort = line.split("effort:", 1)[1].strip()
        elif "files:" in line:
            # Multi-line files list
            task.files = []
        elif "description:" in line:
            task.description = line.split("description:", 1)[1].strip()
        elif line.strip().startswith("-") and task.files is not None:
            # File entry
            file_match = re.match(r'\s*-\s*(.+)', line)
            if file_match:
                task.files.append(file_match.group(1).strip())

    # Load completed tasks cache
    global COMPLETED_TASKS
    COMPLETED_TASKS = {tid for tid, task in tasks.items() if task.status == "COMPLETED"}

    return tasks


def save_tasks(tasks: Dict[str, Task]) -> None:
    """Update the roadmap file with modified task statuses."""
    content = ROADMAP_PATH.read_text()

    for task_id, task in tasks.items():
        # Find and update status line
        status_pattern = rf'(  - id: {task_id}\n.*?)status: \w+'
        new_status = f"status: {task.status}"
        replacement = rf"\1status: {task.status}"
        content = re.sub(status_pattern, replacement, content, flags=re.DOTALL)

        # Find and update agent line if set
        if task.agent:
            agent_pattern = rf'(  - id: {task_id}\n.*?)agent: \w+(?:\s+\d+)?'
            new_agent = f"agent: {task.agent}"
            replacement = rf"\1agent: {task.agent}"
            content = re.sub(agent_pattern, replacement, content, flags=re.DOTALL)

    ROADMAP_PATH.write_text(content)


def claim_task(task_id: str, agent: str) -> str:
    """Claim a task for an agent."""
    tasks = parse_roadmap()

    if task_id not in tasks:
        return f"❌ Task {task_id} not found"

    task = tasks[task_id]

    # Check if dependencies are met
    if task.depends_on:
        completed = {tid for tid, t in tasks.items() if t.status == "COMPLETED"}
        unmet = [d for d in task.depends_on if d not in completed]
        if unmet:
            return f"❌ Task {task_id} blocked by unmet dependencies: {unmet}"

    if task.status != "UNASSIGNED":
        return f"❌ Task {task_id} already {task.status} by {task.agent or 'unknown'}"

    task.status = "CLAIMED"
    task.agent = agent
    save_tasks(tasks)

    return f"✅ Task {task_id} claimed by {agent}: {task.name}"


def update_task(task_id: str, status: str) -> str:
    """Update task status."""
    tasks = parse_roadmap()

    if task_id not in tasks:
        return f"❌ Task {task_id} not found"

    task = tasks[task_id]
    old_status = task.status
    task.status = status.upper()

    save_tasks(tasks)

    return f"✅ Task {task_id} updated: {old_status} → {status}"


def list_tasks(agent: Optional[str] = None, status: Optional[str] = None, ready: bool = False) -> str:
    """List tasks with optional filtering."""
    tasks = parse_roadmap()

    lines = []
    lines.append(f"{'ID':<12} {'Status':<12} {'Agent':<15} {'Task Name'}")
    lines.append("-" * 80)

    for task_id, task in tasks.items():
        if agent and task.agent != agent:
            continue
        if status and task.status != status:
            continue
        if ready and not task.is_ready:
            continue

        lines.append(f"{task_id:<12} {task.emoji} {task.status:<10} {str(task.agent or 'None'):<15} {task.name[:40]}")

    return "\n".join(lines)


def show_ready_for(agent: str) -> str:
    """Show tasks ready for a specific agent."""
    tasks = parse_roadmap()

    lines = []
    lines.append(f"Tasks ready for {agent}:")
    lines.append("")

    ready_count = 0
    for task_id, task in tasks.items():
        # Skip if not right agent type
        if "Opus" in agent and task_id.startswith("T8-"):
            continue  # Opus doesn't do docs
        if "Haiku" in agent and task_id.startswith(("T1-2", "T2-2", "T3-1", "T5", "T7")):
            continue  # Haiku skips complex tasks

        if task.status == "UNASSIGNED" and task.is_ready:
            ready_count += 1
            lines.append(f"  {task.emoji} {task_id:<12} {task.name} (effort: {task.effort})")

    if ready_count == 0:
        lines.append("  No ready tasks available")
    else:
        lines.append(f"\n  Total: {ready_count} tasks")

    return "\n".join(lines)


def show_progress() -> str:
    """Show overall progress by track."""
    tasks = parse_roadmap()

    # Group by track
    tracks = {}
    for task_id, task in tasks.items():
        track = task_id.split("-")[0]  # T1, T2, etc.
        if track not in tracks:
            tracks[track] = {"total": 0, "completed": 0, "claimed": 0}
        tracks[track]["total"] += 1
        if task.status == "COMPLETED":
            tracks[track]["completed"] += 1
        elif task.status == "CLAIMED":
            tracks[track]["claimed"] += 1

    # Calculate totals
    total_tasks = sum(t["total"] for t in tracks.values())
    total_completed = sum(t["completed"] for t in tracks.values())
    total_claimed = sum(t["claimed"] for t in tracks.values())

    lines = []
    lines.append("PMOVES Distributed Compute - Progress")
    lines.append("=" * 50)
    lines.append("")

    for track, data in sorted(tracks.items()):
        percent = (data["completed"] / data["total"] * 100) if data["total"] > 0 else 0
        bar = "█" * int(percent / 10) + "░" * (10 - int(percent / 10))
        lines.append(f"{track}: {bar} {percent:.0f}% ({data['completed']}/{data['total']})")

    lines.append("")
    lines.append(f"Total: {total_completed}/{total_tasks} completed ({total_completed/total_tasks*100:.0f}%)")
    lines.append(f"Active: {total_claimed} tasks claimed")

    # Ready to start (unassigned, no dependencies)
    ready_tasks = [t for t in tasks.values() if t.status == "UNASSIGNED" and t.is_ready]
    lines.append(f"Ready to start: {len(ready_tasks)} tasks")

    return "\n".join(lines)


def show_dependencies(task_id: str) -> str:
    """Show task dependency chain."""
    tasks = parse_roadmap()

    if task_id not in tasks:
        return f"❌ Task {task_id} not found"

    task = tasks[task_id]

    lines = []
    lines.append(f"Dependency chain for {task_id}: {task.name}")
    lines.append("")

    # Dependencies
    if task.depends_on:
        lines.append("⬇️ Depends on:")
        for dep_id in task.depends_on:
            if dep_id in tasks:
                dep = tasks[dep_id]
                emoji = STATUS_EMOJI.get(dep.status, "⚪")
                lines.append(f"  {emoji} {dep_id}: {dep.name} ({dep.status})")
            else:
                lines.append(f"  ⚪ {dep_id}: (not found)")

    # Dependents
    dependents = [tid for tid, t in tasks.items() if task_id in t.depends_on]
    if dependents:
        lines.append("")
        lines.append("⬆️ Required by:")
        for dep_id in dependents:
            dep = tasks[dep_id]
            emoji = STATUS_EMOJI.get(dep.status, "⚪")
            lines.append(f"  {emoji} {dep_id}: {dep.name} ({dep.status})")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="PMOVES Task Tracker")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Claim command
    claim_parser = subparsers.add_parser("claim", help="Claim a task")
    claim_parser.add_argument("task_id", help="Task ID to claim")
    claim_parser.add_argument("--agent", required=True, help="Agent claiming the task")

    # Update command
    update_parser = subparsers.add_parser("update", help="Update task status")
    update_parser.add_argument("task_id", help="Task ID to update")
    update_parser.add_argument("--status", required=True,
                             choices=["BLOCKED", "CLAIMED", "COMPLETED", "UNASSIGNED", "SKIPPED"],
                             help="New status")

    # List command
    list_parser = subparsers.add_parser("list", help="List tasks")
    list_parser.add_argument("--agent", help="Filter by agent")
    list_parser.add_argument("--status", help="Filter by status")
    list_parser.add_argument("--ready", action="store_true", help="Show only ready tasks")

    # Ready command
    ready_parser = subparsers.add_parser("ready", help="Show tasks ready for agent")
    ready_parser.add_argument("--for", dest="agent", required=True,
                            choices=["Opus", "Sonnet", "Haiku", "All"],
                            help="Agent type")

    # Progress command
    subparsers.add_parser("progress", help="Show overall progress")

    # Dependencies command
    dep_parser = subparsers.add_parser("deps", help="Show task dependencies")
    dep_parser.add_argument("task_id", help="Task ID")

    # Sync command - check file freshness
    subparsers.add_parser("sync", help="Reload roadmap from file")

    args = parser.parse_args()

    if args.command == "claim":
        print(claim_task(args.task_id, args.agent))
    elif args.command == "update":
        print(update_task(args.task_id, args.status))
    elif args.command == "list":
        print(list_tasks(args.agent, args.status, args.ready))
    elif args.command == "ready":
        if args.agent == "All":
            for agent_type in ["Opus", "Sonnet", "Haiku"]:
                print(show_ready_for(agent_type))
                print()
        else:
            print(show_ready_for(args.agent))
    elif args.command == "progress":
        print(show_progress())
    elif args.command == "deps":
        print(show_dependencies(args.task_id))
    elif args.command == "sync":
        global COMPLETED_TASKS
        parse_roadmap()  # Reload
        print("✅ Roadmap reloaded")


if __name__ == "__main__":
    main()
