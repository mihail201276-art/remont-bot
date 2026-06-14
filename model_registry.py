from ai_interface import AIModel, ModelInfo


class ModelRegistry:

    def __init__(self):
        self._models: dict[str, AIModel] = {}

    def register(self, model: AIModel) -> None:
        self._models[model.info.id] = model

    def get_model(self, model_id: str) -> AIModel:
        model = self._models.get(model_id)
        if model is None:
            return next(iter(self._models.values()))
        return model

    def list_models(self) -> list[ModelInfo]:
        return [m.info for m in self._models.values()]

    def get_default(self) -> AIModel:
        return next(iter(self._models.values()))
