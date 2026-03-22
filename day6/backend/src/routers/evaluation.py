"""
Evaluation API routes for RAG system assessment
用于 RAG 系统评估的评估 API 路由

Day 5 Feature: Evaluation & Observability
Day 5 功能： 评估与可观测性

Endpoints:
- POST /evaluation/rag: Evaluate RAG quality (RAGAS metrics)
- POST /evaluation/retrieval: Evaluate retrieval quality
- POST /evaluation/batch: Batch evaluation
- GET /evaluation/metrics/explanations: Get metric explanations
"""

from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime

from models.schemas import (
    EvaluationRequest,
    EvaluationResponse,
    EvaluationMetrics,
    RetrievalEvaluationRequest,
    RetrievalMetrics,
    BatchEvaluationRequest,
    BatchEvaluationResponse,
    ApiResponse,
)
from services.evaluation_service import evaluation_service
from services.metrics_service import metrics_service
from services.tracing_service import tracing_service

router = APIRouter(prefix="/evaluation", tags=["Evaluation"])


@router.post("/rag", response_model=EvaluationResponse)
async def evaluate_rag(request: EvaluationRequest):
    """
    Evaluate RAG quality using RAGAS metrics
    使用 RAGAS 指标评估 RAG 质量

    Day 5: RAGAS evaluation endpoint
    Day 5： RAGAS 评估端点

    Metrics calculated:
    计算的指标：
    - Faithfulness: How well the answer is grounded in context
      忠实度：答案在上下文中的基础程度
    - Answer Relevance: How relevant the answer is to the question
      答案相关性：答案与问题的相关程度
    - Context Precision: Precision of retrieved context
      上下文精确度：检索上下文的精确度
    - Context Recall: Recall of relevant information (if ground_truth provided)
      上下文召回率：相关信息的召回率（如果提供了真实答案）
    """
    if not evaluation_service.is_enabled:
        raise HTTPException(
            status_code=503,
            detail="Evaluation service is disabled / 评估服务已禁用"
        )

    # Start trace
    # 开始追踪
    trace_id = tracing_service.start_trace(
        operation_type="evaluation",
        metadata={"question_length": len(request.question)}
    )
    span_id = tracing_service.start_span(trace_id, "rag_evaluation")

    try:
        # Run evaluation
        # 运行评估
        report = await evaluation_service.evaluate_single(
            question=request.question,
            answer=request.answer,
            contexts=request.contexts,
            ground_truth=request.ground_truth,
        )

        # End trace
        # 结束追踪
        tracing_service.end_span(span_id, status="OK")
        tracing_service.end_trace(trace_id)

        return EvaluationResponse(
            rag_metrics=EvaluationMetrics(
                faithfulness=report.faithfulness_score,
                answer_relevance=report.answer_relevance_score,
                context_precision=report.context_precision_score,
                context_recall=report.context_recall_score,
                overall_score=report.overall_score,
            ),
            evaluation_time_ms=report.evaluation_time_ms,
            timestamp=report.timestamp,
        )

    except Exception as e:
        tracing_service.add_event(span_id, "error", {"message": str(e)})
        tracing_service.end_span(span_id, status="ERROR")
        tracing_service.end_trace(trace_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retrieval")
async def evaluate_retrieval(request: RetrievalEvaluationRequest):
    """
    Evaluate retrieval quality
    评估检索质量

    Day 5: Retrieval metrics endpoint
    Day 5： 检索指标端点

    Metrics calculated:
    计算的指标：
    - Recall@K: Proportion of relevant items retrieved
      Recall@K：检索到的相关项目的比例
    - Precision@K: Proportion of retrieved items that are relevant
      Precision@K：检索到的项目中相关的比例
    - MRR: Mean Reciprocal Rank
      MRR：平均倒数排名
    - NDCG@K: Normalized Discounted Cumulative Gain
      NDCG@K：归一化折扣累积增益
    """
    if not metrics_service.is_enabled:
        raise HTTPException(
            status_code=503,
            detail="Metrics service is disabled / 指标服务已禁用"
        )

    # Run evaluation
    # 运行评估
    result = metrics_service.evaluate_retrieval(
        query=request.query,
        retrieved_ids=request.retrieved_ids,
        relevant_ids=request.relevant_ids,
        k=request.k,
    )

    return {
        "query": result.query,
        "k": result.k,
        "metrics": RetrievalMetrics(
            recall_at_k=result.recall_at_k,
            precision_at_k=result.precision_at_k,
            mrr=result.mrr,
            ndcg_at_k=result.ndcg_at_k,
        ),
        "statistics": {
            "total_relevant": result.total_relevant,
            "retrieved_relevant": result.retrieved_relevant,
            "total_retrieved": result.total_retrieved,
        },
        "timestamp": result.timestamp.isoformat(),
    }


@router.post("/batch", response_model=BatchEvaluationResponse)
async def evaluate_batch(request: BatchEvaluationRequest):
    """
    Batch evaluate multiple query-response pairs
    批量评估多个查询-响应对

    Day 5: Batch evaluation endpoint
    Day 5： 批量评估端点
    """
    if not evaluation_service.is_enabled:
        raise HTTPException(
            status_code=503,
            detail="Evaluation service is disabled / 评估服务已禁用"
        )

    # Start trace
    # 开始追踪
    trace_id = tracing_service.start_trace(
        operation_type="batch_evaluation",
        metadata={"batch_size": len(request.questions)}
    )
    span_id = tracing_service.start_span(trace_id, "batch_rag_evaluation")

    start_time = datetime.now()

    try:
        # Run batch evaluation
        # 运行批量评估
        reports = await evaluation_service.evaluate_batch(
            questions=request.questions,
            answers=request.answers,
            contexts_list=request.contexts_list,
            ground_truths=request.ground_truths,
        )

        # Convert to response format
        # 转换为响应格式
        results = []
        total_faithfulness = 0.0
        total_relevance = 0.0
        total_precision = 0.0
        total_recall = 0.0
        total_overall = 0.0

        for report in reports:
            results.append(EvaluationResponse(
                rag_metrics=EvaluationMetrics(
                    faithfulness=report.faithfulness_score,
                    answer_relevance=report.answer_relevance_score,
                    context_precision=report.context_precision_score,
                    context_recall=report.context_recall_score,
                    overall_score=report.overall_score,
                ),
                evaluation_time_ms=report.evaluation_time_ms,
                timestamp=report.timestamp,
            ))
            total_faithfulness += report.faithfulness_score
            total_relevance += report.answer_relevance_score
            total_precision += report.context_precision_score
            total_recall += report.context_recall_score
            total_overall += report.overall_score

        # Calculate averages
        # 计算平均值
        count = len(reports)
        average_metrics = EvaluationMetrics(
            faithfulness=total_faithfulness / count if count else 0,
            answer_relevance=total_relevance / count if count else 0,
            context_precision=total_precision / count if count else 0,
            context_recall=total_recall / count if count else 0,
            overall_score=total_overall / count if count else 0,
        )

        end_time = datetime.now()
        total_time_ms = (end_time - start_time).total_seconds() * 1000

        # End trace
        # 结束追踪
        tracing_service.end_span(span_id, status="OK")
        tracing_service.end_trace(trace_id)

        return BatchEvaluationResponse(
            results=results,
            average_metrics=average_metrics,
            total_evaluations=count,
            total_time_ms=total_time_ms,
        )

    except Exception as e:
        tracing_service.add_event(span_id, "error", {"message": str(e)})
        tracing_service.end_span(span_id, status="ERROR")
        tracing_service.end_trace(trace_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/explanations")
async def get_metric_explanations():
    """
    Get explanations for all evaluation metrics
    获取所有评估指标的说明

    Day 5: Metric documentation endpoint
    Day 5： 指标文档端点
    """
    rag_metrics = {
        "faithfulness": evaluation_service.get_metric_explanation("faithfulness"),
        "answer_relevance": evaluation_service.get_metric_explanation("answer_relevance"),
        "context_precision": evaluation_service.get_metric_explanation("context_precision"),
        "context_recall": evaluation_service.get_metric_explanation("context_recall"),
    }

    retrieval_metrics = {
        "recall_at_k": (
            "Measures the proportion of relevant items that were retrieved. "
            "Higher is better. A score of 1.0 means all relevant items were found. "
            "衡量检索到的相关项目的比例。"
            "越高越好。1.0 分表示找到了所有相关项目。"
        ),
        "precision_at_k": (
            "Measures the proportion of retrieved items that are relevant. "
            "Higher is better. A score of 1.0 means all retrieved items are relevant. "
            "衡量检索到的项目中相关的比例。"
            "越高越好。1.0 分表示所有检索到的项目都是相关的。"
        ),
        "mrr": (
            "Mean Reciprocal Rank. Measures the position of the first relevant result. "
            "Higher is better. A score of 1.0 means the first result is relevant. "
            "平均倒数排名。衡量第一个相关结果的位置。"
            "越高越好。1.0 分表示第一个结果是相关的。"
        ),
        "ndcg_at_k": (
            "Normalized Discounted Cumulative Gain. Measures ranking quality considering position. "
            "Higher is better. A score of 1.0 means perfect ranking. "
            "归一化折扣累积增益。考虑位置因素衡量排序质量。"
            "越高越好。1.0 分表示完美排序。"
        ),
    }

    return {
        "rag_metrics": rag_metrics,
        "retrieval_metrics": retrieval_metrics,
    }


@router.get("/health")
async def evaluation_health():
    """
    Check evaluation service health
    检查评估服务健康状态

    Day 5: Health check for evaluation services
    Day 5： 评估服务的健康检查
    """
    return {
        "evaluation_enabled": evaluation_service.is_enabled,
        "metrics_enabled": metrics_service.is_enabled,
        "tracing_enabled": tracing_service.is_enabled,
    }
