"""
Offline tests for the Gmail email-parsing heuristics -- no network or
database needed. Run with: pytest tests/test_email_parser.py
"""
import pytest

from app.services.email_parser import parse_email
from app.models.application import ApplicationStatus

PLATFORM_DOMAINS = {
    "@linkedin.com": "linkedin",
    "@naukri.com": "naukri",
    "@indeed.com": "indeed",
    "@internshala.com": "internshala",
    "greenhouse.io": "greenhouse",
    "lever.co": "lever",
}

CASES = [
    ("LinkedIn <jobs-noreply@linkedin.com>", "Your application was sent to Acme Corp",
     "Your application for Senior Backend Engineer at Acme Corp has been received.",
     "confirmation", "linkedin", "Acme Corp", None),
    ("Naukri.com <no-reply@naukri.com>", "Application Confirmation - Software Engineer at Beta Solutions",
     "Thank you for applying to Software Engineer at Beta Solutions. We have received your application.",
     "confirmation", "naukri", "Beta Solutions", None),
    ("Indeed <donotreply@indeed.com>", "Your application to Gamma Inc",
     "Your application has been submitted successfully.",
     "confirmation", "indeed", "Gamma Inc", None),
    ("Internshala <noreply@internshala.com>", "Application submitted for Data Analyst Intern at Delta Labs",
     "We've received your application for the Data Analyst Intern position.",
     "confirmation", "internshala", "Delta Labs", None),
    ('"Epsilon Careers" <careers@epsilon.com>', "Epsilon Careers - Application Received",
     "Epsilon Careers: Application Received. Thank you for your interest.",
     "confirmation", None, "Epsilon Careers", None),
    ('"Zeta Corp Recruiting" <talent@zeta.com>', "Interview Invitation - Backend Engineer",
     "We would like to schedule an interview with you for the Backend Engineer role.",
     "status_update", None, None, ApplicationStatus.INTERVIEW_ROUND_1),
    ('"Theta Inc" <hr@theta.com>', "Update on your application",
     "Unfortunately, we have decided not to move forward with your application at this time.",
     "status_update", None, None, ApplicationStatus.REJECTED),
    ('"Iota Systems" <noreply@iota.com>', "Congratulations! Job Offer from Iota Systems",
     "We are pleased to offer you the position of Software Engineer at Iota Systems.",
     "status_update", None, None, ApplicationStatus.OFFER_RECEIVED),
    ('"Kappa Tech" <hr@kappa.com>', "Next Steps: Online Assessment",
     "Please complete an assessment as the next step in our hiring process.",
     "status_update", None, None, ApplicationStatus.ASSESSMENT),
    ("Newsletter <news@randomsite.com>", "10 tips for your career",
     "Check out our latest blog post about career growth.",
     "unrelated", None, None, None),
]


@pytest.mark.parametrize("from_addr,subject,body,exp_kind,exp_platform,exp_company_contains,exp_status", CASES)
def test_parse_email(from_addr, subject, body, exp_kind, exp_platform, exp_company_contains, exp_status):
    result = parse_email(from_addr, subject, body, PLATFORM_DOMAINS)
    assert result.kind == exp_kind
    if exp_platform:
        assert result.platform_slug == exp_platform
    if exp_company_contains:
        assert result.company_name and exp_company_contains.lower() in result.company_name.lower()
    if exp_status:
        assert result.new_status == exp_status
