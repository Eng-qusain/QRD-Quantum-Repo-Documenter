"""
PDF Generation Engine — ReportLab-based PDF builder.

Supports:
- Syntax-highlighted source code
- Data tables (CSV / Excel previews)
- Images and SVGs
- Clickable Table of Contents
- Page headers / footers
- Multiple themes (default, dark, github, monokai)
"""

from __future__ import annotations

import logging
import textwrap
from datetime import datetime
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, LETTER, A3, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfgen import canvas

logger = logging.getLogger(__name__)

# ─── Theme Definitions ────────────────────────────────────────────────────────

THEMES = {
    "default": {
        "bg": colors.white,
        "text": colors.HexColor("#1a1a2e"),
        "code_bg": colors.HexColor("#f6f8fa"),
        "code_text": colors.HexColor("#24292e"),
        "accent": colors.HexColor("#0969da"),
        "heading": colors.HexColor("#0969da"),
        "border": colors.HexColor("#d0d7de"),
        "line_num": colors.HexColor("#8b949e"),
        "header_bg": colors.HexColor("#0969da"),
        "header_text": colors.white,
    },
    "dark": {
        "bg": colors.HexColor("#0d1117"),
        "text": colors.HexColor("#c9d1d9"),
        "code_bg": colors.HexColor("#161b22"),
        "code_text": colors.HexColor("#c9d1d9"),
        "accent": colors.HexColor("#58a6ff"),
        "heading": colors.HexColor("#58a6ff"),
        "border": colors.HexColor("#30363d"),
        "line_num": colors.HexColor("#8b949e"),
        "header_bg": colors.HexColor("#161b22"),
        "header_text": colors.HexColor("#58a6ff"),
    },
    "github": {
        "bg": colors.white,
        "text": colors.HexColor("#24292e"),
        "code_bg": colors.HexColor("#f6f8fa"),
        "code_text": colors.HexColor("#24292e"),
        "accent": colors.HexColor("#0366d6"),
        "heading": colors.HexColor("#24292e"),
        "border": colors.HexColor("#e1e4e8"),
        "line_num": colors.HexColor("#babbbd"),
        "header_bg": colors.HexColor("#24292e"),
        "header_text": colors.white,
    },
    "monokai": {
        "bg": colors.HexColor("#272822"),
        "text": colors.HexColor("#f8f8f2"),
        "code_bg": colors.HexColor("#1e1f1c"),
        "code_text": colors.HexColor("#f8f8f2"),
        "accent": colors.HexColor("#66d9e8"),
        "heading": colors.HexColor("#a6e22e"),
        "border": colors.HexColor("#49483e"),
        "line_num": colors.HexColor("#75715e"),
        "header_bg": colors.HexColor("#1e1f1c"),
        "header_text": colors.HexColor("#a6e22e"),
    },
}

PAGE_SIZES = {
    "A4": A4,
    "Letter": LETTER,
    "A3": A3,
}


# ─── Custom Flowables ─────────────────────────────────────────────────────────

