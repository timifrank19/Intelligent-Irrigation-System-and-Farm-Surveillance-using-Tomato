# =============================================================================
# FILE:      irrigation/fuzzy.py
# LOCATION:  Intelligent_Tomato_Farm/irrigation/fuzzy.py
# PURPOSE:   Fuzzy logic irrigation decision. Preserved from S_Backend.py.
# =============================================================================

from __future__ import annotations
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl


class FuzzyIrrigationDecider:
    def __init__(self):
        self._setup()

    def _setup(self):
        self.soil = ctrl.Antecedent(np.arange(0, 0.6, 0.01), "soil")
        self.temp = ctrl.Antecedent(np.arange(15, 45, 1), "temp")
        self.confidence = ctrl.Antecedent(np.arange(0, 101, 1), "confidence")
        self.pump = ctrl.Consequent(np.arange(0, 101, 1), "pump")

        self.soil["dry"] = fuzz.trimf(self.soil.universe, [0, 0, 0.30])
        self.soil["optimal"] = fuzz.trimf(self.soil.universe, [0.25, 0.35, 0.45])
        self.soil["wet"] = fuzz.trimf(self.soil.universe, [0.40, 0.60, 0.60])

        self.temp["low"] = fuzz.trimf(self.temp.universe, [15, 15, 25])
        self.temp["normal"] = fuzz.trimf(self.temp.universe, [22, 28, 34])
        self.temp["high"] = fuzz.trimf(self.temp.universe, [32, 40, 45])

        self.confidence["low"] = fuzz.trimf(self.confidence.universe, [0, 0, 50])
        self.confidence["high"] = fuzz.trimf(self.confidence.universe, [50, 100, 100])

        self.pump["off"] = fuzz.trimf(self.pump.universe, [0, 0, 20])
        self.pump["medium"] = fuzz.trimf(self.pump.universe, [15, 50, 85])
        self.pump["on"] = fuzz.trimf(self.pump.universe, [80, 100, 100])

        r1 = ctrl.Rule(self.soil["dry"] & self.temp["high"], self.pump["on"])
        r2 = ctrl.Rule(self.soil["dry"] & self.temp["normal"], self.pump["medium"])
        r3 = ctrl.Rule(self.soil["optimal"], self.pump["off"])
        r4 = ctrl.Rule(self.soil["wet"], self.pump["off"])
        r5 = ctrl.Rule(self.confidence["low"] & self.temp["high"], self.pump["medium"])

        self.system = ctrl.ControlSystem([r1, r2, r3, r4, r5])
        self.sim = ctrl.ControlSystemSimulation(self.system)

    def decide(self, soil, temp, confidence=100.0) -> float:
        try:
            self.sim.input["soil"] = max(0.15, min(0.55, float(soil)))
            self.sim.input["temp"] = max(15.0, min(45.0, float(temp)))
            self.sim.input["confidence"] = max(0.0, min(100.0, float(confidence)))
            self.sim.compute()
            return float(self.sim.output["pump"])
        except Exception:
            return 50.0
