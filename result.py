from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Callable

T = TypeVar("T")
E = TypeVar("E")
U = TypeVar("U")
F = TypeVar("F")

class Result(ABC, Generic[T, E]):
    @abstractmethod
    def is_ok(self) -> bool: ...

    @abstractmethod
    def is_err(self) -> bool: ...

    @abstractmethod
    def unwrap_or(self, default: T) -> T: ...

    @abstractmethod
    def unwrap_or_else(self, f: Callable[[E], T]) -> T: ...

    @abstractmethod
    def map(self, f: Callable[[T], U]) -> "Result[U, E]": ...

    @abstractmethod
    def map_err(self, f: Callable[[E], F]) -> "Result[T, F]": ...

    @abstractmethod
    def bind(self, f: Callable[[T], Result[U, E]]) -> "Result[U, E]": ...

    @abstractmethod
    def fold(self, on_ok: Callable[[T], U], on_err: Callable[[E], U]) -> U: ...

    @abstractmethod
    def to_dict(self) -> dict: ...

    def __bool__(self) -> bool:
        return self.is_ok()

    def __repr__(self) -> str:
        if self.is_ok():
            return f"Ok({self.unwrap_or(None)})"
        else:
            return f"Err({self.unwrap_or_else(lambda e: e)})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Result):
            return False

        if self.is_ok() and other.is_ok():
            return self.unwrap_or(None) == other.unwrap_or(None)
        elif self.is_err() and other.is_err():
            return self.unwrap_or_else(lambda e: e) == other.unwrap_or_else(lambda e: e)
        else:
            return False

    def __hash__(self) -> int:
        if self.is_ok():
            return hash(("ok", self.unwrap_or(None)))
        else:
            return hash(("err", self.unwrap_or_else(lambda e: e)))

class Ok(Result[T, E]):
    def __init__(self, value: T):
        self._value = value

    def is_ok(self) -> bool:
        return True

    def is_err(self) -> bool:
        return False

    def fold(self, on_ok: Callable[[T], U], on_err: Callable[[E], U]) -> U:
        return on_ok(self._value)

    def to_dict(self) -> dict:
        return {"ok": self._value}

    def unwrap_or(self, default: T) -> T:
        return self._value

    def unwrap_or_else(self, f: Callable[[E], T]) -> T:
        return self._value

class Err(Result[T, E]):
    def __init__(self, error: E):
        self._error = error

    def is_ok(self) -> bool:
        return False

    def is_err(self) -> bool:
        return True

    def fold(self, on_ok: Callable[[T], U], on_err: Callable[[E], U]) -> U:
        return on_err(self._error)

    def to_dict(self) -> dict:
        return {"err": self._error}

    def unwrap_or(self, default: T) -> T:
        return default

    def unwrap_or_else(self, f: Callable[[E], T]) -> T:
        return f(self._error)
