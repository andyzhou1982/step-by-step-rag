"""
Request tracing service using OpenTelemetry
使用 OpenTelemetry 的请求追踪服务

Day 5 Feature: Evaluation & Observability
Day 5 功能： 评估与可观测性

This service provides distributed tracing for RAG operations:
该服务为 RAG 操作提供分布式追踪：
- Request tracing with spans
  带 span 的请求追踪
- Performance metrics collection
  性能指标收集
- Structured logging
  结构化日志
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
import time
import uuid
import functools
import logging
import json

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource

import structlog

from config import settings

# Configure standard logging
# 配置标准日志
logging.basicConfig(level=logging.INFO)

# Configure structured logging with structlog
# 使用 structlog 配置结构化日志
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# Get structured logger
# 获取结构化日志器
logger = structlog.get_logger()


@dataclass
class SpanInfo:
    """
    Information about a tracing span
    追踪 span 的信息

    Day 5: Span data class
    Day 5： Span 数据类
    """
    span_id: str
    trace_id: str
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: float = 0.0
    attributes: Dict[str, Any] = field(default_factory=dict)
    status: str = "OK"
    events: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary / 转换为字典"""
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "operation_name": self.operation_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "attributes": self.attributes,
            "status": self.status,
            "events": self.events,
        }


