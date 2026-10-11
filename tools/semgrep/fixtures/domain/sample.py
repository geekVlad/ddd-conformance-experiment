from app.infrastructure.repository import Repository


def dependency() -> type[Repository]:
    return Repository


class OrderRequest:
    pass


class Order:
    pass
