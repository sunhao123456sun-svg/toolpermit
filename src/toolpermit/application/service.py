"""Application orchestration shared by every local interface."""

from __future__ import annotations

from pathlib import Path

from toolpermit.approvals import ApprovalRecord, ApprovalService
from toolpermit.audit import AuditStore, EventRecord, RunRecord
from toolpermit.policy import load_policy
from toolpermit.replay import ReplayReport, replay_events
from toolpermit.suggest import Suggestion, suggest_policy


class ToolPermitApplication:
    def __init__(self, database: Path) -> None:
        self.store = AuditStore(database)
        self.store.initialize()
        self.approvals = ApprovalService(self.store)

    def list_pending_approvals(self) -> tuple[ApprovalRecord, ...]:
        return self.approvals.list_pending()

    def approve(self, approval_id: str, *, actor: str) -> bool:
        return self.approvals.approve(approval_id, actor=actor)

    def reject(self, approval_id: str, *, actor: str) -> bool:
        return self.approvals.reject(approval_id, actor=actor)

    def list_runs(self) -> tuple[RunRecord, ...]:
        return self.store.list_runs()

    def events_for_run(self, run_id: str) -> tuple[EventRecord, ...]:
        return self.store.list_events(run_id=run_id)

    def get_event(self, event_id: str) -> EventRecord:
        return self.store.get_event(event_id)

    def export_jsonl(self, *, run_id: str | None = None) -> tuple[str, ...]:
        return tuple(self.store.export_jsonl(run_id=run_id))

    def delete_run(self, run_id: str) -> bool:
        return self.store.delete_run(run_id)

    def suggest(self, run_id: str) -> Suggestion:
        return suggest_policy(self.events_for_run(run_id))

    def replay(
        self,
        policy_path: Path,
        *,
        run_id: str | None = None,
        baseline_path: Path | None = None,
    ) -> ReplayReport:
        candidate = load_policy(policy_path)
        baseline = load_policy(baseline_path) if baseline_path is not None else None
        events = self.store.list_events(run_id=run_id)
        return replay_events(events, candidate, baseline=baseline)
