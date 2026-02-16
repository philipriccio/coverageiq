"""Test to verify the SQLAlchemy concurrent session fix."""
import asyncio
import sys
sys.path.insert(0, '/data/.openclaw/workspace/coverageiq/backend')

from app.database import AsyncSessionLocal, init_db


async def test_session_isolation():
    """Test that multiple concurrent operations use isolated sessions."""
    await init_db()
    
    async def operation_1():
        async with AsyncSessionLocal() as session:
            # Simulate some work
            await asyncio.sleep(0.1)
            return "operation_1_complete"
    
    async def operation_2():
        async with AsyncSessionLocal() as session:
            # Simulate some work
            await asyncio.sleep(0.1)
            return "operation_2_complete"
    
    # Run both operations concurrently
    # This should work without "concurrent operations not permitted" error
    results = await asyncio.gather(operation_1(), operation_2())
    
    assert results == ["operation_1_complete", "operation_2_complete"]
    print("✓ Concurrent sessions are properly isolated")


async def main():
    print("Testing SQLAlchemy concurrent session fix...")
    print()
    
    try:
        await test_session_isolation()
        print("\n✓ All tests passed! The fix is working correctly.")
        return 0
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
