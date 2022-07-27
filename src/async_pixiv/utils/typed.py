from typing_extensions import Literal

__all__ = [
    'RequestMethod',
]

RequestMethod = Literal['GET', 'POST', 'HEAD', 'PUT', 'PATCH', 'DELETE']
