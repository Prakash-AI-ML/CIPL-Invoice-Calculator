from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from collections import defaultdict


def current_month_range(to_date=None):
    # If to_date is not provided, use today's date
    if to_date is None:
        today = date.today()
    else:
        # If to_date is a string like "2025-12-13", convert it to date
        if isinstance(to_date, str):
            today = datetime.strptime(to_date, "%Y-%m-%d").date()
        else:
            # Assume it's already a date object
            today = to_date

    # Start date is the 1st of the month
    start_date = date(today.year, today.month, 1)

    # End date is the last day of the month
    end_date = start_date + relativedelta(months=1) - relativedelta(days=1)

    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

async def total_payable(session: AsyncSession):
    query = text("""SELECT
    -- Current
    COUNT(CASE
        WHEN pa.balance > 0 AND pa.status != 1
         AND DATEDIFF(CURDATE(), DATE_ADD(pa.updated_invoice_date, INTERVAL COALESCE(c.pay_term, 30) DAY)) <= 0
        THEN 1 END) AS current_count,

    ROUND(SUM(CASE
        WHEN pa.balance > 0 AND pa.status != 1
         AND DATEDIFF(CURDATE(), DATE_ADD(pa.updated_invoice_date, INTERVAL COALESCE(c.pay_term, 30) DAY)) <= 0
        THEN pa.balance ELSE 0 END), 2) AS current_amount,

    -- 1–30
    COUNT(CASE
        WHEN pa.balance > 0 AND pa.status != 1
         AND DATEDIFF(CURDATE(), DATE_ADD(pa.updated_invoice_date, INTERVAL COALESCE(c.pay_term, 30) DAY)) BETWEEN 1 AND 30
        THEN 1 END) AS overdue_1_30_count,

    ROUND(SUM(CASE
        WHEN pa.balance > 0 AND pa.status != 1
         AND DATEDIFF(CURDATE(), DATE_ADD(pa.updated_invoice_date, INTERVAL COALESCE(c.pay_term, 30) DAY)) BETWEEN 1 AND 30
        THEN pa.balance ELSE 0 END), 2) AS overdue_1_30_amount,

    -- 31–60
    COUNT(CASE
        WHEN pa.balance > 0 AND pa.status != 1
         AND DATEDIFF(CURDATE(), DATE_ADD(pa.updated_invoice_date, INTERVAL COALESCE(c.pay_term, 30) DAY)) BETWEEN 31 AND 60
        THEN 1 END) AS overdue_31_60_count,

    ROUND(SUM(CASE
        WHEN pa.balance > 0 AND pa.status != 1
         AND DATEDIFF(CURDATE(), DATE_ADD(pa.updated_invoice_date, INTERVAL COALESCE(c.pay_term, 30) DAY)) BETWEEN 31 AND 60
        THEN pa.balance ELSE 0 END), 2) AS overdue_31_60_amount,

    -- 61–90
    COUNT(CASE
        WHEN pa.balance > 0 AND pa.status != 1
         AND DATEDIFF(CURDATE(), DATE_ADD(pa.updated_invoice_date, INTERVAL COALESCE(c.pay_term, 30) DAY)) BETWEEN 61 AND 90
        THEN 1 END) AS overdue_61_90_count,

    ROUND(SUM(CASE
        WHEN pa.balance > 0 AND pa.status != 1
         AND DATEDIFF(CURDATE(), DATE_ADD(pa.updated_invoice_date, INTERVAL COALESCE(c.pay_term, 30) DAY)) BETWEEN 61 AND 90
        THEN pa.balance ELSE 0 END), 2) AS overdue_61_90_amount,
                 
    -- 61–90
    COUNT(CASE
        WHEN pa.balance > 0 AND pa.status != 1
         AND DATEDIFF(CURDATE(), DATE_ADD(pa.updated_invoice_date, INTERVAL COALESCE(c.pay_term, 30) DAY)) BETWEEN 91 AND 120
        THEN 1 END) AS overdue_91_120_count,

    ROUND(SUM(CASE
        WHEN pa.balance > 0 AND pa.status != 1
         AND DATEDIFF(CURDATE(), DATE_ADD(pa.updated_invoice_date, INTERVAL COALESCE(c.pay_term, 30) DAY)) BETWEEN 91 AND 120
        THEN pa.balance ELSE 0 END), 2) AS overdue_91_120_amount,
                 
    -- 61–90
    COUNT(CASE
        WHEN pa.balance > 0 AND pa.status != 1
         AND DATEDIFF(CURDATE(), DATE_ADD(pa.updated_invoice_date, INTERVAL COALESCE(c.pay_term, 30) DAY)) BETWEEN 121 AND 150
        THEN 1 END) AS overdue_121_150_count,

    ROUND(SUM(CASE
        WHEN pa.balance > 0 AND pa.status != 1
         AND DATEDIFF(CURDATE(), DATE_ADD(pa.updated_invoice_date, INTERVAL COALESCE(c.pay_term, 30) DAY)) BETWEEN 121 AND 150
        THEN pa.balance ELSE 0 END), 2) AS overdue_121_150_amount,
                 
    -- 61–90
    COUNT(CASE
        WHEN pa.balance > 0 AND pa.status != 1
         AND DATEDIFF(CURDATE(), DATE_ADD(pa.updated_invoice_date, INTERVAL COALESCE(c.pay_term, 30) DAY)) > 150
        THEN 1 END) AS overdue_150_count,

    ROUND(SUM(CASE
        WHEN pa.balance > 0 AND pa.status != 1
         AND DATEDIFF(CURDATE(), DATE_ADD(pa.updated_invoice_date, INTERVAL COALESCE(c.pay_term, 30) DAY)) > 150
        THEN pa.balance ELSE 0 END), 2) AS overdue_150_amount

FROM payable_aging pa
LEFT JOIN invoices i 
    ON i.customer_id COLLATE utf8mb4_unicode_ci = pa.customer_id COLLATE utf8mb4_unicode_ci
LEFT JOIN client_details c 
    ON TRIM(c.name) = TRIM(i.customer_name);
""")

    result = await session.execute(query)
    row = result.mappings().first() or {}

    return {
        "not_in_overdue": {
            "count": row.get("current_count", 0),
            "total_amount": float(row.get("current_amount", 0))
        },

        "current": {
                "count": row.get("overdue_1_30_count", 0),
                "total_amount": float(row.get("overdue_1_30_amount", 0))
            },
        "overdue": {
            
            "31_60": {
                "count": row.get("overdue_31_60_count", 0),
                "total_amount": float(row.get("overdue_31_60_amount", 0))
            },
            "61_90": {
                "count": row.get("overdue_61_90_count", 0),
                "total_amount": float(row.get("overdue_61_90_amount", 0))
            },
             "91_120": {
                "count": row.get("overdue_91_120_count", 0),
                "total_amount": float(row.get("overdue_91_120_amount", 0))
            },
             "121_150": {
                "count": row.get("overdue_121_150_count", 0),
                "total_amount": float(row.get("overdue_121_150_amount", 0))
            },
            "150+": {
                "count": row.get("overdue_150_count", 0),
                "total_amount": float(row.get("overdue_150_amount", 0))
            }
        }
    }