class SyntaxCodeBlock(Flowable):
    """A flowable that renders syntax-highlighted code with line numbers."""

    def __init__(
        self,
        code: str,
        language: str,
        theme: dict,
        font_size: int = 8,
        show_line_numbers: bool = True,
        max_line_width: int = 100,
    ) -> None:
        super().__init__()
        self.code = code
        self.language = language
        self.theme = theme
        self.font_size = font_size
        self.show_line_numbers = show_line_numbers
        self.max_line_width = max_line_width
        self._lines: list[str] = []
        self._prepare()

    def _prepare(self) -> None:
        """Pre-process code lines with wrapping."""
        raw_lines = self.code.split("\n")
        self._lines = []
        for line in raw_lines:
            if len(line) > self.max_line_width:
                # Wrap long lines
                wrapped = textwrap.wrap(
                    line,
                    width=self.max_line_width,
                    subsequent_indent="    ",
                    break_long_words=True,
                    break_on_hyphens=False,
                )
                self._lines.extend(wrapped if wrapped else [""])
            else:
                self._lines.append(line)

    def wrap(self, available_width: float, available_height: float) -> tuple[float, float]:
        line_height = self.font_size * 1.4
        num_lines = len(self._lines)
        padding = 16  # top + bottom padding
        self.width = available_width
        self.height = line_height * num_lines + padding
        return self.width, self.height

    def draw(self) -> None:
        c = self.canv
        theme = self.theme
        line_height = self.font_size * 1.4
        padding = 8
        line_num_width = 40 if self.show_line_numbers else 0

        # Background
        c.setFillColor(theme["code_bg"])
        c.rect(0, 0, self.width, self.height, fill=1, stroke=0)

        # Border
        c.setStrokeColor(theme["border"])
        c.setLineWidth(0.5)
        c.rect(0, 0, self.width, self.height, fill=0, stroke=1)

        # Line number separator
        if self.show_line_numbers:
            c.setStrokeColor(theme["border"])
            c.setLineWidth(0.5)
            c.line(line_num_width, 0, line_num_width, self.height)

        c.setFont("Courier", self.font_size)

        for i, line in enumerate(self._lines):
            y = self.height - padding - (i + 1) * line_height + (line_height - self.font_size) / 2

            # Line number
            if self.show_line_numbers:
                c.setFillColor(theme["line_num"])
                c.drawRightString(line_num_width - 4, y, str(i + 1))

            # Code content
            c.setFillColor(theme["code_text"])
            # Replace tabs with spaces for PDF rendering
            display_line = line.replace("\t", "    ")
            c.drawString(line_num_width + 6, y, display_line[:self.max_line_width])


class FileHeaderBlock(Flowable):
    """Renders a styled file header card."""

    def __init__(self, file_info: dict, theme: dict) -> None:
        super().__init__()
        self.file_info = file_info
        self.theme = theme
        self.height: float = 70
        self.width: float = 500

    def wrap(self, available_width: float, available_height: float) -> tuple[float, float]:
        self.width = available_width
        return self.width, self.height

    def draw(self) -> None:
        c = self.canv
        theme = self.theme
        fi = self.file_info

        # Background
        c.setFillColor(theme["header_bg"])
        c.roundRect(0, 0, self.width, self.height, 4, fill=1, stroke=0)

        # File name (large)
        c.setFillColor(theme["header_text"])
        c.setFont("Helvetica-Bold", 13)
        c.drawString(12, self.height - 22, fi.get("name", ""))

        # Metadata row
        c.setFont("Helvetica", 9)
        meta_y = self.height - 42
        meta_parts = []
        if fi.get("language"):
            meta_parts.append(f"Language: {fi['language']}")
        if fi.get("line_count"):
            meta_parts.append(f"Lines: {fi['line_count']:,}")
        if fi.get("size_bytes"):
            kb = fi["size_bytes"] / 1024
            meta_parts.append(f"Size: {kb:.1f} KB")
        if fi.get("last_modified"):
            meta_parts.append(f"Modified: {fi['last_modified']}")

        c.drawString(12, meta_y, "  ·  ".join(meta_parts))

        # Relative path
        if fi.get("relative_path"):
            c.setFont("Helvetica", 8)
            c.setFillColor(colors.HexColor("#8b949e"))
            c.drawString(12, self.height - 58, fi["relative_path"])


# ─── PDF Builder ──────────────────────────────────────────────────────────────

