import os
import random
from PIL import Image, ImageDraw, ImageFont
from faker import Faker
from datetime import datetime, timedelta

# --- CONFIGURATION ---
fake = Faker('en_IN')
OUTPUT_DIR = "generated_samples"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- DATA POOLS ---
HOSPITALS = ["Apollo Hospitals", "Fortis Healthcare", "City Care Clinic", "Max Healthcare"]
LABS = ["Metropolis Labs", "Dr. Lal PathLabs", "Thyrocare", "City Diagnostics"]
DOCTOR_REGS = ["KA/12345/2015", "MH/67890/2018", "DL/34567/2020"]

# --- HELPER FUNCTIONS ---
def get_fonts():
    try:
        header = ImageFont.truetype("arial.ttf", 28)
        sub_header = ImageFont.truetype("arial.ttf", 22)
        body = ImageFont.truetype("arial.ttf", 16)
        small = ImageFont.truetype("arial.ttf", 14)
        return header, sub_header, body, small
    except:
        return (ImageFont.load_default(),) * 4

def draw_header_clinic(d, width, fonts, context=None):
    header, sub, body, small = fonts
    
    # Use context if available, else random
    clinic_name = context.get("hospital_name", random.choice(HOSPITALS)) if context else random.choice(HOSPITALS)
    doc_name = context.get("doctor_name", f"Dr. {fake.first_name()} {fake.last_name()}") if context else f"Dr. {fake.first_name()} {fake.last_name()}"
    
    d.text((50, 40), clinic_name, fill=(0, 51, 102), font=header)
    d.text((50, 80), doc_name, fill='black', font=sub)
    d.text((50, 110), "Reg: KA/12345/2020", fill='black', font=small)
    d.line((40, 160, width-40, 160), fill='black', width=2)
    return 180

def draw_footer(d, width, height, fonts):
    _, _, _, small = fonts
    d.line((40, height-100, width-40, height-100), fill='black', width=2)
    d.text((width-200, height-130), "VERIFIED", fill='blue', font=small)
    d.ellipse((width-220, height-140, width-100, height-110), outline='blue', width=2)

# --- GENERATORS (Updated to accept Context) ---

def generate_prescription(filename, context=None):
    width, height = 800, 1000
    img = Image.new('RGB', (width, height), 'white')
    d = ImageDraw.Draw(img)
    fonts = get_fonts()
    header, sub, body, small = fonts
    
    y = draw_header_clinic(d, width, fonts, context)
    
    # Context Data or Random
    pat_name = context.get("patient_name", fake.name()) if context else fake.name()
    date = context.get("date", datetime.now().strftime("%d/%m/%Y")) if context else datetime.now().strftime("%d/%m/%Y")
    diagnosis = context.get("diagnosis", "Viral Fever") if context else "Viral Fever"
    meds = context.get("medicines", ["Tab Dolo 650mg"]) if context else ["Tab Dolo 650mg"]

    d.text((50, y), f"Patient: {pat_name}", fill='black', font=body)
    d.text((550, y), f"Date: {date}", fill='black', font=body)
    
    y += 80
    d.text((50, y), f"Diagnosis: {diagnosis}", fill='black', font=sub)
    y += 50
    d.text((50, y), "Rx:", fill='black', font=body)
    y += 30
    for m in meds:
        d.text((70, y), f"- {m}", fill='black', font=body)
        y += 30

    draw_footer(d, width, height, fonts)
    img.save(os.path.join(OUTPUT_DIR, filename))
    print(f"Generated Prescription: {filename}")

def generate_medical_bill(filename, context=None):
    width, height = 800, 1000
    img = Image.new('RGB', (width, height), 'white')
    d = ImageDraw.Draw(img)
    fonts = get_fonts()
    header, sub, body, small = fonts
    
    y = draw_header_clinic(d, width, fonts, context)
    
    pat_name = context.get("patient_name", fake.name()) if context else fake.name()
    date = context.get("date", datetime.now().strftime("%d/%m/%Y")) if context else datetime.now().strftime("%d/%m/%Y")
    items = context.get("bill_items", [("Consultation", 500)]) if context else [("Consultation", 500)]

    d.text((350, y), "INVOICE", fill='black', font=header)
    y += 50
    d.text((50, y), f"Bill No: {random.randint(10000,99999)}", fill='black', font=body)
    d.text((50, y+30), f"Patient: {pat_name}", fill='black', font=body)
    d.text((550, y), f"Date: {date}", fill='black', font=body)
    
    y += 80
    d.rectangle((40, y, width-40, y+30), fill='lightgray')
    d.text((50, y+5), "PARTICULARS", fill='black', font=body)
    d.text((600, y+5), "AMOUNT", fill='black', font=body)
    y += 40
    
    total = 0
    for item, cost in items:
        d.text((50, y), item, fill='black', font=body)
        d.text((600, y), f"{cost}.00", fill='black', font=body)
        total += cost
        y += 30
        
    d.line((40, y+20, width-40, y+20), fill='black', width=1)
    d.text((450, y+40), f"TOTAL: Rs. {total}", fill='black', font=header)
    
    draw_footer(d, width, height, fonts)
    img.save(os.path.join(OUTPUT_DIR, filename))
    print(f"Generated Bill: {filename}")

