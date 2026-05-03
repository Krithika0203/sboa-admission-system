"""
services/notifications.py
Email-only confirmation notification (Gmail SMTP).
Triggered automatically when a parent submits an application.

Setup:
  1. Enable 2-Step Verification on your Gmail account
  2. Go to myaccount.google.com → Security → App Passwords
  3. Generate an App Password for "Mail"
  4. Set in .env:
       SMTP_EMAIL=yourgmail@gmail.com
       SMTP_PASSWORD=abcdefghijklmnop   (16-char App Password, no spaces)
"""
import os, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
SMTP_EMAIL    = os.environ.get("SMTP_EMAIL", "").strip()
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "").strip()
SMTP_HOST     = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT     = int(os.environ.get("SMTP_PORT", "587"))
SCHOOL_NAME   = "SBOA Public School"
SCHOOL_EMAIL  = os.environ.get("SCHOOL_EMAIL", "admissions@sboa.edu.in")
SCHOOL_PHONE  = os.environ.get("SCHOOL_PHONE", "044-2345-6789")


# ── Email ─────────────────────────────────────────────────────────────────────
def send_email(to_email: str, student_name: str, app_id: str,
               class_applying: str, school: str) -> dict:
    """Send branded HTML confirmation email to parent via Gmail SMTP."""

    if not SMTP_EMAIL or not SMTP_PASSWORD:
        return {
            "success": False,
            "hint": "Set SMTP_EMAIL and SMTP_PASSWORD in your .env file or HF Secrets"
        }

    if not to_email or "@" not in to_email:
        return {"success": False, "error": "Invalid email address"}

    subject = f"SBOA Admission Application Received — ID: {app_id}"

    html_body = f"""
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f4f6f9;font-family:Arial,sans-serif">
<div style="max-width:600px;margin:30px auto;background:#ffffff;
            border-radius:12px;overflow:hidden;
            box-shadow:0 2px 12px rgba(0,0,0,0.10)">

  <!-- Header -->
  <div style="background:#1e3a5f;padding:28px 24px;text-align:center">
    <div style="font-size:36px">🏫</div>
    <h2 style="color:#ffffff;margin:8px 0 4px;font-size:22px">{SCHOOL_NAME}</h2>
    <p style="color:#a8c8f0;margin:0;font-size:14px">Admission Portal</p>
  </div>

  <!-- Body -->
  <div style="padding:28px 28px 20px">
    <h3 style="color:#1e3a5f;margin-top:0">✅ Application Received Successfully!</h3>
    <p style="color:#333;line-height:1.6">Dear Parent / Guardian,</p>
    <p style="color:#333;line-height:1.6">
      Thank you for applying to <strong>{SCHOOL_NAME}</strong>.
      Your application has been received and is currently under review by our admissions team.
    </p>

    <!-- Application Details Box -->
    <div style="background:#e8f4fd;border-left:5px solid #2d6a9f;
                padding:18px;margin:20px 0;border-radius:0 8px 8px 0">
      <p style="margin:6px 0;color:#333"><strong>Student Name:</strong>&nbsp; {student_name}</p>
      <p style="margin:6px 0;color:#333"><strong>Class Applied:</strong>&nbsp; {class_applying}</p>
      <p style="margin:6px 0;color:#333"><strong>School:</strong>&nbsp; {school}</p>
      <p style="margin:10px 0 6px;color:#333"><strong>Application ID:</strong></p>
      <div style="background:#ffffff;border:2px solid #2d6a9f;border-radius:8px;
                  padding:10px 16px;display:inline-block;margin-top:2px">
        <span style="font-family:monospace;font-size:20px;font-weight:bold;
                     color:#1e3a5f;letter-spacing:2px">{app_id}</span>
      </div>
    </div>

    <p style="color:#333;line-height:1.6">
      Please save your <strong>Application ID: {app_id}</strong>.
      You will need it to track your application status.
    </p>

    <!-- Next Steps -->
    <div style="background:#fff8e1;border:1px solid #ffcc02;
                padding:16px 20px;border-radius:8px;margin-top:20px">
      <p style="margin:0 0 10px;color:#7a5800;font-weight:bold">📋 Next Steps</p>
      <ol style="margin:0;padding-left:20px;color:#555;line-height:2">
        <li>Our admissions team will review your application</li>
        <li>You will receive a call or email within <strong>3–5 working days</strong></li>
        <li>Keep your documents ready for verification</li>
      </ol>
    </div>

    <!-- Contact -->
    <div style="margin-top:20px;padding:14px 18px;background:#f0f0f0;
                border-radius:8px;font-size:13px;color:#555">
      <strong>Need help?</strong>&nbsp;
      📧 {SCHOOL_EMAIL} &nbsp;|&nbsp; 📞 {SCHOOL_PHONE}
    </div>
  </div>

  <!-- Footer -->
  <div style="background:#f1f1f1;padding:14px;text-align:center;
              font-size:11px;color:#999">
    {SCHOOL_NAME} · Admission Portal · This is an automated message, please do not reply directly.
  </div>

</div>
</body>
</html>
"""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"{SCHOOL_NAME} Admissions <{SMTP_EMAIL}>"
        msg["To"]      = to_email
        msg["Reply-To"] = SCHOOL_EMAIL
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, to_email, msg.as_string())

        return {"success": True, "to": to_email}

    except smtplib.SMTPAuthenticationError:
        return {
            "success": False,
            "error": "Gmail authentication failed",
            "hint": (
                "Use a Gmail App Password, not your regular password. "
                "Go to myaccount.google.com → Security → 2-Step Verification → App Passwords"
            )
        }
    except smtplib.SMTPException as e:
        return {"success": False, "error": f"SMTP error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Also send a copy to school admin inbox ────────────────────────────────────
def send_admin_copy(student_name: str, app_id: str,
                    class_applying: str, school: str,
                    parent_email: str, parent_phone: str) -> dict:
    """Send a brief notification to the school admin email."""
    if not SMTP_EMAIL or not SMTP_PASSWORD or not SCHOOL_EMAIL:
        return {"success": False, "error": "SMTP not configured"}

    subject = f"New Admission Application — {student_name} | {class_applying} | ID: {app_id}"

    html_body = f"""
<div style="font-family:Arial,sans-serif;max-width:500px;margin:auto;padding:20px">
  <h3 style="color:#1e3a5f">New Application Received</h3>
  <table style="width:100%;border-collapse:collapse">
    <tr><td style="padding:6px;color:#555"><strong>Student Name</strong></td>
        <td style="padding:6px">{student_name}</td></tr>
    <tr style="background:#f5f5f5">
        <td style="padding:6px;color:#555"><strong>Class Applied</strong></td>
        <td style="padding:6px">{class_applying}</td></tr>
    <tr><td style="padding:6px;color:#555"><strong>School</strong></td>
        <td style="padding:6px">{school}</td></tr>
    <tr style="background:#f5f5f5">
        <td style="padding:6px;color:#555"><strong>Application ID</strong></td>
        <td style="padding:6px"><strong>{app_id}</strong></td></tr>
    <tr><td style="padding:6px;color:#555"><strong>Parent Email</strong></td>
        <td style="padding:6px">{parent_email}</td></tr>
    <tr style="background:#f5f5f5">
        <td style="padding:6px;color:#555"><strong>Parent Phone</strong></td>
        <td style="padding:6px">{parent_phone}</td></tr>
  </table>
  <p style="color:#888;font-size:12px;margin-top:16px">
    Login to the SBOA Admission Portal to review this application.
  </p>
</div>
"""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"{SCHOOL_NAME} Admission Portal <{SMTP_EMAIL}>"
        msg["To"]      = SCHOOL_EMAIL
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, SCHOOL_EMAIL, msg.as_string())

        return {"success": True, "to": SCHOOL_EMAIL}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── MAIN TRIGGER ──────────────────────────────────────────────────────────────
def notify_on_submission(app_data: dict, app_id: str) -> dict:
    """
    Call this immediately after insert() in apply.py.
    Sends:
      1. Confirmation email to parent
      2. Notification email to school admin inbox
    Returns status dict.
    """
    student_name   = app_data.get("student_name", "Student")
    class_applying = app_data.get("class_applying", "")
    school         = app_data.get("school", SCHOOL_NAME)
    email          = app_data.get("email", "").strip()
    phone          = str(app_data.get("father_phone",
                         app_data.get("phone", ""))).strip()

    results = {"app_id": app_id, "email": None, "admin_copy": None}

    # 1. Email to parent
    if email and "@" in email:
        results["email"] = send_email(
            email, student_name, app_id, class_applying, school)
    else:
        results["email"] = {
            "success": False,
            "error": "No valid email address in application"
        }

    # 2. Copy to school admin
    results["admin_copy"] = send_admin_copy(
        student_name, app_id, class_applying, school, email, phone)

    return results
