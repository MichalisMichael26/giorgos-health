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


## Hard read-only doctor fix
The configured doctor username (`DJANGO_DOCTOR_USERNAME`, default `drsavvas`) is now ALWAYS treated as `doctor_readonly`, even if the role profile is missing or was accidentally changed.

Enforcement layers:
1. Build deploy repairs/creates the `UserAccessProfile` role as doctor_readonly.
2. Middleware rejects every non-safe modifying HTTP request for the doctor account, except logout.
3. Middleware redirects doctor GET requests away from create/edit/delete/action pages.
4. The UI displays a read-only banner, removes the mobile quick-add button, disables mutation links/forms, and preserves read-only data display.
5. Doctor login redirects directly to Doctor View.

This is server-side enforcement; hiding buttons is only an additional UX layer.


## Hospital Mode — latest labs readability fix
Hospital Mode now shows the complete most-recent laboratory date as a compact table:
`Test | Result | Unit`.

The latest collection date is displayed once in the panel header. The table has an internal scroll area,
a sticky header, links each test to its trend chart, and avoids automatic clinical colour-coding.


## Mobile Web Push Notifications

The app now supports real Web Push notifications for custom Health Reminders.

### What it does
- A parent can open `Υγεία → Υπενθυμίσεις` and tap `🔔 Ενεργοποίηση`.
- The browser registers `/service-worker.js`.
- A VAPID key pair is generated automatically once and stored in PostgreSQL.
- The current device's push subscription is stored in PostgreSQL.
- `python manage.py dispatch_push_reminders` sends due reminders to all active non-doctor devices.
- Notifications request the device's normal notification sound and vibration (`silent: false`).
- Tapping the notification opens `/reminders/`.
- A reminder can notify at the exact time or 5/10/15/30/60 minutes before.
- It can optionally send a second notification 5/10/15/30/60 minutes after the due time when the reminder is still incomplete.
- A `🧪 Δοκιμή` button sends an immediate test push to the current user's subscribed devices.
- Dr Savvas/read-only doctor accounts cannot subscribe or modify push settings.

### iPhone / iPad
On supported iOS/iPadOS versions, Web Push for web apps requires the site to be added to the Home Screen and opened from that Home Screen icon. The reminders page detects this and shows a setup note.

### Server-side dispatch
A Service Worker receives pushes, but the server still needs to *send* them at the right time.
The project includes:
- management command: `python manage.py dispatch_push_reminders`
- example Render cron config: `render-push-cron.example.yaml`

For near-minute reminders, schedule the command once per minute.

The active `render.yaml` was intentionally not changed to add a paid/extra Cron service automatically. Configure the cron job in Render after deciding on the plan/billing.

### Security
- PushSubscription endpoint/keys and the VAPID private key are internal and are explicitly excluded from Audit Log snapshots.
- They are not added to JSON/Excel/ZIP exports.
- The VAPID private key is generated inside the deployed app and stored in PostgreSQL, not committed to GitHub.


## Web Push send fix
The first push implementation stored the VAPID private key as PEM text in PostgreSQL
but passed that PEM string directly to `pywebpush.webpush()`. `pywebpush` treats a
non-file string as encoded DER/raw key material, so delivery could fail even with a valid
active device subscription.

The sender now parses the stored PEM explicitly with `py_vapid.Vapid.from_pem()` and
passes a Vapid object to `webpush()`.

The Test Push endpoint now distinguishes:
- no active subscribed device
- expired subscription (404/410)
- authentication rejection (401/403)
- other HTTP delivery failures
- pre-network/key processing failures

No push endpoint or subscription encryption key is returned to the browser.


## Automatic reminder rules
The app now creates/synchronizes these rules automatically:

1. **Fixed feeding schedule** — push 11 minutes before:
   `01:30, 04:30, 07:30, 10:30, 13:30, 16:30, 19:30, 22:30`.
   The repetitive schedule rows are kept out of the main reminder-card list to avoid clutter.

2. **Appointments** — push exactly 24 hours before the appointment, at the same clock time.
   Existing and future scheduled appointments are synchronized automatically.

3. **Low consumed meal rule** — this is a user-defined operational rule, not a medical threshold:
   when a MealEntry is saved with `consumed_ml <= 50`, the app creates a one-time reminder
   exactly 60 minutes after the actual meal time (falling back to scheduled time).
   If that meal is later edited above 50 ml, the automatic follow-up reminder is removed.

Automatic reminders have stable `source_key` identifiers so repeated syncs cannot create duplicates.
The push dispatcher runs `sync_all_automatic_reminders()` before each dispatch.


## Reminder page visibility fix
The reminder page now synchronizes automatic reminders when a parent opens it,
then displays the next five automatic notification times in a compact panel.

The repetitive meal schedule is no longer mistaken for "no reminders":
- automatic reminders appear under `Επόμενες αυτόματες υπενθυμίσεις`
- manual reminders remain in a separate list
- the empty state now says only that there are no *manual* reminders

The Dr Savvas/read-only doctor account:
- never registers a push subscription
- is excluded from all push delivery
- does not see push activation/test controls
- does not run automatic-reminder synchronization from a GET request


