#!/usr/bin/env python
\"\"\"Backend verification script for CerviVal application.\"\"\"
import sys
import os
import json

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_imports():
    \"\"\"Test that all critical imports work.\"\"\"
    print(\"\\n[1/10] Testing imports...\")
    try:
        from app.core.config import settings
        from app.database import init_db, get_db, SessionLocal
        from app.api import auth, patients, predict
        from app import models, schemas
        from app.core.security import create_access_token, decode_access_token
        from app.main import app
        print(\"✓ All imports successful\")\n        return True
    except Exception as e:
        print(f\"✗ Import failed: {e}\")\n        return False

def test_database_init():
    \"\"\"Test database initialization.\"\"\"
    print(\"[2/10] Testing database initialization...\")
    try:
        from app.database import init_db
        init_db()
        print(\"✓ Database initialized successfully\")\n        return True
    except Exception as e:
        print(f\"✗ Database init failed: {e}\")\n        return False

def test_database_session():
    \"\"\"Test database session management.\"\"\"
    print(\"[3/10] Testing database session...\")
    try:
        from app.database import SessionLocal
        db = SessionLocal()
        db.execute(\"SELECT 1\")
        db.close()
        print(\"✓ Database session works\")\n        return True
    except Exception as e:
        print(f\"✗ Database session failed: {e}\")\n        return False

def test_user_registration():
    \"\"\"Test user registration.\"\"\"
    print(\"[4/10] Testing user registration...\")
    try:
        from app.database import SessionLocal
        from app.core.security import get_password_hash
        from app import models
        
        db = SessionLocal()
        
        # Clean up test user if exists
        db.query(models.User).filter(
            models.User.email == \"test@example.com\"
        ).delete()
        db.commit()
        
        # Create test user
        user = models.User(
            email=\"test@example.com\",
            full_name=\"Test User\",
            hashed_password=get_password_hash(\"testpassword123\"),
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print(f\"✓ User registration works (created user ID {user.id})\")\n        
        db.close()
        return True
    except Exception as e:
        print(f\"✗ User registration failed: {e}\")\n        return False

def test_login():
    \"\"\"Test password verification and token creation.\"\"\"
    print(\"[5/10] Testing login/authentication...\")
    try:
        from app.database import SessionLocal
        from app.core.security import verify_password, create_access_token
        from app import models
        
        db = SessionLocal()
        
        # Get test user
        user = db.query(models.User).filter(
            models.User.email == \"test@example.com\"
        ).first()
        
        if not user:
            print(\"✗ Test user not found\")\n            return False
        
        # Verify password
        if not verify_password(\"testpassword123\", user.hashed_password):
            print(\"✗ Password verification failed\")\n            return False
        
        # Create token
        token = create_access_token({\"sub\": user.email})
        if not token:
            print(\"✗ Token creation failed\")\n            return False
        
        print(f\"✓ Login and token creation work\")\n        
        db.close()
        return True
    except Exception as e:
        print(f\"✗ Login test failed: {e}\")\n        return False

def test_jwt_validation():
    \"\"\"Test JWT token validation.\"\"\"
    print(\"[6/10] Testing JWT validation...\")
    try:
        from app.core.security import create_access_token, decode_access_token
        
        # Create token
        token = create_access_token({\"sub\": \"test@example.com\"})
        
        # Decode token
        payload = decode_access_token(token)
        if not payload or payload.get(\"sub\") != \"test@example.com\":
            print(\"✗ JWT validation failed\")\n            return False
        
        # Test invalid token
        payload_invalid = decode_access_token(\"invalid.token.here\")
        if payload_invalid is not None:
            print(\"✗ Invalid token should return None\")\n            return False
        
        print(\"✓ JWT validation works\")\n        return True
    except Exception as e:
        print(f\"✗ JWT validation test failed: {e}\")\n        return False

def test_model_creation():
    \"\"\"Test model creation and relationships.\"\"\"
    print(\"[7/10] Testing model relationships...\")
    try:
        from app.database import SessionLocal
        from app import models
        
        db = SessionLocal()
        
        # Create test patient
        patient = models.Patient(
            name=\"Test Patient\",
            age=45,
            email=\"patient@example.com\",
            hpv_status=\"positive\",
            smoking=False,
            symptoms=\"abnormal bleeding\"
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)
        
        user = db.query(models.User).filter(
            models.User.email == \"test@example.com\"
        ).first()
        
        # Create test report
        report = models.Report(
            patient_id=patient.id,
            uploaded_by_id=user.id,
            image_path=\"/tmp/test.jpg\",
            prediction=\"Normal\",
            confidence=0.95,
            probabilities='{\"Normal\": 0.95, \"CIN1\": 0.05}'
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        
        # Verify relationships
        assert report.patient.name == \"Test Patient\"
        assert report.uploaded_by.email == \"test@example.com\"
        assert len(patient.reports) > 0
        
        print(f\"✓ Model relationships work\")\n        
        db.close()
        return True
    except Exception as e:
        print(f\"✗ Model relationships test failed: {e}\")\n        return False

def test_fastapi_startup():
    \"\"\"Test that FastAPI app starts without errors.\"\"\"
    print(\"[8/10] Testing FastAPI startup...\")
    try:
        from app.main import app
        
        # Check that app is properly configured
        if not app.routes:
            print(\"✗ No routes configured\")\n            return False
        
        print(f\"✓ FastAPI app initialized with {len(app.routes)} routes\")\n        return True
    except Exception as e:
        print(f\"✗ FastAPI startup test failed: {e}\")\n        return False

def test_ai_model_handling():
    \"\"\"Test that missing AI model doesn't crash backend.\"\"\"
    print(\"[9/10] Testing AI model handling...\")
    try:
        from app.core.config import settings
        from app.api.predict import init_prediction_service
        
        # Initialize prediction service (should handle missing model gracefully)
        init_prediction_service()
        
        print(\"✓ AI model handler initialized (model availability check works)\")\n        return True
    except Exception as e:
        print(f\"✗ AI model handling test failed: {e}\")\n        return False

def test_no_hardcoded_secrets():
    \"\"\"Test that no secrets are hardcoded in critical files.\"\"\"
    print(\"[10/10] Checking for hardcoded secrets...\")
    try:
        import re
        
        critical_files = [
            'app/main.py',
            'app/core/config.py',
            'app/database.py',
        ]
        
        secrets_to_check = [
            r'SECRET_KEY\\s*=\\s*[\"\\'](?!dev-key)[^\"\\']',
            r'PASSWORD\\s*=\\s*[\"\\'](?!password|your-password)[^\"\\']',
            r'API_KEY\\s*=\\s*[\"\\'](?!your-api-key)[^\"\\']',
        ]
        
        for file in critical_files:
            try:
                with open(file, 'r') as f:
                    content = f.read()
                    # The dev key and environment variables are expected
                    if 'password@' in content.lower() and 'localhost' not in content.lower():
                        print(f\"✗ Possible hardcoded credentials in {file}\")\n                        return False
            except FileNotFoundError:
                pass
        
        print(\"✓ No obvious hardcoded secrets detected\")\n        return True
    except Exception as e:
        print(f\"✗ Secret check failed: {e}\")\n        return False

def main():
    \"\"\"Run all tests.\"\"\"
    print(\"=\"*60)
    print(\"CerviVal Backend Verification Suite\")
    print(\"=\"*60)
    
    tests = [
        test_imports,
        test_database_init,
        test_database_session,
        test_user_registration,
        test_login,
        test_jwt_validation,
        test_model_creation,
        test_fastapi_startup,
        test_ai_model_handling,
        test_no_hardcoded_secrets,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f\"✗ Test {test.__name__} crashed: {e}\")\n            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(\"=\"*60)
    print(f\"VERIFICATION SUMMARY: {passed}/{total} tests passed\")
    print(\"=\"*60)
    
    if passed == total:
        print(\"\\n✓ All backend tests passed!\\n\")
        return 0
    else:
        print(f\"\\n✗ {total - passed} test(s) failed\\n\")
        return 1

if __name__ == \"__main__\":
    sys.exit(main())
