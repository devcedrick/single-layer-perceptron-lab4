"""Train a two-input perceptron for the AND and OR truth tables.

Run: python perceptron_lab4.py --gate both
Uses only the Python standard library (Python 3.10 or newer).
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass


INPUTS = ((0, 0), (0, 1), (1, 0), (1, 1))
TARGETS = {"AND": (0, 0, 0, 1), "OR": (0, 1, 1, 1)}


@dataclass(frozen=True)
class Parameters:
    """Weights and bias of a single neuron."""

    w1: float = 0.0
    w2: float = 0.0
    bias: float = 0.0

    def net_input(self, inputs: tuple[int, int]) -> float:
        return self.w1 * inputs[0] + self.w2 * inputs[1] + self.bias

    def predict(self, inputs: tuple[int, int]) -> int:
        """Use a step activation: a zero net input predicts class 1."""
        return int(self.net_input(inputs) >= 0)


@dataclass(frozen=True)
class TrainingStep:
    """One sample's prediction before updating, and parameters afterward."""

    epoch: int
    inputs: tuple[int, int]
    target: int
    net: float
    prediction: int
    error: int
    after: Parameters


@dataclass(frozen=True)
class TrainingResult:
    gate: str
    parameters: Parameters
    steps: tuple[TrainingStep, ...]
    epochs: int
    converged: bool


def train(gate: str, learning_rate: float = 1.0,
          max_epochs: int = 100) -> TrainingResult:
    """Apply online perceptron updates in the fixed INPUTS order.

    Stop after a complete epoch with no mistakes. Each call starts with
    zero weights and bias so AND and OR are learned independently.
    """
    if gate not in TARGETS:
        raise ValueError(f"Unsupported gate: {gate}")
    if not 0 < learning_rate < float("inf"):
        raise ValueError("learning_rate must be finite and positive")
    if max_epochs < 1:
        raise ValueError("max_epochs must be at least 1")

    parameters = Parameters()
    steps: list[TrainingStep] = []
    for epoch in range(1, max_epochs + 1):
        mistakes = 0
        for inputs, target in zip(INPUTS, TARGETS[gate]):
            net = parameters.net_input(inputs)
            prediction = parameters.predict(inputs)
            error = target - prediction
            mistakes += int(error != 0)
            adjustment = learning_rate * error
            parameters = Parameters(
                w1=parameters.w1 + adjustment * inputs[0],
                w2=parameters.w2 + adjustment * inputs[1],
                bias=parameters.bias + adjustment,
            )
            steps.append(TrainingStep(
                epoch, inputs, target, net, prediction, error, parameters,
            ))
        if mistakes == 0:
            return TrainingResult(gate, parameters, tuple(steps), epoch, True)

    return TrainingResult(gate, parameters, tuple(steps), max_epochs, False)


def format_result(result: TrainingResult) -> str:
    """Create a readable training trace and final truth table."""
    lines = [
        f"{result.gate} GATE", "=" * 68,
        "Ep  A B  Target  Net  Pred  Error  |  Updated w1  w2  bias",
        "-" * 68,
    ]
    for step in result.steps:
        p = step.after
        lines.append(
            f"{step.epoch:2}  {step.inputs[0]} {step.inputs[1]}"
            f"  {step.target:6}  {step.net:3g}  {step.prediction:4}"
            f"  {step.error:5}  |  {p.w1:10g} {p.w2:3g} {p.bias:5g}"
        )
    status = "Converged" if result.converged else "Epoch limit reached"
    p = result.parameters
    lines.extend([
        "", f"{status} after {result.epochs} epochs.",
        f"Final weights: w1={p.w1:g}, w2={p.w2:g}, bias={p.bias:g}",
        "Final truth table:", "A B | Target | Prediction | Result",
    ])
    for inputs, target in zip(INPUTS, TARGETS[result.gate]):
        prediction = p.predict(inputs)
        verdict = "PASS" if prediction == target else "FAIL"
        lines.append(
            f"{inputs[0]} {inputs[1]} | {target:6} | {prediction:10} | {verdict}"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", choices=("and", "or", "both"), default="both")
    parser.add_argument("--learning-rate", type=float, default=1.0)
    parser.add_argument("--max-epochs", type=int, default=100)
    args = parser.parse_args()
    gates = ("AND", "OR") if args.gate == "both" else (args.gate.upper(),)
    try:
        results = [train(gate, args.learning_rate, args.max_epochs)
                   for gate in gates]
    except ValueError as error:
        parser.error(str(error))
    print("\nLABORATORY ACTIVITY #4: SINGLE-LAYER PERCEPTRON")
    print(f"Learning rate: {args.learning_rate:g};\nInitial weights and bias: 0")
    print("Activation: 1 when net >= 0, otherwise 0\n")
    print("\n\n".join(format_result(result) for result in results))
    return 0 if all(result.converged for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
