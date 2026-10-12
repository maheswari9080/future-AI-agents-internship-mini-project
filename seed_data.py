"""
Seed database script for EWB Student Record Management System.
Inserts realistic student records across multiple courses for demonstration.
"""

from datetime import date
from app.database import SessionLocal, init_db
from app.models import Student

DEMO_STUDENTS = [
    {
        "name": "Aarav Sharma",
        "date_of_birth": date(2003, 5, 14),
        "email": "aarav.sharma@example.com",
        "phone": "+91 98765 43210",
        "course": "Artificial Intelligence & ML",
        "address": "42 MG Road, Bengaluru, Karnataka",
        "enrollment_date": date(2024, 7, 10),
    },
    {
        "name": "Diya Patel",
        "date_of_birth": date(2004, 2, 22),
        "email": "diya.patel@example.com",
        "phone": "+91 98123 45678",
        "course": "Full Stack Web Development",
        "address": "15 CG Road, Ahmedabad, Gujarat",
        "enrollment_date": date(2024, 8, 1),
    },
    {
        "name": "Rohan Iyer",
        "date_of_birth": date(2002, 11, 30),
        "email": "rohan.iyer@example.com",
        "phone": "+91 97654 32109",
        "course": "Data Science & Analytics",
        "address": "77 Anna Salai, Chennai, Tamil Nadu",
        "enrollment_date": date(2024, 6, 15),
    },
    {
        "name": "Ananya Sen",
        "date_of_birth": date(2003, 9, 18),
        "email": "ananya.sen@example.com",
        "phone": "+91 99234 56781",
        "course": "Cybersecurity & Ethical Hacking",
        "address": "10 Park Street, Kolkata, West Bengal",
        "enrollment_date": date(2024, 8, 20),
    },
    {
        "name": "Kavya Reddy",
        "date_of_birth": date(2004, 6, 5),
        "email": "kavya.reddy@example.com",
        "phone": "+91 98451 23456",
        "course": "Artificial Intelligence & ML",
        "address": "88 Jubilee Hills, Hyderabad, Telangana",
        "enrollment_date": date(2024, 9, 1),
    },
    {
        "name": "Vikram Malhotra",
        "date_of_birth": date(2001, 12, 12),
        "email": "vikram.malhotra@example.com",
        "phone": "+91 98987 65432",
        "course": "Cloud Computing & DevOps",
        "address": "23 Connaught Place, New Delhi",
        "enrollment_date": date(2024, 7, 25),
    },
    {
        "name": "Sneha Nair",
        "date_of_birth": date(2003, 4, 8),
        "email": "sneha.nair@example.com",
        "phone": "+91 97456 12345",
        "course": "Full Stack Web Development",
        "address": "56 Marine Drive, Kochi, Kerala",
        "enrollment_date": date(2024, 8, 5),
    },
    {
        "name": "Aditya Verma",
        "date_of_birth": date(2002, 8, 27),
        "email": "aditya.verma@example.com",
        "phone": "+91 98321 65498",
        "course": "Data Science & Analytics",
        "address": "34 Hazratganj, Lucknow, Uttar Pradesh",
        "enrollment_date": date(2024, 7, 18),
    },
    {
        "name": "Pooja Hegde",
        "date_of_birth": date(2004, 1, 19),
        "email": "pooja.hegde@example.com",
        "phone": "+91 98877 66554",
        "course": "Artificial Intelligence & ML",
        "address": "12 Mall Road, Shimla, Himachal Pradesh",
        "enrollment_date": date(2024, 9, 12),
    },
    {
        "name": "Manish Joshi",
        "date_of_birth": date(2002, 3, 14),
        "email": "manish.joshi@example.com",
        "phone": "+91 97766 55443",
        "course": "Cloud Computing & DevOps",
        "address": "19 FC Road, Pune, Maharashtra",
        "enrollment_date": date(2024, 6, 29),
    },
    {
        "name": "Meera Pillai",
        "date_of_birth": date(2003, 10, 24),
        "email": "meera.pillai@example.com",
        "phone": None,
        "course": "Cybersecurity & Ethical Hacking",
        "address": "67 Kowdiar, Thiruvananthapuram, Kerala",
        "enrollment_date": date(2024, 8, 14),
    },
    {
        "name": "Karthik Sundaram",
        "date_of_birth": date(2001, 7, 9),
        "email": None,
        "phone": "+91 98234 11223",
        "course": "Data Science & Analytics",
        "address": "81 RS Puram, Coimbatore, Tamil Nadu",
        "enrollment_date": date(2024, 9, 2),
    },
]


def seed():
    init_db()
    db = SessionLocal()
    try:
        existing_count = db.query(Student).count()
        if existing_count > 0:
            print(f"Database already contains {existing_count} records. Skipping seed.")
            return

        print("Seeding database with 12 fictional student records...")
        for student_data in DEMO_STUDENTS:
            s = Student(**student_data)
            db.add(s)
        db.commit()
        print("Database seeded successfully!")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
