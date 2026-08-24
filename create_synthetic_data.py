import json
import random
from datetime import date, timedelta


# ============================================================
# 1. REPRODUCIBILITY
# ============================================================

SEED = int(
    __import__("os").environ.get(
        "CLAIM_SEED",
        "42"
    )
)
rng = random.Random(SEED)

# ============================================================
# 2. SYNTHETIC DATA POOLS
# ============================================================

FIRST_NAMES = [
    "Michael", "Sarah", "David", "Priya",
    "James", "Linda", "Carlos", "Emma"
]

LAST_NAMES = [
    "Thomas", "Nair", "Johnson", "Martinez",
    "Chen", "Williams", "Kumar", "Davis"
]

STREETS = [
    "Maple St", "Oak Ave", "Pine Rd",
    "Cedar Ln", "Elm Dr", "Birch Ct"
]

CITIES_STATES_ZIPS = [
    ("Springfield", "IL", "62704"),
    ("Kochi", "KL", "68201"),
    ("Austin", "TX", "73301"),
    ("Denver", "CO", "80202"),
]

INSURANCE_PLANS = [
    "BlueCross BlueShield PPO",
    "United Health Choice",
    "Aetna Open Access",
    "Cigna HMO",
]

ICD10_CODES = [
    "E11.9",
    "I10",
    "J45.909",
    "M54.5",
    "K21.9",
    "F41.1",
]

CPT_CODES = [
    "99213",
    "99214",
    "80053",
    "71046",
    "93000",
    "97110",
    "97140",
    "97530",
]

PLACE_OF_SERVICE_CODES = [
    "11",
    "21",
    "22",
    "23",
]


# ============================================================
# 3. HELPERS
# ============================================================

def random_name():
    first = rng.choice(FIRST_NAMES)
    last = rng.choice(LAST_NAMES)
    middle = rng.choice("ABCDEFGHJKLMNPRST")
    return f"{last}, {first} {middle}"


def random_address():
    city, state, zip_code = rng.choice(CITIES_STATES_ZIPS)

    return {
        "street": f"{rng.randint(100, 9999)} {rng.choice(STREETS)}",
        "city": city,
        "state": state,
        "zip": zip_code,
        "phone": (
            f"({rng.randint(200, 999)}) "
            f"{rng.randint(200, 999)}-"
            f"{rng.randint(1000, 9999)}"
        ),
    }


def random_date(start_date, end_date):
    days = (end_date - start_date).days
    return start_date + timedelta(days=rng.randint(0, days))


def format_date(d):
    return d.strftime("%d/%m/%Y")


def random_dob():
    start = date(1945, 1, 1)
    end = date(2005, 12, 31)
    return random_date(start, end)


def random_service_date():
    return random_date(
        date(2026, 1, 1),
        date(2026, 12, 31),
    )


def random_npi():
    return "".join(rng.choices("0123456789", k=10))


# ============================================================
# 4. PATIENT / INSURED
# ============================================================

patient_name = random_name()
patient_dob = random_dob()
patient_sex = rng.choice(["M", "F"])

relationship_to_insured = rng.choice(
    ["Self", "Spouse", "Child", "Other"]
)

if relationship_to_insured == "Self":
    insured_name = patient_name
    insured_dob = patient_dob
    insured_sex = patient_sex
else:
    insured_name = random_name()
    insured_dob = random_dob()
    insured_sex = rng.choice(["M", "F"])


# ============================================================
# 5. INSURANCE
# ============================================================

insurance_type = rng.choice([
    "MEDICARE",
    "MEDICAID",
    "TRICARE",
    "CHAMPVA",
    "GROUP HEALTH PLAN",
])

insured_id_number = f"INS{rng.randint(1000000, 9999999)}"

insurance_plan_name = rng.choice(INSURANCE_PLANS)

insurance_policy_group_number = (
    f"GRP{rng.randint(10000, 99999)}"
)


# ============================================================
# 6. ADDRESSES
# ============================================================

patient_address = random_address()
insured_address = (
    patient_address.copy()
    if relationship_to_insured == "Self"
    else random_address()
)

other_insured_name = (
    random_name()
    if rng.random() < 0.5
    else ""
)

other_insured_policy_group = (
    f"OTHGRP{rng.randint(10000, 99999)}"
    if other_insured_name
    else ""
)


# ============================================================
# 7. CONDITION FLAGS
# ============================================================

employment_related = rng.random() < 0.2
auto_accident = rng.random() < 0.1
other_accident = rng.random() < 0.1

auto_accident_state = (
    rng.choice(["IL", "TX", "CO", "KL"])
    if auto_accident
    else ""
)


# ============================================================
# 8. CLINICAL INFORMATION
# ============================================================

# Illness date must be after the patient's adulthood.
minimum_illness_date = patient_dob + timedelta(days=18 * 365)

current_illness_date = random_date(
    minimum_illness_date,
    date(2026, 8, 1),
)

referring_provider = (
    f"Dr. {rng.choice(FIRST_NAMES)} "
    f"{rng.choice(LAST_NAMES)}"
)

hospitalization_from = date(2026, 5, 10)
hospitalization_to = date(2026, 5, 12)

