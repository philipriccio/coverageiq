"""Test script to verify Day 4 features: Report Generation & UI."""
import asyncio
import json
from datetime import datetime

# Add backend to path
import sys
sys.path.insert(0, '/data/.openclaw/workspace/coverageiq/backend')

from app.models import CoverageReport, ScriptMetadata, ReportStatus, Recommendation
from app.services.pdf_export import get_pdf_exporter
from app.database import AsyncSessionLocal, init_db

# Create alias for compatibility
async_session_maker = AsyncSessionLocal

async def create_test_report():
    """Create a test coverage report with sample data."""
    await init_db()
    
    async with async_session_maker() as db:
        # Create script metadata
        script = ScriptMetadata(
            id="test-script-001",
            user_id="test-user",
            filename_hash="test_hash",
            file_hash="test_file_hash",
            format="pdf",
            title="The Last Frontier",
            author="Alex Writer",
            page_count=58
        )
        
        # Create completed coverage report
        report = CoverageReport(
            id="test-report-001",
            script_id="test-script-001",
            genre="drama",
            comps=["Northern Exposure", "ER"],
            analysis_depth="standard",
            status=ReportStatus.COMPLETED,
            completed_at=datetime.utcnow(),
            
            # Scores
            subscores={
                "concept": 8,
                "character": 9,
                "structure": 7,
                "dialogue": 8,
                "market": 6
            },
            total_score=38,
            recommendation=Recommendation.RECOMMEND,
            
            # Content
            logline="A disgraced surgeon finds redemption working as the only doctor in a remote Alaskan village, where she must navigate harsh wilderness, skeptical locals, and her own troubled past.",
            synopsis="Dr. Maggie Chen, a brilliant surgeon whose career was derailed by a malpractice tragedy, takes a job as the sole physician in Koyukuk, Alaska—a village of 94 people accessible only by air. On her first day, she treats a baby with pneumonia, faces a skeptical village elder, and clashes with the local bush pilot who becomes her unlikely ally. As a dangerous storm cuts off the village, Maggie must perform an emergency appendectomy with limited supplies, proving her worth and beginning her journey toward healing.",
            overall_comments="THE LAST FRONTIER is a compelling medical drama with a strong sense of place and an eminently watchable protagonist. The pilot effectively establishes the series engine—a doctor solving medical mysteries in an isolated setting while navigating community dynamics. The Alaska setting isn't mere backdrop; it's an active character that generates unique story possibilities unavailable to standard hospital shows. Maggie's backstory provides strong emotional stakes without overwhelming the narrative.",
            strengths=[
                "Strong protagonist with clear internal and external conflicts",
                "Unique setting that differentiates from standard medical dramas",
                "Effective ensemble introduction without overcrowding",
                "Solid understanding of medical procedural elements",
                "Series engine is clear: weekly medical cases + ongoing character arcs"
            ],
            weaknesses=[
                "Some dialogue feels on-the-nose, particularly early Maggie scenes",
                "Storm sequence borders on predictable—consider fresher stakes",
                "Villain setup with Sarah feels rushed; could use more nuance",
                "Elijah's arc needs clarification—is he recurring or regular?"
            ],
            character_notes=json.dumps({
                "protagonist": {
                    "name": "Dr. Maggie Chen",
                    "assessment": "Excellent series lead with layers. The malpractice backstory provides guilt and motivation without making her unlikable. Her competence is established immediately through the baby treatment.",
                    "series_runway": "Strong - her redemption arc can span multiple seasons. The 'fish out of water' dynamic gives 2-3 seasons of material, and her evolving relationships with the community provide ongoing story."
                },
                "supporting_cast": {
                    "assessment": "Well-balanced ensemble. Elias has clear potential as love interest/adversary. Walter provides necessary exposition and warmth. Sarah sets up institutional conflict.",
                    "standouts": ["Elias - charismatic, immediately engaging"],
                    "concerns": ["May need more diverse representation in village"]
                },
                "character_dynamics": "The Maggie-Elias friction is classic 'will they/won't they' setup, but grounded in their professional conflict. The medical hierarchy dynamics (Sarah vs. Maggie) need more nuance to avoid feeling contrived."
            }),
            structure_analysis=json.dumps({
                "pilot_type": "Premise pilot - establishes situation and core relationships",
                "act_breaks": "Clear four-act structure with escalating stakes",
                "cold_open": "Strong hook with medical emergency and character introduction",
                "act_one": "Sets up Maggie's arrival and immediate challenge (baby)",
                "act_two": "Deepens relationships, introduces storm complication",
                "act_three": "Medical crisis and climax with appendectomy",
                "tag": "Promise of ongoing dynamics and series potential"
            }),
            market_positioning=json.dumps({
                "genre": "Medical Drama",
                "comparable_series": ["Northern Exposure", "ER", "Virgin River", "The Good Doctor"],
                "target_network": "Prime Video, Apple TV+, or Netflix",
                "target_audience": "Adults 25-54, fans of character-driven procedurals",
                "castability": "Strong female lead opportunity. Elias is a breakout role."
            }),
            evidence_quotes=[
                {"quote": "You gonna be sick, Doc?", "page": 1, "context": "Maggie's first line - establishes her confidence and Elias's vulnerability"},
                {"quote": "There's no hospital. / That's the clinic. You're it.", "page": 2, "context": "Effective world-building that immediately establishes stakes"},
                {"quote": "I flew a thousand miles to be someone's second choice.", "page": 5, "context": "Reveals Maggie's insecurity and the theme of redemption"},
                {"quote": "You're alone, Maggie. Just like everyone else up here.", "page": 12, "context": "Thematic statement that resonates throughout the series"}
            ],
            model_used="kimi-k2.5"
        )
        
        db.add(script)
        db.add(report)
        await db.commit()
        
        print("✅ Test report created successfully")
        print(f"   Report ID: {report.id}")
        print(f"   Total Score: {report.total_score}/50")
        print(f"   Recommendation: {report.recommendation.value}")
        
        return report.id

