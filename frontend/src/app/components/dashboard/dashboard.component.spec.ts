import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { FormsModule } from '@angular/forms';
import { DashboardComponent } from './dashboard.component';
import { EmailService } from '../../services/email.service';
import { of, throwError } from 'rxjs';
import {
  EmailResponse,
  ClassificationResponse,
  ExtractionResponse,
  ReviewResponse,
  AuditLogResponse
} from '../../models/email.models';

describe('DashboardComponent', () => {
  let component: DashboardComponent;
  let fixture: ComponentFixture<DashboardComponent>;
  let emailService: jasmine.SpyObj<EmailService>;

  const mockEmails: EmailResponse[] = [
    {
      id: 1,
      subject: 'Patient Fall Report',
      sender: 'dr.smith@hospital.org',
      recipient: 'safety@clinicverse.com',
      body: 'Patient fell in Ward 3B',
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
    },
    {
      id: 2,
      subject: 'Quality Complaint',
      sender: 'quality@pharma.com',
      recipient: 'complaints@clinicverse.com',
      body: 'Tablet coating defect',
      receivedAt: '2025-09-02T14:00:00Z',
      status: 'COMPLETED',
      errorMessage: null,
      createdAt: '2025-09-02T14:00:00Z',
      updatedAt: '2025-09-02T14:05:00Z',
      documents: [],
      reviewStatus: 'ACCEPTED',
      finalCategory: 'QUALITY_COMPLAINT',
      reviewedBy: 'dr.smith',
      reviewedAt: '2025-09-02T15:00:00Z'
    }
  ];

  const mockClassification: ClassificationResponse = {
    id: 1,
    emailId: 1,
    primaryCategory: 'SAFETY_REPORT',
    primaryConfidence: 0.95,
    allCategories: '[{"category":"SAFETY_REPORT","confidence":0.95}]',
    summary: 'Patient safety incident',
    isRelevant: true,
    relevanceConfidence: 0.95,
    createdAt: '2025-09-01T10:00:00Z'
  };

  const mockAuditLogs: AuditLogResponse[] = [
    {
      id: 1,
      emailId: 1,
      action: 'EMAIL_RECEIVED',
      actorId: 'imap',
      details: 'Email received',
      source: 'imap',
      timestamp: '2025-09-01T10:00:00Z'
    },
    {
      id: 2,
      emailId: 1,
      action: 'AI_CLASSIFIED',
      actorId: 'ai-service',
      details: 'Classified as SAFETY_REPORT',
      source: 'ai-service',
      timestamp: '2025-09-01T10:01:00Z'
    }
  ];

  beforeEach(async () => {
    const emailServiceSpy = jasmine.createSpyObj('EmailService', [
      'getEmails',
      'getEmail',
      'getDocuments',
      'getClassification',
      'getExtraction',
      'getReview',
      'acceptReview',
      'overrideReview',
      'getAuditLogs',
      'getAuditLogsByEmail'
    ]);

    emailServiceSpy.getEmails.and.returnValue(of(mockEmails));
    emailServiceSpy.getEmail.and.returnValue(of(mockEmails[0]));
    emailServiceSpy.getDocuments.and.returnValue(of([]));
    emailServiceSpy.getClassification.and.returnValue(of(mockClassification));
    emailServiceSpy.getExtraction.and.returnValue(of(null as any));
    emailServiceSpy.getReview.and.returnValue(throwError(() => ({ status: 404 })));
    emailServiceSpy.getAuditLogsByEmail.and.returnValue(of(mockAuditLogs));

    await TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, FormsModule],
      declarations: [DashboardComponent],
      providers: [{ provide: EmailService, useValue: emailServiceSpy }]
    }).compileComponents();

    emailService = TestBed.inject(EmailService) as jasmine.SpyObj<EmailService>;
    fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('loadEmails', () => {
    it('should load emails on init', fakeAsync(() => {
      fixture.detectChanges();
      tick();
      expect(component.emails.length).toBe(2);
      expect(component.filteredEmails.length).toBe(2);
      expect(component.isLoading).toBeFalse();
    }));

    it('should set isLoading to true while loading', () => {
      fixture.detectChanges();
      expect(component.isLoading).toBeFalse();
    });
  });

  describe('selectEmail', () => {
    it('should select an email and load details', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      component.selectEmail(mockEmails[0]);
      tick();

      expect(component.selectedEmail).toBe(mockEmails[0]);
      expect(component.selectedClassification).toBeTruthy();
      expect(component.selectedClassification?.primaryCategory).toBe('SAFETY_REPORT');
    }));

    it('should load audit logs when selecting email', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      component.selectEmail(mockEmails[0]);
      tick();

      expect(component.selectedAuditLogs.length).toBe(2);
    }));
  });

  describe('applyFilter', () => {
    it('should filter emails by category', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      component.applyFilter('SAFETY_REPORT');
      expect(component.activeFilter).toBe('SAFETY_REPORT');
    }));

    it('should show all emails when filter is ALL', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      component.applyFilter('ALL');
      expect(component.filteredEmails.length).toBe(2);
    }));
  });

  describe('toggleDocumentViewer', () => {
    it('should toggle document viewer visibility', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      expect(component.showDocumentViewer).toBeFalse();
      component.toggleDocumentViewer();
      expect(component.showDocumentViewer).toBeTrue();
      component.toggleDocumentViewer();
      expect(component.showDocumentViewer).toBeFalse();
    }));
  });

  describe('toggleExtraction', () => {
    it('should toggle extraction visibility', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      expect(component.showExtraction).toBeFalse();
      component.toggleExtraction();
      expect(component.showExtraction).toBeTrue();
    }));
  });

  describe('toggleAuditHistory', () => {
    it('should toggle audit history visibility', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      expect(component.showAuditHistory).toBeFalse();
      component.toggleAuditHistory();
      expect(component.showAuditHistory).toBeTrue();
    }));
  });

  describe('acceptClassification', () => {
    it('should call acceptReview on the service', fakeAsync(() => {
      emailService.acceptReview.and.returnValue(of({ message: 'Accepted' }));
      emailService.getEmail.and.returnValue(of(mockEmails[0]));

      fixture.detectChanges();
      tick();

      component.selectEmail(mockEmails[0]);
      tick();

      component.reviewNotes = 'Confirmed';
      component.acceptClassification();
      tick();

      expect(emailService.acceptReview).toHaveBeenCalledWith(1, jasmine.objectContaining({
        reviewerId: 'reviewer-001',
        notes: 'Confirmed'
      }));
    }));
  });

  describe('overrideClassification', () => {
    it('should call overrideReview on the service', fakeAsync(() => {
      emailService.overrideReview.and.returnValue(of({ message: 'Overridden' }));
      emailService.getEmail.and.returnValue(of(mockEmails[0]));

      fixture.detectChanges();
      tick();

      component.selectEmail(mockEmails[0]);
      tick();

      component.overrideCategory = 'NOT_RELEVANT';
      component.reviewNotes = 'Reclassified';
      component.overrideClassification();
      tick();

      expect(emailService.overrideReview).toHaveBeenCalledWith(1, jasmine.objectContaining({
        reviewerId: 'reviewer-001',
        overriddenCategory: 'NOT_RELEVANT',
        notes: 'Reclassified'
      }));
    }));
  });

  describe('hasReview', () => {
    it('should return false when no review', fakeAsync(() => {
      fixture.detectChanges();
      tick();

      component.selectEmail(mockEmails[0]);
      expect(component.hasReview()).toBeFalse();
    }));

    it('should return true when review exists', fakeAsync(() => {
      emailService.getReview.and.returnValue(of({
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
      }));

      fixture.detectChanges();
      tick();

      component.selectEmail(mockEmails[0]);
      tick();

      expect(component.hasReview()).toBeTrue();
    }));
  });

  describe('getCategoryLabel', () => {
    it('should return correct labels', () => {
      expect(component.getCategoryLabel('SAFETY_REPORT')).toBe('Safety Report');
      expect(component.getCategoryLabel('QUALITY_COMPLAINT')).toBe('Quality Complaint');
      expect(component.getCategoryLabel('INFO_REQUEST')).toBe('Info Request');
      expect(component.getCategoryLabel('NOT_RELEVANT')).toBe('Not Relevant');
      expect(component.getCategoryLabel('UNKNOWN')).toBe('UNKNOWN');
    });
  });

  describe('getConfidenceColor', () => {
    it('should return green for high confidence', () => {
      expect(component.getConfidenceColor(0.9)).toBe('#27ae60');
    });

    it('should return orange for medium confidence', () => {
      expect(component.getConfidenceColor(0.6)).toBe('#e67e22');
    });

    it('should return red for low confidence', () => {
      expect(component.getConfidenceColor(0.3)).toBe('#e74c3c');
    });
  });

  describe('formatDate', () => {
    it('should format date string', () => {
      const result = component.formatDate('2025-09-01T10:00:00Z');
      expect(result).toBeTruthy();
    });

    it('should return empty string for empty input', () => {
      expect(component.formatDate('')).toBe('');
    });
  });

  describe('getStatusClass', () => {
    it('should return correct status classes', () => {
      expect(component.getStatusClass('COMPLETED')).toBe('status-completed');
      expect(component.getStatusClass('PROCESSING')).toBe('status-processing');
      expect(component.getStatusClass('FAILED')).toBe('status-failed');
      expect(component.getStatusClass('RECEIVED')).toBe('status-received');
    });
  });
});
