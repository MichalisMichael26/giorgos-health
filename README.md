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
