from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.routes import auth, account_holders, accounts, transactions, cards, statements, card_transactions

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.API_VERSION,
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_PREFIX}/auth", tags=["Authentication"])
app.include_router(account_holders.router, prefix=f"{settings.API_PREFIX}/account-holders", tags=["Account Holders"])
app.include_router(accounts.router, prefix=f"{settings.API_PREFIX}/accounts", tags=["Accounts"])
app.include_router(transactions.router, prefix=f"{settings.API_PREFIX}/transactions", tags=["Transactions"])
app.include_router(cards.router, prefix=f"{settings.API_PREFIX}/cards", tags=["Cards"])
app.include_router(card_transactions.router, prefix=f"{settings.API_PREFIX}", tags=["Card Transactions"])
app.include_router(statements.router, prefix=f"{settings.API_PREFIX}", tags=["Statements"])


@app.get("/")
async def root():
    return {
        "message": "Banking REST Service API",
        "version": settings.API_VERSION,
        "docs": f"{settings.API_PREFIX}/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

