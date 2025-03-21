import time
from tests.utils import send_websocket_message


def test_convo_history_absent(client):
    # no ws connection, so no convo history available
    response = client.get("/memory/conversation_history")
    json = response.json()
    assert response.status_code == 200
    assert "history" in json
    assert len(json["history"]) == 0


def test_convo_history_update(client):
    message = "It's late! It's late!"

    # send websocket messages
    send_websocket_message({"text": message}, client)

    # check working memory update
    response = client.get("/memory/conversation_history")
    json = response.json()
    assert response.status_code == 200
    assert "history" in json
    assert len(json["history"]) == 2  # mex and reply

    # Human message
    assert json["history"][0]["who"] == "Human"
    assert json["history"][0]["text"] == message
    assert isinstance(json["history"][0]["when"], float)  # timestamp
    
    # Cat message
    assert json["history"][1]["who"] == "AI"
    assert "You did not configure" in json["history"][1]["text"] 
    assert "You did not configure" in json["history"][1]["content"] # TODOV2: remove "content"
    assert "You did not configure" in json["history"][1]["why"]["agent_output"]["output"]
    assert isinstance(json["history"][1]["when"], float)  # timestamp


def test_convo_history_reset(client):
    # send websocket messages
    send_websocket_message({"text": "It's late! It's late!"}, client)

    # delete convo history
    response = client.delete("/memory/conversation_history")
    assert response.status_code == 200

    # check working memory update
    response = client.get("/memory/conversation_history")
    json = response.json()
    assert response.status_code == 200
    assert "history" in json
    assert len(json["history"]) == 0


# TODO: should be tested also with concurrency!
def test_convo_history_by_user(client):
    convos = {
        # user_id: n_messages
        "White Rabbit": 2,
        "Alice": 3,
    }

    # send websocket messages
    for user_id, n_messages in convos.items():
        for m in range(n_messages):
            time.sleep(0.1)
            send_websocket_message(
                {"text": f"Mex n.{m} from {user_id}"}, client, user_id=user_id
            )

    # check working memories
    for user_id, n_messages in convos.items():
        response = client.get(
            "/memory/conversation_history/", headers={"user_id": user_id}
        )
        json = response.json()
        assert response.status_code == 200
        assert "history" in json
        assert len(json["history"]) == n_messages * 2  # mex and reply
        for m_idx, m in enumerate(json["history"]):
            assert "who" in m
            assert "text" in m
            if m_idx % 2 == 0:  # even message
                m_number_from_user = int(m_idx / 2)
                assert m["who"] == "Human"
                assert m["text"] == f"Mex n.{m_number_from_user} from {user_id}"
            else:
                assert m["who"] == "AI"

    # delete White Rabbit convo
    response = client.delete(
        "/memory/conversation_history/", headers={"user_id": "White Rabbit"}
    )
    assert response.status_code == 200

    # check convo deletion per user
    ### White Rabbit convo is empty
    response = client.get(
        "/memory/conversation_history/", headers={"user_id": "White Rabbit"}
    )
    json = response.json()
    assert len(json["history"]) == 0
    ### Alice convo still the same
    response = client.get(
        "/memory/conversation_history/", headers={"user_id": "Alice"}
    )
    json = response.json()
    assert len(json["history"]) == convos["Alice"] * 2
