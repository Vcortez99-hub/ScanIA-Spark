import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Create axios instance
const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('auth_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('auth_token')
      window.location.href = '/'
    }
    return Promise.reject(error)
  }
)

// Authentication API
export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  
  register: (email: string, password: string, full_name: string) =>
    api.post('/auth/register', { email, password, full_name }),
  
  logout: () =>
    api.post('/auth/logout'),
  
  getCurrentUser: () =>
    api.get('/auth/me'),
  
  changePassword: (current_password: string, new_password: string) =>
    api.post('/auth/change-password', { current_password, new_password }),
}

// Scans API
export const scansApi = {
  list: (params?: {
    page?: number
    per_page?: number
    status?: string
    target?: string
  }) =>
    api.get('/scans', { params }),
  
  create: (data: {
    target_url: string
    scan_types: string[]
    options?: any
    environment_type?: string
  }) =>
    api.post('/scans', data),
  
  get: (scanId: string) =>
    api.get(`/scans/${scanId}`),
  
  update: (scanId: string, data: any) =>
    api.put(`/scans/${scanId}`, data),
  
  delete: (scanId: string) =>
    api.delete(`/scans/${scanId}`),
  
  getStatus: (scanId: string) =>
    api.get(`/scans/${scanId}/status`),
  
  cancel: (scanId: string) =>
    api.post(`/scans/${scanId}/cancel`),
  
  getStats: () =>
    api.get('/scans/stats/summary'),
}

// Vulnerabilities API
export const vulnerabilitiesApi = {
  list: (params?: {
    page?: number
    per_page?: number
    scan_id?: string
    severity?: string[]
    status?: string[]
    search?: string
  }) =>
    api.get('/vulnerabilities', { params }),
  
  get: (vulnId: string) =>
    api.get(`/vulnerabilities/${vulnId}`),
  
  update: (vulnId: string, data: any) =>
    api.put(`/vulnerabilities/${vulnId}`, data),
  
  markFalsePositive: (vulnId: string, reason: string) =>
    api.post(`/vulnerabilities/${vulnId}/false-positive`, { reason }),
  
  markRemediated: (vulnId: string, notes: string) =>
    api.post(`/vulnerabilities/${vulnId}/remediate`, { notes }),
  
  getStats: () =>
    api.get('/vulnerabilities/stats/summary'),
}

// Types
export interface User {
  id: string
  email: string
  full_name: string
  role: string
  is_active: boolean
  created_at: string
  last_login?: string
}

export interface Scan {
  id: string
  target_url: string
  scan_types: string[]
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  options: any
  environment_type: string
  scan_number?: number
  started_at?: string
  completed_at?: string
  duration_seconds?: number
  celery_job_id?: string
  error_message?: string
  created_at: string
  updated_at: string
  vulnerability_summary: Record<string, number>
  total_vulnerabilities: number
  risk_score: number
}

export interface Vulnerability {
  id: string
  scan_id: string
  vulnerability_id: string
  cve_id?: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  cvss_score?: number
  title: string
  description: string
  solution?: string
  references: string[]
  affected_url: string
  affected_component?: string
  affected_parameter?: string
  vulnerability_type?: string
  status: 'open' | 'fixed' | 'false_positive' | 'accepted_risk' | 'in_progress'
  is_false_positive: boolean
  created_at: string
  updated_at: string
  risk_level: string
  remediation_urgency: number
}

export interface ScanStats {
  total_scans: number
  running_scans: number
  completed_scans: number
  failed_scans: number
  avg_duration_minutes: number
  scans_by_day: Record<string, number>
  vulnerability_trends: Record<string, Record<string, number>>
}

export interface VulnerabilityStats {
  total_vulnerabilities: number
  by_severity: Record<string, number>
  by_status: Record<string, number>
  by_type: Record<string, number>
  critical_open: number
  high_open: number
  avg_cvss_score: number
  exploitable_count: number
  false_positive_rate: number
  remediation_stats: Record<string, any>
}

export default api