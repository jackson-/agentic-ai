import spacy
import re

# Load Spacy NLP model
nlp = spacy.load("en_core_web_sm")

# Predefined templates for common denial reasons
DENIAL_TEMPLATES = {
    "CO-50": "Medical Neccesity",
    "CO-45": "Coding Error",
    "N10": "Payment Issue",
    "N30": "Coverage Issue"
}

# Keywords to identify relevant and non-relevant sentences
KEYWORDS = {"pain", "discomfort", "experienced", "partial", "blurry", "fatigued", "lightheaded"}
NON_KEYWORDS = {"no", "not"}

def contains_word(word, text):
    return re.search(rf'\b{re.escape(word)}\b', text)

def extract_denial_details(denial_text, patient_name):
    """
    Extract claim denial details using regex and NLP.
    """
    claim_pattern = (
        r"Claim Number:\s*(?P<ClaimNumber>.+)\n\s*"
        r"Patient Name:\s*(?P<PatientName>.+)\n\s*"
        r"Date of Service:\s*(?P<DateOfService>.+)\n\s*"
        r"Procedure Code:\s*(?P<ProcedureCode>.+)\n\s*"
        r"Billed Amount:\s*(?P<BilledAmount>.+)\n\s*"
        r"Allowed Amount:\s*(?P<AllowedAmount>.+)\n\s*"
        r"Patient Responsibility:\s*(?P<PatientResponsibility>.+)\n\s*"
        r"Paid Amount:\s*(?P<PaidAmount>.+)\n\s*"
        r"Adjustment:\s*(?P<Adjustment>.+)\n\s*"
        r"CARC:\s*(?P<CARC>CO-\d+).+\n?\s*"
        r"(RARC:\s*(?P<RARC>N\d+))?"
    )
    # Find all matches
    target_claim = None
    claims = [match.groupdict() for match in re.finditer(claim_pattern, denial_text)]
    print(claims)
    for claim in claims:
        if claim["PatientName"] == patient_name:
            target_claim = claim
            break
    return target_claim

def extract_sentences_from_json(data, keywords, non_keywords):
    """
    Recursively traverse the JSON object, extract sentences, and filter them based on keywords.
    """
    justification = []

    if isinstance(data, dict):
        for key, value in data.items():
            justification.extend(extract_sentences_from_json(value, keywords, non_keywords))
    elif isinstance(data, list):
        for item in data:
            justification.extend(extract_sentences_from_json(item, keywords, non_keywords))
    elif isinstance(data, str):
        # Use Spacy to split text into sentences
        doc = nlp(data)
        for sent in doc.sents:
            if any(keyword in sent.text.lower() for keyword in keywords) and not any(contains_word(non_keyword, sent.text.lower()) for non_keyword in NON_KEYWORDS):
                justification.append(sent.text.strip())

    return justification

def generate_appeal(claim, clinical_notes):
    """
    Generate an appeal JSON using denial details and clinical notes.
    """
    # Extract justification sentences from the entire medical note
    justification_sentences = extract_sentences_from_json(clinical_notes, KEYWORDS, NON_KEYWORDS)
    medical_justification = " ".join(justification_sentences)

    appeal = {
        "Patient": claim["PatientName"],
        "Claim Number": claim["ClaimNumber"],
        "Date of Service": claim["DateOfService"],
        "Procedure Code": claim["ProcedureCode"],
        "Reason for Appeal": f'{DENIAL_TEMPLATES.get(claim["CARC"], "No predefined reason available.")}{": " + DENIAL_TEMPLATES.get(claim["RARC"]) if claim["RARC"] else ""}',
        "Justification": medical_justification,
        "Request": "Please reconsider the claim and approve coverage as it was medically necessary."
    }
    return appeal

