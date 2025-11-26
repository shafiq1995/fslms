import sqlite3

def safe_add_column(cursor, table, column, definition):
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition};")
        print(f"✅ Added column: {table}.{column}")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(f"⚠️ Column already exists: {table}.{column}")
        else:
            print(f"❌ Error adding {table}.{column}: {e}")

def safe_create_table(cursor, name, sql):
    try:
        cursor.execute(sql)
        print(f"✅ Ensured table exists: {name}")
    except sqlite3.OperationalError as e:
        if "already exists" in str(e):
            print(f"⚠️ Table already exists: {name}")
        else:
            print(f"❌ Error creating table {name}: {e}")

def repair_database():
    db_path = "db.sqlite3"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🩺 Repairing database schema...")

    # ==========================
    # InstructorProfile columns
    # ==========================
    instructor_fields = {
        "approved_at": "DATETIME",
        "created_at": "DATETIME",
        "updated_at": "DATETIME",
        "languages": "TEXT",
        "signature_image": "VARCHAR(255)",
        "total_courses": "INTEGER DEFAULT 0",
        "total_students": "INTEGER DEFAULT 0",
    }

    for column, definition in instructor_fields.items():
        safe_add_column(cursor, "instructor_tool_instructorprofile", column, definition)

    # ==========================
    # LearnerProfile columns
    # ==========================
    learner_fields = {
        "student_id": "VARCHAR(120)",
        "created_at": "DATETIME",
        "updated_at": "DATETIME",
        "emergency_contact": "VARCHAR(50)",
        "guardian_name": "VARCHAR(150)",
        "special_needs": "TEXT",
        "learning_hours": "INTEGER DEFAULT 0",
    }

    for column, definition in learner_fields.items():
        safe_add_column(cursor, "student_tool_learnerprofile", column, definition)

    # ==========================
    # Django Auth Relations
    # ==========================
    print("\n🔧 Checking Django auth relations...")

    auth_tables = [
        ("auth_group_permissions", """
            CREATE TABLE IF NOT EXISTS auth_group_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                permission_id INTEGER NOT NULL,
                FOREIGN KEY(group_id) REFERENCES auth_group(id),
                FOREIGN KEY(permission_id) REFERENCES auth_permission(id)
            );
        """),
        ("accounts_user_groups", """
            CREATE TABLE IF NOT EXISTS accounts_user_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                group_id INTEGER NOT NULL,
                FOREIGN KEY(user_id) REFERENCES accounts_user(id),
                FOREIGN KEY(group_id) REFERENCES auth_group(id)
            );
        """),
        ("accounts_user_user_permissions", """
            CREATE TABLE IF NOT EXISTS accounts_user_user_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                permission_id INTEGER NOT NULL,
                FOREIGN KEY(user_id) REFERENCES accounts_user(id),
                FOREIGN KEY(permission_id) REFERENCES auth_permission(id)
            );
        """),
    ]

    for name, sql in auth_tables:
        safe_create_table(cursor, name, sql)

    conn.commit()
    conn.close()
    print("\n✅ Database repair completed successfully.")

if __name__ == "__main__":
    repair_database()
