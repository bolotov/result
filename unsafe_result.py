from result import Ok, Err, T, E, Result
from typing import Callable, TypeVar, Union

class UnsafeMethodCallError(Exception): ...

class UnsafeMixin:
    def unwrap(self) -> T:
        if self.is_ok():
            return self._value  # Use protected/internal access
        raise UnsafeMethodCallError("Called unwrap on Err")

    def unwrap_err(self) -> E:
        if self.is_err():
            return self._error
        raise UnsafeMethodCallError("Called unwrap_err on Ok")

class UnsafeOk(UnsafeMixin, Ok[T, E]):
    pass

class UnsafeErr(UnsafeMixin, Err[T, E]):
    pass

def unsafe_ok(value: T) -> UnsafeOk[T, E]:
    return UnsafeOk(value)

def unsafe_err(error: E) -> UnsafeErr[T, E]:
    return UnsafeErr(error)

UnsafeResult = Union[UnsafeOk[T, E], UnsafeErr[T, E]]

