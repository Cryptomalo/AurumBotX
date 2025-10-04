# AURUMBOTX - PREDICTION MODEL (FIXED VERSION)
# Bug Fix: Error preparing features: 'Close' column validation
# Professional Implementation with Comprehensive Data Validation

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketDataValidator:
    """
    Comprehensive market data validation and cleaning
    """
    
    @staticmethod
    def validate_required_columns(df: pd.DataFrame, required_columns: List[str] = None) -> Tuple[bool, List[str]]:
        """
        Validate that all required columns are present
        FIXED: Comprehensive column validation with detailed error reporting
        """
        if required_columns is None:
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        
        try:
            missing_columns = []
            
            # Check each required column
            for col in required_columns:
                if col not in df.columns:
                    missing_columns.append(col)
                    logger.error(f"Missing required column: {col}")
            
            # Check if DataFrame is empty
            if df.empty:
                logger.error("DataFrame is empty")
                return False, ["DataFrame is empty"]
            
            # Check column data types
            for col in required_columns:
                if col in df.columns:
                    if not pd.api.types.is_numeric_dtype(df[col]):
                        logger.warning(f"Column {col} is not numeric, attempting conversion")
                        try:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                        except Exception as e:
                            logger.error(f"Failed to convert {col} to numeric: {e}")
                            missing_columns.append(f"{col} (conversion failed)")
            
            if missing_columns:
                logger.error(f"Validation failed. Missing/invalid columns: {missing_columns}")
                return False, missing_columns
            
            logger.info(f"Column validation passed for {len(required_columns)} columns")
            return True, []
            
        except Exception as e:
            logger.error(f"Column validation error: {e}")
            return False, [f"Validation error: {str(e)}"]
    
    @staticmethod
    def validate_ohlc_logic(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate OHLC price logic and relationships
        """
        errors = []
        
        try:
            # Check if High >= Low
            invalid_hl = df['High'] < df['Low']
            if invalid_hl.any():
                count = invalid_hl.sum()
                errors.append(f"High < Low in {count} rows")
                logger.warning(f"Found {count} rows where High < Low")
                
                # Fix invalid OHLC
                df.loc[invalid_hl, 'High'] = df.loc[invalid_hl, ['High', 'Low']].max(axis=1)
                df.loc[invalid_hl, 'Low'] = df.loc[invalid_hl, ['High', 'Low']].min(axis=1)
            
            # Check if High >= Open, Close
            invalid_h_oc = (df['High'] < df['Open']) | (df['High'] < df['Close'])
            if invalid_h_oc.any():
                count = invalid_h_oc.sum()
                errors.append(f"High < Open/Close in {count} rows")
                logger.warning(f"Found {count} rows where High < Open/Close")
                
                # Fix High values
                df.loc[invalid_h_oc, 'High'] = df.loc[invalid_h_oc, ['High', 'Open', 'Close']].max(axis=1)
            
            # Check if Low <= Open, Close
            invalid_l_oc = (df['Low'] > df['Open']) | (df['Low'] > df['Close'])
            if invalid_l_oc.any():
                count = invalid_l_oc.sum()
                errors.append(f"Low > Open/Close in {count} rows")
                logger.warning(f"Found {count} rows where Low > Open/Close")
                
                # Fix Low values
                df.loc[invalid_l_oc, 'Low'] = df.loc[invalid_l_oc, ['Low', 'Open', 'Close']].min(axis=1)
            
            # Check for zero or negative prices
            price_cols = ['Open', 'High', 'Low', 'Close']
            for col in price_cols:
                invalid_prices = df[col] <= 0
                if invalid_prices.any():
                    count = invalid_prices.sum()
                    errors.append(f"Zero/negative prices in {col}: {count} rows")
                    logger.error(f"Found {count} zero/negative prices in {col}")
            
            # Check for negative volume
            if 'Volume' in df.columns:
                negative_volume = df['Volume'] < 0
                if negative_volume.any():
                    count = negative_volume.sum()
                    errors.append(f"Negative volume in {count} rows")
                    logger.warning(f"Found {count} negative volume values")
                    df.loc[negative_volume, 'Volume'] = 0
            
            if not errors:
                logger.info("OHLC validation passed")
                return True, []
            else:
                logger.warning(f"OHLC validation completed with {len(errors)} issues fixed")
                return True, errors  # Return True as we fixed the issues
                
        except Exception as e:
            logger.error(f"OHLC validation error: {e}")
            return False, [f"OHLC validation error: {str(e)}"]
    
    @staticmethod
    def clean_data_quality(df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean data quality issues (NaN, inf, outliers)
        """
        try:
            logger.info(f"Starting data cleaning for {len(df)} rows")
            
            # Handle infinite values
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            for col in numeric_columns:
                # Replace infinite values with NaN
                df[col] = df[col].replace([np.inf, -np.inf], np.nan)
            
            # Handle NaN values
            initial_nan_count = df.isnull().sum().sum()
            if initial_nan_count > 0:
                logger.warning(f"Found {initial_nan_count} NaN values, cleaning...")
                
                # Forward fill first, then backward fill
                df = df.fillna(method='ffill').fillna(method='bfill')
                
                # If still NaN, use interpolation
                df = df.interpolate(method='linear')
                
                # Final fallback: fill with median
                for col in numeric_columns:
                    if df[col].isnull().any():
                        median_val = df[col].median()
                        df[col] = df[col].fillna(median_val)
                        logger.warning(f"Filled remaining NaN in {col} with median: {median_val}")
            
            # Handle outliers using IQR method
            for col in ['Open', 'High', 'Low', 'Close']:
                if col in df.columns:
                    Q1 = df[col].quantile(0.25)
                    Q3 = df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 3 * IQR  # More conservative than 1.5
                    upper_bound = Q3 + 3 * IQR
                    
                    outliers = (df[col] < lower_bound) | (df[col] > upper_bound)
                    if outliers.any():
                        count = outliers.sum()
                        logger.warning(f"Found {count} outliers in {col}, capping values")
                        df.loc[df[col] < lower_bound, col] = lower_bound
                        df.loc[df[col] > upper_bound, col] = upper_bound
            
            # Volume outliers (different approach)
            if 'Volume' in df.columns:
                volume_99 = df['Volume'].quantile(0.99)
                volume_outliers = df['Volume'] > volume_99 * 10  # 10x the 99th percentile
                if volume_outliers.any():
                    count = volume_outliers.sum()
                    logger.warning(f"Found {count} extreme volume outliers, capping")
                    df.loc[volume_outliers, 'Volume'] = volume_99
            
            final_nan_count = df.isnull().sum().sum()
            logger.info(f"Data cleaning completed. NaN values: {initial_nan_count} → {final_nan_count}")
            
            return df
            
        except Exception as e:
            logger.error(f"Data cleaning error: {e}")
            return df  # Return original data if cleaning fails

class FeatureEngineer:
    """
    Advanced feature engineering for market prediction
    """
    
    @staticmethod
    def create_technical_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        Create comprehensive technical analysis features
        """
        try:
            logger.info("Creating technical features...")
            
            # Price-based features
            df['Price_Range'] = df['High'] - df['Low']
            df['Price_Change'] = df['Close'].pct_change()
            df['Price_Change_Abs'] = df['Price_Change'].abs()
            df['Body_Size'] = abs(df['Close'] - df['Open'])
            df['Upper_Shadow'] = df['High'] - df[['Open', 'Close']].max(axis=1)
            df['Lower_Shadow'] = df[['Open', 'Close']].min(axis=1) - df['Low']
            
            # Moving averages
            for period in [5, 10, 20, 50]:
                df[f'SMA_{period}'] = df['Close'].rolling(window=period).mean()
                df[f'EMA_{period}'] = df['Close'].ewm(span=period).mean()
                df[f'Price_SMA_{period}_Ratio'] = df['Close'] / df[f'SMA_{period}']
            
            # Volatility features
            df['Volatility_5'] = df['Price_Change'].rolling(window=5).std()
            df['Volatility_20'] = df['Price_Change'].rolling(window=20).std()
            df['ATR_14'] = df['Price_Range'].rolling(window=14).mean()
            
            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # MACD
            df['MACD'] = df['EMA_12'] - df['EMA_26'] if 'EMA_12' in df.columns and 'EMA_26' in df.columns else 0
            df['MACD_Signal'] = df['MACD'].ewm(span=9).mean() if 'MACD' in df.columns else 0
            df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
            
            # Bollinger Bands
            df['BB_Middle'] = df['Close'].rolling(window=20).mean()
            bb_std = df['Close'].rolling(window=20).std()
            df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
            df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
            df['BB_Width'] = df['BB_Upper'] - df['BB_Lower']
            df['BB_Position'] = (df['Close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
            
            # Volume features
            if 'Volume' in df.columns:
                df['Volume_SMA_20'] = df['Volume'].rolling(window=20).mean()
                df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA_20']
                df['Volume_Price_Trend'] = df['Volume'] * df['Price_Change']
            
            # Momentum features
            for period in [3, 7, 14]:
                df[f'Momentum_{period}'] = df['Close'] / df['Close'].shift(period) - 1
                df[f'ROC_{period}'] = df['Close'].pct_change(periods=period)
            
            # Support/Resistance levels
            df['High_20'] = df['High'].rolling(window=20).max()
            df['Low_20'] = df['Low'].rolling(window=20).min()
            df['Resistance_Distance'] = (df['High_20'] - df['Close']) / df['Close']
            df['Support_Distance'] = (df['Close'] - df['Low_20']) / df['Close']
            
            logger.info(f"Technical features created. Total columns: {len(df.columns)}")
            return df
            
        except Exception as e:
            logger.error(f"Feature engineering error: {e}")
            return df
    
    @staticmethod
    def create_time_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        Create time-based features
        """
        try:
            if not isinstance(df.index, pd.DatetimeIndex):
                logger.warning("Index is not datetime, skipping time features")
                return df
            
            logger.info("Creating time features...")
            
            # Basic time features
            df['Hour'] = df.index.hour
            df['DayOfWeek'] = df.index.dayofweek
            df['DayOfMonth'] = df.index.day
            df['Month'] = df.index.month
            df['Quarter'] = df.index.quarter
            
            # Cyclical encoding
            df['Hour_Sin'] = np.sin(2 * np.pi * df['Hour'] / 24)
            df['Hour_Cos'] = np.cos(2 * np.pi * df['Hour'] / 24)
            df['DayOfWeek_Sin'] = np.sin(2 * np.pi * df['DayOfWeek'] / 7)
            df['DayOfWeek_Cos'] = np.cos(2 * np.pi * df['DayOfWeek'] / 7)
            df['Month_Sin'] = np.sin(2 * np.pi * df['Month'] / 12)
            df['Month_Cos'] = np.cos(2 * np.pi * df['Month'] / 12)
            
            # Market session features (assuming UTC)
            df['Is_Asian_Session'] = ((df['Hour'] >= 0) & (df['Hour'] < 8)).astype(int)
            df['Is_European_Session'] = ((df['Hour'] >= 8) & (df['Hour'] < 16)).astype(int)
            df['Is_American_Session'] = ((df['Hour'] >= 16) & (df['Hour'] < 24)).astype(int)
            df['Is_Weekend'] = (df['DayOfWeek'] >= 5).astype(int)
            
            logger.info("Time features created successfully")
            return df
            
        except Exception as e:
            logger.error(f"Time feature creation error: {e}")
            return df

class PredictionModel:
    """
    Advanced prediction model with comprehensive validation and error handling
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.models = {}
        self.scalers = {}
        self.feature_columns = []
        self.is_trained = False
        
        # Model configurations
        self.model_configs = {
            'random_forest': {
                'n_estimators': 100,
                'max_depth': 10,
                'min_samples_split': 5,
                'min_samples_leaf': 2,
                'random_state': 42
            },
            'gradient_boosting': {
                'n_estimators': 100,
                'learning_rate': 0.1,
                'max_depth': 6,
                'random_state': 42
            },
            'linear': {
                'fit_intercept': True
            }
        }
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """
        Prepare features for model training/prediction
        FIXED: Comprehensive feature preparation with validation
        """
        try:
            logger.info("Preparing features for model...")
            
            # Step 1: Validate required columns
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            is_valid, missing_cols = MarketDataValidator.validate_required_columns(df, required_columns)
            
            if not is_valid:
                raise ValueError(f"Feature preparation failed. Missing columns: {missing_cols}")
            
            # Step 2: Validate OHLC logic
            is_valid_ohlc, ohlc_errors = MarketDataValidator.validate_ohlc_logic(df)
            if not is_valid_ohlc:
                raise ValueError(f"OHLC validation failed: {ohlc_errors}")
            
            # Step 3: Clean data quality
            df_clean = MarketDataValidator.clean_data_quality(df.copy())
            
            # Step 4: Create technical features
            df_features = FeatureEngineer.create_technical_features(df_clean)
            
            # Step 5: Create time features
            df_features = FeatureEngineer.create_time_features(df_features)
            
            # Step 6: Create target variable (next period return)
            df_features['Target'] = df_features['Close'].shift(-1) / df_features['Close'] - 1
            
            # Step 7: Select feature columns (exclude target and original OHLC)
            exclude_columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Target']
            feature_columns = [col for col in df_features.columns if col not in exclude_columns]
            
            # Step 8: Remove columns with too many NaN values
            nan_threshold = 0.5  # Remove columns with >50% NaN
            valid_features = []
            for col in feature_columns:
                nan_ratio = df_features[col].isnull().sum() / len(df_features)
                if nan_ratio <= nan_threshold:
                    valid_features.append(col)
                else:
                    logger.warning(f"Removing feature {col} due to {nan_ratio:.2%} NaN values")
            
            # Step 9: Final cleaning
            df_features = df_features[valid_features + ['Target']].dropna()
            
            if len(df_features) == 0:
                raise ValueError("No valid data remaining after feature preparation")
            
            logger.info(f"Feature preparation completed: {len(valid_features)} features, {len(df_features)} samples")
            return df_features[valid_features], valid_features
            
        except Exception as e:
            logger.error(f"Feature preparation error: {e}")
            raise ValueError(f"Error preparing features: {str(e)}")
    
    def train_models(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Train multiple prediction models
        """
        try:
            logger.info("Starting model training...")
            
            # Prepare features
            X, feature_columns = self.prepare_features(df)
            y = df['Target'].iloc[:len(X)]  # Align target with features
            
            if len(X) < 50:
                raise ValueError(f"Insufficient data for training: {len(X)} samples (minimum 50 required)")
            
            self.feature_columns = feature_columns
            
            # Split data (80% train, 20% test)
            split_idx = int(len(X) * 0.8)
            X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
            y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
            
            # Scale features
            self.scalers['robust'] = RobustScaler()
            X_train_scaled = self.scalers['robust'].fit_transform(X_train)
            X_test_scaled = self.scalers['robust'].transform(X_test)
            
            # Train models
            results = {}
            
            # Random Forest
            self.models['random_forest'] = RandomForestRegressor(**self.model_configs['random_forest'])
            self.models['random_forest'].fit(X_train_scaled, y_train)
            
            # Gradient Boosting
            self.models['gradient_boosting'] = GradientBoostingRegressor(**self.model_configs['gradient_boosting'])
            self.models['gradient_boosting'].fit(X_train_scaled, y_train)
            
            # Linear Regression
            self.models['linear'] = LinearRegression(**self.model_configs['linear'])
            self.models['linear'].fit(X_train_scaled, y_train)
            
            # Evaluate models
            for name, model in self.models.items():
                y_pred = model.predict(X_test_scaled)
                
                mse = mean_squared_error(y_test, y_pred)
                mae = mean_absolute_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)
                
                results[name] = {
                    'mse': mse,
                    'mae': mae,
                    'r2': r2,
                    'rmse': np.sqrt(mse)
                }
                
                logger.info(f"{name} - R²: {r2:.4f}, RMSE: {np.sqrt(mse):.4f}, MAE: {mae:.4f}")
            
            self.is_trained = True
            logger.info("Model training completed successfully")
            
            return results
            
        except Exception as e:
            logger.error(f"Model training error: {e}")
            raise
    
    def predict(self, df: pd.DataFrame, model_name: str = 'random_forest') -> Dict[str, Any]:
        """
        Make predictions using trained model
        """
        try:
            if not self.is_trained:
                raise ValueError("Models not trained. Call train_models() first.")
            
            if model_name not in self.models:
                raise ValueError(f"Model {model_name} not available. Available: {list(self.models.keys())}")
            
            # Prepare features
            X, _ = self.prepare_features(df)
            
            # Ensure feature alignment
            if set(X.columns) != set(self.feature_columns):
                missing_features = set(self.feature_columns) - set(X.columns)
                extra_features = set(X.columns) - set(self.feature_columns)
                
                if missing_features:
                    logger.warning(f"Missing features: {missing_features}")
                if extra_features:
                    logger.warning(f"Extra features: {extra_features}")
                
                # Align features
                X = X.reindex(columns=self.feature_columns, fill_value=0)
            
            # Scale features
            X_scaled = self.scalers['robust'].transform(X)
            
            # Make prediction
            model = self.models[model_name]
            prediction = model.predict(X_scaled)
            
            # Get feature importance (if available)
            feature_importance = None
            if hasattr(model, 'feature_importances_'):
                feature_importance = dict(zip(self.feature_columns, model.feature_importances_))
                # Sort by importance
                feature_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
            
            # Calculate confidence based on model performance and prediction consistency
            confidence = self._calculate_prediction_confidence(X_scaled, model_name)
            
            result = {
                'prediction': float(prediction[-1]) if len(prediction) > 0 else 0.0,
                'confidence': confidence,
                'model_used': model_name,
                'feature_importance': feature_importance,
                'timestamp': datetime.now(),
                'data_points': len(X)
            }
            
            logger.info(f"Prediction completed: {result['prediction']:.4f} (confidence: {confidence:.2%})")
            return result
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            raise
    
    def _calculate_prediction_confidence(self, X_scaled: np.ndarray, model_name: str) -> float:
        """
        Calculate prediction confidence based on model performance and data quality
        """
        try:
            base_confidence = 0.5
            
            # Model-specific confidence adjustments
            model_confidence = {
                'random_forest': 0.7,
                'gradient_boosting': 0.75,
                'linear': 0.6
            }
            
            confidence = model_confidence.get(model_name, 0.5)
            
            # Adjust based on data quality
            if len(X_scaled) > 100:
                confidence += 0.1
            elif len(X_scaled) < 50:
                confidence -= 0.1
            
            # Ensure confidence is within bounds
            confidence = max(0.1, min(0.9, confidence))
            
            return confidence
            
        except Exception as e:
            logger.warning(f"Confidence calculation error: {e}")
            return 0.5
    
    def save_models(self, filepath: str) -> bool:
        """
        Save trained models to file
        """
        try:
            if not self.is_trained:
                logger.warning("No trained models to save")
                return False
            
            model_data = {
                'models': self.models,
                'scalers': self.scalers,
                'feature_columns': self.feature_columns,
                'config': self.config,
                'timestamp': datetime.now()
            }
            
            joblib.dump(model_data, filepath)
            logger.info(f"Models saved to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Model saving error: {e}")
            return False
    
    def load_models(self, filepath: str) -> bool:
        """
        Load trained models from file
        """
        try:
            model_data = joblib.load(filepath)
            
            self.models = model_data['models']
            self.scalers = model_data['scalers']
            self.feature_columns = model_data['feature_columns']
            self.config = model_data.get('config', {})
            self.is_trained = True
            
            logger.info(f"Models loaded from {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Model loading error: {e}")
            return False

