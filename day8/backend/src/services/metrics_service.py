"""
Retrieval metrics service for evaluating search quality
用于评估搜索质量的检索指标服务

Day 5 Feature: Evaluation & Observability
Day 5 功能： 评估与可观测性

This service calculates retrieval metrics:
该服务计算检索指标：
- Recall@K: Proportion of relevant items retrieved
  Recall@K：检索到的相关项目的比例
- Precision@K: Proportion of retrieved items that are relevant
  Precision@K：检索到的项目中相关的比例
- MRR (Mean Reciprocal Rank): Position of first relevant result
  MRR：第一个相关结果的位置
- NDCG (Normalized Discounted Cumulative Gain): Ranking quality
  NDCG：排序质量
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from datetime import datetime
import math
import logging

from config import settings

# Configure logging
# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class RetrievalMetricsResult:
    """
    Result of retrieval metrics calculation
    检索指标计算结果

    Day 5: Data class for retrieval evaluation
    Day 5： 检索评估数据类
    """
    # Query information
    # 查询信息
    query: str
    k: int = 5

    # Core metrics
    # 核心指标
    recall_at_k: float = 0.0
    precision_at_k: float = 0.0
    mrr: float = 0.0
    ndcg_at_k: float = 0.0

    # Additional statistics
    # 额外统计
    total_relevant: int = 0
    retrieved_relevant: int = 0
    total_retrieved: int = 0

    # Metadata
    # 元数据
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for API response
        转换为字典用于 API 响应
        """
        return {
            "query": self.query,
            "k": self.k,
            "metrics": {
                "recall_at_k": self.recall_at_k,
                "precision_at_k": self.precision_at_k,
                "mrr": self.mrr,
                "ndcg_at_k": self.ndcg_at_k,
            },
            "statistics": {
                "total_relevant": self.total_relevant,
                "retrieved_relevant": self.retrieved_relevant,
                "total_retrieved": self.total_retrieved,
            },
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class AggregatedMetrics:
    """
    Aggregated metrics across multiple queries
    多个查询的聚合指标

    Day 5: Aggregate evaluation results
    Day 5： 聚合评估结果
    """
    # Average metrics
    # 平均指标
    avg_recall: float = 0.0
    avg_precision: float = 0.0
    avg_mrr: float = 0.0
    avg_ndcg: float = 0.0

    # Statistics
    # 统计
    total_queries: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary / 转换为字典"""
        return {
            "average_metrics": {
                "recall": self.avg_recall,
                "precision": self.avg_precision,
                "mrr": self.avg_mrr,
                "ndcg": self.avg_ndcg,
            },
            "total_queries": self.total_queries,
            "timestamp": self.timestamp.isoformat(),
        }


class RetrievalMetricsService:
    """
    Service for calculating retrieval quality metrics
    用于计算检索质量指标的服务

    Day 5: Core retrieval evaluation functionality
    Day 5： 核心检索评估功能
    """

    def __init__(self):
        """
        Initialize the metrics service
        初始化指标服务
        """
        self._enabled = settings.evaluation_enabled

    def calculate_recall_at_k(
        self,
        retrieved_ids: List[str],
        relevant_ids: Set[str],
        k: int = 5
    ) -> float:
        """
        Calculate Recall@K: proportion of relevant items retrieved
        计算 Recall@K：检索到的相关项目的比例

        Args:
            retrieved_ids: List of retrieved document IDs in order
                          按顺序检索的文档 ID 列表
            relevant_ids: Set of relevant document IDs
                         相关文档 ID 集合
            k: Number of results to consider
               考虑的结果数量
        Returns:
            Recall@K score (0-1)
            Recall@K 分数（0-1）
        """
        if not relevant_ids:
            return 0.0

        # Take top K results
        # 取前 K 个结果
        top_k = retrieved_ids[:k]

        # Count relevant items in top K
        # 统计前 K 个中的相关项目
        relevant_retrieved = len(set(top_k) & relevant_ids)

        return relevant_retrieved / len(relevant_ids)

    def calculate_precision_at_k(
        self,
        retrieved_ids: List[str],
        relevant_ids: Set[str],
        k: int = 5
    ) -> float:
        """
        Calculate Precision@K: proportion of retrieved items that are relevant
        计算 Precision@K：检索到的项目中相关的比例

        Args:
            retrieved_ids: List of retrieved document IDs in order
                          按顺序检索的文档 ID 列表
            relevant_ids: Set of relevant document IDs
                         相关文档 ID 集合
            k: Number of results to consider
               考虑的结果数量
        Returns:
            Precision@K score (0-1)
            Precision@K 分数（0-1）
        """
        if k == 0:
            return 0.0

        # Take top K results
        # 取前 K 个结果
        top_k = retrieved_ids[:k]

        # Count relevant items in top K
        # 统计前 K 个中的相关项目
        relevant_retrieved = len(set(top_k) & relevant_ids)

        return relevant_retrieved / k

    def calculate_mrr(
        self,
        retrieved_ids: List[str],
        relevant_ids: Set[str]
    ) -> float:
        """
        Calculate Mean Reciprocal Rank: position of first relevant result
        计算平均倒数排名：第一个相关结果的位置

        Args:
            retrieved_ids: List of retrieved document IDs in order
                          按顺序检索的文档 ID 列表
            relevant_ids: Set of relevant document IDs
                         相关文档 ID 集合
        Returns:
            MRR score (0-1)
            MRR 分数（0-1）
        """
        for i, doc_id in enumerate(retrieved_ids):
            if doc_id in relevant_ids:
                # Reciprocal rank (1-indexed)
                # 倒数排名（从 1 开始）
                return 1.0 / (i + 1)

        return 0.0

    def calculate_dcg_at_k(
        self,
        retrieved_ids: List[str],
        relevant_ids: Set[str],
        k: int = 5
    ) -> float:
        """
        Calculate Discounted Cumulative Gain at K
        计算 K 处的折扣累积增益

        DCG = sum(rel_i / log2(i + 1)) for i in 1..K

        Args:
            retrieved_ids: List of retrieved document IDs in order
                          按顺序检索的文档 ID 列表
            relevant_ids: Set of relevant document IDs
                         相关文档 ID 集合
            k: Number of results to consider
               考虑的结果数量
        Returns:
            DCG@K score
            DCG@K 分数
        """
        dcg = 0.0
        for i, doc_id in enumerate(retrieved_ids[:k]):
            if doc_id in relevant_ids:
                # Binary relevance: 1 if relevant, 0 otherwise
                # 二元相关性：相关为 1，否则为 0
                rel = 1.0
                # Discount: log2(i + 2) where i is 0-indexed
                # 折扣：log2(i + 2)，其中 i 是 0 索引
                dcg += rel / math.log2(i + 2)

        return dcg

    def calculate_ndcg_at_k(
        self,
        retrieved_ids: List[str],
        relevant_ids: Set[str],
        k: int = 5
    ) -> float:
        """
        Calculate Normalized Discounted Cumulative Gain at K
        计算 K 处的归一化折扣累积增益

        NDCG = DCG / IDCG

        Args:
            retrieved_ids: List of retrieved document IDs in order
                          按顺序检索的文档 ID 列表
            relevant_ids: Set of relevant document IDs
                         相关文档 ID 集合
            k: Number of results to consider
               考虑的结果数量
        Returns:
            NDCG@K score (0-1)
            NDCG@K 分数（0-1）
        """
        if not relevant_ids:
            return 0.0

        # Calculate DCG
        # 计算 DCG
        dcg = self.calculate_dcg_at_k(retrieved_ids, relevant_ids, k)

        # Calculate ideal DCG (all relevant items at top positions)
        # 计算理想 DCG（所有相关项目在最前面的位置）
        # Create ideal ranking: relevant items first
        # 创建理想排名：相关项目在前
        ideal_ranking = list(relevant_ids)[:k]
        idcg = self.calculate_dcg_at_k(ideal_ranking, relevant_ids, k)

        if idcg == 0:
            return 0.0

        return dcg / idcg

    def evaluate_retrieval(
        self,
        query: str,
        retrieved_ids: List[str],
        relevant_ids: List[str],
        k: int = 5
    ) -> RetrievalMetricsResult:
        """
        Evaluate retrieval quality for a single query
        评估单个查询的检索质量

        Args:
            query: The search query
                   搜索查询
            retrieved_ids: List of retrieved document IDs in order
                          按顺序检索的文档 ID 列表
            relevant_ids: List of relevant document IDs (ground truth)
                         相关文档 ID 列表（真实答案）
            k: Number of results to consider
               考虑的结果数量
        Returns:
            RetrievalMetricsResult with all metrics
            包含所有指标的 RetrievalMetricsResult
        """
        relevant_set = set(relevant_ids)

        # Calculate all metrics
        # 计算所有指标
        recall = self.calculate_recall_at_k(retrieved_ids, relevant_set, k)
        precision = self.calculate_precision_at_k(retrieved_ids, relevant_set, k)
        mrr = self.calculate_mrr(retrieved_ids, relevant_set)
        ndcg = self.calculate_ndcg_at_k(retrieved_ids, relevant_set, k)

        # Count statistics
        # 统计数量
        top_k = retrieved_ids[:k]
        retrieved_relevant = len(set(top_k) & relevant_set)

        return RetrievalMetricsResult(
            query=query,
            k=k,
            recall_at_k=recall,
            precision_at_k=precision,
            mrr=mrr,
            ndcg_at_k=ndcg,
            total_relevant=len(relevant_ids),
            retrieved_relevant=retrieved_relevant,
            total_retrieved=min(k, len(retrieved_ids)),
        )

    def evaluate_batch(
        self,
        queries: List[str],
        retrieved_ids_list: List[List[str]],
        relevant_ids_list: List[List[str]],
        k: int = 5
    ) -> AggregatedMetrics:
        """
        Evaluate retrieval quality across multiple queries
        评估多个查询的检索质量

        Args:
            queries: List of search queries
                    搜索查询列表
            retrieved_ids_list: List of retrieved ID lists for each query
                               每个查询的检索 ID 列表
            relevant_ids_list: List of relevant ID lists for each query
                              每个查询的相关 ID 列表
            k: Number of results to consider
               考虑的结果数量
        Returns:
            AggregatedMetrics with average scores
            包含平均分数的 AggregatedMetrics
        """
        if not queries:
            return AggregatedMetrics()

        recalls = []
        precisions = []
        mrrs = []
        ndcgs = []

        for query, retrieved, relevant in zip(queries, retrieved_ids_list, relevant_ids_list):
            result = self.evaluate_retrieval(query, retrieved, relevant, k)
            recalls.append(result.recall_at_k)
            precisions.append(result.precision_at_k)
            mrrs.append(result.mrr)
            ndcgs.append(result.ndcg_at_k)

        return AggregatedMetrics(
            avg_recall=sum(recalls) / len(recalls) if recalls else 0.0,
            avg_precision=sum(precisions) / len(precisions) if precisions else 0.0,
            avg_mrr=sum(mrrs) / len(mrrs) if mrrs else 0.0,
            avg_ndcg=sum(ndcgs) / len(ndcgs) if ndcgs else 0.0,
            total_queries=len(queries),
        )

    @property
    def is_enabled(self) -> bool:
        """Check if metrics calculation is enabled / 检查指标计算是否启用"""
        return self._enabled


# Global metrics service instance
# 全局指标服务实例
metrics_service = RetrievalMetricsService()
