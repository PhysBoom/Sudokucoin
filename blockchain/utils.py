class CompositeNumbers:
    """Singleton class to find nth composite number"""

    __instance = None

    def __init__(self, *args, **kwargs):
        if CompositeNumbers.__instance is None:
            CompositeNumbers.__instance = self
            is_prime = [True] * 10**5
            for i in range(2, 10**5):
                if i * i > 10**5:
                    break

                if is_prime[i]:
                    for j in range(i * i, 10**5, i):
                        is_prime[j] = False

            self.composite_numbers = [i for i in range(4, 10**5) if not is_prime[i]]
        else:
            raise Exception("This is a singleton class")

    @classmethod
    def get_instance(cls, *args, **kwargs):
        if cls.__instance is None:
            cls(*args, **kwargs)
        return cls.__instance

    def get_nth(self, n):
        return self.composite_numbers[n - 1]
