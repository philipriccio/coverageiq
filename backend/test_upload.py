"""Test script for upload endpoint."""
import asyncio
import sys
sys.path.append(".")

from httpx import AsyncClient

# Test configuration
BASE_URL = "http://localhost:8000"


async def test_health():
    """Test health endpoint."""
    async with AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print(f"Health check: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        print("✓ Health check passed")


async def test_models():
    """Test models endpoint."""
    async with AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/models")
        print(f"Models endpoint: {response.status_code}")
        data = response.json()
        print(f"Available models: {[m['id'] for m in data['models']]}")
        assert response.status_code == 200
        assert len(data["models"]) > 0
        default_model = [m for m in data["models"] if m.get("default")]
        assert len(default_model) > 0
        assert default_model[0]["id"] == "kimi-k2.5"
        print("✓ Models endpoint passed")


async def test_upload_pdf():
    """Test PDF upload endpoint."""
    # Create a simple test PDF using reportlab
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        import io
        
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        
        # Add title page
        c.setFont("Helvetica-Bold", 24)
        c.drawString(100, 700, "TEST SCRIPT")
        c.setFont("Helvetica", 12)
        c.drawString(100, 650, "Written by Test Author")
        c.drawString(100, 630, "This is a test screenplay for CoverageIQ.")
        c.showPage()
        
        # Add a scene
        c.setFont("Courier-Bold", 12)
        c.drawString(72, 700, "FADE IN:")
        c.drawString(72, 680, "INT. COFFEE SHOP - DAY")
        c.setFont("Courier", 12)
        c.drawString(72, 650, "A cozy coffee shop with warm lighting.")
        c.drawString(72, 635, "JANE (30s) sits at a table, typing on her laptop.")
        c.setFont("Courier-Bold", 12)
        c.drawString(280, 605, "JANE")
        c.setFont("Courier", 12)
        c.drawString(170, 590, "I can't believe this is happening.")
        c.showPage()
        
        c.save()
        buffer.seek(0)
        pdf_content = buffer.read()
        
        print(f"Created test PDF: {len(pdf_content)} bytes")
        
        # Upload the PDF
        async with AsyncClient() as client:
            files = {"file": ("test_script.pdf", pdf_content, "application/pdf")}
            response = await client.post(f"{BASE_URL}/api/scripts/upload", files=files)
            
            print(f"Upload response: {response.status_code}")
            data = response.json()
            print(f"Response data: {data}")
            
            assert response.status_code == 200
            assert "script_id" in data
            assert data["format"] == "pdf"
            print(f"✓ PDF upload passed (script_id: {data['script_id']})")
            return data["script_id"]
            
    except ImportError:
        print("reportlab not installed, skipping PDF test")
        return None


async def test_list_scripts():
    """Test list scripts endpoint."""
    async with AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/scripts/list")
        print(f"List scripts: {response.status_code}")
        data = response.json()
        print(f"Total scripts: {data['total']}")
        print(f"✓ List scripts passed")


async def main():
    """Run all tests."""
    print("="*50)
    print("CoverageIQ Day 2 - Upload & Text Extraction Tests")
    print("="*50)
    
    try:
        await test_health()
        print()
        await test_models()
        print()
        script_id = await test_upload_pdf()
        print()
        await test_list_scripts()
        print()
        
        print("="*50)
        print("All tests passed! ✓")
        print("="*50)
        
        if script_id:
            print(f"\nYou can view the script at: {BASE_URL}/api/scripts/{script_id}")
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
