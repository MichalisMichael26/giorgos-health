# Giorgos Health

Private responsive Django app for family health tracking.

## Included
- Feeding schedule: 01:30, then every 3 hours
- Scheduled and actual feeding time
- Offered / consumed ml
- Formula and supplement fields
- Glucose readings with date and time
- Edit and delete
- Growth measurements
- Historical view by date range
- Daily timeline
- PDF export for the selected history period
- Responsive desktop, tablet and mobile interface
- Mobile bottom navigation
- PostgreSQL / Render ready

## PDF
The PDF export is generated on the server with ReportLab. The code attempts to use
a Unicode system font such as DejaVu Sans or Liberation Sans so Greek text can
be exported correctly.

## Security
Do not commit passwords, medical reports, API keys or private health data to GitHub.

## Website icon
The Giorgos Health logo is included as:
- Browser favicon
- Bookmark icon
- Apple touch icon
- PWA/mobile home-screen icon

## Meal entry defaults
- Actual time defaults to the scheduled time.
- Consumed amount defaults to 175 ml.
- Formula defaults to 5 scoops.
- Supplement defaults to 1 scoop.
All values remain editable.

## Automatic measurement date and meal defaults
- New measurements automatically use today's date, which remains editable.
- The Greek weekday is shown automatically from the selected date.
- Offered amount defaults to 175 ml and remains editable.


## Added health-management features
- 7 / 30 / 90 day charts for glucose, total daily ml, weight and length.
- Medication / supplement history with dose, unit and time.
- Medical appointments with in-app reminder window.
- Expanded "today" dashboard.
- One-click rolling 24-hour PDF report.
- Automatic night mode between 22:00 and 06:00 plus manual toggle.

The appointment reminders in this version are shown inside the app/dashboard.
True push, SMS or email notifications would require a separate notification provider or scheduled delivery service.


## Charts: all-time option
Analytics now supports 7 days, 30 days, 90 days and "Πάντα" (all available data).

## Report preview workflow
Reports no longer need to download immediately:
- 24-hour report opens as an HTML preview in a new tab.
- History-period report opens as an HTML preview in a new tab.
- Each report preview includes Print and Download PDF actions.


## Daily milk guide
The dashboard now includes an age-aware daily milk guide.

General age guide used:
- up to 2 weeks: 420–560 ml/day
- 2–8 weeks: 450–735 ml/day
- 2–3 months: 525–1,080 ml/day
- 3–5 months: 900–1,050 ml/day
- about 6 months: 840–960 ml/day
- 7–9 months: about 600 ml/day
- 10–12 months: about 400 ml/day
- 1–2 years: about 350–400 ml/day of whole cow's milk or another suitable milk drink

For babies after the first week until around 6 months, when a current weight exists, the app also shows a general weight-based guide of about 150–200 ml/kg/day.

A clinician-defined daily target can be saved in the child's profile. When present, it is displayed prominently and used as the main comparison target instead of the general guide.

These values are informational population guides and do not replace individualized advice from a pediatrician or dietitian.


## Appointment doctor presets
Medical appointments now offer three doctor/provider choices:
- Δρ Σάββας Σάββα - Παιδίατρος (Κλινική)
- Δρ Όλγα Γραφάκου (Κλινική ΝΑΜΙΙ)
- Άλλο, with free-text doctor and optional clinic/hospital

No database migration is required for this change because the existing doctor and clinic model fields are reused.


## Mobile report fix
- Report previews now open as dedicated pages in the same browser tab.
- This avoids mobile/PWA/new-tab session issues.
- Report previews use a normal Return link instead of window.close().
- Both HTML report previews show the Giorgos Health logo and the full name Giorgos Panayiotis Michael.
- Both generated PDF report types also show the Giorgos Health logo and the full name.


## Persistent login
- "Να παραμείνω συνδεδεμένος" is enabled by default.
- Remembered sessions last up to 90 days.
- The 90-day expiry refreshes whenever the app is used.
- Closing the browser does not end a remembered session.
- If the checkbox is disabled, the session ends with the browser session.
- Authentication remains enabled; private data is not made public.

## Advanced health features added

### Medical documents
- Discharge summaries, laboratory results, medical opinions, prescriptions and other documents.
- PDF/JPG/PNG up to 10 MB per file.
- Files are stored as PostgreSQL binary data rather than the Render ephemeral filesystem, so deploys do not remove them.
- Documents are included in the full ZIP backup.

### Vaccinations
- Vaccine name, dose, administration date, next dose and reminder days.
- Due reminders appear on the dashboard.

