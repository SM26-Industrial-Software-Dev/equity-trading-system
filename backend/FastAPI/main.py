from fastapi import FastAPI, Response
from redis import Redis
import jwt
import uuid
import json
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone

app = FastAPI()

redis_port_number = 6379  # Default Redis port
redis_host = 'localhost'  # Redis host address
redis_dictionaries = ["Users", "Accounts", "Tickers", "Positions"]

day_in_sec = 24*60*60  # Number of seconds in a day

secret_key = "mysecretkey"  
algorithm = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_cookie(user_id: uuid):

    payload = {
        "name": str(user_id),
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(seconds=day_in_sec)
    }
    authentication_cookie = jwt.encode(payload, secret_key, algorithm=algorithm)
    return authentication_cookie

# Initialize Redis client
redis_client = Redis(host=redis_host, port=redis_port_number, db=0)

@app.post("/registerUser")
def register_user(username: str, password: str, response: Response):

    # Check if the username already exists in Redis
    if redis_client.hexists(redis_dictionaries[0], username):
        return {"message": "Username already exists."}
    
    user_id = str(uuid.uuid4())

    uuid_account_array = []
    now = datetime.now(timezone.utc).isoformat()
    user_data = {
        "user_id": user_id,
        "password_hash": pwd_context.hash(password),
        "accounts": uuid_account_array,
        "created_at": now,
        "updated_at": now
    }

    redis_client.hset(redis_dictionaries[0], username, json.dumps(user_data))
    
    authentication_cookie = create_cookie(user_id)
    response.set_cookie(
        key="session",
        value=authentication_cookie,
        httponly=True,
        samesite="lax",
        max_age=day_in_sec
    )

    return {"message": "User registered successfully."}

@app.get("/login")
def login_user(username: str, password: str, response: Response):

    raw_user = redis_client.hget(redis_dictionaries[0], username)
    if not raw_user:
        return {"message": "wrong username or password"}

    user_data = json.loads(raw_user)
    if not pwd_context.verify(password, user_data["password_hash"]):
        return {"message": "wrong username or password"}
    
    authentication_cookie = create_cookie(user_data["user_id"])
    response.set_cookie(
        key="session",
        value=authentication_cookie,
        httponly=True,
        samesite="lax",
        max_age=day_in_sec
    )
    return {"message": "login succesful."}

@app.post("/logout")
def logout(response: Response):

    response.delete_cookie(
        key="session",
        httponly=True,
        samesite="lax"
    )

    return {"message": "logged out"}




