# Single-Layer Perceptron: AND and OR

A two-input single-layer perceptron written from scratch in Python. It learns the
AND and OR truth tables independently, starting from zero weights and bias, and
prints every weight update so the learning rule can be checked by hand.

**Course:** CSci 141 — Intelligent Systems
**Laboratory Exercise No. 4**
**Author:** Ken Cedrick A. Jimeno

No NumPy, no scikit-learn, no external machine-learning libraries — just the
Python standard library.

## Overview

A perceptron computes a weighted sum of its inputs and passes it through a step
activation. Training walks the four input pairs in a fixed order and applies an
online update after each one. An epoch that produces no mistakes is treated as
proof of convergence.

| Gate | Epochs to converge | Final weights and bias | Accuracy |
| ---- | ------------------ | ---------------------- | -------- |
| AND  | 6                  | `w1 = 2, w2 = 1, bias = -3` | 4 / 4 |
| OR   | 4                  | `w1 = 1, w2 = 1, bias = -1` | 4 / 4 |

Both functions are linearly separable, so a single neuron is enough. XOR is not,
and is deliberately out of scope.

## Requirements

- Python 3.10 or newer
- Nothing else. `perceptron_lab4.py` imports only `argparse` and `dataclasses`.

## Usage

```sh
python perceptron_lab4.py --gate both
```

Single gate, with a custom learning rate and epoch limit:

```sh
python perceptron_lab4.py --gate and
python perceptron_lab4.py --gate or --learning-rate 0.5 --max-epochs 200
```

| Option | Default | Description |
| ------ | ------- | ----------- |
| `--gate` | `both` | Which function to learn: `and`, `or`, or `both`. |
| `--learning-rate` | `1.0` | Positive step size applied to every update. |
| `--max-epochs` | `100` | Upper bound on passes over the training set. |

The program exits with status `0` when every requested gate converges and `1`
when the epoch limit is reached first. Invalid settings are rejected with a
usage error.

## Model and learning rule

```text
net        = w1 * A + w2 * B + bias
prediction = 1 if net >= 0 else 0
error      = target - prediction

w1   = w1   + learning_rate * error * A
w2   = w2   + learning_rate * error * B
bias = bias + learning_rate * error
```

A zero net input predicts 1, so the decision boundary itself belongs to the
positive class. Because a mistake-free epoch can only happen after the boundary
has settled, convergence is checked over a complete epoch rather than per
sample. Samples are always visited in the order `(0,0)`, `(0,1)`, `(1,0)`,
`(1,1)`.

The learning rate and epoch limit are validated up front: the rate must be
finite and positive, and at least one epoch must be allowed.

## Reading the trace

Each row is one sample. The prediction and error are computed **before** the
update; the three parameter columns show the weights and bias **after** it.

```text
Ep  A B  Target  Net  Pred  Error  |  Updated w1  w2  bias
 2  1 1       1   -1     0      1  |           2   1    -1
```

In that row the neuron sees net input `-1`, predicts `0`, and is wrong by `1`.
The update adds `1 * 1 * A = 1` to `w1`, `1 * 1 * B = 1` to `w2`, and `1` to the
bias.

After training, the program re-evaluates all four input pairs with the final
parameters and prints a `PASS` / `FAIL` verdict for each row.

## Repository layout

```text
.
├── perceptron_lab4.py              # model, training loop, trace formatting, CLI
├── Perceptron_Lab4_Documentation.docx  # lab report: flow, traces, results, links
├── perceptron_console_output.txt   # captured stdout of a real run
├── perceptron_console_output.png   # rendering of that capture, not an OS screenshot
├── build_documentation.py          # optional PDF/PNG rebuild; needs reportlab + Pillow
└── README.md
```

`build_documentation.py` is a convenience only: it captures the console output,
renders the PNG, and rebuilds the PDF report. It requires `reportlab` and
`Pillow`, which the lab program itself does not use.

## Code organization

| Component | Responsibility |
| --------- | -------------- |
| `Parameters` | Immutable neuron state; computes net input and prediction. |
| `TrainingStep` | One sample's pre-update prediction plus post-update parameters. |
| `TrainingResult` | Final parameters, full trace, epoch count, convergence flag. |
| `train()` | Learning only — no printing, no side effects. |
| `format_result()` | Presentation of a `TrainingResult`. |
| `main()` | Command-line parsing and exit status. |

Imports never execute the program; everything runs under `if __name__ ==
"__main__"`.

## Validation

- Both gates converge well inside the default limit (6 and 4 epochs).
- All eight final truth-table predictions pass.
- Each trace row follows from the previous one under the stated learning rule.
- The final epoch of each trace contains no errors.
- A one-epoch limit reports non-convergence and exits with status `1`.

These checks establish correctness for these two truth tables, not performance
on unseen data. The model has no hidden layer, no shuffling, and no notion of a
general decision boundary beyond what these four samples determine.

## Documentation

- `Perceptron_Lab4_Documentation.docx` — laboratory report with the execution
  flow, complete training traces, final results, and links to the source files.

## Academic context

Submitted as Laboratory Exercise No. 4 for CSci 141 — Intelligent Systems.
