# 用户注册功能 BDD 规则文档

## 功能概述
用户注册功能允许新用户通过填写用户名、密码、邮箱来创建账户。

## 验证规则

### 用户名验证规则
| 规则编号 | 规则描述 | 验证条件 |
|---------|---------|---------|
| U001 | 用户名必填 | 用户名不能为空 |
| U002 | 用户名长度限制 | 长度在 3-20 个字符之间 |
| U003 | 用户名格式 | 只能包含字母、数字和下划线 |
| U004 | 用户名唯一性 | 用户名不能已被注册 |

### 密码验证规则
| 规则编号 | 规则描述 | 验证条件 |
|---------|---------|---------|
| P001 | 密码必填 | 密码不能为空 |
| P002 | 密码最小长度 | 至少 8 个字符 |
| P003 | 密码复杂度 | 必须包含大小写字母和数字 |
| P004 | 密码确认 | 两次输入的密码必须一致 |

### 邮箱验证规则
| 规则编号 | 规则描述 | 验证条件 |
|---------|---------|---------|
| E001 | 邮箱必填 | 邮箱不能为空 |
| E002 | 邮箱格式 | 必须符合标准邮箱格式 |
| E003 | 邮箱唯一性 | 邮箱不能已被注册 |

## BDD 测试场景

### 场景1: 成功注册
```gherkin
Feature: 用户注册

  Scenario: 用户使用有效信息成功注册
    Given 用户访问注册页面
    When 用户输入有效的用户名 "testuser"
    And 用户输入有效的密码 "Password123"
    And 用户确认密码 "Password123"
    And 用户输入有效的邮箱 "test@example.com"
    And 用户点击注册按钮
    Then 用户注册成功
    And 系统显示注册成功消息
```

### 场景2: 用户名验证失败
```gherkin
  Scenario Outline: 用户名验证失败
    Given 用户访问注册页面
    When 用户输入用户名 "<username>"
    And 用户输入有效的密码 "Password123"
    And 用户确认密码 "Password123"
    And 用户输入有效的邮箱 "test@example.com"
    And 用户点击注册按钮
    Then 注册失败
    And 显示错误消息 "<error_message>"

    Examples:
      | username | error_message |
      | "" | 用户名不能为空 |
      | "ab" | 用户名长度必须在3-20个字符之间 |
      | "a" * 21 | 用户名长度必须在3-20个字符之间 |
      | "test@user" | 用户名只能包含字母、数字和下划线 |
      | "test user" | 用户名只能包含字母、数字和下划线 |
```

### 场景3: 密码验证失败
```gherkin
  Scenario Outline: 密码验证失败
    Given 用户访问注册页面
    When 用户输入有效的用户名 "testuser"
    And 用户输入密码 "<password>"
    And 用户确认密码 "<confirm_password>"
    And 用户输入有效的邮箱 "test@example.com"
    And 用户点击注册按钮
    Then 注册失败
    And 显示错误消息 "<error_message>"

    Examples:
      | password | confirm_password | error_message |
      | "" | "" | 密码不能为空 |
      | "Pass1" | "Pass1" | 密码长度至少为8个字符 |
      | "password" | "password" | 密码必须包含大小写字母和数字 |
      | "PASSWORD1" | "PASSWORD1" | 密码必须包含大小写字母和数字 |
      | "Password" | "Password" | 密码必须包含大小写字母和数字 |
      | "Password123" | "Password456" | 两次输入的密码不一致 |
```

### 场景4: 邮箱验证失败
```gherkin
  Scenario Outline: 邮箱验证失败
    Given 用户访问注册页面
    When 用户输入有效的用户名 "testuser"
    And 用户输入有效的密码 "Password123"
    And 用户确认密码 "Password123"
    And 用户输入邮箱 "<email>"
    And 用户点击注册按钮
    Then 注册失败
    And 显示错误消息 "<error_message>"

    Examples:
      | email | error_message |
      | "" | 邮箱不能为空 |
      | "invalid" | 邮箱格式不正确 |
      | "test@" | 邮箱格式不正确 |
      | "@example.com" | 邮箱格式不正确 |
      | "test@.com" | 邮箱格式不正确 |
```

### 场景5: 用户名已存在
```gherkin
  Scenario: 用户名已被注册
    Given 数据库中已存在用户名 "existinguser"
    And 用户访问注册页面
    When 用户输入用户名 "existinguser"
    And 用户输入有效的密码 "Password123"
    And 用户确认密码 "Password123"
    And 用户输入有效的邮箱 "new@example.com"
    And 用户点击注册按钮
    Then 注册失败
    And 显示错误消息 "用户名已被注册"
```

### 场景6: 邮箱已存在
```gherkin
  Scenario: 邮箱已被注册
    Given 数据库中已存在邮箱 "existing@example.com"
    And 用户访问注册页面
    When 用户输入有效的用户名 "newuser"
    And 用户输入有效的密码 "Password123"
    And 用户确认密码 "Password123"
    And 用户输入邮箱 "existing@example.com"
    And 用户点击注册按钮
    Then 注册失败
    And 显示错误消息 "邮箱已被注册"
```