async def get_cash_flow(
    session: AsyncSession,
    year: int | None = None,
    quarter: str | None = None
):
    # ----------------------------
    # Validate year (only if provided)
    # ----------------------------
    if year is not None:
        if year < 2018 or year > 2026:
            raise ValueError("Year must be between 2018 and 2026")

    # ----------------------------
    # Quarter date ranges
    # ----------------------------
    quarter_ranges = {
        "q1": (1, 1, 3, 31),
        "q2": (4, 1, 6, 30),
        "q3": (7, 1, 9, 30),
        "q4": (10, 1, 12, 31),
    }

    credit_filter = ""
    debit_filter = ""
    params = {}

    # ----------------------------
    # Date filtering logic
    # ----------------------------
    if year is not None:
        if quarter:
            quarter = quarter.lower()
            if quarter not in quarter_ranges:
                raise ValueError("Quarter must be one of: q1, q2, q3, q4")

            sm, sd, em, ed = quarter_ranges[quarter]
            start_date = date(year, sm, sd)
            end_date = date(year, em, ed)
        else:
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)

        credit_filter = "AND pa.invoice_date BETWEEN :start_date AND :end_date"
        debit_filter = "AND pa.debit_date BETWEEN :start_date AND :end_date"
        params["start_date"] = start_date
        params["end_date"] = end_date

    elif quarter:
        raise ValueError("Quarter cannot be used without specifying a year")

    # ----------------------------
    # SQL Query
    # ----------------------------
    query = text(f"""
        SELECT 
            month,
            ROUND(SUM(monthly_credit), 2) AS monthly_credit,
            ROUND(SUM(monthly_debit), 2) AS monthly_debit
        FROM (
            -- Credit (Invoice Date)
            SELECT 
                DATE_FORMAT(pa.invoice_date, '%Y-%m') AS month,
                SUM(pa.credit) AS monthly_credit,
                0 AS monthly_debit
            FROM payable_aging pa
            WHERE pa.invoice_date IS NOT NULL
            {credit_filter}
            GROUP BY DATE_FORMAT(pa.invoice_date, '%Y-%m')

            UNION ALL

            -- Debit (Payment Date)
            SELECT 
                DATE_FORMAT(pa.debit_date, '%Y-%m') AS month,
                0 AS monthly_credit,
                SUM(pa.debit) AS monthly_debit
            FROM payable_aging pa
            WHERE pa.debit_date IS NOT NULL
            {debit_filter}
            GROUP BY DATE_FORMAT(pa.debit_date, '%Y-%m')
        ) t
        GROUP BY month
        ORDER BY month DESC
    """)

    # ----------------------------
    # Execute
    # ----------------------------
    result = await session.execute(query, params)
    return result.mappings().all()


