"""
Content filtering service for input validation and output sanitization
输入验证和输出净化的内容过滤服务

Day 6: Security & Governance
Day 6： 安全与治理
"""

import re
from typing import Optional, List, Tuple, Dict
from dataclasses import dataclass
from enum import Enum

from config import settings


class FilterResult(Enum):
    """
    Result of content filtering
    内容过滤结果

    Day 6: New enum for filter results
    Day 6： 过滤结果的新枚举
    """
    SAFE = "safe"
    WARNING = "warning"
    BLOCKED = "blocked"


@dataclass
class FilterCheckResult:
    """
    Result of a single filter check
    单个过滤器检查的结果

    Day 6: New model for filter check result
    Day 6： 过滤器检查结果的新模型
    """
    result: FilterResult
    matched_pattern: Optional[str] = None
    matched_content: Optional[str] = None
    message: Optional[str] = None


@dataclass
class ContentFilterResponse:
    """
    Response from content filtering
    内容过滤的响应

    Day 6: New model for filter response
    Day 6： 过滤器响应的新模型
    """
    is_safe: bool
    original_content: str
    filtered_content: str
    filter_results: List[FilterCheckResult]
    warnings: List[str]
    blocked_reasons: List[str]


class ContentFilterService:
    """
    Service for filtering and validating content
    过滤和验证内容的服务

    Day 6: New service for content security
    Day 6： 内容安全的新服务

    Features:
    - SQL injection detection
    - XSS detection
    - Sensitive data detection (PII)
    - Profanity/inappropriate content detection
    - Prompt injection detection (for AI inputs)
    """

    def __init__(self):
        # SQL injection patterns
        # SQL 注入模式
        self._sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE)\b)",
            r"(--|\#|\/\*|\*\/)",
            r"(\bOR\b\s+\d+\s*=\s*\d+)",
            r"(\bAND\b\s+\d+\s*=\s*\d+)",
            r"(UNION\s+SELECT)",
            r"(;\s*(SELECT|INSERT|UPDATE|DELETE|DROP))",
        ]

        # XSS patterns
        # XSS 模式
        self._xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"expression\s*\(",
            r"vbscript:",
        ]

        # PII patterns (Personally Identifiable Information)
        # PII 模式（个人身份信息）
        self._pii_patterns = [
            # Email addresses / 邮箱地址
            (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "email"),
            # Phone numbers (US format) / 电话号码（美国格式）
            (r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "phone"),
            # Credit card numbers / 信用卡号
            (r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "credit_card"),
            # Social Security numbers / 社会安全号码
            (r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b", "ssn"),
        ]

        # Prompt injection patterns (for AI inputs)
        # 提示注入模式（用于 AI 输入）
        self._prompt_injection_patterns = [
            r"(?i)ignore\s+(all\s+)?previous\s+instructions",
            r"(?i)disregard\s+(all\s+)?previous",
            r"(?i)system\s*:\s*you\s+are",
            r"(?i)assistant\s*:\s*",
            r"(?i)forget\s+everything",
            r"(?i)new\s+instructions\s*:",
            r"(?i)override\s+(your\s+)?(instructions|programming)",
            r"(?i)pretend\s+(to\s+be|you\s+are)",
            r"(?i)act\s+as\s+(if|a)",
        ]

        # Inappropriate content patterns (basic profanity filter)
        # 不当内容模式（基本脏话过滤器）
        self._inappropriate_patterns = [
            r"(?i)\b(damn|hell|crap)\b",  # Mild / 轻度
            # Add more patterns as needed for your use case
            # 根据您的用例添加更多模式
        ]

        # Compile all regex patterns for efficiency
        # 编译所有正则表达式以提高效率
        self._compiled_sql = [re.compile(p, re.IGNORECASE) for p in self._sql_patterns]
        self._compiled_xss = [re.compile(p, re.IGNORECASE) for p in self._xss_patterns]
        self._compiled_pii = [(re.compile(p[0]), p[1]) for p in self._pii_patterns]
        self._compiled_prompt_injection = [re.compile(p) for p in self._prompt_injection_patterns]
        self._compiled_inappropriate = [re.compile(p) for p in self._inappropriate_patterns]

    def filter_input(
        self,
        content: str,
        check_sql_injection: bool = True,
        check_xss: bool = True,
        check_prompt_injection: bool = True,
        check_pii: bool = False,
        check_inappropriate: bool = False
    ) -> ContentFilterResponse:
        """
        Filter and validate input content
        过滤和验证输入内容

        Args:
            content: Input content to filter
                    要过滤的输入内容
            check_sql_injection: Check for SQL injection
                                检查 SQL 注入
            check_xss: Check for XSS attacks
                      检查 XSS 攻击
            check_prompt_injection: Check for AI prompt injection
                                   检查 AI 提示注入
            check_pii: Check for PII data
                      检查 PII 数据
            check_inappropriate: Check for inappropriate content
                                检查不当内容
        Returns:
            ContentFilterResponse with filtering results
            包含过滤结果的 ContentFilterResponse
        """
        results: List[FilterCheckResult] = []
        warnings: List[str] = []
        blocked_reasons: List[str] = []
        filtered_content = content

        # Check SQL injection
        # 检查 SQL 注入
        if check_sql_injection:
            sql_result = self._check_sql_injection(content)
            results.append(sql_result)
            if sql_result.result == FilterResult.BLOCKED:
                blocked_reasons.append(f"SQL injection detected: {sql_result.message}")
            elif sql_result.result == FilterResult.WARNING:
                warnings.append(f"Potential SQL injection: {sql_result.message}")

        # Check XSS
        # 检查 XSS
        if check_xss:
            xss_result = self._check_xss(content)
            results.append(xss_result)
            if xss_result.result == FilterResult.BLOCKED:
                blocked_reasons.append(f"XSS attack detected: {xss_result.message}")
            elif xss_result.result == FilterResult.WARNING:
                warnings.append(f"Potential XSS: {xss_result.message}")

        # Check prompt injection
        # 检查提示注入
        if check_prompt_injection:
            prompt_result = self._check_prompt_injection(content)
            results.append(prompt_result)
            if prompt_result.result == FilterResult.BLOCKED:
                blocked_reasons.append(f"Prompt injection detected: {prompt_result.message}")
            elif prompt_result.result == FilterResult.WARNING:
                warnings.append(f"Potential prompt injection: {prompt_result.message}")

        # Check PII (warning only, not blocking)
        # 检查 PII（仅警告，不阻止）
        if check_pii:
            pii_result, filtered_content = self._check_and_mask_pii(content)
            results.append(pii_result)
            if pii_result.result == FilterResult.WARNING:
                warnings.append(f"PII detected and masked: {pii_result.message}")

        # Check inappropriate content
        # 检查不当内容
        if check_inappropriate:
            inappropriate_result = self._check_inappropriate(content)
            results.append(inappropriate_result)
            if inappropriate_result.result == FilterResult.WARNING:
                warnings.append(f"Inappropriate content detected: {inappropriate_result.message}")

        is_safe = len(blocked_reasons) == 0

        return ContentFilterResponse(
            is_safe=is_safe,
            original_content=content,
            filtered_content=filtered_content,
            filter_results=results,
            warnings=warnings,
            blocked_reasons=blocked_reasons,
        )

    def filter_output(
        self,
        content: str,
        check_pii: bool = True,
        check_inappropriate: bool = True
    ) -> ContentFilterResponse:
        """
        Filter and sanitize output content
        过滤和净化输出内容

        Args:
            content: Output content to filter
                    要过滤的输出内容
            check_pii: Check and mask PII data
                      检查和遮罩 PII 数据
            check_inappropriate: Check for inappropriate content
                                检查不当内容
        Returns:
            ContentFilterResponse with filtering results
            包含过滤结果的 ContentFilterResponse
        """
        results: List[FilterCheckResult] = []
        warnings: List[str] = []
        blocked_reasons: List[str] = []
        filtered_content = content

        # Check and mask PII in output
        # 检查并遮罩输出中的 PII
        if check_pii:
            pii_result, filtered_content = self._check_and_mask_pii(content)
            results.append(pii_result)
            if pii_result.result == FilterResult.WARNING:
                warnings.append(f"PII masked in output: {pii_result.message}")

        # Check inappropriate content
        # 检查不当内容
        if check_inappropriate:
            inappropriate_result = self._check_inappropriate(filtered_content)
            results.append(inappropriate_result)
            if inappropriate_result.result == FilterResult.WARNING:
                warnings.append(f"Inappropriate content in output: {inappropriate_result.message}")

        return ContentFilterResponse(
            is_safe=True,  # Output is not blocked, only warned
            original_content=content,
            filtered_content=filtered_content,
            filter_results=results,
            warnings=warnings,
            blocked_reasons=blocked_reasons,
        )

    def _check_sql_injection(self, content: str) -> FilterCheckResult:
        """Check for SQL injection patterns
        检查 SQL 注入模式"""
        for pattern in self._compiled_sql:
            match = pattern.search(content)
            if match:
                return FilterCheckResult(
                    result=FilterResult.BLOCKED,
                    matched_pattern=pattern.pattern,
                    matched_content=match.group(),
                    message="SQL injection pattern detected",
                )
        return FilterCheckResult(result=FilterResult.SAFE)

    def _check_xss(self, content: str) -> FilterCheckResult:
        """Check for XSS patterns
        检查 XSS 模式"""
        for pattern in self._compiled_xss:
            match = pattern.search(content)
            if match:
                return FilterCheckResult(
                    result=FilterResult.BLOCKED,
                    matched_pattern=pattern.pattern,
                    matched_content=match.group(),
                    message="XSS pattern detected",
                )
        return FilterCheckResult(result=FilterResult.SAFE)

    def _check_prompt_injection(self, content: str) -> FilterCheckResult:
        """Check for prompt injection patterns
        检查提示注入模式"""
        for pattern in self._compiled_prompt_injection:
            match = pattern.search(content)
            if match:
                return FilterCheckResult(
                    result=FilterResult.WARNING,  # Warning instead of blocking
                    matched_pattern=pattern.pattern,
                    matched_content=match.group(),
                    message="Potential prompt injection detected",
                )
        return FilterCheckResult(result=FilterResult.SAFE)

    def _check_and_mask_pii(self, content: str) -> Tuple[FilterCheckResult, str]:
        """Check for PII and mask it
        检查 PII 并遮罩"""
        detected_types: List[str] = []
        filtered_content = content

        for pattern, pii_type in self._compiled_pii:
            matches = pattern.findall(content)
            if matches:
                detected_types.append(pii_type)
                # Mask the PII
                # 遮罩 PII
                filtered_content = pattern.sub(f"[{pii_type.upper()}_REDACTED]", filtered_content)

        if detected_types:
            return FilterCheckResult(
                result=FilterResult.WARNING,
                matched_content=", ".join(detected_types),
                message=f"PII detected: {', '.join(detected_types)}",
            ), filtered_content

        return FilterCheckResult(result=FilterResult.SAFE), filtered_content

    def _check_inappropriate(self, content: str) -> FilterCheckResult:
        """Check for inappropriate content
        检查不当内容"""
        for pattern in self._compiled_inappropriate:
            match = pattern.search(content)
            if match:
                return FilterCheckResult(
                    result=FilterResult.WARNING,
                    matched_pattern=pattern.pattern,
                    matched_content=match.group(),
                    message="Inappropriate content detected",
                )
        return FilterCheckResult(result=FilterResult.SAFE)

    def sanitize_html(self, content: str) -> str:
        """
        Sanitize HTML content by removing dangerous tags
        通过删除危险标签来净化 HTML 内容

        Args:
            content: HTML content to sanitize
                    要净化的 HTML 内容
        Returns:
            Sanitized content
            净化后的内容
        """
        # Remove script tags
        # 删除 script 标签
        content = re.sub(r"<script[^>]*>.*?</script>", "", content, flags=re.IGNORECASE | re.DOTALL)

        # Remove dangerous attributes
        # 删除危险属性
        content = re.sub(r'\s*on\w+\s*=\s*["\'][^"\']*["\']', "", content, flags=re.IGNORECASE)

        # Remove javascript: URLs
        # 删除 javascript: URL
        content = re.sub(r'javascript\s*:', "", content, flags=re.IGNORECASE)

        return content

    def truncate_content(self, content: str, max_length: int = 10000) -> str:
        """
        Truncate content to a maximum length
        将内容截断到最大长度

        Args:
            content: Content to truncate
                    要截断的内容
            max_length: Maximum allowed length
                       最大允许长度
        Returns:
            Truncated content
            截断后的内容
        """
        if len(content) <= max_length:
            return content
        return content[:max_length] + "...[truncated]"


# Global content filter service instance
# 全局内容过滤器服务实例
content_filter_service = ContentFilterService()
