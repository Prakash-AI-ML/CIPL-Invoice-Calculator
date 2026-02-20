from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, update, insert
from typing import Optional, Dict, Any, List, Tuple
import logging

logger = logging.getLogger(__name__)


async def get_clients(session: AsyncSession):
    query = text("""
        SELECT id, client_id, name, phone, address, pay_term, merchant_category, template, status FROM client_details
        """)
    result = await session.execute(query)
    rows = result.mappings().all()
    return [dict(row) for row in rows] if rows else []


async def get_clients_edit(session: AsyncSession,
                           client_index: int
                           ):
    query = text("""
        SELECT id, client_id, name, phone, address, pay_term, merchant_category, 
                 template, bank_name, bank_acc_number, bank_origin, swift_code, iban_no,
                  status FROM client_details 
                 WHERE id = :id
        """)
    result = await session.execute(query, {'id': client_index})
    rows = result.mappings().all()
    return [dict(row) for row in rows] if rows else []



async def insert_client(
    session: AsyncSession,
    client_data: dict
):
    query = text("""
        INSERT INTO client_details (
            client_id, name, phone, address, pay_term,
            merchant_category, template,
            bank_name, bank_acc_number, bank_origin,
            swift_code, iban_no, status, created_by, updated_by
        )
        VALUES (
            :client_id, :name, :phone, :address, :pay_term,
            :merchant_category, :template,
            :bank_name, :bank_acc_number, :bank_origin,
            :swift_code, :iban_no, :status, :created_by, :updated_by
        )
        
    """)

    result = await session.execute(query, client_data)
    await session.commit()

    return result.lastrowid # returns inserted row id



async def update_client(
    session: AsyncSession,
    client_index: int,
    client_data: dict
):
    query = text("""
        UPDATE client_details
        SET
            client_id = :client_id,
            name = :name,
            phone = :phone,
            address = :address,
            pay_term = :pay_term,
            merchant_category = :merchant_category,
            template = :template,
            bank_name = :bank_name,
            bank_acc_number = :bank_acc_number,
            bank_origin = :bank_origin,
            swift_code = :swift_code,
            iban_no = :iban_no,
            status = :status,
            created_by = :created_by,
            updated_by = :updated_by
                 
        WHERE id = :id
    """)

    client_data["id"] = client_index

    result = await session.execute(query, client_data)
    await session.commit()

    return result.rowcount  # number of updated rows


async def delete_client(
    session: AsyncSession,
    client_index: int
):
    query = text("""
        DELETE FROM client_details
        WHERE id = :id
    """)

    result = await session.execute(query, {"id": client_index})
    await session.commit()

    return result.rowcount  # number of deleted rows