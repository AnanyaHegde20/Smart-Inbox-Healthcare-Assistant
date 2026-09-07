import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { EmailService } from './email.service';
import {
  EmailResponse,
  ClassificationResponse,
  ExtractionResponse,
  DocumentResponse,
  ReviewResponse,
  AuditLogResponse,
  AcceptReviewRequest,
  OverrideReviewRequest
} from '../models/email.models';

describe('EmailService', () => {
  let service: EmailService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [EmailService]
    });
    service = TestBed.inject(EmailService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('getEmails', () => {
    it('should return an array of emails', () => {
      const mockEmails: EmailResponse[] = [
        {
          id: 1,
          subject: 'Test Subject',
          sender: 'test@example.com',
          recipient: 'inbox@clinicverse.com',
          body: 'Test body',
          receivedAt: '2025-09-01T10:00:00Z',
          status: 'COMPLETED',
          errorMessage: null,
          createdAt: '2025-09-01T10:00:00Z',
          updatedAt: '2025-09-01T10:05:00Z',
          documents: [],
          reviewStatus: null,
          finalCategory: null,
          reviewedBy: null,
          reviewedAt: null
        }
      ];

      service.getEmails().subscribe(emails => {
        expect(emails.length).toBe(1);
        expect(emails[0].subject).toBe('Test Subject');
      });

      const req = httpMock.expectOne('/api/emails');
      expect(req.request.method).toBe('GET');
      req.flush(mockEmails);
    });
  });

  describe('getEmail', () => {
    it('should return a single email by id', () => {
      const mockEmail: EmailResponse = {
        id: 1,
        subject: 'Test Subject',
        sender: 'test@example.com',
        recipient: 'inbox@clinicverse.com',
        body: 'Test body',
        receivedAt: '2025-09-01T10:00:00Z',
        status: 'COMPLETED',
        errorMessage: null,
        createdAt: '2025-09-01T10:00:00Z',
        updatedAt: '2025-09-01T10:05:00Z',
        documents: [],
        reviewStatus: null,
        finalCategory: null,
        reviewedBy: null,
        reviewedAt: null
      };

      service.getEmail(1).subscribe(email => {
        expect(email.id).toBe(1);
        expect(email.subject).toBe('Test Subject');
      });

      const req = httpMock.expectOne('/api/emails/1');
      expect(req.request.method).toBe('GET');
      req.flush(mockEmail);
    });
  });

  describe('getDocuments', () => {
    it('should return documents for an email', () => {
      const mockDocs: DocumentResponse[] = [
        {
          id: 1,
          emailId: 1,
          filename: 'report.pdf',
          contentType: 'application/pdf',
          fileSize: 1024,
          extractedText: 'Extracted text',
          ocrUsed: false,
          pageCount: 1,
          language: 'en'
        }
      ];

      service.getDocuments(1).subscribe(docs => {
        expect(docs.length).toBe(1);
        expect(docs[0].filename).toBe('report.pdf');
      });

      const req = httpMock.expectOne('/api/emails/1/documents');
      expect(req.request.method).toBe('GET');
      req.flush(mockDocs);
    });
  });

  describe('getClassification', () => {
    it('should return classification for an email', () => {
      const mockClassification: ClassificationResponse = {
        id: 1,
        emailId: 1,
        primaryCategory: 'SAFETY_REPORT',
        primaryConfidence: 0.95,
        allCategories: '[{"category":"SAFETY_REPORT","confidence":0.95}]',
        summary: 'Test summary',
        isRelevant: true,
        relevanceConfidence: 0.95,
        createdAt: '2025-09-01T10:00:00Z'
      };

      service.getClassification(1).subscribe(classification => {
        expect(classification.primaryCategory).toBe('SAFETY_REPORT');
        expect(classification.primaryConfidence).toBe(0.95);
      });

      const req = httpMock.expectOne('/api/emails/1/classification');
      expect(req.request.method).toBe('GET');
      req.flush(mockClassification);
    });
  });

  describe('getExtraction', () => {
    it('should return extraction for an email', () => {
      const mockExtraction: ExtractionResponse = {
        id: 1,
        emailId: 1,
        extractedData: '{"patient_id":"SYN-1042"}',
        extractionType: 'ICSR',
        confidenceScore: 0.9,
        createdAt: '2025-09-01T10:00:00Z'
      };

      service.getExtraction(1).subscribe(extraction => {
        expect(extraction.extractionType).toBe('ICSR');
        expect(extraction.confidenceScore).toBe(0.9);
      });

      const req = httpMock.expectOne('/api/emails/1/extraction');
      expect(req.request.method).toBe('GET');
      req.flush(mockExtraction);
    });
  });

  describe('getReview', () => {
    it('should return review for an email', () => {
      const mockReview: ReviewResponse = {
        id: 1,
        emailId: 1,
        reviewerId: 'dr.smith',
        action: 'ACCEPTED',
        originalCategory: 'SAFETY_REPORT',
        originalConfidence: 0.95,
        overriddenCategory: null,
        finalCategory: 'SAFETY_REPORT',
        notes: 'Confirmed',
        reviewedAt: '2025-09-01T11:00:00Z'
      };

      service.getReview(1).subscribe(review => {
        expect(review.action).toBe('ACCEPTED');
        expect(review.reviewerId).toBe('dr.smith');
      });

      const req = httpMock.expectOne('/api/reviews/email/1');
      expect(req.request.method).toBe('GET');
      req.flush(mockReview);
    });
  });

  describe('acceptReview', () => {
    it('should send accept review request', () => {
      const request: AcceptReviewRequest = {
        reviewerId: 'dr.smith',
        notes: 'Confirmed'
      };

      service.acceptReview(1, request).subscribe(response => {
        expect(response).toBeTruthy();
      });

      const req = httpMock.expectOne('/api/reviews/1/accept');
      expect(req.request.method).toBe('POST');
      expect(request.reviewerId).toBe('dr.smith');
      req.flush({ message: 'Review accepted' });
    });
  });

  describe('overrideReview', () => {
    it('should send override review request', () => {
      const request: OverrideReviewRequest = {
        reviewerId: 'admin.chen',
        overriddenCategory: 'NOT_RELEVANT',
        notes: 'Reclassified'
      };

      service.overrideReview(1, request).subscribe(response => {
        expect(response).toBeTruthy();
      });

      const req = httpMock.expectOne('/api/reviews/1/override');
      expect(req.request.method).toBe('POST');
      expect(request.overriddenCategory).toBe('NOT_RELEVANT');
      req.flush({ message: 'Review overridden' });
    });
  });

  describe('getAuditLogs', () => {
    it('should return all audit logs', () => {
      const mockLogs: AuditLogResponse[] = [
        {
          id: 1,
          emailId: 1,
          action: 'EMAIL_RECEIVED',
          actorId: 'imap',
          details: 'Email received',
          source: 'imap',
          timestamp: '2025-09-01T10:00:00Z'
        }
      ];

      service.getAuditLogs().subscribe(logs => {
        expect(logs.length).toBe(1);
        expect(logs[0].action).toBe('EMAIL_RECEIVED');
      });

      const req = httpMock.expectOne('/api/audit-logs');
      expect(req.request.method).toBe('GET');
      req.flush(mockLogs);
    });
  });

  describe('getAuditLogsByEmail', () => {
    it('should return audit logs for a specific email', () => {
      const mockLogs: AuditLogResponse[] = [
        {
          id: 1,
          emailId: 1,
          action: 'EMAIL_RECEIVED',
          actorId: 'imap',
          details: 'Email received',
          source: 'imap',
          timestamp: '2025-09-01T10:00:00Z'
        }
      ];

      service.getAuditLogsByEmail(1).subscribe(logs => {
        expect(logs.length).toBe(1);
      });

      const req = httpMock.expectOne('/api/audit-logs/email/1');
      expect(req.request.method).toBe('GET');
      req.flush(mockLogs);
    });
  });

  describe('getAuditLogsByAction', () => {
    it('should return audit logs for a specific action', () => {
      const mockLogs: AuditLogResponse[] = [
        {
          id: 1,
          emailId: 1,
          action: 'AI_CLASSIFIED',
          actorId: 'ai-service',
          details: 'Classified as SAFETY_REPORT',
          source: 'ai-service',
          timestamp: '2025-09-01T10:01:00Z'
        }
      ];

      service.getAuditLogsByAction('AI_CLASSIFIED').subscribe(logs => {
        expect(logs.length).toBe(1);
        expect(logs[0].action).toBe('AI_CLASSIFIED');
      });

      const req = httpMock.expectOne('/api/audit-logs/action/AI_CLASSIFIED');
      expect(req.request.method).toBe('GET');
      req.flush(mockLogs);
    });
  });

  describe('getAuditStats', () => {
    it('should return audit statistics', () => {
      const mockStats: Record<string, number> = {
        'EMAIL_RECEIVED': 10,
        'AI_CLASSIFIED': 8,
        'REVIEW_ACCEPTED': 5
      };

      service.getAuditStats().subscribe(stats => {
        expect(stats['EMAIL_RECEIVED']).toBe(10);
        expect(stats['AI_CLASSIFIED']).toBe(8);
      });

      const req = httpMock.expectOne('/api/audit-logs/stats');
      expect(req.request.method).toBe('GET');
      req.flush(mockStats);
    });
  });
});
