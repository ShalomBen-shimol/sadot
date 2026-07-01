"""Admin API for the configurable ownership-transfer workflows (the builder)."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import select

from app.api.deps import AdminUser, SessionDep
from app.models.enums import DocumentType, SignatureType, TaskPriority, TransferType
from app.models.workflow import TransferWorkflow
from app.services import workflow as workflow_service

router = APIRouter(prefix="/workflows", tags=["workflows"])


class WorkflowUpdate(BaseModel):
    steps: list[dict]


@router.get("/step-types")
def step_types(_: AdminUser):
    """Vocabulary + option lists the builder needs to render step editors."""
    return {
        "step_types": workflow_service.STEP_TYPES,
        "transfer_types": [t.value for t in TransferType],
        "document_types": [d.value for d in DocumentType],
        "signature_types": [s.value for s in SignatureType],
        "priorities": [p.value for p in TaskPriority],
    }


@router.get("")
def list_workflows(session: SessionDep, _: AdminUser):
    """Active workflow per transfer type (falls back to the seeded default)."""
    out = []
    for ttype in [t.value for t in TransferType]:
        wf = workflow_service.get_active_workflow(session, ttype)
        out.append({"transfer_type": ttype, "version": wf.version, "steps": wf.steps})
    return out


@router.get("/{transfer_type}")
def get_workflow(transfer_type: str, session: SessionDep, _: AdminUser):
    wf = workflow_service.get_active_workflow(session, transfer_type)
    return {"transfer_type": transfer_type, "version": wf.version, "steps": wf.steps}


@router.put("/{transfer_type}")
def update_workflow(
    transfer_type: str, payload: WorkflowUpdate, session: SessionDep, user: AdminUser
):
    """Save a new active version of a transfer's workflow (previous versions kept)."""
    if transfer_type not in {t.value for t in TransferType}:
        raise HTTPException(status_code=422, detail="Unknown transfer type")

    latest = session.exec(
        select(TransferWorkflow)
        .where(TransferWorkflow.transfer_type == transfer_type)
        .order_by(TransferWorkflow.version.desc())
    ).first()
    new_version = (latest.version + 1) if latest else 1

    for existing in session.exec(
        select(TransferWorkflow).where(
            TransferWorkflow.transfer_type == transfer_type,
            TransferWorkflow.is_active == True,  # noqa: E712
        )
    ).all():
        existing.is_active = False
        session.add(existing)

    wf = TransferWorkflow(
        transfer_type=transfer_type,
        version=new_version,
        is_active=True,
        steps=payload.steps,
        created_by_user_id=user.id,
    )
    session.add(wf)
    session.commit()
    session.refresh(wf)
    return {"transfer_type": transfer_type, "version": wf.version, "steps": wf.steps}
