"""
AI-Based Suspicious Activity Monitoring Sentry (Phase 10)
Combines unsupervised Scikit-learn Isolation Forest machine learning with a
deterministic heuristic rule engine to detect:
- Nocturnal bulk exfiltration / anomalous downloads
- Brute-force decryption / key guessing attacks
- Credential stuffing / rapid authentication failures
- Unusual API velocity spikes
"""
import uuid
import numpy as np
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sklearn.ensemble import IsolationForest

from app.models.db_models import SecurityAlert, AuditLog, LoginHistory, User
from app.config import settings

class AISecuritySentry:
    _instance = None
    _model: Optional[IsolationForest] = None

    def __init__(self):
        self.init_model()

    @classmethod
    def get_instance(cls) -> "AISecuritySentry":
        if cls._instance is None:
            cls._instance = AISecuritySentry()
        return cls._instance

    def init_model(self):
        """Initializes and trains the Isolation Forest on standard baseline clinician behavior."""
        # Baseline training data: 200 normal operational samples + 10 edge samples
        rng = np.random.default_rng(42)
        
        # Features: [hour_of_day, is_nocturnal, failed_logins, failed_decryptions, downloads, req_rate, priv_level]
        # Normal shifts: 08:00 to 19:00
        normal_hours = rng.uniform(8.0, 19.0, size=200)
        normal_nocturnal = np.zeros(200)
        normal_failed_logins = rng.choice([0, 0, 0, 1], size=200)
        normal_failed_decryptions = rng.choice([0, 0, 0, 0, 1], size=200)
        normal_downloads = rng.integers(0, 3, size=200)
        normal_req_rate = rng.integers(1, 15, size=200)
        normal_priv = rng.choice([1, 1, 1, 2], size=200)

        X_normal = np.column_stack([
            normal_hours,
            normal_nocturnal,
            normal_failed_logins,
            normal_failed_decryptions,
            normal_downloads,
            normal_req_rate,
            normal_priv
        ])

        # A few synthetic anomalies to establish boundary
        anom_hours = np.array([2.0, 3.5, 1.0, 23.5, 4.0])
        anom_nocturnal = np.ones(5)
        anom_failed_logins = np.array([5, 8, 0, 1, 6])
        anom_failed_decryptions = np.array([4, 6, 5, 0, 3])
        anom_downloads = np.array([8, 12, 10, 15, 7])
        anom_req_rate = np.array([45, 60, 50, 40, 55])
        anom_priv = np.array([1, 1, 1, 1, 1])

        X_anom = np.column_stack([
            anom_hours,
            anom_nocturnal,
            anom_failed_logins,
            anom_failed_decryptions,
            anom_downloads,
            anom_req_rate,
            anom_priv
        ])

        X_train = np.vstack([X_normal, X_anom])

        self._model = IsolationForest(
            n_estimators=100,
            contamination=settings.ANOMALY_CONTAMINATION,
            random_state=42
        )
        self._model.fit(X_train)

    def evaluate_heuristics(self, features: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Deterministic rule-based heuristics providing guaranteed deterministic triggers.
        """
        hour = features.get("hour_of_day", 12.0)
        is_nocturnal = features.get("is_nocturnal", (hour >= 23 or hour <= 5))
        failed_logins = features.get("failed_logins_recent", 0)
        failed_decryptions = features.get("failed_decryptions_recent", 0)
        downloads = features.get("download_count_recent", 0)
        req_rate = features.get("request_rate_recent", 1)

        # 1. Nocturnal Bulk Download Exfiltration Rule
        if is_nocturnal and downloads >= 3:
            return {
                "alert_type": "NOCTURNAL_BULK_DOWNLOAD",
                "severity": "CRITICAL",
                "risk_score": 94.5,
                "reason": f"Anomalous nocturnal bulk download burst ({downloads} scans requested during non-clinical hours {hour:.1f}:00 UTC)."
            }

        # 2. Brute-Force Decryption / Key Guessing Rule
        if failed_decryptions >= 3:
            return {
                "alert_type": "BRUTE_FORCE_DECRYPTION",
                "severity": "HIGH",
                "risk_score": 89.0,
                "reason": f"Detected {failed_decryptions} consecutive cryptographic decryption failures. Possible key-guessing or ciphertext tampering attempt."
            }

        # 3. Credential Stuffing Rule
        if failed_logins >= 4:
            return {
                "alert_type": "CREDENTIAL_STUFFING",
                "severity": "HIGH",
                "risk_score": 85.5,
                "reason": f"High frequency of failed authentication attempts ({failed_logins} failures). Possible credential stuffing or password spray attack."
            }

        # 4. Abnormal API Rate Burst Rule
        if req_rate >= 35:
            return {
                "alert_type": "VELOCITY_SPIKE",
                "severity": "MEDIUM",
                "risk_score": 72.0,
                "reason": f"Unusually high activity velocity ({req_rate} requests/min) exceeding clinical interaction baseline."
            }

        return None

    def analyze_event(
        self,
        features: Dict[str, Any],
        user_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Combines deterministic rules with Isolation Forest anomaly score.
        Persists a SecurityAlert to DB if risk exceeds threshold.
        """
        # 1. Evaluate deterministic heuristics
        heuristic_hit = self.evaluate_heuristics(features)

        # 2. Evaluate Isolation Forest ML pipeline
        hour = features.get("hour_of_day", 12.0)
        is_nocturnal = 1.0 if (hour >= 23 or hour <= 5) else 0.0
        feature_vec = np.array([[
            hour,
            is_nocturnal,
            float(features.get("failed_logins_recent", 0)),
            float(features.get("failed_decryptions_recent", 0)),
            float(features.get("download_count_recent", 0)),
            float(features.get("request_rate_recent", 1)),
            float(features.get("privilege_level", 1))
        ]])

        raw_score = float(self._model.decision_function(feature_vec)[0])
        is_ml_outlier = bool(self._model.predict(feature_vec)[0] == -1)

        # Transform raw score to [0 - 100] risk scale
        # Normal scores typically +0.15 to +0.25; outliers negative
        ml_risk = max(5.0, min(99.0, (0.20 - raw_score) * 150.0))

        if heuristic_hit:
            alert_type = heuristic_hit["alert_type"]
            severity = heuristic_hit["severity"]
            risk_score = heuristic_hit["risk_score"]
            reason = heuristic_hit["reason"]
            source = "RULE_ENGINE_AND_ISOLATION_FOREST"
            is_anomaly = True
        else:
            is_anomaly = is_ml_outlier or (ml_risk >= 60.0)
            if ml_risk >= 80.0:
                severity = "HIGH"
            elif ml_risk >= 60.0:
                severity = "MEDIUM"
            else:
                severity = "LOW"
            
            alert_type = "BEHAVIORAL_ANOMALY" if is_anomaly else "NORMAL_ACTIVITY"
            risk_score = round(ml_risk, 2)
            reason = f"Isolation Forest detected behavioral drift (ML score: {raw_score:.3f})." if is_anomaly else "Behavior consistent with authorized clinical baseline."
            source = "ISOLATION_FOREST_UNSUPERVISED"

        result = {
            "is_anomaly": is_anomaly,
            "risk_score": risk_score,
            "severity": severity,
            "alert_type": alert_type,
            "reason": reason,
            "source": source,
            "raw_ml_score": round(raw_score, 4),
            "features_analyzed": features
        }

        # 3. Persist Alert if anomaly detected and DB session provided
        if is_anomaly and db is not None:
            alert_record = SecurityAlert(
                alert_id=str(uuid.uuid4()),
                user_id=user_id,
                alert_type=alert_type,
                severity=severity,
                risk_score=risk_score,
                detection_source=source,
                reason=reason,
                is_resolved=False,
                created_at=datetime.now(timezone.utc)
            )
            db.add(alert_record)
            db.commit()
            db.refresh(alert_record)
            result["alert_id"] = alert_record.alert_id

        return result
