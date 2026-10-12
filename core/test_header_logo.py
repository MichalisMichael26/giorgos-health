from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class HeaderLogoTests(SimpleTestCase):
    def test_brand_asset_exists_and_is_not_cropped(self):
        base_dir = Path(settings.BASE_DIR)
        template = (base_dir / "templates" / "base.html").read_text(encoding="utf-8")
        css = (base_dir / "static" / "css" / "app.css").read_text(encoding="utf-8")

        self.assertTrue((base_dir / "static" / "images" / "logo.png").is_file())
        self.assertIn('class="brand-logo" width="58" height="58"', template)
        last_fix = css.split("Header logo visibility fix (Oct 2026)")[-1]
        self.assertIn("object-fit: contain;", last_fix)
        self.assertIn("flex: 0 0 58px;", last_fix)
        self.assertIn(".topbar .desktop-nav", last_fix)
        self.assertIn("@media (max-width: 720px)", last_fix)
