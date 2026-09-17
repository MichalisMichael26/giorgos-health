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
