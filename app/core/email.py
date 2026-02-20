from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import pandas as pd
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class EmailConfig:
    @staticmethod
    def get_config():
            # Validate required fields for production
        required = [settings.mail_username, settings.mail_password, settings.mail_from, settings.mail_server, settings.mail_from_name]
        if not all(required):
            logger.warning("Production email config incomplete – falling back to dev mode (no emails sent)")
            return ConnectionConfig(SUPPRESS_SEND=1)

        return ConnectionConfig(
            MAIL_USERNAME=settings.mail_username,
            MAIL_PASSWORD=settings.mail_password,
            MAIL_FROM=settings.mail_from,
            MAIL_FROM_NAME=settings.mail_from_name,
            MAIL_PORT=settings.mail_port or 587,
            MAIL_SERVER=settings.mail_server,
            MAIL_STARTTLS = True,
            MAIL_SSL_TLS = False,
            USE_CREDENTIALS = True,
            VALIDATE_CERTS = True
        )
        

# Instantiate once at import time
conf = EmailConfig.get_config()
fm = FastMail(conf)

async def send_reset_email(email: str, username: str, reset_url: str):
    template = f"""
    <div style="font-family: 'Poppins', sans-serif; max-width: 600px; margin: auto; padding: 30px; background: #f8fafc; border-radius: 16px; text-align: center;">
        <h2 style="color: #2563eb;">Password Reset Request</h2>
        <p>Hello <strong>{username}</strong>,</p>
        <p>You requested to reset your password for <strong>Accounts AI</strong>.</p>
        <div style="margin: 40px 0;">
            <a href="{reset_url}" style="background: linear-gradient(135deg, #38bdf8, #22c55e); color: white; padding: 16px 36px; border-radius: 999px; text-decoration: none; font-weight: 600; font-size: 16px; display: inline-block;">
                Reset Password Now
            </a>
        </div>
        <p><small>This link will expire in 15 minutes.</small></p>
        <p><small>If you didn't request this, please ignore this email.</small></p>
        <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 40px 0;">
        <p style="color: #64748b; font-size: 13px;">© 2025 Accounts AI • Secure Financial Management</p>
    </div>
    """

    message = MessageSchema(
        subject="Reset Your Accounts AI Password",
        recipients=[email],
        body=template,
        subtype="html"
    )

    try:
        await fm.send_message(message)
        logger.info(f"Password reset email sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send email to {email}: {e}")
   

