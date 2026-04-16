import sys
import argparse
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.user import User
from app.models.role import Role

def main():
    parser = argparse.ArgumentParser(description="Change a user's role from the terminal.")
    parser.add_argument("username", type=str, help="Username of the user")
    parser.add_argument("role", type=str, help="The new role (e.g., Admin, Analyst)")
    
    args = parser.parse_args()
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == args.username).first()
        if not user:
            print(f"Error: User '{args.username}' not found.")
            return
            
        role = db.query(Role).filter(Role.name == args.role).first()
        if not role:
            print(f"Error: Role '{args.role}' not found.")
            return
            
        user.roles = [role]
        db.commit()
        print(f"Success! {args.username} is now assigned as {args.role}.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
