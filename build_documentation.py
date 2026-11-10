"""Rebuild output artifacts. Requires reportlab and Pillow; the lab program does not."""

from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
    Image as PdfImage,
)

from perceptron_lab4 import INPUTS, TARGETS, train


ROOT = Path(__file__).resolve().parent


def capture_output() -> str:
    result = subprocess.run(
        [sys.executable, str(ROOT / "perceptron_lab4.py"), "--gate", "both"],
        check=True, capture_output=True, text=True,
    )
    (ROOT / "perceptron_console_output.txt").write_text(result.stdout, encoding="utf-8")
    return result.stdout


def render_console(output: str) -> Path:
    """Render captured stdout faithfully; this is not an OS terminal screenshot."""
    font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 20)
    lines = output.splitlines()
    width = max(1100, int(max(font.getlength(line) for line in lines)) + 64)
    picture = Image.new("RGB", (width, 88 + len(lines) * 27), "#111827")
    draw = ImageDraw.Draw(picture)
    draw.text((30, 22), "CAPTURED CONSOLE OUTPUT | python perceptron_lab4.py --gate both",
              font=font, fill="#67e8f9")
    for index, line in enumerate(lines):
        draw.text((30, 70 + index * 27), line, font=font, fill="#e5e7eb")
    destination = ROOT / "perceptron_console_output.png"
    picture.save(destination)
    return destination


