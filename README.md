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