# Example Denial Text
denial_text = """
******ELECTRONIC REMITTANCE ADVICE******

Payer: Medicare
Payment Amount: $0.00
Payment ID: INV-412X-KW3
Vendor ID: 173829
Vendor Name: Sample Medical Practice

Payment Details:
- Payment Method: Electronic Funds Transfer (EFT)
- Payment Date: 2024-12-20
- Account Number: XXXX1234

Claim Details:

Claim Number: CLM567890
Patient Name: Carmen Lopez
Date of Service: 2024-12-15
Procedure Code: 80048 (Basic metabolic panel)
Billed Amount: $55.00
Allowed Amount: $0.00
Patient Responsibility: $0.00
Paid Amount: $0.00
Adjustment: -$55.00
CARC: CO-50 (Not deemed a medical necessity)
RARC: N10 (Payment based on the findings of a review organization)

Total Billed Amount: $55.00
Total Allowed Amount: $0.00
Total Patient Responsibility: $0.00
Total Paid Amount: $0.00
Total Adjustments: -$55.00

If you have any questions regarding this remittance advice, please contact our Provider Services department at 1-800-555-1234 or email providerservices@medicare.gov.

Thank you,
Medicare Claims Processing Department
"""

# Example Clinical Notes JSON
clinical_note = {
  "Patient Name": "Carmen Lopez",
  "DOB": "1975-11-02",
  "Date of Service": "2024-12-15",
  "Provider": "Dr. Daniel Rivera, MD",
  "Chief Complaint (CC)": "Decreased urine output and general malaise.",
  "History of Present Illness (HPI)": "Ms. Carmen Lopez is a 49-year-old female presenting with 3 days of reduced urine output, mild diffuse fatigue, and intermittent nausea. She reports having been recently treated for a urinary tract infection with antibiotics about 2 weeks ago. Since then, she has noticed a gradual decrease in urine volume. She denies flank pain, severe abdominal pain, or changes in fluid intake. She also denies recent fevers or chills. No significant changes in diet or medications, other than the recent antibiotic course. She has a history of hypertension, controlled on a low-dose ACE inhibitor, and no known chronic kidney disease prior to this episode.",
  "Review of Systems (ROS)": {
    "General": "Fatigue, mild malaise.",
    "Genitourinary": "Markedly decreased urine output over the past 72 hours. No gross hematuria reported.",
    "Gastrointestinal": "Intermittent nausea, no vomiting, stable appetite.",
    "Cardiovascular": "No chest pain, palpitations, or lower extremity edema.",
    "Neurological": "No headaches, confusion, or changes in mental status.",
    "Musculoskeletal": "No new joint pains or swelling.",
    "Other Systems": "All other systems negative unless noted."
  },
  "Vital Signs": {
    "Blood Pressure": "142/88 mmHg",
    "Heart Rate": "78 bpm",
    "Respiratory Rate": "18/min",
    "Temperature": "98.2°F (36.8°C)",
    "Oxygen Saturation": "98% on room air"
  },
  "Physical Examination": {
    "General": "Appears tired but not in acute distress.",
    "Cardiovascular": "Regular rate and rhythm, no murmurs. Peripheral pulses intact.",
    "Respiratory": "Clear to auscultation bilaterally, no wheezes, rales, or rhonchi."
  },
  "Results": "No current labs available at the time of evaluation. No imaging results. Past medical history includes hypertension but no known renal issues.",
  "Orders": [
    "Order serum creatinine, BUN, electrolytes, and estimated GFR to assess kidney function.",
    "Obtain a urinalysis and urine microscopy to evaluate for possible acute kidney injury etiology.",
    "Order renal ultrasound to rule out obstructive causes of acute kidney injury."
  ],
  "Assessment and Plan": {
    "Assessment": "Suspected acute kidney injury (AKI), possibly pre-renal vs. acute interstitial nephritis post recent antibiotic use. Further workup needed.",
    "Plan": [
      "Obtain lab tests to confirm AKI and determine severity.",
      "Assess for underlying cause (e.g., volume depletion, medication effect, obstruction).",
      "Consider holding ACE inhibitor temporarily if kidney function is significantly impaired.",
      "Follow up within 24-48 hours with lab results. If worsening, consider referral to nephrology."
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
