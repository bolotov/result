from result import Ok, Err, T, E, Result, U, F
from typing import Callable, TypeVar, Union

class UnsafeMethodCallError(Exception):
    """Exception raised when unsafe methods are called on wrong Result variant"""
    ...

class UnsafeMixin:
    """Mixin providing unsafe methods that can raise exceptions"""
    
    def unwrap(self) -> T:
        """Extract the Ok value. Raises UnsafeMethodCallError if called on Err"""
        if self.is_ok():
            return self._value
        raise UnsafeMethodCallError("Called unwrap on Err")
    
    def unwrap_err(self) -> E:
        """Extract the Err value. Raises UnsafeMethodCallError if called on Ok"""
        if self.is_err():
            return self._error
        raise UnsafeMethodCallError("Called unwrap_err on Ok")
    
    def map(self, f: Callable[[T], U]) -> "Result[U, E]":
        """Map a function over the Ok value, catching exceptions"""
        if self.is_ok():
            try:
                return unsafe_ok(f(self._value))
            except Exception as e:
                return unsafe_err(e)
        else:
            return unsafe_err(self._error)
    
    def map_err(self, f: Callable[[E], F]) -> "Result[T, F]":
        """Map a function over the Err value, catching exceptions"""
        if self.is_err():
            try:
                return unsafe_err(f(self._error))
            except Exception as e:
                return unsafe_err(e)
        else:
            return unsafe_ok(self._value)
    
    def bind(self, f: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        """Monadic bind operation, catching exceptions"""
        if self.is_ok():
            try:
                return f(self._value)
            except Exception as e:
                return unsafe_err(e)
        else:
            return unsafe_err(self._error)
    
    def and_then(self, f: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        """Alias for bind - more readable for some use cases"""
        return self.bind(f)
    
    def or_else(self, f: Callable[[E], "Result[T, F]"]) -> "Result[T, F]":
        """Chain error handling - if Err, try to recover"""
        if self.is_err():
            try:
                return f(self._error)
            except Exception as e:
                return unsafe_err(e)
        else:
            return unsafe_ok(self._value)

class UnsafeOk(UnsafeMixin, Ok[T, E]):
    """Ok variant with unsafe methods available"""
    ...

class UnsafeErr(UnsafeMixin, Err[T, E]):
    """Err variant with unsafe methods available"""
    ...

def unsafe_ok(value: T) -> UnsafeOk[T, E]:
    """Create an UnsafeOk instance"""
    return UnsafeOk(value)

def unsafe_err(error: E) -> UnsafeErr[T, E]:
    """Create an UnsafeErr instance"""
    return UnsafeErr(error)

# Type alias for better readability
UnsafeResult = Union[UnsafeOk[T, E], UnsafeErr[T, E]]

# Utility functions for working with unsafe results
def try_unsafe(f: Callable[[], T]) -> UnsafeResult[T, Exception]:
    """Execute a function and wrap result in UnsafeResult"""
    try:
        return unsafe_ok(f())
    except Exception as e:
        return unsafe_err(e)

def chain_unsafe(*operations: Callable[[T], UnsafeResult[T, E]]) -> Callable[[T], UnsafeResult[T, E]]:
    """Chain multiple unsafe operations together"""
    def chained(value: T) -> UnsafeResult[T, E]:
        result = unsafe_ok(value)
        for op in operations:
            if result.is_ok():
                result = result.bind(op)
            else:
                break
        return result
    return chained
