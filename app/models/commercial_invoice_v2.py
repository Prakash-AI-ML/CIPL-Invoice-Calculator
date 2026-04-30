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
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from ..db.base_class import BaseDB  # assuming this is your declarative base


class StatusEnum(PyEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    # You can add more later: DRAFT, CANCELLED, ARCHIVED, etc.

class CiplList(BaseDB):
    __tablename__ = "cipl_list"   # better name than just "invoices"

    id = Column(Integer, primary_key=True, index=True, autoincrement= True)

    job_number = Column(
        String(800),
        nullable=True,
        unique= True,
        comment="TPL/00xxP/MM/YY"
    )

    group_number = Column(
        String(900),
        nullable=True,
        unique= True,
        comment="ES-00136,ES-00137,ES-00140,ES-00141..."
    )
    vessel = Column(
        String(800),
        nullable=True,
        unique= False,
        comment="CEBU / INCEDA / KOTA LORIS... "
    )

    voyage = Column(
        String(900),
        nullable=True,
        comment="060N, 045N, 059N, 097N..."
    )
    truck_type = Column(
        String(900),
        nullable=True,
        comment="6x40'OT / 4x40'OT / 1x40'OT..."
    )
    bl_no = Column(
        String(900),
        nullable=True,
        unique= True,
        comment="SESOC2604011501"
    )
    cipl_ori = Column(
        String(900),
        nullable=True,
        comment="ES-00136-ORI ,ES-00137-ORI ,ES-00140-ORI ,ES-00141-ORI..."
    )
    cipl_fnl = Column(
        String(900),
        nullable=True,
        comment="ES-00136-FNL,ES-00137-FNL,ES-00140-FNL,ES-00141-FNL..."
    )
    # Full original JSON data (recommended to store the complete parsed structure)
    

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

    commercial_invoices = relationship(
        "CommercialInvoiceV2",
        back_populates="cipl_list",
        cascade="all, delete-orphan"
    )

 

class CommercialInvoiceV2(BaseDB):
    __tablename__ = "commercial_invoices_v2"   # better name than just "invoices"

    id = Column(Integer, primary_key=True, index=True, autoincrement= True)
    
    cipl_list_id = Column(
    Integer,
    ForeignKey("cipl_list.id", ondelete="SET NULL"),  # or CASCADE if you prefer
    nullable=True,
    index=True
)

    # Main business key — should be unique
    reference_number = Column(
        String(80),
        nullable=False,
        unique=True,
        index=True,
        comment="e.g. ES-00130-ori / ES-00130-fin"
    )

    job_number = Column(
        String(800),
        nullable=True,
        comment="TPL/00xxP/MM/YY"
    )

    group_number = Column(
        String(900),
        nullable=True,
        comment="ES-00136,ES-00137,ES-00140,ES-00141..."
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

    cipl_list = relationship("CiplList", back_populates="commercial_invoices")

    