def generate_diagnostic_report(filename, context=None):
    width, height = 800, 1000
    img = Image.new('RGB', (width, height), 'white')
    d = ImageDraw.Draw(img)
    fonts = get_fonts()
    header, sub, body, small = fonts
    
    lab_name = context.get("lab_name", random.choice(LABS)) if context else random.choice(LABS)
    pat_name = context.get("patient_name", fake.name()) if context else fake.name()
    date = context.get("date", datetime.now().strftime("%d/%m/%Y")) if context else datetime.now().strftime("%d/%m/%Y")
    tests = context.get("lab_tests", []) if context else []

    d.text((50, 40), lab_name, fill=(139, 0, 0), font=header)
    d.line((40, 100, width-40, 100), fill='black', width=2)
    
    y = 120
    d.text((50, y), f"Patient: {pat_name}", fill='black', font=body)
    d.text((550, y), f"Date: {date}", fill='black', font=body)
    
    y += 60
    d.rectangle((40, y, width-40, y+30), fill='lightgray')
    d.text((50, y+5), "TEST NAME", fill='black', font=body)
    d.text((350, y+5), "RESULT", fill='black', font=body)
    d.text((550, y+5), "RANGE", fill='black', font=body)
    y += 50
    
    for t_name, res, rng in tests:
        d.text((50, y), t_name, fill='black', font=body)
        d.text((350, y), res, fill='black', font=body)
        d.text((550, y), rng, fill='black', font=body)
        y += 40
        
    draw_footer(d, width, height, fonts)
    img.save(os.path.join(OUTPUT_DIR, filename))
    print(f"Generated Report: {filename}")

# --- SCENARIO ORCHESTRATOR ---

def create_linked_case():
    """
    Creates a matched set of documents for a single patient scenario.
    """
    # 1. Define the Shared Context
    case_date = datetime.now().strftime("%d/%m/%Y")
    patient = fake.name()
    doctor = f"Dr. {fake.first_name()} {fake.last_name()}"
    hospital = "City Care Clinic"
    
    print(f"\n--- Creating Linked Case for: {patient} ---")

    # --- DOCUMENT 1: LAB REPORT (The Medical Evidence) ---
    # Scenario: Patient has low platelets (Dengue indication)
    lab_context = {
        "patient_name": patient,
        "date": case_date,
        "lab_name": "Metropolis Labs",
        "lab_tests": [
            ("Platelet Count", "90,000", "1.5 - 4.5 Lakhs"), # LOW
            ("Dengue NS1 Antigen", "POSITIVE", "Negative"),  # POSITIVE
            ("Hemoglobin", "13.5", "13.0 - 17.0")
        ]
    }
    generate_diagnostic_report("linked_1_report.jpg", lab_context)

    # --- DOCUMENT 2: MEDICAL BILL (The Financial Claim) ---
    # The bill charges must match the report (Dengue Test)
    bill_context = {
        "patient_name": patient,
        "date": case_date,
        "hospital_name": hospital,
        "doctor_name": doctor,
        "bill_items": [
            ("Consultation Charges", 1000),
            ("Dengue NS1 Antigen Test", 1200), # Matches Report
            ("CBC (Platelet Count)", 400),     # Matches Report
            ("IV Fluids Administration", 1500)
        ]
    }
    generate_medical_bill("linked_2_bill.jpg", bill_context)

    # --- DOCUMENT 3: PRESCRIPTION (The Medical Necessity) ---
    presc_context = {
        "patient_name": patient,
        "date": case_date,
        "hospital_name": hospital,
        "doctor_name": doctor,
        "diagnosis": "Dengue Fever",
        "medicines": [
            "Tab Dolo 650mg (1-1-1)",
            "IV Fluids NS 500ml",
            "Drink plenty of water"
        ]
    }
    generate_prescription("linked_3_prescription.jpg", presc_context)

if __name__ == "__main__":
    create_linked_case()