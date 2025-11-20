import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import Base, get_db
from backend.config import settings

# Use the local PostgreSQL database for testing
# In a real CI/CD, this would be a separate test database
SQLALCHEMY_DATABASE_URL = settings.database_url

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    # Create tables once for the session
    Base.metadata.create_all(bind=engine)
    yield
    # Drop tables after session
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db():
    # Connect to the database
    connection = engine.connect()
    # Begin a non-ORM transaction
    transaction = connection.begin()
    
    # Bind an individual Session to the connection
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    # Rollback the transaction
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass  # Session is closed in the db fixture
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    del app.dependency_overrides[get_db]
