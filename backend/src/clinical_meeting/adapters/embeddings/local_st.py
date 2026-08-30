from sentence_transformers import SentenceTransformer


class LocalSentenceTransformerAdapter:
    def __init__(self, model_name: str) -> None:
        self._model = SentenceTransformer(model_name)
        self._model_name = model_name

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model.encode(texts, normalize_embeddings=True)
        return [vector.tolist() for vector in vectors]

    @property
    def dimension(self) -> int:
        size = self._model.get_sentence_embedding_dimension()
        if size is None:
            raise RuntimeError("Embedding model did not report vector dimension")
        return int(size)

    @property
    def model_name(self) -> str:
        return self._model_name
