// Hebrew label maps for the back-office enums (mirrors lib/api.ts string unions).
import type {
  DogStatus,
  DogGender,
  DogSize,
  LocationType,
  SurrenderType,
  SurrenderStatus,
  PaymentStatus,
  AdoptionStatus,
  OwnershipTransferStatus,
  TransferType,
  DocumentType,
  DocumentStatus,
  SignatureType,
  SignatureStatus,
} from "@/lib/api";

export const dogStatusLabels: Record<DogStatus, string> = {
  draft: "טיוטה",
  pending_surrender: "ממתין למסירה",
  in_facility: "בפנסיון",
  available_for_adoption: "זמין לאימוץ",
  reserved: "משוריין",
  adopted: "אומץ",
  inactive: "לא פעיל",
};

export const dogGenderLabels: Record<DogGender, string> = {
  male: "זכר",
  female: "נקבה",
  unknown: "לא ידוע",
};

export const dogSizeLabels: Record<DogSize, string> = {
  small: "קטן",
  medium: "בינוני",
  large: "גדול",
  xlarge: "ענק",
};

export const locationTypeLabels: Record<LocationType, string> = {
  home: "בבית",
  facility: "בפנסיון",
  adopted: "אומץ",
};

export const surrenderTypeLabels: Record<SurrenderType, string> = {
  facility: "פנסיון",
  full: "מסירה מלאה",
  home_subscription: "מנוי בית",
};

export const surrenderStatusLabels: Record<SurrenderStatus, string> = {
  new_lead: "ליד חדש",
  contacted: "נוצר קשר",
  waiting_for_details: "ממתין לפרטים",
  waiting_for_payment: "ממתין לתשלום",
  active_home_subscription: "מנוי בית פעיל",
  waiting_for_documents: "ממתין למסמכים",
  ownership_transfer_in_progress: "העברת בעלות בתהליך",
  transferred_to_facility: "הועבר לפנסיון",
  available_for_adoption: "זמין לאימוץ",
  cancelled: "בוטל",
  completed: "הושלם",
};

export const paymentStatusLabels: Record<PaymentStatus, string> = {
  pending: "ממתין",
  paid: "שולם",
  failed: "נכשל",
  refunded: "הוחזר",
};

export const adoptionStatusLabels: Record<AdoptionStatus, string> = {
  new_lead: "ליד חדש",
  screening: "סינון",
  waiting_for_call: "ממתין לשיחה",
  meeting_scheduled: "נקבעה פגישה",
  waiting_for_decision: "ממתין להחלטה",
  approved: "אושר",
  waiting_for_signatures: "ממתין לחתימות",
  waiting_for_documents: "ממתין למסמכים",
  authority_submission_ready: "מוכן להגשה לרשות",
  sent_to_authority: "נשלח לרשות",
  waiting_for_authority_confirmation: "ממתין לאישור רשות",
  ownership_transferred: "בעלות הועברה",
  completed: "הושלם",
  rejected: "נדחה",
  cancelled: "בוטל",
};

export const ownershipTransferStatusLabels: Record<OwnershipTransferStatus, string> = {
  draft: "טיוטה",
  waiting_for_documents: "ממתין למסמכים",
  waiting_for_signatures: "ממתין לחתימות",
  ready_to_send: "מוכן לשליחה",
  sent_to_authority: "נשלח לרשות",
  followup_required: "נדרש מעקב",
  confirmed: "אושר",
  failed: "נכשל",
  stopped_manually: "הופסק ידנית",
};

export const transferTypeLabels: Record<TransferType, string> = {
  surrender_to_facility: "מוסר → פנסיון",
  facility_to_adopter: "פנסיון → מאמץ",
  direct_surrenderer_to_adopter: "מוסר → מאמץ (ישיר)",
};

export const documentTypeLabels: Record<DocumentType, string> = {
  ownership_transfer_form: "טופס העברת בעלות",
  receiver_approval_form: "טופס אישור מקבל",
  id_card_surrenderer: "ת.ז. מוסר",
  id_card_receiver: "ת.ז. מקבל",
  adopter_with_dog_photo: "תמונת מאמץ עם הכלב",
  authority_submission: "הגשה לרשות",
  authority_confirmation: "אישור רשות",
  other: "אחר",
};

export const documentStatusLabels: Record<DocumentStatus, string> = {
  pending: "ממתין",
  uploaded: "הועלה",
  approved: "אושר",
  rejected: "נדחה",
};

export const signatureTypeLabels: Record<SignatureType, string> = {
  surrenderer: "מוסר",
  receiver: "מקבל",
  adopter: "מאמץ",
};

export const signatureStatusLabels: Record<SignatureStatus, string> = {
  pending: "ממתין",
  sent: "נשלח",
  signed: "נחתם",
  declined: "נדחה",
  expired: "פג תוקף",
};
