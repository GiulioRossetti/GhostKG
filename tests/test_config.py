"""Tests for configuration module."""

import os
import json
import tempfile
import pytest
from pathlib import Path

from ghost_kg import (
    FSRSConfig,
    DatabaseConfig,
    LLMConfig,
    FastModeConfig,
    GhostKGConfig,
    get_default_config,
    ConfigurationError,
)


class TestFSRSConfig:
    """Test FSRS configuration."""
    
    def test_default_config(self):
        """Test default FSRS configuration."""
        config = FSRSConfig()
        assert len(config.parameters) == 17
        assert all(isinstance(p, (int, float)) for p in config.parameters)
    
    def test_custom_parameters(self):
        """Test custom FSRS parameters."""
        params = [1.0] * 17
        config = FSRSConfig(parameters=params)
        assert config.parameters == params
    
    def test_validation_wrong_count(self):
        """Test validation fails with wrong parameter count."""
        config = FSRSConfig(parameters=[1.0] * 10)
        with pytest.raises(ConfigurationError, match="exactly 17 values"):
            config.validate()
    
    def test_validation_non_numeric(self):
        """Test validation fails with non-numeric parameters."""
        config = FSRSConfig(parameters=[1.0] * 16 + ["invalid"])
        with pytest.raises(ConfigurationError, match="must be numeric"):
            config.validate()
    
    def test_validation_not_list(self):
        """Test validation fails when parameters is not a list."""
        config = FSRSConfig(parameters="invalid")
        with pytest.raises(ConfigurationError, match="must be a list"):
            config.validate()


class TestDatabaseConfig:
    """Test database configuration."""
    
    def test_default_config(self):
        """Test default database configuration."""
        config = DatabaseConfig()
        assert config.path == "agent_memory.db"
        assert config.check_same_thread is False
        assert config.timeout == 5.0
    
    def test_custom_config(self):
        """Test custom database configuration."""
        config = DatabaseConfig(
            path="/custom/path.db",
            check_same_thread=True,
            timeout=10.0
        )
        assert config.path == "/custom/path.db"
        assert config.check_same_thread is True
        assert config.timeout == 10.0
    
    def test_validation_empty_path(self):
        """Test validation fails with empty path."""
        config = DatabaseConfig(path="")
        with pytest.raises(ConfigurationError, match="cannot be empty"):
            config.validate()
    
    def test_validation_negative_timeout(self):
        """Test validation fails with negative timeout."""
        config = DatabaseConfig(timeout=-1.0)
        with pytest.raises(ConfigurationError, match="must be positive"):
            config.validate()


class TestLLMConfig:
    """Test LLM configuration."""
    
    def test_default_config(self):
        """Test default LLM configuration."""
        config = LLMConfig()
        assert config.host  # Should have a default
        assert config.model == "llama3.2"
        assert config.timeout == 30
        assert config.max_retries == 3
    
    def test_custom_config(self):
        """Test custom LLM configuration."""
        config = LLMConfig(
            host="http://custom:11434",
            model="llama2",
            timeout=60,
            max_retries=5
        )
        assert config.host == "http://custom:11434"
        assert config.model == "llama2"
        assert config.timeout == 60
        assert config.max_retries == 5
    
    def test_validation_empty_host(self):
        """Test validation fails with empty host."""
        config = LLMConfig(host="")
        with pytest.raises(ConfigurationError, match="cannot be empty"):
            config.validate()
    
    def test_validation_negative_timeout(self):
        """Test validation fails with negative timeout."""
        config = LLMConfig(timeout=-1)
        with pytest.raises(ConfigurationError, match="must be positive"):
            config.validate()
    
    def test_validation_zero_retries(self):
        """Test validation fails with zero retries."""
        config = LLMConfig(max_retries=0)
        with pytest.raises(ConfigurationError, match="must be at least 1"):
            config.validate()


class TestFastModeConfig:
    """Test fast mode configuration."""
    
    def test_default_config(self):
        """Test default fast mode configuration."""
        config = FastModeConfig()
        assert config.gliner_model == "urchade/gliner_small-v2.1"
        assert len(config.entity_labels) > 0
        assert "support" in config.sentiment_thresholds
    
    def test_custom_config(self):
        """Test custom fast mode configuration."""
        config = FastModeConfig(
            gliner_model="custom-model",
            entity_labels=["Custom"],
            sentiment_thresholds={"custom": 0.5}
        )
        assert config.gliner_model == "custom-model"
        assert config.entity_labels == ["Custom"]
        assert config.sentiment_thresholds == {"custom": 0.5}
    
    def test_validation_empty_model(self):
        """Test validation fails with empty model name."""
        config = FastModeConfig(gliner_model="")
        with pytest.raises(ConfigurationError, match="cannot be empty"):
            config.validate()
    
    def test_validation_empty_labels(self):
        """Test validation fails with empty labels."""
        config = FastModeConfig(entity_labels=[])
        with pytest.raises(ConfigurationError, match="cannot be empty"):
            config.validate()