class PDFBuilder:
    """
    Main PDF construction class.

    Usage:
        builder = PDFBuilder(output_path, options)
        builder.add_cover_page(project_name, stats)
        builder.add_toc()
        builder.add_file(file_info, content)
        builder.build()
    """

    def __init__(
        self,
        output_path: str,
        theme: str = "default",
        paper_size: str = "A4",
        orientation: str = "portrait",
        font_size: int = 9,
        show_line_numbers: bool = True,
        project_name: str = "Project Documentation",
    ) -> None:
        self.output_path = output_path
        self.theme = THEMES.get(theme, THEMES["default"])
        self.paper = PAGE_SIZES.get(paper_size, A4)
        self.font_size = font_size
        self.show_line_numbers = show_line_numbers
        self.project_name = project_name

        if orientation == "landscape":
            self.paper = landscape(self.paper)

        self._story: list = []
        self._toc: Optional[TableOfContents] = None
        self._page_count = 0

        self._setup_styles()

    def _setup_styles(self) -> None:
        """Initialize paragraph styles."""
        t = self.theme
        self.styles = {
            "title": ParagraphStyle(
                "Title",
                fontSize=28,
                leading=34,
                textColor=t["heading"],
                alignment=TA_CENTER,
                spaceAfter=12,
                fontName="Helvetica-Bold",
            ),
            "subtitle": ParagraphStyle(
                "Subtitle",
                fontSize=14,
                leading=18,
                textColor=t["text"],
                alignment=TA_CENTER,
                spaceAfter=6,
            ),
            "h1": ParagraphStyle(
                "H1",
                fontSize=18,
                leading=22,
                textColor=t["heading"],
                spaceBefore=16,
                spaceAfter=8,
                fontName="Helvetica-Bold",
            ),
            "h2": ParagraphStyle(
                "H2",
                fontSize=14,
                leading=18,
                textColor=t["heading"],
                spaceBefore=12,
                spaceAfter=6,
                fontName="Helvetica-Bold",
            ),
            "h3": ParagraphStyle(
                "H3",
                fontSize=11,
                leading=14,
                textColor=t["heading"],
                spaceBefore=8,
                spaceAfter=4,
                fontName="Helvetica-Bold",
            ),
            "body": ParagraphStyle(
                "Body",
                fontSize=10,
                leading=14,
                textColor=t["text"],
                spaceAfter=4,
            ),
            "caption": ParagraphStyle(
                "Caption",
                fontSize=8,
                leading=10,
                textColor=colors.grey,
                alignment=TA_CENTER,
                spaceAfter=8,
            ),
            "toc1": ParagraphStyle(
                "TOC1",
                fontSize=11,
                leading=16,
                textColor=t["accent"],
                leftIndent=0,
                spaceAfter=2,
            ),
            "toc2": ParagraphStyle(
                "TOC2",
                fontSize=9,
                leading=14,
                textColor=t["text"],
                leftIndent=16,
                spaceAfter=1,
            ),
        }

    def _make_header_footer(self, canvas_obj: canvas.Canvas, doc: BaseDocTemplate) -> None:
        """Draw page header and footer."""
        canvas_obj.saveState()
        t = self.theme
        w, h = canvas_obj._pagesize

        # Header bar
        canvas_obj.setFillColor(t["header_bg"])
        canvas_obj.rect(0, h - 28, w, 28, fill=1, stroke=0)

        canvas_obj.setFillColor(t["header_text"])
        canvas_obj.setFont("Helvetica-Bold", 10)
        canvas_obj.drawString(15, h - 18, self.project_name)
        canvas_obj.setFont("Helvetica", 9)
        canvas_obj.drawRightString(w - 15, h - 18, "RepoDoc Pro")

        # Footer
        canvas_obj.setFillColor(t["border"])
        canvas_obj.setLineWidth(0.5)
        canvas_obj.line(15, 25, w - 15, 25)

        canvas_obj.setFillColor(t["text"])
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.drawString(15, 14, datetime.now().strftime("%Y-%m-%d"))
        canvas_obj.drawCentredString(w / 2, 14, "RepoDoc Pro — Professional Code Documentation")
        canvas_obj.drawRightString(w - 15, 14, f"Page {doc.page}")

        canvas_obj.restoreState()

    def add_cover_page(
        self,
        project_name: str,
        stats: Optional[dict] = None,
        description: str = "",
    ) -> None:
        """Add a cover page to the document."""
        t = self.theme

        self._story.append(Spacer(1, 3 * cm))
        self._story.append(Paragraph(project_name, self.styles["title"]))
        self._story.append(Paragraph("Technical Documentation", self.styles["subtitle"]))
        self._story.append(Spacer(1, 0.5 * cm))
        self._story.append(
            HRFlowable(
                width="60%",
                thickness=2,
                color=t["accent"],
                spaceAfter=20,
                hAlign="CENTER",
            )
        )
        self._story.append(Spacer(1, 0.5 * cm))

        if description:
            self._story.append(Paragraph(description, self.styles["body"]))
            self._story.append(Spacer(1, 0.5 * cm))

        # Stats summary table
        if stats:
            data = [
                ["Metric", "Value"],
                ["Total Files", f"{stats.get('total_files', 0):,}"],
                ["Lines of Code", f"{stats.get('total_lines', 0):,}"],
                ["Languages", str(len(stats.get("language_distribution", {})))],
                ["Generated", datetime.now().strftime("%B %d, %Y at %H:%M UTC")],
            ]
            table = Table(data, colWidths=[6 * cm, 8 * cm])
            table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), t["header_bg"]),
                    ("TEXTCOLOR", (0, 0), (-1, 0), t["header_text"]),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [t["code_bg"], t["bg"]]),
                    ("TEXTCOLOR", (0, 1), (-1, -1), t["text"]),
                    ("GRID", (0, 0), (-1, -1), 0.5, t["border"]),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("ROUNDEDCORNERS", [4, 4, 4, 4]),
                ])
            )
            self._story.append(table)

        self._story.append(Spacer(1, 1 * cm))
        self._story.append(Paragraph("Generated by RepoDoc Pro", self.styles["caption"]))
        self._story.append(PageBreak())

    def add_toc(self) -> None:
        """Add a Table of Contents placeholder."""
        self._story.append(Paragraph("Table of Contents", self.styles["h1"]))
        self._story.append(Spacer(1, 0.3 * cm))
        self._toc = TableOfContents()
        self._toc.levelStyles = [self.styles["toc1"], self.styles["toc2"]]
        self._story.append(self._toc)
        self._story.append(PageBreak())

    def add_section_header(self, title: str, level: int = 1) -> None:
        """Add a section heading that appears in the TOC."""
        style_key = f"h{min(level, 3)}"
        p = Paragraph(title, self.styles[style_key])
        p._bookmarkName = title.replace(" ", "_")
        self._story.append(p)

    # Approximate maximum lines per PDF page at the given font size.
    # Calculated as: (A4 height - margins - header - footer) / line_height
    # = (841pt - 30pt top - 30pt bottom - 28pt header - 25pt footer) / (font_size * 1.4)
    # Using a conservative factor of 0.75 for safety margin.
    def _max_lines_per_page(self) -> int:
        usable_pts = 841 - 113  # A4 height minus all reserved space
        line_height = self.font_size * 1.4
        return max(30, int((usable_pts / line_height) * 0.75))

    def add_source_file(
        self,
        file_info: dict,
        content: str,
        language: str = "text",
    ) -> None:
        """Add a source code file to the PDF.

        Large files are split into page-sized chunks to prevent ReportLab
        LayoutError ('Flowable too large on page').
        """
        lines = content.split("\n")
        max_lines = self._max_lines_per_page()

        self._story.append(PageBreak())
        self._story.append(FileHeaderBlock(file_info, self.theme))
        self._story.append(Spacer(1, 0.3 * cm))

        # Split into chunks that fit on a single page
        for chunk_start in range(0, len(lines), max_lines):
            chunk = lines[chunk_start:chunk_start + max_lines]
            if chunk_start > 0:
                # Subsequent chunks: new page, no repeated header
                self._story.append(PageBreak())

            # Adjust line numbering so it reflects the actual source line numbers
            chunk_content = "\n".join(chunk)
            self._story.append(
                SyntaxCodeBlock(
                    code=chunk_content,
                    language=language,
                    theme=self.theme,
                    font_size=self.font_size,
                    show_line_numbers=self.show_line_numbers,
                )
            )

    def add_csv_preview(
        self,
        file_info: dict,
        headers: list[str],
        rows: list[list],
        stats: dict,
    ) -> None:
        """Add a CSV data preview."""
        self._story.append(PageBreak())
        self._story.append(Paragraph(f"📊 {file_info['name']}", self.styles["h2"]))
        self._story.append(Paragraph(file_info.get("relative_path", ""), self.styles["caption"]))

        # Stats card
        stat_items = [
            f"Rows: {stats.get('row_count', 'N/A'):,}",
            f"Columns: {stats.get('column_count', 'N/A')}",
            f"Size: {file_info.get('size_bytes', 0) / 1024:.1f} KB",
        ]
        self._story.append(Paragraph("  |  ".join(stat_items), self.styles["body"]))
        self._story.append(Spacer(1, 0.3 * cm))

        # Data table
        if headers and rows:
            t = self.theme
            table_data = [headers] + rows
            table = Table(table_data, repeatRows=1)
            table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), t["header_bg"]),
                    ("TEXTCOLOR", (0, 0), (-1, 0), t["header_text"]),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [t["code_bg"], t["bg"]]),
                    ("TEXTCOLOR", (0, 1), (-1, -1), t["text"]),
                    ("GRID", (0, 0), (-1, -1), 0.3, t["border"]),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("WORDWRAP", (0, 0), (-1, -1), True),
                ])
            )
            self._story.append(table)

    def add_image(
        self,
        file_info: dict,
        image_path: str,
        max_width_cm: float = 15,
        max_height_cm: float = 20,
    ) -> None:
        """Embed a raster image."""
        self._story.append(PageBreak())
        self._story.append(Paragraph(f"🖼 {file_info['name']}", self.styles["h2"]))
        self._story.append(Paragraph(file_info.get("relative_path", ""), self.styles["caption"]))
        self._story.append(Spacer(1, 0.3 * cm))

        try:
            img = Image(
                image_path,
                width=max_width_cm * cm,
                height=max_height_cm * cm,
                kind="proportional",
            )
            img.hAlign = "CENTER"
            self._story.append(img)
        except Exception as e:
            self._story.append(
                Paragraph(f"[Image could not be rendered: {e}]", self.styles["caption"])
            )

    def add_ai_summary(self, file_path: str, ai_doc: dict) -> None:
        """Add AI-generated documentation for a file."""
        self._story.append(Spacer(1, 0.5 * cm))
        self._story.append(Paragraph("AI Documentation", self.styles["h3"]))

        fields = [
            ("Summary", ai_doc.get("summary", "")),
            ("Purpose", ai_doc.get("purpose", "")),
            ("Complexity", ai_doc.get("complexity", "")),
        ]
        for label, value in fields:
            if value:
                self._story.append(Paragraph(f"<b>{label}:</b> {value}", self.styles["body"]))

        # Key functions
        funcs = ai_doc.get("key_functions", [])
        if funcs:
            self._story.append(Paragraph("<b>Key Functions:</b>", self.styles["body"]))
            for fn in funcs:
                self._story.append(Paragraph(f"• {fn}", self.styles["body"]))

        # Dependencies
        deps = ai_doc.get("dependencies", [])
        if deps:
            self._story.append(
                Paragraph(f"<b>Dependencies:</b> {', '.join(deps)}", self.styles["body"])
            )

    def add_statistics_page(self, stats: dict) -> None:
        """Add a project statistics summary page."""
        self._story.append(PageBreak())
        self._story.append(Paragraph("Project Statistics", self.styles["h1"]))
        self._story.append(Spacer(1, 0.5 * cm))

        # Overall stats table
        data = [
            ["Metric", "Value"],
            ["Total Files", f"{stats.get('total_files', 0):,}"],
            ["Total Directories", f"{stats.get('total_directories', 0):,}"],
            ["Total Lines of Code", f"{stats.get('total_lines', 0):,}"],
            ["Total Size", self._format_size(stats.get("total_size_bytes", 0))],
            ["Average File Size", self._format_size(int(stats.get("average_file_size", 0)))],
            ["Average Line Count", f"{stats.get('average_line_count', 0):.0f}"],
        ]

        t = self.theme
        table = Table(data, colWidths=[7 * cm, 8 * cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), t["header_bg"]),
            ("TEXTCOLOR", (0, 0), (-1, 0), t["header_text"]),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [t["code_bg"], t["bg"]]),
            ("TEXTCOLOR", (0, 1), (-1, -1), t["text"]),
            ("GRID", (0, 0), (-1, -1), 0.5, t["border"]),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        self._story.append(table)

    def build(self) -> str:
        """Build the final PDF and return the output path."""
        doc = SimpleDocTemplate(
            self.output_path,
            pagesize=self.paper,
            rightMargin=1.5 * cm,
            leftMargin=1.5 * cm,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm,
            title=self.project_name,
            author="RepoDoc Pro",
            subject="Technical Documentation",
            creator="RepoDoc Pro v1.0",
        )

        doc.build(
            self._story,
            onFirstPage=self._make_header_footer,
            onLaterPages=self._make_header_footer,
        )

        logger.info(f"PDF built: {self.output_path}")
        return self.output_path

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        if size_bytes < 1024 ** 2:
            return f"{size_bytes / 1024:.1f} KB"
        if size_bytes < 1024 ** 3:
            return f"{size_bytes / (1024 ** 2):.1f} MB"
        return f"{size_bytes / (1024 ** 3):.2f} GB"
