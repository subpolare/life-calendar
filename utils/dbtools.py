from typing import Any
import asyncpg, os, json
from dotenv import load_dotenv
from security import encryption
from datetime import date, datetime
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/life')
_pool: asyncpg.Pool | None = None

async def init_pool(min_size: int = 5, max_size: int = 20):
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size        = min_size,
            max_size        = max_size,
            command_timeout = 30,
        )

async def close_pool():
    if _pool:
        await _pool.close()

async def get_database_pool():
    if _pool is None:
        await init_pool()
    return _pool

def _json_serializer(obj: Any) -> Any:
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f'Type {obj.__class__.__name__} is not JSON serializable')

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
    
async def set_name(user_id: int, name: str):
    pool = await get_database_pool()
    async with pool.acquire() as conn:
        user_key = await get_or_create_user_key(user_id, conn)
        enc = encryption.encrypt(name.encode(), user_key)
        await conn.execute('UPDATE users SET name = $2 WHERE id = $1;', user_id, json.dumps(enc))
    
async def set_gender(user_id: int, gender: str):
    pool = await get_database_pool()
    async with pool.acquire() as conn:
        user_key = await get_or_create_user_key(user_id, conn)
        enc = encryption.encrypt(gender.encode(), user_key)
        await conn.execute('UPDATE users SET gender = $2 WHERE id = $1;', user_id, json.dumps(enc))

async def set_empty_event(user_id: int, event: str, first = False):
    pool = await get_database_pool()

    async with pool.acquire() as conn:
        user_key = await get_or_create_user_key(user_id, conn)
        if first:  
            events = []
            await conn.execute('UPDATE users SET data = NULL WHERE id = $1;', user_id)

        else: 
            row = await conn.fetchrow('SELECT data FROM users WHERE id = $1;', user_id)
            if row and row['data']:
                try:
                    stored_enc: dict[str, Any] = json.loads(row['data'])
                    decrypted: str = encryption.decrypt(stored_enc, user_key)
                    events: list[Any] = json.loads(decrypted)
                    if not isinstance(events, list):
                        events = []
                except Exception:
                    events = []
            else:
                events = []

        events.append({event: None})
        plaintext: bytes = json.dumps(events, ensure_ascii = False).encode()
        enc_dict: dict[str, Any] = encryption.encrypt(plaintext, user_key)
        enc_str: str = json.dumps(enc_dict, ensure_ascii = False)
        await conn.execute('INSERT INTO users(id, data) VALUES($1, $2) ON CONFLICT (id) DO UPDATE SET data = EXCLUDED.data;', user_id, enc_str)

async def get_events(user_id: int):
    pool = await get_database_pool()
    async with pool.acquire() as conn:
        user_key = await get_or_create_user_key(user_id, conn)
        row = await conn.fetchrow('SELECT data FROM users WHERE id = $1;', user_id)
        if row and row['data']:
            try:
                stored_enc: dict[str, Any] = json.loads(row['data'])
                decrypted: str = encryption.decrypt(stored_enc, user_key)
                events: list[Any] = json.loads(decrypted)
                if not isinstance(events, list):
                    events = []
            except Exception:
                events = []
        else:
            events = []
        return events

async def set_event(user_id: int, event: str, dates: Any):
    pool = await get_database_pool()
    async with pool.acquire() as conn:
        user_key = await get_or_create_user_key(user_id, conn)
        row = await conn.fetchrow('SELECT data FROM users WHERE id = $1;', user_id)
        if row and row['data']:
            try:
                stored_enc: dict[str, Any] = json.loads(row['data'])
                decrypted: str = encryption.decrypt(stored_enc, user_key)
                events: list[Any] = json.loads(decrypted)
                if not isinstance(events, list):
                    events = []
            except Exception:
                events = []
        else:
            events = []
        events = [item for item in events if list(item.values())[0] is not None]

        if isinstance(dates, tuple):
            value = [d.isoformat() for d in dates]
        else:
            value = [dates.isoformat()]
        events.append({event: value})

        enc = encryption.encrypt(json.dumps(events, default = _json_serializer, ensure_ascii = False).encode(), user_key)
        await conn.execute('INSERT INTO users(id, data) VALUES($1, $2) ON CONFLICT (id) DO UPDATE SET data = EXCLUDED.data;', user_id, json.dumps(enc))
    
