"""
RAGAS evaluation service for RAG quality assessment
用于 RAG 质量评估的 RAGAS 评估服务

Day 5 Feature: Evaluation & Observability
Day 5 功能： 评估与可观测性

This service integrates RAGAS framework to evaluate RAG system quality:
该服务集成 RAGAS 框架评估 RAG 系统质量：
- Faithfulness: How well the answer is grounded in the context
  忠实度：答案在上下文中的基础程度
- Answer Relevance: How relevant the answer is to the question
  答案相关性：答案与问题的相关程度
- Context Precision: Precision of retrieved context
  上下文精确度：检索上下文的精确度
- Context Recall: Recall of relevant information from context
  上下文召回率：从上下文中检索相关信息的能力
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
import logging

# RAGAS imports (v0.4.x compatible)
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from datasets import Dataset
import pandas as pd

# LangChain imports for evaluation
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from config import settings

# Configure logging
# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """
    Result of a single RAG evaluation
    单次 RAG 评估结果

    Attributes:
        metric_name: Name of the evaluation metric
                    评估指标名称
        score: Score value (0-1)
              分数值（0-1）
        details: Additional details about the evaluation
                关于评估的额外详情
    """
    metric_name: str
    score: float
    details: Optional[str] = None


@dataclass
class RAGEvaluationReport:
    """
    Complete evaluation report for a RAG query
    RAG 查询的完整评估报告

    Day 5: Comprehensive evaluation data class
    Day 5： 综合评估数据类
    """
    # Query information
    # 查询信息
    question: str
    answer: str
    contexts: List[str]

    # Individual metric scores
    # 各指标分数
    faithfulness_score: float = 0.0
    answer_relevance_score: float = 0.0
    context_precision_score: float = 0.0
    context_recall_score: float = 0.0

    # Overall score
    # 总体分数
    overall_score: float = 0.0

    # Metadata
    # 元数据
    evaluation_time_ms: float = 0.0
    timestamp: datetime = None

    # Ground truth for evaluation (optional)
    # 评估用的真实答案（可选）
    ground_truth: Optional[str] = None

    def __post_init__(self):
        """Initialize default values / 初始化默认值"""
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for API response
        转换为字典用于 API 响应
        """
        return {
            "question": self.question,
            "answer": self.answer,
            "contexts": self.contexts,
            "metrics": {
                "faithfulness": self.faithfulness_score,
                "answer_relevance": self.answer_relevance_score,
                "context_precision": self.context_precision_score,
                "context_recall": self.context_recall_score,
            },
            "overall_score": self.overall_score,
            "evaluation_time_ms": self.evaluation_time_ms,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "ground_truth": self.ground_truth,
        }


