"""
XGBoost Trading Model för prisriktning-prediktioner

Implementerar ML-baserad trading modell som använder tekniska indikatorer
för att förutsäga prisriktningar och generera trading-signaler.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import xgboost as xgb
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import logging
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class XGBoostTradingModel:
    """
    XGBoost-baserad trading modell för prisriktning-prediktioner

    Träna en gradient boosting modell på tekniska indikatorer för att förutsäga
    om priset kommer att gå upp eller ner nästa period.
    """

    def __init__(self,
                 objective: str = 'binary:logistic',
                 max_depth: int = 6,
                 learning_rate: float = 0.1,
                 n_estimators: int = 100,
                 subsample: float = 0.8,
                 colsample_bytree: float = 0.8,
                 random_state: int = 42):
        """
        Initiera XGBoost trading modell

        Args:
            objective: XGBoost objective funktion
            max_depth: Max djup för träden
            learning_rate: Learning rate för boosting
            n_estimators: Antal estimators (träden)
            subsample: Subsample ratio för träning
            colsample_bytree: Kolumn subsample ratio
            random_state: Random state för reproducerbarhet
        """
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.is_trained = False
        self.training_date = None

        # XGBoost parametrar
        self.params = {
            'objective': objective,
            'max_depth': max_depth,
            'learning_rate': learning_rate,
            'n_estimators': n_estimators,
            'subsample': subsample,
            'colsample_bytree': colsample_bytree,
            'random_state': random_state,
            'eval_metric': 'logloss',
            'verbosity': 1
        }

        # Träning metadata
        self.training_metrics = {}
        self.feature_importance = {}

    def train(self,
              X_train: pd.DataFrame,
              y_train: pd.Series,
              X_val: Optional[pd.DataFrame] = None,
              y_val: Optional[pd.Series] = None,
              early_stopping_rounds: int = 20) -> Dict[str, float]:
        """
        Träna XGBoost modellen

        Args:
            X_train: Träning features
            y_train: Träning targets
            X_val: Validerings features (optional)
            y_val: Validerings targets (optional)
            early_stopping_rounds: Antal rundor för early stopping

        Returns:
            Dict med träning metrics
        """
        try:
            self.feature_names = X_train.columns.tolist()

            # Feature scaling
            X_train_scaled = self.scaler.fit_transform(X_train)

            # Hantera class imbalance genom att beräkna scale_pos_weight
            pos_weight = len(y_train[y_train == 0]) / len(y_train[y_train == 1])
            self.params['scale_pos_weight'] = pos_weight

            # Skapa XGBoost DMatrix för effektivitet
            dtrain = xgb.DMatrix(X_train_scaled, label=y_train)

            # Valideringsdata om tillgängligt
            evals = [(dtrain, 'train')]
            if X_val is not None and y_val is not None:
                X_val_scaled = self.scaler.transform(X_val)
                dval = xgb.DMatrix(X_val_scaled, label=y_val)
                evals.append((dval, 'validation'))

            # Träna modellen
            self.model = xgb.train(
                self.params,
                dtrain,
                num_boost_round=self.params['n_estimators'],
                evals=evals,
                early_stopping_rounds=early_stopping_rounds if len(evals) > 1 else None,
                verbose_eval=False
            )

            self.is_trained = True
            self.training_date = datetime.now()

            # Beräkna träning metrics
            train_pred_proba = self.model.predict(dtrain)
            train_pred = (train_pred_proba > 0.5).astype(int)

            self.training_metrics = {
                'train_accuracy': accuracy_score(y_train, train_pred),
                'train_precision': np.mean(y_train == train_pred),
                'pos_weight': pos_weight
            }

            # Feature importance
            self.feature_importance = dict(zip(
                self.feature_names,
                self.model.get_score(importance_type='gain').values()
            ))

            logger.info(f"XGBoost modell tränad. Träning accuracy: {self.training_metrics['train_accuracy']:.4f}")

            return self.training_metrics

        except Exception as e:
            logger.error(f"Fel vid träning av XGBoost modell: {str(e)}")
            raise

    def predict_proba(self, features: pd.DataFrame) -> np.ndarray:
        """
        Prediktera sannolikhet för uppgång

        Args:
            features: Feature DataFrame

        Returns:
            Array med sannolikheter för uppgång (0-1)
        """
        if not self.is_trained:
            raise ValueError("Modellen är inte tränad ännu")

        try:
            # Säkerställ att features har rätt format
            missing_features = set(self.feature_names) - set(features.columns)
            if missing_features:
                raise ValueError(f"Missing features: {missing_features}")

            # Välj endast relevanta features
            X = features[self.feature_names]

            # Scale features
            X_scaled = self.scaler.transform(X)

            # Skapa DMatrix och prediktera
            dtest = xgb.DMatrix(X_scaled)
            probabilities = self.model.predict(dtest)

            return probabilities

        except Exception as e:
            logger.error(f"Fel vid prediktion: {str(e)}")
            raise

    def predict(self, features: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        """
        Prediktera binär klass (upp/ner)

        Args:
            features: Feature DataFrame
            threshold: Tröskelvärde för klassificering

        Returns:
            Array med binära prediktioner (0 eller 1)
        """
        probabilities = self.predict_proba(features)
        return (probabilities > threshold).astype(int)

    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, Any]:
        """
        Evaluera modellens prestanda

        Args:
            X_test: Test features
            y_test: Test targets

        Returns:
            Dict med utvärderingsmetrics
        """
        if not self.is_trained:
            raise ValueError("Modellen är inte tränad ännu")

        try:
            # Prediktioner
            y_pred_proba = self.predict_proba(X_test)
            y_pred = (y_pred_proba > 0.5).astype(int)

            # Metrics
            accuracy = accuracy_score(y_test, y_pred)
            conf_matrix = confusion_matrix(y_test, y_pred)

            # Trading-specifika metrics
            precision = conf_matrix[1][1] / (conf_matrix[1][1] + conf_matrix[0][1]) if (conf_matrix[1][1] + conf_matrix[0][1]) > 0 else 0
            recall = conf_matrix[1][1] / (conf_matrix[1][1] + conf_matrix[1][0]) if (conf_matrix[1][1] + conf_matrix[1][0]) > 0 else 0
            specificity = conf_matrix[0][0] / (conf_matrix[0][0] + conf_matrix[0][1]) if (conf_matrix[0][0] + conf_matrix[0][1]) > 0 else 0

            # Win rate för long trades
            long_trades = y_pred == 1
            if np.sum(long_trades) > 0:
                long_win_rate = np.mean(y_test[long_trades] == 1)
            else:
                long_win_rate = 0

            evaluation_results = {
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'specificity': specificity,
                'long_win_rate': long_win_rate,
                'confusion_matrix': conf_matrix.tolist(),
                'total_predictions': len(y_pred),
                'positive_predictions': int(np.sum(y_pred)),
                'negative_predictions': int(len(y_pred) - np.sum(y_pred))
            }

            logger.info(f"Model evaluation - Accuracy: {accuracy:.4f}, Long Win Rate: {long_win_rate:.4f}")

            return evaluation_results

        except Exception as e:
            logger.error(f"Fel vid evaluering: {str(e)}")
            raise

    def generate_trading_signal(self,
                               features: pd.DataFrame,
                               confidence_threshold: float = 0.6,
                               min_probability: float = 0.5) -> Dict[str, Any]:
        """
        Generera trading-signal baserat på modellens prediktioner

        Args:
            features: Senaste features
            confidence_threshold: Minsta confidence för stark signal
            min_probability: Minsta sannolikhet för signal

        Returns:
            Dict med trading signal information
        """
        if not self.is_trained:
            return {
                'signal': 'HOLD',
                'confidence': 0.0,
                'probability': 0.5,
                'reason': 'Modell inte tränad'
            }

        try:
            # Prediktera på senaste datapunkt
            latest_features = features.iloc[-1:].copy()
            probability = self.predict_proba(latest_features)[0]

            # Bestäm signal
            if probability > (1 + confidence_threshold) / 2:
                signal = 'BUY'
                confidence = (probability - 0.5) * 2
            elif probability < (1 - confidence_threshold) / 2:
                signal = 'SELL'
                confidence = (0.5 - probability) * 2
            else:
                signal = 'HOLD'
                confidence = 0.0

            # Kontrollera mot minsta sannolikhet
            if abs(probability - 0.5) < abs(min_probability - 0.5):
                signal = 'HOLD'
                confidence = 0.0

            signal_data = {
                'signal': signal,
                'confidence': float(confidence),
                'probability': float(probability),
                'timestamp': datetime.now().isoformat(),
                'top_features': self._get_top_contributing_features(latest_features.iloc[0])
            }

            return signal_data

        except Exception as e:
            logger.error(f"Fel vid signalgenerering: {str(e)}")
            return {
                'signal': 'HOLD',
                'confidence': 0.0,
                'probability': 0.5,
                'reason': f'Fel: {str(e)}'
            }

    def _get_top_contributing_features(self, feature_values: pd.Series, top_n: int = 5) -> Dict[str, float]:
        """
        Identifiera de mest bidragande features för senaste prediktion

        Args:
            feature_values: Feature värden för senaste datapunkt
            top_n: Antal top features att returnera

        Returns:
            Dict med feature namn och deras bidrag
        """
        try:
            # Använd feature importance som approximation
            top_features = sorted(self.feature_importance.items(),
                                key=lambda x: x[1], reverse=True)[:top_n]

            return {feature: importance for feature, importance in top_features}

        except Exception:
            # Fallback om feature importance inte är tillgängligt
            return {}

    def get_model_info(self) -> Dict[str, Any]:
        """Returnera information om modellen"""
        return {
            'is_trained': self.is_trained,
            'training_date': self.training_date.isoformat() if self.training_date else None,
            'feature_count': len(self.feature_names),
            'feature_names': self.feature_names,
            'training_metrics': self.training_metrics,
            'parameters': self.params
        }

    def reset_model(self):
        """Återställ modellen för omträning"""
        self.model = None
        self.is_trained = False
        self.training_date = None
        self.training_metrics = {}
        self.feature_importance = {}
        self.scaler = StandardScaler()


def create_optimized_xgboost_model() -> XGBoostTradingModel:
    """
    Utility funktion för att skapa optimerad XGBoost modell för trading

    Returns:
        XGBoostTradingModel med optimerade parametrar
    """
    return XGBoostTradingModel(
        max_depth=6,           # Balans mellan bias och variance
        learning_rate=0.1,     # Konservativ learning rate
        n_estimators=200,      # Tillräckligt många träden för convergence
        subsample=0.8,         # Minska overfitting
        colsample_bytree=0.8,  # Feature subsampling
        random_state=42
    )