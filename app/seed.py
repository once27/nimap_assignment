import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.role import Role

roles = [
    {"name": "Admin", "permissions": ["*"]},
    {"name": "Analyst", "permissions": ["upload_doc", "edit_doc", "search_doc"]},
    {"name": "Auditor", "permissions": ["view_doc", "search_doc"]},
    {"name": "Client", "permissions": ["view_doc", "search_doc"]}
]

def seed_roles():
    db = SessionLocal()
    try:
        count = 0
        for role_data in roles:
            existing = db.query(Role).filter(Role.name == role_data["name"]).first()
            if not existing:
                r = Role(name=role_data["name"], permissions=role_data["permissions"])
                db.add(r)
                count += 1
        db.commit()
        print(f"Successfully seeded {count} new role(s).")
    finally:
        db.close()

if __name__ == "__main__":
    seed_roles()
