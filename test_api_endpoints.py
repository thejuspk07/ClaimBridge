"""
Automated Verification Suite for ClaimBridge FastAPI Backend & Endpoints.
"""
import requests
import json
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

def test_suite():
    print("==========================================")
    print("CLAIMBRIDGE BACKEND VERIFICATION SUITE")
    print("==========================================")

    # 1. Health Check
    print("\n1. Testing GET /api/health...")
    r = requests.get(f"{BASE_URL}/api/health")
    assert r.status_code == 200, f"Health check failed: {r.text}"
    print("   [PASS] Health Status:", r.json())

    # 2. Demo Load
    print("\n2. Testing POST /api/demo/load...")
    r = requests.post(f"{BASE_URL}/api/demo/load")
    assert r.status_code == 200, f"Demo load failed: {r.text}"
    demo_claims = r.json()
    print(f"   [PASS] Demo claims loaded: {len(demo_claims)} claims")

    # 3. List Claims
    print("\n3. Testing GET /api/claims...")
    r = requests.get(f"{BASE_URL}/api/claims")
    assert r.status_code == 200, f"List claims failed: {r.text}"
    claims = r.json()
    print(f"   [PASS] Listed claims count: {len(claims)}")
    assert len(claims) >= 10, "Expected at least 10 claims"

    # 4. Detail Claim 001
    print("\n4. Testing GET /api/claims/claim_001...")
    r = requests.get(f"{BASE_URL}/api/claims/claim_001")
    assert r.status_code == 200, f"Get detail failed: {r.text}"
    claim1 = r.json()
    print(f"   [PASS] Patient Name: {claim1['patient']['name']}")
    print(f"   [PASS] Insured ID  : {claim1['insurance']['insured_id']}")
    print(f"   [PASS] Total Charge: ${claim1['total_charge']:.2f}")
    print(f"   [PASS] Validation  : {claim1['validation']['status']} (Errors: {claim1['validation']['error_count']}, Warnings: {claim1['validation']['warning_count']})")
    assert claim1['patient']['name'] == "Nair, David J", "Patient name mismatch on claim_001"
    assert claim1['insurance']['insured_id'] == "INS7539906", "Insured ID mismatch on claim_001"

    # 5. Approve Claim
    print("\n5. Testing POST /api/claims/claim_001/approve...")
    r = requests.post(f"{BASE_URL}/api/claims/claim_001/approve")
    assert r.status_code == 200, f"Approve failed: {r.text}"
    appr_claim = r.json()
    print(f"   [PASS] Status after approval: {appr_claim['status']}")
    assert appr_claim['status'] == "approved", "Status not approved"

    # 6. Manual Correction / Review
    print("\n6. Testing POST /api/claims/claim_001/review (audit trail)...")
    rev_payload = {
        "action": "review",
        "reviewer": "Dr. Verification",
        "notes": "Verified patient ID and confirmed policy group",
        "corrections": {
            "patient.address.city": "Springfield"
        }
    }
    r = requests.post(f"{BASE_URL}/api/claims/claim_001/review", json=rev_payload)
    assert r.status_code == 200, f"Review failed: {r.text}"
    rev_claim = r.json()
    print(f"   [PASS] Updated City: {rev_claim['patient']['address']['city']}")
    print(f"   [PASS] Audit Corrections logged: {len(rev_claim['manual_corrections'])}")
    assert rev_claim['patient']['address']['city'] == "Springfield"
    assert len(rev_claim['manual_corrections']) > 0

    # 7. Export JSON
    print("\n7. Testing GET /api/claims/claim_001/export...")
    r = requests.get(f"{BASE_URL}/api/claims/claim_001/export")
    assert r.status_code == 200, f"Export JSON failed: {r.text}"
    exported_data = r.json()
    assert exported_data['claim_id'] == "claim_001"
    print("   [PASS] Exported valid JSON for claim_001")

    # 8. Export CSV
    print("\n8. Testing GET /api/claims/export/csv...")
    r = requests.get(f"{BASE_URL}/api/claims/export/csv")
    assert r.status_code == 200, f"Export CSV failed: {r.text}"
    csv_text = r.text
    print(f"   [PASS] Exported CSV size: {len(csv_text)} bytes")
    assert "Claim ID,Filename,Uploaded At" in csv_text

    # 9. Test Live Upload / Real Pipeline Processing
    print("\n9. Testing POST /api/claims/process (LIVE PDF Upload -> Render -> OCR -> Extract -> Validate)...")
    test_pdf = Path("data/dataset/pdfs/claim_001.pdf")
    with open(test_pdf, "rb") as f:
        files = {"file": (test_pdf.name, f, "application/pdf")}
        r = requests.post(f"{BASE_URL}/api/claims/process", files=files)
    assert r.status_code == 200, f"Live upload failed: {r.text}"
    live_result = r.json()
    print(f"   [PASS] Live Processed Claim ID : {live_result['claim_id']}")
    print(f"   [PASS] Extracted Patient Name  : {live_result['patient']['name']}")
    print(f"   [PASS] Extracted DOB           : {live_result['patient']['dob']}")
    print(f"   [PASS] Extracted Insured ID    : {live_result['insurance']['insured_id']}")
    print(f"   [PASS] Extracted Total Charge  : ${live_result['total_charge']:.2f}")
    print(f"   [PASS] Confidence Score        : {live_result['confidence_score']}%")
    print(f"   [PASS] Image URL               : {live_result['image_url']}")
    print(f"   [PASS] Processing Time         : {live_result.get('processing_time_ms')} ms")
    assert live_result['patient']['name'] == "Nair, David J"
    assert live_result['insurance']['insured_id'] == "INS7539906"
    assert live_result['total_charge'] == 1632.23

    print("\n==========================================")
    print("ALL VERIFICATION SUITE TESTS PASSED (100%)")
    print("==========================================")

if __name__ == "__main__":
    test_suite()
