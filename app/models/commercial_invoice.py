# models/invoice.py
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Float,
    DateTime,
    Enum,
    Text,
    JSON
)
from sqlalchemy.sql import func

from ..db.base_class import BaseDB  # assuming this is your declarative base


class StatusEnum(PyEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    # You can add more later: DRAFT, CANCELLED, ARCHIVED, etc.


class CommercialInvoice(BaseDB):
    __tablename__ = "commercial_invoices"   # better name than just "invoices"

    id = Column(Integer, primary_key=True, index=True)

    # Main business key — should be unique
    reference_number = Column(
        String(80),
        nullable=False,
        unique=True,
        index=True,
        comment="e.g. ES-00130-ori / ES-00130-fin"
    )

    # Full original JSON data (recommended to store the complete parsed structure)
    raw_json = Column(
        JSON,                    # or JSON (PostgreSQL) / MEDIUMTEXT (MySQL)
        nullable=False,
        comment="Complete original JSON document"
    )

    # Whether this is the original parsed version or a modified/processed one
    is_original = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="True = original extraction, False = manually corrected/versioned"
    )

    # Example of extracted/indexed fields (add more as needed)
    
    divided_by = Column(
        Float,
        nullable=True,
        comment="Your custom division factor (?)"
    )

    # Status
    status = Column(
        Enum(StatusEnum),
        nullable=False,
        default=StatusEnum.ACTIVE,
        index=True
    )

    # Audit fields
    created_by = Column(Integer, nullable=False, comment="User ID who created")
    updated_by = Column(Integer, nullable=False, comment="User ID who last modified")

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    
