import os
import random
from PIL import Image, ImageDraw, ImageFont
from faker import Faker
from datetime import datetime, timedelta

# --- CONFIGURATION ---
fake = Faker('en_IN')
OUTPUT_DIR = "generated_samples"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- DATA PATTERNS FROM GUIDE ---
DOCTOR_REGS = [
    "KA/12345/2015", "MH/67890/2018", "DL/34567/2020", "TN/45678/2016",
    "AP/99887/2019", "WB/11223/2017"
]

DIAGNOSES = [
    "Viral fever", "Upper respiratory tract infection", "Gastroenteritis",
    "Hypertension", "Type 2 Diabetes", "Migraine", "Allergic rhinitis", "Lower back pain"
]

MEDICINES = [
    ("Paracetamol 650mg", 5.00),
    ("Amoxicillin 500mg", 12.00),
    ("Azithromycin 500mg", 25.00),
    ("Omeprazole 20mg", 8.00),
    ("Cetirizine 10mg", 4.00),
    ("Metformin 500mg", 3.50),
    ("Amlodipine 5mg", 6.00),
    ("Dolo 650mg", 4.50),
    ("Pan-D", 10.00)
]

TESTS = [
    ("Complete Blood Count (CBC)", 400),
    ("Blood Sugar (Fasting)", 150),
    ("Lipid Profile", 800),
    ("Liver Function Test", 600),
    ("X-Ray Chest", 500),
    ("ECG", 300)
]

HOSPITALS = ["Apollo Hospitals", "Fortis Healthcare", "City Care Clinic", "Max Healthcare", "TrustWell Hospital"]
LABS = ["Metropolis Labs", "Dr. Lal PathLabs", "Thyrocare", "City Diagnostics"]

# --- HELPER FUNCTIONS ---
def get_fonts():
    try:
        # Attempt to load a standard font, adjust path if on Linux/Mac
        header = ImageFont.truetype("arial.ttf", 28)
        sub_header = ImageFont.truetype("arial.ttf", 22)
        body = ImageFont.truetype("arial.ttf", 16)
        small = ImageFont.truetype("arial.ttf", 14)
        return header, sub_header, body, small
    except:
        return (ImageFont.load_default(),) * 4

def draw_header_clinic(d, width, fonts):
    header, sub, body, small = fonts
    clinic_name = random.choice(HOSPITALS)
    doc_name = f"Dr. {fake.first_name()} {fake.last_name()}, MBBS, MD"
    reg = random.choice(DOCTOR_REGS)
    
    d.text((50, 40), clinic_name, fill=(0, 51, 102), font=header)
    d.text((50, 80), doc_name, fill='black', font=sub)
    d.text((50, 110), f"Reg. No: {reg}", fill='black', font=small)
    d.text((50, 130), f"Ph: +91 {fake.msisdn()}", fill='black', font=small)
    d.line((40, 160, width-40, 160), fill='black', width=2)
    return 180 # Return Y position

def draw_footer(d, width, height, fonts):
    _, _, _, small = fonts
    d.line((40, height-100, width-40, height-100), fill='black', width=2)
    d.text((50, height-80), "Emergency Contact: 108", fill='gray', font=small)
    d.text((width-250, height-80), "Signature / Stamp", fill='black', font=small)
    
    # Stamp
    d.ellipse((width-200, height-130, width-80, height-40), outline='blue', width=3)
    d.text((width-180, height-95), "VERIFIED", fill='blue', font=small)

# --- GENERATORS ---

