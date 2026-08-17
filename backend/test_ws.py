"""
Quick WebSocket test to verify LMA connectivity.
"""
import asyncio
import json
import websockets

# ============================================
# REPLACE THESE WITH YOUR ACTUAL VALUES
# ============================================
MEETING_ID = 1  # Get this from Swagger after creating a meeting
LMA_TOKEN = "EOA8Ifn_sERNJ-0NiRWOaj1nlnAz7GgumE4LFepepvc"  # Get this from POST /api/v1/auth/lma-token
# ============================================


async def test_lma_connection():
    uri = f"ws://localhost:8000/ws/lma/{MEETING_ID}?token={LMA_TOKEN}"
    print(f"🔌 Connecting to: {uri}")

    try:
        async with websockets.connect(uri) as ws:
            print("✅ Connected!")

            # Send handshake
            await ws.send(json.dumps({"type": "handshake", "meeting_id": MEETING_ID}))
            response = await ws.recv()
            print(f"📡 Handshake response: {response}")

            # Send a mock transcript chunk
            mock_chunk = {
                "chunk_id": 1,
                "raw_text": "[Speaker 0] Hello, testing the WebSocket connection.",
                "confidence": 0.95,
                "language": "en",
                "start_ms": 1000,
                "end_ms": 4000,
                "reason": "natural_silence"
            }

            print(f"\n📤 Sending chunk {mock_chunk['chunk_id']}...")
            await ws.send(json.dumps(mock_chunk))

            # Wait for ACK
            response = await ws.recv()
            print(f"📥 Received ACK: {response}")

            # Send another chunk
            mock_chunk_2 = {
                "chunk_id": 2,
                "raw_text": "[Speaker 1] Yes, it seems to be working fine.",
                "confidence": 0.92,
                "language": "en",
                "start_ms": 5000,
                "end_ms": 8000,
                "reason": "natural_silence"
            }

            print(f"\n📤 Sending chunk {mock_chunk_2['chunk_id']}...")
            await ws.send(json.dumps(mock_chunk_2))

            response = await ws.recv()
            print(f"📥 Received ACK: {response}")

            print("\n✅ All chunks sent successfully!")

    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ Connection closed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_lma_connection())