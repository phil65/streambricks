from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class MicrosoftUser(BaseModel):
    """Microsoft Identity Token information from Streamlit's experimental_user."""

    model_config = ConfigDict(use_attribute_docstrings=True)

    is_logged_in: bool
    """Whether the user is currently logged in"""

    ver: str
    """Version of the token format"""

    iss: str
    """The service that issued the token"""

    sub: str
    """Subject identifier for the user"""

    application_id: str = Field(alias="aud")
    """Intended recipient of the token (your application)"""

    expiration_time: int = Field(alias="exp")
    """Timestamp when the token expires"""

    issued_time: int = Field(alias="iat")
    """Timestamp when the token was issued"""

    start_time: int = Field(alias="nbf")
    """Timestamp when the token becomes valid"""

    name: str
    """Complete name of the user"""

    username: str = Field(alias="preferred_username")
    """Preferred username for the user account"""

    user_id: str = Field(alias="oid")
    """Unique Microsoft identifier for the user"""

    email: str
    """Email address of the authenticated user"""

    tenant_id: str = Field(alias="tid")
    """Microsoft Entra tenant identifier"""

    nonce: str
    """One-time value to prevent replay attacks"""

    aio: str
    """Internal Microsoft authentication tracking information"""


class GoogleUser(BaseModel):
    """Google Identity Token information from Streamlit's experimental_user."""

    model_config = ConfigDict(use_attribute_docstrings=True, extra="allow")

    is_logged_in: bool
    """Authentication status of the user"""

    iss: str
    """The service that issued the token"""

    authorized_party: str = Field(alias="azp")
    """The client that was authorized to receive the token"""

    client_id: str = Field(alias="aud")
    """Intended recipient of the token (your application)"""

    user_id: str = Field(alias="sub")
    """Unique Google identifier for the user"""

    email: str
    """Email address of the authenticated user"""

    email_verified: bool
    """Confirmation that Google has verified the email address"""

    access_token_hash: str = Field(alias="at_hash")
    """Hash of access token for security validation"""

    nonce: str
    """One-time value to prevent replay attacks"""

    name: str
    """Complete name of the user"""

    picture: str
    """Link to the user's Google profile image"""

    given_name: str
    """First/given name of the user"""

    family_name: str
    """Last/family name of the user"""

    issued_time: int = Field(alias="iat")
    """Timestamp when the token was issued"""

    expiration_time: int = Field(alias="exp")
    """Timestamp when the token expires"""
