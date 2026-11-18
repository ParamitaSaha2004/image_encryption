"""
Elliptic Curve Cryptography (ECC) Key Agreement Engine
Implements Elliptic Curve Diffie-Hellman (ECDH) over the NIST P-256 (secp256r1) curve.
Handles public/private keypair generation, PEM serialization, public key validation,
and shared secret computation.
"""
from typing import Tuple, Optional, Union
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

class ECDHError(Exception):
    """Exception raised for ECDH key operations failures."""
    pass

class ECDHManager:
    CURVE = ec.SECP256R1()  # NIST P-256 standard curve

    @classmethod
    def generate_keypair(cls) -> Tuple[str, str]:
        """
        Generates a new NIST P-256 keypair.
        Returns (public_key_pem, private_key_pem).
        """
        private_key = ec.generate_private_key(cls.CURVE)
        public_key = private_key.public_key()

        priv_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode("utf-8")

        pub_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode("utf-8")

        return pub_pem, priv_pem

    @classmethod
    def load_private_key(cls, pem_data: Union[str, bytes], password: Optional[bytes] = None) -> ec.EllipticCurvePrivateKey:
        """Loads a PEM-encoded private key."""
        if isinstance(pem_data, str):
            pem_data = pem_data.encode("utf-8")
        try:
            return serialization.load_pem_private_key(pem_data, password=password)
        except Exception as e:
            raise ECDHError(f"Failed to parse private key: {str(e)}")

    @classmethod
    def load_public_key(cls, pem_data: Union[str, bytes]) -> ec.EllipticCurvePublicKey:
        """Loads and validates a PEM-encoded public key."""
        if isinstance(pem_data, str):
            pem_data = pem_data.encode("utf-8")
        try:
            return serialization.load_pem_public_key(pem_data)
        except Exception as e:
            raise ECDHError(f"Failed to parse public key: {str(e)}")

    @classmethod
    def compute_shared_secret(
        cls, 
        private_key: ec.EllipticCurvePrivateKey, 
        peer_public_key: ec.EllipticCurvePublicKey
    ) -> bytes:
        """
        Computes the raw ECDH shared secret Z = d_local * Q_peer over curve P-256.
        Returns a 32-byte shared secret coordinate.
        """
        try:
            shared_secret = private_key.exchange(ec.ECDH(), peer_public_key)
            return shared_secret
        except Exception as e:
            raise ECDHError(f"ECDH key exchange failed: {str(e)}")

    @classmethod
    def exchange_from_pems(cls, local_priv_pem: str, peer_pub_pem: str) -> bytes:
        """Convenience method to compute shared secret directly from PEM strings."""
        priv_key = cls.load_private_key(local_priv_pem)
        peer_pub = cls.load_public_key(peer_pub_pem)
        return cls.compute_shared_secret(priv_key, peer_pub)
