import spacy

# Load Spacy NLP model
nlp = spacy.load("en_core_web_sm")

# Predefined templates for common denial reasons
DENIAL_TEMPLATES = {
    "CO-50": "Medical Neccesity",
    "CO-45": "Coding Error",
}

# Keywords to identify relevant sentences
KEYWORDS = {"pain", "discomfort", "experienced", "partial"}

def extract_denial_details(denial_text, patient_name):
    """
    Extract claim denial details using regex and NLP.
    """
    claim_pattern = r"(?m)^\d+\.\s+Claim Number: (?P<ClaimNumber>\w+)\n\s+Patient Name: (?P<PatientName>.+)\n\s+Date of Service: (?P<DateOfService>.+)\n\s+Procedure Code: (?P<ProcedureCode>.+)\n\s+Billed Amount: (?P<BilledAmount>.+)\n\s+Allowed Amount: (?P<AllowedAmount>.+)\n\s+Patient Responsibility: (?P<PatientResponsibility>.+)\n\s+Paid Amount: (?P<PaidAmount>.+)\n\s+Adjustment: (?P<Adjustment>.+)\n\s+CARC: (?P<CARC>\w+-\w+)(?:\n\s+RARC: (?P<RARC>.+))?"

    # Find all matches
    target_claim = None
    claims = [match.groupdict() for match in re.finditer(claim_pattern, denial_text)]
    for claim in claims:
        print(claim)
        if claim["PatientName"] == patient_name:
            target_claim = claim
            break
    return target_claim

def extract_sentences_from_json(data, keywords):
    """
    Recursively traverse the JSON object, extract sentences, and filter them based on keywords.
    """
    justification = []

    if isinstance(data, dict):
        for key, value in data.items():
            justification.extend(extract_sentences_from_json(value, keywords))
    elif isinstance(data, list):
        for item in data:
            justification.extend(extract_sentences_from_json(item, keywords))
    elif isinstance(data, str):
        # Use Spacy to split text into sentences
        doc = nlp(data)
        for sent in doc.sents:
            if any(keyword in sent.text.lower() for keyword in keywords):
                justification.append(sent.text.strip())
    
    return justification

def generate_appeal(claim, clinical_notes):
    """
    Generate an appeal JSON using denial details and clinical notes.
    """
    # Extract justification sentences from the entire medical note
    justification_sentences = extract_sentences_from_json(clinical_notes, KEYWORDS)
    medical_justification = " ".join(justification_sentences)
    
    appeal = {
        "Patient": claim["PatientName"],
        "Claim Number": claim["ClaimNumber"],
        "Date of Service": claim["DateOfService"],
        "Procedure Code": claim["ProcedureCode"],
        "Reason for Appeal": f'{DENIAL_TEMPLATES.get(claim["CARC"], "No predefined reason available.")} {": " + claim["RARC"]}',
        "Justification": medical_justification,
        "Request": "Please reconsider the claim and approve coverage as it was medically necessary."
    }
    return appeal

# Example Denial Text
denial_text = """
******ELECTRONIC REMITTANCE ADVICE******

Payer: Medicare
Payment Amount: $2,443.01
Payment ID: INV-207B-H&1
Vendor ID: 173829
Vendor Name: Sample Medical Practice

Payment Details:
- Payment Method: Electronic Funds Transfer (EFT)
- Payment Date: 2024-12-20
- Account Number: XXXX1234

Claim Details:

1. Claim Number: CLM123456
   Patient Name: John Doe
   Date of Service: 2024-12-01
   Procedure Code: 99213 (Office visit, established patient)
   Billed Amount: $150.00
   Allowed Amount: $85.00
   Patient Responsibility: $20.00 (Copay)
   Paid Amount: $65.00
   Adjustment: -$65.00
   CARC: CO-45 (Charge exceeds fee schedule/maximum allowable)
   RARC: N30 (Patient ineligible for this service)

2. Claim Number: CLM789012
   Patient Name: Jane Smith
   Date of Service: 2024-12-05
   Procedure Code: 85025 (Complete blood count)
   Billed Amount: $50.00
   Allowed Amount: $30.00
   Patient Responsibility: $0.00
   Paid Amount: $30.00
   Adjustment: -$20.00
   CARC: CO-45 (Charge exceeds fee schedule/maximum allowable)

3. Claim Number: CLM345678
   Patient Name: Robert Johnson
   Date of Service: 2024-12-10
   Procedure Code: 73030 (X-ray, shoulder, 2 views)
   Billed Amount: $75.00
   Allowed Amount: $0.00
   Patient Responsibility: $0.00
   Paid Amount: $0.00
   Adjustment: -$75.00
   CARC: CO-50 (Not deemed a medical necessity)
   RARC: N10 (Payment based on the findings of a review organization)

Total Billed Amount: $275.00
Total Allowed Amount: $115.00
Total Patient Responsibility: $20.00
Total Paid Amount: $95.00
Total Adjustments: -$160.00

If you have any questions regarding this remittance advice, please contact our Provider Services department at 1-800-555-1234 or email providerservices@medicare.gov.

Thank you,
Medicare Claims Processing Department
"""