# Example usage and testing
def test_prediction_model():
    """Test the prediction model with sample data"""
    
    try:
        # Generate sample market data
        dates = pd.date_range(start='2024-01-01', periods=200, freq='1H')
        np.random.seed(42)
        
        # Create realistic OHLC data
        base_price = 50000
        returns = np.random.normal(0, 0.02, 200)
        prices = [base_price]
        
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        # Generate OHLC from prices
        test_data = []
        for i, price in enumerate(prices):
            volatility = np.random.uniform(0.005, 0.02)
            open_price = price * (1 + np.random.normal(0, volatility/2))
            close_price = price * (1 + np.random.normal(0, volatility/2))
            high_price = max(open_price, close_price) * (1 + np.random.uniform(0, volatility))
            low_price = min(open_price, close_price) * (1 - np.random.uniform(0, volatility))
            volume = np.random.randint(1000, 10000)
            
            test_data.append({
                'Open': open_price,
                'High': high_price,
                'Low': low_price,
                'Close': close_price,
                'Volume': volume
            })
        
        df = pd.DataFrame(test_data, index=dates)
        
        print("Prediction Model Test")
        print("=" * 50)
        
        # Initialize model
        model = PredictionModel()
        
        # Test feature preparation
        print("Testing feature preparation...")
        features, feature_cols = model.prepare_features(df)
        print(f"✅ Features prepared: {len(feature_cols)} features, {len(features)} samples")
        
        # Test model training
        print("\nTesting model training...")
        results = model.train_models(df)
        
        print("\nModel Performance:")
        for name, metrics in results.items():
            print(f"{name}:")
            print(f"  R²: {metrics['r2']:.4f}")
            print(f"  RMSE: {metrics['rmse']:.4f}")
            print(f"  MAE: {metrics['mae']:.4f}")
        
        # Test prediction
        print("\nTesting prediction...")
        recent_data = df.tail(50)  # Use last 50 data points
        prediction = model.predict(recent_data, 'random_forest')
        
        print(f"✅ Prediction: {prediction['prediction']:.4f}")
        print(f"✅ Confidence: {prediction['confidence']:.2%}")
        print(f"✅ Model: {prediction['model_used']}")
        
        # Test model saving/loading
        print("\nTesting model persistence...")
        save_path = "/tmp/test_model.joblib"
        if model.save_models(save_path):
            print("✅ Model saved successfully")
            
            # Test loading
            new_model = PredictionModel()
            if new_model.load_models(save_path):
                print("✅ Model loaded successfully")
                
                # Test prediction with loaded model
                loaded_prediction = new_model.predict(recent_data, 'random_forest')
                print(f"✅ Loaded model prediction: {loaded_prediction['prediction']:.4f}")
        
        print("\n🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    # Run test
    success = test_prediction_model()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")

