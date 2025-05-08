from sqlalchemy.orm import Session
from database.models import Invoice
from schemas.invoice_schema import InvoiceCreate, InvoiceUpdate


class InvoiceService:
    def __init__(self):
        self.model = Invoice

    def get(self, db: Session, invoice_id: int):
        return db.query(self.model).filter(self.model.id == invoice_id).first()

    def get_all(self, db: Session, skip: int = 0, limit: int = 100):
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, invoice: InvoiceCreate):
        db_invoice = self.model(**invoice.model_dump())
        db.add(db_invoice)
        db.commit()
        db.refresh(db_invoice)
        return db_invoice

    def update(self, db: Session, invoice_id: int, invoice: InvoiceUpdate):
        db_invoice = db.query(self.model).filter(self.model.id == invoice_id).first()
        if db_invoice:
            for key, value in invoice.model_dump(exclude_unset=True).items():
                setattr(db_invoice, key, value)
            db.commit()
            db.refresh(db_invoice)
        return db_invoice

    def delete(self, db: Session, invoice_id: int):
        db_invoice = db.query(self.model).filter(self.model.id == invoice_id).first()
        if db_invoice:
            db.delete(db_invoice)
            db.commit()
        return db_invoice
