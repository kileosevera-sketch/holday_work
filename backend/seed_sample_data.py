"""Generates a realistic test dataset for Post-Sales Feedback Analysis & Failure Prediction."""
from datetime import datetime, timedelta, timezone
import random
import pandas as pd

SAMPLE_FEEDBACK = [
    # Power & Battery Circuitry Fault
    "The battery started swelling after two weeks of normal use and now the phone won't turn on at all.",
    "Dead on arrival. Plugged it in for 4 hours but there is no power and the charging LED never lights up.",
    "Sudden shutdown while using navigation. Battery drops from 80% to 0% in under 5 minutes.",
    "Won't charge with the included adapter. The charging port feels loose and sparks intermittently.",
    
    # Thermal Management Defect
    "Device gets extremely hot to the touch during simple video calls. The cooling fan is constantly loud and noisy.",
    "There was a strong burning smell coming from the exhaust vents before the system shut down from thermal overheating.",
    "Severe thermal throttling causing heavy stutter and frame drops. Back panel reached over 50 degrees Celsius.",
    
    # Display Panel Defect
    "Screen flickering started yesterday. Now there are permanent green vertical lines running down the entire OLED panel.",
    "The touchscreen is completely unresponsive on the right half. Ghost touch keeps opening random apps.",
    "Black screen issue. The notification sound plays, but the display remains pitch black.",
    
    # Firmware & OS Instability
    "The app freezes and crashes whenever I try to export reports. Constant boot loop after the latest firmware update.",
    "Encountered multiple blue screen errors (KERNEL_DATA_INPAGE_ERROR) after waking the machine from sleep mode.",
    "System UI completely locked up. Had to perform a hard reset three times today.",
    
    # Wireless & Connectivity Drop
    "Wi-Fi keeps disconnecting every few minutes. Other laptops in the room work fine, but this one drops signal constantly.",
    "Bluetooth pairing fails with all my headphones. Audio cuts out and stutters if I move more than 2 feet away.",
    
    # Audio Hardware Fault
    "The left speaker has a loud buzzing noise and distorted audio at volumes above 40%.",
    "Microphone stopped working completely. Callers can only hear static and muffled clicks.",
    
    # Transit & Shipping Issues
    "The delivery package was completely crushed when it arrived. The corner of the monitor frame is cracked and dented.",
    "Package was delayed by two weeks and tracking was never updated. Box arrived ripped open.",
    
    # Billing & Subscription Error
    "I was charged twice on my credit card for the annual warranty renewal. Demanding an immediate refund.",
    "Cancelled the subscription three weeks ago, but my account was still billed $149 yesterday. Unauthorized charge!",
    
    # Customer Service Gap
    "Called customer support three times regarding my broken unit. The representative was rude and hung up on me.",
    "Submitted an urgent support ticket 6 days ago with zero response. Ticket was closed without any resolution.",
    
    # Positive Experience
    "Exceptional build quality and very fast shipping! Everything works smoothly right out of the box.",
    "Customer service was incredibly helpful in replacing my lost cable within 24 hours. Highly satisfied!",
    "Great product! The battery easily lasts two full days and the display colors are vibrant and crisp.",
]

def generate_csv(filepath: str = "sample_postsale_feedback.csv", count: int = 40):
    today = datetime.now(timezone.utc)
    rows = []
    for i in range(count):
        text = random.choice(SAMPLE_FEEDBACK)
        days_ago = random.randint(0, 14)
        date_str = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        customer_id = f"CUST-{1000 + i}"
        product_model = random.choice(["ApexBook Pro 15", "QuantumPhone X", "UltraTab 11", "EchoSound Max"])
        rows.append({
            "customer_id": customer_id,
            "product_model": product_model,
            "feedback_text": text,
            "service_date": date_str,
        })
    df = pd.DataFrame(rows)
    df.to_csv(filepath, index=False)
    print(f"Generated {len(df)} sample feedback records at: {filepath}")
    return filepath

if __name__ == "__main__":
    generate_csv()

