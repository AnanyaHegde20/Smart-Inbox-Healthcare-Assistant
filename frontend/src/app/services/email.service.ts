import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  EmailResponse,
  ClassificationResponse,
  ExtractionResponse,
  DocumentResponse,
  ReviewResponse,
  AcceptReviewRequest,
  OverrideReviewRequest,
  AuditLogResponse
} from '../models/email.models';

@Injectable({ providedIn: 'root' })
export class EmailService {
  private baseUrl = '/api';

  constructor(private http: HttpClient) {}

  getEmails(): Observable<EmailResponse[]> {
    return this.http.get<EmailResponse[]>(`${this.baseUrl}/emails`);
  }

  getEmail(id: number): Observable<EmailResponse> {
    return this.http.get<EmailResponse>(`${this.baseUrl}/emails/${id}`);
  }

  getDocuments(emailId: number): Observable<DocumentResponse[]> {
    return this.http.get<DocumentResponse[]>(`${this.baseUrl}/emails/${emailId}/documents`);
  }

  getClassification(emailId: number): Observable<ClassificationResponse> {
    return this.http.get<ClassificationResponse>(`${this.baseUrl}/emails/${emailId}/classification`);
  }

  getExtraction(emailId: number): Observable<ExtractionResponse> {
    return this.http.get<ExtractionResponse>(`${this.baseUrl}/emails/${emailId}/extraction`);
  }

  getReview(emailId: number): Observable<ReviewResponse> {
    return this.http.get<ReviewResponse>(`${this.baseUrl}/reviews/email/${emailId}`);
  }

  acceptReview(emailId: number, request: AcceptReviewRequest): Observable<any> {
    return this.http.post(`${this.baseUrl}/reviews/${emailId}/accept`, request);
  }

  overrideReview(emailId: number, request: OverrideReviewRequest): Observable<any> {
    return this.http.post(`${this.baseUrl}/reviews/${emailId}/override`, request);
  }

  getAuditLogs(): Observable<AuditLogResponse[]> {
    return this.http.get<AuditLogResponse[]>(`${this.baseUrl}/audit-logs`);
  }

  getAuditLogsByEmail(emailId: number): Observable<AuditLogResponse[]> {
    return this.http.get<AuditLogResponse[]>(`${this.baseUrl}/audit-logs/email/${emailId}`);
  }

  getAuditLogsByAction(action: string): Observable<AuditLogResponse[]> {
    return this.http.get<AuditLogResponse[]>(`${this.baseUrl}/audit-logs/action/${action}`);
  }

  getAuditStats(): Observable<Record<string, number>> {
    return this.http.get<Record<string, number>>(`${this.baseUrl}/audit-logs/stats`);
  }
}
