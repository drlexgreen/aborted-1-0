
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import secrets
import string

app = FastAPI(
    title="ABORTED 1.0",
    description="Backend for the music party game",
    version="1.0.0",
)

# Пока комнаты хранятся в памяти.
# При перезапуске сервера они исчезнут.
rooms = {}

MAX_PLAYERS = 6
MIN_PLAYERS = 2


class PlayerRequest(BaseModel):
    player_name: str


def make_room_code():
    alphabet = string.ascii_uppercase + string.digits
    alphabet = alphabet.replace("0", "").replace("O", "")
    alphabet = alphabet.replace("1", "").replace("I", "")

    while True:
        code = "".join(secrets.choice(alphabet) for _ in range(6))
        if code not in rooms:
            return code


@app.get("/")
def home():
    return FileResponse("index.html")


@app.get("/health")
def health():
    return {"ok": True, "status": "online"}


@app.post("/rooms")
def create_room(request: PlayerRequest):
    player_name = request.player_name.strip()

    if not player_name:
        raise HTTPException(
            status_code=400,
            detail="Enter a player name",
        )

    if len(player_name) > 24:
        raise HTTPException(
            status_code=400,
            detail="Player name must be 24 characters or less",
        )

    code = make_room_code()

    rooms[code] = {
        "room_code": code,
        "status": "waiting",
        "players": [
            {
                "name": player_name,
                "is_host": True,
            }
        ],
        "max_players": MAX_PLAYERS,
        "min_players": MIN_PLAYERS,
    }

    return rooms[code]


@app.post("/rooms/{room_code}/join")
def join_room(room_code: str, request: PlayerRequest):
    code = room_code.strip().upper()
    player_name = request.player_name.strip()

    if not player_name:
        raise HTTPException(
            status_code=400,
            detail="Enter a player name",
        )

    if len(player_name) > 24:
        raise HTTPException(
            status_code=400,
            detail="Player name must be 24 characters or less",
        )

    room = rooms.get(code)

    if room is None:
        raise HTTPException(
            status_code=404,
            detail="Room not found",
        )

    if room["status"] != "waiting":
        raise HTTPException(
            status_code=400,
            detail="This game has already started",
        )

    if len(room["players"]) >= room["max_players"]:
        raise HTTPException(
            status_code=400,
            detail="Room is full",
        )

    if any(
        player["name"].casefold() == player_name.casefold()
        for player in room["players"]
    ):
        raise HTTPException(
            status_code=400,
            detail="This name is already taken in the room",
        )

    room["players"].append({
        "name": player_name,
        "is_host": False,
    })

    return room


@app.get("/rooms/{room_code}")
def get_room(room_code: str):
    code = room_code.strip().upper()
    room = rooms.get(code)

    if room is None:
        raise HTTPException(
            status_code=404,
            detail="Room not found",
        )

    return room
