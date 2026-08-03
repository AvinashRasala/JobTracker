export type ApplicationStatus =
  | "applied"
  | "application_viewed"
  | "under_review"
  | "assessment"
  | "coding_test"
  | "interview_round_1"
  | "interview_round_2"
  | "interview_round_3"
  | "hr_interview"
  | "offer_received"
  | "rejected"
  | "withdrawn"
  | "joined";

export const STATUS_LABELS: Record<ApplicationStatus, string> = {
  applied: "Applied",
  application_viewed: "Viewed",
  under_review: "Under Review",
  assessment: "Assessment",
  coding_test: "Coding Test",
  interview_round_1: "Interview R1",
  interview_round_2: "Interview R2",
  interview_round_3: "Interview R3",
  hr_interview: "HR Interview",
  offer_received: "Offer Received",
  rejected: "Rejected",
  withdrawn: "Withdrawn",
  joined: "Joined",
};

// Which stamp color each status maps to -- kept as one lookup so the
// meaning of a color stays consistent everywhere it appears.
export const STATUS_COLOR: Record<ApplicationStatus, "green" | "amber" | "red" | "slate"> = {
  applied: "slate",
  application_viewed: "slate",
  under_review: "amber",
  assessment: "amber",
  coding_test: "amber",
  interview_round_1: "amber",
  interview_round_2: "amber",
  interview_round_3: "amber",
  hr_interview: "amber",
  offer_received: "green",
  joined: "green",
  rejected: "red",
  withdrawn: "red",
};

export type WorkType = "remote" | "hybrid" | "onsite" | "unknown";
export type EmploymentType = "full_time" | "part_time" | "contract" | "internship" | "freelance" | "unknown";
export type DataSource = "gmail_parser" | "chrome_extension" | "manual";

export interface Application {
  id: string;
  role_title: string;
  company_name: string | null;
  platform_name: string | null;
  job_url: string | null;
  location: string | null;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string | null;
  work_type: WorkType;
  employment_type: EmploymentType;
  status: ApplicationStatus;
  source: DataSource;
  applied_at: string;
  last_status_change_at: string | null;
  created_at: string;
  expected_ctc: number | null;
  offered_ctc: number | null;
  notice_period_days: number | null;
  referred_by_name: string | null;
  referred_by_email: string | null;
  referred_by_relationship: string | null;
  follow_up_at: string | null;
}

export type InterviewMode = "phone" | "video" | "onsite" | "assessment" | "other";
export type InterviewOutcome = "pending" | "cleared" | "rejected" | "rescheduled" | "no_show";

export const INTERVIEW_MODE_LABELS: Record<InterviewMode, string> = {
  phone: "Phone",
  video: "Video",
  onsite: "Onsite",
  assessment: "Assessment",
  other: "Other",
};

export const INTERVIEW_OUTCOME_LABELS: Record<InterviewOutcome, string> = {
  pending: "Pending",
  cleared: "Cleared",
  rejected: "Rejected",
  rescheduled: "Rescheduled",
  no_show: "No-show",
};

export interface InterviewRound {
  id: string;
  application_id: string;
  round_name: string;
  mode: InterviewMode;
  scheduled_at: string | null;
  interviewer_name: string | null;
  interviewer_designation: string | null;
  feedback: string | null;
  outcome: InterviewOutcome;
  created_at: string;
  updated_at: string;
}

export interface OfferComparisonItem {
  id: string;
  role_title: string;
  company_name: string | null;
  location: string | null;
  work_type: WorkType;
  status: ApplicationStatus;
  offered_ctc: number | null;
  expected_ctc: number | null;
  salary_currency: string | null;
  notice_period_days: number | null;
  applied_at: string;
}

export interface UserProfile {
  id: string;
  email: string;
  full_name: string | null;
  is_admin: boolean;
  is_active: boolean;
  created_at: string;
  phone_number: string | null;
  avatar_url: string | null;
  current_ctc: number | null;
  current_notice_period_days: number | null;
  years_of_experience: number | null;
}

export interface ApplicationListResponse {
  total: number;
  items: Application[];
}

export interface DashboardStats {
  total_applications: number;
  applications_today: number;
  applications_this_week: number;
  applications_this_month: number;
  applications_this_year: number;
  success_rate: number;
  interview_rate: number;
  offer_rate: number;
  rejection_rate: number;
  response_rate: number;
  average_response_time_days: number | null;
  most_applied_company: string | null;
  most_applied_role: string | null;
  most_used_platform: string | null;
  needs_follow_up: number;
}

export interface StatusCount {
  status: string;
  count: number;
}

export interface PlatformCount {
  platform: string;
  count: number;
}

export interface DailyCount {
  date: string;
  count: number;
}
