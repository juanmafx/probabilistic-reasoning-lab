# Domain errors raised for invalid input and unsatisfiable models.
class ProbabilisticArgumentsError(ValueError):
    pass


class FormulaSyntaxError(ProbabilisticArgumentsError):
    pass


class InvalidProbabilityError(ProbabilisticArgumentsError):
    pass


class InconsistentPremisesError(ProbabilisticArgumentsError):
    pass


class ModelError(ProbabilisticArgumentsError):
    pass


class StorageError(ProbabilisticArgumentsError):
    pass
