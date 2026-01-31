"""Configuration management for GhostKG.

This module provides dataclass-based configuration for all GhostKG components.
Configurations can be loaded from code, environment variables, YAML, or JSON files.
"""

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from ghost_kg.exceptions import ConfigurationError


@dataclass
class FSRSConfig:
    """FSRS algorithm configuration.

    Parameters control the spaced repetition algorithm behavior.
    The default parameters are optimized for general use cases.

    Attributes:
        parameters: List of 17 FSRS algorithm parameters
    """

    parameters: List[float] = field(
        default_factory=lambda: [
            0.4,
            0.6,
            2.4,
            5.8,
            4.93,
            0.94,
            0.86,
            0.01,
            1.49,
            0.14,
            0.94,
            2.18,
            0.05,
            0.34,
            1.26,
            0.29,
            2.61,
        ]
    )

    def validate(self) -> None:
        """
        Validate FSRS configuration.

        Returns:
            None

        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not isinstance(self.parameters, list):
            raise ConfigurationError("FSRS parameters must be a list")
        if len(self.parameters) != 17:
            raise ConfigurationError(
                f"FSRS parameters must have exactly 17 values, got {len(self.parameters)}"
            )
        if not all(isinstance(p, (int, float)) for p in self.parameters):
            raise ConfigurationError("All FSRS parameters must be numeric")


@dataclass
class DatabaseConfig:
    """Database configuration.

    Attributes:
        path: Path to the SQLite database file
        check_same_thread: Whether to check thread identity (False allows multi-threading)
        timeout: Connection timeout in seconds
    """

    path: str = "agent_memory.db"
    check_same_thread: bool = False
    timeout: float = 5.0

    def validate(self) -> None:
        """
        Validate database configuration.

        Returns:
            None

        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not self.path:
            raise ConfigurationError("Database path cannot be empty")
        if self.timeout <= 0:
            raise ConfigurationError(f"Database timeout must be positive, got {self.timeout}")


@dataclass
class LLMConfig:
    """LLM (Language Model) configuration.

    Attributes:
        host: Ollama server host URL
        model: Model name to use (e.g., 'llama3.2', 'llama2')
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts on failure
    """

    host: str = field(default_factory=lambda: os.getenv("OLLAMA_HOST", "http://localhost:11434"))
    model: str = "llama3.2"
    timeout: int = 30
    max_retries: int = 3

    def validate(self) -> None:
        """
        Validate LLM configuration.

        Returns:
            None

        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not self.host:
            raise ConfigurationError("LLM host cannot be empty")
        if self.timeout <= 0:
            raise ConfigurationError(f"LLM timeout must be positive, got {self.timeout}")
        if self.max_retries < 1:
            raise ConfigurationError(f"LLM max_retries must be at least 1, got {self.max_retries}")


@dataclass
class FastModeConfig:
    """Fast mode extraction configuration.

    Attributes:
        gliner_model: GLiNER model name/path for entity extraction
        entity_labels: List of entity types to extract
        sentiment_thresholds: Thresholds for sentiment classification
    """

    gliner_model: str = "urchade/gliner_small-v2.1"
    entity_labels: List[str] = field(
        default_factory=lambda: ["Topic", "Person", "Concept", "Organization"]
    )
    sentiment_thresholds: Dict[str, float] = field(
        default_factory=lambda: {
            "support": 0.3,
            "oppose": -0.3,
            "like": 0.1,
            "dislike": -0.1,
        }
    )

    def validate(self) -> None:
        """
        Validate fast mode configuration.

        Returns:
            None

        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not self.gliner_model:
            raise ConfigurationError("GLiNER model name cannot be empty")
        if not self.entity_labels:
            raise ConfigurationError("Entity labels cannot be empty")


