from __future__ import annotations

import concurrent.futures
import time
from pathlib import Path

from spikes.phase1.approval_store import ApprovalStore


def test_only_one_worker_consumes_an_approval(tmp_path: Path) -> None:
    store = ApprovalStore(tmp_path / "approval.db")
    store.initialize()
    store.create("approval-1", "digest-1", time.time() + 60)
    assert store.approve("approval-1")

    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(lambda _: store.consume("approval-1", "digest-1"), range(32)))

    assert results.count(True) == 1
    assert store.state("approval-1") == "executing"


def test_digest_mismatch_cannot_consume_approval(tmp_path: Path) -> None:
    store = ApprovalStore(tmp_path / "approval.db")
    store.initialize()
    store.create("approval-1", "digest-1", time.time() + 60)
    assert store.approve("approval-1")
    assert not store.consume("approval-1", "changed")
    assert store.state("approval-1") == "approved"


def test_expired_approval_cannot_be_approved(tmp_path: Path) -> None:
    store = ApprovalStore(tmp_path / "approval.db")
    store.initialize()
    store.create("approval-1", "digest-1", time.time() - 1)
    assert not store.approve("approval-1")
    assert store.state("approval-1") == "pending"


def test_restart_marks_inflight_as_unknown_instead_of_retrying(tmp_path: Path) -> None:
    store = ApprovalStore(tmp_path / "approval.db")
    store.initialize()
    store.create("approval-1", "digest-1", time.time() + 60)
    assert store.approve("approval-1")
    assert store.consume("approval-1", "digest-1")

    restarted = ApprovalStore(store.path)
    assert restarted.recover_inflight() == 1
    assert restarted.state("approval-1") == "unknown"

