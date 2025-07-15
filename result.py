from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Callable

T = TypeVar("T")
E = TypeVar("E")
U = TypeVar("U")
F = TypeVar("F")

# MARK: Decorators for denotation
def pure(func): return func  # document intent only
def total(func): return func
def partial(reason): return lambda func: func
def unsafe(reason): return lambda func: func
def composable(func): return func


class Result(ABC, Generic[T, E]):
    @abstractmethod
    @pure
    @total
    def is_ok(self) -> bool: ...

    @abstractmethod
    @pure
    @total
    def is_err(self) -> bool: ...

    @abstractmethod
    @pure
    @total
    def unwrap_or(self, default: T) -> T: ...

    @abstractmethod
    @pure
    @total
    def unwrap_or_else(self, f: Callable[[E], T]) -> T: ...

    @abstractmethod
    @pure
    @total
    def fold(self, on_ok: Callable[[T], U], on_err: Callable[[E], U]) -> U: ...

    @abstractmethod
    @pure
    @total
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
