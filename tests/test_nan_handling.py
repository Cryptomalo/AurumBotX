import pandas as pd

from utils.nan_eliminator import NaNEliminator


def test_nan_eliminator_removes_nan_and_inf():
    df = pd.DataFrame(
        {
            "Open": [1.0, 2.0, None],
            "Close": [1.1, float("inf"), 1.3],
            "Volume": [100, 200, 300],
        }
    )
    eliminator = NaNEliminator()
    cleaned = eliminator.clean(df)
    assert cleaned.isna().sum().sum() == 0
    assert cleaned.size > 0
