from fastapi import Depends, HTTPException, status
from app.core.security import oauth2_scheme, verify_access_token

def get_current_user_token(token: str = Depends(oauth2_scheme)):
    """
    Frontend se aane wale Bearer token ko extract aur verify karta hai.
    """
    payload = verify_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token. Please login again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload

def verify_admin_role(payload: dict = Depends(get_current_user_token)):
    """
    JWT token payload se user ka role check karta hai with proper trimming and lowercasing.
    """
    # Safe lookup for both lowercase 'role' and titlecase 'Role'
    raw_role = payload.get("role") or payload.get("Role") or "analyst"
    
    # Strip whitespace & lowercase comparison
    cleaned_role = str(raw_role).strip().lower()
    
    if cleaned_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Administrator privileges required for this action."
        )
    return cleaned_role