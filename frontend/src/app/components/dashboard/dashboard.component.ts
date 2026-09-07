import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { EmailService } from '../../services/email.service';
import {
  EmailResponse,
  ClassificationResponse,
  ExtractionResponse,
  ReviewResponse,
  AuditLogResponse,
  CATEGORY_LABELS,
  CATEGORY_COLORS,
  VALID_CATEGORIES,
  AUDIT_ACTION_LABELS,
  AUDIT_SOURCE_COLORS,
  AcceptReviewRequest,
  OverrideReviewRequest
} from '../../models/email.models';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit {
  emails: EmailResponse[] = [];
  filteredEmails: EmailResponse[] = [];
  classifications: Map<number, ClassificationResponse> = new Map();
  extractions: Map<number, ExtractionResponse> = new Map();
  reviews: Map<number, ReviewResponse> = new Map();
  auditLogs: Map<number, AuditLogResponse[]> = new Map();
  documents: Map<number, any[]> = new Map();

  selectedEmail: EmailResponse | null = null;
  selectedClassification: ClassificationResponse | null = null;
  selectedExtraction: ExtractionResponse | null = null;
  selectedReview: ReviewResponse | null = null;
  selectedAuditLogs: AuditLogResponse[] = [];

  activeFilter = 'ALL';
  isLoading = false;
  showDocumentViewer = false;
  showExtraction = false;
  showAuditHistory = false;
  overrideCategory = '';
  reviewNotes = '';
  isReviewing = false;
  reviewSuccess = '';
  reviewError = '';

  categoryLabels = CATEGORY_LABELS;
  categoryColors = CATEGORY_COLORS;
  validCategories = VALID_CATEGORIES;
  auditActionLabels = AUDIT_ACTION_LABELS;
  auditSourceColors = AUDIT_SOURCE_COLORS;

  filters = [
    { key: 'ALL', label: 'All' },
    { key: 'SAFETY_REPORT', label: 'Safety' },
    { key: 'QUALITY_COMPLAINT', label: 'Complaint' },
    { key: 'INFO_REQUEST', label: 'Info' },
    { key: 'NOT_RELEVANT', label: 'Not Relevant' }
  ];

  constructor(private emailService: EmailService, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    this.loadEmails();
  }

  loadEmails(): void {
    this.isLoading = true;
    this.cdr.detectChanges();
    this.emailService.getEmails().subscribe({
      next: (emails) => {
        this.emails = emails;
        this.filteredEmails = emails;
        emails.forEach(e => this.loadDetails(e.id));
        this.isLoading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.isLoading = false;
        this.cdr.detectChanges();
      }
    });
  }

  loadDetails(emailId: number): void {
    this.emailService.getClassification(emailId).subscribe({
      next: (c) => { this.classifications.set(emailId, c); this.cdr.detectChanges(); },
      error: () => {}
    });
    this.emailService.getExtraction(emailId).subscribe({
      next: (e) => { this.extractions.set(emailId, e); this.cdr.detectChanges(); },
      error: () => {}
    });
    this.emailService.getDocuments(emailId).subscribe({
      next: (d) => { this.documents.set(emailId, d); this.cdr.detectChanges(); },
      error: () => {}
    });
    this.emailService.getReview(emailId).subscribe({
      next: (r) => { this.reviews.set(emailId, r); this.cdr.detectChanges(); },
      error: () => {}
    });
  }

  applyFilter(key: string): void {
    this.activeFilter = key;
    if (key === 'ALL') {
      this.filteredEmails = this.emails;
    } else {
      this.filteredEmails = this.emails.filter(e => {
        const c = this.classifications.get(e.id);
        return c?.primaryCategory === key;
      });
    }
    this.cdr.detectChanges();
  }

  selectEmail(email: EmailResponse): void {
    this.selectedEmail = email;
    this.selectedClassification = this.classifications.get(email.id) || null;
    this.selectedExtraction = this.extractions.get(email.id) || null;
    this.selectedReview = this.reviews.get(email.id) || null;
    this.showDocumentViewer = false;
    this.showExtraction = false;
    this.showAuditHistory = false;
    this.overrideCategory = '';
    this.reviewNotes = '';
    this.reviewSuccess = '';
    this.reviewError = '';
    this.cdr.detectChanges();

    this.emailService.getAuditLogsByEmail(email.id).subscribe({
      next: (logs) => {
        this.selectedAuditLogs = logs;
        this.auditLogs.set(email.id, logs);
        this.cdr.detectChanges();
      },
      error: () => {}
    });
  }

  toggleDocumentViewer(): void {
    this.showDocumentViewer = !this.showDocumentViewer;
  }

  toggleExtraction(): void {
    this.showExtraction = !this.showExtraction;
  }

  toggleAuditHistory(): void {
    this.showAuditHistory = !this.showAuditHistory;
  }

  acceptClassification(): void {
    if (!this.selectedEmail || this.isReviewing) return;
    this.isReviewing = true;
    this.reviewSuccess = '';
    this.reviewError = '';

    const request: AcceptReviewRequest = {
      reviewerId: 'reviewer-001',
      notes: this.reviewNotes || undefined
    };
    this.emailService.acceptReview(this.selectedEmail.id, request).subscribe({
      next: (response) => {
        this.reviewSuccess = response.message || 'Classification accepted';
        this.isReviewing = false;
        this.reviewNotes = '';
        this.loadDetails(this.selectedEmail!.id);
        this.refreshAuditLogs(this.selectedEmail!.id);
        this.refreshEmailInList(this.selectedEmail!.id);
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.reviewError = err.error?.message || 'Failed to accept review';
        this.isReviewing = false;
        this.cdr.detectChanges();
      }
    });
  }

  overrideClassification(): void {
    if (!this.selectedEmail || !this.overrideCategory || this.isReviewing) return;
    this.isReviewing = true;
    this.reviewSuccess = '';
    this.reviewError = '';

    const request: OverrideReviewRequest = {
      reviewerId: 'reviewer-001',
      overriddenCategory: this.overrideCategory,
      notes: this.reviewNotes || undefined
    };
    this.emailService.overrideReview(this.selectedEmail.id, request).subscribe({
      next: (response) => {
        this.reviewSuccess = response.message || 'Classification overridden';
        this.isReviewing = false;
        this.overrideCategory = '';
        this.reviewNotes = '';
        this.loadDetails(this.selectedEmail!.id);
        this.refreshAuditLogs(this.selectedEmail!.id);
        this.refreshEmailInList(this.selectedEmail!.id);
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.reviewError = err.error?.message || 'Failed to override review';
        this.isReviewing = false;
        this.cdr.detectChanges();
      }
    });
  }

  private refreshAuditLogs(emailId: number): void {
    this.emailService.getAuditLogsByEmail(emailId).subscribe({
      next: (logs) => {
        this.selectedAuditLogs = logs;
        this.auditLogs.set(emailId, logs);
        this.cdr.detectChanges();
      },
      error: () => {}
    });
  }

  private refreshEmailInList(emailId: number): void {
    this.emailService.getEmail(emailId).subscribe({
      next: (updated) => {
        const idx = this.emails.findIndex(e => e.id === emailId);
        if (idx >= 0) {
          this.emails[idx] = updated;
          this.applyFilter(this.activeFilter);
          this.cdr.detectChanges();
        }
      },
      error: () => {}
    });
  }

  hasReview(): boolean {
    return this.selectedReview !== null;
  }

  getReviewStatusClass(): string {
    if (!this.selectedReview) return '';
    return this.selectedReview.action === 'ACCEPTED' ? 'review-accepted' : 'review-overridden';
  }

  getAuditActionLabel(action: string): string {
    return AUDIT_ACTION_LABELS[action] || action;
  }

  getSourceColor(source: string): string {
    return AUDIT_SOURCE_COLORS[source] || '#95a5a6';
  }

  getCategoryLabel(cat: string): string {
    return CATEGORY_LABELS[cat] || cat;
  }

  getCategoryColor(cat: string): string {
    return CATEGORY_COLORS[cat] || '#6c757d';
  }

  getConfidenceColor(confidence: number): string {
    if (confidence >= 0.8) return '#27ae60';
    if (confidence >= 0.5) return '#e67e22';
    return '#e74c3c';
  }

  formatDate(dateStr: string): string {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleString();
  }

  getStatusClass(status: string): string {
    switch (status) {
      case 'COMPLETED': return 'status-completed';
      case 'PROCESSING': return 'status-processing';
      case 'FAILED': return 'status-failed';
      default: return 'status-received';
    }
  }

  parseExtractedData(data: string): any {
    try {
      return JSON.parse(data);
    } catch {
      return { raw: data };
    }
  }

  getObjectKeys(obj: any): string[] {
    return Object.keys(obj || {});
  }
}
