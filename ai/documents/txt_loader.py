import logging

logger = logging.getLogger(__name__)


class TXTLoader:
    def __init__(self):
        pass

    def validate(self, filepath: str) -> bool:
        pass

    def extract(self, filepath: str) -> str:
        pass

    def load(self, filepath: str) -> str:
        pass
