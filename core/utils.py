import unicodedata


def normalizar(texto):
    """Minúsculas e sem acentos (para ordenar e buscar)."""
    sem_acento = "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")
    return sem_acento.lower()