async def total_expenses_by_category(
    session: AsyncSession,
    year: int | None = None,
    quarter: str | None = None
):
    # ----------------------------
    # Validate year (only if given)
    # ----------------------------
    if year is not None:
        if year < 2018 or year > 2026:
            raise ValueError("Year must be between 2018 and 2026")

    # ----------------------------
    # Quarter date ranges
    # ----------------------------
    quarter_ranges = {
        "q1": (1, 1, 3, 31),
        "q2": (4, 1, 6, 30),
        "q3": (7, 1, 9, 30),
        "q4": (10, 1, 12, 31),
    }

    params = {}
    date_filter = ""

    # ----------------------------
    # Date filtering logic
    # ----------------------------
    if year is not None:
        if quarter:
            quarter = quarter.lower()
            if quarter not in quarter_ranges:
                raise ValueError("Quarter must be one of: q1, q2, q3, q4")

            sm, sd, em, ed = quarter_ranges[quarter]
            start_date = date(year, sm, sd)
            end_date = date(year, em, ed)
        else:
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)

        date_filter = """
            WHERE (
                pa.invoice_date BETWEEN :start_date AND :end_date
                OR pa.debit_date BETWEEN :start_date AND :end_date
            )
        """
        params["start_date"] = start_date
        params["end_date"] = end_date

    elif quarter:
        raise ValueError("Quarter cannot be used without a year")

    # ----------------------------
    # SQL Query
    # ----------------------------
    query = text(f"""
        SELECT 
            COALESCE(c.merchant_category, 'Others') AS merchant_category,
            ROUND(SUM(pa.credit), 2) AS total_credit,
            ROUND(SUM(pa.debit), 2) AS total_debit
        FROM payable_aging pa
        LEFT JOIN invoices i 
            ON i.customer_id COLLATE utf8mb4_unicode_ci =
               pa.customer_id COLLATE utf8mb4_unicode_ci
        LEFT JOIN client_details c 
            ON TRIM(c.name) = TRIM(i.customer_name)
        {date_filter}
        GROUP BY COALESCE(c.merchant_category, 'Others')
        ORDER BY total_debit DESC
    """)

    # ----------------------------
    # Execute
    # ----------------------------
    result = await session.execute(query, params)
    return result.mappings().all()



