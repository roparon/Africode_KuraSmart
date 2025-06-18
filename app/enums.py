import enum

class UserRole(enum.Enum):
    voter = "voter"
    candidate = "candidate"
    admin = "admin"
    super_admin = "super_admin"