class EvaluationService:
    """
    Service for evaluating RAG system quality using RAGAS
    使用 RAGAS 评估 RAG 系统质量的服务

    Day 5: Core evaluation functionality
    Day 5： 核心评估功能
    """

    def __init__(self):
        """
        Initialize the evaluation service
        初始化评估服务
        """
        self._llm: Optional[ChatOpenAI] = None
        self._embeddings: Optional[OpenAIEmbeddings] = None
        self._enabled = settings.evaluation_enabled

    def _get_llm(self) -> ChatOpenAI:
        """
        Get or create LLM instance for evaluation
        获取或创建用于评估的 LLM 实例

        Returns:
            ChatOpenAI instance
            ChatOpenAI 实例
        """
        if self._llm is None:
            kwargs = {
                "model": settings.openai_model,
                "api_key": settings.openai_api_key,
                "temperature": 0.0,  # Use deterministic output for evaluation
                # 使用确定性输出进行评估
            }
            if settings.openai_api_base:
                kwargs["base_url"] = settings.openai_api_base
            self._llm = ChatOpenAI(**kwargs)
        return self._llm

    def _get_embeddings(self) -> OpenAIEmbeddings:
        """
        Get or create embeddings instance for evaluation
        获取或创建用于评估的嵌入实例

        Returns:
            OpenAIEmbeddings instance
            OpenAIEmbeddings 实例
        """
        if self._embeddings is None:
            kwargs = {
                "api_key": settings.openai_api_key,
            }
            if settings.openai_api_base:
                kwargs["base_url"] = settings.openai_api_base
            self._embeddings = OpenAIEmbeddings(**kwargs)
        return self._embeddings

    async def evaluate_single(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: Optional[str] = None
    ) -> RAGEvaluationReport:
        """
        Evaluate a single RAG query-response pair
        评估单个 RAG 查询-响应对

        Args:
            question: User's question
                     用户的问题
            answer: Generated answer
                   生成的答案
            contexts: Retrieved context documents
                     检索的上下文文档
            ground_truth: Expected answer (optional, for context_recall)
                         期望答案（可选，用于 context_recall）
        Returns:
            Evaluation report with all metrics
            包含所有指标的评估报告
        """
        if not self._enabled:
            logger.warning("Evaluation is disabled, returning empty report")
            # 警告：评估已禁用，返回空报告
            return RAGEvaluationReport(
                question=question,
                answer=answer,
                contexts=contexts,
                ground_truth=ground_truth,
            )

        start_time = datetime.now()

        try:
            # Prepare data for RAGAS v0.4.x (new column names)
            # 为 RAGAS v0.4.x 准备数据（新列名）
            data = {
                "user_input": [question],
                "response": [answer],
                "retrieved_contexts": [contexts],
            }

            # Add reference (ground_truth) if available
            # 如果有真实答案则添加 reference
            if ground_truth:
                data["reference"] = [ground_truth]

            # Create dataset
            # 创建数据集
            dataset = Dataset.from_dict(data)

            # Configure metrics based on available data
            # 根据可用数据配置指标
            # Set strictness=1 for compatibility with APIs that don't support n>1
            # 设置 strictness=1 以兼容不支持 n>1 的 API（如通义千问）
            answer_relevancy.strictness = 1

            metrics = [
                faithfulness,
                answer_relevancy,
            ]

            # context_precision and context_recall require reference
            # context_precision 和 context_recall 需要 reference
            if ground_truth:
                metrics.extend([context_precision, context_recall])

            # Run evaluation
            # 运行评估
            llm = self._get_llm()
            embeddings = self._get_embeddings()

            # Wrap LLM and embeddings for ragas v0.4.x
            # 为 ragas v0.4.x 包装 LLM 和 embeddings
            wrapped_llm = LangchainLLMWrapper(llm)
            wrapped_embeddings = LangchainEmbeddingsWrapper(embeddings)

            # RAGAS evaluate function (v0.4.x returns EvaluationResult)
            # RAGAS 评估函数（v0.4.x 返回 EvaluationResult）
            result = evaluate(
                dataset,
                metrics=metrics,
                llm=wrapped_llm,
                embeddings=wrapped_embeddings,
            )

            # Extract scores from EvaluationResult (v0.4.x API)
            # 从 EvaluationResult 提取分数（v0.4.x API）
            df = result.to_pandas()
            logger.info(f"RAGAS result columns: {df.columns.tolist() if df is not None else 'None'}")
            logger.info(f"RAGAS result data: {df.to_dict() if df is not None else 'None'}")

            if df is not None and len(df) > 0:
                # Get first row scores (single evaluation)
                # 获取第一行分数（单次评估）
                row = df.iloc[0]

                # Helper function to safely extract score (handle NaN)
                # 辅助函数：安全提取分数（处理 NaN）
                def get_score(row, col_name, default=0.0):
                    val = row.get(col_name, default)
                    if val is None or (isinstance(val, float) and pd.isna(val)):
                        return default
                    return float(val)

                faithfulness_score = get_score(row, "faithfulness")
                answer_relevance_score = get_score(row, "answer_relevancy")
                context_precision_score = get_score(row, "context_precision")
                context_recall_score = get_score(row, "context_recall") if ground_truth else 0.0

                logger.info(f"Extracted scores - faithfulness: {faithfulness_score}, answer_relevancy: {answer_relevance_score}, context_precision: {context_precision_score}, context_recall: {context_recall_score}")
            else:
                # Fallback to zero scores
                # 回退到零分
                faithfulness_score = 0.0
                answer_relevance_score = 0.0
                context_precision_score = 0.0
                context_recall_score = 0.0

            # Calculate overall score (weighted average)
            # 计算总体分数（加权平均）
            if ground_truth:
                overall_score = (
                    faithfulness_score * 0.3 +
                    answer_relevance_score * 0.3 +
                    context_precision_score * 0.2 +
                    context_recall_score * 0.2
                )
            else:
                overall_score = (
                    faithfulness_score * 0.4 +
                    answer_relevance_score * 0.4 +
                    context_precision_score * 0.2
                )

            end_time = datetime.now()
            evaluation_time_ms = (end_time - start_time).total_seconds() * 1000

            return RAGEvaluationReport(
                question=question,
                answer=answer,
                contexts=contexts,
                faithfulness_score=faithfulness_score,
                answer_relevance_score=answer_relevance_score,
                context_precision_score=context_precision_score,
                context_recall_score=context_recall_score,
                overall_score=overall_score,
                evaluation_time_ms=evaluation_time_ms,
                timestamp=end_time,
                ground_truth=ground_truth,
            )

        except Exception as e:
            logger.error(f"Evaluation failed: {e}", exc_info=True)
            # 错误：评估失败
            end_time = datetime.now()
            evaluation_time_ms = (end_time - start_time).total_seconds() * 1000

            return RAGEvaluationReport(
                question=question,
                answer=answer,
                contexts=contexts,
                evaluation_time_ms=evaluation_time_ms,
                ground_truth=ground_truth,
            )

    async def evaluate_batch(
        self,
        questions: List[str],
        answers: List[str],
        contexts_list: List[List[str]],
        ground_truths: Optional[List[str]] = None
    ) -> List[RAGEvaluationReport]:
        """
        Evaluate multiple RAG query-response pairs
        评估多个 RAG 查询-响应对

        Args:
            questions: List of user questions
                      用户问题列表
            answers: List of generated answers
                    生成的答案列表
            contexts_list: List of retrieved contexts for each query
                          每个查询的检索上下文列表
            ground_truths: List of expected answers (optional)
                          期望答案列表（可选）
        Returns:
            List of evaluation reports
            评估报告列表
        """
        if not self._enabled:
            logger.warning("Evaluation is disabled")
            # 警告：评估已禁用
            return []

        reports = []
        ground_truths = ground_truths or [None] * len(questions)

        for i, (q, a, ctx) in enumerate(zip(questions, answers, contexts_list)):
            gt = ground_truths[i] if i < len(ground_truths) else None
            report = await self.evaluate_single(q, a, ctx, gt)
            reports.append(report)

        return reports

    def get_metric_explanation(self, metric_name: str) -> str:
        """
        Get explanation for a metric
        获取指标说明

        Args:
            metric_name: Name of the metric
                        指标名称
        Returns:
            Explanation string
            说明字符串
        """
        explanations = {
            "faithfulness": (
                "Measures how well the answer is grounded in the retrieved context. "
                "A high score means the answer contains only information from the context. "
                "衡量答案在检索上下文中的基础程度。"
                "高分意味着答案只包含上下文中的信息。"
            ),
            "answer_relevance": (
                "Measures how relevant the answer is to the question. "
                "A high score means the answer directly addresses the question. "
                "衡量答案与问题的相关程度。"
                "高分意味着答案直接解决了问题。"
            ),
            "context_precision": (
                "Measures the precision of retrieved context. "
                "A high score means most retrieved chunks are relevant. "
                "衡量检索上下文的精确度。"
                "高分意味着大多数检索的分块都是相关的。"
            ),
            "context_recall": (
                "Measures whether all relevant information was retrieved. "
                "Requires ground truth for calculation. "
                "衡量是否检索了所有相关信息。"
                "需要真实答案进行计算。"
            ),
        }
        return explanations.get(metric_name, "Unknown metric / 未知指标")

    @property
    def is_enabled(self) -> bool:
        """Check if evaluation is enabled / 检查评估是否启用"""
        return self._enabled


# Global evaluation service instance
# 全局评估服务实例
evaluation_service = EvaluationService()
