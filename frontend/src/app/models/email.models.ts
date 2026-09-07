export interface EmailResponse {
  id: number;
  subject: string;
  sender: string;
  recipient: string;
  body: string;
  receivedAt: string;
  status: 'RECEIVED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  errorMessage: string | null;
  createdAt: string;
  updatedAt: string;
  documents: DocumentSummary[];
  reviewStatus: string | null;
  finalCategory: string | null;
  reviewedBy: string | null;
  reviewedAt: string | null;
}

export interface DocumentSummary {
  id: number;
  filename: string;
  contentType: string;
  fileSize: number;
}

export interface DocumentResponse {
  id: number;
  emailId: number;
  filename: string;
  contentType: string;
  fileSize: number;
  extractedText: string;
  ocrUsed: boolean;
  pageCount: number;
  language: string;
}

export interface ClassificationResponse {
  id: number;
  emailId: number;
  primaryCategory: string;
  primaryConfidence: number;
  allCategories: string;
  summary: string;
  isRelevant: boolean | null;
  relevanceConfidence: number | null;
  createdAt: string;
}

export interface ExtractionResponse {
  id: number;
  emailId: number;
  extractedData: string;
  extractionType: string;
  confidenceScore: number;
  createdAt: string;
}

export interface ReviewResponse {
  id: number;
  emailId: number;
  reviewerId: string;
  action: 'ACCEPTED' | 'OVERRIDDEN';
  originalCategory: string;
  originalConfidence: number;
  overriddenCategory: string | null;
  finalCategory: string;
  notes: string | null;
  reviewedAt: string;
}

export interface AuditLogResponse {
  id: number;
  emailId: number;
  action: string;
  actorId: string;
  details: string;
  source: string;
  timestamp: string;
}

export const AUDIT_ACTION_LABELS: Record<string, string> = {
  'EMAIL_RECEIVED': 'Email Received',
  'DOCUMENT_RECEIVED': 'Document Received',
  'PDF_TEXT_EXTRACTED': 'Text Extracted',
  'OCR_COMPLETED': 'OCR Completed',
  'LANGUAGE_DETECTED': 'Language Detected',
  'AI_CLASSIFIED': 'AI Classified',
  'FACTS_EXTRACTED': 'Facts Extracted',
  'SUMMARY_GENERATED': 'Summary Generated',
  'REVIEW_ACCEPTED': 'Review Accepted',
  'REVIEW_OVERRIDDEN': 'Review Overridden',
  'PROCESSING_FAILED': 'Processing Failed'
};

export const AUDIT_SOURCE_COLORS: Record<string, string> = {
  'imap': '#3498db',
  'ai-service': '#9b59b6',
  'reviewer': '#27ae60',
  'system': '#95a5a6'
};

export interface AcceptReviewRequest {
  reviewerId: string;
  notes?: string;
}

export interface OverrideReviewRequest {
  reviewerId: string;
  overriddenCategory: string;
  notes?: string;
}

export const CATEGORY_LABELS: Record<string, string> = {
  'SAFETY_REPORT': 'Safety Report',
  'QUALITY_COMPLAINT': 'Quality Complaint',
  'INFO_REQUEST': 'Info Request',
  'NOT_RELEVANT': 'Not Relevant'
};

export const CATEGORY_COLORS: Record<string, string> = {
  'SAFETY_REPORT': '#e67e22',
  'QUALITY_COMPLAINT': '#e74c3c',
  'INFO_REQUEST': '#3498db',
  'NOT_RELEVANT': '#95a5a6'
};

export const VALID_CATEGORIES = [
  'SAFETY_REPORT',
  'QUALITY_COMPLAINT',
  'INFO_REQUEST',
  'NOT_RELEVANT'
];
