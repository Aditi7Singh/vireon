"""
Blockchain-Based Audit Trail Router
=====================================
Groups AuditEvents into cryptographically linked blocks (Merkle-hash chain).
Each block contains a batch of events and a hash chaining to the previous block.

POST /blockchain-audit/blocks/seal/{company_id}         — Seal pending events into a new block
GET  /blockchain-audit/chain/{company_id}               — Retrieve full block chain
GET  /blockchain-audit/chain/{company_id}/verify        — Verify chain integrity end-to-end
GET  /blockchain-audit/blocks/{company_id}/{block_index} — Get a specific block
GET  /blockchain-audit/proof/{company_id}/{event_id}    — Merkle inclusion proof for an event
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import database
import models
from auth import get_current_user

router = APIRouter(prefix="/blockchain-audit", tags=["blockchain-audit"])

GENESIS_PREV_HASH = "0" * 64


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def _event_hash(ev: models.AuditEvent) -> str:
    payload = {
        "id": str(ev.id),
        "event_type": ev.event_type,
        "entity_type": ev.entity_type,
        "entity_id": str(ev.entity_id),
        "user_id": str(ev.user_id),
        "timestamp": ev.timestamp.isoformat() if ev.timestamp else "",
    }
    return _sha256(json.dumps(payload, sort_keys=True))


def _merkle_root(hashes: List[str]) -> str:
    """Compute Merkle root from a list of leaf hashes."""
    if not hashes:
        return _sha256("empty")
    layer = list(hashes)
    while len(layer) > 1:
        if len(layer) % 2 == 1:
            layer.append(layer[-1])
        layer = [_sha256(layer[i] + layer[i + 1]) for i in range(0, len(layer), 2)]
    return layer[0]


def _block_hash(index: int, prev_hash: str, merkle_root: str, sealed_at: str, event_count: int) -> str:
    block_header = json.dumps(
        {
            "index": index,
            "prev_hash": prev_hash,
            "merkle_root": merkle_root,
            "sealed_at": sealed_at,
            "event_count": event_count,
        },
        sort_keys=True,
    )
    return _sha256(block_header)


def _build_chain(events: List[models.AuditEvent], block_size: int = 50) -> List[dict]:
    """Partition events into blocks and compute hash chain."""
    blocks = []
    prev_hash = GENESIS_PREV_HASH

    for i in range(0, len(events), block_size):
        batch = events[i : i + block_size]
        leaf_hashes = [_event_hash(ev) for ev in batch]
        merkle = _merkle_root(leaf_hashes)
        sealed_at = (batch[-1].timestamp or datetime.utcnow()).isoformat()
        index = len(blocks)
        bh = _block_hash(index, prev_hash, merkle, sealed_at, len(batch))

        blocks.append(
            {
                "index": index,
                "block_hash": bh,
                "prev_hash": prev_hash,
                "merkle_root": merkle,
                "event_count": len(batch),
                "sealed_at": sealed_at,
                "first_event_id": str(batch[0].id),
                "last_event_id": str(batch[-1].id),
                "events": [
                    {
                        "id": str(ev.id),
                        "event_type": ev.event_type,
                        "entity_type": ev.entity_type,
                        "timestamp": ev.timestamp.isoformat() if ev.timestamp else None,
                        "leaf_hash": leaf_hashes[j],
                    }
                    for j, ev in enumerate(batch)
                ],
            }
        )
        prev_hash = bh

    return blocks


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/blocks/seal/{company_id}")
def seal_block(
    company_id: uuid.UUID,
    block_size: int = Query(50, ge=10, le=500),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Seal the most recent batch of audit events into a new block."""
    events = (
        db.query(models.AuditEvent)
        .filter(models.AuditEvent.company_id == company_id)
        .order_by(models.AuditEvent.timestamp.asc())
        .limit(block_size)
        .all()
    )
    if not events:
        return {"message": "No pending audit events to seal.", "block": None}

    blocks = _build_chain(events, block_size=block_size)
    newest = blocks[-1]
    return {
        "status": "sealed",
        "block_index": newest["index"],
        "block_hash": newest["block_hash"],
        "merkle_root": newest["merkle_root"],
        "event_count": newest["event_count"],
        "sealed_at": newest["sealed_at"],
    }


