import os
import random
from PIL import Image, ImageDraw, ImageFont
from faker import Faker

fake = Faker('en_IN')
BASE_DIR = "test_suite"

TEST_CASES = [
    {
        "id": "TC001",
        "desc": "Simple_Consultation_Approved",
        "date": "01/11/2024",
        "doctor": {"name": "Dr. Sharma", "reg": "KA/45678/2015"},
        "hospital": "City Care Clinic",
        "patient": "Rajesh Kumar",
        "diagnosis": "Viral fever",
        "medicines": ["Paracetamol 650mg", "Vitamin C"],
        "bill_items": [("Consultation Fee", 1000), ("Diagnostic Tests (CBC, Dengue)", 500)]
    },
    {
        "id": "TC002",
        "desc": "Dental_Partial_Approval",
        "date": "15/10/2024",
        "doctor": {"name": "Dr. Patel", "reg": "MH/23456/2018"},
        "hospital": "Smile Dental Care",
        "patient": "Priya Singh",
        "diagnosis": "Tooth decay requiring root canal",
        "medicines": ["Painkillers", "Antibiotics"],
        "bill_items": [("Root Canal Treatment", 8000), ("Teeth Whitening (Cosmetic)", 4000)]
    },
    {
        "id": "TC003",
        "desc": "Limit_Exceeded",
        "date": "20/10/2024",
        "doctor": {"name": "Dr. Gupta", "reg": "DL/34567/2016"},
        "hospital": "General Hospital",
        "patient": "Amit Verma",
        "diagnosis": "Gastroenteritis",
        "medicines": ["Antibiotics", "Probiotics"],
        "bill_items": [("Consultation Fee", 2000), ("Pharmacy / Medicines", 5500)]
    },
    {
        "id": "TC004",
        "desc": "Missing_Documents",
        "date": "25/10/2024",
        "doctor": None, # Simulating missing prescription
        "hospital": "City Clinic",
        "patient": "Sneha Reddy",
        "diagnosis": None,
        "medicines": [],
        "bill_items": [("Consultation Fee", 1500), ("Medicines", 500)],
        "skip_prescription": True # Logic flag
    },
    {
        "id": "TC005",
        "desc": "Waiting_Period_PreExisting",
        "date": "15/10/2024",
        "doctor": {"name": "Dr. Mehta", "reg": "GJ/56789/2014"},
        "hospital": "Diabetes Care Center",
        "patient": "Vikram Joshi",
        "diagnosis": "Type 2 Diabetes",
        "medicines": ["Metformin", "Glimepiride"],
        "bill_items": [("Consultation Fee", 1000), ("Medicines", 2000)]
    },
    {
        "id": "TC006",
        "desc": "Alternative_Medicine",
        "date": "28/10/2024",
        "doctor": {"name": "Vaidya Krishnan", "reg": "AYUR/KL/2345/2019"},
        "hospital": "Kerala Ayurveda Kendra",
        "patient": "Kavita Nair",
        "diagnosis": "Chronic joint pain",
        "medicines": ["Ayurvedic Oil Application"],
        "bill_items": [("Consultation Fee", 1000), ("Panchakarma Therapy", 3000)]
    },
    {
        "id": "TC007",
        "desc": "PreAuth_Missing_MRI",
        "date": "02/11/2024",
        "doctor": {"name": "Dr. Rao", "reg": "AP/67890/2017"},
        "hospital": "Ortho & Spine Center",
        "patient": "Suresh Patil",
        "diagnosis": "Suspected lumbar disc herniation",
        "medicines": ["Pain Relief Gel"],
        "bill_items": [("MRI Scan Lumbar Spine", 15000)]
    },
    {
        "id": "TC008",
        "desc": "Fraud_Manual_Review",
        "date": "30/10/2024",
        "doctor": {"name": "Dr. Khan", "reg": "UP/45678/2016"},
        "hospital": "City Neurology",
        "patient": "Ravi Menon",
        "diagnosis": "Migraine",
        "medicines": ["Sumatriptan", "Propranolol"],
        "bill_items": [("Consultation Fee", 2000), ("Medicines", 2800)]
    },
    {
        "id": "TC009",
        "desc": "Excluded_WeightLoss",
        "date": "18/10/2024",
        "doctor": {"name": "Dr. Banerjee", "reg": "WB/34567/2015"},
        "hospital": "Slim & Fit Clinic",
        "patient": "Anita Desai",
        "diagnosis": "Obesity - BMI 35",
        "medicines": ["Diet Supplements"],
        "bill_items": [("Consultation Fee", 3000), ("Bariatric Diet Plan", 5000)]
    },
    {
        "id": "TC010",
        "desc": "Network_Hospital_Cashless",
        "date": "03/11/2024",
        "doctor": {"name": "Dr. Iyer", "reg": "TN/56789/2013"},
        "hospital": "Apollo Hospitals", # Network Hospital
        "patient": "Deepak Shah",
        "diagnosis": "Acute bronchitis",
        "medicines": ["Antibiotics", "Bronchodilators"],
        "bill_items": [("Consultation Fee", 1500), ("Medicines & Nebulization", 3000)]
    }
]

