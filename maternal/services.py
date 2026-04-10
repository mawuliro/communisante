"""
Lightweight clinical hints for the UI (not a substitute for protocol training).
"""


def bp_follow_up_suggested(systolic, diastolic) -> bool:
    """True when BP crosses common ANC referral thresholds (example values from project settings)."""
    from django.conf import settings

    sys_thr = getattr(settings, 'HIGH_RISK_BP_SYSTOLIC', 140)
    dia_thr = getattr(settings, 'HIGH_RISK_BP_DIASTOLIC', 90)
    if systolic is not None and systolic >= sys_thr:
        return True
    if diastolic is not None and diastolic >= dia_thr:
        return True
    return False
