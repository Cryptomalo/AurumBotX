#!/usr/bin/env python3
"""
Data Preprocessor V2 - normalizza dati e rimuove NaN/infiniti.
"""
from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd

from utils.nan_eliminator import NaNEliminator

logger = logging.getLogger(__name__)


class DataPreprocessorV2:
    """Preprocessore dati con pipeline robusta di pulizia."""

    def __init__(self) -> None:
        self.nan_eliminator = NaNEliminator()

    def preprocess(self, data: pd.DataFrame) -> Optional[pd.DataFrame]:
        if data is None or data.empty:
            logger.warning("DataPreprocessorV2: input vuoto")
            return None

        df = data.copy()
        df = self._standardize_columns(df)
        df = self.nan_eliminator.clean(df)
        df = self._clip_outliers(df)
        return df

    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        rename_map = {col: col.capitalize() for col in df.columns}
        df = df.rename(columns=rename_map)
        return df

    def _clip_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            series = df[col]
            if series.empty:
                continue
            lower, upper = series.quantile([0.01, 0.99])
            df[col] = series.clip(lower=lower, upper=upper)
        return df