async def send_due_today_reminder_email(email: str, username: str, response: list[dict]):
    """
    Send a daily reminder email for invoices due TODAY (days_remaining_for_payment == 0).
    
    :param email: Recipient email address
    :param username: Recipient's username
    :param response: List of dicts from the query result (empty if no invoices)
    """
    if not response:
        # No invoices due today → do not send email
        logger.info("No invoices due today. Skipping email.")
        return

    df = pd.DataFrame(response)

    # Ensure sorted by client_name then invoice_date (matching query ORDER BY)
    df = df.sort_values(['client_name', 'invoice_date']).reset_index(drop=True)

    # Blank client_name after the first occurrence per client
    df['client_name_display'] = df.groupby('client_name')['client_name'].transform(
        lambda x: x.where(x.duplicated(keep='first'), x)
    )
    df['client_name_display'] = df['client_name_display'].fillna('')

    # Due text: "Today" since all rows have days_remaining_for_payment == 0
    df['due_text'] = 'Today'

    # Select and rename relevant columns
    table_df = df[[
        'client_name_display', 'ref_no', 'invoice_date',
        'description', 'credit', 'debit', 'balance', 'due_text'
    ]].rename(columns={
        'client_name_display': 'Client Name',
        'ref_no': 'Invoice Ref',
        'invoice_date': 'Invoice Date',
        'description': 'Description',
        'balance': 'Outstanding Balance',
        'due_text': 'Due'
    })

    # Generate styled HTML table with visual separators between clients
    html_table = '''
    <table style="width:100%; max-width:1000px; border-collapse: collapse; font-family: 'Poppins', sans-serif; margin: 30px 0; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <thead>
            <tr style="background: linear-gradient(135deg, #2563eb, #38bdf8); color: white;">
                <th style="padding: 16px; text-align: left;">Client Name</th>
                <th style="padding: 16px; text-align: left;">Invoice Ref</th>
                <th style="padding: 16px; text-align: left;">Invoice Date</th>
                <th style="padding: 16px; text-align: left;">Description</th>
                <th style="padding: 16px; text-align: left;">Credit</th>
                <th style="padding: 16px; text-align: left;">Previous Debit</th>
                <th style="padding: 16px; text-align: right;">Outstanding Balance</th>
                <th style="padding: 16px; text-align: center;">Due</th>
            </tr>
        </thead>
        <tbody>
    '''

    prev_client = None
    for i, row in table_df.iterrows():
        current_client = row['Client Name']

        # Add visual separator (empty row) when client changes
        if prev_client is not None and current_client != prev_client and current_client != '':
            html_table += '<tr><td colspan="6" style="padding: 24px 0;"></td></tr>'

        # Alternating row background
        bg_color = "#f8fafc" if i % 2 == 0 else "white"

        html_table += f'''
        <tr style="background: {bg_color};">
            <td style="padding: 16px; vertical-align: top;">{current_client or ''}</td>
            <td style="padding: 16px; vertical-align: top;">{row['Invoice Ref']}</td>
            <td style="padding: 16px; vertical-align: top;">{row['Invoice Date']}</td>
            <td style="padding: 16px; vertical-align: top;">{row['Description'] or ''}</td>
            <td style="padding: 16px; text-align: right; vertical-align: top;">{row['credit']:,.2f}</td>
            <td style="padding: 16px; text-align: right; vertical-align: top;">{row['debit']:,.2f}</td>
            <td style="padding: 16px; text-align: right; vertical-align: top; font-weight: 600;">RM {row['Outstanding Balance']:,.2f}</td>
            <td style="padding: 16px; text-align: center; vertical-align: top; font-weight: bold; color: #dc2626;">{row['Due']}</td>
        </tr>
        '''

        prev_client = current_client if current_client else prev_client
    # Add footer row with total
    html_table += f'''
        <tr>
            <td colspan="4" style="padding: 20px 16px; text-align: right; font-weight: 600; font-size: 16px; color: #1e293b;">
                Total (RM):
            </td>
            <td style="padding: 20px 16px; text-align: right; font-weight: 700; font-size: 16px; color: #525EF7;">
                {table_df['credit'].sum():,.2f}
            </td>
            <td style="padding: 20px 16px; text-align: right; font-weight: 700; font-size: 16px; color: #3DF295;">
                {table_df['debit'].sum():,.2f}
            </td>
            <td style="padding: 20px 16px; text-align: right; font-weight: 700; font-size: 16px; color: #dc2626;">
                {table_df['Outstanding Balance'].sum():,.2f}
            </td>
        </tr>
    '''
    html_table += '''
        </tbody>
    </table>
    '''

    # Full email template
    template = f"""
    <div style="font-family: 'Poppins', sans-serif; max-width: 1000px; margin: auto; padding: 30px; background: #f0f9ff; border-radius: 16px; text-align: center;">
        <h2 style="color: #2563eb;">Invoices Due Today – Action Required</h2>
        <p>Hello <strong>{username}</strong>,</p>
        <p>The following invoices are <strong>due today</strong>. Please ensure timely payment to avoid any late fees.</p>
        
        {html_table}
        
        <p>If you have already made payments, kindly disregard this reminder.</p>
        <p>For any questions, feel free to reply to this email.</p>
        
        <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 40px 0;">
        <p style="color: #64748b; font-size: 13px;">© 2025 Accounts AI • Secure Financial Management</p>
    </div>
    """

    message = MessageSchema(
        subject="Invoices Due Today – Immediate Attention Required",
        recipients=[email],
        body=template,
        subtype="html"
    )

    try:
        await fm.send_message(message)
        logger.info(f"Due today reminder email sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send due today email to {email}: {e}")
