"""Coverage analysis pipeline.

This module orchestrates the end-to-end coverage generation process:
1. Retrieve script from database (metadata only - text is passed through)
2. Prepare and chunk text if needed
3. Send to LLM with appropriate prompts (Moonshot primary, Claude fallback)
4. Parse and validate the response
5. Save results to database
6. Handle errors and retries

Privacy Note: Script text is held in memory only during analysis and never persisted.
"""
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import CoverageReport, ScriptMetadata, ReportStatus, Recommendation
from app.services.llm_client import (
    get_moonshot_client, 
    get_claude_client,
    MoonshotClient, 
    ClaudeClient,
    LLMError, 
    LLMContentModerationError
)
from app.services.prompts import build_full_prompt, TV_PILOT_SYSTEM_CONTEXT


class AnalysisError(Exception):
    """Raised when analysis pipeline fails."""
    pass


class AnalysisPipeline:
    """Pipeline for generating TV pilot coverage reports.
    
    This class handles the full analysis workflow from script text to
    structured coverage report. Uses Moonshot as primary LLM with
    Claude as fallback for content moderation rejections.
    """
    
    def __init__(
        self, 
        moonshot_client: Optional[MoonshotClient] = None,
        claude_client: Optional[ClaudeClient] = None
    ):
        """Initialize the pipeline.
        
        Args:
            moonshot_client: Optional MoonshotClient instance. If None, uses singleton.
            claude_client: Optional ClaudeClient instance. If None, uses singleton.
        """
        self._moonshot_client = moonshot_client
        self._claude_client = claude_client
    
    @property
    def moonshot_client(self) -> MoonshotClient:
        """Lazy-load the Moonshot client."""
        if self._moonshot_client is None:
            self._moonshot_client = get_moonshot_client()
        return self._moonshot_client
    
    @property
    def claude_client(self) -> ClaudeClient:
        """Lazy-load the Claude client."""
        if self._claude_client is None:
            self._claude_client = get_claude_client()
        return self._claude_client
    
    async def analyze_script(
        self,
        script_text: str,
        report_id: str,
        script_id: str,
        genre: Optional[str] = None,
        comps: Optional[List[str]] = None,
        analysis_depth: str = "standard",
        db: Optional[AsyncSession] = None
    ) -> Tuple[Dict[str, Any], str]:
        """Run full coverage analysis on a script.
        
        This is the main entry point for analysis. It handles:
        - Progress updates via database
        - LLM communication (Moonshot primary, Claude fallback)
        - Response parsing and validation
        - Result storage
        
        Args:
            script_text: Full text of the screenplay
            report_id: UUID of the coverage report record
            script_id: UUID of the script metadata record
            genre: Optional genre for context
            comps: Optional comparable series
            analysis_depth: 'quick', 'standard', or 'deep'
            db: Database session for updates
            
        Returns:
            Tuple of (analysis results dictionary, model used string)
            
        Raises:
            AnalysisError: If analysis fails
        """
        start_time = datetime.utcnow()
        
        try:
            # Build the prompt
            prompt = build_full_prompt(depth=analysis_depth, genre=genre)
            
            # Add comps context if provided
            if comps:
                comps_str = ", ".join(comps)
                prompt = f"""COMPARABLE SERIES: {comps_str}

Use these as reference points for market positioning and quality assessment.

{prompt}"""
            
            # Determine if we need chunking based on script length
            # Kimi K2.5 128k model can handle ~96k tokens (~384k chars)
            # We use a conservative limit to leave room for prompt and response
            CHARS_PER_TOKEN = 4  # Rough estimate
            CONTEXT_LIMIT = 128000
            PROMPT_TOKENS = 4000  # Approximate prompt size
            RESPONSE_TOKENS = 8000  # Expected response
            SAFETY_MARGIN = 10000
            
            available_for_script = (CONTEXT_LIMIT - PROMPT_TOKENS - RESPONSE_TOKENS - SAFETY_MARGIN) * CHARS_PER_TOKEN
            
            use_chunking = len(script_text) > available_for_script
            
            print(f"[Analysis] Script length: {len(script_text)} chars, chunking: {use_chunking}")
            
            # Try Moonshot first, fallback to Claude on content moderation
            model_used = None
            raw_result = None
            
            try:
                if use_chunking:
                    print(f"[Analysis] Using chunking with Moonshot...")
                    raw_result = await self.moonshot_client.analyze_with_chunking(
                        script_text=script_text,
                        prompt=prompt,
                        model=MoonshotClient.MODEL_KIMI_K2_5
                    )
                else:
                    print(f"[Analysis] Sending to Moonshot...")
                    raw_result = await self.moonshot_client.analyze_script(
                        script_text=script_text,
                        prompt=prompt,
                        model=MoonshotClient.MODEL_KIMI_K2_5,
                        expect_json=True
                    )
                model_used = "moonshot-v1-128k"
                print(f"[Analysis] Moonshot response received")
                
            except LLMContentModerationError as e:
                # Moonshot rejected content - fallback to Claude
                print(f"[Analysis] Moonshot rejected content (moderation): {str(e)}")
                print("[Analysis] Falling back to Claude...")
                
                try:
                    if use_chunking:
                        raw_result = await self.claude_client.analyze_with_chunking(
                            script_text=script_text,
                            prompt=prompt,
                            model=ClaudeClient.MODEL_CLAUDE_SONNET
                        )
                    else:
                        raw_result = await self.claude_client.analyze_script(
                            script_text=script_text,
                            prompt=prompt,
                            model=ClaudeClient.MODEL_CLAUDE_SONNET,
                            expect_json=True
                        )
                    model_used = ClaudeClient.MODEL_CLAUDE_SONNET
                    print("[Analysis] Claude fallback completed")
                    
                except LLMError as claude_error:
                    raise AnalysisError(f"Both Moonshot and Claude failed. Claude error: {str(claude_error)}")
            
            except LLMError as e:
                # Other Moonshot errors - don't fallback, just raise
                raise AnalysisError(f"Moonshot analysis failed: {str(e)}")
            
            if raw_result is None or model_used is None:
                raise AnalysisError("Analysis returned no results")
            
            print(f"[Analysis] Parsing results...")
            # Parse and validate the result
            parsed_result = self._parse_analysis_result(raw_result)
            
            # Add model_used to the result for tracking
            parsed_result["_model_used"] = model_used
            
            # Calculate processing time
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()
            
            print(f"[Analysis] Completed in {processing_time:.1f}s using {model_used}")
            
            return parsed_result, model_used
            
        except AnalysisError:
            raise
        except Exception as e:
            print(f"[Analysis] Unexpected error: {type(e).__name__}: {e}")
            raise AnalysisError(f"Analysis pipeline failed: {str(e)}")
    
    def _parse_analysis_result(self, raw_result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and validate the LLM response into a structured format.
        
        Args:
            raw_result: Raw JSON response from LLM
            
        Returns:
            Cleaned and validated result dictionary
            
        Raises:
            AnalysisError: If parsing or validation fails
        """
        try:
            # Ensure required top-level fields exist
            required_fields = ["logline", "synopsis", "overall_comments", "strengths", 
                             "weaknesses", "subscores", "total_score", "recommendation"]
            
            for field in required_fields:
                if field not in raw_result:
                    print(f"Warning: Missing field '{field}' in analysis result")
                    if field in ["strengths", "weaknesses"]:
                        raw_result[field] = []
                    elif field == "subscores":
                        raw_result[field] = {}
                    elif field == "total_score":
                        raw_result[field] = 0
                    else:
                        raw_result[field] = ""
            
            # Validate subscores
            subscores = raw_result.get("subscores", {})
            validated_subscores = {}
            
            # Map various field names to standard categories
            score_mapping = {
                "concept": ["concept", "premise", "idea", "hook"],
                "character": ["character", "characters", "protagonist", "ensemble"],
                "structure": ["structure", "pacing", "plot", "narrative"],
                "dialogue": ["dialogue", "writing", "voice", "execution"],
                "market": ["market", "viability", "commercial", "audience", "timeliness"]
            }
            
            for standard_key, possible_keys in score_mapping.items():
                found = False
                for key in possible_keys:
                    if key in subscores:
                        score_data = subscores[key]
                        if isinstance(score_data, dict):
                            validated_subscores[standard_key] = {
                                "score": min(10, max(0, int(score_data.get("score", 0)))),
                                "rationale": score_data.get("rationale", score_data.get("note", ""))
                            }
                        else:
                            validated_subscores[standard_key] = {
                                "score": min(10, max(0, int(score_data))),
                                "rationale": ""
                            }
                        found = True
                        break
                
                if not found:
                    validated_subscores[standard_key] = {"score": 0, "rationale": ""}
            
            raw_result["subscores"] = validated_subscores
            
            # Recalculate total score from subscores to ensure consistency
            total = sum(s["score"] for s in validated_subscores.values())
            raw_result["total_score"] = total
            
            # Validate recommendation based on score
            rec = raw_result.get("recommendation", "").upper()
            if total >= 38 and "RECOMMEND" not in rec:
                raw_result["recommendation"] = "Recommend"
            elif total >= 25 and "CONSIDER" not in rec and "RECOMMEND" not in rec:
                raw_result["recommendation"] = "Consider"
            elif total < 25 and "PASS" not in rec:
                raw_result["recommendation"] = "Pass"
            
            # Ensure evidence_quotes is a list
            if "evidence_quotes" not in raw_result or not isinstance(raw_result["evidence_quotes"], list):
                raw_result["evidence_quotes"] = []
            
            # Validate evidence quotes format
            validated_quotes = []
            for quote in raw_result["evidence_quotes"]:
                if isinstance(quote, dict):
                    validated_quotes.append({
                        "quote": quote.get("quote", "")[:500],  # Limit length
                        "page": int(quote.get("page", 0)),
                        "context": quote.get("context", "")[:200]
                    })
            raw_result["evidence_quotes"] = validated_quotes
            
            return raw_result
            
        except Exception as e:
            raise AnalysisError(f"Failed to parse analysis result: {str(e)}")
    
    async def save_analysis_results(
        self,
        report_id: str,
        results: Dict[str, Any],
        model_used: str,
        db: AsyncSession
    ) -> CoverageReport:
        """Save analysis results to the database.
        
        Args:
            report_id: UUID of the report to update
            results: Parsed analysis results
            model_used: Name of the LLM model used (for tracking)
            db: Database session
            
        Returns:
            Updated CoverageReport object
            
        Raises:
            AnalysisError: If save fails
        """
        try:
            # Fetch the report
            result = await db.execute(
                select(CoverageReport).where(CoverageReport.id == report_id)
            )
            report = result.scalar_one_or_none()
            
            if not report:
                raise AnalysisError(f"Report {report_id} not found")
            
            # Extract subscores for storage
            subscores_data = results.get("subscores", {})
            subscores_flat = {
                key: data.get("score", 0) 
                for key, data in subscores_data.items()
            }
            
            # Update report fields
            report.status = ReportStatus.COMPLETED
            report.completed_at = datetime.utcnow()
            
            report.logline = results.get("logline", "")
            report.synopsis = results.get("synopsis", "")
            report.overall_comments = results.get("overall_comments", "")
            
            report.strengths = results.get("strengths", [])
            report.weaknesses = results.get("weaknesses", [])
            
            # Serialize complex objects
            report.character_notes = json.dumps(results.get("character_analysis", {}), indent=2)
            report.structure_analysis = json.dumps(results.get("structure_analysis", {}), indent=2)
            report.market_positioning = json.dumps(results.get("market_positioning", {}), indent=2)
            
            # Scores
            report.subscores = subscores_flat
            report.total_score = results.get("total_score", 0)
            
            # Recommendation
            rec_str = results.get("recommendation", "PASS").upper()
            if "RECOMMEND" in rec_str:
                report.recommendation = Recommendation.RECOMMEND
            elif "CONSIDER" in rec_str:
                report.recommendation = Recommendation.CONSIDER
            else:
                report.recommendation = Recommendation.PASS
            
            # Evidence quotes
            report.evidence_quotes = results.get("evidence_quotes", [])
            
            # Track which model was used (for cost tracking and debugging)
            report.model_used = model_used
            
            await db.commit()
            await db.refresh(report)
            
            return report
            
        except Exception as e:
            await db.rollback()
            raise AnalysisError(f"Failed to save analysis results: {str(e)}")
    
    async def mark_failed(
        self,
        report_id: str,
        error_message: str,
        db: AsyncSession
    ):
        """Mark a report as failed.
        
        Args:
            report_id: UUID of the report
            error_message: Error description
            db: Database session
        """
        try:
            result = await db.execute(
                select(CoverageReport).where(CoverageReport.id == report_id)
            )
            report = result.scalar_one_or_none()
            
            if report:
                report.status = ReportStatus.FAILED
                report.error_message = error_message
                report.completed_at = datetime.utcnow()
                await db.commit()
        except Exception as e:
            await db.rollback()
            print(f"Failed to mark report as failed: {e}")


# Singleton instance
_pipeline: Optional[AnalysisPipeline] = None


def get_analysis_pipeline() -> AnalysisPipeline:
    """Get or create the analysis pipeline singleton.
    
    Returns:
        AnalysisPipeline instance
    """
    global _pipeline
    if _pipeline is None:
        _pipeline = AnalysisPipeline()
    return _pipeline


def reset_pipeline():
    """Reset the singleton pipeline (useful for testing)."""
    global _pipeline
    _pipeline = None


# Convenience function for running full analysis
async def run_coverage_analysis(
    script_text: str,
    report_id: str,
    script_id: str,
    db: AsyncSession,
    genre: Optional[str] = None,
    comps: Optional[List[str]] = None,
    analysis_depth: str = "standard"
) -> CoverageReport:
    """Run complete coverage analysis and save results.
    
    This is a convenience wrapper that handles the full workflow:
    1. Run analysis (Moonshot primary, Claude fallback)
    2. Parse results
    3. Save to database with model tracking
    4. Handle errors
    
    Args:
        script_text: Full script text
        report_id: Report UUID
        script_id: Script UUID
        db: Database session
        genre: Optional genre
        comps: Optional comparable series
        analysis_depth: Analysis depth level
        
    Returns:
        Updated CoverageReport
        
    Raises:
        AnalysisError: If analysis fails
    """
    pipeline = get_analysis_pipeline()
    
    try:
        # Run analysis (with automatic fallback to Claude if needed)
        results, model_used = await pipeline.analyze_script(
            script_text=script_text,
            report_id=report_id,
            script_id=script_id,
            genre=genre,
            comps=comps,
            analysis_depth=analysis_depth,
            db=db
        )
        
        # Save results with model tracking
        report = await pipeline.save_analysis_results(report_id, results, model_used, db)
        
        return report
        
    except Exception as e:
        # Mark as failed
        await pipeline.mark_failed(report_id, str(e), db)
        raise AnalysisError(f"Coverage analysis failed: {str(e)}")