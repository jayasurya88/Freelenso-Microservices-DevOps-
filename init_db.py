from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys
import importlib.util
from pathlib import Path

def init_service_db(service_name):
    print(f"\nInitializing database for {service_name}...")
    
    # Import the database and models modules from the service
    service_path = Path(f"services/{service_name}/app")
    
    # Import database module
    db_spec = importlib.util.spec_from_file_location(
        "database", service_path / "database.py"
    )
    database = importlib.util.module_from_spec(db_spec)
    db_spec.loader.exec_module(database)
    
    # Import models module
    models_spec = importlib.util.spec_from_file_location(
        "models", service_path / "models.py"
    )
    models = importlib.util.module_from_spec(models_spec)
    models_spec.loader.exec_module(models)
    
    try:
        # Create all tables
        database.Base.metadata.create_all(bind=database.engine)
        print(f"✅ Successfully initialized database for {service_name}")
    except Exception as e:
        print(f"❌ Error initializing database for {service_name}: {str(e)}")

def main():
    services = ["user-service", "project-service", "payment-service", "notification-service"]
    
    for service in services:
        init_service_db(service)

if __name__ == "__main__":
    main() 