# Example Clinical Notes JSON
clinical_note = {
    "Patient Name": "Robert Johnson",
    "DOB": "07/15/1960",
    "Date of Service": "2024-12-10",
    "Provider": "Dr. Jane Provider, MD",
    "Chief Complaint (CC)": "Left shoulder pain and limited range of motion.",
    "History of Present Illness (HPI)": (
        "Mr. Robert Johnson is a 64-year-old male presenting with a 3-week history of "
        "progressive left shoulder pain. He reports that the discomfort began after slipping "
        "on ice and catching himself with his left arm extended. Since then, he has experienced "
        "intermittent, dull to sharp pain localized to the anterior and lateral aspects of the "
        "left shoulder. The pain is worse with overhead activities, lying on the affected side, "
        "and during attempts to lift moderately heavy objects. He denies numbness, tingling, or "
        "referred pain down the arm. Over-the-counter NSAIDs have provided only partial relief. "
        "There is no history of recent fevers, unexplained weight loss, or prior shoulder surgeries. "
        "He has no known allergies and no recent changes in his daily activities, aside from avoiding "
        "certain movements due to discomfort."
    ),
    "Review of Systems (ROS)": {
        "Musculoskeletal": "Reports left shoulder pain as described in HPI; denies joint swelling or redness in other joints.",
        "Neurological": "Denies numbness, tingling, or weakness distally in the left arm.",
        "General": "Denies fever, chills, weight loss.",
        "Cardiovascular and Respiratory": "No chest pain, palpitations, shortness of breath, or wheezing.",
        "Other Systems": "All other systems reviewed and negative unless noted above."
    },
    "Vital Signs": {
        "Blood Pressure": "124/76 mmHg",
        "Heart Rate": "76 bpm",
        "Respiratory Rate": "16/min",
        "Temperature": "98.5°F (36.9°C)",
        "Oxygen Saturation": "98% on room air"
    },
    "Physical Examination": {
        "General": "Appears alert and in no acute distress, though guards the left shoulder somewhat when moving.",
        "Left Shoulder": {
            "Inspection": "No visible swelling, redness, or deformity.",
            "Palpation": "Tenderness over the anterior aspect of the left shoulder and mildly over the greater tuberosity region.",
            "Range of Motion": (
                "Forward flexion and abduction limited by about 20% compared to the right shoulder due to pain. "
                "Pain is elicited at approximately 90° of abduction and with internal rotation maneuvers."
            ),
            "Special Tests": (
                "Positive painful arc test at around 80-100° of abduction. Mild discomfort with Neer’s and Hawkins’ "
                "tests suggest possible impingement. No gross instability but difficulty maintaining full abduction "
                "against resistance suggests possible rotator cuff involvement."
            )
        },
        "Cardiovascular": "Regular rate and rhythm, no murmurs.",
        "Respiratory": "Clear to auscultation bilaterally, no wheezes, rales, or rhonchi."
    },
    "Results (Prior to Imaging)": (
        "No lab work has been performed at this visit. No prior imaging studies of the shoulder available "
        "for comparison."
    ),
    "Orders": [
        "Order left shoulder X-ray (AP and scapular Y views) to assess bony anatomy and look for any structural abnormalities.",
        "Prescribe a short course of NSAIDs for pain control (as tolerated).",
        "Recommend physical therapy consultation focusing on rotator cuff strengthening, scapular stabilization exercises, and stretching."
    ],
    "Assessment and Plan": {
        "Assessment": (
            "Likely rotator cuff tendinopathy/subacromial impingement secondary to a fall, with ongoing pain "
            "and limited range of motion. Need to rule out subtle fracture or bony abnormalities."
        ),
        "Plan": [
            "Obtain left shoulder X-ray (2 views) to evaluate osseous structures and exclude fractures or significant degenerative changes.",
            "Continue conservative management with NSAIDs and PT referral.",
            "Follow-up in 2-3 weeks or sooner if symptoms worsen. Consider MRI if X-ray is unremarkable and symptoms persist."
        ]
    }
}

claim = extract_denial_details(denial_text, clinical_note['Patient Name'])
if claim:
    # Generate the Appeal JSON
    appeal_json = generate_appeal(claim, clinical_note)
    print(appeal_json)
else:
  print("No matching claim found.")
