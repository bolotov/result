# class `Result` (early alpha-version)

This is a Result implementation in Python.

`Result` type represents  retult of opreation that can finish succesfully or not (with an error). It is an alternative approach to handle exceptions, where result either has sucessful value (`Ok`), or the value of an error (`Err`).

This approach allowes to handle errors and exceptions in more controlled and predictable way.



## Initialisation

```python
Result(ok: Optional[T] = None, err: Optional[E] = None)
```

This creates `Result`which accepts either success value (`ok`) or error value (`err`) but not both.

Passing both or none will cause `ValueError` (**I know** it's a chicken egg problem for now).


It will be made in such a way that it would be possible to drop it into a project.
API is unstable and may be a subject of changes