async def cash_flow_category_monthly(
    session: AsyncSession,
    year: int | None = None,
    quarter: str | None = None
):
    # ----------------------------
    # Validate year (only if provided)
    # ----------------------------
    if year is not None:
        if year < 2018 or year > 2026:
            raise ValueError("Year must be between 2018 and 2026")

    # ----------------------------
    # Quarter date ranges
    # ----------------------------
    quarter_ranges = {
        "q1": (1, 1, 3, 31),
        "q2": (4, 1, 6, 30),
        "q3": (7, 1, 9, 30),
        "q4": (10, 1, 12, 31),
    }

    params = {}
    invoice_date_filter = ""
    debit_date_filter = ""

    # ----------------------------
    # Date filtering logic
    # ----------------------------
    if year is not None:
        if quarter:
            quarter = quarter.lower()
            if quarter not in quarter_ranges:
                raise ValueError("Quarter must be one of: q1, q2, q3, q4")

            sm, sd, em, ed = quarter_ranges[quarter]
            start_date = date(year, sm, sd)
            end_date = date(year, em, ed)
        else:
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)

        invoice_date_filter = "WHERE pa.invoice_date BETWEEN :start_date AND :end_date"
        debit_date_filter = "WHERE pa.debit_date BETWEEN :start_date AND :end_date"

        params["start_date"] = start_date
        params["end_date"] = end_date

    elif quarter:
        raise ValueError("Quarter cannot be used without specifying a year")

    # ----------------------------
    # SQL Query
    # ----------------------------
    query = text(f"""
        SELECT 
            month,
            merchant_category,
            ROUND(SUM(monthly_credit), 2) AS monthly_credit,
            ROUND(SUM(monthly_debit), 2) AS monthly_debit,
            ROUND(SUM(monthly_credit - monthly_debit), 2) AS net_cash_flow
        FROM (
            -- Credit side (invoice date)
            SELECT
                DATE_FORMAT(pa.invoice_date, '%Y-%m') AS month,
                COALESCE(c.merchant_category, 'Others') AS merchant_category,
                SUM(pa.credit) AS monthly_credit,
                0 AS monthly_debit
            FROM payable_aging pa
            LEFT JOIN invoices i
                ON i.customer_id COLLATE utf8mb4_unicode_ci =
                   pa.customer_id COLLATE utf8mb4_unicode_ci
            LEFT JOIN client_details c
                ON TRIM(c.name) = TRIM(i.customer_name)
            {invoice_date_filter}
            GROUP BY month, merchant_category

            UNION ALL

            -- Debit side (payment date)
            SELECT
                DATE_FORMAT(pa.debit_date, '%Y-%m') AS month,
                COALESCE(c.merchant_category, 'Others') AS merchant_category,
                0 AS monthly_credit,
                SUM(pa.debit) AS monthly_debit
            FROM payable_aging pa
            LEFT JOIN invoices i
                ON i.customer_id COLLATE utf8mb4_unicode_ci =
                   pa.customer_id COLLATE utf8mb4_unicode_ci
            LEFT JOIN client_details c
                ON TRIM(c.name) = TRIM(i.customer_name)
            {debit_date_filter}
            GROUP BY month, merchant_category
        ) t
        GROUP BY month, merchant_category
        ORDER BY month DESC, net_cash_flow DESC
    """)

    # ----------------------------
    # Execute
    # ----------------------------
    result = await session.execute(query, params)
    return result.mappings().all()


async def payable_analysis(
    session: AsyncSession,
    year: int | None = None,
    quarter: str | None = None
):
    # ----------------------------
    # Validate year
    # ----------------------------
    if year is not None:
        if year < 2018 or year > 2026:
            raise ValueError("Year must be between 2018 and 2026")

    # ----------------------------
    # Quarter date ranges
    # ----------------------------
    quarter_ranges = {
        "q1": (1, 1, 3, 31),
        "q2": (4, 1, 6, 30),
        "q3": (7, 1, 9, 30),
        "q4": (10, 1, 12, 31),
    }

    date_filter = ""
    params = {}

    # ----------------------------
    # Date filtering logic
    # ----------------------------
    if year is not None:
        if quarter:
            quarter = quarter.lower()
            if quarter not in quarter_ranges:
                raise ValueError("Quarter must be one of: q1, q2, q3, q4")

            sm, sd, em, ed = quarter_ranges[quarter]
            start_date = date(year, sm, sd)
            end_date = date(year, em, ed)
        else:
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)

        date_filter = """
            WHERE (
                pa.invoice_date BETWEEN :start_date AND :end_date
                OR pa.debit_date BETWEEN :start_date AND :end_date
            )
        """
        params["start_date"] = start_date
        params["end_date"] = end_date

    elif quarter:
        raise ValueError("Quarter cannot be used without specifying a year")

    # ----------------------------
    # SQL Query
    # ----------------------------
    query = text(f"""
        SELECT
            COUNT(*) AS total_invoices,

            SUM(
                CASE
                    WHEN status = 1 THEN 1
                    ELSE 0
                END
            ) AS paid_invoices,

            SUM(
                CASE
                    WHEN pa.debit = 0 AND pa.credit > 0 THEN 1
                    ELSE 0
                END
            ) AS unpaid_invoices,

            SUM(
                CASE
                    WHEN pa.debit > 0 AND pa.debit < pa.credit THEN 1
                    ELSE 0
                END
            ) AS partially_paid_invoices
        FROM payable_aging pa
        {date_filter}
    """)

    # ----------------------------
    # Execute
    # ----------------------------
    result = await session.execute(query, params)
    return result.mappings().one()