### WHO growth percentiles
- Boys 0–5 years.
- Official WHO simplified percentile field tables are embedded for P3, P15, P50, P85 and P97.
- Weight-for-age: WHO Child Growth Standards, birth to 5 years.
- Length-for-age: WHO Child Growth Standards, birth to 2 years.
- Height-for-age: WHO Child Growth Standards, 2 to 5 years.
- Head-circumference-for-age: WHO Child Growth Standards, birth to 5 years.
- The app reports percentile bands rather than claiming an exact percentile between published curves.

WHO source pages:
- https://www.who.int/tools/child-growth-standards/standards/weight-for-age
- https://www.who.int/toolkits/child-growth-standards/standards/length-height-for-age
- https://www.who.int/tools/child-growth-standards/standards/head-circumference-for-age

### Feeding performance and comparison
- Average consumed ml per feed.
- Percentage of offered volume consumed.
- Completed / partial / missed feeding counts.
- 7 / 30 / 90 days / all-time views.
- Dashboard today-vs-yesterday comparison and 7-day averages.

### Doctor View
- Read-only clinical summary with no editing controls.
- Today's feeding/glucose summary, 7-day glucose range/average, growth with WHO percentile bands, medications, symptoms, upcoming appointments and vaccines.

### Emergency card
- Full name and date of birth.
- User-entered medical instructions.
- Treating doctors, contact numbers and current feeding plan.
- Latest weight and glucose shown automatically.

### Audit log
- Records create/update/delete events after this upgrade.
- Stores user, time, object and field-level before/after values.
- Binary document content is intentionally excluded from audit payloads.

### Backup / Export
- Full ZIP: JSON + Excel + uploaded medical documents.
- Excel workbook: separate sheet per data category.
- PDF: printable full-data report.

### Mobile quick add
- Large + button on mobile.
- Quick links for Meal, Glucose, Medication, Symptom and Diaper.


## Functional Health Hub
The previous "Περισσότερα" concept is now presented as a visible "Υγεία" hub.

Mobile bottom navigation:
- Αρχική
- Γεύματα
- Γλυκόζη
- Υγεία
- Doctor

The floating "+" quick-add remains available for fast entry.

The Health hub groups:
- Emergency / Doctor View / Product & medicine checker
- Growth / WHO / medications / vaccines / appointments / symptoms / diapers
- Documents / history / 24h report / backup
- Analytics / feeding performance / profile / audit / checker rules

## Product / medicine checker
The checker is deliberately conservative:
- It does NOT label an unknown product or medicine as safe.
- It compares entered product names, ingredients, and medicine excipients against locally configured rules.
- Rules must be entered from clinician/pharmacist instructions.
- A no-match result means only "no configured restriction was found".
- Previously clinician/pharmacist-reviewed products can be saved in a separate registry.
- Medicine pages link to official Cyprus Pharmaceutical Services and EMA search sources.
- Checker rules and saved product/medicine reviews are included in full ZIP/Excel/PDF exports and audit history.


## Default checker restrictions
Migration 0006 seeds these active "avoid" rules:
- λακτόζη
- lactose
- ζάχαρη
- sugar

The rules apply to both foods and medicines/preparations and remain editable from the checker rules page.


## Structured emergency phone contacts
The Emergency Card now has separate phone fields for:
- father
- mother
- Dr Savvas Savva
- Dr Olga Grafakou
- optional other contact

Phone numbers are deliberately left blank until entered by the user. On mobile, populated numbers are tappable `tel:` links.


## Locked birth date and appointment ordering
- Giorgos' birth date is fixed to 27/06/2026.
- The profile and Emergency Card forms show the date but do not allow editing.
- The ChildProfile model enforces the fixed date on every save.
- Migration 0008 also corrects any existing ChildProfile row to 27/06/2026.
- Medical appointments are displayed newest date/time first on the appointments page.
- Dashboard upcoming appointment reminders remain chronological so the next appointment is still shown first.


## Checker wording simplified
The product/medicine checker now communicates the configured-rule behavior directly:
- If an active restriction is found in entered ingredients/excipients, it reports the matched restriction.
- If no restriction matches, it displays "Δεν εντοπίστηκε λακτόζη ή ζάχαρη".
- The previous long generic "Σημαντικό" warning was removed.
- A short scope note remains: the result is based on entered ingredients and active app rules.


## 2026 Daily Care Mega Upgrade

This package adds:

