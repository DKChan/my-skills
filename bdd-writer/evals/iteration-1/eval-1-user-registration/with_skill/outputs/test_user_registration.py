"""
用户注册功能测试

业务规则:
- BR-1: 用户名验证 - 长度3-20字符，仅允许字母、数字、下划线，必须唯一
- BR-2: 密码验证 - 长度8-32字符，必须包含字母和数字
- BR-3: 邮箱验证 - 符合邮箱格式，最大100字符，必须唯一
- BR-4: 注册流程 - 验证通过后创建用户，发送验证邮件

测试场景:
- S1-S6: 用户名验证场景
- S7-S11: 密码验证场景
- S12-S14: 邮箱验证场景
- S15-S18: 边界值测试场景
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    pass


# === 被测模块（模拟实现）===

@dataclass
class UserRegistrationInput:
    """用户注册输入数据"""
    username: str
    password: str
    email: str


@dataclass
class RegistrationResult:
    """注册结果"""
    success: bool
    message: str
    user_id: str | None = None


class UserRegistrationError(Exception):
    """用户注册异常"""
    pass


class UserRegistrationService:
    """用户注册服务"""

    # 验证规则常量
    USERNAME_MIN_LENGTH = 3
    USERNAME_MAX_LENGTH = 20
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_MAX_LENGTH = 32
    EMAIL_MAX_LENGTH = 100

    # 正则表达式
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]+$')
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    def __init__(self) -> None:
        """初始化服务，模拟已存在的用户数据"""
        self._existing_usernames: set[str] = {"admin", "testuser"}
        self._existing_emails: set[str] = {"admin@example.com", "test@example.com"}

    def register(self, input_data: UserRegistrationInput) -> RegistrationResult:
        """
        执行用户注册

        Args:
            input_data: 用户注册输入数据

        Returns:
            RegistrationResult: 注册结果

        Raises:
            UserRegistrationError: 注册失败时抛出
        """
        # BR-1: 用户名验证
        self._validate_username(input_data.username)

        # BR-2: 密码验证
        self._validate_password(input_data.password)

        # BR-3: 邮箱验证
        self._validate_email(input_data.email)

        # BR-4: 创建用户
        user_id = self._create_user(input_data)

        return RegistrationResult(
            success=True,
            message="注册成功",
            user_id=user_id
        )

    def _validate_username(self, username: str) -> None:
        """
        验证用户名 (BR-1)

        规则:
        - 不能为空
        - 长度 3-20 字符
        - 仅允许字母、数字、下划线
        - 必须唯一
        """
        if not username:
            raise UserRegistrationError("用户名不能为空")

        if len(username) < self.USERNAME_MIN_LENGTH:
            raise UserRegistrationError(f"用户名长度必须在{self.USERNAME_MIN_LENGTH}-{self.USERNAME_MAX_LENGTH}个字符")

        if len(username) > self.USERNAME_MAX_LENGTH:
            raise UserRegistrationError(f"用户名长度必须在{self.USERNAME_MIN_LENGTH}-{self.USERNAME_MAX_LENGTH}个字符")

        if not self.USERNAME_PATTERN.match(username):
            raise UserRegistrationError("用户名只能包含字母、数字、下划线")

        if username in self._existing_usernames:
            raise UserRegistrationError("用户名已被使用")

    def _validate_password(self, password: str) -> None:
        """
        验证密码 (BR-2)

        规则:
        - 不能为空
        - 长度 8-32 字符
        - 必须包含字母和数字
        """
        if not password:
            raise UserRegistrationError("密码不能为空")

        if len(password) < self.PASSWORD_MIN_LENGTH:
            raise UserRegistrationError(f"密码长度必须在{self.PASSWORD_MIN_LENGTH}-{self.PASSWORD_MAX_LENGTH}个字符")

        if len(password) > self.PASSWORD_MAX_LENGTH:
            raise UserRegistrationError(f"密码长度必须在{self.PASSWORD_MIN_LENGTH}-{self.PASSWORD_MAX_LENGTH}个字符")

        has_letter = any(c.isalpha() for c in password)
        has_digit = any(c.isdigit() for c in password)

        if not (has_letter and has_digit):
            raise UserRegistrationError("密码必须包含字母和数字")

    def _validate_email(self, email: str) -> None:
        """
        验证邮箱 (BR-3)

        规则:
        - 不能为空
        - 符合邮箱格式
        - 最大 100 字符
        - 必须唯一
        """
        if not email:
            raise UserRegistrationError("邮箱不能为空")

        if len(email) > self.EMAIL_MAX_LENGTH:
            raise UserRegistrationError(f"邮箱长度不能超过{self.EMAIL_MAX_LENGTH}个字符")

        if not self.EMAIL_PATTERN.match(email):
            raise UserRegistrationError("邮箱格式不正确")

        if email in self._existing_emails:
            raise UserRegistrationError("邮箱已被注册")

    def _create_user(self, input_data: UserRegistrationInput) -> str:
        """
        创建用户 (BR-4)

        模拟创建用户并返回用户ID
        """
        # 模拟生成用户ID
        user_id = f"user_{input_data.username}"

        # 更新已存在用户集合
        self._existing_usernames.add(input_data.username)
        self._existing_emails.add(input_data.email)

        return user_id


# === 测试类 ===

class TestUserRegistration:
    """用户注册功能测试套件"""

    @pytest.fixture
    def registration_service(self) -> UserRegistrationService:
        """创建注册服务实例"""
        return UserRegistrationService()

    @pytest.fixture
    def valid_input(self) -> UserRegistrationInput:
        """创建有效的注册输入"""
        return UserRegistrationInput(
            username="newuser",
            password="SecurePass123",
            email="newuser@example.com"
        )

    # === BR-1: 用户名验证测试 ===

    @pytest.mark.parametrize(
        "username,expected_error",
        [
            ("", "用户名不能为空"),  # S2: 用户名为空
            ("ab", "用户名长度必须在3-20个字符"),  # S3: 用户名过短
            ("a" * 21, "用户名长度必须在3-20个字符"),  # S4: 用户名过长
            ("user@name", "用户名只能包含字母、数字、下划线"),  # S5: 用户名含非法字符
            ("user name", "用户名只能包含字母、数字、下划线"),  # 含空格
            ("admin", "用户名已被使用"),  # S6: 用户名已存在
        ],
        ids=[
            "empty_username",
            "too_short",
            "too_long",
            "invalid_char_at",
            "invalid_char_space",
            "already_exists",
        ]
    )
    def test_username_validation_failures(
        self,
        registration_service: UserRegistrationService,
        valid_input: UserRegistrationInput,
        username: str,
        expected_error: str
    ) -> None:
        """验证用户名校验失败场景 (BR-1, S2-S6)"""
        valid_input.username = username

        with pytest.raises(UserRegistrationError) as exc_info:
            registration_service.register(valid_input)

        assert expected_error in str(exc_info.value)

    @pytest.mark.parametrize(
        "username",
        [
            "abc",  # S15: 边界值-用户名最小长度
            "a" * 20,  # S16: 边界值-用户名最大长度
            "test_user_123",  # 正常值
            "UserName",  # 大小写混合
        ],
        ids=[
            "min_length",
            "max_length",
            "normal_value",
            "mixed_case",
        ]
    )
    def test_username_validation_success(
        self,
        registration_service: UserRegistrationService,
        valid_input: UserRegistrationInput,
        username: str
    ) -> None:
        """验证用户名校验成功场景 (BR-1, S15-S16)"""
        valid_input.username = username
        valid_input.email = f"{username}@example.com"  # 确保邮箱唯一

        result = registration_service.register(valid_input)

        assert result.success is True

    # === BR-2: 密码验证测试 ===

    @pytest.mark.parametrize(
        "password,expected_error",
        [
            ("", "密码不能为空"),  # S7: 密码为空
            ("Pass123", "密码长度必须在8-32个字符"),  # S8: 密码过短
            ("A" * 33, "密码长度必须在8-32个字符"),  # S9: 密码过长
            ("passworddd", "密码必须包含字母和数字"),  # S10: 密码纯字母
            ("1234567890", "密码必须包含字母和数字"),  # S11: 密码纯数字
        ],
        ids=[
            "empty_password",
            "too_short",
            "too_long",
            "letters_only",
            "digits_only",
        ]
    )
    def test_password_validation_failures(
        self,
        registration_service: UserRegistrationService,
        valid_input: UserRegistrationInput,
        password: str,
        expected_error: str
    ) -> None:
        """验证密码校验失败场景 (BR-2, S7-S11)"""
        valid_input.password = password

        with pytest.raises(UserRegistrationError) as exc_info:
            registration_service.register(valid_input)

        assert expected_error in str(exc_info.value)

    @pytest.mark.parametrize(
        "password",
        [
            "Pass1234",  # S17: 边界值-密码最小长度
            "A" * 31 + "1",  # S18: 边界值-密码最大长度
            "SecurePass123!",  # 正常值（含特殊字符）
            "MyP4ssw0rd",  # 正常值
        ],
        ids=[
            "min_length",
            "max_length",
            "with_special_char",
            "normal_value",
        ]
    )
    def test_password_validation_success(
        self,
        registration_service: UserRegistrationService,
        valid_input: UserRegistrationInput,
        password: str
    ) -> None:
        """验证密码校验成功场景 (BR-2, S17-S18)"""
        valid_input.password = password

        result = registration_service.register(valid_input)

        assert result.success is True

    # === BR-3: 邮箱验证测试 ===

    @pytest.mark.parametrize(
        "email,expected_error",
        [
            ("", "邮箱不能为空"),  # S12: 邮箱为空
            ("invalid-email", "邮箱格式不正确"),  # S13: 邮箱格式错误-无@
            ("userexample.com", "邮箱格式不正确"),  # 无@符号
            ("user@", "邮箱格式不正确"),  # 无域名
            ("@example.com", "邮箱格式不正确"),  # 无用户名
            ("user@@example.com", "邮箱格式不正确"),  # 多个@
            ("admin@example.com", "邮箱已被注册"),  # S14: 邮箱已存在
        ],
        ids=[
            "empty_email",
            "no_at_symbol",
            "missing_at",
            "missing_domain",
            "missing_username",
            "multiple_at",
            "already_exists",
        ]
    )
    def test_email_validation_failures(
        self,
        registration_service: UserRegistrationService,
        valid_input: UserRegistrationInput,
        email: str,
        expected_error: str
    ) -> None:
        """验证邮箱校验失败场景 (BR-3, S12-S14)"""
        valid_input.email = email

        with pytest.raises(UserRegistrationError) as exc_info:
            registration_service.register(valid_input)

        assert expected_error in str(exc_info.value)

    @pytest.mark.parametrize(
        "email",
        [
            "user@example.com",  # 正常格式
            "user.name@example.com",  # 含点号
            "user+tag@example.com",  # 含加号
            "USER@EXAMPLE.COM",  # 大写
        ],
        ids=[
            "normal_format",
            "with_dot",
            "with_plus",
            "uppercase",
        ]
    )
    def test_email_validation_success(
        self,
        registration_service: UserRegistrationService,
        valid_input: UserRegistrationInput,
        email: str
    ) -> None:
        """验证邮箱校验成功场景 (BR-3)"""
        valid_input.email = email

        result = registration_service.register(valid_input)

        assert result.success is True

    # === BR-4: 注册流程测试 ===

    def test_successful_registration(
        self,
        registration_service: UserRegistrationService,
        valid_input: UserRegistrationInput
    ) -> None:
        """验证正常注册流程 (BR-4, S1)"""
        result = registration_service.register(valid_input)

        assert result.success is True
        assert result.message == "注册成功"
        assert result.user_id is not None
        assert result.user_id.startswith("user_")

    def test_registration_returns_user_id(
        self,
        registration_service: UserRegistrationService,
        valid_input: UserRegistrationInput
    ) -> None:
        """验证注册成功返回用户ID (BR-4)"""
        result = registration_service.register(valid_input)

        assert result.user_id == f"user_{valid_input.username}"


# === 参数化综合测试 ===

class TestUserRegistrationBoundary:
    """用户注册边界值测试套件"""

    @pytest.fixture
    def registration_service(self) -> UserRegistrationService:
        """创建注册服务实例"""
        return UserRegistrationService()

    @pytest.mark.parametrize(
        "username,password,email,should_succeed",
        [
            # 边界值组合测试
            ("abc", "Pass1234", "a@b.co", True),  # 最小边界
            ("a" * 20, "A" * 31 + "1", "user@example.com", True),  # 最大边界
            ("ab", "Pass1234", "user@example.com", False),  # 用户名过短
            ("a" * 21, "Pass1234", "user@example.com", False),  # 用户名过长
            ("abc", "Pass123", "user@example.com", False),  # 密码过短
            ("abc", "A" * 33, "user@example.com", False),  # 密码过长
        ],
        ids=[
            "min_boundary_all",
            "max_boundary_all",
            "username_too_short",
            "username_too_long",
            "password_too_short",
            "password_too_long",
        ]
    )
    def test_boundary_combinations(
        self,
        registration_service: UserRegistrationService,
        username: str,
        password: str,
        email: str,
        should_succeed: bool
    ) -> None:
        """边界值组合测试"""
        input_data = UserRegistrationInput(
            username=username,
            password=password,
            email=email
        )

        if should_succeed:
            result = registration_service.register(input_data)
            assert result.success is True
        else:
            with pytest.raises(UserRegistrationError):
                registration_service.register(input_data)