## Native Android alarm API
Authenticated endpoint: `/native/alarm-schedule/`

It uses the existing Django login session and returns the next 14 days of active reminders,
including the exact `notify_at_epoch_ms` timestamp needed by Android AlarmManager.

The `drsavvas` / doctor-readonly account always receives `enabled: false` and zero alarm items.


## Specialized feeding guide safety update
The dashboard no longer uses general population formula-volume guides as Giorgos' active target.

- The 150–200 ml/kg/day weight reference remains visible only as a standard-formula population reference.
- The age-based volume guide is also explicitly labelled as a standard-formula reference.
- Giorgos' current intake is not compared against those population ranges.
- A progress bar is shown only when a clinician-specific ml/24h target is entered in the Child Profile.
- The dashboard explains that Giorgos receives energy-fortified feeding and that the metabolic/clinical team's individualized target takes precedence.


## Dual feeding targets
Giorgos Health now separates individualized 24-hour volume targets into:
- **With Maxijul**
- **Without Maxijul**

The old generic clinician target fields remain in the database for backwards compatibility,
but are hidden from the current UI and are NOT automatically copied into either new plan.
This avoids assuming that an old target belonged to the fortified plan.

Daily behavior:
- all recorded feeds contain Maxijul -> use the **With Maxijul** target, if entered;
- all recorded feeds contain no Maxijul -> use the **Without Maxijul** target, if entered;
- a mixture of both -> label the day **Mixed** and apply no automatic target;
- no feeds yet -> use the configured current-plan toggle only to select which plan is expected.

The dashboard also shows Maxijul scoops, estimated grams, kcal and carbohydrate from the
configured scoop/nutrition values. These estimates do not convert Maxijul calories into
"equivalent formula ml".


### Maxijul intake estimate
The app distinguishes between:
- scoops added to prepared bottles;
- estimated scoops actually consumed.

When offered_ml is available, consumed Maxijul is estimated proportionally:
`entered scoops × consumed_ml / offered_ml`, capped at 100% of the entered scoop amount.
This assumes the powder is evenly mixed through the prepared bottle.


## 11-minute meal reminders
Automatic fixed feeding reminders now use an exact lead time of **11 minutes** before the scheduled meal.
Existing generated meal reminders are updated by the normal automatic reminder sync; when their timing changes,
their push-delivery flags are reset so the new 11-minute schedule can be delivered.
The native Android alarm schedule API reads the same `notify_minutes_before` value, so it inherits the 11-minute timing.


## History timeline Maxijul
Meal entries in the existing daily History timeline now show Maxijul alongside formula when it was recorded.
Example: `Formula: 5 · Maxijul: 1 scoop`.
No meal-duration tracking was added.


## Feeding Performance template fix
Fixed an unclosed `{% if milk_guide_today %}` block in `templates/feeding/performance.html`.
This caused the Feeding Performance page to fail rendering after the dual Maxijul target update.


## 48-hour clinical print report
A new dashboard shortcut opens a print-friendly **48ωρος Κλινικός Φάκελος**.

It includes:
- child identity and age;
- latest growth/weight and recent growth history;
- known allergies (new ChildProfile field);
- emergency instructions, current feeding plan, feeding targets and treating doctors;
- active safety/restriction rules;
- meals and Maxijul for the rolling last 48 hours;
- glucose measurements and 48-hour min/max/average;
- medications/supplements;
- symptoms;
- diapers/stools;
- laboratory results from the 48-hour window, with the latest available lab panel as fallback;
- full vaccine history;
- upcoming medical appointments.

The page is optimized for browser printing and **Print / Save as PDF**.
It reproduces stored data and does not add clinical interpretation.


## Allergies in Health menu
The Health hub now has a prominent **Allergies** card.
The dedicated Allergies page:
- shows the ChildProfile `known_allergies` field;
- clearly separates allergies from active food/medicine restriction rules;
- lets parent users jump to profile editing;
- remains read-only for the configured Dr Savvas account through the existing server-side read-only protection.


## Upcoming vaccine doses
The Vaccines page now separates:
- **administered vaccine history** at the top;
- **confirmed upcoming doses** underneath.

Upcoming doses are derived only from the existing `VaccineEntry.next_date` values.
No future dates are invented. If a later administration of the same vaccine is recorded
on or after the previous `next_date`, that older planned dose is automatically removed
from the upcoming list.


## Dashboard / diapers / push reliability update
- Dashboard now shows **meal-by-meal yesterday vs today** for every fixed feeding slot.
- Dashboard hero now has **+ Πάνα** beside **+ Γλυκόζη**.
- Diaper list no longer loads every photo inline; this reduces mobile layout flicker.
- Each diaper has a dedicated **View** page with full details and a large photo when available.
- Automatic meal reminder UI now correctly says **11 minutes before**.
- Production WSGI starts a lightweight push dispatcher approximately every 30 seconds.
- PostgreSQL advisory locking prevents concurrent scheduler processes from double-sending.
- Failed push attempts are no longer marked as successfully notified.
- Reminders wrongly marked by older code are repaired when no successful delivery log exists.
- Existing browser subscriptions are re-synced to the server when the Reminders page is opened.
- Dr Savvas remains excluded from push delivery.


