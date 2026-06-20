import sys
import os
import json
import time
import httpx

# Ensure backend path is in Python path for any imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://127.0.0.1:8000"

def test_workflow():
    print("=== STARTING API INTEGRATION TESTING ===")
    
    # 1. Start Client Session
    with httpx.Client(base_url=BASE_URL, timeout=15.0) as client:
        # Generate dynamic test credentials to avoid collision
        timestamp = int(time.time())
        username_user = f"patient_{timestamp}"
        username_admin = f"admin_{timestamp}"
        email_user = f"patient_{timestamp}@example.com"
        email_admin = f"admin_{timestamp}@example.com"
        password = "testpassword123"

        # --- A. PATIENT ACCOUNT SETUP ---
        print("\n[Auth Test] Registering a new Patient...")
        reg_payload = {
            "username": username_user,
            "email": email_user,
            "password": password,
            "role": "user"
        }
        res_reg = client.post("/api/auth/register", json=reg_payload)
        assert res_reg.status_code == 200, f"Registration failed: {res_reg.text}"
        user_data = res_reg.json()
        print(f"Registered User: {user_data['username']} (ID: {user_data['id']})")

        # --- B. PATIENT LOGIN ---
        print("\n[Auth Test] Logging in Patient...")
        login_payload = {
            "username": username_user,
            "email": email_user,
            "password": password,
            "role": "user"
        }
        res_login = client.post("/api/auth/login", json=login_payload)
        assert res_login.status_code == 200, f"Login failed: {res_login.text}"
        token_data = res_login.json()
        token = token_data["access_token"]
        print("Logged in. Received Token.")
        
        # Authenticate client headers
        client.headers.update({"Authorization": f"Bearer {token}"})

        # --- C. PROFILE TEST ---
        print("\n[Profile Test] Reading profile details...")
        res_prof_get = client.get("/api/profile")
        assert res_prof_get.status_code == 200, f"Get profile failed: {res_prof_get.text}"
        print(f"Current Profile: {res_prof_get.json()}")

        print("\n[Profile Test] Updating profile fields...")
        prof_update = {
            "full_name": "Test Patient",
            "age": 45,
            "gender": "female",
            "height": 165.0,
            "weight": 78.5,
            "phone": "+1 555-123-4567"
        }
        res_prof_put = client.put("/api/profile", json=prof_update)
        assert res_prof_put.status_code == 200, f"Put profile failed: {res_prof_put.text}"
        print(f"Updated Profile: {res_prof_put.json()}")

        # --- D. ML PREDICTION TEST ---
        print("\n[ML & AI Test] Submitting patient vitals for risk assessment...")
        # Classic diabetic characteristics input
        vitals_payload = {
            "pregnancies": 3,
            "glucose": 156,
            "blood_pressure": 82,
            "skin_thickness": 35,
            "insulin": 140,
            "bmi": 32.4,
            "pedigree_function": 0.521,
            "age": 45
        }
        res_predict = client.post("/api/predictions/predict", json=vitals_payload)
        assert res_predict.status_code == 200, f"Prediction call failed: {res_predict.text}"
        pred_result = res_predict.json()
        print(f"Diabetes Risk Probability: {pred_result['result_probability']*100:.1f}%")
        print(f"Risk Outcome Class: {pred_result['result_class']} ({'HIGH RISK' if pred_result['result_class'] == 1 else 'LOW RISK'})")
        safe_suggestion = pred_result['gemini_suggestion'][:150].encode('ascii', errors='replace').decode('ascii')
        print(f"AI Wellness Advice preview:\n{safe_suggestion}...")

        # --- E. HISTORY LOG TEST ---
        print("\n[History Test] Fetching prediction log history...")
        res_history = client.get("/api/predictions/history")
        assert res_history.status_code == 200, f"History fetch failed: {res_history.text}"
        history_list = res_history.json()
        print(f"Log Count: {len(history_list)} items found.")
        assert len(history_list) >= 1, "Log history should not be empty after prediction submit."

        # --- F. FEEDBACK AND RATING TEST ---
        print("\n[Feedback Test] Submitting user rating feedback...")
        fb_payload = {
            "rating": 5,
            "comment": "Outstanding diagnostic precision and recommendations!"
        }
        res_fb = client.post("/api/feedbacks", json=fb_payload)
        assert res_fb.status_code == 200, f"Feedback submission failed: {res_fb.text}"
        print(f"Submitted Rating Feedback: {res_fb.json()}")

        # --- G. ADMIN INTERFACES ACCESS SECURITY CHECK ---
        print("\n[Security Test] Verifying Patient user cannot access admin stats...")
        res_admin_stats = client.get("/api/admin/users")
        # Should yield 403 Forbidden since the client token belongs to a Patient
        assert res_admin_stats.status_code == 403, f"Expected 403 Forbidden, got: {res_admin_stats.status_code}"
        print("Security Guard active: Non-admin user access denied.")

        # --- H. ADMIN ACCOUNT SETUP & ANALYTICS CHECK ---
        print("\n[Admin Test] Registering a new Admin user...")
        reg_admin_payload = {
            "username": username_admin,
            "email": email_admin,
            "password": password,
            "role": "admin"
        }
        # Clear headers authorization so we register a new admin
        client.headers.pop("Authorization")
        res_admin_reg = client.post("/api/auth/register", json=reg_admin_payload)
        assert res_admin_reg.status_code == 200, f"Admin registration failed: {res_admin_reg.text}"
        print(f"Admin Account Registered: {username_admin}")

        print("\n[Admin Test] Logging in Admin user...")
        res_admin_login = client.post("/api/auth/login", json=reg_admin_payload)
        assert res_admin_login.status_code == 200, f"Admin login failed: {res_admin_login.text}"
        admin_token = res_admin_login.json()["access_token"]
        client.headers.update({"Authorization": f"Bearer {admin_token}"})
        print("Logged in as Admin.")

        print("\n[Admin Test] Reading aggregated system statistics (Power BI data)...")
        res_stats = client.get("/api/admin/stats")
        assert res_stats.status_code == 200, f"Get stats failed: {res_stats.text}"
        stats = res_stats.json()
        print(f"System Stats: Total Users: {stats['total_users']}, Assessments: {stats['total_predictions']}, Avg Rating: {stats['avg_rating']}")

        print("\n[Admin Test] Retrieving all registered users records...")
        res_all_users = client.get("/api/admin/users")
        assert res_all_users.status_code == 200, f"Get users failed: {res_all_users.text}"
        all_users = res_all_users.json()
        print(f"Found {len(all_users)} total users in db.")

        print("\n[Admin Test] Reading system notification logs...")
        res_notif = client.get("/api/admin/notifications")
        assert res_notif.status_code == 200, f"Get notifications failed: {res_notif.text}"
        notif_logs = res_notif.json()
        print(f"Found {len(notif_logs)} notification logs in db.")

        print("\n[Admin Test] Reading patient feedbacks report...")
        res_all_fb = client.get("/api/feedbacks")
        assert res_all_fb.status_code == 200, f"Get feedbacks failed: {res_all_fb.text}"
        all_fb = res_all_fb.json()
        print(f"Found {len(all_fb)} patient feedbacks.")

    print("\n=== ALL API INTEGRATION TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    test_workflow()
