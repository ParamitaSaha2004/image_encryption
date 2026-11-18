"""
Database Initialization and Seeding Script
Creates database tables and seeds default roles, settings, and clinician accounts.
"""
from sqlalchemy.orm import Session
from app.database.connection import engine, SessionLocal, Base
from app.models.db_models import Role, User, SystemSetting, AccessPermission
from app.security.token_util import hash_password
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import uuid
import datetime

def generate_ecdh_keypair():
    """Generates a NIST P-256 ECDH key pair for demonstration users."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    
    pub_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode("utf-8")
    
    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode("utf-8")
    
    return pub_pem, priv_pem

def init_database():
    print("[*] Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    print("[+] All database tables verified / created.")

    db: Session = SessionLocal()
    try:
        # 1. Seed Roles
        roles_data = [
            ("SUPER_ADMIN", "Root authority: Full security policy control, administrative auditing, and user management."),
            ("ADMIN", "Security & system administrator: Observes security alerts, monitors images, reviews audit logs."),
            ("USER", "Standard authorized clinician or researcher: Uploads, encrypts, decrypts, and shares images.")
        ]
        
        roles_map = {}
        for r_name, r_desc in roles_data:
            role = db.query(Role).filter(Role.role_name == r_name).first()
            if not role:
                role = Role(role_name=r_name, description=r_desc)
                db.add(role)
                db.commit()
                db.refresh(role)
            roles_map[r_name] = role.role_id
        print("[+] Roles seeded successfully.")

        # 2. Seed Default System Settings
        settings_data = [
            ("MAX_UPLOAD_SIZE_MB", "50", "Maximum allowed single image payload size in megabytes."),
            ("ANOMALY_CONTAMINATION_RATE", "0.05", "Expected anomaly proportion parameter for Isolation Forest model."),
            ("MAX_FAILED_LOGINS_BEFORE_LOCK", "5", "Number of consecutive authentication failures triggering temporary lockout."),
            ("DEFAULT_SHARE_EXPIRY_HOURS", "24", "Default lifetime for newly generated secure image shares."),
            ("AUDIT_HASH_CHAIN_GENESIS", "0000000000000000000000000000000000000000000000000000000000000000", "Genesis previous hash for tamper-evident audit chaining.")
        ]
        for key, val, desc in settings_data:
            existing = db.query(SystemSetting).filter(SystemSetting.setting_key == key).first()
            if not existing:
                db.add(SystemSetting(setting_key=key, setting_value=val, description=desc))
        db.commit()
        print("[+] System settings seeded.")

        # 3. Seed Demo Users
        demo_users = [
            ("superadmin", "superadmin@hice.security", "Password123!", "SUPER_ADMIN"),
            ("sec_admin", "admin@hice.security", "Password123!", "ADMIN"),
            ("dr_alice_radiology", "alice@hospital.org", "Password123!", "USER"),
            ("dr_bob_oncology", "bob@hospital.org", "Password123!", "USER")
        ]

        for username, email, pwd, role_name in demo_users:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                pub_pem, priv_pem = generate_ecdh_keypair()
                user = User(
                    user_id=str(uuid.uuid4()),
                    username=username,
                    email=email,
                    password_hash=hash_password(pwd),
                    role_id=roles_map[role_name],
                    public_key_pem=pub_pem,
                    encrypted_private_key=priv_pem,  # Demo key (in production encrypted with user master secret)
                    is_active=True
                )
                db.add(user)
                db.commit()
                db.refresh(user)

                # Add default access permission
                perm = AccessPermission(
                    permission_id=str(uuid.uuid4()),
                    user_id=user.user_id,
                    can_upload=True,
                    can_export_analytics=True,
                    max_shares_per_day=100,
                    is_restricted=False
                )
                db.add(perm)
                db.commit()
                print(f"    - Created demonstration account: {username} ({role_name})")

        print("[+] Demonstration users and ECDH keypairs seeded successfully.")

    finally:
        db.close()

if __name__ == "__main__":
    init_database()
