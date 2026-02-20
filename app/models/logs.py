from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, func
from ..db.base_class import BaseDB


class ActivityLog(BaseDB):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)

    # ─── Subscriber Info ─────────────────────────────
    subscriber_id = Column(Integer, index=True, nullable=True)
    subscriber_name = Column(String(100), nullable=True)
    subscriber_email = Column(String(255), index=True, nullable=True)
    subscriber_role = Column(String(50), index=True, nullable=True)

    # ─── Log Info ────────────────────────────────
    endpoint = Column(String(255), nullable=False)
    action = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)

    # ─── Network Info ────────────────────────────────
    ip = Column(String(45), index=True, nullable=True)  # IPv4/IPv6 as string
    port = Column(Integer, nullable=True)

    # ─── Device / Browser Info ───────────────────────
    browser = Column(String(50), nullable=True)
    browser_version = Column(String(50), nullable=True)
    os = Column(String(50), nullable=True)
    os_version = Column(String(50), nullable=True)
    device = Column(String(100), nullable=True)

    is_mobile = Column(Boolean, default=False)
    is_tablet = Column(Boolean, default=False)
    is_pc = Column(Boolean, default=False)
    is_bot = Column(Boolean, default=False)

    # ─── Request Context ─────────────────────────────
    method = Column(String(10), nullable=False)
    path = Column(String(255), index=True, nullable=False)
    referer = Column(Text, nullable=True)
    origin = Column(Text, nullable=True)

    # ─── App Context ─────────────────────────────────
    is_backend = Column(Boolean, default=False)

    # ─── Request Parameters / Payload ───────────────
    params = Column(JSON, nullable=True)  # MySQL JSON column

    # ─── Metadata ────────────────────────────────────
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    impersonated_by = Column(Integer, nullable=True)