def generate_prescription(filename):
    width, height = 800, 1000
    img = Image.new('RGB', (width, height), 'white')
    d = ImageDraw.Draw(img)
    fonts = get_fonts()
    header, sub, body, small = fonts
    
    y = draw_header_clinic(d, width, fonts)
    
    # Patient Details
    pat_name = fake.name()
    age = random.randint(18, 75)
    date = (datetime.now() - timedelta(days=random.randint(0, 10))).strftime("%d/%m/%Y")
    
    d.text((50, y), f"Patient Name: {pat_name}", fill='black', font=body)
    d.text((550, y), f"Date: {date}", fill='black', font=body)
    d.text((50, y+30), f"Age/Sex: {age} / {random.choice(['M','F'])}", fill='black', font=body)
    
    y += 80
    
    # Diagnosis
    diag = random.choice(DIAGNOSES)
    d.text((50, y), "Chief Complaints:", fill='black', font=sub)
    d.text((70, y+30), "- Fever since 2 days", fill='black', font=body)
    d.text((70, y+55), "- Body ache", fill='black', font=body)
    
    y += 100
    d.text((50, y), f"Diagnosis: {diag}", fill='black', font=sub)
    
    y += 60
    d.text((50, y), "Rx (Prescription):", fill='black', font=sub)
    y += 40
    
    # Medicines
    num_meds = random.randint(2, 4)
    selected_meds = random.sample(MEDICINES, num_meds)
    for idx, (med_name, _) in enumerate(selected_meds, 1):
        freq = random.choice(["1-0-1", "1-1-1", "1-0-0"])
        dur = random.choice(["3 days", "5 days", "1 week"])
        d.text((70, y), f"{idx}. {med_name}", fill='black', font=body)
        d.text((350, y), f"-- {freq} (After Food)", fill='black', font=body)
        d.text((600, y), f"for {dur}", fill='black', font=body)
        y += 35

    # Tests Advised
    y += 40
    d.text((50, y), "Investigations Advised:", fill='black', font=sub)
    d.text((70, y+30), f"- {random.choice(TESTS)[0]}", fill='black', font=body)

    draw_footer(d, width, height, fonts)
    img.save(os.path.join(OUTPUT_DIR, filename))
    print(f"Created Prescription: {filename}")

def generate_medical_bill(filename):
    width, height = 800, 1000
    img = Image.new('RGB', (width, height), 'white')
    d = ImageDraw.Draw(img)
    fonts = get_fonts()
    header, sub, body, small = fonts
    
    y = draw_header_clinic(d, width, fonts)
    
    # Invoice Details
    bill_no = random.randint(10000, 99999)
    date = datetime.now().strftime("%d/%m/%Y")
    
    d.text((350, y), "INVOICE", fill='black', font=header)
    y += 50
    d.text((50, y), f"Bill No: {bill_no}", fill='black', font=body)
    d.text((550, y), f"Date: {date}", fill='black', font=body)
    y += 30
    d.text((50, y), f"Patient: {fake.name()}", fill='black', font=body)
    
    y += 60
    # Table Header
    d.rectangle((40, y, width-40, y+30), fill='lightgray')
    d.text((50, y+5), "PARTICULARS", fill='black', font=body)
    d.text((600, y+5), "AMOUNT (INR)", fill='black', font=body)
    y += 40
    
    # Items
    total = 0
    
    # 1. Consultation
    cons_fee = random.choice([500, 800, 1000, 1500])
    d.text((50, y), "Consultation Charges", fill='black', font=body)
    d.text((600, y), f"{cons_fee}.00", fill='black', font=body)
    total += cons_fee
    y += 30
    
    # 2. Random Test
    if random.random() > 0.3:
        test_name, test_cost = random.choice(TESTS)
        d.text((50, y), test_name, fill='black', font=body)
        d.text((600, y), f"{test_cost}.00", fill='black', font=body)
        total += test_cost
        y += 30
        
    # 3. Procedure (Rare)
    if random.random() > 0.7:
        proc_cost = 1200
        d.text((50, y), "Wound Dressing / Minor Proc", fill='black', font=body)
        d.text((600, y), f"{proc_cost}.00", fill='black', font=body)
        total += proc_cost
        y += 30

    # Totals
    d.line((40, y+20, width-40, y+20), fill='black', width=1)
    y += 30
    d.text((450, y), "Sub Total:", fill='black', font=body)
    d.text((600, y), f"{total}.00", fill='black', font=body)
    
    gst = int(total * 0.18)
    y += 30
    d.text((450, y), "GST (18%):", fill='black', font=body)
    d.text((600, y), f"{gst}.00", fill='black', font=body)
    
    grand_total = total + gst
    y += 40
    d.rectangle((440, y-5, width-40, y+35), outline='black')
    d.text((450, y), "TOTAL:", fill='black', font=sub)
    d.text((600, y), f"Rs. {grand_total}", fill='black', font=sub)
    
    draw_footer(d, width, height, fonts)
    img.save(os.path.join(OUTPUT_DIR, filename))
    print(f"Created Bill: {filename}")

