import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_conversation_crud_and_multiturn(client: AsyncClient, sample_geotiff_t1: str, sample_geotiff_t2: str):
    """
    Verifies Section 9 & 39:
    Multi-turn conversation creation, message retrieval, and context linking.
    """
    # 1. Create conversation
    create_res = await client.post("/api/v1/conversations", json={"title": "Multi-turn Urban Analysis"})
    assert create_res.status_code == 201
    conv_id = create_res.json()["conversation_id"]

    # 2. Add message to conversation
    msg_res = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"role": "user", "content": "Analyze this region for land changes."}
    )
    assert msg_res.status_code == 201

    # 3. Retrieve messages
    list_res = await client.get(f"/api/v1/conversations/{conv_id}/messages")
    assert list_res.status_code == 200
    msgs = list_res.json()["messages"]
    assert len(msgs) == 1
    assert msgs[0]["content"] == "Analyze this region for land changes."

    # 4. Chat within the conversation
    chat_res = await client.post(
        "/api/v1/chat",
        json={
            "message": "Focus on urban expansion between 2022 and 2025.",
            "conversation_id": conv_id,
            "imagery_ids": [sample_geotiff_t1, sample_geotiff_t2]
        }
    )
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert chat_data["conversation_id"] == conv_id

    # 5. Check that message history now contains both user and assistant turns
    updated_msgs_res = await client.get(f"/api/v1/conversations/{conv_id}/messages")
    updated_msgs = updated_msgs_res.json()["messages"]
    assert len(updated_msgs) >= 3  # Initial message + turn 2 user message + turn 2 assistant message
