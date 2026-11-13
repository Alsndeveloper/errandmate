"""
Database Seeding Script for ErrandMate
Populates rich realistic demo personas, ratings, and tasks across lifecycles.
"""
import sqlite3
from server.database import get_db, init_db
from server.security import hash_password


def seed_database():
    init_db()
    pw_hash = hash_password("Password123!")
    admin_pw_hash = hash_password("admin123")

    with get_db() as conn:
        # Always ensure 'admin' user exists
        admin_user = conn.execute("SELECT id FROM users WHERE username = 'admin' OR email = 'admin@errandmate.com'").fetchone()
        if not admin_user:
            conn.execute(
                """INSERT OR REPLACE INTO users (username, full_name, email, phone, password, role, id_type, id_number, residential_address, postcode, is_id_verified, tasks_done)
                   VALUES ('admin', 'Platform Administrator', 'admin@errandmate.com', '+447000999000', ?, 'both', 'Passport', 'ADMIN-UK-99201', 'Cardiff Civic Centre', 'CF10 3ND', 1, 50)""",
                (admin_pw_hash,)
            )

        # Check if already seeded with demo personas
        existing = conn.execute("SELECT id FROM users WHERE email = 'runner@errandmate.com'").fetchone()
        if existing:
            return

        print("Seeding ErrandMate demo users and tasks...")

        # 1. Insert Standard Demo Users with Verified Personal IDs
        users = [
            ("jane_foster", "Jane Foster", "poster@errandmate.com", "+447100222333", pw_hash, "poster", "UK Driving Licence", "DL-99281744", "42 Albany Road, Roath", "CF24 3NT", 1, 0),
            ("bob_walker", "Bob Walker", "runner@errandmate.com", "+447200444555", pw_hash, "runner", "Passport", "P-88392011", "15 Wellfield Road, Roath", "CF24 3PB", 1, 28),
            ("alan_sunny", "Alan Sunny", "student@errandmate.com", "+447300666777", pw_hash, "both", "Student ID", "STU-CMET-8392", "14 Maplewood Street, Cathays", "CF24 9ZZ", 1, 12),
            ("clara_davies", "Clara Davies", "clara@errandmate.com", "+447400888999", pw_hash, "poster", "National ID Card", "NID-11029384", "8 Pen-Y-Wain Road, Roath", "CF24 4GG", 1, 0),
        ]

        for u in users:
            conn.execute(
                """INSERT OR IGNORE INTO users (username, full_name, email, phone, password, role, id_type, id_number, residential_address, postcode, is_id_verified, tasks_done)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                u
            )

        # Get user IDs
        poster_id = conn.execute("SELECT id FROM users WHERE email = 'poster@errandmate.com'").fetchone()[0]
        runner_id = conn.execute("SELECT id FROM users WHERE email = 'runner@errandmate.com'").fetchone()[0]
        student_id = conn.execute("SELECT id FROM users WHERE email = 'student@errandmate.com'").fetchone()[0]
        clara_id = conn.execute("SELECT id FROM users WHERE email = 'clara@errandmate.com'").fetchone()[0]

        # 2. Insert Tasks across all lifecycle stages
        tasks = [
            # Open tasks
            (
                "Grocery pickup from Tesco Extra",
                "Need 4 bags of groceries picked up from Click & Collect bay 3. Order is prepaid under Foster.",
                "Grocery Shopping", "Cardiff Heath / Western Ave", 16.50, "Today by 6:00 PM", "open",
                poster_id, None, "2026-11-04 14:10:00", None, None, None, None, None, None
            ),
            (
                "Urgent prescription pickup from Boots Queen Street",
                "Pick up prescription bag from Boots pharmacy counter on Queen St and deliver to desk on 4th floor.",
                "Pharmacy Pickup", "Cardiff City Centre", 10.00, "Today by 4:30 PM", "open",
                clara_id, None, "2026-11-04 14:20:00", None, None, None, None, None, None
            ),
            (
                "Deliver university assignment portfolio to Cyncoed Campus",
                "A3 portfolio folder needs safe delivery to Cardiff Met Cyncoed reception before submission window.",
                "Delivery / Courier", "Roath to Cyncoed", 14.00, "Tomorrow 10:00 AM", "open",
                student_id, None, "2026-11-04 15:00:00", None, None, None, None, None, None
            ),
            (
                "Afternoon dog walk for friendly Golden Retriever in Bute Park",
                "Take Barney (well-behaved 3yo dog) on a 45-min stroll around Bute Park trail. Leash provided.",
                "Pet Care", "Cathays / Bute Park", 18.00, "Today 5:00 PM", "open",
                poster_id, None, "2026-11-04 15:30:00", None, None, None, None, None, None
            ),
            (
                "Help assembling IKEA Pax wardrobe unit",
                "Need assistance lifting and securing two tall sliding door panels on Pax unit in 2nd bedroom.",
                "Moving Help", "Cardiff Bay", 35.00, "Saturday 11:00 AM", "open",
                poster_id, None, "2026-11-04 16:00:00", None, None, None, None, None, None
            ),
            (
                "Fix home Wi-Fi mesh router & configure Smart TV",
                "Mesh node upstairs is disconnected. Need someone tech-savvy to reconnect backhaul and connect Apple TV.",
                "Tech Support", "Canton", 25.00, "Flexible", "open",
                clara_id, None, "2026-11-04 16:30:00", None, None, None, None, None, None
            ),
            # In-progress task
            (
                "Collect parcel from Royal Mail Depot on Penarth Road",
                "Present collection slip number RM-99482. Package weighs ~3kg. Deliver to flat 14.",
                "Delivery / Courier", "Grangetown / Penarth Rd", 12.50, "Today 5:30 PM", "in_progress",
                poster_id, runner_id, "2026-11-04 12:00:00", "2026-11-04 12:15:00", "2026-11-04 12:45:00", None, None, None, None
            ),
            # Awaiting confirmation task
            (
                "Pick up garden compost bags & flower seeds from B&Q",
                "2x 25L multipurpose compost bags and 3 packs of lavender seeds from B&Q Culverhouse Cross.",
                "Gardening", "Culverhouse Cross to Roath", 22.00, "Today 3:00 PM", "awaiting_confirmation",
                clara_id, runner_id, "2026-11-04 10:00:00", "2026-11-04 10:30:00", "2026-11-04 11:00:00", "2026-11-04 13:00:00", None, None, None
            ),
            # Completed tasks with ratings
            (
                "Emergency phone charger & adapter delivery to Cardiff Central",
                "Stranded with 2% battery at train platform 3. Needed USB-C fast charger immediately.",
                "Delivery / Courier", "Cardiff Central Station", 15.00, "Yesterday", "completed",
                student_id, runner_id, "2026-11-03 09:00:00", "2026-11-03 09:05:00", "2026-11-03 09:10:00", "2026-11-03 09:25:00", "2026-11-03 09:30:00", None, None
            ),
            (
                "Weekly fresh produce market run from Cardiff Central Market",
                "Fresh sourdough bread from Ashton's and seasonal veg basket. Delivered carefully.",
                "Grocery Shopping", "Cardiff Market to Penylan", 14.50, "Yesterday", "completed",
                clara_id, runner_id, "2026-11-03 11:00:00", "2026-11-03 11:15:00", "2026-11-03 11:30:00", "2026-11-03 12:15:00", "2026-11-03 12:20:00", None, None
            )
        ]

        for t in tasks:
            cursor = conn.execute("""
                INSERT INTO tasks (
                    title, description, category, location, price, deadline, status,
                    poster_id, runner_id, posted_on, accepted_on, started_on, submitted_on, finished_on,
                    cancelled_on, cancellation_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, t)
            task_id = cursor.lastrowid

            # Add ratings for completed tasks
            if t[6] == "completed":
                reviewer_id = t[7]
                r_runner_id = t[8]
                review_text = "Prompt, communicative, and very reliable!" if "produce" in t[0] else "Absolute lifesaver! Delivered within 20 minutes."
                conn.execute("""
                    INSERT OR IGNORE INTO ratings (task_id, reviewer_id, runner_id, rating, review)
                    VALUES (?, ?, ?, 5, ?)
                """, (task_id, reviewer_id, r_runner_id, review_text))

        print("ErrandMate database successfully populated with rich demo data!")


if __name__ == "__main__":
    seed_database()