## Meal remaining calculator and main diaper navigation
Meal entry now supports **Remaining ml**:
- enter `Offered ml` and `Remaining ml`;
- `Consumed ml` is calculated automatically as `Offered - Remaining`;
- server-side validation rejects a remainder greater than the offered amount;
- the old workflow is still supported: if `Remaining ml` is left blank and `Consumed ml` is entered, the remainder is calculated on save;
- migration `0016` backfills existing meals with `remaining_ml = offered_ml - consumed_ml` when possible.

Remaining ml is also shown in the meal list, History timeline, 24-hour report and 48-hour clinical report.

**Diapers** have been moved out of the Health hub and into the main navigation immediately after **Glucose**, on desktop and mobile.


## Preserve date/time on edit
All shared HTML date/time widgets now use browser-compatible formats:
- Date: `YYYY-MM-DD`
- Time: `HH:MM`

This keeps the existing date/time visibly prefilled when editing meals, glucose readings,
growth measurements, medications, appointments, vaccines, symptoms, diapers, labs,
documents, reminders and other forms that use the shared DateInput/TimeInput widgets.
The fields remain editable if a genuine correction is needed.


## Possible diarrhea on diaper entries
Diaper entries now include a separate **Possible diarrhea** checkbox.
It is stored as a parent observation only and is not treated as a medical diagnosis.

The flag appears in:
- diaper create/edit form;
- diaper list;
- diaper View page;
- 48-hour clinical print report.


## Feeding interval starts from meal finish
The feeding schedule is now dynamic instead of being driven by the old fixed clock slots.

Current logic:
- each meal can store **start time** and **finish time**;
- the default feeding interval is **180 minutes (3 hours)**;
- the next meal is calculated as `previous meal finish + feeding interval`;
- the automatic meal push is scheduled **11 minutes before** that calculated next meal;
- if a feed starts but has no finish time yet, the app does not invent the next exact feed time;
- old fixed `meal-schedule:*` reminders are removed by migration `0018`;
- the ≤50 ml follow-up rule now counts its one hour from meal completion when a finish time is available;
- dashboard comparison is by meal sequence (#1, #2, #3...) rather than fixed clock slot;
- reports, meal history, Hospital Mode, Doctor View and exports include finish time;
- existing historical meals are NOT assigned an invented finish time.

The old 01:30 / 04:30 / ... times remain only as bootstrap/reference times when no completed meal with a finish time is available yet.

The interval can be changed in Child Profile through `feeding_interval_minutes`; it defaults to 180.


## Dr Grafakou read-only account
A second protected doctor account is provisioned automatically during deploy:

- username: `drgrafakou`
- display name: `Δρ Όλγα Γραφάκου`
- default password: `Olga`
- role: `doctor_readonly`

The password may later be overridden with the Render environment variable
`DJANGO_GRAFAKOU_PASSWORD`.

Both `drsavvas` and `drgrafakou` are hard-protected as read-only by `core/access.py`,
even if their access-profile row is accidentally changed. Read-only doctors are also
excluded from push subscriptions and push delivery through the existing
`is_readonly_doctor()` checks.


## UI design refresh
A light visual refresh was applied without changing application behaviour:
- cleaner glass-style top navigation;
- active page highlighting on desktop and mobile navigation;
- refined typography, spacing, borders and shadows;
- upgraded hero and dashboard KPI cards;
- clearer countdown / feeding panels;
- more polished forms and focus states;
- softer table styling and row feedback;
- improved shortcut cards and buttons;
- refined mobile bottom navigation;
- matching dark-mode refinements;
- reduced-motion accessibility support.

No database migration is required for this visual update.


## Color boost
A second visual pass adds a bit more colour while keeping the interface clean:
- richer pastel gradients in the background;
- more colourful active navigation state;
- livelier hero banner and primary buttons;
- more colourful KPI cards and shortcut icons;
- subtle rainbow accent line on panels/cards/forms;
- slightly warmer tables, messages and mobile nav;
- dark mode stays balanced and readable.

No migrations are required for this visual update.


## Meal and glucose comments visibility
When a meal or glucose entry contains notes/comments, they are now visible in the main read-only views instead of being hidden inside Edit forms.

Comments are shown in:
- Dashboard today's meals;
- Dashboard today's glucose;
- Dashboard meal-by-meal yesterday vs today comparison;
- Meals list;
- Glucose list;
- History timeline;
- History preview/report;
- History PDF;
- 24-hour preview and PDF;
- 48-hour clinical report (already supported and retained).

Empty comments remain hidden/represented by a dash so screens stay uncluttered.
No migration is required.


## More colour pass
A stronger pastel colour pass was added while preserving readability:
- more distinct section colours;
- richer dashboard KPI cards;
- coloured meal/glucose/medication panels;
- more varied shortcut cards;
- richer comments, reminders and forms;
- stronger active navigation colours;
- matching dark-mode colour accents.

No migration is required.
