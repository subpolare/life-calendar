import asyncpg, os, json
from dotenv import load_dotenv
from security import encryption
load_dotenv()

DATABASE_URL       = os.getenv('DATABASE_URL')
DATABASE_PORT      = os.getenv('DATABASE_PORT')
DATABASE_USER      = os.getenv('DATABASE_USER')
DATABASE_PASSWORD  = os.getenv('DATABASE_PASSWORD')

async def get_database_pool():
    return await asyncpg.create_pool(DATABASE_URL)

async def get_or_create_user_key(user_id: int, conn):
    res = await conn.fetchrow('SELECT key FROM users WHERE id = $1;', user_id)
    if res and res['key']:
        key_record = json.loads(res['key'])
        user_key = encryption.decrypt_key(key_record)
        return user_key
    else:
        user_key = encryption.generate_user_key()
        key_record = encryption.encrypt_key(user_key)
        await conn.execute('''
            UPDATE users SET key = $2 WHERE id = $1;
        ''', user_id, json.dumps(key_record))
        return user_key

async def set_birth(user_id: int, birth: str):
    pool = await get_database_pool()
    async with pool.acquire() as conn:
        user_key = await get_or_create_user_key(user_id, conn)
        enc = encryption.encrypt(birth.encode(), user_key)
        await conn.execute('''
            INSERT INTO users(id, birth) VALUES($1, $2)
            ON CONFLICT (id) DO UPDATE SET birth = EXCLUDED.birth;
        ''', user_id, json.dumps(enc))
    await pool.close()

async def set_name(user_id: int, name: str):
    pool = await get_database_pool()
    async with pool.acquire() as conn:
        user_key = await get_or_create_user_key(user_id, conn)
        enc = encryption.encrypt(name.encode(), user_key)
        await conn.execute('UPDATE users SET name = $2 WHERE id = $1;', user_id, json.dumps(enc))
    await pool.close()

async def set_gender(user_id: int, gender: str):
    pool = await get_database_pool()
    async with pool.acquire() as conn:
        user_key = await get_or_create_user_key(user_id, conn)
        enc = encryption.encrypt(gender.encode(), user_key)
        await conn.execute('UPDATE users SET gender = $2 WHERE id = $1;', user_id, json.dumps(enc))
    await pool.close()

async def get_user_data(user_id: int):
    pool = await get_database_pool()
    async with pool.acquire() as conn:
        res = await conn.fetchrow('SELECT name, birth, gender, key FROM users WHERE id = $1;', user_id)
        user_key = encryption.decrypt_key(json.loads(res['key']))
        data = {}
        for k in ['name', 'birth', 'gender']:
            if res[k]:
                data[k] = encryption.decrypt(json.loads(res[k]), user_key).decode()
        return data