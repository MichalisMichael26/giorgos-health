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