async def test_pdf_export(report_id: str):
    """Test PDF export functionality."""
    print("\n📄 Testing PDF Export...")
    
    async with async_session_maker() as db:
        from sqlalchemy import select
        result = await db.execute(
            select(CoverageReport).where(CoverageReport.id == report_id)
        )
        report = result.scalar_one()
        
        result = await db.execute(
            select(ScriptMetadata).where(ScriptMetadata.id == report.script_id)
        )
        script = result.scalar_one()
        
        # Prepare report data
        report_data = {
            'script_title': script.title,
            'total_score': report.total_score,
            'recommendation': report.recommendation.value,
            'subscores': report.subscores,
            'logline': report.logline,
            'synopsis': report.synopsis,
            'overall_comments': report.overall_comments,
            'strengths': report.strengths,
            'weaknesses': report.weaknesses,
            'character_notes': report.character_notes,
            'structure_analysis': report.structure_analysis,
            'market_positioning': report.market_positioning,
            'evidence_quotes': report.evidence_quotes
        }
        
        # Export PDF
        exporter = get_pdf_exporter()
        pdf_content = exporter.export_coverage_report(report_data)
        
        # Save to file
        output_path = '/data/.openclaw/workspace/coverageiq/test_output.pdf'
        with open(output_path, 'wb') as f:
            f.write(pdf_content)
        
        print(f"✅ PDF exported successfully: {output_path}")
        print(f"   File size: {len(pdf_content)} bytes")

async def main():
    print("=" * 60)
    print("CoverageIQ Day 4: Report Generation & UI Test")
    print("=" * 60)
    
    # Create test report
    report_id = await create_test_report()
    
    # Test PDF export
    await test_pdf_export(report_id)
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Test Google Docs export (requires OAuth)")
    print("2. Verify frontend displays report correctly")
    print("3. Test end-to-end flow with real analysis")

if __name__ == "__main__":
    asyncio.run(main())
