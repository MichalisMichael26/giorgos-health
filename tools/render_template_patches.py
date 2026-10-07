from pathlib import Path


BUTTON_FRAGMENT = """
    {% if featured_diagnosis_document %}
    <div class="official-featured-document-button">
        <a class="btn secondary no-print" href="{% url 'document_preview' featured_diagnosis_document.pk %}">📄 Επίσημο έντυπο</a>
    </div>
    {% endif %}
"""


def patch_template(path_str):
    path = Path(path_str)
    text = path.read_text(encoding="utf-8")

    if "official-featured-document-button" in text:
        return False

    marker = 'class="diagnosis-gold-banner'
    start = text.find(marker)
    if start < 0:
        return False

    end = text.find("</section>", start)
    if end < 0:
        return False

    text = text[:end] + BUTTON_FRAGMENT + text[end:]
    path.write_text(text, encoding="utf-8")
    return True


if __name__ == "__main__":
    targets = [
        "templates/dashboard.html",
        "templates/doctor/view.html",
    ]
    for target in targets:
        changed = patch_template(target)
        print(f"{target}: {'patched' if changed else 'unchanged'}")
