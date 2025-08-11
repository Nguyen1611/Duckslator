# test_mongo.py
import asyncio
from db import users_coll

async def test_mongo():
    test_user = {
        "name": "Test User",
        "email": "test@example.com",
        "role": "tester"
    }

    result = await users_coll.insert_one(test_user)
    print(f"Inserted user with ID: {result.inserted_id}")

if __name__ == "__main__":
    asyncio.run(test_mongo())