- Mobile barcode scanning using the phone camera.
- Barcode lookup against the local reviewed-product registry first, then Open Food Facts for food products.
- Ingredient-label camera capture and in-browser OCR using Tesseract.js (Greek + English).
- Ingredient checking is based on the entered/OCR ingredient list only. If there are no ingredients, the app asks for them instead of returning a green result.
- Label photo stored with the reviewed product in PostgreSQL.
- Reviewed products tabs: checked/confirmed, avoid, needs review, including last review date.
- Live next-meal countdown plus time since the last logged meal.
- Custom reminders for meal, medication, vaccine, measurement, lab, or other. Vaccine/appointment reminders continue to work.
- Structured numeric laboratory results plus trend charts.
- Optional photos on symptom and diaper entries, stored in PostgreSQL.
- Questions for the doctor and a Doctor Visit page.
- Hospital Mode focused on last glucose, last feed, medication, labs, emergency card, and quick entry.
- Privacy-controlled Emergency QR: sharing is OFF by default; the user chooses which sections appear.
- Global search across documents, labs, medications, appointments, products, symptoms, questions, and date-based records.
- Daily Health Summary and PDF.
- User roles: parent/full access and doctor/read-only. The doctor role is enforced server-side by middleware.
- Manual backup continues to provide ZIP/Excel/PDF and now includes stored product-label, symptom, and diaper photos.
- Optional S3-compatible cloud backup (including Cloudflare R2) with Backup history.
- Management command for scheduled cloud backup: `python manage.py cloud_backup`.
- `render-cron-backup.example.yaml` is an example only; it is intentionally not activated automatically because scheduled jobs/cloud credentials can have billing implications.

### Cloud backup environment variables

- `BACKUP_S3_ENDPOINT_URL`
- `BACKUP_S3_ACCESS_KEY_ID`
- `BACKUP_S3_SECRET_ACCESS_KEY`
- `BACKUP_S3_BUCKET`
- `BACKUP_S3_REGION` (optional, default `auto`)

### Camera/OCR notes

The scanner page loads `html5-qrcode` and `Tesseract.js` from public CDNs in the browser. Camera access requires HTTPS and user permission. If a camera or online barcode lookup is unavailable, manual barcode and ingredient entry remain available.


## Giorgos vaccination record seed
Migration `0010_seed_giorgos_vaccines.py` inserts, without duplicating exact existing entries:
- Hexyon — 1η δόση — 27/08/2026 — next date 27/10/2026
- Prevenar 20 — 1η δόση — 27/08/2026 — next date 27/10/2026
- Rotavirus — 1η δόση — 27/08/2026 — next date 27/10/2026

Hexyon is stored as one combined vaccine entry with a note that it covers DTaP + IPV + Hib + Hep B.

## Dr Savvas read-only account
The build creates/updates a read-only doctor account only when `DJANGO_DOCTOR_PASSWORD` is present.
Render environment variables:
- `DJANGO_DOCTOR_USERNAME=drsavvas`
- `DJANGO_DOCTOR_DISPLAY_NAME=Δρ Σάββας Σάββα`
- `DJANGO_DOCTOR_PASSWORD=<secret set in Render>`

The password is deliberately not stored in GitHub/source code.
The account is non-staff, non-superuser, and is assigned `doctor_readonly`.


## Laboratory values imported from discharge summary
Migration `0011_seed_discharge_lab_results.py` imports structured laboratory values from the discharge summary dated 16/09/2026:
- admission laboratory table (12/09/2026)
- blood gas values from 12/09/2026
- blood gas values from 14/09/2026
- repeat laboratory table from 16/09/2026
- ammonia 69 μg/dL with a note that its exact collection date is not separately stated

No reference ranges are invented. Units not printed in the discharge table are left blank.


## Laboratory comparison table
The laboratory page now defaults to a compact comparison matrix instead of individual cards:
- one test per row
- one date per column, newest first
- grouped into hematology, renal/electrolytes/glucose, liver/metabolic, and blood gases
- sticky test-name column on mobile
- horizontal swipe on small screens
- tap any value to edit it
- direct chart link per test
- no clinical colour-coding is inferred unless reference ranges are explicitly entered


## Diaper stool consistency quick choices
The diaper form now includes a ready-made consistency selector:
- Σχηματισμένη
- Μαλακή
- Πολτώδης
- Υδαρής / πολύ υδαρής («πορδοζούμι»)

The stored value remains the formal description `Υδαρής / πολύ υδαρής`.
Older free-text consistency values remain editable and are preserved.
