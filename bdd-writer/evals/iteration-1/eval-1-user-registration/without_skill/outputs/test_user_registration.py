"""
用户注册功能测试模块

测试用户注册时用户名、密码、邮箱的验证规则
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import pytest
from pydantic import BaseModel, field_validator


# ============ 数据模型 ============

class UserRegistration(BaseModel):
    """用户注册数据模型"""

    username: str
    password: str
    confirm_password: str
    email: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """验证用户名"""
        if not v:
            raise ValueError("用户名不能为空")
        if len(v) < 3 or len(v) > 20:
            raise ValueError("用户名长度必须在3-20个字符之间")
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("用户名只能包含字母、数字和下划线")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """验证密码"""
        if not v:
            raise ValueError("密码不能为空")
        if len(v) < 8:
            raise ValueError("密码长度至少为8个字符")
        if not re.search(r"[a-z]", v):
            raise ValueError("密码必须包含大小写字母和数字")
        if not re.search(r"[A-Z]", v):
            raise ValueError("密码必须包含大小写字母和数字")
        if not re.search(r"\d", v):
            raise ValueError("密码必须包含大小写字母和数字")
        return v

    @field_validator("confirm_password")
    @classmethod
    def validate_confirm_password(cls, v: str, info: Any) -> str:
        """验证密码确认"""
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("两次输入的密码不一致")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """验证邮箱"""
        if not v:
            raise ValueError("邮箱不能为空")
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, v):
            raise ValueError("邮箱格式不正确")
        return v


@dataclass
class UserRepository:
    """用户仓库（模拟数据库）"""

    existing_usernames: set[str]
    existing_emails: set[str]

    def username_exists(self, username: str) -> bool:
        """检查用户名是否存在"""
        return username in self.existing_usernames

    def email_exists(self, email: str) -> bool:
        """检查邮箱是否存在"""
        return email in self.existing_emails


@dataclass
class RegistrationResult:
    """注册结果"""

    success: bool
    message: str
    user: UserRegistration | None = None


class RegistrationService:
    """用户注册服务"""

    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    def register(self, data: dict[str, str]) -> RegistrationResult:
        """执行用户注册"""
        try:
            user = UserRegistration(**data)
        except ValueError as e:
            return RegistrationResult(success=False, message=str(e))

        # 检查用户名唯一性
        if self.user_repository.username_exists(user.username):
            return RegistrationResult(success=False, message="用户名已被注册")

        # 检查邮箱唯一性
        if self.user_repository.email_exists(user.email):
            return RegistrationResult(success=False, message="邮箱已被注册")

        return RegistrationResult(success=True, message="注册成功", user=user)


# ============ 测试夹具 ============

@pytest.fixture
def empty_repository() -> UserRepository:
    """空的用户仓库"""
    return UserRepository(existing_usernames=set(), existing_emails=set())


@pytest.fixture
def populated_repository() -> UserRepository:
    """包含已注册用户的仓库"""
    return UserRepository(
        existing_usernames={"existinguser", "admin"},
        existing_emails={"existing@example.com", "admin@example.com"},
    )


@pytest.fixture
def registration_service(empty_repository: UserRepository) -> RegistrationService:
    """注册服务实例"""
    return RegistrationService(empty_repository)


@pytest.fixture
def registration_service_with_existing_users(
    populated_repository: UserRepository,
) -> RegistrationService:
    """包含已存在用户的注册服务"""
    return RegistrationService(populated_repository)


# ============ 成功注册测试 ============

class TestSuccessfulRegistration:
    """成功注册测试"""

    def test_valid_registration(
        self, registration_service: RegistrationService
    ) -> None:
        """测试使用有效信息成功注册"""
        # Given: 有效的注册数据
        data = {
            "username": "testuser",
            "password": "Password123",
            "confirm_password": "Password123",
            "email": "test@example.com",
        }

        # When: 执行注册
        result = registration_service.register(data)

        # Then: 注册成功
        assert result.success is True
        assert result.message == "注册成功"
        assert result.user is not None
        assert result.user.username == "testuser"
        assert result.user.email == "test@example.com"

    def test_registration_with_underscore_username(
        self, registration_service: RegistrationService
    ) -> None:
        """测试用户名包含下划线"""
        data = {
            "username": "test_user_2024",
            "password": "SecurePass1",
            "confirm_password": "SecurePass1",
            "email": "underscore@example.com",
        }

        result = registration_service.register(data)

        assert result.success is True
        assert result.user is not None
        assert result.user.username == "test_user_2024"


# ============ 用户名验证测试 ============

class TestUsernameValidation:
    """用户名验证测试"""

    @pytest.mark.parametrize(
        "username,expected_error",
        [
            ("", "用户名不能为空"),
            ("ab", "用户名长度必须在3-20个字符之间"),
            ("a" * 21, "用户名长度必须在3-20个字符之间"),
            ("test@user", "用户名只能包含字母、数字和下划线"),
            ("test user", "用户名只能包含字母、数字和下划线"),
            ("test-user", "用户名只能包含字母、数字和下划线"),
            ("test.user", "用户名只能包含字母、数字和下划线"),
            ("test中文", "用户名只能包含字母、数字和下划线"),
        ],
    )
    def test_invalid_username(
        self,
        registration_service: RegistrationService,
        username: str,
        expected_error: str,
    ) -> None:
        """测试无效用户名"""
        data = {
            "username": username,
            "password": "Password123",
            "confirm_password": "Password123",
            "email": "test@example.com",
        }

        result = registration_service.register(data)

        assert result.success is False
        assert expected_error in result.message

    def test_username_already_exists(
        self,
        registration_service_with_existing_users: RegistrationService,
    ) -> None:
        """测试用户名已被注册"""
        data = {
            "username": "existinguser",
            "password": "Password123",
            "confirm_password": "Password123",
            "email": "new@example.com",
        }

        result = registration_service_with_existing_users.register(data)

        assert result.success is False
        assert result.message == "用户名已被注册"


# ============ 密码验证测试 ============

class TestPasswordValidation:
    """密码验证测试"""

    @pytest.mark.parametrize(
        "password,confirm_password,expected_error",
        [
            ("", "", "密码不能为空"),
            ("Pass1", "Pass1", "密码长度至少为8个字符"),
            ("password", "password", "密码必须包含大小写字母和数字"),
            ("PASSWORD", "PASSWORD", "密码必须包含大小写字母和数字"),
            ("Password", "Password", "密码必须包含大小写字母和数字"),
            ("password123", "password123", "密码必须包含大小写字母和数字"),
            ("PASSWORD123", "PASSWORD123", "密码必须包含大小写字母和数字"),
            ("Password123", "Password456", "两次输入的密码不一致"),
        ],
    )
    def test_invalid_password(
        self,
        registration_service: RegistrationService,
        password: str,
        confirm_password: str,
        expected_error: str,
    ) -> None:
        """测试无效密码"""
        data = {
            "username": "testuser",
            "password": password,
            "confirm_password": confirm_password,
            "email": "test@example.com",
        }

        result = registration_service.register(data)

        assert result.success is False
        assert expected_error in result.message

    @pytest.mark.parametrize(
        "password",
        [
            "Password1",
            "Abcdefg1",
            "Test1234",
            "MySecure2024Pass",
        ],
    )
    def test_valid_passwords(
        self, registration_service: RegistrationService, password: str
    ) -> None:
        """测试有效密码"""
        data = {
            "username": "testuser",
            "password": password,
            "confirm_password": password,
            "email": "test@example.com",
        }

        result = registration_service.register(data)

        assert result.success is True


# ============ 邮箱验证测试 ============

class TestEmailValidation:
    """邮箱验证测试"""

    @pytest.mark.parametrize(
        "email,expected_error",
        [
            ("", "邮箱不能为空"),
            ("invalid", "邮箱格式不正确"),
            ("test@", "邮箱格式不正确"),
            ("@example.com", "邮箱格式不正确"),
            ("test@.com", "邮箱格式不正确"),
            ("test@example", "邮箱格式不正确"),
            ("test@@example.com", "邮箱格式不正确"),
            ("test @example.com", "邮箱格式不正确"),
        ],
    )
    def test_invalid_email(
        self,
        registration_service: RegistrationService,
        email: str,
        expected_error: str,
    ) -> None:
        """测试无效邮箱"""
        data = {
            "username": "testuser",
            "password": "Password123",
            "confirm_password": "Password123",
            "email": email,
        }

        result = registration_service.register(data)

        assert result.success is False
        assert expected_error in result.message

    @pytest.mark.parametrize(
        "email",
        [
            "test@example.com",
            "user.name@example.com",
            "user+tag@example.org",
            "test123@sub.example.com",
            "a@b.co",
        ],
    )
    def test_valid_emails(
        self, registration_service: RegistrationService, email: str
    ) -> None:
        """测试有效邮箱"""
        data = {
            "username": "testuser",
            "password": "Password123",
            "confirm_password": "Password123",
            "email": email,
        }

        result = registration_service.register(data)

        assert result.success is True

    def test_email_already_exists(
        self,
        registration_service_with_existing_users: RegistrationService,
    ) -> None:
        """测试邮箱已被注册"""
        data = {
            "username": "newuser",
            "password": "Password123",
            "confirm_password": "Password123",
            "email": "existing@example.com",
        }

        result = registration_service_with_existing_users.register(data)

        assert result.success is False
        assert result.message == "邮箱已被注册"


# ============ 边界值测试 ============

class TestBoundaryValues:
    """边界值测试"""

    def test_username_min_length(
        self, registration_service: RegistrationService
    ) -> None:
        """测试用户名最小长度（3个字符）"""
        data = {
            "username": "abc",
            "password": "Password123",
            "confirm_password": "Password123",
            "email": "test@example.com",
        }

        result = registration_service.register(data)

        assert result.success is True

    def test_username_max_length(
        self, registration_service: RegistrationService
    ) -> None:
        """测试用户名最大长度（20个字符）"""
        data = {
            "username": "a" * 20,
            "password": "Password123",
            "confirm_password": "Password123",
            "email": "test@example.com",
        }

        result = registration_service.register(data)

        assert result.success is True

    def test_password_min_length(
        self, registration_service: RegistrationService
    ) -> None:
        """测试密码最小长度（8个字符）"""
        data = {
            "username": "testuser",
            "password": "Passwo1",
            "confirm_password": "Passwo1",
            "email": "test@example.com",
        }

        result = registration_service.register(data)

        assert result.success is False
        assert "密码长度至少为8个字符" in result.message

    def test_password_exactly_8_chars(
        self, registration_service: RegistrationService
    ) -> None:
        """测试密码正好8个字符"""
        data = {
            "username": "testuser",
            "password": "Passwo12",
            "confirm_password": "Passwo12",
            "email": "test@example.com",
        }

        result = registration_service.register(data)

        assert result.success is True


# ============ 集成测试 ============

class TestRegistrationIntegration:
    """注册集成测试"""

    def test_complete_registration_flow(
        self, empty_repository: UserRepository
    ) -> None:
        """测试完整的注册流程"""
        service = RegistrationService(empty_repository)

        # 第一个用户注册成功
        result1 = service.register(
            {
                "username": "user1",
                "password": "Password123",
                "confirm_password": "Password123",
                "email": "user1@example.com",
            }
        )
        assert result1.success is True

        # 模拟用户已保存到数据库
        empty_repository.existing_usernames.add("user1")
        empty_repository.existing_emails.add("user1@example.com")

        # 第二个用户使用相同用户名注册失败
        result2 = service.register(
            {
                "username": "user1",
                "password": "Password456",
                "confirm_password": "Password456",
                "email": "user2@example.com",
            }
        )
        assert result2.success is False
        assert result2.message == "用户名已被注册"

        # 第二个用户使用不同用户名注册成功
        result3 = service.register(
            {
                "username": "user2",
                "password": "Password456",
                "confirm_password": "Password456",
                "email": "user2@example.com",
            }
        )
        assert result3.success is True