# --- 2. HELPER FUNCTIONS ---
def get_fonts():
    try:
        header = ImageFont.truetype("arial.ttf", 28)
        sub = ImageFont.truetype("arial.ttf", 22)
        body = ImageFont.truetype("arial.ttf", 16)
        return header, sub, body
    except:
        return (ImageFont.load_default(),) * 3

def draw_shared_header(d, case, fonts):
    header, sub, body = fonts
    # Clinic Name
    d.text((50, 40), case['hospital'], fill=(0, 51, 102), font=header)
    
    # Doctor Details (if valid)
    if case.get('doctor'):
        d.text((50, 80), case['doctor']['name'], fill='black', font=sub)
        d.text((50, 110), f"Reg: {case['doctor']['reg']}", fill='black', font=body)
    
    d.line((40, 150, 760, 150), fill='black', width=2)
    return 170

# --- 3. GENERATORS ---

def generate_prescription(case, folder):
    if case.get("skip_prescription"):
        return

    width, height = 800, 1000
    img = Image.new('RGB', (width, height), 'white')
    d = ImageDraw.Draw(img)
    fonts = get_fonts()
    header, sub, body = fonts
    
    y = draw_shared_header(d, case, fonts)
    
    # Patient Info
    d.text((50, y), f"Patient: {case['patient']}", fill='black', font=body)
    d.text((550, y), f"Date: {case['date']}", fill='black', font=body)
    y += 60
    
    # Diagnosis
    d.text((50, y), f"Diagnosis: {case['diagnosis']}", fill='black', font=sub)
    y += 60
    
    # Rx
    d.text((50, y), "Rx / Medicines:", fill='black', font=sub)
    y += 40
    for med in case['medicines']:
        d.text((70, y), f"- {med}", fill='black', font=body)
        y += 30
        
    # Signature
    d.line((40, 900, 760, 900), fill='black', width=2)
    d.text((600, 910), "SIGNED", fill='blue', font=body)
    
    filename = f"{folder}/prescription.jpg"
    img.save(filename)
    print(f"  -> Created {filename}")

def generate_bill(case, folder):
    width, height = 800, 1000
    img = Image.new('RGB', (width, height), 'white')
    d = ImageDraw.Draw(img)
    fonts = get_fonts()
    header, sub, body = fonts
    
    y = draw_shared_header(d, case, fonts)
    
    # Bill Header
    d.text((350, y), "INVOICE", fill='black', font=header)
    y += 50
    d.text((50, y), f"Bill No: {random.randint(1000,9999)}", fill='black', font=body)
    d.text((550, y), f"Date: {case['date']}", fill='black', font=body)
    d.text((50, y+25), f"Patient: {case['patient']}", fill='black', font=body)
    
    y += 70
    # Table
    d.rectangle((40, y, 760, y+30), fill='lightgray')
    d.text((50, y+5), "Description", fill='black', font=body)
    d.text((600, y+5), "Amount (INR)", fill='black', font=body)
    y += 40
    
    total = 0
    for item, cost in case['bill_items']:
        d.text((50, y), item, fill='black', font=body)
        d.text((600, y), f"{cost}.00", fill='black', font=body)
        total += cost
        y += 30
        
    y += 20
    d.line((40, y, 760, y), fill='black', width=2)
    y += 10
    d.text((450, y), f"TOTAL: Rs. {total}.00", fill='black', font=sub)
    
    # Footer
    d.text((50, 950), "This is a computer generated invoice.", fill='gray', font=body)
    
    filename = f"{folder}/bill.jpg"
    img.save(filename)
    print(f"  -> Created {filename}")

# --- 4. MAIN LOOP ---
if __name__ == "__main__":
    print(f"Generating {len(TEST_CASES)} Test Case Scenarios...\n")
    
    for case in TEST_CASES:
        folder_name = f"{BASE_DIR}/{case['id']}_{case['desc']}"
        os.makedirs(folder_name, exist_ok=True)
        
        print(f"Processing {case['id']}...")
        generate_prescription(case, folder_name)
        generate_bill(case, folder_name)
        print("")
        
    print(f"Done! Check the '{BASE_DIR}' folder.")