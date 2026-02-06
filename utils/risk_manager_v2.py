#!/usr/bin/env python3
# Copyright (c) 2025 AurumBotX
# SPDX-License-Identifier: MIT

"""
Risk Manager V2 - controlli base per validazione trade.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class RiskConfig:
    min_confidence: float = 0.6
    max_position_size: float = 0.05


class RiskManagerV2:
    def __init__(self, config: RiskConfig | None = None):
        self.config = config or RiskConfig()

    def validate(self, signal: Dict) -> Dict:
        errors: List[str] = []
        confidence = signal.get("confidence")
        if confidence is None:
            errors.append("Missing confidence")
        elif confidence < self.config.min_confidence:
            errors.append("Confidence below threshold")

        action = signal.get("action")
        if action not in {"buy", "sell"}:
            errors.append("Invalid action")

        return {"valid": not errors, "errors": errors}