def generate_diagnostic_report(filename):
    width, height = 800, 1000
    img = Image.new('RGB', (width, height), 'white')
    d = ImageDraw.Draw(img)
    fonts = get_fonts()
    header, sub, body, small = fonts
    
    # Header
    lab_name = random.choice(LABS)
    d.text((50, 40), lab_name, fill=(139, 0, 0), font=header)
    d.text((50, 80), "NABL Accredited Laboratory", fill='black', font=small)
    d.line((40, 120, width-40, 120), fill='black', width=2)
    
    y = 150
    d.text((50, y), f"Patient: {fake.name()}", fill='black', font=body)
    d.text((550, y), f"Date: {datetime.now().strftime('%d/%m/%Y')}", fill='black', font=body)
    d.text((50, y+30), f"Ref. By: Dr. {fake.last_name()}", fill='black', font=body)
    
    y += 80
    # Report Table
    d.rectangle((40, y, width-40, y+30), fill='lightgray')
    d.text((50, y+5), "TEST NAME", fill='black', font=body)
    d.text((350, y+5), "RESULT", fill='black', font=body)
    d.text((550, y+5), "NORMAL RANGE", fill='black', font=body)
    y += 50
    
    # Content (CBC Simulation)
    d.text((50, y), "COMPLETE BLOOD COUNT", fill='black', font=sub)
    y += 40
    
    tests = [
        ("Hemoglobin", "14.2 g/dL", "13.0 - 17.0"),
        ("Total WBC", "8,500 /cmm", "4,000 - 11,000"),
        ("Platelet Count", "2.4 Lakhs", "1.5 - 4.5 Lakhs"),
        ("Neutrophils", "60 %", "40 - 70"),
        ("Lymphocytes", "32 %", "20 - 40")
    ]
    
    for t_name, res, normal in tests:
        d.text((50, y), t_name, fill='black', font=body)
        d.text((350, y), res, fill='black', font=body)
        d.text((550, y), normal, fill='black', font=body)
        d.line((40, y+25, width-40, y+25), fill='lightgray', width=1)
        y += 35
        
    draw_footer(d, width, height, fonts)
    img.save(os.path.join(OUTPUT_DIR, filename))
    print(f"Created Report: {filename}")

def generate_pharmacy_bill(filename):
    width, height = 800, 1000
    img = Image.new('RGB', (width, height), 'white')
    d = ImageDraw.Draw(img)
    fonts = get_fonts()
    header, sub, body, small = fonts
    
    # Header
    pharm_name = f"{fake.city()} Medicos & Pharmacy"
    d.text((200, 40), pharm_name, fill='green', font=header)
    d.text((250, 80), "GST: 29ABCDE1234F1Z5", fill='black', font=small)
    d.line((40, 120, width-40, 120), fill='black', width=2)
    
    y = 150
    d.text((50, y), f"Patient: {fake.name()}", fill='black', font=body)
    d.text((550, y), f"Date: {datetime.now().strftime('%d/%m/%Y')}", fill='black', font=body)
    d.text((50, y+30), f"Doctor: Dr. {fake.last_name()}", fill='black', font=body)
    
    y += 70
    # Table
    d.text((50, y), "Item", fill='black', font=body)
    d.text((300, y), "Batch", fill='black', font=body)
    d.text((450, y), "Qty", fill='black', font=body)
    d.text((550, y), "Rate", fill='black', font=body)
    d.text((650, y), "Amount", fill='black', font=body)
    d.line((40, y+25, width-40, y+25), fill='black', width=1)
    y += 40
    
    # Items
    total = 0
    selected_meds = random.sample(MEDICINES, 3)
    
    for med_name, rate in selected_meds:
        qty = random.randint(5, 15)
        amt = qty * rate
        batch = f"{random.choice(['A','B','X'])}{random.randint(100,999)}"
        
        d.text((50, y), med_name[:25], fill='black', font=body)
        d.text((300, y), batch, fill='black', font=body)
        d.text((450, y), str(qty), fill='black', font=body)
        d.text((550, y), f"{rate}", fill='black', font=body)
        d.text((650, y), f"{amt:.2f}", fill='black', font=body)
        total += amt
        y += 30
        
    y += 20
    d.line((40, y, width-40, y), fill='black', width=1)
    y += 20
    d.text((550, y), f"Total: Rs. {total:.2f}", fill='black', font=sub)
    
    draw_footer(d, width, height, fonts)
    img.save(os.path.join(OUTPUT_DIR, filename))
    print(f"Created Pharmacy Bill: {filename}")

if __name__ == "__main__":
    generate_prescription("test_prescription.jpg")
    generate_medical_bill("test_bill.jpg")
    generate_diagnostic_report("test_report.jpg")
    generate_pharmacy_bill("test_pharmacy.jpg")
    
    print(f"\n[SUCCESS] 4 Documents generated in '{OUTPUT_DIR}/'")