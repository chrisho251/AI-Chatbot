"""One off generator for the layout fixtures.

Writes tests/fixtures/layout.pdf, a born digital file with text, a ruled table, an equation and a
figure, and tests/fixtures/blank.pdf, a blank page followed by a page with one line, so the blank
page path of the region split is covered. Run it from the repository root.
"""

import sys
from pathlib import Path

PAGE_W, PAGE_H = 612, 792


def esc(text: str) -> str:
    return text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


class Page:
    def __init__(self) -> None:
        self.ops: list[str] = []

    def text(self, x: float, y: float, size: int, font: str, value: str) -> None:
        self.ops.append(f"BT /{font} {size} Tf {x} {y} Td ({esc(value)}) Tj ET\n")

    def line(self, x0: float, y0: float, x1: float, y1: float, width: float = 0.8) -> None:
        self.ops.append(f"{width} w {x0} {y0} m {x1} {y1} l S\n")

    def rect(self, x: float, y: float, w: float, h: float, gray: float) -> None:
        self.ops.append(f"{gray} g {x} {y} {w} {h} re f\n")


def write_pdf(path: Path, pages: list[Page]) -> None:
    objects: list[bytes] = []

    def add(body: bytes) -> int:
        objects.append(body)
        return len(objects)

    font_map = {
        name: add(
            f"<< /Type /Font /Subtype /Type1 /BaseFont /{name} "
            f"/Encoding /WinAnsiEncoding >>".encode()
        )
        for name in ("Courier", "Helvetica", "Times")
    }
    fonts = "/Font << " + " ".join(f"/{n} {i} 0 R" for n, i in font_map.items()) + " >>"
    resources = f"<< {fonts} >>"

    content_ids = [
        add(f"<< /Length {len(body)} >>\nstream\n".encode() + body + b"\nendstream")
        for body in ("".join(page.ops).encode("latin-1") for page in pages)
    ]
    pages_id = len(objects) + len(pages) + 1
    page_ids = [
        add(
            f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 {PAGE_W} {PAGE_H}] "
            f"/Resources {resources} /Contents {content_id} 0 R >>".encode()
        )
        for content_id in content_ids
    ]
    kids = " ".join(f"{num} 0 R" for num in page_ids)
    actual = add(f"<< /Type /Pages /Count {len(page_ids)} /Kids [{kids}] >>".encode())
    assert actual == pages_id, (actual, pages_id)
    catalog = add(f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode())

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for offset in offsets[1:]:
        out += f"{offset:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root {catalog} 0 R >>\nstartxref\n{xref}\n%%EOF\n"
    ).encode()
    path.write_bytes(bytes(out))


def layout_pages() -> list[Page]:
    one = Page()
    one.text(72, 720, 22, "Times", "Regression and Random Variables")
    one.text(72, 680, 13, "Helvetica", "Chapter 3. Least squares estimation")
    one.text(72, 640, 12, "Helvetica", "The normal equations for a simple linear")
    one.text(72, 624, 12, "Helvetica", "regression of y on x are written below.")
    one.text(72, 560, 12, "Times", "y = a + b x + e")
    one.text(72, 470, 12, "Helvetica", "Coefficient estimates")
    top, left, width, row = 440, 72, 300, 26
    for x0, y0, x1, y1 in [
        (left, top + row, left + width, top + row),
        (left, top - row, left + width, top - row),
        (left, top, left, top - row),
        (left + width, top, left + width, top - row),
        (left + 140, top, left + 140, top - row),
    ]:
        one.line(x0, y0, x1, y1)
    for index, (x, y) in enumerate([("x", "y"), ("1", "2.5"), ("2", "4.1"), ("3", "5.8")]):
        one.text(left + 8, top - 18 - index * 26, 12, "Helvetica", x)
        one.text(left + 148, top - 18 - index * 26, 12, "Helvetica", y)
    one.text(72, 300, 12, "Helvetica", "The fitted line and the residuals")
    for step in range(1, 6):
        one.line(72 + step * 90, 120, 72 + step * 90, 260)
    one.line(72, 190, 512, 190)
    one.text(72, 200, 12, "Helvetica", "0")
    one.text(72, 60, 12, "Helvetica", "Table 3.1 gives the same coefficients.")

    two = Page()
    two.text(72, 720, 22, "Times", "Implementation notes")
    two.text(72, 680, 12, "Helvetica", "A short listing that fits the dataset follows.")
    two.rect(72, 300, 460, 340, 0.94)
    for index, line in enumerate(
        [
            "import numpy as np",
            "",
            "x = np.array([1, 2, 3])",
            "y = np.array([2.5, 4.1, 5.8])",
            "",
            "b, a = np.polyfit(x, y, 1)",
            "print(a, b)",
        ]
    ):
        two.text(88, 610 - index * 22, 11, "Courier", line)
    two.text(72, 250, 12, "Helvetica", "The slope is the estimate of the effect.")
    two.text(72, 200, 12, "Helvetica", "The intercept is the level at x = 0.")
    return [one, two]


def blank_pages() -> list[Page]:
    """A page with nothing on it and a page with one line, so the blank page path is covered."""
    filled = Page()
    filled.text(72, 720, 12, "Helvetica", "The last page carries one line only.")
    return [Page(), filled]


def main() -> None:
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "workers/w1_ingest/tests/fixtures")
    target.mkdir(parents=True, exist_ok=True)
    write_pdf(target / "layout.pdf", layout_pages())
    write_pdf(target / "blank.pdf", blank_pages())
    for name in ("layout.pdf", "blank.pdf"):
        print(f"wrote {name} {(target / name).stat().st_size} bytes")


if __name__ == "__main__":
    main()
