from sqlalchemy.orm import Session
from app.models.statement import Statement, StatementFormat
from app.models.account import Account
from app.models.transaction import Transaction
from app.schemas.statement import StatementData, TransactionSummary
from typing import List, Optional
from datetime import date, datetime, timezone
from decimal import Decimal
import os
import json
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch


class StatementService:
    """Service for generating and managing account statements"""
    
    @staticmethod
    def generate_statement(
        db: Session,
        account_id: int,
        period_start: date,
        period_end: date,
        format: str
    ) -> Statement:
        """
        Generate a statement for an account
        Returns: Statement object with file_path populated
        """
        # Validate account exists
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise ValueError("Account not found")
        
        # Validate date range
        if period_start > period_end:
            raise ValueError("Start date must be before end date")
        
        # Get transactions for the period
        transactions = db.query(Transaction).filter(
            ((Transaction.from_account_id == account_id) | (Transaction.to_account_id == account_id)),
            Transaction.created_at >= period_start,
            Transaction.created_at < datetime.combine(period_end, datetime.max.time())
        ).order_by(Transaction.created_at).all()
        
        # Calculate summary
        statement_data = StatementService._calculate_summary(
            account, transactions, period_start, period_end
        )
        
        # Generate file based on format
        if format.lower() == "json":
            file_path = StatementService._generate_json_statement(statement_data, account_id)
        elif format.lower() == "pdf":
            file_path = StatementService._generate_pdf_statement(statement_data, account_id)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        # Create statement record
        statement = Statement(
            account_id=account_id,
            statement_period_start=period_start,
            statement_period_end=period_end,
            format=StatementFormat(format.lower()),
            file_path=file_path
        )
        
        db.add(statement)
        db.commit()
        db.refresh(statement)
        
        return statement
    
    @staticmethod
    def _calculate_summary(
        account: Account,
        transactions: List[Transaction],
        period_start: date,
        period_end: date
    ) -> StatementData:
        """Calculate statement summary and transaction list"""
        # Get opening balance (balance at start of period)
        opening_balance = account.balance  # Simplified - in production, calculate from history
        
        total_debits = Decimal('0.00')
        total_credits = Decimal('0.00')
        running_balance = opening_balance
        transaction_summaries = []
        
        for txn in transactions:
            # Determine if this is a debit or credit for this account
            is_debit = txn.from_account_id == account.id
            amount = txn.amount
            
            if is_debit:
                total_debits += amount
                running_balance -= amount
                debit = amount
                credit = None
            else:
                total_credits += amount
                running_balance += amount
                debit = None
                credit = amount
            
            transaction_summaries.append(TransactionSummary(
                date=txn.created_at,
                description=txn.description or f"{txn.transaction_type.value} - {txn.reference_number}",
                debit=debit,
                credit=credit,
                balance=running_balance
            ))
        
        closing_balance = running_balance
        
        return StatementData(
            account_number=account.account_number,
            account_holder_name=f"{account.account_holder.first_name} {account.account_holder.last_name}",
            statement_period_start=period_start,
            statement_period_end=period_end,
            opening_balance=opening_balance,
            closing_balance=closing_balance,
            total_debits=total_debits,
            total_credits=total_credits,
            transactions=transaction_summaries,
            generated_at=datetime.now(timezone.utc)
        )
    
    @staticmethod
    def _generate_json_statement(statement_data: StatementData, account_id: int) -> str:
        """Generate JSON format statement"""
        # Create statements directory if it doesn't exist
        os.makedirs("statements", exist_ok=True)
        
        # Generate filename
        filename = f"statement_{account_id}_{statement_data.statement_period_start}_{statement_data.statement_period_end}.json"
        file_path = os.path.join("statements", filename)
        
        # Convert to dict and save
        with open(file_path, 'w') as f:
            json.dump(statement_data.model_dump(mode='json'), f, indent=2, default=str)
        
        return file_path
    
    @staticmethod
    def _generate_pdf_statement(statement_data: StatementData, account_id: int) -> str:
        """Generate PDF format statement"""
        # Create statements directory if it doesn't exist
        os.makedirs("statements", exist_ok=True)
        
        # Generate filename
        filename = f"statement_{account_id}_{statement_data.statement_period_start}_{statement_data.statement_period_end}.pdf"
        file_path = os.path.join("statements", filename)
        
        # Create PDF
        doc = SimpleDocTemplate(file_path, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title = Paragraph("<b>Account Statement</b>", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 0.2*inch))
        
        # Account info
        account_info = [
            ["Account Number:", statement_data.account_number],
            ["Account Holder:", statement_data.account_holder_name],
            ["Statement Period:", f"{statement_data.statement_period_start} to {statement_data.statement_period_end}"],
            ["Generated:", statement_data.generated_at.strftime("%Y-%m-%d %H:%M:%S")]
        ]
        
        info_table = Table(account_info, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Transaction table
        data = [["Date", "Description", "Debit", "Credit", "Balance"]]
        
        for txn in statement_data.transactions:
            data.append([
                txn.date.strftime("%Y-%m-%d %H:%M"),
                txn.description[:40],  # Truncate long descriptions
                f"${txn.debit:.2f}" if txn.debit else "",
                f"${txn.credit:.2f}" if txn.credit else "",
                f"${txn.balance:.2f}"
            ])
        
        txn_table = Table(data, colWidths=[1.5*inch, 2.5*inch, 1*inch, 1*inch, 1*inch])
        txn_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(txn_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Summary
        summary_data = [
            ["Opening Balance:", f"${statement_data.opening_balance:.2f}"],
            ["Total Debits:", f"${statement_data.total_debits:.2f}"],
            ["Total Credits:", f"${statement_data.total_credits:.2f}"],
            ["Closing Balance:", f"${statement_data.closing_balance:.2f}"]
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 1.5*inch])
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (0, 3), (1, 3), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('LINEABOVE', (0, 3), (-1, 3), 2, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(summary_table)
        
        # Build PDF
        doc.build(story)
        
        return file_path
    
    @staticmethod
    def get_statement_by_id(db: Session, statement_id: int) -> Optional[Statement]:
        """Get statement by ID"""
        return db.query(Statement).filter(Statement.id == statement_id).first()
    
    @staticmethod
    def list_statements(db: Session, account_id: int) -> List[Statement]:
        """List all statements for an account"""
        return db.query(Statement).filter(
            Statement.account_id == account_id
        ).order_by(Statement.generated_at.desc()).all()