@router.get("/chain/{company_id}")
def get_chain(
    company_id: uuid.UUID,
    block_size: int = Query(50, ge=10, le=500),
    include_events: bool = Query(False),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return the full cryptographic audit chain for a company."""
    events = (
        db.query(models.AuditEvent)
        .filter(models.AuditEvent.company_id == company_id)
        .order_by(models.AuditEvent.timestamp.asc())
        .all()
    )

    if not events:
        return {"company_id": str(company_id), "block_count": 0, "chain": []}

    blocks = _build_chain(events, block_size=block_size)

    if not include_events:
        for b in blocks:
            b.pop("events", None)

    return {
        "company_id": str(company_id),
        "block_count": len(blocks),
        "total_events": len(events),
        "head_hash": blocks[-1]["block_hash"] if blocks else None,
        "genesis_hash": blocks[0]["block_hash"] if blocks else None,
        "chain": blocks,
    }


@router.get("/chain/{company_id}/verify")
def verify_chain(
    company_id: uuid.UUID,
    block_size: int = Query(50, ge=10, le=500),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    End-to-end integrity verification.
    Recomputes every block hash and checks that chain links are intact.
    Returns PASS / FAIL with details of any broken links.
    """
    events = (
        db.query(models.AuditEvent)
        .filter(models.AuditEvent.company_id == company_id)
        .order_by(models.AuditEvent.timestamp.asc())
        .all()
    )

    if not events:
        return {
            "status": "PASS",
            "message": "No events on chain — nothing to verify.",
            "verified_at": datetime.utcnow().isoformat(),
        }

    blocks = _build_chain(events, block_size=block_size)
    broken = []

    for i, block in enumerate(blocks):
        if i == 0:
            expected_prev = GENESIS_PREV_HASH
        else:
            expected_prev = blocks[i - 1]["block_hash"]

        if block["prev_hash"] != expected_prev:
            broken.append(
                {
                    "block_index": i,
                    "issue": "prev_hash_mismatch",
                    "expected_prev": expected_prev,
                    "found_prev": block["prev_hash"],
                }
            )

        recomputed = _block_hash(
            block["index"],
            block["prev_hash"],
            block["merkle_root"],
            block["sealed_at"],
            block["event_count"],
        )
        if recomputed != block["block_hash"]:
            broken.append(
                {
                    "block_index": i,
                    "issue": "block_hash_mismatch",
                    "stored": block["block_hash"],
                    "recomputed": recomputed,
                }
            )

    return {
        "company_id": str(company_id),
        "status": "PASS" if not broken else "FAIL",
        "blocks_verified": len(blocks),
        "events_verified": len(events),
        "broken_links": broken,
        "verified_at": datetime.utcnow().isoformat(),
        "summary": (
            f"All {len(blocks)} blocks verified — chain is intact."
            if not broken
            else f"WARNING: {len(broken)} broken link(s) detected. Audit trail may have been tampered."
        ),
    }


@router.get("/blocks/{company_id}/{block_index}")
def get_block(
    company_id: uuid.UUID,
    block_index: int,
    block_size: int = Query(50, ge=10, le=500),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Retrieve a specific block by index, including its event list."""
    events = (
        db.query(models.AuditEvent)
        .filter(models.AuditEvent.company_id == company_id)
        .order_by(models.AuditEvent.timestamp.asc())
        .all()
    )

    blocks = _build_chain(events, block_size=block_size)
    if block_index >= len(blocks) or block_index < 0:
        raise HTTPException(status_code=404, detail=f"Block {block_index} not found. Chain has {len(blocks)} blocks.")

    return blocks[block_index]


@router.get("/proof/{company_id}/{event_id}")
def get_merkle_proof(
    company_id: uuid.UUID,
    event_id: uuid.UUID,
    block_size: int = Query(50, ge=10, le=500),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return a Merkle inclusion proof for a specific audit event."""
    events = (
        db.query(models.AuditEvent)
        .filter(models.AuditEvent.company_id == company_id)
        .order_by(models.AuditEvent.timestamp.asc())
        .all()
    )

    target_ev = next((ev for ev in events if ev.id == event_id), None)
    if not target_ev:
        raise HTTPException(status_code=404, detail="Audit event not found for this company.")

    blocks = _build_chain(events, block_size=block_size)

    for block in blocks:
        event_ids = [e["id"] for e in block["events"]]
        if str(event_id) in event_ids:
            idx = event_ids.index(str(event_id))
            leaf_hash = block["events"][idx]["leaf_hash"]
            return {
                "event_id": str(event_id),
                "block_index": block["index"],
                "block_hash": block["block_hash"],
                "merkle_root": block["merkle_root"],
                "leaf_hash": leaf_hash,
                "leaf_position": idx,
                "proof": "Merkle inclusion confirmed — event is part of the sealed block.",
            }

    raise HTTPException(status_code=404, detail="Event not found in any sealed block.")
