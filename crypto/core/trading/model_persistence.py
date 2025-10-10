"""
Model Persistence för XGBoost Trading Modeller

Implementerar save/load funktionalitet för tränade modeller med metadata,
versionshantering och automatisk cleanup av gamla modeller.
"""

import os
import joblib
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
import gzip
from pathlib import Path
import shutil

from .trading.xgboost_trader import XGBoostTradingModel

logger = logging.getLogger(__name__)


class ModelPersistence:
    """
    Hanterar persistens av XGBoost trading modeller

    Inkluderar metadata, versionshantering, backup och cleanup.
    """

    def __init__(self, models_dir: str = "models", max_versions_per_token: int = 5):
        """
        Initiera model persistence

        Args:
            models_dir: Katalog för att spara modeller
            max_versions_per_token: Max antal versioner att behålla per token
        """
        self.models_dir = Path(models_dir)
        self.max_versions_per_token = max_versions_per_token
        self.models_dir.mkdir(exist_ok=True)

        # Skapa subkataloger
        self.active_dir = self.models_dir / "active"
        self.archive_dir = self.models_dir / "archive"
        self.backup_dir = self.models_dir / "backup"

        for dir_path in [self.active_dir, self.archive_dir, self.backup_dir]:
            dir_path.mkdir(exist_ok=True)

    def save_model(self,
                  model: XGBoostTradingModel,
                  token_id: str,
                  metadata: Optional[Dict[str, Any]] = None,
                  compress: bool = True) -> str:
        """
        Spara tränad modell med metadata

        Args:
            model: Tränad XGBoost modell
            token_id: Token identifierare
            metadata: Ytterligare metadata
            compress: Komprimera modellen

        Returns:
            Filpath till sparad modell
        """
        if not model.is_trained:
            raise ValueError("Kan inte spara otränad modell")

        try:
            # Skapa model data
            model_data = {
                'model': model.model,
                'feature_names': model.feature_names,
                'scaler': model.scaler,
                'training_date': model.training_date.isoformat() if model.training_date else None,
                'training_metrics': model.training_metrics,
                'feature_importance': model.feature_importance,
                'parameters': model.params,
                'metadata': metadata or {},
                'token_id': token_id,
                'version': self._get_next_version(token_id),
                'saved_at': datetime.now().isoformat(),
                'framework_version': '1.0.0'
            }

            # Skapa filnamn
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{token_id}_v{model_data['version']}_{timestamp}.pkl"

            if compress:
                filename = filename + ".gz"
                filepath = self.active_dir / filename
                with gzip.open(filepath, 'wb') as f:
                    joblib.dump(model_data, f)
            else:
                filepath = self.active_dir / filename
                joblib.dump(model_data, filepath)

            # Spara även metadata separat för enkel åtkomst
            metadata_file = filepath.with_suffix('.meta.json')
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'token_id': token_id,
                    'version': model_data['version'],
                    'training_date': model_data['training_date'],
                    'training_metrics': model_data['training_metrics'],
                    'filepath': str(filepath),
                    'compressed': compress,
                    'saved_at': model_data['saved_at']
                }, f, indent=2, ensure_ascii=False)

            logger.info(f"Modell sparad: {filepath}")

            # Cleanup gamla versioner
            self._cleanup_old_versions(token_id)

            return str(filepath)

        except Exception as e:
            logger.error(f"Fel vid sparande av modell: {str(e)}")
            raise

    def load_model(self, token_id: str, version: Optional[int] = None) -> XGBoostTradingModel:
        """
        Ladda modell från fil

        Args:
            token_id: Token identifierare
            version: Specifik version (senaste om None)

        Returns:
            Laddad XGBoost modell
        """
        try:
            filepath = self._find_model_file(token_id, version)
            if not filepath:
                raise FileNotFoundError(f"Ingen modell hittad för {token_id}")

            # Ladda model data
            if str(filepath).endswith('.gz'):
                with gzip.open(filepath, 'rb') as f:
                    model_data = joblib.load(f)
            else:
                model_data = joblib.load(filepath)

            # Återskapa modell
            model = XGBoostTradingModel()
            model.model = model_data['model']
            model.feature_names = model_data['feature_names']
            model.scaler = model_data['scaler']
            model.is_trained = True
            model.training_date = datetime.fromisoformat(model_data['training_date']) if model_data['training_date'] else None
            model.training_metrics = model_data.get('training_metrics', {})
            model.feature_importance = model_data.get('feature_importance', {})
            model.params = model_data.get('parameters', {})

            logger.info(f"Modell laddad: {filepath}")
            return model

        except Exception as e:
            logger.error(f"Fel vid laddning av modell: {str(e)}")
            raise

    def load_latest_model(self, token_id: str) -> Optional[XGBoostTradingModel]:
        """
        Ladda senaste version av modell för token

        Args:
            token_id: Token identifierare

        Returns:
            Senaste modellen eller None om ingen finns
        """
        try:
            return self.load_model(token_id)
        except FileNotFoundError:
            return None

    def list_available_models(self) -> List[Dict[str, Any]]:
        """
        Lista alla tillgängliga modeller

        Returns:
            Lista med model metadata
        """
        models = []

        # Sök igenom alla .meta.json filer
        for meta_file in self.active_dir.glob("*.meta.json"):
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    models.append(metadata)
            except Exception as e:
                logger.warning(f"Kunde inte läsa metadata från {meta_file}: {str(e)}")

        # Sortera efter sparad datum (nyaste först)
        models.sort(key=lambda x: x.get('saved_at', ''), reverse=True)

        return models

    def get_model_history(self, token_id: str) -> List[Dict[str, Any]]:
        """
        Hämta versionshistorik för en token

        Args:
            token_id: Token identifierare

        Returns:
            Lista med versioner sorterade efter datum
        """
        all_models = self.list_available_models()
        token_models = [m for m in all_models if m.get('token_id') == token_id]

        # Inkludera även arkiverade modeller
        for meta_file in self.archive_dir.glob(f"{token_id}_*.meta.json"):
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    token_models.append(metadata)
            except Exception as e:
                logger.warning(f"Kunde inte läsa arkiverad metadata från {meta_file}: {str(e)}")

        # Sortera efter version (högst först)
        token_models.sort(key=lambda x: x.get('version', 0), reverse=True)

        return token_models

    def archive_model(self, token_id: str, version: int):
        """
        Arkivera en specifik model version

        Args:
            token_id: Token identifierare
            version: Version att arkivera
        """
        try:
            filepath = self._find_model_file(token_id, version)
            if not filepath:
                raise FileNotFoundError(f"Modell version {version} för {token_id} hittades inte")

            # Flytta till archive
            archive_name = filepath.name
            archive_path = self.archive_dir / archive_name
            shutil.move(filepath, archive_path)

            # Flytta även metadata
            meta_file = filepath.with_suffix('.meta.json')
            if meta_file.exists():
                archive_meta = self.archive_dir / meta_file.name
                shutil.move(meta_file, archive_meta)

            logger.info(f"Modell arkiverad: {archive_path}")

        except Exception as e:
            logger.error(f"Fel vid arkivering: {str(e)}")
            raise

    def delete_model(self, token_id: str, version: int):
        """
        Ta bort en specifik model version

        Args:
            token_id: Token identifierare
            version: Version att ta bort
        """
        try:
            filepath = self._find_model_file(token_id, version)
            if not filepath:
                raise FileNotFoundError(f"Modell version {version} för {token_id} hittades inte")

            # Ta bort filer
            filepath.unlink(missing_ok=True)
            meta_file = filepath.with_suffix('.meta.json')
            meta_file.unlink(missing_ok=True)

            logger.info(f"Modell borttagen: {filepath}")

        except Exception as e:
            logger.error(f"Fel vid borttagning: {str(e)}")
            raise

    def backup_models(self, backup_name: Optional[str] = None) -> str:
        """
        Skapa backup av alla modeller

        Args:
            backup_name: Namn på backup (timestamp om None)

        Returns:
            Path till backup
        """
        if backup_name is None:
            backup_name = datetime.now().strftime("%Y%m%d_%H%M%S")

        backup_path = self.backup_dir / f"backup_{backup_name}"
        backup_path.mkdir(exist_ok=True)

        try:
            # Kopiera alla modeller
            for item in self.active_dir.iterdir():
                if item.is_file():
                    shutil.copy2(item, backup_path / item.name)

            # Skapa backup manifest
            manifest = {
                'backup_name': backup_name,
                'created_at': datetime.now().isoformat(),
                'models': self.list_available_models(),
                'total_files': len(list(backup_path.iterdir()))
            }

            with open(backup_path / 'manifest.json', 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)

            logger.info(f"Backup skapad: {backup_path}")
            return str(backup_path)

        except Exception as e:
            logger.error(f"Fel vid backup: {str(e)}")
            raise

    def _find_model_file(self, token_id: str, version: Optional[int] = None) -> Optional[Path]:
        """
        Hitta model-fil för given token och version

        Args:
            token_id: Token identifierare
            version: Specifik version eller None för senaste

        Returns:
            Path till model-fil eller None
        """
        if version is not None:
            # Sök efter specifik version
            pattern = f"{token_id}_v{version}_*.pkl*"
        else:
            # Sök efter alla versioner av token
            pattern = f"{token_id}_v*_*.pkl*"

        candidates = list(self.active_dir.glob(pattern))

        if not candidates:
            return None

        if version is not None:
            # Returnera första match (bör vara unik)
            return candidates[0]
        else:
            # Returnera senaste version
            candidates.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            return candidates[0]

    def _get_next_version(self, token_id: str) -> int:
        """
        Hämta nästa versionsnummer för token

        Args:
            token_id: Token identifierare

        Returns:
            Nästa versionsnummer
        """
        existing_versions = []

        # Sök efter befintliga versioner
        for meta_file in self.active_dir.glob(f"{token_id}_*.meta.json"):
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    existing_versions.append(metadata.get('version', 0))
            except Exception:
                continue

        return max(existing_versions) + 1 if existing_versions else 1

    def _cleanup_old_versions(self, token_id: str):
        """
        Rensa upp gamla versioner, behåll endast de senaste

        Args:
            token_id: Token identifierare
        """
        try:
            # Hämta alla versioner
            versions = []
            for meta_file in self.active_dir.glob(f"{token_id}_*.meta.json"):
                try:
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        versions.append((
                            metadata['version'],
                            meta_file,
                            metadata.get('saved_at', '')
                        ))
                except Exception:
                    continue

            # Sortera efter datum (nyaste först)
            versions.sort(key=lambda x: x[2], reverse=True)

            # Arkivera gamla versioner
            if len(versions) > self.max_versions_per_token:
                for version, meta_file, _ in versions[self.max_versions_per_token:]:
                    try:
                        # Hitta motsvarande model-fil
                        model_file = meta_file.with_suffix('')
                        if model_file.suffix == '.meta':
                            model_file = model_file.with_suffix('.pkl')
                        else:
                            # Hantera komprimerade filer
                            model_file = model_file.with_suffix('.pkl.gz')

                        if model_file.exists():
                            archive_model = self.archive_dir / model_file.name
                            shutil.move(model_file, archive_model)

                        archive_meta = self.archive_dir / meta_file.name
                        shutil.move(meta_file, archive_meta)

                        logger.debug(f"Arkiverade gammal version: {version}")

                    except Exception as e:
                        logger.warning(f"Kunde inte arkivera version {version}: {str(e)}")

        except Exception as e:
            logger.error(f"Fel vid cleanup: {str(e)}")


