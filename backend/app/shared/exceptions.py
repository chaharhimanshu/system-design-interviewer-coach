"""
Shared Exceptions for System Design Interview Coach
Common exceptions used across the application
"""


class SDCoachException(Exception):
    """Base exception for all application exceptions"""

    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class AuthenticationError(SDCoachException):
    """Raised when authentication fails"""

    pass


class AuthorizationError(SDCoachException):
    """Raised when user lacks permission"""

    pass


class UserNotFoundError(SDCoachException):
    """Raised when user is not found"""

    pass


class InvalidTokenError(AuthenticationError):
    """Raised when JWT token is invalid"""

    pass


class ValidationError(SDCoachException):
    """Raised when input validation fails"""

    pass


class BusinessRuleError(SDCoachException):
    """Raised when business rule is violated"""

    pass


class ExternalServiceError(SDCoachException):
    """Raised when external service fails"""

    pass


class DatabaseError(SDCoachException):
    """Raised when database operation fails"""

    pass


class SessionNotFoundError(SDCoachException):
    """Raised when interview session is not found"""

    pass


class ResourceNotFoundError(SDCoachException):
    """Raised when a resource is not found"""

    pass


class ConflictError(SDCoachException):
    """Raised when there is a conflict in the operation"""

    pass


class BusinessLogicError(SDCoachException):
    """Raised when business logic validation fails"""

    pass


class QuestionGenerationError(SDCoachException):
    """Raised when question generation fails"""

    pass


class EvaluationError(SDCoachException):
    """Raised when evaluation fails"""

    pass
