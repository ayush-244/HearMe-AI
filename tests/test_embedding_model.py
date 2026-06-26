"""Unit tests for the embedding model wrapper."""
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from ai.embeddings.embedding_model import EmbeddingModel


@pytest.fixture
def mock_sentence_transformer():
    with patch("sentence_transformers.SentenceTransformer") as mock_st:
        mock_instance = MagicMock()
        mock_instance.get_sentence_embedding_dimension.return_value = 768
        mock_instance.encode.return_value = MagicMock()
        mock_instance.encode.return_value.tolist.return_value = [0.1] * 768
        mock_instance.device = "cpu"
        mock_st.return_value = mock_instance
        yield mock_st, mock_instance


class TestEmbeddingModel:
    def test_initialization_defaults(self):
        model = EmbeddingModel()
        assert model.model_name == "BAAI/bge-base-en-v1.5"
        assert model.batch_size == 32
        assert model.max_seq_length == 512
        assert model.is_loaded is False

    def test_initialization_custom(self):
        model = EmbeddingModel(
            model_name="custom-model",
            batch_size=64,
            max_seq_length=256,
            device="cpu",
        )
        assert model.model_name == "custom-model"
        assert model.batch_size == 64
        assert model.max_seq_length == 256
        assert model.is_loaded is False

    def test_initialize_loads_model(self, mock_sentence_transformer):
        mock_st, mock_instance = mock_sentence_transformer
        model = EmbeddingModel(model_name="test-model", batch_size=16)
        model.initialize()

        assert model.is_loaded is True
        assert model.dimension == 768
        mock_st.assert_called_once_with("test-model", device=None)
        assert mock_instance.max_seq_length == 512

    def test_initialize_idempotent(self, mock_sentence_transformer):
        mock_st, _ = mock_sentence_transformer
        model = EmbeddingModel(model_name="test-model")
        model.initialize()
        model.initialize()

        assert mock_st.call_count == 1

    def test_embed_single_text(self, mock_sentence_transformer):
        _, mock_instance = mock_sentence_transformer
        model = EmbeddingModel()
        model.initialize()

        vector = model.embed("Hello world")
        assert len(vector) == 768
        mock_instance.encode.assert_called_once()

    def test_embed_empty_text(self, mock_sentence_transformer):
        _, mock_instance = mock_sentence_transformer
        model = EmbeddingModel()
        model.initialize()

        vector = model.embed("")
        assert len(vector) == 768
        assert all(v == 0.0 for v in vector)
        mock_instance.encode.assert_not_called()

    def test_embed_whitespace_text(self, mock_sentence_transformer):
        _, mock_instance = mock_sentence_transformer
        model = EmbeddingModel()
        model.initialize()

        vector = model.embed("   \n  ")
        assert len(vector) == 768
        assert all(v == 0.0 for v in vector)
        mock_instance.encode.assert_not_called()

    def test_embed_batch(self, mock_sentence_transformer):
        _, mock_instance = mock_sentence_transformer
        mock_instance.encode.return_value = [
            MagicMock(tolist=lambda: [0.1] * 768),
            MagicMock(tolist=lambda: [0.2] * 768),
        ]
        model = EmbeddingModel(batch_size=16)
        model.initialize()

        vectors = model.embed_batch(["text one", "text two"])
        assert len(vectors) == 2
        assert len(vectors[0]) == 768
        assert len(vectors[1]) == 768

    def test_embed_batch_empty(self, mock_sentence_transformer):
        model = EmbeddingModel()
        model.initialize()

        vectors = model.embed_batch([])
        assert vectors == []

    def test_embed_batch_with_empty_texts(self, mock_sentence_transformer):
        _, mock_instance = mock_sentence_transformer
        # Single encode call with valid texts only
        mock_instance.encode.return_value = [
            MagicMock(tolist=lambda: [0.1] * 768),
            MagicMock(tolist=lambda: [0.0] * 768),
        ]
        model = EmbeddingModel()
        model.initialize()

        vectors = model.embed_batch(["valid text", ""])
        assert len(vectors) == 2
        mock_instance.encode.assert_called_once()

    def test_get_model_info_before_init(self, mock_sentence_transformer):
        model = EmbeddingModel()
        info = model.get_model_info()
        assert info["model_name"] == "BAAI/bge-base-en-v1.5"
        assert info["dimension"] == 768

    def test_get_model_info(self, mock_sentence_transformer):
        model = EmbeddingModel(model_name="test-model")
        model.initialize()
        info = model.get_model_info()
        assert info["model_name"] == "test-model"
        assert info["dimension"] == 768
        assert info["batch_size"] == 32
        assert info["max_seq_length"] == 512

    def test_dimension_property(self, mock_sentence_transformer):
        with patch("sentence_transformers.SentenceTransformer") as mock_st:
            mock_instance = MagicMock()
            mock_instance.get_sentence_embedding_dimension.return_value = 384
            mock_instance.encode.return_value = MagicMock()
            mock_instance.encode.return_value.tolist.return_value = [0.1] * 384
            mock_st.return_value = mock_instance

            model = EmbeddingModel()
            model.initialize()
            assert model.dimension == 384

    def test_initialize_error(self):
        with patch("sentence_transformers.SentenceTransformer") as mock_st:
            mock_st.side_effect = RuntimeError("Model not found")
            model = EmbeddingModel(model_name="nonexistent-model")
            with pytest.raises(RuntimeError, match="Model not found"):
                model.initialize()

    def test_auto_initialize_on_embed(self, mock_sentence_transformer):
        _, mock_instance = mock_sentence_transformer
        model = EmbeddingModel()
        # No explicit initialize call
        vector = model.embed("auto init test")
        assert len(vector) == 768
        mock_instance.encode.assert_called_once()
