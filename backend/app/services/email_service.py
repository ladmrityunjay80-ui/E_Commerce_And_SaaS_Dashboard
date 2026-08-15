from typing import Optional
from app.core.config import settings


class EmailService:
    def __init__(self):
        self.use_sendgrid = bool(settings.SENDGRID_API_KEY)
        self.use_resend = bool(settings.RESEND_API_KEY)
        
        if self.use_sendgrid:
            try:
                from sendgrid import SendGridAPIClient
                from sendgrid.helpers.mail import Mail
                self.sendgrid_client = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
                self.Mail = Mail
            except ImportError:
                self.use_sendgrid = False
        
        if self.use_resend:
            try:
                import resend
                resend.api_key = settings.RESEND_API_KEY
                self.resend = resend
            except ImportError:
                self.use_resend = False

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None
    ) -> bool:
        """Send email using configured service."""
        if self.use_sendgrid:
            return await self._send_via_sendgrid(to_email, subject, html_content, text_content, from_email)
        elif self.use_resend:
            return await self._send_via_resend(to_email, subject, html_content, text_content, from_email)
        else:
            print(f"Email would be sent to {to_email}: {subject}")
            return True

    async def _send_via_sendgrid(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str],
        from_email: Optional[str]
    ) -> bool:
        """Send email via SendGrid."""
        try:
            message = self.Mail(
                from_email=from_email or settings.SENDGRID_FROM_EMAIL,
                to_emails=to_email,
                subject=subject,
                html_content=html_content,
                plain_text_content=text_content
            )
            response = self.sendgrid_client.send(message)
            return response.status_code == 202
        except Exception as e:
            print(f"SendGrid email failed: {str(e)}")
            return False

    async def _send_via_resend(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str],
        from_email: Optional[str]
    ) -> bool:
        """Send email via Resend."""
        try:
            params = {
                "from": from_email or settings.SENDGRID_FROM_EMAIL,
                "to": [to_email],
                "subject": subject,
                "html": html_content,
            }
            if text_content:
                params["text"] = text_content
            
            self.resend.Emails.send(params)
            return True
        except Exception as e:
            print(f"Resend email failed: {str(e)}")
            return False

    async def send_welcome_email(self, user_email: str, user_name: str) -> bool:
        """Send welcome email to new user."""
        html_content = f"""
        <html>
        <body>
            <h1>Welcome to SaaS Admin Dashboard</h1>
            <p>Hello {user_name},</p>
            <p>Welcome to our platform! We're excited to have you on board.</p>
            <p>If you have any questions, feel free to reach out to our support team.</p>
            <p>Best regards,<br>The SaaS Admin Team</p>
        </body>
        </html>
        """
        return await self.send_email(
            to_email=user_email,
            subject="Welcome to SaaS Admin Dashboard",
            html_content=html_content,
            text_content=f"Welcome {user_name}! We're excited to have you on board."
        )

    async def send_invoice_email(self, user_email: str, invoice_number: str, amount: float) -> bool:
        """Send invoice notification email."""
        html_content = f"""
        <html>
        <body>
            <h1>Invoice {invoice_number}</h1>
            <p>Hello,</p>
            <p>Your invoice {invoice_number} for ${amount:.2f} is now available.</p>
            <p>Please log in to your dashboard to view and pay the invoice.</p>
            <p>Best regards,<br>The SaaS Admin Team</p>
        </body>
        </html>
        """
        return await self.send_email(
            to_email=user_email,
            subject=f"Invoice {invoice_number} Available",
            html_content=html_content,
            text_content=f"Your invoice {invoice_number} for ${amount:.2f} is now available."
        )

    async def send_subscription_expiry_email(self, user_email: str, plan_name: str) -> bool:
        """Send subscription expiry warning email."""
        html_content = f"""
        <html>
        <body>
            <h1>Subscription Expiring Soon</h1>
            <p>Hello,</p>
            <p>Your subscription to {plan_name} is expiring soon.</p>
            <p>Please renew your subscription to continue enjoying our services.</p>
            <p>Best regards,<br>The SaaS Admin Team</p>
        </body>
        </html>
        """
        return await self.send_email(
            to_email=user_email,
            subject="Subscription Expiring Soon",
            html_content=html_content,
            text_content=f"Your subscription to {plan_name} is expiring soon. Please renew to continue."
        )

    def get_email_service(self) -> str:
        """Return the active email service."""
        if self.use_sendgrid:
            return "sendgrid"
        elif self.use_resend:
            return "resend"
        return "none"
