def caching_fibonacci():
    """
    Create a Fibonacci function with internal cache.

    Returns:
        Function that calculates Fibonacci numbers using recursion and caching.
    """
    cache = {}

    def fibonacci(n):
        """
        Calculate the n-th Fibonacci number.

        Args:
            n: Fibonacci sequence index.

        Returns:
            Fibonacci number for the given index.
        """
        if n <= 0:
            result = 0
        elif n == 1:
            result = 1
        elif n in cache:
            result = cache[n]
        else:
            # Store calculated value to avoid repeated recursive calls.
            cache[n] = fibonacci(n - 1) + fibonacci(n - 2)
            result = cache[n]

        return result

    return fibonacci


# Отримуємо функцію fibonacci
fib = caching_fibonacci()

# Використовуємо функцію fibonacci для обчислення чисел Фібоначчі
print(fib(10))  # Виведе 55
print(fib(15))  # Виведе 610