# Utility funktioner
def save_trained_model(model: XGBoostTradingModel,
                      token_id: str,
                      filepath: str,
                      metadata: Optional[Dict[str, Any]] = None) -> str:
    """
    Utility funktion för att spara modell

    Args:
        model: Tränad modell
        token_id: Token ID
        filepath: Sökväg att spara till
        metadata: Ytterligare metadata

    Returns:
        Fullständig sökväg till sparad modell
    """
    persistence = ModelPersistence()
    return persistence.save_model(model, token_id, metadata)


def load_trained_model(filepath: str) -> XGBoostTradingModel:
    """
    Utility funktion för att ladda modell från specifik fil

    Args:
        filepath: Sökväg till modellfil

    Returns:
        Laddad modell
    """
    model_data = joblib.load(filepath)

    model = XGBoostTradingModel()
    model.model = model_data['model']
    model.feature_names = model_data['feature_names']
    model.scaler = model_data['scaler']
    model.is_trained = True
    model.training_date = datetime.fromisoformat(model_data['training_date']) if model_data['training_date'] else None
    model.training_metrics = model_data.get('training_metrics', {})
    model.feature_importance = model_data.get('feature_importance', {})

    return model


def get_model_persistence(models_dir: str = "models") -> ModelPersistence:
    """
    Skapa ModelPersistence instans

    Args:
        models_dir: Katalog för modeller

    Returns:
        ModelPersistence instans
    """
    return ModelPersistence(models_dir)