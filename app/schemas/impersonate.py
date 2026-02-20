from pydantic import BaseModel
from typing import List, Optional
class SubscriberListResponse(BaseModel):
    id: int
    name: str
    email: str | None
    profile_path: str | None
    role: str | None


class SubscriberResponse(BaseModel):
    current_user_mail: str
    impersonated_by:Optional[int] = None
    subscribers: List[SubscriberListResponse]