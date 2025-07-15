from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Callable

T = TypeVar("T")
E = TypeVar("E")
U = TypeVar("U")
F = TypeVar("F")

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
            return f"Err({self.unwrap_err()})"


class Ok(Result[T, E]):
    def __init__(self, value: T):
        self._value = value

    def is_ok(self) -> bool:
        return True

    def is_err(self) -> bool:
        return False

    # NOTE: ALL AND ANY CODE THAT can rise exceptiion is UNSAFE/NONSENSIAL
    # and belongs to mixin that would be creates as a sepparate file or anyhow
    # ... or maybe use some conditional avialability like @unsafe decorator
    # which would either make it to be a stub that raises exception DO NOT USE
    # or would be acrual functionality somthing denotational and working?

    # FIXME: Potentialy unsafe (if called on Err)
    # def unwrap(self) -> T:
    #     return self._value

    # FIXME: Unsafe and BAD (put in UNSAFE)
    # def map(self, f: Callable[[T], U]) -> "Result[U, E]":
    #     try:
    #         return Ok(f(self._value))
    #     except Exception as e:
    #         return Err(e)

    # FIXME: UNSAFE if Err
    # def map_err(self, f: Callable[[E], F]) -> "Result[T, F]":
    #     return Ok(self._value)

    # FIXME: This is obviously BAD, find a better way (put in unsafe)
    # def bind(self, f: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
    #    try:
    #        return f(self._value)
    #     except Exception as e:
    #         return Err(e)

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

    # FIXME: Potentialy unsafe (if called on Ok)
    # def unwrap_err(self) -> E:
    #     return self._error

    # FIXME: UNSAFE if Ok
    # def map(self, f: Callable[[T], U]) -> "Result[U, E]":
    #     return Err(self._error)

    # FIXME: unsafe
    # def map_err(self, f: Callable[[E], F]) -> "Result[T, F]":
    #     try:
    #         return Err(f(self._error))
    #     except Exception as e:
    #         return Err(e)

    # FIXME: UNSAFE if Ok
    # def bind(self, f: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
    #     return Err(self._error)

    def fold(self, on_ok: Callable[[T], U], on_err: Callable[[E], U]) -> U:
        return on_err(self._error)

    def to_dict(self) -> dict:
        return {"err": self._error}

    def unwrap_or(self, default: T) -> T:
        return default

    def unwrap_or_else(self, f: Callable[[E], T]) -> T:
        return f(self._error)
