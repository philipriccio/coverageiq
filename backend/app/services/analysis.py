"""Coverage analysis pipeline."""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CoverageExample, CoverageReport, DomainKnowledge, Recommendation, ReportStatus, ScriptMetadata
from app.services.llm_client import ClaudeClient, LLMError, OpenAIClient, get_claude_client, get_openai_client
from app.services.prompts import build_prompt_context


class AnalysisError(Exception):
    pass


class AnalysisPipeline:
    def __init__(self, openai_client: Optional[OpenAIClient] = None, claude_client: Optional[ClaudeClient] = None):
        self._openai_client = openai_client
        self._claude_client = claude_client

    @property
    def openai_client(self) -> OpenAIClient:
        if self._openai_client is None:
            self._openai_client = get_openai_client()
        return self._openai_client

    @property
    def claude_client(self) -> ClaudeClient:
        if self._claude_client is None:
            self._claude_client = get_claude_client()
        return self._claude_client

    async def _get_prompt_assets(self, genre: Optional[str], db: Optional[AsyncSession]) -> Tuple[List[str], List[str]]:
        if db is None:
            return [], []

        knowledge_result = await db.execute(
            select(DomainKnowledge).where(
                (DomainKnowledge.category == (genre or "").lower()) | (DomainKnowledge.category == "general")
            ).order_by(DomainKnowledge.updated_at.desc())
        )
        knowledge_entries = [row.content for row in knowledge_result.scalars().all()]

        examples_result = await db.execute(
            select(CoverageExample, CoverageReport)
            .join(CoverageReport, CoverageExample.coverage_report_id == CoverageReport.id)
            .where(CoverageExample.is_featured.is_(True))
            .where((CoverageExample.genre == genre) | (CoverageExample.genre.is_(None)))
            .order_by(CoverageExample.created_at.desc())
            .limit(2)
        )
        example_coverages: List[str] = []
        for example, report in examples_result.all():
            example_coverages.append(
                f"Title: {example.script_title}\nRecommendation: {report.recommendation.value if report.recommendation else 'N/A'}\n"
                f"Total Score: {report.total_score or 0}/50\n"
                f"Logline: {report.logline or ''}\n"
                f"Overall Comments: {report.overall_comments or ''}\n"
                f"Strengths: {'; '.join(report.strengths or [])}\n"
                f"Weaknesses: {'; '.join(report.weaknesses or [])}"
            )
        return knowledge_entries, example_coverages

    async def analyze_script(
        self,
        script_text: str,
        report_id: str,
        script_id: str,
        genre: Optional[str] = None,
        comps: Optional[List[str]] = None,
        analysis_depth: str = "standard",
        db: Optional[AsyncSession] = None,
    ) -> Tuple[Dict[str, Any], str]:
        del report_id, script_id
        knowledge_entries, example_coverages = await self._get_prompt_assets(genre, db)
        prompt = build_prompt_context(
            depth=analysis_depth,
            genre=genre,
            comps=comps,
            domain_knowledge_entries=knowledge_entries,
            example_coverages=example_coverages,
        )

        depth_token_limits = {"quick": 4000, "standard": 8000, "deep": 20000}
        max_tokens = depth_token_limits.get(analysis_depth, 8000)

        use_chunking = len(script_text) > ((128000 - 4000 - max_tokens - 10000) * 4)

        try:
            if use_chunking:
                raw_result = await self.openai_client.analyze_with_chunking(
                    script_text=script_text,
                    prompt=prompt,
                    model=OpenAIClient.MODEL_GPT_4_1,
                )
            else:
                raw_result = await self.openai_client.analyze_script(
                    script_text=script_text,
                    prompt=prompt,
                    model=OpenAIClient.MODEL_GPT_4_1,
                    expect_json=True,
                    max_tokens=max_tokens,
                )
            return self._parse_analysis_result(raw_result), OpenAIClient.MODEL_GPT_4_1
        except LLMError as primary_error:
            try:
                fallback_model = ClaudeClient.MODEL_CLAUDE_SONNET
                if use_chunking:
                    raw_result = await self.claude_client.analyze_with_chunking(
                        script_text=script_text,
                        prompt=prompt,
                        model=fallback_model,
                    )
                else:
                    raw_result = await self.claude_client.analyze_script(
                        script_text=script_text,
                        prompt=prompt,
                        model=fallback_model,
                        expect_json=True,
                        max_tokens=max_tokens,
                    )
                return self._parse_analysis_result(raw_result), fallback_model
            except LLMError as fallback_error:
                raise AnalysisError(f"OpenAI failed: {primary_error}. Claude fallback failed: {fallback_error}") from fallback_error

    def _parse_analysis_result(self, raw_result: Dict[str, Any]) -> Dict[str, Any]:
        try:
            required_fields = ["logline", "synopsis", "overall_comments", "strengths", "weaknesses", "subscores", "total_score", "recommendation"]
            for field in required_fields:
                if field not in raw_result:
                    raw_result[field] = [] if field in {"strengths", "weaknesses"} else ({} if field == "subscores" else "")

            subscores = raw_result.get("subscores", {})
            score_mapping = {
                "concept": ["concept", "premise", "idea", "hook"],
                "character": ["character", "characters", "protagonist", "ensemble"],
                "structure": ["structure", "pacing", "plot", "narrative"],
                "dialogue": ["dialogue", "writing", "voice", "execution"],
                "market": ["market", "viability", "commercial", "audience", "timeliness"],
            }
            validated_subscores = {}
            for standard_key, aliases in score_mapping.items():
                matched = None
                for alias in aliases:
                    if alias in subscores:
                        matched = subscores[alias]
                        break
                if isinstance(matched, dict):
                    validated_subscores[standard_key] = {"score": min(10, max(0, int(matched.get("score", 0)))), "rationale": matched.get("rationale", matched.get("note", ""))}
                elif matched is not None:
                    validated_subscores[standard_key] = {"score": min(10, max(0, int(matched))), "rationale": ""}
                else:
                    validated_subscores[standard_key] = {"score": 0, "rationale": ""}

            raw_result["subscores"] = validated_subscores
            raw_result["total_score"] = sum(item["score"] for item in validated_subscores.values())
            total = raw_result["total_score"]
            raw_result["recommendation"] = "Recommend" if total >= 38 else "Consider" if total >= 25 else "Pass"
            raw_result["evidence_quotes"] = [
                {"quote": q.get("quote", "")[:500], "page": int(q.get("page", 0)), "context": q.get("context", "")[:200]}
                for q in raw_result.get("evidence_quotes", [])
                if isinstance(q, dict)
            ]

            mandate_checklist = raw_result.get("mandate_checklist", {})
            checklist_keys = ["canadian_content", "star_role", "intl_copro", "budget_feasible"]
            raw_result["mandate_checklist"] = {
                key: {
                    "result": bool(mandate_checklist.get(key, {}).get("result", False)),
                    "rationale": str(mandate_checklist.get(key, {}).get("rationale", ""))[:300],
                }
                for key in checklist_keys
            }
            return raw_result
        except Exception as exc:
            raise AnalysisError(f"Failed to parse analysis result: {exc}") from exc

    async def save_analysis_results(self, report_id: str, results: Dict[str, Any], model_used: str, db: AsyncSession) -> CoverageReport:
        try:
            result = await db.execute(select(CoverageReport).where(CoverageReport.id == report_id))
            report = result.scalar_one_or_none()
            if not report:
                raise AnalysisError(f"Report {report_id} not found")
            report.status = ReportStatus.COMPLETED
            report.completed_at = datetime.utcnow()
            report.logline = results.get("logline", "")
            report.synopsis = results.get("synopsis", "")
            report.overall_comments = results.get("overall_comments", "")
            report.strengths = results.get("strengths", [])
            report.weaknesses = results.get("weaknesses", [])
            report.character_notes = json.dumps(results.get("character_analysis", {}), indent=2)
            report.structure_analysis = json.dumps(results.get("structure_analysis", {}), indent=2)
            report.market_positioning = json.dumps(results.get("market_positioning", {}), indent=2)
            report.subscores = {key: value.get("score", 0) for key, value in results.get("subscores", {}).items()}
            report.total_score = results.get("total_score", 0)
            rec = results.get("recommendation", "Pass")
            report.recommendation = Recommendation.RECOMMEND if rec == "Recommend" else Recommendation.CONSIDER if rec == "Consider" else Recommendation.PASS
            report.evidence_quotes = results.get("evidence_quotes", [])
            report.mandate_checklist = results.get("mandate_checklist", {})
            report.model_used = model_used
            await db.commit()
            await db.refresh(report)
            return report
        except Exception as exc:
            await db.rollback()
            raise AnalysisError(f"Failed to save analysis results: {exc}") from exc

    async def mark_failed(self, report_id: str, error_message: str, db: AsyncSession):
        result = await db.execute(select(CoverageReport).where(CoverageReport.id == report_id))
        report = result.scalar_one_or_none()
        if report:
            report.status = ReportStatus.FAILED
            report.error_message = error_message
            report.completed_at = datetime.utcnow()
            await db.commit()


_pipeline: Optional[AnalysisPipeline] = None


def get_analysis_pipeline() -> AnalysisPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = AnalysisPipeline()
    return _pipeline


def reset_pipeline():
    global _pipeline
    _pipeline = None


async def run_coverage_analysis(
    script_text: str,
    report_id: str,
    script_id: str,
    db: AsyncSession,
    genre: Optional[str] = None,
    comps: Optional[List[str]] = None,
    analysis_depth: str = "standard",
) -> CoverageReport:
    pipeline = get_analysis_pipeline()
    try:
        results, model_used = await pipeline.analyze_script(
            script_text=script_text,
            report_id=report_id,
            script_id=script_id,
            genre=genre,
            comps=comps,
            analysis_depth=analysis_depth,
            db=db,
        )
        return await pipeline.save_analysis_results(report_id, results, model_used, db)
    except Exception as exc:
        await pipeline.mark_failed(report_id, str(exc), db)
        raise AnalysisError(f"Coverage analysis failed: {exc}") from exc
