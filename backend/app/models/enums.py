"""Centralised enumerations for statuses, types and workflows."""
from enum import Enum


class UserRole(str, Enum):
    admin = "admin"
    field_worker = "field_worker"
    viewer = "viewer"


class DogStatus(str, Enum):
    draft = "draft"
    pending_surrender = "pending_surrender"
    in_facility = "in_facility"
    available_for_adoption = "available_for_adoption"
    reserved = "reserved"
    adopted = "adopted"
    inactive = "inactive"


class DogGender(str, Enum):
    male = "male"
    female = "female"
    unknown = "unknown"


class DogSize(str, Enum):
    small = "small"
    medium = "medium"
    large = "large"
    xlarge = "xlarge"


class LocationType(str, Enum):
    home = "home"        # at the surrenderer's home
    facility = "facility"  # at the boarding facility
    adopted = "adopted"


class SurrenderType(str, Enum):
    facility = "facility"            # standard hand-off, dog lives at facility
    full = "full"                    # full surrender / ownership transfer
    home_subscription = "home_subscription"  # "מסירה מהבית" monthly subscription


class SurrenderStatus(str, Enum):
    new_lead = "new_lead"
    contacted = "contacted"
    waiting_for_details = "waiting_for_details"
    waiting_for_payment = "waiting_for_payment"
    active_home_subscription = "active_home_subscription"
    waiting_for_documents = "waiting_for_documents"
    ownership_transfer_in_progress = "ownership_transfer_in_progress"
    transferred_to_facility = "transferred_to_facility"
    available_for_adoption = "available_for_adoption"
    cancelled = "cancelled"
    completed = "completed"


class PaymentStatus(str, Enum):
    pending = "pending"
    paid = "paid"
    failed = "failed"
    refunded = "refunded"


class AdoptionStatus(str, Enum):
    new_lead = "new_lead"
    screening = "screening"
    waiting_for_call = "waiting_for_call"
    meeting_scheduled = "meeting_scheduled"
    waiting_for_decision = "waiting_for_decision"
    approved = "approved"
    waiting_for_signatures = "waiting_for_signatures"
    waiting_for_documents = "waiting_for_documents"
    authority_submission_ready = "authority_submission_ready"
    sent_to_authority = "sent_to_authority"
    waiting_for_authority_confirmation = "waiting_for_authority_confirmation"
    ownership_transferred = "ownership_transferred"
    completed = "completed"
    rejected = "rejected"
    cancelled = "cancelled"


class AdoptionLeadStatus(str, Enum):
    new = "new"
    contacted = "contacted"
    matched = "matched"
    converted = "converted"
    closed = "closed"


class TransferType(str, Enum):
    surrender_to_facility = "surrender_to_facility"
    facility_to_adopter = "facility_to_adopter"
    direct_surrenderer_to_adopter = "direct_surrenderer_to_adopter"


class OwnershipTransferStatus(str, Enum):
    draft = "draft"
    waiting_for_documents = "waiting_for_documents"
    waiting_for_signatures = "waiting_for_signatures"
    ready_to_send = "ready_to_send"
    sent_to_authority = "sent_to_authority"
    followup_required = "followup_required"
    confirmed = "confirmed"
    failed = "failed"
    stopped_manually = "stopped_manually"


class DocumentType(str, Enum):
    ownership_transfer_form = "ownership_transfer_form"
    receiver_approval_form = "receiver_approval_form"
    id_card_surrenderer = "id_card_surrenderer"
    id_card_receiver = "id_card_receiver"
    adopter_with_dog_photo = "adopter_with_dog_photo"
    authority_submission = "authority_submission"
    authority_confirmation = "authority_confirmation"
    other = "other"


class DocumentStatus(str, Enum):
    pending = "pending"
    uploaded = "uploaded"
    approved = "approved"
    rejected = "rejected"


class SignatureType(str, Enum):
    surrenderer = "surrenderer"
    receiver = "receiver"
    adopter = "adopter"


class SignatureStatus(str, Enum):
    pending = "pending"
    sent = "sent"
    signed = "signed"
    declined = "declined"
    expired = "expired"


class TaskStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    done = "done"
    cancelled = "cancelled"


class TaskPriority(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"


class MessageChannel(str, Enum):
    whatsapp = "whatsapp"
    email = "email"
    sms = "sms"
    system = "system"
    web = "web"  # website chat widget


class ConversationChannel(str, Enum):
    web = "web"
    whatsapp = "whatsapp"


class ConversationStatus(str, Enum):
    active = "active"              # bot is handling it
    lead_created = "lead_created"  # produced a surrender lead
    escalated = "escalated"        # handed to a human
    closed = "closed"


class ConversationGoal(str, Enum):
    surrender = "surrender"        # owner wants to give a dog away
    adopt = "adopt"
    general = "general"


class MessageDirection(str, Enum):
    inbound = "inbound"
    outbound = "outbound"


class MessageStatus(str, Enum):
    queued = "queued"
    sent = "sent"
    delivered = "delivered"
    read = "read"
    failed = "failed"


class EntityType(str, Enum):
    """Generic polymorphic entity references for documents/tasks/signatures."""
    dog = "dog"
    person = "person"
    surrender_case = "surrender_case"
    adoption_case = "adoption_case"
    adoption_lead = "adoption_lead"
    ownership_transfer = "ownership_transfer"
