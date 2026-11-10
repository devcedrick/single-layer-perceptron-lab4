"""Build the Laboratory Exercise No. 4 report as a .docx file.

Formatting contract: black text only, 11 pt Times New Roman body, 14 pt
Heading 1, justified paragraphs, 1.5 line spacing.

Requires python-docx. The table of contents is a real Word field; on Windows
the builder asks Word to populate it so page numbers are correct on first open.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

from perceptron_lab4 import INPUTS, TARGETS, train

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "Perceptron_Lab4_Documentation.docx"
REPO_URL = "https://github.com/devcedrick/single-layer-perceptron-lab4"

BLACK = RGBColor(0, 0, 0)
BODY_FONT = "Times New Roman"
MONO_FONT = "Consolas"


# --------------------------------------------------------------------------
# Low-level helpers
# --------------------------------------------------------------------------

def force_black(style) -> None:
    """Remove the theme colour Word applies to built-in styles."""
    style.font.color.rgb = BLACK
    r_pr = style.element.get_or_add_rPr()
    color = r_pr.find(qn("w:color"))
    if color is None:
        return
    for attribute in ("w:themeColor", "w:themeShade", "w:themeTint"):
        if color.get(qn(attribute)) is not None:
            del color.attrib[qn(attribute)]


def set_style_font(style, name: str, size: float) -> None:
    """Force a concrete font, overriding the template's theme font pair."""
    style.font.name = name
    style.font.size = Pt(size)
    r_pr = style.element.get_or_add_rPr()
    r_fonts = r_pr.find(qn("w:rFonts"))
    if r_fonts is None:
        r_fonts = OxmlElement("w:rFonts")
        r_pr.append(r_fonts)
    for attribute in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme",
                      "w:cstheme"):
        if r_fonts.get(qn(attribute)) is not None:
            del r_fonts.attrib[qn(attribute)]
    for attribute in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        r_fonts.set(qn(attribute), name)


def set_run_font(run, name: str, size: float, bold: bool = False,
                 italic: bool = False) -> None:
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = BLACK
    r_pr = run._element.get_or_add_rPr()
    r_fonts = r_pr.find(qn("w:rFonts"))
    if r_fonts is None:
        r_fonts = OxmlElement("w:rFonts")
        r_pr.append(r_fonts)
    for attribute in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        r_fonts.set(qn(attribute), name)


def add_text(paragraph, text: str, size: float = 11, bold: bool = False,
             italic: bool = False, font: str = BODY_FONT):
    run = paragraph.add_run(text)
    set_run_font(run, font, size, bold, italic)
    return run


def add_hyperlink(paragraph, url: str, text: str | None = None,
                  size: float = 11) -> None:
    """Insert a hyperlink that still respects the black-text rule."""
    relationship_id = paragraph.part.relate_to(url, RT.HYPERLINK, is_external=True)
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), relationship_id)

    run = OxmlElement("w:r")
    r_pr = OxmlElement("w:rPr")
    r_fonts = OxmlElement("w:rFonts")
    for attribute in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        r_fonts.set(qn(attribute), BODY_FONT)
    r_pr.append(r_fonts)
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "000000")
    r_pr.append(color)
    half_points = OxmlElement("w:sz")
    half_points.set(qn("w:val"), str(int(size * 2)))
    r_pr.append(half_points)
    underline = OxmlElement("w:u")
    underline.set(qn("w:val"), "single")
    r_pr.append(underline)
    run.append(r_pr)

    text_element = OxmlElement("w:t")
    text_element.set(qn("xml:space"), "preserve")
    text_element.text = text or url
    run.append(text_element)
    hyperlink.append(run)
    paragraph._p.append(hyperlink)


def add_toc_field(paragraph) -> None:
    """Insert a Word TOC field with a prompt as its placeholder."""
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = ' TOC \\o "1-1" \\h \\z \\u '
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    run._r.append(begin)
    run._r.append(instruction)
    run._r.append(separate)

    placeholder = paragraph.add_run("Right-click and choose Update Field.")
    set_run_font(placeholder, BODY_FONT, 11)

    end_run = paragraph.add_run()
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    end_run._r.append(end)