@dataclass
class TraceInfo:
    """
    Information about a complete trace
    完整追踪的信息

    Day 5: Trace data class
    Day 5： Trace 数据类
    """
    trace_id: str
    request_id: str
    operation_type: str  # "query", "upload", "evaluation"
    start_time: datetime
    end_time: Optional[datetime] = None
    total_duration_ms: float = 0.0
    spans: List[SpanInfo] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary / 转换为字典"""
        return {
            "trace_id": self.trace_id,
            "request_id": self.request_id,
            "operation_type": self.operation_type,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_duration_ms": self.total_duration_ms,
            "spans": [s.to_dict() for s in self.spans],
            "metadata": self.metadata,
        }


class TracingService:
    """
    Service for request tracing and performance monitoring
    用于请求追踪和性能监控的服务

    Day 5: Core tracing functionality
    Day 5： 核心追踪功能
    """

    def __init__(self):
        """
        Initialize the tracing service
        初始化追踪服务
        """
        self._enabled = settings.tracing_enabled
        self._tracer: Optional[trace.Tracer] = None
        self._active_traces: Dict[str, TraceInfo] = {}
        self._active_spans: Dict[str, SpanInfo] = {}

        if self._enabled:
            self._setup_tracer()

    def _setup_tracer(self):
        """
        Set up OpenTelemetry tracer
        设置 OpenTelemetry 追踪器
        """
        # Create resource
        # 创建资源
        resource = Resource(attributes={
            "service.name": "step-by-step-rag",
            "service.version": "5.0.0",
            "deployment.environment": "development",
        })

        # Create tracer provider
        # 创建追踪器提供者
        provider = TracerProvider(resource=resource)

        # Add console exporter for development
        # 为开发环境添加控制台导出器
        console_exporter = ConsoleSpanExporter()
        provider.add_span_processor(SimpleSpanProcessor(console_exporter))

        # Set global tracer provider
        # 设置全局追踪器提供者
        trace.set_tracer_provider(provider)

        # Get tracer
        # 获取追踪器
        self._tracer = trace.get_tracer(__name__)

    def start_trace(
        self,
        operation_type: str,
        request_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start a new trace
        开始一个新的追踪

        Args:
            operation_type: Type of operation ("query", "upload", "evaluation")
                           操作类型（"query", "upload", "evaluation"）
            request_id: Optional request ID
                       可选的请求 ID
            metadata: Optional metadata
                     可选的元数据
        Returns:
            Trace ID
            追踪 ID
        """
        trace_id = str(uuid.uuid4())
        request_id = request_id or str(uuid.uuid4())

        trace_info = TraceInfo(
            trace_id=trace_id,
            request_id=request_id,
            operation_type=operation_type,
            start_time=datetime.now(),
            metadata=metadata or {},
        )

        self._active_traces[trace_id] = trace_info

        logger.info(
            "trace_started",
            trace_id=trace_id,
            request_id=request_id,
            operation_type=operation_type,
        )

        return trace_id

    def end_trace(self, trace_id: str) -> Optional[TraceInfo]:
        """
        End a trace
        结束追踪

        Args:
            trace_id: The trace ID to end
                     要结束的追踪 ID
        Returns:
            The completed TraceInfo
            完成的 TraceInfo
        """
        if trace_id not in self._active_traces:
            return None

        trace_info = self._active_traces[trace_id]
        trace_info.end_time = datetime.now()
        trace_info.total_duration_ms = (
            trace_info.end_time - trace_info.start_time
        ).total_seconds() * 1000

        logger.info(
            "trace_completed",
            trace_id=trace_id,
            duration_ms=trace_info.total_duration_ms,
            operation_type=trace_info.operation_type,
        )

        # Remove from active traces
        # 从活动追踪中移除
        del self._active_traces[trace_id]

        return trace_info

    def start_span(
        self,
        trace_id: str,
        operation_name: str,
        attributes: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start a new span within a trace
        在追踪中开始一个新的 span

        Args:
            trace_id: Parent trace ID
                     父追踪 ID
            operation_name: Name of the operation
                           操作名称
            attributes: Optional span attributes
                       可选的 span 属性
        Returns:
            Span ID
            Span ID
        """
        if trace_id not in self._active_traces:
            logger.warning("trace_not_found", trace_id=trace_id)
            return ""

        span_id = str(uuid.uuid4())

        span_info = SpanInfo(
            span_id=span_id,
            trace_id=trace_id,
            operation_name=operation_name,
            start_time=datetime.now(),
            attributes=attributes or {},
        )

        self._active_spans[span_id] = span_info

        logger.debug(
            "span_started",
            span_id=span_id,
            trace_id=trace_id,
            operation_name=operation_name,
        )

        return span_id

    def end_span(
        self,
        span_id: str,
        status: str = "OK",
        events: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[SpanInfo]:
        """
        End a span
        结束 span

        Args:
            span_id: The span ID to end
                    要结束的 span ID
            status: Span status ("OK", "ERROR")
                   Span 状态
            events: Optional events to add
                   可选的要添加的事件
        Returns:
            The completed SpanInfo
            完成的 SpanInfo
        """
        if span_id not in self._active_spans:
            return None

        span_info = self._active_spans[span_id]
        span_info.end_time = datetime.now()
        span_info.duration_ms = (
            span_info.end_time - span_info.start_time
        ).total_seconds() * 1000
        span_info.status = status

        if events:
            span_info.events.extend(events)

        # Add span to trace
        # 将 span 添加到追踪
        if span_info.trace_id in self._active_traces:
            self._active_traces[span_info.trace_id].spans.append(span_info)

        # Remove from active spans
        # 从活动 span 中移除
        del self._active_spans[span_id]

        logger.debug(
            "span_completed",
            span_id=span_id,
            duration_ms=span_info.duration_ms,
            status=status,
        )

        return span_info

    def add_event(self, span_id: str, event_name: str, attributes: Optional[Dict[str, Any]] = None):
        """
        Add an event to a span
        向 span 添加事件

        Args:
            span_id: The span ID
                    Span ID
            event_name: Name of the event
                       事件名称
            attributes: Optional event attributes
                       可选的事件属性
        """
        if span_id not in self._active_spans:
            return

        event = {
            "name": event_name,
            "timestamp": datetime.now().isoformat(),
            "attributes": attributes or {},
        }

        self._active_spans[span_id].events.append(event)

    def get_trace(self, trace_id: str) -> Optional[TraceInfo]:
        """
        Get trace information
        获取追踪信息

        Args:
            trace_id: The trace ID
                     追踪 ID
        Returns:
            TraceInfo if found
            如果找到则返回 TraceInfo
        """
        return self._active_traces.get(trace_id)

    @property
    def is_enabled(self) -> bool:
        """Check if tracing is enabled / 检查追踪是否启用"""
        return self._enabled

    def traced(
        self,
        operation_name: Optional[str] = None,
        operation_type: str = "operation"
    ):
        """
        Decorator for tracing functions
        用于追踪函数的装饰器

        Day 5: Decorator for automatic tracing
        Day 5： 自动追踪的装饰器

        Args:
            operation_name: Name of the operation (defaults to function name)
                           操作名称（默认为函数名）
            operation_type: Type of operation
                           操作类型
        """
        def decorator(func: Callable):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                if not self._enabled:
                    return await func(*args, **kwargs)

                op_name = operation_name or func.__name__
                trace_id = self.start_trace(operation_type)
                span_id = self.start_span(trace_id, op_name)

                try:
                    result = await func(*args, **kwargs)
                    self.end_span(span_id, status="OK")
                    self.end_trace(trace_id)
                    return result
                except Exception as e:
                    self.add_event(span_id, "exception", {
                        "type": type(e).__name__,
                        "message": str(e),
                    })
                    self.end_span(span_id, status="ERROR")
                    self.end_trace(trace_id)
                    raise

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                if not self._enabled:
                    return func(*args, **kwargs)

                op_name = operation_name or func.__name__
                trace_id = self.start_trace(operation_type)
                span_id = self.start_span(trace_id, op_name)

                try:
                    result = func(*args, **kwargs)
                    self.end_span(span_id, status="OK")
                    self.end_trace(trace_id)
                    return result
                except Exception as e:
                    self.add_event(span_id, "exception", {
                        "type": type(e).__name__,
                        "message": str(e),
                    })
                    self.end_span(span_id, status="ERROR")
                    self.end_trace(trace_id)
                    raise

            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper

        return decorator


# Global tracing service instance
# 全局追踪服务实例
tracing_service = TracingService()