class TestGhostKGConfig:
    """Test main GhostKG configuration."""
    
    def test_default_config(self):
        """Test default GhostKG configuration."""
        config = GhostKGConfig()
        assert isinstance(config.fsrs, FSRSConfig)
        assert isinstance(config.database, DatabaseConfig)
        assert isinstance(config.llm, LLMConfig)
        assert isinstance(config.fast_mode, FastModeConfig)
    
    def test_custom_config(self):
        """Test custom GhostKG configuration."""
        config = GhostKGConfig(
            llm=LLMConfig(model="llama2"),
            database=DatabaseConfig(path="/custom/path.db")
        )
        assert config.llm.model == "llama2"
        assert config.database.path == "/custom/path.db"
    
    def test_validate_all(self):
        """Test validation of all sub-configurations."""
        config = GhostKGConfig()
        config.validate()  # Should not raise
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = GhostKGConfig()
        data = config.to_dict()
        assert "fsrs" in data
        assert "database" in data
        assert "llm" in data
        assert "fast_mode" in data
    
    def test_from_dict_default(self):
        """Test loading from empty dictionary."""
        config = GhostKGConfig.from_dict({})
        assert isinstance(config, GhostKGConfig)
        config.validate()
    
    def test_from_dict_partial(self):
        """Test loading from partial dictionary."""
        data = {
            "llm": {"model": "llama2"},
            "database": {"path": "/custom/path.db"}
        }
        config = GhostKGConfig.from_dict(data)
        assert config.llm.model == "llama2"
        assert config.database.path == "/custom/path.db"
        # Other configs should have defaults
        assert len(config.fsrs.parameters) == 17
    
    def test_from_dict_full(self):
        """Test loading from full dictionary."""
        data = {
            "fsrs": {"parameters": [1.0] * 17},
            "database": {"path": "/test.db", "timeout": 10.0},
            "llm": {"host": "http://test:11434", "model": "llama2", "timeout": 60},
            "fast_mode": {"gliner_model": "custom", "entity_labels": ["Custom"]}
        }
        config = GhostKGConfig.from_dict(data)
        assert config.fsrs.parameters == [1.0] * 17
        assert config.database.path == "/test.db"
        assert config.llm.model == "llama2"
        assert config.fast_mode.gliner_model == "custom"
    
    def test_from_dict_invalid(self):
        """Test loading from invalid dictionary."""
        data = {"llm": {"timeout": "invalid"}}  # String instead of int
        with pytest.raises(ConfigurationError):
            GhostKGConfig.from_dict(data)
    
    def test_from_env_default(self):
        """Test loading from environment with no variables set."""
        # Clear any GHOSTKG_ variables
        original_env = os.environ.copy()
        try:
            for key in list(os.environ.keys()):
                if key.startswith("GHOSTKG_"):
                    del os.environ[key]
            
            config = GhostKGConfig.from_env()
            assert isinstance(config, GhostKGConfig)
            config.validate()
        finally:
            os.environ.clear()
            os.environ.update(original_env)
    
    def test_from_env_custom(self):
        """Test loading from environment with custom variables."""
        original_env = os.environ.copy()
        try:
            os.environ["GHOSTKG_LLM_HOST"] = "http://custom:11434"
            os.environ["GHOSTKG_LLM_MODEL"] = "llama2"
            os.environ["GHOSTKG_DATABASE_PATH"] = "/custom/path.db"
            os.environ["GHOSTKG_DATABASE_TIMEOUT"] = "10.5"
            
            config = GhostKGConfig.from_env()
            assert config.llm.host == "http://custom:11434"
            assert config.llm.model == "llama2"
            assert config.database.path == "/custom/path.db"
            assert config.database.timeout == 10.5
        finally:
            os.environ.clear()
            os.environ.update(original_env)
    
    def test_from_env_bool_conversion(self):
        """Test boolean conversion from environment."""
        original_env = os.environ.copy()
        try:
            os.environ["GHOSTKG_DATABASE_CHECK_SAME_THREAD"] = "true"
            
            config = GhostKGConfig.from_env()
            assert config.database.check_same_thread is True
        finally:
            os.environ.clear()
            os.environ.update(original_env)
    
    def test_from_json_file(self):
        """Test loading from JSON file."""
        data = {
            "llm": {"model": "llama2"},
            "database": {"path": "/test.db"}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name
        
        try:
            config = GhostKGConfig.from_json(temp_path)
            assert config.llm.model == "llama2"
            assert config.database.path == "/test.db"
        finally:
            os.unlink(temp_path)
    
    def test_from_json_file_not_found(self):
        """Test loading from non-existent JSON file."""
        with pytest.raises(ConfigurationError, match="not found"):
            GhostKGConfig.from_json("/nonexistent/config.json")
    
    def test_from_json_invalid_json(self):
        """Test loading from invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            temp_path = f.name
        
        try:
            with pytest.raises(ConfigurationError, match="Invalid JSON"):
                GhostKGConfig.from_json(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_from_yaml_file(self):
        """Test loading from YAML file."""
        try:
            import yaml
        except ImportError:
            pytest.skip("PyYAML not installed")
        
        data = """
        llm:
          model: llama2
        database:
          path: /test.db
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(data)
            temp_path = f.name
        
        try:
            config = GhostKGConfig.from_yaml(temp_path)
            assert config.llm.model == "llama2"
            assert config.database.path == "/test.db"
        finally:
            os.unlink(temp_path)
    
    def test_from_yaml_file_not_found(self):
        """Test loading from non-existent YAML file."""
        try:
            import yaml
        except ImportError:
            pytest.skip("PyYAML not installed")
        
        with pytest.raises(ConfigurationError, match="not found"):
            GhostKGConfig.from_yaml("/nonexistent/config.yaml")


class TestGetDefaultConfig:
    """Test convenience function."""
    
    def test_get_default_config(self):
        """Test getting default configuration."""
        config = get_default_config()
        assert isinstance(config, GhostKGConfig)
        config.validate()
