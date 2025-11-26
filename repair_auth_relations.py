import sqlite3

def repair_auth_relations():
    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()

    print("🛠️ Checking for missing Django auth relations...")

    # Check for and create missing tables
    tables = [
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

    for name, sql in tables:
        try:
            cursor.execute(sql)
            print(f"✅ Ensured table: {name}")
        except Exception as e:
            print(f"⚠️ Could not create {name}: {e}")

    conn.commit()
    conn.close()
    print("✅ Auth relations repaired successfully.")

if __name__ == "__main__":
    repair_auth_relations()