def add_page_number(paragraph) -> None:
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = " PAGE "
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for element in (begin, instruction, separate, end):
        run._r.append(element)
    set_run_font(run, BODY_FONT, 9)


def restart_numbering(section) -> None:
    sect_pr = section._sectPr
    page_numbering = OxmlElement("w:pgNumType")
    page_numbering.set(qn("w:start"), "1")
    columns = sect_pr.find(qn("w:cols"))
    if columns is not None:
        columns.addprevious(page_numbering)
    else:
        sect_pr.append(page_numbering)


def clear_numbering(section) -> None:
    sect_pr = section._sectPr
    for element in sect_pr.findall(qn("w:pgNumType")):
        sect_pr.remove(element)


def keep_header_row(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    header = OxmlElement("w:tblHeader")
    header.set(qn("w:val"), "true")
    tr_pr.append(header)


def prevent_row_split(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    cant_split = OxmlElement("w:cantSplit")
    cant_split.set(qn("w:val"), "true")
    tr_pr.append(cant_split)


def tighten_cell(cell, size: float, bold: bool = False,
                 alignment=WD_ALIGN_PARAGRAPH.CENTER) -> None:
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    for paragraph in cell.paragraphs:
        paragraph.alignment = alignment
        paragraph.paragraph_format.space_before = Pt(1)
        paragraph.paragraph_format.space_after = Pt(1)
        paragraph.paragraph_format.line_spacing = 1.0
        for run in paragraph.runs:
            set_run_font(run, BODY_FONT, size, bold)


# --------------------------------------------------------------------------
# Document building blocks
# --------------------------------------------------------------------------

def body(document, text: str, space_before: float = 0) -> None:
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    paragraph.paragraph_format.line_spacing = 1.5
    paragraph.paragraph_format.space_before = Pt(space_before)
    paragraph.paragraph_format.space_after = Pt(6)
    add_text(paragraph, text)


def equation(document, text: str) -> None:
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    paragraph.paragraph_format.left_indent = Inches(1.35)
    paragraph.paragraph_format.line_spacing = 1.0
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(0)
    add_text(paragraph, text, size=10.5, font=MONO_FONT)


def spacer(document, points: float = 6) -> None:
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.line_spacing = 1.0
    add_text(paragraph, "", size=points)


def code_block(document, text: str) -> None:
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    paragraph.paragraph_format.line_spacing = 1.0
    paragraph.paragraph_format.space_before = Pt(6)
    paragraph.paragraph_format.space_after = Pt(10)
    paragraph.paragraph_format.left_indent = Inches(0.25)
    add_text(paragraph, text, size=9.5, font=MONO_FONT)


def caption(document, text: str) -> None:
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(10)
    paragraph.paragraph_format.space_after = Pt(4)
    paragraph.paragraph_format.keep_with_next = True
    add_text(paragraph, text, size=9.5, bold=True)


def table(document, headers, rows, widths, size: float = 9) -> None:
    grid = document.add_table(rows=1, cols=len(headers))
    grid.style = "Table Grid"
    grid.alignment = WD_TABLE_ALIGNMENT.CENTER
    grid.autofit = False

    header_row = grid.rows[0]
    keep_header_row(header_row)
    prevent_row_split(header_row)
    for cell, label, width in zip(header_row.cells, headers, widths):
        cell.width = Inches(width)
        cell.text = label
        tighten_cell(cell, size, bold=True)

    for values in rows:
        row = grid.add_row()
        prevent_row_split(row)
        for cell, value, width in zip(row.cells, values, widths):
            cell.width = Inches(width)
            cell.text = str(value)
            tighten_cell(cell, size)

    for column, width in zip(grid.columns, widths):
        column.width = Inches(width)

    spacer = document.add_paragraph()
    spacer.paragraph_format.space_before = Pt(0)
    spacer.paragraph_format.space_after = Pt(0)
    spacer.paragraph_format.line_spacing = 1.0
    add_text(spacer, "", size=8)


def bullet(document, label: str, url: str | None = None) -> None:
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    paragraph.paragraph_format.left_indent = Inches(0.3)
    paragraph.paragraph_format.first_line_indent = Inches(-0.2)
    paragraph.paragraph_format.line_spacing = 1.5
    paragraph.paragraph_format.space_after = Pt(2)
    add_text(paragraph, f"\u2022  {label}: ")
    if url:
        add_hyperlink(paragraph, url)


# --------------------------------------------------------------------------
# Sections
# --------------------------------------------------------------------------

def build_styles(document) -> None:
    normal = document.styles["Normal"]
    set_style_font(normal, BODY_FONT, 11)
    force_black(normal)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    for name, size, before, after in (("Heading 1", 14, 18, 8),
                                      ("Heading 2", 12, 12, 6)):
        style = document.styles[name]
        set_style_font(style, BODY_FONT, size)
        style.font.bold = True
        style.font.italic = False
        force_black(style)
        style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.line_spacing = 1.5
        style.paragraph_format.keep_with_next = True


def build_title_page(document, date_text: str) -> None:
    for _ in range(5):
        document.add_paragraph()

    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_text(paragraph, "Laboratory Exercise No. 4", size=16, bold=True)

    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(18)
    add_text(paragraph, "Single-Layer Perceptron", size=26, bold=True)

    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_text(paragraph, "Learning the AND and OR Truth Tables from Scratch",
             size=13, italic=True)

    for _ in range(6):
        document.add_paragraph()

    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_text(paragraph, "Ken Cedrick Jimeno", size=14, bold=True)

    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_text(paragraph, "CSci 141 \u2014 Intelligent Systems", size=12)

    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_text(paragraph, date_text, size=12)


def build_toc(document) -> None:
    heading = document.add_paragraph()
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    heading.paragraph_format.space_after = Pt(18)
    add_text(heading, "Table of Contents", size=14, bold=True)

    entry = document.add_paragraph()
    entry.paragraph_format.line_spacing = 1.5
    add_toc_field(entry)


def build_introduction(document) -> None:
    document.add_heading("Introduction", level=1)

    body(document,
         "This laboratory exercise implements a single-layer perceptron that learns "
         "the AND and OR logical functions. The program builds the neuron, the training "
         "loop, and the training trace from first principles, using only the Python "
         "standard library, so that every weight adjustment can be inspected by hand "
         "instead of taken on trust.")

    body(document,
         "A perceptron is the simplest trainable classifier. It forms a weighted sum "
         "of its inputs, adds a bias, and passes the result through a step activation "
         "function. Learning is error-driven: after each training sample the weights "
         "move in the direction that reduces the difference between the target and the "
         "prediction. Because the correction uses only the current sample, the method "
         "is an example of online, or stochastic, gradient descent on a perceptron "
         "loss.")

    body(document, "The model and its learning rule are as follows:")
    equation(document, "net        = w1 * A + w2 * B + bias")
    equation(document, "prediction = 1 if net >= 0, otherwise 0")
    equation(document, "error      = target - prediction")
    equation(document, "w1         = w1 + learning_rate * error * A")
    equation(document, "w2         = w2 + learning_rate * error * B")
    equation(document, "bias       = bias + learning_rate * error")
    spacer(document, 8)

    body(document,
         "A net input of exactly zero predicts class 1, so the decision boundary "
         "belongs to the positive class. Both target functions are linearly separable: "
         "a single straight line in the input plane separates the positive from the "
         "negative examples. AND has one positive case, (1,1), while OR has three. "
         "Because both are separable, one neuron with two inputs is sufficient and "
         "training is guaranteed to terminate. XOR is the standard counterexample: its "
         "positive cases sit on opposite corners of the input square, no single "
         "straight line separates them, and this program therefore does not attempt "
         "it.")

    caption(document, "Table 1. Truth tables for the two target functions.")
    table(document,
          ["A", "B", "AND", "OR"],
          [[*inputs, and_target, or_target]
           for inputs, and_target, or_target
           in zip(INPUTS, TARGETS["AND"], TARGETS["OR"])],
          [1.0, 1.0, 1.0, 1.0], size=10)

    body(document,
         "Each gate is trained from scratch. Weights and bias start at zero, the four "
         "samples are visited in the fixed order (0,0), (0,1), (1,0), (1,1), and the "
         "learning rate is 1 unless it is overridden on the command line. An epoch that "
         "produces no mistakes is treated as confirmation of convergence, and the "
         "confirmation epoch is included in the reported count.")


def build_execution_flow(document) -> None:
    document.add_heading("Program Execution Flow", level=1)

    body(document,
         "The implementation is one module with a pure training core and a thin "
         "command-line wrapper. A run proceeds through the following steps.")

    steps = [
        "Parse the gate (and, or, both), the learning rate, and the epoch limit.",
        "Validate the inputs: the gate must be known, the rate must be finite and "
        "positive, and at least one epoch must be allowed.",
        "Initialise the weights and bias to zero and create a fresh trace for each "
        "requested gate.",
        "For each sample, compute the net input and the prediction before any update.",
        "Compute the error as target minus prediction, then update w1, w2, and the "
        "bias.",
        "Record the step: the sample, the pre-update prediction, and the post-update "
        "parameters.",
        "Repeat until a complete epoch contains no mistakes, or until the epoch limit "
        "is reached.",
        "Print the trace, then re-evaluate all four input pairs with the final "
        "parameters.",
        "Exit with status 0 if every requested gate converged, or 1 otherwise.",
    ]
    for number, text in enumerate(steps, start=1):
        paragraph = document.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        paragraph.paragraph_format.left_indent = Inches(0.35)
        paragraph.paragraph_format.first_line_indent = Inches(-0.35)
        paragraph.paragraph_format.line_spacing = 1.5
        paragraph.paragraph_format.space_after = Pt(2)
        add_text(paragraph, f"{number}.  ")
        add_text(paragraph, text)

    body(document,
         "Two design choices keep the code testable. The train() function is pure: it "
         "takes a gate and the hyperparameters, returns an immutable TrainingResult, "
         "and prints nothing. The format_result() function owns all presentation, so "
         "the trace can be verified independently of how it is displayed.",
         space_before=8)

    body(document, "The program is run from the repository root:")
    code_block(document, "python perceptron_lab4.py --gate both")

    caption(document, "Table 2. Command-line options.")
    table(document,
          ["Option", "Default", "Description"],
          [["--gate", "both", "Function to learn: and, or, or both."],
           ["--learning-rate", "1.0", "Positive step size for every update."],
           ["--max-epochs", "100", "Maximum passes over the training set."]],
          [1.7, 0.9, 3.9], size=9.5)

    body(document,
         "A mistake-free epoch is required because one clean sample says nothing about "
         "the other three; rows with zero error appear inside epochs that still contain "
         "mistakes. The epoch limit exists so that a non-separable target, or an "
         "unfortunate learning rate, cannot loop forever. Reaching the limit is "
         "reported in the output and produces a non-zero exit status.")


def trace_rows(result):
    rows = []
    for step in result.steps:
        after = step.after
        rows.append([step.epoch, step.inputs[0], step.inputs[1], step.target,
                     f"{step.net:g}", step.prediction, step.error,
                     f"{after.w1:g}", f"{after.w2:g}", f"{after.bias:g}"])
    return rows


def final_rows(result):
    parameters = result.parameters
    return [[*inputs, target, f"{parameters.net_input(inputs):g}",
             parameters.predict(inputs),
             "PASS" if parameters.predict(inputs) == target else "FAIL"]
            for inputs, target in zip(INPUTS, TARGETS[result.gate])]


def build_traces(document) -> None:
    document.add_heading("Training Trace", level=1)

    body(document,
         "Each row below is one sample. The net input, prediction (Pred), and error "
         "are computed before the update; w1, w2, and bias are shown after it. Ep is "
         "the epoch number and T is the target. A non-zero error is what triggers "
         "learning, so rows with E = 0 leave the parameters unchanged.")

    and_result = train("AND")
    caption(document,
            "Table 3. Complete training trace for the AND gate "
            f"({len(and_result.steps)} updates over {and_result.epochs} epochs).")
    table(document,
          ["Ep", "A", "B", "T", "Net", "Pred", "Error", "w1", "w2", "Bias"],
          trace_rows(and_result),
          [0.45, 0.4, 0.4, 0.55, 0.55, 0.55, 0.6, 0.85, 0.85, 0.8], size=8.5)

    parameters = and_result.parameters
    body(document,
         f"The AND gate converges in {and_result.epochs} epochs. Its final model is "
         f"net = {parameters.w1:g}A + {parameters.w2:g}B + ({parameters.bias:g}), "
         "which predicts 0 for every input except (1,1). The complete trace is "
         "reproduced in Table 3 so that each update can be checked against the "
         "learning rule.")

    caption(document, "Table 4. Final truth table for the AND gate.")
    table(document,
          ["A", "B", "Target", "Net", "Prediction", "Result"],
          final_rows(and_result), [0.8] * 6, size=9.5)

    or_result = train("OR")
    caption(document,
            "Table 5. Complete training trace for the OR gate "
            f"({len(or_result.steps)} updates over {or_result.epochs} epochs).")
    table(document,
          ["Ep", "A", "B", "T", "Net", "Pred", "Error", "w1", "w2", "Bias"],
          trace_rows(or_result),
          [0.45, 0.4, 0.4, 0.55, 0.55, 0.55, 0.6, 0.85, 0.85, 0.8], size=8.5)

    parameters = or_result.parameters
    body(document,
         f"The OR gate converges in {or_result.epochs} epochs. Its final model is "
         f"net = {parameters.w1:g}A + {parameters.w2:g}B + ({parameters.bias:g}), "
         "which predicts 1 whenever at least one input is 1.")

    caption(document, "Table 6. Final truth table for the OR gate.")
    table(document,
          ["A", "B", "Target", "Net", "Prediction", "Result"],
          final_rows(or_result), [0.8] * 6, size=9.5)

    caption(document, "Table 7. Summary of training results.")
    table(document,
          ["Gate", "Epochs", "w1", "w2", "Bias", "Accuracy"],
          [["AND", and_result.epochs, f"{and_result.parameters.w1:g}",
            f"{and_result.parameters.w2:g}", f"{and_result.parameters.bias:g}",
            "4 / 4"],
           ["OR", or_result.epochs, f"{or_result.parameters.w1:g}",
            f"{or_result.parameters.w2:g}", f"{or_result.parameters.bias:g}",
            "4 / 4"]],
          [1.0, 1.0, 1.0, 1.0, 1.0, 1.2], size=10)

    body(document,
         "Both gates converge far below the 100-epoch default and all eight final "
         "predictions pass. Convergence is checked per epoch rather than per sample: "
         "the first AND epoch, for example, contains three error-free rows but still "
         "ends with a mistake, so a single clean sample is not sufficient evidence "
         "that learning is complete.")


def build_links(document) -> None:
    heading = document.add_heading("Link to Program Files", level=1)
    heading.paragraph_format.page_break_before = True

    body(document,
         "The complete source code, this report, the captured console output, and a "
         "README are published in a public GitHub repository. The links below point "
         "to the repository and to the individual files.")

    bullet(document, "Repository", REPO_URL)
    bullet(document, "Source code",
           f"{REPO_URL}/blob/main/perceptron_lab4.py")
    bullet(document, "Training console output",
           f"{REPO_URL}/blob/main/perceptron_console_output.txt")
    bullet(document, "README",
           f"{REPO_URL}/blob/main/README.md")
    bullet(document, "This report",
           f"{REPO_URL}/blob/main/Perceptron_Lab4_Documentation.docx")

    body(document,
         "The program requires Python 3.10 or newer and no third-party packages. To "
         "reproduce the traces in this report, clone the repository and run the "
         "following command from its root.", space_before=10)
    code_block(document, "python perceptron_lab4.py --gate both")

    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    paragraph.paragraph_format.space_before = Pt(18)
    add_text(paragraph, "Prepared by Ken Cedrick Jimeno for CSci 141 \u2014 "
                        "Intelligent Systems.", size=10.5, italic=True)


def build_document() -> Path:
    document = Document()
    build_styles(document)

    section = document.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    for margin in ("left_margin", "right_margin"):
        setattr(section, margin, Inches(1))
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)

    date_text = datetime.now().strftime("%B %d, %Y")
    build_title_page(document, date_text)

    document.add_section(WD_SECTION.NEW_PAGE)
    build_toc(document)

    document.add_section(WD_SECTION.NEW_PAGE)
    build_introduction(document)
    build_execution_flow(document)
    build_traces(document)
    build_links(document)

    # Page layout: the title page carries no footer, numbering starts at 1 on
    # the table of contents, and the body continues that count.
    sections = document.sections
    toc_section = sections[1]
    content_section = sections[2]
    toc_section.footer.is_linked_to_previous = False
    footer_paragraph = toc_section.footer.paragraphs[0]
    footer_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_page_number(footer_paragraph)
    restart_numbering(toc_section)
    clear_numbering(content_section)

    properties = document.core_properties
    properties.title = "Laboratory Exercise No. 4 - Single-Layer Perceptron"
    properties.author = "Ken Cedrick Jimeno"
    properties.subject = "CSci 141 - Intelligent Systems"
    properties.comments = ("AND and OR single-layer perceptron: flow, complete "
                           "training traces, results, and source links.")

    document.save(OUTPUT)
    return OUTPUT


def update_fields_with_word(path: Path) -> bool:
    """Populate the TOC and page fields. Returns False if Word is unavailable."""
    try:
        import win32com.client as win32
    except ImportError:
        return False

    application = None
    document = None
    try:
        application = win32.Dispatch("Word.Application")
        application.Visible = False
        application.DisplayAlerts = 0
        document = application.Documents.Open(str(path))
        document.Fields.Update()
        for table_of_contents in document.TablesOfContents:
            table_of_contents.Update()
        document.Save()
        return True
    except Exception as error:  # pragma: no cover - depends on desktop Word
        print(f"Word field update skipped: {error}")
        return False
    finally:
        if document is not None:
            try:
                document.Close(False)
            except Exception:
                pass
        if application is not None:
            try:
                application.Quit()
            except Exception:
                pass


def normalize_toc_style(path: Path) -> bool:
    """Apply the body font to the TOC styles Word creates during the update."""
    document = Document(path)
    changed = False
    for style in document.styles:
        if style.name.lower() not in ("toc 1", "toc 2", "toc 3"):
            continue
        set_style_font(style, BODY_FONT, 11)
        force_black(style)
        style.paragraph_format.line_spacing = 1.5
        style.paragraph_format.space_after = Pt(6)
        changed = True
    if changed:
        document.save(path)
    return changed


def restore_hyperlinks(path: Path) -> int:
    """Re-wrap URL runs as hyperlinks if the field-update step flattened them."""
    document = Document(path)
    repaired = 0
    for paragraph in document.paragraphs:
        index = paragraph.text.find("https://")
        if index < 0 or paragraph._p.findall(qn("w:hyperlink")):
            continue
        prefix = paragraph.text[:index]
        url = paragraph.text[index:].strip()
        for child in list(paragraph._p):
            if child.tag in (qn("w:r"), qn("w:hyperlink"),
                             qn("w:bookmarkStart"), qn("w:bookmarkEnd")):
                paragraph._p.remove(child)
        run = paragraph.add_run(prefix)
        set_run_font(run, BODY_FONT, 11)
        add_hyperlink(paragraph, url, url, 11)
        repaired += 1
    if repaired:
        document.save(path)
    return repaired


def main() -> None:
    path = build_document()
    updated = update_fields_with_word(path)
    if updated:
        normalize_toc_style(path)
    restore_hyperlinks(path)
    note = "fields updated" if updated else "TOC will populate on open in Word"
    print(f"Created {path.name} ({note}).")


if __name__ == "__main__":
    main()
