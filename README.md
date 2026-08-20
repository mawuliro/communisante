# 🏥 CommuniSanté

> Plateforme communautaire de santé maternelle pour agents de santé communautaires (ASC) en Afrique francophone — suivi des grossesses, alertes de risque, triage IMCI, et travail hors-ligne avec synchronisation différée.

[![Python](https://img.shields.io/badge/Python-3.12+-blue)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.2-green)](https://djangoproject.com)
[![DRF](https://img.shields.io/badge/DRF-3.15-red)](https://www.django-rest-framework.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)](https://postgresql.org)
[![Railway](https://img.shields.io/badge/Railway-Deployed-purple)](https://railway.app)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

**Description** : _A powerful community app to help solve problems in our community._

---

## 📖 Sommaire

- [Aperçu](#aperçu)
- [Pourquoi CommuniSanté ?](#pourquoi-communisante-)
- [Fonctionnalités](#fonctionnalités)
- [Stack technique](#stack-technique)
- [Architecture](#architecture)
- [Installation](#installation)
- [Structure du projet](#structure-du-projet)
- [Modèles de données](#modèles-de-données)
- [API REST](#api-rest)
- [Travail hors-ligne](#travail-hors-ligne)
- [SMS — Africa's Talking](#sms--africas-talking)
- [Rôles & permissions](#rôles--permissions)
- [Internationalisation](#internationalisation)
- [Déploiement Railway](#déploiement-railway)
- [Licence](#licence)

---

## Aperçu

CommuniSanté est une application Django destinée aux **agents de santé communautaires (ASC)** exerçant en zones rurales d'Afrique subsaharienne, avec un focus sur la **santé maternelle** : suivi des grossesses, consultations prénatales (CPN), détection précoce des signes de danger, et alertes automatiques vers les superviseurs de district.

Le projet répond à un besoin concret : dans de nombreuses communautés rurales, les ASC n'ont **pas de connexion internet fiable**. CommuniSanté a donc été conçu dès le départ pour fonctionner **hors-ligne** (PWA + service worker + file d'attente de synchronisation), puis synchroniser les données dès qu'une connexion est disponible.

### Public cible

- **Agents de santé communautaires (ASC)** : enregistrent les patientes, suivent les grossesses, effectuent le triage
- **Superviseurs de district** : reçoivent les alertes critiques, suivent les CPN manquées, exportent les rapports
- **Administrateurs** : gèrent les districts, les protocoles de triage, et la configuration système

---

## Pourquoi CommuniSanté ?

### Le problème

En Afrique subsaharienne, la mortalité maternelle reste élevée (542 décès pour 100 000 naissances en moyenne, contre 9 dans les pays développés). Les causes principales :

- **Retard de détection** des grossesses à risque
- **CPN manquées** non détectées à temps
- **Communication lente** entre ASC ruraux et superviseurs de district
- **Pas de connectivité fiable** dans les villages

### La solution

| Défi | Réponse CommuniSanté |
|---|---|
| Pas d'internet | **PWA hors-ligne** + service worker + synchronisation différée |
| CPN manquées | **Alertes automatiques** générées quand une visite prévue n'est pas enregistrée |
| Signes de danger non détectés | **Triage IMCI** basé sur des protocoles médicaux versionnés et éditables |
| Communication lente | **SMS automatiques** aux superviseurs via Africa's Talking |
| Rapports difficiles à compiler | **Export CSV + PDF** générés à la volée par district |

---

## Fonctionnalités

### 👤 Gestion des patients

- Enregistrement des patientes (nom, âge, sexe, village)
- Affectation à un agent de santé communautaire (ASC)
- Recherche et filtrage par ASC, district, statut

### 🤰 Suivi des grossesses

- Enregistrement de grossesse avec date des dernières règles (DDR)
- Calcul automatique de la **date d'accouchement prévue (DPA)** : DDR + 280 jours
- Niveau de risque (faible / moyen / élevé) ajustable
- Une grossesse active par patiente (les anciennes sont archivées)
- **Consultations prénatales (CPN)** : enregistrement des visites avec calcul automatique des visites manquées

### 🚨 Système d'alertes

- **Alertes automatiques** générées par le système :
  - Visite prénatale manquée
  - Signe de danger détecté lors d'un triage
  - Grossesse à haut risque
- **Sévérité** en 4 niveaux : Low / Medium / High / Critical
- **Résolution** par les superviseurs avec traçabilité (qui, quand)
- **SMS automatique** aux superviseurs pour les alertes critiques (via Africa's Talking)

### 🩺 Triage IMCI

- **Protocoles de symptômes versionnés** (IMCI enfant, CPN mère) — éditables depuis l'admin Django
- **Symptômes pondérés** : chaque symptôme a un poids vers le score total
- **Règles de triage** : mapping score → recommandation (référence urgente, CPN planifiée, etc.)
- **Historique des évaluations** (SymptomCheck) avec symptômes sélectionnés, score, recommandation
- **Endpoints API** pour exécuter un triage à distance (`POST /api/triage/run/`)

### 📊 Dashboard & rapports

- **Dashboard adapté au rôle** :
  - ASC : résumé de ses patientes, CPN à venir, alertes
  - Superviseur : vue district, alertes non résolues, grossesses à risque
  - Admin : vue globale, gestion des districts
- **Export CSV** : patients par district
- **Export PDF** : grossesses à haut risque (généré avec reportlab, traduit selon la langue)

### 📱 PWA & hors-ligne

- **Service worker** : mise en cache des pages et assets
- **Web manifest** : installable comme app native
- **Synchronisation différée** : les formulaires soumis hors-ligne sont stockés en file d'attente (IndexedDB), puis synchronisés via `POST /sync/` quand la connexion revient
- **Notifications hors-ligne** dans l'UI : l'utilisateur sait que ses données sont en attente

### 📡 API REST

- Authentification **JWT** (SimpleJWT)
- Endpoints pour patients, triage, et schéma Swagger
- **Documentation Swagger** auto-générée (drf-spectacular)
- **Scoped comme l'app web** : un ASC ne voit que ses patientes, un superviseur son district

### 🌍 Internationalisation

- **Bilingue FR / EN** via Django i18n
- Locale par défaut : `fr-FR`
- Fuseau horaire par défaut : `Africa/Abidjan`
- Tous les modèles et templates utilisent `gettext_lazy`
- Script de compilation des traductions : `scripts/build_fr_django_po.py`

---

## Stack technique

| Catégorie | Technologie |
|---|---|
| **Framework** | Django 5.2 LTS |
| **API** | Django REST Framework 3.15 |
| **Auth** | Django auth + JWT (SimpleJWT 5.3) |
| **DB** | PostgreSQL 15 (prod), SQLite (dev) |
| **CSS** | Tailwind CSS 3.4 + crispy-tailwind |
| **Forms** | django-crispy-forms 2.1 |
| **PWA** | Service Worker + Web Manifest |
| **SMS** | Africa's Talking (HTTPS API) |
| **PDF** | reportlab 4.1 |
| **API docs** | drf-spectacular 0.27 (OpenAPI 3 + Swagger UI) |
| **CORS** | django-cors-headers 4.3 |
| **Server** | Gunicorn 21.2 (Railway) |
| **Static** | WhiteNoise 6.6 |
| **Error tracking** | Sentry SDK 1.44 (optionnel) |
| **Déploiement** | Railway (PostgreSQL managé + Gunicorn) |

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Navigateur (Client)                  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  PWA (installable)                                │  │
│  │  • Service Worker (cache + offline fallback)     │  │
│  │  • Web Manifest (icônes, theme color)            │  │
│  │  • IndexedDB (file d'attente hors-ligne)         │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  UI : Django Templates + Tailwind CSS 3         │  │
│  │  • Forms (crispy-forms + crispy-tailwind)        │  │
│  │  • Accessibilité (skip links, ARIA)              │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                            │
                            ▼ (HTTPS)
┌──────────────────────────────────────────────────────────┐
│              Railway (container Python)                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Gunicorn (2 workers, --preload, 120s timeout)    │  │
│  │  • WhiteNoise sert les fichiers statiques        │  │
│  │  • Migrations au preDeploy (railway.toml)        │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Django 5.2                                      │  │
│  │  • 7 apps (accounts, patients, maternal, ...)   │  │
│  │  • Django ORM (PostgreSQL)                       │  │
│  │  • DRF + drf-spectacular (API + Swagger)        │  │
│  │  • Service Worker + offline_sync view           │  │
│  │  • Africa's Talking SMS sender (urllib)         │  │
│  │  • reportlab (PDF exports)                       │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│   Railway PostgreSQL     │  │  Africa's Talking SMS API │
│  • 11 modèles principaux │  │  • HTTPS POST              │
│  • Migrations Django      │  │  • Numéros E.164 (+221...)  │
│  • Indexes optimisés      │  │  • No-op si pas de clé API │
└──────────────────────────┘  └──────────────────────────┘
```

---

## Installation

### Prérequis

- **Python 3.12+**
- **PostgreSQL 15+** (ou SQLite pour dev local)
- **Node.js 18+** (pour compiler Tailwind CSS)
- **virtualenv** ou **conda**

### Étapes

```bash
# 1. Cloner le dépôt
git clone https://github.com/mawuliro/communisante.git
cd communisante

# 2. Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/macOS
# ou : venv\Scripts\activate  # Windows

# 3. Installer les dépendances Python
pip install -r requirements.txt

# 4. (Optionnel) Installer les dépendances JS pour Tailwind
npm install

# 5. Configurer les variables d'environnement
cp .env.example .env
# Édite .env :
#   SECRET_KEY=une-chaîne-aléatoire-longue
#   DEBUG=True
#   ALLOWED_HOSTS=localhost,127.0.0.1
#   LANGUAGE_CODE=fr-FR
#   TIME_ZONE=Africa/Abidjan
#   (optionnel) AFRICASTALKING_USERNAME=...
#   (optionnel) AFRICASTALKING_API_KEY=...

# 6. Migrations
python manage.py migrate

# 7. Créer un superuser
python manage.py createsuperuser

# 8. Compiler le CSS Tailwind (si modifications)
npm run build:css
# ou : npx tailwindcss -c tailwind.config.cjs -i ./static/src/tailwind-input.css -o ./static/css/communisante.css --minify

# 9. Lancer le serveur de dev
python manage.py runserver
```

Ouvre <http://localhost:8000> — c'est prêt ! 🎉

### Accès à l'admin Django

- URL : <http://localhost:8000/admin/>
- Identifiants : ceux du superuser créé à l'étape 7

### Compiler les traductions FR

```bash
python3 scripts/build_fr_django_po.py
msgfmt -o locale/fr/LC_MESSAGES/django.mo locale/fr/LC_MESSAGES/django.po
```

---

## Structure du projet

```
communisante/
├── communisante/                # Projet Django principal
│   ├── settings/                # Settings splités (dev, prod, build_static)
│   ├── urls.py                  # Routes racines (+ i18n_patterns)
│   ├── wsgi.py                  # WSGI entry point
│   └── asgi.py                  # ASGI entry point
├── accounts/                    # App : auth, users, districts
│   ├── models.py                # User (custom), District, HealthWorker
│   ├── views.py                 # Login, logout, profile
│   ├── access.py                # Helpers de permissions
│   └── urls.py
├── patients/                    # App : enregistrement des patients
│   ├── models.py                # Patient (FK HealthWorker)
│   ├── forms.py                 # PatientForm (crispy)
│   ├── views.py                 # CRUD + scoping par ASC/district
│   ├── access.py                # patient_queryset_for_user, user_can_manage_patients
│   └── urls.py
├── maternal/                    # App : grossesses & CPN
│   ├── models.py                # PregnancyRecord, PrenatalVisit
│   ├── forms.py                 # PregnancyForm, PrenatalVisitForm
│   ├── services.py              # Logique métier (EDD, visites manquées)
│   ├── access.py                # pregnancy_queryset_for_user
│   └── urls.py
├── alerts/                      # App : alertes & SMS
│   ├── models.py                # Alert (type, severity, resolved)
│   ├── services.py               # Génération automatique d'alertes
│   ├── sms.py                   # Africa's Talking SMS sender
│   ├── access.py                # alert_queryset_for_user
│   └── urls.py
├── triage/                      # App : triage IMCI
│   ├── models.py                # SymptomProtocol, Symptom, TriageRule, SymptomCheck
│   ├── services.py              # save_symptom_check_from_triage
│   ├── management/              # Commandes d'admin pour seed protocoles
│   └── urls.py
├── dashboard/                   # App : dashboard + rapports
│   ├── views.py                 # DashboardView (role-aware)
│   ├── reporting.py             # CSV + PDF exports (reportlab)
│   └── urls.py
├── api/                         # App : API REST (DRF)
│   ├── serializers.py           # PatientSerializer, SymptomCheckSerializer
│   ├── views.py                 # PatientViewSet, TriageRunAPIView
│   └── urls.py                  # /api/token/, /api/triage/run/, /api/schema/swagger/
├── core/                        # App : vues transversales
│   ├── views.py                 # health, service_worker, web_manifest
│   ├── offline_sync.py          # Vue de sync hors-ligne (POST /sync/)
│   ├── context_processors.py    # Variables globales templates
│   └── urls.py                  # Home page
├── templates/                   # Templates HTML (Django + Tailwind)
│   ├── base.html                # Layout (skip link, ARIA, Tailwind)
│   ├── accounts/
│   ├── patients/
│   ├── maternal/
│   ├── alerts/
│   ├── triage/
│   ├── dashboard/
│   └── core/
├── static/
│   ├── css/
│   │   └── communisante.css     # Tailwind compilé (versionné)
│   ├── src/
│   │   └── tailwind-input.css   # Source Tailwind
│   ├── js/                       # Service worker, offline sync
│   └── img/
├── locale/
│   └── fr/LC_MESSAGES/django.po # Traductions françaises
├── scripts/
│   └── build_fr_django_po.py    # Génération du .po
├── requirements.txt
├── railway.toml                  # Config Railway (build + deploy)
├── Procfile                      # Heroku-compatible (legacy)
├── tailwind.config.cjs
├── package.json
├── .env.example
├── .gitignore
└── manage.py
```

---

## Modèles de données

Le schéma comporte **11 modèles principaux** répartis sur 6 apps.

### `accounts` — Authentification & organisation

```python
class User(AbstractUser):
    class Role(models.TextChoices):
        CHW = 'CHW', 'Community Health Worker'
        SUPERVISOR = 'SUPERVISOR', 'District Supervisor'
        ADMIN = 'ADMIN', 'System Administrator'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CHW)
    phone = models.CharField(max_length=20, blank=True)
    language = models.CharField(max_length=10, choices=[('en','English'),('fr','French')], default='fr')

class District(models.Model):
    name = models.CharField(max_length=255)
    supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='districts')

class HealthWorker(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    district = models.ForeignKey(District, on_delete=models.PROTECT, related_name='health_workers')
```

### `patients` — Patients

```python
class Patient(models.Model):
    class Sex(models.TextChoices):
        FEMALE = 'F', 'Female'
        MALE = 'M', 'Male'
        OTHER = 'O', 'Other'

    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    age = models.PositiveSmallIntegerField(null=True, blank=True)
    sex = models.CharField(max_length=1, choices=Sex.choices, blank=True)
    village = models.CharField(max_length=255, blank=True)
    assigned_chw = models.ForeignKey(HealthWorker, on_delete=models.PROTECT, related_name='patients')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['assigned_chw', 'created_at']),
        ]
```

### `maternal` — Grossesses & CPN

```python
class PregnancyRecord(models.Model):
    class RiskLevel(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='pregnancies')
    last_menstrual_period = models.DateField()  # DDR
    expected_delivery_date = models.DateField(editable=False)  # DPA = DDR + 280j (auto)
    risk_level = models.CharField(max_length=10, choices=RiskLevel.choices, default=RiskLevel.LOW)
    is_active = models.BooleanField(default=True)

class PrenatalVisit(models.Model):
    pregnancy = models.ForeignKey(PregnancyRecord, on_delete=models.CASCADE, related_name='visits')
    visit_date = models.DateField()
    performed_by = models.ForeignKey(HealthWorker, on_delete=models.PROTECT)
    notes = models.TextField(blank=True)
```

### `alerts` — Alertes

```python
class Alert(models.Model):
    class AlertType(models.TextChoices):
        MISSED_VISIT = 'MISSED_VISIT', 'Missed visit'
        DANGER_SIGN = 'DANGER_SIGN', 'Danger sign'
        HIGH_RISK = 'HIGH_RISK', 'High risk'

    class Severity(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical'

    type = models.CharField(max_length=20, choices=AlertType.choices)
    related_patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='alerts')
    related_pregnancy = models.ForeignKey(PregnancyRecord, on_delete=models.CASCADE, null=True, blank=True)
    severity = models.CharField(max_length=20, choices=Severity.choices)
    resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
```

### `triage` — Triage IMCI

```python
class SymptomProtocol(models.Model):
    name = models.CharField(max_length=255)  # e.g. "IMCI child v3"
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

class Symptom(models.Model):
    protocol = models.ForeignKey(SymptomProtocol, on_delete=models.CASCADE, related_name='symptoms')
    name = models.CharField(max_length=255)
    severity_weight = models.IntegerField()
    category = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

class TriageRule(models.Model):
    class Recommendation(models.TextChoices):
        URGENT = 'URGENT', 'Urgent referral'
        # ... autres
    protocol = models.ForeignKey(SymptomProtocol, on_delete=models.CASCADE)
    min_score = models.IntegerField()
    max_score = models.IntegerField()
    recommendation = models.CharField(max_length=20, choices=Recommendation.choices)

class SymptomCheck(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    symptoms_selected = models.ManyToManyField(Symptom)
    score = models.IntegerField()
    recommendation_given = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)
    performed_by = models.ForeignKey(HealthWorker, on_delete=models.PROTECT)
```

---

## API REST

### Authentification JWT

```bash
# Obtenir un token
curl -X POST https://ton-app.up.railway.app/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "...", "password": "..."}'

# Réponse :
# {"access": "eyJ...", "refresh": "..."}

# Rafraîchir le token
curl -X POST https://ton-app.up.railway.app/api/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "..."}'
```

### Endpoints

| Méthode | URL | Description | Auth |
|---|---|---|---|
| `POST` | `/api/token/` | Obtenir un JWT | Non |
| `POST` | `/api/token/refresh/` | Rafraîchir le JWT | Non |
| `GET` | `/api/patients/` | Liste des patients (scoped par rôle) | JWT |
| `GET` | `/api/patients/{id}/` | Détail d'un patient | JWT |
| `POST` | `/api/triage/run/` | Exécuter un triage | JWT |
| `GET` | `/api/schema/` | Schéma OpenAPI 3 | Non |
| `GET` | `/api/schema/swagger/` | UI Swagger interactive | Non |
| `POST` | `/sync/` | Synchroniser les données hors-ligne | JWT |

### Exemple : exécuter un triage

```bash
curl -X POST https://ton-app.up.railway.app/api/triage/run/ \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{
    "protocol_id": 1,
    "patient_id": 42,
    "symptom_ids": [1, 3, 7]
  }'

# Réponse :
# {
#   "id": 123,
#   "score": 15,
#   "recommendation_given": "Urgent referral",
#   "date": "2026-08-20T12:00:00Z",
#   "symptom_ids": [1, 3, 7]
# }
```

### Documentation Swagger

Une fois le serveur lancé, ouvrez :
- **Schéma OpenAPI** : <http://localhost:8000/api/schema/>
- **Swagger UI** : <http://localhost:8000/api/schema/swagger/>

---

## Travail hors-ligne

### Architecture

```
┌──────────────────────────────────────────────────────────┐
│              Navigateur (zone rurale)                   │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Service Worker (sw.js)                          │  │
│  │  • Cache les pages visitées                      │  │
│  │  • Sert le fallback hors-ligne                  │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  IndexedDB                                       │  │
│  │  • File d'attente des formulaires soumis         │  │
│  │  • Chaque item : {kind, payload, timestamp}     │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                            │
                            ▼ (quand connexion disponible)
┌──────────────────────────────────────────────────────────┐
│              Django : POST /sync/                       │
│  • Reçoit la file JSON                                 │
│  • Applique chaque item via les forms Django           │
│  • Retourne {ok: true/false} par item                  │
└──────────────────────────────────────────────────────────┘
```

### Types d'opérations hors-ligne supportées

- **Création de patient** (`kind: patient_create`)
- **Mise à jour de patient** (`kind: patient_update`)
- **Création de grossesse** (`kind: pregnancy_create`)
- **Mise à jour de grossesse** (`kind: pregnancy_update`)
- **Création de CPN** (`kind: prenatal_visit_create`)
- **Résolution d'alerte** (`kind: alert_resolve`)

### Format de synchronisation

```json
POST /sync/
Authorization: Bearer eyJ...
Content-Type: application/json

{
  "items": [
    {
      "kind": "patient_create",
      "payload": {
        "first_name": "Awa",
        "last_name": "Doe",
        "age": 25,
        "sex": "F",
        "village": "Kpalimé",
        "assigned_chw": 3
      }
    },
    {
      "kind": "pregnancy_create",
      "payload": {
        "patient_id": 42,
        "last_menstrual_period": "2026-01-15"
      }
    }
  ]
}
```

Réponse :

```json
{
  "results": [
    {"ok": true, "patient_id": 42},
    {"ok": true, "pregnancy_id": 17}
  ]
}
```

---

## SMS — Africa's Talking

### Configuration

Le système envoie des SMS aux superviseurs pour les alertes critiques via **Africa's Talking** (gratuit jusqu'à 1000 SMS/mois en sandbox).

Variables d'environnement :

```env
AFRICASTALKING_USERNAME=your_username
AFRICASTALKING_API_KEY=your_api_key
```

> ⚠️ Sans ces variables, `send_sms()` est un **no-op** (ne fait rien, retourne `False`). C'est utile en dev pour ne pas envoyer de vrais SMS.

### Numéros E.164

Les numéros doivent être au format **E.164** avec indicatif pays :
- Sénégal : `+221 77 123 45 67`
- Côte d'Ivoire : `+225 07 12 34 56 78`
- Togo : `+228 90 12 34 56`

### Limitation

Les messages sont tronqués à 480 caractères (limite pratique des SMS GSM).

---

## Rôles & permissions

### Hiérarchie des rôles

```
┌─────────────────────────────────────────────┐
│  ADMIN (System Administrator)               │
│  • Gère tout : districts, ASC, protocoles   │
│  • Voit tous les patients et alertes       │
│  • Télécharge tous les rapports            │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│  SUPERVISOR (District Supervisor)           │
│  • Gère les ASC de son district             │
│  • Voit les patients de son district        │
│  • Reçoit les alertes de son district      │
│  • Télécharge les rapports de son district  │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│  CHW (Community Health Worker)              │
│  • Gère ses patients uniquement             │
│  • Enregistre les grossesses et CPN         │
│  • Effectue les triages                     │
│  • Voit ses propres alertes                 │
└─────────────────────────────────────────────┘
```

### Helpers de permissions

Chaque app a un module `access.py` qui centralise la logique de scoping :

```python
# patients/access.py
def patient_queryset_for_user(user):
    """Retourne le queryset de patients visibles par l'utilisateur."""
    if user.is_superuser or user.is_admin_user:
        return Patient.objects.all()
    if user.is_supervisor:
        # Patients des ASC de son district
        district_ids = District.objects.filter(supervisor=user).values_list('id', flat=True)
        return Patient.objects.filter(assigned_chw__district_id__in=district_ids)
    if user.is_chw:
        return Patient.objects.filter(assigned_chw__user=user)
    return Patient.objects.none()

def user_can_manage_patients(user):
    """L'utilisateur peut-il créer/modifier des patients ?"""
    return user.is_authenticated and user.role in ['CHW', 'SUPERVISOR', 'ADMIN']
```

---

## Internationalisation

### Configuration

- **Langue par défaut** : `fr-FR`
- **Fuseau horaire** : `Africa/Abidjan` (UTC+0)
- **Langues disponibles** : Français (`fr`), Anglais (`en`)

### URLs avec préfixe de langue

Les URLs sont wrappées dans `i18n_patterns` :

- `/fr/patients/` → page patients en français
- `/en/patients/` → page patients en anglais
- `/fr/accounts/login/` → connexion en français

### Compilation des traductions

```bash
# Générer le fichier .po à partir des chaînes marquées avec _()
python3 scripts/build_fr_django_po.py

# Compiler le .po en .mo (fichier binaire utilisé par Django)
msgfmt -o locale/fr/LC_MESSAGES/django.mo locale/fr/LC_MESSAGES/django.po
```

### Marquer une chaîne pour traduction

```python
from django.utils.translation import gettext_lazy as _

class Patient(models.Model):
    first_name = models.CharField(max_length=150, verbose_name=_('first name'))
    # Le mot "first name" sera traduit automatiquement selon la langue
```

---

## Déploiement Railway

### Architecture Railway

```
┌──────────────────────────────────────────────────────────┐
│                    Railway                              │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Build phase                                     │  │
│  │  • pip install -r requirements.txt              │  │
│  │  • python manage.py collectstatic --noinput      │  │
│  │    (settings=communisante.settings.build_static) │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  preDeploy phase                                 │  │
│  │  • python manage.py migrate --noinput            │  │
│  │    (settings=communisante.settings.prod)         │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Run phase                                       │  │
│  │  • gunicorn communisante.wsgi:application        │  │
│  │    --bind 0.0.0.0:$PORT --workers 2 --preload    │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  PostgreSQL (Railway add-on)                     │  │
│  │  • DATABASE_URL injectée automatiquement         │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### Étapes de déploiement

1. **Forkez** le repo sur GitHub
2. **Connectez** le repo à Railway : <https://railway.app/new>
3. **Ajoutez** un add-on PostgreSQL sur Railway
4. **Configurez** les variables d'environnement (onglet Variables) :

| Variable | Valeur |
|---|---|
| `SECRET_KEY` | `openssl rand -base64 32` |
| `DATABASE_URL` | (auto par Railway Postgres) |
| `ALLOWED_HOSTS` | `.up.railway.app` |
| `CSRF_TRUSTED_ORIGINS` | `https://ton-app.up.railway.app` |
| `CORS_ALLOWED_ORIGINS` | `https://ton-app.up.railway.app` |
| `AFRICASTALKING_USERNAME` | (optionnel) |
| `AFRICASTALKING_API_KEY` | (optionnel) |
| `SENTRY_DSN` | (optionnel) |

5. Railway build + deploy automatiquement

### Healthcheck

- **Endpoint** : `/health/`
- Pas de healthcheck HTTP configuré dans `railway.toml` (évite les faux échecs si l'endpoint réagit mal)
- Si vous voulez en activer un : Railway → Service → Settings → Healthcheck Path = `/health/`

### Bonnes pratiques Railway

- ✅ `collectstatic` au build, pas au runtime (évite de ralentir les healthchecks)
- ✅ Migrations au `preDeployCommand` (DB only, pas besoin de FS)
- ✅ `--preload` pour Gunicorn (charge Django une fois avant le fork des workers)
- ✅ Pas de `release:` dans le Procfile (non fiable sur Railway)

---

## Licence

MIT — voir le fichier [LICENSE](LICENSE).

---

## 👥 Équipe

- **Développement** : Mawulikplimi Roland ([@mawuliro](https://github.com/mawuliro))
- **Localisation** : Lomé, Togo 🇹🇬

---

## 🙏 Remerciements

- **Django** (framework) — <https://djangoproject.com>
- **Django REST Framework** — <https://www.django-rest-framework.org>
- **Tailwind CSS** — <https://tailwindcss.com>
- **Africa's Talking** (SMS) — <https://africastalking.com>
- **Railway** (hébergement) — <https://railway.app>
- **reportlab** (génération PDF) — <https://reportlab.com>
- **drf-spectacular** (OpenAPI) — <https://drf-spectacular.readthedocs.io>

---

<p align="center">
  Fait avec ❤️ à Lomé, Togo 🇹🇬<br>
  Pour la santé maternelle en Afrique subsaharienne
</p>
