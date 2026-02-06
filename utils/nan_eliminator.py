#!/usr/bin/env python3
# Copyright (c) 2025 AurumBotX
# SPDX-License-Identifier: MIT

"""
NaN Eliminator - pulizia robusta di NaN e infiniti.
"""
from __future__ import annotations

import logging
from typing import Dict, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class NaNEliminator:
    def __init__(self, nan_threshold: float = 0.5) -> None:
        self.nan_threshold = nan_threshold

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            return df

        df = df.copy()
        df = df.replace([np.inf, -np.inf], np.nan)

        threshold = int(len(df) * self.nan_threshold)
        df = df.dropna(thresh=threshold, axis=1)
        df = df.dropna(axis=0, how="any")

        return df

    def report(self, df: Optional[pd.DataFrame]) -> Dict[str, float]:
        if df is None:
            return {"nan_ratio": 1.0, "inf_ratio": 1.0}

        total = df.size if df.size > 0 else 1
        nan_ratio = float(df.isna().sum().sum()) / total
        inf_ratio = float(np.isinf(df.select_dtypes(include=[np.number])).sum().sum()) / total
        return {"nan_ratio": nan_ratio, "inf_ratio": inf_ratio}