def build_pdf(console_image: Path) -> None:
    styles = getSampleStyleSheet()
    styles["Title"].textColor = colors.HexColor("#12344a")
    styles["Heading1"].textColor = colors.HexColor("#12344a")
    styles["BodyText"].leading = 15
    story = []

    def paragraph(text: str, style: str = "BodyText") -> None:
        story.extend([Paragraph(text, styles[style]), Spacer(1, 10)])

    def table(rows, widths=None):
        item = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
        item.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#12344a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.HexColor("#edf4f7"), colors.white]),
            ("LINEBELOW", (0, 0), (-1, 0), 1, colors.HexColor("#2397a7")),
        ]))
        story.extend([item, Spacer(1, 12)])

    paragraph("Laboratory Activity #4", "Title")
    paragraph("Single-layer perceptron | AND and OR", "Heading2")
    paragraph("Purpose", "Heading1")
    paragraph("Train one two-input neuron independently for each logical function. "
              "Both truth tables are linearly separable, so each can be represented "
              "by a single perceptron. No hidden layers or external ML libraries are used.")
    table([["A", "B", "AND", "OR"],
           *[[*x, a, o] for x, a, o in zip(INPUTS, TARGETS["AND"], TARGETS["OR"])]],
          [110] * 4)
    paragraph("Model and learning rule", "Heading1")
    paragraph("net = w1 * A + w2 * B + bias<br/>"
              "prediction = 1 if net &gt;= 0, otherwise 0<br/>"
              "error = target - prediction<br/>"
              "w1 = w1 + learning_rate * error * A<br/>"
              "w2 = w2 + learning_rate * error * B<br/>"
              "bias = bias + learning_rate * error")
    paragraph("Each gate starts at w1 = w2 = bias = 0 with learning rate 1. "
              "Samples always follow (0,0), (0,1), (1,0), (1,1). Updates happen "
              "immediately after each sample. Training stops after a full epoch "
              "with zero mistakes, or at the 100-epoch limit. The final confirmation "
              "epoch is included in the epoch count.")
    paragraph("Program execution flow", "Heading1")
    paragraph("1. Parse the gate, learning rate, and epoch limit.<br/>"
              "2. Initialize a fresh model and training trace for each gate.<br/>"
              "3. For each sample, compute net input, prediction, and error.<br/>"
              "4. Update weights and bias; record that training step.<br/>"
              "5. Repeat epochs until convergence or the limit.<br/>"
              "6. Print the trace and evaluate all four inputs with the final model.<br/>"
              "7. Exit with status 0 on convergence, or 1 if the limit is reached.")

    for gate in TARGETS:
        result = train(gate)
        story.append(PageBreak())
        paragraph(f"{gate}: complete training trace", "Title")
        paragraph("Net, prediction (Y), and error (E) are computed before the update. "
                  "The last three columns show parameters after that sample's update. "
                  "T is the target; E = T - Y. Nonzero errors trigger learning.")
        rows = [["Epoch", "A", "B", "T", "Net", "Y", "E", "w1", "w2", "Bias"]]
        for step in result.steps:
            p = step.after
            rows.append([step.epoch, *step.inputs, step.target, f"{step.net:g}",
                         step.prediction, step.error, f"{p.w1:g}", f"{p.w2:g}", f"{p.bias:g}"])
        table(rows, [47] + [43] * 9)
        p = result.parameters
        paragraph(f"Converged in {result.epochs} epochs. Final model: "
                  f"net = {p.w1:g} * A + {p.w2:g} * B + ({p.bias:g}).")
        table([["A", "B", "Target", "Final net", "Prediction", "Check"],
               *[[*x, t, f"{p.net_input(x):g}", p.predict(x),
                  "PASS" if p.predict(x) == t else "FAIL"]
                 for x, t in zip(INPUTS, TARGETS[gate])]], [74] * 6)

    story.append(PageBreak())
    paragraph("Console output and source", "Title")
    paragraph("The image below is a rendering of captured program stdout, "
              "not an operating-system terminal screenshot. The accompanying PNG "
              "and TXT files contain the full trace. If a literal terminal screenshot "
              "is required for submission, run the command below and capture your terminal.")
    # Preserve the full console image at legible width on its own file; show
    # just the final OR verification here so report text remains readable.
    with Image.open(console_image) as image:
        excerpt = image.crop((0, image.height - 10 * 27, image.width, image.height))
        excerpt_path = ROOT / "tmp" / "console_excerpt.png"
        excerpt_path.parent.mkdir(exist_ok=True)
        excerpt.save(excerpt_path)
    story.append(PdfImage(str(excerpt_path), width=460,
                          height=460 * excerpt.height / excerpt.width))
    story.append(Spacer(1, 14))
    paragraph("Run the program", "Heading1")
    paragraph('<font face="Courier">python perceptron_lab4.py --gate both</font><br/>'
              'Use <font face="Courier">--gate and</font> or '
              '<font face="Courier">--gate or</font> for a single function. '
              'Options: <font face="Courier">--learning-rate 1 --max-epochs 100</font>. '
              'Python 3.10 or newer is required; the lab program uses only the standard library.')
    paragraph("Source code", "Heading1")
    paragraph('<link href="perceptron_lab4.py" color="#087e96">'
              'Open perceptron_lab4.py (relative local link)</link><br/>'
              "Keep the PDF beside the Python file. Some PDF viewers block local links. "
              "This is a local source link; a public submission URL requires uploading "
              "the source to your own repository or file-sharing service.")
    paragraph("Code organization", "Heading1")
    paragraph("Parameters owns the neuron's state and prediction. TrainingStep and "
              "TrainingResult preserve an immutable trace. train() performs learning "
              "without printing; format_result() handles presentation; main() handles "
              "command-line arguments. Imports do not trigger execution.")
    paragraph("Validation and interpretation", "Heading1")
    paragraph("All eight final truth-table predictions pass. Each trace row is checked "
              "against the learning rule; the final epoch has no errors. Invalid training "
              "settings are rejected, and a one-epoch limit reports non-convergence. "
              "These checks establish correctness for these truth tables, not performance "
              "on unseen datasets. A single perceptron cannot represent XOR.")

    def footer(canvas, doc):
        canvas.setStrokeColor(colors.HexColor("#c7d8e0"))
        canvas.line(50, 44, A4[0] - 50, 44)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#526575"))
        canvas.drawString(50, 30, "INTELLIGENT SYSTEMS / LAB 04")
        canvas.drawRightString(A4[0] - 50, 30, str(doc.page))

    document = SimpleDocTemplate(str(ROOT / "Perceptron_Lab4_Documentation.pdf"),
                                 pagesize=A4, rightMargin=50, leftMargin=50,
                                 topMargin=42, bottomMargin=58,
                                 title="Laboratory Activity 4 - Single-layer Perceptron")
    document.build(story, onFirstPage=footer, onLaterPages=footer)


def main() -> None:
    output = capture_output()
    build_pdf(render_console(output))
    print("Created PDF documentation and captured console PNG/TXT.")


if __name__ == "__main__":
    main()
