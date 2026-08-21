"""Topic management endpoints — backed by Cloud Firestore."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from ..dependencies import CurrentUser, get_current_user
from ..firebase_config import FirebaseUnavailable, get_firestore
from ..schemas import Topic, TopicCreate, TopicUpdate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/topics", tags=["topics"])


def _require_firestore():
    """Return an initialized Firestore client or raise a 503."""
    try:
        return get_firestore()
    except FirebaseUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Server Firebase storage unavailable: {exc}",
        ) from exc


def _collection(user: CurrentUser):
    return _require_firestore().collection("users").document(user.uid).collection("topics")


def _serialize(doc_id: str, data: dict) -> Topic:
    return Topic(
        id=doc_id,
        owner_uid=data.get("owner_uid", ""),
        title=data.get("title", ""),
        description=data.get("description"),
        subject=data.get("subject"),
        document_count=data.get("document_count", 0),
        created_at=data.get("created_at") or datetime.now(timezone.utc),
        updated_at=data.get("updated_at") or datetime.now(timezone.utc),
    )


@router.get("", response_model=list[Topic])
def list_topics(user: CurrentUser = Depends(get_current_user)):
    return [_serialize(d.id, d.to_dict()) for d in _collection(user).stream()]


@router.post("", response_model=Topic, status_code=201)
def create_topic(payload: TopicCreate, user: CurrentUser = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    doc_id = str(uuid.uuid4())
    record = {
        "owner_uid": user.uid,
        "title": payload.title,
        "description": payload.description,
        "subject": payload.subject,
        "document_count": 0,
        "created_at": now,
        "updated_at": now,
    }
    _collection(user).document(doc_id).set(record)
    return _serialize(doc_id, record)


@router.get("/{topic_id}", response_model=Topic)
def get_topic(topic_id: str, user: CurrentUser = Depends(get_current_user)):
    doc = _collection(user).document(topic_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Topic not found")
    return _serialize(doc.id, doc.to_dict())


@router.patch("/{topic_id}", response_model=Topic)
def update_topic(
    topic_id: str,
    payload: TopicUpdate,
    user: CurrentUser = Depends(get_current_user),
):
    ref = _collection(user).document(topic_id)
    if not ref.get().exists:
        raise HTTPException(status_code=404, detail="Topic not found")
    updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    updates["updated_at"] = datetime.now(timezone.utc)
    ref.update(updates)
    return _serialize(topic_id, {**ref.get().to_dict(), **updates})


@router.delete("/{topic_id}", status_code=204)
def delete_topic(topic_id: str, user: CurrentUser = Depends(get_current_user)):
    ref = _collection(user).document(topic_id)
    if not ref.get().exists:
        raise HTTPException(status_code=404, detail="Topic not found")
    ref.delete()