async def monthly_invoice_analysis(
    session: AsyncSession,
    year: int | None = None,
    quarter: str | None = None
):
    # ----------------------------
    # Validate year
    # ----------------------------
    if year is not None:
        if year < 2018 or year > 2026:
            raise ValueError("Year must be between 2018 and 2026")

    # ----------------------------
    # Quarter date ranges
    # ----------------------------
    quarter_ranges = {
        "q1": (1, 1, 3, 31),
        "q2": (4, 1, 6, 30),
        "q3": (7, 1, 9, 30),
        "q4": (10, 1, 12, 31),
    }

    date_filter = ""
    params = {}

    # ----------------------------
    # Date filtering logic
    # ----------------------------
    if year is not None:
        if quarter:
            quarter = quarter.lower()
            if quarter not in quarter_ranges:
                raise ValueError("Quarter must be one of: q1, q2, q3, q4")
            sm, sd, em, ed = quarter_ranges[quarter]
            start_date = date(year, sm, sd)
            end_date = date(year, em, ed)
        else:
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)

        date_filter = """
            WHERE pa.invoice_date BETWEEN :start_date AND :end_date
        """
        params["start_date"] = start_date
        params["end_date"] = end_date

    elif quarter:
        raise ValueError("Quarter cannot be used without specifying a year")

    # ----------------------------
    # SQL Query
    # ----------------------------
    query = text(f"""
        SELECT
            DATE_FORMAT(pa.invoice_date, '%Y-%m') AS month,
            COUNT(*) AS total_invoices,
            
            SUM(
                CASE WHEN status = 1 THEN 1 ELSE 0 END
            ) AS paid_invoices,

            SUM(
                CASE WHEN pa.debit = 0 AND pa.credit > 0 THEN 1 ELSE 0 END
            ) AS unpaid_invoices,

            SUM(
                CASE WHEN pa.debit > 0 AND pa.debit < pa.credit THEN 1 ELSE 0 END
            ) AS partially_paid_invoices

        FROM payable_aging pa
        {date_filter}
        GROUP BY month
        ORDER BY month DESC
    """)

    # ----------------------------
    # Execute
    # ----------------------------
    result = await session.execute(query, params)
    return result.mappings().all()


async def current_month_payment_analysis(session: AsyncSession,):
    query = text("""SELECT
            pc.*,
            u.username as payment_by_,
        CASE
            WHEN pc.approval_status = 'APPROVED'
            THEN users.username
            ELSE NULL
        END AS approved_by_
            FROM payment_clearance pc
             LEFT JOIN subscribers u 
        ON pc.payment_by = u.id
    LEFT JOIN subscribers users
        ON pc.updated_by = users.id
            WHERE pc.debit_date BETWEEN :start_date AND :end_date 
            """)
    
    payment_date = current_month_range()
    params = {'start_date': payment_date[0], 'end_date':payment_date[1]}
    
    result = await session.execute(query, params)
    data = result.mappings().all()

    if data:
        result = {
            "total": 0,
        "approved": {
            "total": 0,
            "by": defaultdict(float)
        },
        "pending": {
            "total": 0,
            "by": defaultdict(float)
        }
    }

        for item in data:
            debit = float(item.get("debit", 0))

            if item.get("approval_status") == "APPROVED":
                user = item.get("approved_by_") or "Unknown"
                result["approved"]["total"] += debit
                result["approved"]["by"][user] += debit

            elif item.get("approval_status") == "PENDING":
                user = item.get("payment_by_") or "Unknown"
                result["pending"]["total"] += debit
                result["pending"]["by"][user] += debit
            result['total'] += debit

        # convert users dict → list
        result["approved"]["by"] = [
            {"name": user, "total": total}
            for user, total in result["approved"]["by"].items()
        ]

        result["pending"]["by"] = [
            {"name": user, "total": total}
            for user, total in result["pending"]["by"].items()
        ]
        return result
    return data


