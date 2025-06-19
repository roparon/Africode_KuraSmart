import enum
from enum import Enum

class UserRole(enum.Enum):
    voter = "voter"
    candidate = "candidate"
    admin = "admin"
    super_admin = "super_admin"

class ElectionStatusEnum(str, Enum):
    INACTIVE = "inactive"
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"
