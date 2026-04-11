"""
CSV / PDF exports for supervisors and administrators (scoped like the web app).
"""

from __future__ import annotations

import csv
from io import BytesIO, StringIO

from django.db.models import Count, Q, QuerySet
from django.http import HttpResponse
from django.utils import translation
from django.utils.translation import gettext as _
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from accounts.models import District
from maternal.models import PregnancyRecord
from patients.models import Patient


def _patients_base_qs(user):
    qs = Patient.objects.select_related(
        'assigned_chw',
        'assigned_chw__user',
        'assigned_chw__district',
    )
    if user.is_superuser or getattr(user, 'is_admin_user', False):
        return qs
    if getattr(user, 'is_supervisor', False):
        d_ids = District.objects.filter(supervisor=user).values_list('id', flat=True)
        return qs.filter(assigned_chw__district_id__in=d_ids)
    return Patient.objects.none()


def patients_for_district_csv(user, district_id: int | None) -> QuerySet[Patient]:
    """Patients visible to the user; optional ``district_id`` when admin or supervised district."""
    qs = _patients_base_qs(user).order_by(
        'assigned_chw__district__name',
        'assigned_chw__user__last_name',
        'last_name',
        'first_name',
    )
    if district_id is None:
        return qs
    if user.is_superuser or getattr(user, 'is_admin_user', False):
        return qs.filter(assigned_chw__district_id=district_id)
    if getattr(user, 'is_supervisor', False):
        if District.objects.filter(pk=district_id, supervisor=user).exists():
            return qs.filter(assigned_chw__district_id=district_id)
        return Patient.objects.none()
    return Patient.objects.none()


def high_risk_pregnancies_qs(user):
    """Active pregnancies flagged HIGH risk; scoped to supervisor districts or all for admin."""
    base = (
        PregnancyRecord.objects.filter(is_active=True, risk_level=PregnancyRecord.RiskLevel.HIGH)
        .select_related(
            'patient',
            'patient__assigned_chw',
            'patient__assigned_chw__user',
            'patient__assigned_chw__district',
        )
        .order_by('expected_delivery_date')
    )
    if user.is_superuser or getattr(user, 'is_admin_user', False):
        return base
    if getattr(user, 'is_supervisor', False):
        d_ids = District.objects.filter(supervisor=user).values_list('id', flat=True)
        return base.filter(patient__assigned_chw__district_id__in=d_ids)
    return PregnancyRecord.objects.none()


def build_district_activity_csv(user, district_id: int | None) -> bytes:
    """UTF-8 with BOM for Excel; one row per patient with CHW / district / alert counts."""
    qs = patients_for_district_csv(user, district_id)
    qs = qs.annotate(
        open_alerts=Count(
            'alerts',
            filter=Q(alerts__resolved=False),
        ),
        active_preg=Count('pregnancies', filter=Q(pregnancies__is_active=True)),
    )

    buf = StringIO()
    w = csv.writer(buf)
    w.writerow(
        [
            _('District'),
            _('CHW'),
            _('Patient'),
            _('Village'),
            _('Sex'),
            _('Age'),
            _('Active pregnancies'),
            _('Open alerts'),
            _('Registered'),
        ]
    )
    for p in qs:
        hw = p.assigned_chw
        w.writerow(
            [
                hw.district.name if hw and hw.district_id else '',
                hw.user.get_full_name() or hw.user.username if hw else '',
                f'{p.first_name} {p.last_name}'.strip(),
                p.village or '',
                p.get_sex_display() if p.sex else '',
                p.age if p.age is not None else '',
                p.active_preg,
                p.open_alerts,
                p.created_at.isoformat() if p.created_at else '',
            ]
        )
    return ('\ufeff' + buf.getvalue()).encode('utf-8')


def build_high_risk_pdf_bytes(user, language: str | None) -> bytes:
    """Simple PDF table of high-risk active pregnancies."""
    lang = language or 'fr'
    buffer = BytesIO()
    with translation.override(lang):
        title = str(_('High-risk pregnancies (active register)'))
        headers = [
            str(_('Patient')),
            str(_('District')),
            str(_('LMP')),
            str(_('EDD')),
            str(_('Risk')),
        ]
        rows = [headers]
        for pr in high_risk_pregnancies_qs(user):
            pat = pr.patient
            dist = ''
            if pat.assigned_chw_id and pat.assigned_chw.district_id:
                dist = pat.assigned_chw.district.name
            rows.append(
                [
                    f'{pat.first_name} {pat.last_name}'.strip(),
                    dist,
                    str(pr.last_menstrual_period),
                    str(pr.expected_delivery_date),
                    str(pr.get_risk_level_display()),
                ]
            )

        styles = getSampleStyleSheet()
        doc = SimpleDocTemplate(buffer, pagesize=A4, title=title)
        story = [
            Paragraph(title, styles['Title']),
            Spacer(1, 14),
        ]
        if len(rows) == 1:
            story.append(Paragraph(str(_('No high-risk pregnancies in this scope.')), styles['Normal']))
        else:
            t = Table(rows, repeatRows=1)
            t.setStyle(
                TableStyle(
                    [
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#047857')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
                    ]
                )
            )
            story.append(t)
        doc.build(story)
    return buffer.getvalue()


def csv_district_response(user, district_id: int | None) -> HttpResponse:
    data = build_district_activity_csv(user, district_id)
    resp = HttpResponse(data, content_type='text/csv; charset=utf-8')
    resp['Content-Disposition'] = 'attachment; filename="communisante-district-activity.csv"'
    return resp


def pdf_high_risk_response(user, language: str | None) -> HttpResponse:
    data = build_high_risk_pdf_bytes(user, language)
    resp = HttpResponse(data, content_type='application/pdf')
    resp['Content-Disposition'] = 'attachment; filename="communisante-high-risk-pregnancies.pdf"'
    return resp