@dataclass
class GhostKGConfig:
    """Main GhostKG configuration.

    This is the top-level configuration class that contains all sub-configurations.

    Attributes:
        fsrs: FSRS algorithm configuration
        database: Database configuration
        llm: LLM configuration
        fast_mode: Fast mode extraction configuration

    Examples:
        >>> # Default configuration
        >>> config = GhostKGConfig()

        >>> # Custom configuration
        >>> config = GhostKGConfig(
        ...     llm=LLMConfig(host="http://my-server:11434", model="llama2"),
        ...     database=DatabaseConfig(path="/data/agents.db")
        ... )

        >>> # From environment variables
        >>> config = GhostKGConfig.from_env()

        >>> # From YAML file
        >>> config = GhostKGConfig.from_yaml("config.yaml")

        >>> # From JSON file
        >>> config = GhostKGConfig.from_json("config.json")
    """

    fsrs: FSRSConfig = field(default_factory=FSRSConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    fast_mode: FastModeConfig = field(default_factory=FastModeConfig)

    def validate(self) -> None:
        """
        Validate all configuration sections.

        Returns:
            None

        Raises:
            ConfigurationError: If any configuration is invalid
        """
        self.fsrs.validate()
        self.database.validate()
        self.llm.validate()
        self.fast_mode.validate()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of configuration
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GhostKGConfig":
        """
        Load configuration from dictionary.

        Args:
            data (Dict[str, Any]): Dictionary containing configuration data

        Returns:
            GhostKGConfig: GhostKGConfig instance

        Raises:
            ConfigurationError: If dictionary format is invalid

        Examples:
            >>> data = {
            ...     "llm": {"host": "http://localhost:11434", "model": "llama2"},
            ...     "database": {"path": "/data/agents.db"}
            ... }
            >>> config = GhostKGConfig.from_dict(data)
        """
        try:
            fsrs = FSRSConfig(**data.get("fsrs", {}))
            database = DatabaseConfig(**data.get("database", {}))
            llm = LLMConfig(**data.get("llm", {}))
            fast_mode = FastModeConfig(**data.get("fast_mode", {}))

            config = cls(fsrs=fsrs, database=database, llm=llm, fast_mode=fast_mode)
            config.validate()
            return config
        except TypeError as e:
            raise ConfigurationError(f"Invalid configuration dictionary: {e}") from e

    @classmethod
    def from_env(cls, prefix: str = "GHOSTKG") -> "GhostKGConfig":
        """
        Load configuration from environment variables.

        Environment variables should be prefixed with the given prefix and use underscores
        to separate nested keys. For example:
        - GHOSTKG_LLM_HOST
        - GHOSTKG_LLM_MODEL
        - GHOSTKG_DATABASE_PATH

        Args:
            prefix (str): Prefix for environment variables (default: "GHOSTKG")

        Returns:
            GhostKGConfig: GhostKGConfig instance

        Examples:
            >>> # Set environment variables:
            >>> # export GHOSTKG_LLM_HOST=http://my-server:11434
            >>> # export GHOSTKG_LLM_MODEL=llama2
            >>> # export GHOSTKG_DATABASE_PATH=/data/agents.db
            >>> config = GhostKGConfig.from_env()
        """
        prefix = prefix.upper()

        def get_env(section: str, key: str, default: Any = None, type_func=str) -> Any:
            """Get environment variable with type conversion."""
            env_key = f"{prefix}_{section}_{key}".upper()
            value = os.getenv(env_key)
            if value is None:
                return default

            # Type conversion
            if type_func == bool:
                return value.lower() in ("true", "1", "yes", "on")
            elif type_func == int:
                return int(value)
            elif type_func == float:
                return float(value)
            else:
                return value

        # Build configuration from environment
        fsrs = FSRSConfig()  # FSRS params from env not implemented

        database = DatabaseConfig(
            path=get_env("DATABASE", "PATH", DatabaseConfig.path),
            check_same_thread=get_env(
                "DATABASE", "CHECK_SAME_THREAD", DatabaseConfig.check_same_thread, bool
            ),
            timeout=get_env("DATABASE", "TIMEOUT", DatabaseConfig.timeout, float),
        )

        llm = LLMConfig(
            host=get_env("LLM", "HOST", LLMConfig().host),
            model=get_env("LLM", "MODEL", LLMConfig.model),
            timeout=get_env("LLM", "TIMEOUT", LLMConfig.timeout, int),
            max_retries=get_env("LLM", "MAX_RETRIES", LLMConfig.max_retries, int),
        )

        fast_mode = FastModeConfig(
            gliner_model=get_env("FAST_MODE", "GLINER_MODEL", FastModeConfig.gliner_model),
        )

        config = cls(fsrs=fsrs, database=database, llm=llm, fast_mode=fast_mode)
        config.validate()
        return config

    @classmethod
    def from_yaml(cls, path: str) -> "GhostKGConfig":
        """
        Load configuration from YAML file.

        Requires PyYAML to be installed: `pip install pyyaml`

        Args:
            path (str): Path to YAML configuration file

        Returns:
            GhostKGConfig: GhostKGConfig instance

        Raises:
            ConfigurationError: If file cannot be loaded or is invalid
            ImportError: If PyYAML is not installed

        Examples:
            >>> # config.yaml:
            >>> # llm:
            >>> #   host: http://my-server:11434
            >>> #   model: llama2
            >>> # database:
            >>> #   path: /data/agents.db
            >>> config = GhostKGConfig.from_yaml("config.yaml")
        """
        try:
            import yaml
        except ImportError:
            raise ImportError(
                "PyYAML is required to load YAML configuration files. "
                "Install it with: pip install pyyaml"
            )

        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f)

            if data is None:
                data = {}

            return cls.from_dict(data)
        except FileNotFoundError:
            raise ConfigurationError(f"Configuration file not found: {path}")
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in configuration file: {e}") from e
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration from {path}: {e}") from e

    @classmethod
    def from_json(cls, path: str) -> "GhostKGConfig":
        """
        Load configuration from JSON file.

        Args:
            path (str): Path to JSON configuration file

        Returns:
            GhostKGConfig: GhostKGConfig instance

        Raises:
            ConfigurationError: If file cannot be loaded or is invalid

        Examples:
            >>> # config.json:
            >>> # {
            >>> #   "llm": {"host": "http://my-server:11434", "model": "llama2"},
            >>> #   "database": {"path": "/data/agents.db"}
            >>> # }
            >>> config = GhostKGConfig.from_json("config.json")
        """
        try:
            with open(path, "r") as f:
                data = json.load(f)

            return cls.from_dict(data)
        except FileNotFoundError:
            raise ConfigurationError(f"Configuration file not found: {path}")
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in configuration file: {e}") from e
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration from {path}: {e}") from e


# Convenience function for getting default config
def get_default_config() -> GhostKGConfig:
    """
    Get default GhostKG configuration.

    Returns:
        GhostKGConfig: GhostKGConfig with default values
    """
    return GhostKGConfig()