hospitalization_dates = {
    "from": format_date(hospitalization_from),
    "to": format_date(hospitalization_to),
}

additional_claim_info = "SYNTHETIC TRAINING CLAIM"


# ============================================================
# 9. DIAGNOSIS
# ============================================================

diagnosis_codes = rng.sample(
    ICD10_CODES,
    4,
)


# ============================================================
# 10. RESUBMISSION / AUTHORIZATION
# ============================================================

resubmission_code = "7"
original_ref_number = "SYN-0001500"
prior_authorization_number = (
    f"SYN-PA-{rng.randint(1000, 9999)}"
)


# ============================================================
# 11. SIX SERVICE LINES
# ============================================================

service_lines = []

for line_number in range(1, 7):

    service_lines.append({
        "line_number": line_number,
        "date_of_service": format_date(
            random_service_date()
        ),
        "place_of_service": rng.choice(
            PLACE_OF_SERVICE_CODES
        ),
        "procedure_code": rng.choice(CPT_CODES),
        "diagnosis_pointer": rng.choice(
            ["A", "B", "C", "D"]
        ),
        "charges": round(
            rng.uniform(50, 500),
            2
        ),
        "units": rng.randint(1, 3),
        "provider_npi": random_npi(),
    })


# ============================================================
# 12. BILLING
# ============================================================

total_charge = round(
    sum(line["charges"] for line in service_lines),
    2,
)

federal_tax_id = (
    f"{rng.randint(10, 99)}-"
    f"{rng.randint(1000000, 9999999)}"
)

patient_account_number = (
    f"SYN-{rng.randint(100000, 999999)}"
)

accept_assignment = True
amount_paid = 0.00


# ============================================================
# 13. FACILITY / PROVIDER
# ============================================================

signature_present = True

service_facility = random_address()
billing_provider = random_address()

service_facility_npi = random_npi()
billing_provider_npi = random_npi()


# ============================================================
# 14. OTHER PLAN
# ============================================================

another_health_benefit_plan = rng.random() < 0.3

other_health_plan_name = (
    rng.choice(INSURANCE_PLANS)
    if another_health_benefit_plan
    else ""
)


# ============================================================
# 15. FINAL CLAIM JSON
# ============================================================

claim = {
    "insurance_type": insurance_type,

    "insured_id_number": insured_id_number,

    "patient_name": patient_name,
    "patient_dob": format_date(patient_dob),
    "patient_sex": patient_sex,

    "insured_name": insured_name,
    "insured_dob": format_date(insured_dob),
    "insured_sex": insured_sex,

    "patient_address": patient_address,
    "relationship_to_insured": relationship_to_insured,
    "insured_address": insured_address,

    "other_insured_name": other_insured_name,
    "other_insured_policy_group": (
        other_insured_policy_group
    ),

    "employment_related": employment_related,
    "auto_accident": auto_accident,
    "auto_accident_state": auto_accident_state,
    "other_accident": other_accident,

    "insurance_plan_name": insurance_plan_name,
    "insurance_policy_group_number": (
        insurance_policy_group_number
    ),

    "another_health_benefit_plan": (
        another_health_benefit_plan
    ),
    "other_health_plan_name": other_health_plan_name,

    "current_illness_date": (
        format_date(current_illness_date)
    ),

    "referring_provider": referring_provider,

    "hospitalization_dates": hospitalization_dates,

    "additional_claim_info": additional_claim_info,

    "diagnosis_codes": diagnosis_codes,

    "resubmission_code": resubmission_code,
    "original_ref_number": original_ref_number,
    "prior_authorization_number": (
        prior_authorization_number
    ),

    "service_lines": service_lines,

    "federal_tax_id": federal_tax_id,
    "patient_account_number": (
        patient_account_number
    ),
    "accept_assignment": accept_assignment,

    "total_charge": total_charge,
    "amount_paid": amount_paid,

    "signature_present": signature_present,

    "service_facility": service_facility,
    "service_facility_npi": service_facility_npi,

    "billing_provider": billing_provider,
    "billing_provider_npi": billing_provider_npi,

    # Compatibility fields
    "procedure_codes": [
        line["procedure_code"]
        for line in service_lines
    ],

    "date_of_service": (
        service_lines[0]["date_of_service"]
    ),

    "billed_amount": total_charge,
}


# ============================================================
# 16. VALIDATION
# ============================================================

assert len(service_lines) == 6

assert len(diagnosis_codes) == 4

assert all(
    len(line["provider_npi"]) == 10
    for line in service_lines
)

assert len(service_facility_npi) == 10
assert len(billing_provider_npi) == 10

assert total_charge == round(
    sum(line["charges"] for line in service_lines),
    2,
)


# ============================================================
# 17. SAVE
# ============================================================

output_path = "data/processed/claim_001.json"

with open(output_path, "w", encoding="utf-8") as file:
    json.dump(
        claim,
        file,
        indent=4,
    )


print("Synthetic claim generated successfully.")
print(f"Saved to: {output_path}")
print(f"Patient: {patient_name}")
print(f"DOB: {claim['patient_dob']}")
print(f"Diagnosis codes: {diagnosis_codes}")
print(f"Service lines: {len(service_lines)}")
print(f"Total charge: ${total_charge:.2f}")