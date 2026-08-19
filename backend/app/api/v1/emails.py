from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.email_service import EmailService
from app.api.deps import get_current_user
from app.models.user import User as UserModel
from app.core.rbac import has_permission

router = APIRouter()


@router.post("/send")
async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: str = None,
    from_email: str = None,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a generic email via the configured email provider."""
    if not has_permission(current_user, "invoices:read"):
        raise HTTPException(status_code=403, detail="Permission denied")

    try:
        email_service = EmailService()
        sent = await email_service.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            from_email=from_email,
        )
        if not sent:
            raise HTTPException(status_code=502, detail="Failed to send email")
        return {"message": "Email queued successfully", "service": email_service.get_email_service()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
