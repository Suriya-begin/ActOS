import asyncio
import os
import sys
from dotenv import load_dotenv

# Set Python path so we can import app modules
sys.path.append("e:/ActOS/backend")
load_dotenv("e:/ActOS/backend/.env")

async def test_database():
    print("[1/4] Testing database connection...")
    from app.core.database import init_db, get_db
    try:
        await init_db()
        print(" -> Database initialized successfully!")
        return True
    except Exception as e:
        print(f" -> Database connection failed: {e}")
        return False

async def test_nlu():
    print("[2/4] Testing NLU (Intent Extractor)...")
    from app.core.intent_extractor import intent_extractor
    try:
        command = "Chrome open panni Amazon la headphones search pannu"
        intent = await intent_extractor.extract(command)
        print(" -> Extracted intent successfully!")
        print(f" -> Command: '{command}'")
        print(f" -> Extracted App: '{intent.app}' | Action: '{intent.action}'")
        assert intent.app in ["amazon", "chrome"]
        assert intent.action in ["search_product", "search", "open_browser"]
        return True
    except Exception as e:
        print(f" -> NLU extraction failed: {e}")
        return False

async def test_orchestrator():
    print("[3/4] Testing Agent Orchestrator (Playwright browser execution)...")
    from app.core.intent_extractor import ExtractedIntent
    from app.core.orchestrator import orchestrator
    try:
        intent = ExtractedIntent(
            app="amazon",
            action="search_product",
            target="amazon",
            content="headphones",
            language="tanglish",
            needs_auth=False,
            confidence=0.95,
            raw_command="Chrome open panni Amazon la headphones search pannu",
            clarification_needed=False,
            clarification_question=None
        )
        result = await orchestrator.process_command(
            intent=intent,
            user_id="test_user_id",
            session_id="test_session_123"
        )
        print(" -> Orchestrated successfully!")
        print(f" -> Voice Response: {result.get('voice_response')}")
        print(f" -> Execution Result: {result.get('result')}")
        assert result.get("error") == ""
        assert "headphones" in result.get("voice_response").lower() or "amazon" in result.get("voice_response").lower()
        return True
    except Exception as e:
        print(f" -> Agent Orchestration failed: {e}")
        return False

async def test_auth_endpoints():
    print("[4/4] Testing Auth routes via FastAPI test client...")
    from fastapi.testclient import TestClient
    from app.main import app
    import uuid

    try:
        client = TestClient(app)
        
        # Test health check
        res = client.get("/health")
        assert res.status_code == 200
        print(" -> /health endpoint verified!")

        # Test user registration with random email
        random_email = f"test_{uuid.uuid4().hex[:6]}@example.com"
        reg_payload = {
            "email": random_email,
            "password": "test_secure_password_123",
            "first_name": "Test",
            "last_name": "User"
        }
        res = client.post("/api/auth/register", json=reg_payload)
        assert res.status_code == 201
        data = res.json()
        assert "access_token" in data
        assert data["user"]["email"] == random_email
        print(" -> /api/auth/register endpoint verified!")

        # Test login
        login_payload = {
            "email": random_email,
            "password": "test_secure_password_123"
        }
        res = client.post("/api/auth/login", json=login_payload)
        assert res.status_code == 200
        data = res.json()
        token = data["access_token"]
        assert token is not None
        print(" -> /api/auth/login endpoint verified!")

        # Test /me
        res = client.get(f"/api/auth/me?token={token}")
        assert res.status_code == 200
        me_data = res.json()
        assert me_data["valid"] is True
        assert me_data["user"]["email"] == random_email
        print(" -> /api/auth/me endpoint verified!")

        return True
    except Exception as e:
        print(f" -> Auth API endpoint tests failed: {e}")
        return False

async def main():
    print("==================================================")
    print("ACTOS VOICE OS SYSTEM VERIFICATION")
    print("==================================================")
    
    db_ok = await test_database()
    nlu_ok = await test_nlu()
    orch_ok = await test_orchestrator()
    auth_ok = await test_auth_endpoints()
    
    print("==================================================")
    print("VERIFICATION RESULTS SUMMARY:")
    print(f" -> Database Connection: {'PASSED' if db_ok else 'FAILED'}")
    print(f" -> NLU Intent Extractor: {'PASSED' if nlu_ok else 'FAILED'}")
    print(f" -> Orchestrator & Agents: {'PASSED' if orch_ok else 'FAILED'}")
    print(f" -> Auth & Core Endpoints: {'PASSED' if auth_ok else 'FAILED'}")
    print("==================================================")
    
    if db_ok and nlu_ok and orch_ok and auth_ok:
        print("SUCCESS: All tests passed! The system is highly reliable.")
        sys.exit(0)
    else:
        print("ERROR: One or more components failed verification.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