async def delete_event(user_id: int, event: str, dates: Any):
    pool = await get_database_pool()
    async with pool.acquire() as conn:
        user_key = await get_or_create_user_key(user_id, conn)
        row = await conn.fetchrow('SELECT data FROM users WHERE id = $1;', user_id)
        if row and row['data']:
            try:
                stored_enc: dict[str, Any] = json.loads(row['data'])
                decrypted: str = encryption.decrypt(stored_enc, user_key)
                events: list[Any] = json.loads(decrypted)
                if not isinstance(events, list):
                    events = []
            except Exception:
                events = []
        else:
            events = []

        def _to_iso_list(src: Any) -> list[str]:
            if src is None:
                return []
            if isinstance(src, (list, tuple)):
                return [d.isoformat() if hasattr(d, 'isoformat') else str(d) for d in src]
            return [src.isoformat() if hasattr(src, 'isoformat') else str(src)]
        target = _to_iso_list(dates)
        events = [
            item for item in events
            if not (
                list(item.keys())[0] == event and
                _to_iso_list(list(item.values())[0]) == target
            )
        ]

        enc = encryption.encrypt(json.dumps(events, default = _json_serializer, ensure_ascii = False).encode(), user_key)
        await conn.execute('INSERT INTO users(id, data) VALUES($1, $2) ON CONFLICT (id) DO UPDATE SET data = EXCLUDED.data;', user_id, json.dumps(enc))

async def get_user_data(user_id: int):
    pool = await get_database_pool()
    async with pool.acquire() as conn:
        res = await conn.fetchrow('SELECT name, birth, gender, key FROM users WHERE id = $1;', user_id)
        if not res or not res['key']:
            return {}
        try:
            user_key = encryption.decrypt_key(json.loads(res['key']))
        except Exception:
            return {}
        data: dict[str, str | None] = {}
        for k in ['name', 'birth', 'gender']:
            if res[k]:
                try:
                    data[k] = encryption.decrypt(json.loads(res[k]), user_key).decode()
                except Exception:
                    data[k] = None
        return data
    
async def set_action(user_id: int, gender: str):
    pool = await get_database_pool()
    async with pool.acquire() as conn:
        user_key = await get_or_create_user_key(user_id, conn)
        enc = encryption.encrypt(gender.encode(), user_key)
        await conn.execute('UPDATE users SET action = $2 WHERE id = $1;', user_id, json.dumps(enc))
    
async def clear_action(user_id: int):
    pool = await get_database_pool()
    async with pool.acquire() as conn:
        await conn.execute('UPDATE users SET action = NULL WHERE id = $1;', user_id)
    
async def get_action(user_id: int):
    pool = await get_database_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow('SELECT action, key FROM users WHERE id = $1;', user_id)
        user_key = encryption.decrypt_key(json.loads(row['key']))
        action = encryption.decrypt(json.loads(row['action']), user_key).decode()
        return action
    
async def user_exists(user_id: int):
    pool = await get_database_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow('SELECT name, birth, gender FROM users WHERE id = $1;', user_id)
        if not row:
            
            return False
        filled = all(row[col] for col in ('name', 'birth', 'gender'))
    
    return filled

async def delete_data(user_id: int):
    pool = await get_database_pool()
    async with pool.acquire() as conn:
        await conn.execute('UPDATE users SET name = NULL, birth = NULL, gender = NULL, data = NULL WHERE id = $1;', user_id)

async def delete_user(user_id: int):
    pool = await get_database_pool()
    async with pool.acquire() as conn:
        await conn.execute('DELETE FROM users WHERE id = $1;', user_id)
    