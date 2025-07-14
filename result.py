from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Callable

T = TypeVar("T")
E = TypeVar("E")

class Result(ABC, Generic[T, E]):
    @abstractmethod
    def is_ok(self) -> bool:
        pass

    @abstractmethod
    def is_err(self) -> bool:
        pass

    @abstractmethod
    def unwrap_or(self, default: T) -> T:
        pass

    @abstractmethod
    def unwrap_or_else(self, f: Callable[[E], T]) -> T:
        pass

class Ok(Result[T, E]):
    def __init__(self, value: T):
        self._value = value

    def is_ok(self) -> bool:
        return True

    def is_err(self) -> bool:
        return False

    def unwrap(self) -> T:
        return self._value

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

    def unwrap_err(self) -> E:
        return self._error

    def unwrap_or(self, default: T) -> T:
        return default

    def unwrap_or_else(self, f: Callable[[E], T]) -> T:
        return f(self._error)
