"""One-shot fixture generator. Produces tests/fixtures/tiny_lab.pdf.

Run: python tests/fixtures/_make_tiny_pdf.py

We commit the resulting PDF so tests can run without reportlab in CI.
"""

from reportlab.pdfgen import canvas

OUT = "tests/fixtures/tiny_lab.pdf"

c = canvas.Canvas(OUT)
c.drawString(72, 750, "LABORATORY REPORT")
c.drawString(72, 720, "Patient: Jane Doe   Date: 2022-03-14")
c.drawString(72, 690, "Creatinine: 1.4 mg/dL  (Reference: 0.6-1.2)")
c.drawString(72, 660, "eGFR: 52 mL/min/1.73m^2")
c.showPage()
c.save()
print(f"Wrote {OUT}")
