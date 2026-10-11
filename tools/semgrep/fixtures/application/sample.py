from app.domain.money import Money


def dependency() -> type[Money]:
    return Money


class Order:
    pass
