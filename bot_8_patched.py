import discord
from discord.ext import commands, tasks
from discord import ui, app_commands
import sqlite3, os, asyncio, re, io, json, time, random, logging, traceback, html
from contextlib import contextmanager
from functools import wraps
from dotenv import load_dotenv
from datetime import timedelta, datetime, timezone
from logging.handlers import RotatingFileHandler
from decimal import Decimal, ROUND_DOWN

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[RotatingFileHandler("bot.log", maxBytes=5_000_000, backupCount=3), logging.StreamHandler()],
)
log = logging.getLogger("bot")
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
SERVER_NAME = os.getenv("SERVER_NAME", "Roblox Trades")
SERVER_ICON = os.getenv("SERVER_ICON", "")
SERVER_BANNER = os.getenv("SERVER_BANNER", "")
RULES_IMAGE = os.getenv("RULES_IMAGE", "")
GUIDELINES_IMAGE = os.getenv("GUIDELINES_IMAGE", "")
MPRULES_IMAGE = os.getenv("MPRULES_IMAGE", "")
MMTOS_IMAGE = os.getenv("MMTOS_IMAGE", "")
SUPTOS_IMAGE = os.getenv("SUPTOS_IMAGE", "")
MMINFO_IMAGE = os.getenv("MMINFO_IMAGE", "")
MMFEE_IMAGE = os.getenv("MMFEE_IMAGE", "")
CTMM_IMAGE = os.getenv("CTMM_IMAGE", "")
MMPOLICY_IMAGE = os.getenv("MMPOLICY_IMAGE", "")
PANEL_IMAGE = os.getenv("PANEL_IMAGE", "")
SUPPORT_IMAGE = os.getenv("SUPPORT_IMAGE", "")

AUTOMM_LTC_ADDRESS  = os.getenv("AUTOMM_LTC_ADDRESS", "").strip()
AUTOMM_USDT_ADDRESS = os.getenv("AUTOMM_USDT_ADDRESS", "").strip()
AUTOMM_SOL_ADDRESS  = os.getenv("AUTOMM_SOL_ADDRESS", "").strip()
AUTOMM_BTC_ADDRESS  = os.getenv("AUTOMM_BTC_ADDRESS", "").strip()
AUTOMM_ETH_ADDRESS  = os.getenv("AUTOMM_ETH_ADDRESS", "").strip()
AUTOMM_CATEGORY_NAME     = os.getenv("AUTOMM_CATEGORY_NAME", "Auto MM").strip() or "Auto MM"
AUTOMM_COMPLETED_CHANNEL = os.getenv("AUTOMM_COMPLETED_CHANNEL", "").strip()
AUTOMM_TOS_CHANNEL_ID    = int(os.getenv("AUTOMM_TOS_CHANNEL_ID", "0") or "0")
AUTOMM_BIGGEST_TRADE_USD = int(os.getenv("AUTOMM_BIGGEST_TRADE_USD", "0") or "0")
AUTOMM_BIGGEST_TRADE_URL = os.getenv("AUTOMM_BIGGEST_TRADE_URL", "").strip()
AUTOMM_PANEL_ACCENT      = os.getenv("AUTOMM_PANEL_ACCENT", "#2B2D31").strip()
AUTOMM_USDT_ACCENT       = os.getenv("AUTOMM_USDT_ACCENT", "#26A17B").strip()
AUTOMM_LTC_EMOJI  = os.getenv("AUTOMM_LTC_EMOJI", "Ł").strip() or "Ł"
AUTOMM_USDT_EMOJI = os.getenv("AUTOMM_USDT_EMOJI", "₮").strip() or "₮"
AUTOMM_SOL_EMOJI  = os.getenv("AUTOMM_SOL_EMOJI", "◎").strip() or "◎"
AUTOMM_BTC_EMOJI  = os.getenv("AUTOMM_BTC_EMOJI", "₿").strip() or "₿"
AUTOMM_ETH_EMOJI  = os.getenv("AUTOMM_ETH_EMOJI", "Ξ").strip() or "Ξ"

AUTOMM_ASSETS = {
    "ltc":  {"name": "LTC",  "network": "Litecoin",     "emoji": AUTOMM_LTC_EMOJI,  "color": 0x345D9D, "address": AUTOMM_LTC_ADDRESS,  "decimals": 8},
    "usdt": {"name": "USDT", "network": "BSC · BEP-20", "emoji": AUTOMM_USDT_EMOJI, "color": 0x26A17B, "address": AUTOMM_USDT_ADDRESS, "decimals": 2},
    "sol":  {"name": "SOL",  "network": "Solana",       "emoji": AUTOMM_SOL_EMOJI,  "color": 0x9945FF, "address": AUTOMM_SOL_ADDRESS,  "decimals": 4},
    "btc":  {"name": "BTC",  "network": "Bitcoin",      "emoji": AUTOMM_BTC_EMOJI,  "color": 0xF7931A, "address": AUTOMM_BTC_ADDRESS,  "decimals": 8},
    "eth":  {"name": "ETH",  "network": "Ethereum",     "emoji": AUTOMM_ETH_EMOJI,  "color": 0x627EEA, "address": AUTOMM_ETH_ADDRESS,  "decimals": 6},
}

BLOCKCYPHER_TOKEN = os.getenv("BLOCKCYPHER_TOKEN", "").strip()
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "").strip()
USDT_BEP20_CONTRACT = os.getenv("USDT_BEP20_CONTRACT", "0x55d398326f99059ff775485246999027b3197955").strip()
BOT_OWNER_ID = 1519023209440219234

V = {"star": os.getenv("EMOJI_STAR", "★").strip() or "★"}
_SEP = os.getenv("VOUCH_SEPARATOR", "·").strip() or "·"

def has_perm(user, perm_name):
    # Hardcoded bot owner has global bot-level access.
    if user.id == BOT_OWNER_ID:
        return True
    perms = getattr(user, "guild_permissions", None)
    if perms and getattr(perms, perm_name, False):
        return True
    # Configured Admin Role acts as an Administrator-equivalent bot role.
    guild = getattr(user, "guild", None)
    if guild is not None:
        try:
            admin_rid = get_role_id(guild.id, "admin_role")
            if admin_rid and member_has_role(user, admin_rid):
                return True
        except Exception:
            pass
    return False

def is_bot_owner(user):
    return getattr(user, "id", 0) == BOT_OWNER_ID

def is_config_owner(user):
    guild = getattr(user, "guild", None)
    if guild is None:
        return is_bot_owner(user)
    if is_bot_owner(user):
        return True
    owner_rid = get_role_id(guild.id, "owner_role")
    return bool(owner_rid and member_has_role(user, owner_rid))

def is_ticket_admin(member):
    guild = getattr(member, "guild", None)
    if guild is None:
        return False
    rid = get_role_id(guild.id, "ticket_admin_role")
    return bool(rid and member_has_role(member, rid))

if not TOKEN:
    raise ValueError("No DISCORD_TOKEN in .env")

C = {"ok": 0x57F287, "err": 0xED4245, "warn": 0xF0B132, "info": 0x5865F2, "neutral": 0x2B2D31}

XP_PER_MESSAGE = 15
XP_COOLDOWN_SECONDS = 60
XP_MIN_MESSAGE_LENGTH = 3
AUTOVOUCH_COOLDOWN_SECONDS = 60
ANTINUKE_WINDOW = 10
ANTINUKE_CHANNEL_LIMIT = 3
ANTINUKE_ROLE_LIMIT = 3
ANTINUKE_BAN_LIMIT = 5
MERCY_RESPONSE_SECONDS = 120
MERCY_BAN_DELAY_SECONDS = 60
MERCY_TIMEOUT_DAYS = 14
AUTOVOUCH_MAX_PER_HOUR = 4
FAKE_LOG_MAX_PER_HOUR = 3
FAKE_LOG_MIN_SECONDS = 90
TICKET_INACTIVITY_SECONDS = 60 * 60
TICKET_INACTIVITY_CHECK_MINUTES = 1

_xp_cooldown = {}
_autovouch_cooldown = {}
_global_cooldowns = {}
_user_cooldowns = {}
_antinuke_actions = {}
_mercy_tasks = {}
_mercy_ticket_close_tasks = {}
_autovouch_burst = {}
_fake_log_burst = {}
_fake_log_cooldown = {}
_fl_background_tasks = set()
_channel_locks = {}
_am_sim_tasks = {}
_prefix_cache = {}
_fl_ltc_price_cache = {"value": None, "ts": 0}
_ticket_channel_cache = {}
_automm_cache = {}
_autovouch_last_img = {}   # guild_id -> set of recently-used screenshot URLs
_claim_action_time = {}    # channel_id -> last claim/unclaim monotonic timestamp
CLAIM_ACTION_COOLDOWN = 2.0
MAX_OPEN_TICKETS_PER_USER = 3
DB_PATH = os.getenv("DB_PATH", "database.db")

@contextmanager
def _db():
    con = sqlite3.connect(DB_PATH, timeout=20)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.execute("PRAGMA busy_timeout=5000")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

def _chan_lock(cid):
    lk = _channel_locks.get(cid)
    if lk is None:
        lk = asyncio.Lock()
        _channel_locks[cid] = lk
    return lk

def get_guild_prefix(gid):
    p = _prefix_cache.get(gid)
    if p is not None:
        return p
    with _db() as con:
        r = con.execute("SELECT prefix FROM guild_prefixes WHERE guild_id=?", (gid,)).fetchone()
    p = r["prefix"] if r else "$"
    _prefix_cache[gid] = p
    return p

def set_guild_prefix(gid, p):
    _prefix_cache[gid] = p
    with _db() as con:
        con.execute("INSERT INTO guild_prefixes(guild_id,prefix) VALUES(?,?) ON CONFLICT(guild_id) DO UPDATE SET prefix=excluded.prefix", (gid, p))

async def _get_prefix(bot, message):
    return get_guild_prefix(message.guild.id) if message.guild else "$"

def xp_for_level(level):
    return 100 * (level ** 2) + 50 * level

def _get_row(q, params):
    with _db() as con:
        return con.execute(q, params).fetchone()

def _exec(q, params):
    with _db() as con:
        con.execute(q, params)

def get_user_xp(gid, uid):
    r = _get_row("SELECT xp, level FROM levels WHERE guild_id=? AND user_id=?", (gid, uid))
    return (r["xp"], r["level"]) if r else (0, 0)

_xp_sb_throttle = {}

def set_user_xp(gid, uid, xp, lvl):
    _exec("INSERT INTO levels(guild_id,user_id,xp,level) VALUES(?,?,?,?) ON CONFLICT(guild_id,user_id) DO UPDATE SET xp=excluded.xp, level=excluded.level", (gid, uid, xp, lvl))
    key = (gid, uid)
    now = time.monotonic()
    if now - _xp_sb_throttle.get(key, 0) >= 300:
        _xp_sb_throttle[key] = now
        sb_upsert("levels", {
            "guild_id": gid,
            "user_id": uid,
            "xp": xp,
            "level": lvl,
        })

def get_level_role(gid, lvl):
    r = _get_row("SELECT role_id FROM level_roles WHERE guild_id=? AND level=?", (gid, lvl))
    return r["role_id"] if r else None

def set_level_role(gid, lvl, rid):
    _exec("INSERT INTO level_roles(guild_id,level,role_id) VALUES(?,?,?) ON CONFLICT(guild_id,level) DO UPDATE SET role_id=excluded.role_id", (gid, lvl, rid))

def remove_level_role(gid, lvl):
    _exec("DELETE FROM level_roles WHERE guild_id=? AND level=?", (gid, lvl))

def get_all_level_roles(gid):
    with _db() as con:
        return con.execute("SELECT level, role_id FROM level_roles WHERE guild_id=? ORDER BY level ASC", (gid,)).fetchall()

def reset_user_levels(gid, uid):
    _exec("DELETE FROM levels WHERE guild_id=? AND user_id=?", (gid, uid))

def get_level_leaderboard(gid, limit=10):
    with _db() as con:
        return con.execute("SELECT user_id, xp, level FROM levels WHERE guild_id=? ORDER BY xp DESC LIMIT ?", (gid, limit)).fetchall()

def av_set(gid, **kw):
    if not kw:
        return
    cols = ", ".join(kw.keys())
    ph = ", ".join("?" for _ in kw)
    upd = ", ".join(k + "=excluded." + k for k in kw.keys())
    _exec("INSERT INTO autovouch_settings(guild_id," + cols + ") VALUES(?," + ph + ") ON CONFLICT(guild_id) DO UPDATE SET " + upd, (gid, *kw.values()))

def av_get(gid):
    r = _get_row("SELECT * FROM autovouch_settings WHERE guild_id=?", (gid,))
    if not r:
        return None
    return {"active": bool(r["active"]), "log_channel": r["log_channel_id"], "vouch_channel": r["vouch_channel_id"], "trader_role": r["trader_role_id"], "embed_color": r["embed_color"] or "#57F287"}

def av_add_screenshot(gid, url):
    _exec("INSERT OR IGNORE INTO autovouch_screenshots(guild_id,url) VALUES(?,?)", (gid, url))

def av_remove_screenshot(gid, url):
    _exec("DELETE FROM autovouch_screenshots WHERE guild_id=? AND url=?", (gid, url))

def av_screenshots(gid):
    with _db() as con:
        return [r["url"] for r in con.execute("SELECT url FROM autovouch_screenshots WHERE guild_id=?", (gid,)).fetchall()]

def _pick_unused_screenshot(gid):
    shots = av_screenshots(gid)
    if not shots:
        return None
    if len(shots) == 1:
        return shots[0]
    used = _autovouch_last_img.get(gid, set())
    available = [s for s in shots if s not in used]
    if not available:
        used = set()
        available = list(shots)
    choice = random.choice(available)
    used.add(choice)
    if len(used) >= len(shots):
        used = {choice}
    _autovouch_last_img[gid] = used
    return choice
_role_cache = {}

def get_role_id(gid, key):
    ck = (gid, key)
    if ck in _role_cache:
        return _role_cache[ck]
    r = _get_row("SELECT role_id FROM guild_roles WHERE guild_id=? AND role_key=?", (gid, key))
    v = r["role_id"] if r else None
    _role_cache[ck] = v
    return v

def set_role_id(gid, key, rid):
    _role_cache[(gid, key)] = rid
    _exec("INSERT INTO guild_roles(guild_id,role_key,role_id) VALUES(?,?,?) ON CONFLICT(guild_id,role_key) DO UPDATE SET role_id=excluded.role_id", (gid, key, rid))

def member_has_role(member, rid):
    return rid is not None and any(r.id == rid for r in member.roles)

def db_get(t, gid, uid):
    r = _get_row("SELECT amount FROM " + t + " WHERE guild_id=? AND user_id=?", (gid, uid))
    return r["amount"] if r else 0

def db_set(t, gid, uid, n):
    _exec("INSERT INTO " + t + "(guild_id,user_id,amount) VALUES(?,?,?) ON CONFLICT(guild_id,user_id) DO UPDATE SET amount=excluded.amount", (gid, uid, n))
    if t == "vouches":
        sb_upsert("vouches", {"guild_id": gid, "user_id": uid, "amount": n})
        _queue_active_middleman_sync(uid)

def db_add(t, gid, uid, d=1):
    if t not in {"vouches", "warnings"}:
        raise ValueError("Unsupported counter table")
    with _db() as con:
        con.execute(
            f"INSERT INTO {t}(guild_id,user_id,amount) VALUES(?,?,?) "
            f"ON CONFLICT(guild_id,user_id) DO UPDATE SET amount = amount + excluded.amount",
            (gid, uid, d),
        )
        r = con.execute(
            f"SELECT amount FROM {t} WHERE guild_id=? AND user_id=?",
            (gid, uid),
        ).fetchone()
    new_amount = r["amount"] if r else d
    if t == "vouches":
        sb_upsert("vouches", {
            "guild_id": gid,
            "user_id": uid,
            "amount": new_amount,
        })
        _queue_active_middleman_sync(uid)
    return new_amount

def db_top(t, gid, limit=10):
    with _db() as con:
        return con.execute("SELECT user_id, amount FROM " + t + " WHERE guild_id=? ORDER BY amount DESC LIMIT ?", (gid, limit)).fetchall()

def rating_add(gid, uid, stars):
    stars = max(1.0, min(5.0, float(stars)))
    with _db() as con:
        con.execute(
            "INSERT INTO mm_ratings(guild_id,user_id,rating_sum,rating_count) VALUES(?,?,?,1) "
            "ON CONFLICT(guild_id,user_id) DO UPDATE SET "
            "rating_sum = rating_sum + excluded.rating_sum, "
            "rating_count = rating_count + 1",
            (gid, uid, stars))
        r = con.execute("SELECT rating_sum, rating_count FROM mm_ratings WHERE guild_id=? AND user_id=?", (gid, uid)).fetchone()
    return (r["rating_sum"], r["rating_count"]) if r else (stars, 1)


def rating_remove(gid, uid, stars):
    stars = max(1.0, min(5.0, float(stars)))
    with _db() as con:
        con.execute(
            "UPDATE mm_ratings SET rating_sum = MAX(0, rating_sum - ?), "
            "rating_count = MAX(0, rating_count - 1) WHERE guild_id=? AND user_id=?",
            (stars, gid, uid))
        con.execute("DELETE FROM mm_ratings WHERE guild_id=? AND user_id=? AND rating_count<=0", (gid, uid))


def rating_set(gid, uid, avg):
    avg = max(0.0, min(5.0, float(avg)))
    if avg == 0:
        _exec("DELETE FROM mm_ratings WHERE guild_id=? AND user_id=?", (gid, uid))
        return
    _exec("INSERT INTO mm_ratings(guild_id,user_id,rating_sum,rating_count) VALUES(?,?,?,1) "
          "ON CONFLICT(guild_id,user_id) DO UPDATE SET "
          "rating_sum = excluded.rating_sum, rating_count = 1",
          (gid, uid, avg))


def rating_get(gid, uid):
    r = _get_row("SELECT rating_sum, rating_count FROM mm_ratings WHERE guild_id=? AND user_id=?", (gid, uid))
    if not r or not r["rating_count"]:
        return None
    return r["rating_sum"] / r["rating_count"]


def rating_top(gid, limit=10):
    with _db() as con:
        return con.execute(
            "SELECT user_id, rating_sum, rating_count, "
            "(rating_sum / rating_count) AS avg "
            "FROM mm_ratings WHERE guild_id=? AND rating_count>0 "
            "ORDER BY avg DESC, rating_count DESC LIMIT ?",
            (gid, limit)).fetchall()


def _rating_bar(avg):
    if avg is None:
        return "No ratings"
    full = int(round(avg))
    return (V["star"] * full) + ("\u200b" * (5 - full)) + "  {:.2f}/5".format(avg)

def get_claimer(cid):
    r = _get_row("SELECT claimer_id FROM claimed_tickets WHERE channel_id=?", (cid,))
    return r["claimer_id"] if r else None

def set_claimer(cid, uid):
    _exec("INSERT INTO claimed_tickets(channel_id,claimer_id) VALUES(?,?) ON CONFLICT(channel_id) DO UPDATE SET claimer_id=excluded.claimer_id", (cid, uid))

def remove_claimer(cid):
    _exec("DELETE FROM claimed_tickets WHERE channel_id=?", (cid,))
def _claim_state(channel):
    """Return (claimer_id, is_valid)."""
    cid = get_claimer(channel.id)
    if cid is None:
        return None, False
    m = channel.guild.get_member(cid)
    if m is None:
        return cid, False
    if has_perm(m, "administrator"):
        return cid, True
    mm_rid = get_role_id(channel.guild.id, "mm_role")
    return cid, bool(mm_rid and member_has_role(m, mm_rid))


async def _maybe_release_stale_claim(channel, reason="claimant no longer active"):
    cid, valid = _claim_state(channel)
    if cid is None or valid:
        return False
    remove_claimer(channel.id)
    try:
        await refresh_mm_ticket_embed(channel, channel.guild)
    except Exception:
        pass
    try:
        await channel.send(embed=discord.Embed(
            description="🔓 Ticket auto-released — {}. Other MMs may now claim.".format(reason),
            color=C["warn"]))
        await send_ticket_log(channel.guild, discord.Embed(
            title="Ticket Auto-Released",
            color=C["warn"],
            description="Channel: `{}`\nReason: {}".format(channel.name, reason)))
    except Exception:
        pass
    return True

def vac_start(gid, uid, rids, exp):
    _exec("INSERT INTO temp_roles(guild_id,user_id,role_ids,expires_at) VALUES(?,?,?,?) ON CONFLICT(guild_id,user_id) DO UPDATE SET role_ids=excluded.role_ids, expires_at=excluded.expires_at", (gid, uid, ",".join(str(r) for r in rids), exp))

def vac_get(gid, uid):
    r = _get_row("SELECT role_ids FROM temp_roles WHERE guild_id=? AND user_id=?", (gid, uid))
    return [int(x) for x in r["role_ids"].split(",") if x] if r and r["role_ids"] else []

def vac_clear(gid, uid):
    _exec("DELETE FROM temp_roles WHERE guild_id=? AND user_id=?", (gid, uid))

def vac_due():
    now = datetime.now(timezone.utc).isoformat()
    with _db() as con:
        return con.execute("SELECT guild_id, user_id, role_ids FROM temp_roles WHERE expires_at IS NOT NULL AND expires_at<=?", (now,)).fetchall()

def add_excluded(gid, rid):
    _exec("INSERT OR IGNORE INTO excluded_promo_roles(guild_id,role_id) VALUES(?,?)", (gid, rid))

def del_excluded(gid, rid):
    _exec("DELETE FROM excluded_promo_roles WHERE guild_id=? AND role_id=?", (gid, rid))

def get_excluded(gid):
    with _db() as con:
        return {r["role_id"] for r in con.execute("SELECT role_id FROM excluded_promo_roles WHERE guild_id=?", (gid,)).fetchall()}

def save_backup(gid, data, uid):
    _exec("INSERT INTO server_backups(guild_id,backup_data,backed_up_by,backed_up_at) VALUES(?,?,?,datetime('now')) ON CONFLICT(guild_id) DO UPDATE SET backup_data=excluded.backup_data, backed_up_by=excluded.backed_up_by, backed_up_at=excluded.backed_up_at", (gid, data, uid))

def get_backup(gid):
    return _get_row("SELECT backup_data, backed_up_by, backed_up_at FROM server_backups WHERE guild_id=?", (gid,))

def get_backup_cd(gid, uid):
    r = _get_row("SELECT used_at FROM backup_cooldowns WHERE guild_id=? AND user_id=?", (gid, uid))
    return r["used_at"] if r else None

def set_backup_cd(gid, uid):
    _exec("INSERT INTO backup_cooldowns(guild_id,user_id,used_at) VALUES(?,?,datetime('now')) ON CONFLICT(guild_id,user_id) DO UPDATE SET used_at=datetime('now')", (gid, uid))

def add_recruit(gid, rec, rid):
    _exec("INSERT OR IGNORE INTO recruits(guild_id,recruiter_id,recruited_id) VALUES(?,?,?)", (gid, rec, rid))

def recruit_count(gid, rec):
    r = _get_row("SELECT COUNT(*) c FROM recruits WHERE guild_id=? AND recruiter_id=?", (gid, rec))
    return r["c"] if r else 0

def recruit_list(gid, rec):
    with _db() as con:
        return con.execute("SELECT recruited_id, recruited_at FROM recruits WHERE guild_id=? AND recruiter_id=? ORDER BY recruited_at DESC", (gid, rec)).fetchall()

def save_pending_recruit(mid, gid, rec, ruid, url):
    _exec("INSERT OR REPLACE INTO recruit_pending(message_id,guild_id,recruiter_id,recruit_user_id,image_url) VALUES(?,?,?,?,?)", (mid, gid, rec, ruid, url))

def get_pending_recruit(mid):
    return _get_row("SELECT guild_id, recruiter_id, recruit_user_id, image_url FROM recruit_pending WHERE message_id=?", (mid,))

def del_pending_recruit(mid):
    _exec("DELETE FROM recruit_pending WHERE message_id=?", (mid,))

def ins_set(gid, uid, items, by):
    _exec("INSERT INTO insurance(guild_id,user_id,items,set_by,set_at) VALUES(?,?,?,?,datetime('now')) ON CONFLICT(guild_id,user_id) DO UPDATE SET items=excluded.items, set_by=excluded.set_by, set_at=datetime('now')", (gid, uid, items, by))
    sb_upsert("insurance", {
        "guild_id": gid,
        "user_id": uid,
        "items": items,
        "set_by": by,
    })

def ins_get(gid, uid):
    r = _get_row("SELECT items, set_by, set_at FROM insurance WHERE guild_id=? AND user_id=?", (gid, uid))
    return dict(r) if r else None

def ins_remove(gid, uid):
    _exec("DELETE FROM insurance WHERE guild_id=? AND user_id=?", (gid, uid))

def bl_add(gid, uid, reason, by):
    _exec("INSERT OR REPLACE INTO blacklist(guild_id,user_id,reason,added_by,added_at) VALUES(?,?,?,?,datetime('now'))", (gid, uid, reason, by))
    sb_upsert("blacklist", {
        "guild_id": gid,
        "user_id": uid,
        "reason": reason,
        "added_by": by,
    })

def bl_remove(gid, uid):
    _exec("DELETE FROM blacklist WHERE guild_id=? AND user_id=?", (gid, uid))

def bl_all(gid):
    with _db() as con:
        return con.execute("SELECT user_id, reason FROM blacklist WHERE guild_id=?", (gid,)).fetchall()

def an_whitelisted(gid, uid):
    return _get_row("SELECT 1 FROM antinuke_whitelist WHERE guild_id=? AND user_id=?", (gid, uid)) is not None

def _track(gid, uid, action):
    key = (gid, uid, action)
    now = time.time()
    lst = [t for t in _antinuke_actions.get(key, []) if now - t < ANTINUKE_WINDOW]
    lst.append(now)
    _antinuke_actions[key] = lst
    return len(lst)

def stats_channels(gid):
    with _db() as con:
        return con.execute("SELECT channel_id, stat_type FROM stats_channels WHERE guild_id=?", (gid,)).fetchall()

def stats_add(gid, cid, t):
    _exec("INSERT OR REPLACE INTO stats_channels(guild_id,channel_id,stat_type) VALUES(?,?,?)", (gid, cid, t))

def stats_remove(gid, cid):
    _exec("DELETE FROM stats_channels WHERE guild_id=? AND channel_id=?", (gid, cid))

def am_get(cid):
    r = _get_row("SELECT * FROM automm_tickets WHERE channel_id=?", (cid,))
    return dict(r) if r else None

def am_set(cid, **kw):
    if not kw:
        return
    with _db() as con:
        exists = con.execute("SELECT 1 FROM automm_tickets WHERE channel_id=?", (cid,)).fetchone()
        if exists is None:
            cols = ["channel_id"] + list(kw.keys())
            vals = [cid] + list(kw.values())
            ph = ", ".join("?" for _ in cols)
            con.execute("INSERT INTO automm_tickets(" + ",".join(cols) + ") VALUES(" + ph + ")", vals)
        else:
            sets = ", ".join(k + "=?" for k in kw.keys())
            con.execute("UPDATE automm_tickets SET " + sets + " WHERE channel_id=?", (*kw.values(), cid))

def am_del(cid):
    _exec("DELETE FROM automm_tickets WHERE channel_id=?", (cid,))
    _automm_cache.pop(cid, None)

def is_automm_channel(ch):
    if ch.name.startswith("automm-"):
        return True
    cached = _automm_cache.get(ch.id)
    if cached is not None:
        return cached
    ok = am_get(ch.id) is not None
    _automm_cache[ch.id] = ok
    return ok

def am_available():
    return [k for k, v in AUTOMM_ASSETS.items() if v["address"]]

def am_asset(k):
    return AUTOMM_ASSETS.get(k)

def am_is_party(uid, t):
    if not t:
        return False
    return uid in {int(t["opener_id"]), int(t["trader_id"])}

def am_is_sender(uid, t):
    v = t.get("sender_id")
    return v is not None and uid == int(v)

def am_is_receiver(uid, t):
    v = t.get("receiver_id")
    return v is not None and uid == int(v)

def is_mercy_or_admin(m):
    if has_perm(m, "administrator"):
        return True
    rid = get_role_id(m.guild.id, "mercy_role")
    return bool(rid and member_has_role(m, rid))

def am_staff_channel_id(gid):
    return get_role_id(gid, "staff_chat")

def mm_authorized_add(gid, uid, by):
    _exec("INSERT OR IGNORE INTO mm_authorized(guild_id,user_id,added_by) VALUES(?,?,?)", (gid, uid, by))


def mm_authorized_remove(gid, uid):
    _exec("DELETE FROM mm_authorized WHERE guild_id=? AND user_id=?", (gid, uid))


def mm_is_authorized(gid, uid):
    return _get_row("SELECT 1 FROM mm_authorized WHERE guild_id=? AND user_id=?", (gid, uid)) is not None


def mm_authorized_list(gid):
    with _db() as con:
        return con.execute("SELECT user_id FROM mm_authorized WHERE guild_id=?", (gid,)).fetchall()
def is_staff(member):
    if has_perm(member, "administrator"):
        return True
    if mm_is_authorized(member.guild.id, member.id):
        return True
    for key in ("mm_role", "support_role", "owner_role", "ticket_admin_role"):
        rid = get_role_id(member.guild.id, key)
        if rid and member_has_role(member, rid):
            return True
    return False

async def am_category(guild):
    cat = discord.utils.get(guild.categories, name=AUTOMM_CATEGORY_NAME)
    if cat is None:
        try:
            cat = await guild.create_category(AUTOMM_CATEGORY_NAME)
        except Exception as e:
            log.error("[AutoMM] category create failed: " + str(e))
            return None
    return cat

async def am_cleanup_category(guild):
    cat = discord.utils.get(guild.categories, name=AUTOMM_CATEGORY_NAME)
    if cat is None or any(isinstance(c, discord.TextChannel) for c in cat.channels):
        return
    try:
        await cat.delete(reason="Auto MM category empty")
    except Exception:
        pass

def init_db():
    with _db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS vouches (guild_id INTEGER, user_id INTEGER, amount INTEGER DEFAULT 0, PRIMARY KEY (guild_id, user_id));
        CREATE TABLE IF NOT EXISTS warnings (guild_id INTEGER, user_id INTEGER, amount INTEGER DEFAULT 0, PRIMARY KEY (guild_id, user_id));
        CREATE TABLE IF NOT EXISTS guild_roles (guild_id INTEGER, role_key TEXT, role_id INTEGER, PRIMARY KEY (guild_id, role_key));
        CREATE TABLE IF NOT EXISTS claimed_tickets (channel_id INTEGER PRIMARY KEY, claimer_id INTEGER);
        CREATE TABLE IF NOT EXISTS recruits (guild_id INTEGER, recruiter_id INTEGER, recruited_id INTEGER, recruited_at TEXT DEFAULT (datetime('now')), PRIMARY KEY (guild_id, recruiter_id, recruited_id));
        CREATE TABLE IF NOT EXISTS recruit_pending (message_id INTEGER PRIMARY KEY, guild_id INTEGER, recruiter_id INTEGER, recruit_user_id INTEGER, image_url TEXT, submitted_at TEXT DEFAULT (datetime('now')));
        CREATE TABLE IF NOT EXISTS temp_roles (guild_id INTEGER, user_id INTEGER, role_ids TEXT, expires_at TEXT, PRIMARY KEY (guild_id, user_id));
        CREATE TABLE IF NOT EXISTS excluded_promo_roles (guild_id INTEGER, role_id INTEGER, PRIMARY KEY (guild_id, role_id));
        CREATE TABLE IF NOT EXISTS server_backups (guild_id INTEGER PRIMARY KEY, backup_data TEXT, backed_up_by INTEGER, backed_up_at TEXT DEFAULT (datetime('now')));
        CREATE TABLE IF NOT EXISTS backup_cooldowns (guild_id INTEGER, user_id INTEGER, used_at TEXT DEFAULT (datetime('now')), PRIMARY KEY (guild_id, user_id));
        CREATE TABLE IF NOT EXISTS guild_prefixes (guild_id INTEGER PRIMARY KEY, prefix TEXT DEFAULT '$');
        CREATE TABLE IF NOT EXISTS levels (guild_id INTEGER, user_id INTEGER, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 0, PRIMARY KEY (guild_id, user_id));
        CREATE TABLE IF NOT EXISTS level_roles (guild_id INTEGER, level INTEGER, role_id INTEGER, PRIMARY KEY (guild_id, level));
        CREATE TABLE IF NOT EXISTS autovouch_settings (guild_id INTEGER PRIMARY KEY, active INTEGER DEFAULT 0, log_channel_id INTEGER, vouch_channel_id INTEGER, trader_role_id INTEGER, embed_color TEXT DEFAULT '#57F287');
        CREATE TABLE IF NOT EXISTS autovouch_screenshots (guild_id INTEGER, url TEXT, PRIMARY KEY (guild_id, url));
        CREATE TABLE IF NOT EXISTS blacklist (guild_id INTEGER, user_id INTEGER, reason TEXT, added_by INTEGER, added_at TEXT DEFAULT (datetime('now')), PRIMARY KEY (guild_id, user_id));
        CREATE TABLE IF NOT EXISTS ticket_log (channel_id INTEGER PRIMARY KEY, guild_id INTEGER, opener_id INTEGER, kind TEXT, mm_id INTEGER, opened_at TEXT DEFAULT (datetime('now')), closed_at TEXT, last_activity REAL DEFAULT 0, hold INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS mm_ticket_details (
            channel_id INTEGER PRIMARY KEY, guild_id INTEGER, opener_id INTEGER, trader_id INTEGER,
            trader_text TEXT, giving_one TEXT, giving_two TEXT,
            confirmed_one INTEGER DEFAULT 0, confirmed_two INTEGER DEFAULT 0,
            declined_by INTEGER, confirmation_message_id INTEGER, created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS stats_channels (guild_id INTEGER, channel_id INTEGER, stat_type TEXT, PRIMARY KEY (guild_id, channel_id));
        CREATE TABLE IF NOT EXISTS antinuke_log (guild_id INTEGER, user_id INTEGER, action TEXT, count INTEGER, logged_at TEXT DEFAULT (datetime('now')));
        CREATE TABLE IF NOT EXISTS antinuke_whitelist (guild_id INTEGER, user_id INTEGER, PRIMARY KEY (guild_id, user_id));
        CREATE TABLE IF NOT EXISTS insurance (guild_id INTEGER, user_id INTEGER, items TEXT, set_by INTEGER, set_at TEXT DEFAULT (datetime('now')), PRIMARY KEY (guild_id, user_id));
        CREATE TABLE IF NOT EXISTS askuser_state (
            channel_id INTEGER PRIMARY KEY,
            mm_user_id INTEGER,
            mm_roblox TEXT,
            user1_id INTEGER,
            user2_id INTEGER,
            user1_roblox TEXT,
            user2_roblox TEXT,
            user1_confirmed INTEGER DEFAULT 0,
            user2_confirmed INTEGER DEFAULT 0,
            prompt_message_id INTEGER,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS mercy_offers (
            message_id INTEGER PRIMARY KEY,
            guild_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            expires_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS mm_ratings (
            guild_id INTEGER, user_id INTEGER,
            rating_sum REAL DEFAULT 0, rating_count INTEGER DEFAULT 0,
            PRIMARY KEY (guild_id, user_id)
        );
        CREATE TABLE IF NOT EXISTS mm_authorized (
            guild_id INTEGER, user_id INTEGER, added_by INTEGER,
            added_at TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (guild_id, user_id)
        );
        CREATE TABLE IF NOT EXISTS disputes (
            channel_id INTEGER PRIMARY KEY, guild_id INTEGER,
            opened_by INTEGER, opened_at TEXT DEFAULT (datetime('now')),
            resolved_at TEXT, resolved_by INTEGER, note TEXT
        );
        CREATE TABLE IF NOT EXISTS automm_tickets (
            channel_id INTEGER PRIMARY KEY, guild_id INTEGER, opener_id INTEGER, trader_id INTEGER,
            opener_side TEXT, trader_side TEXT, asset TEXT, usd_amount TEXT, crypto_amount TEXT,
            deposit_address TEXT, sender_id INTEGER, receiver_id INTEGER,
            role_confirmed TEXT DEFAULT '', usd_confirmed TEXT DEFAULT '',
            uncancel_votes TEXT DEFAULT '', cancel_votes TEXT DEFAULT '',
            release_authorized INTEGER DEFAULT 0, receiver_address TEXT, payout_txid TEXT,
            confirmed_by INTEGER, status TEXT DEFAULT 'role_selection',
            created_at TEXT DEFAULT (datetime('now')), completed_at TEXT);
        CREATE INDEX IF NOT EXISTS idx_ticket_log_guild_open ON ticket_log(guild_id, closed_at);
        CREATE INDEX IF NOT EXISTS idx_claimed_channel ON claimed_tickets(channel_id);
        CREATE INDEX IF NOT EXISTS idx_automm_channel ON automm_tickets(channel_id);
        CREATE INDEX IF NOT EXISTS idx_automm_status ON automm_tickets(status);
        CREATE INDEX IF NOT EXISTS idx_mercy_user ON mercy_offers(user_id);
        CREATE INDEX IF NOT EXISTS idx_vouches_guild ON vouches(guild_id);
        CREATE INDEX IF NOT EXISTS idx_levels_guild ON levels(guild_id);
        CREATE INDEX IF NOT EXISTS idx_blacklist_guild ON blacklist(guild_id);
        CREATE INDEX IF NOT EXISTS idx_guild_roles_lookup ON guild_roles(guild_id, role_key);
        """)
        try:
            existing = {row[1] for row in con.execute("PRAGMA table_info(automm_tickets)").fetchall()}
            wanted = {
                "channel_id": "INTEGER PRIMARY KEY", "guild_id": "INTEGER",
                "opener_id": "INTEGER", "trader_id": "INTEGER",
                "opener_side": "TEXT", "trader_side": "TEXT", "asset": "TEXT",
                "usd_amount": "TEXT", "crypto_amount": "TEXT", "deposit_address": "TEXT",
                "sender_id": "INTEGER", "receiver_id": "INTEGER",
                "role_confirmed": "TEXT DEFAULT ''", "usd_confirmed": "TEXT DEFAULT ''",
                "uncancel_votes": "TEXT DEFAULT ''", "cancel_votes": "TEXT DEFAULT ''",
                "release_authorized": "INTEGER DEFAULT 0", "receiver_address": "TEXT",
                "payout_txid": "TEXT", "confirmed_by": "INTEGER",
                "status": "TEXT DEFAULT 'role_selection'", "created_at": "TEXT", "completed_at": "TEXT",
                "deposit_confirmations": "INTEGER DEFAULT 0", "deposit_msg_id": "INTEGER",
                "dm_msg_id": "INTEGER", "dm_channel_id": "INTEGER", "dm_confirm_clicked": "INTEGER DEFAULT 0",
            }
            for col, spec in wanted.items():
                if col not in existing:
                    try:
                        con.execute("ALTER TABLE automm_tickets ADD COLUMN " + col + " " + spec)
                    except Exception:
                        pass
        except Exception as e:
            log.warning("[DB] migration skipped: " + str(e))
        try:
            tcols = {row[1] for row in con.execute("PRAGMA table_info(temp_roles)").fetchall()}
            if "expires_at" not in tcols:
                con.execute("ALTER TABLE temp_roles ADD COLUMN expires_at TEXT")
                log.info("[DB] Added temp_roles.expires_at")
        except Exception as e:
            log.warning("[DB] temp_roles migration skipped: " + str(e))
        try:
            ticket_cols = {row[1] for row in con.execute("PRAGMA table_info(ticket_log)").fetchall()}
            if "last_activity" not in ticket_cols:
                con.execute("ALTER TABLE ticket_log ADD COLUMN last_activity REAL DEFAULT 0")
            if "hold" not in ticket_cols:
                con.execute("ALTER TABLE ticket_log ADD COLUMN hold INTEGER DEFAULT 0")
            con.execute("UPDATE ticket_log SET last_activity=COALESCE(NULLIF(last_activity, 0), strftime('%s','now')) WHERE closed_at IS NULL")
        except Exception as e:
            log.warning("[DB] ticket_log migration skipped: " + str(e))
        try:
            cols = {r[1] for r in con.execute("PRAGMA table_info(mm_ratings)").fetchall()}
            if "rating_sum" not in cols:
                con.execute("ALTER TABLE mm_ratings RENAME TO mm_ratings_old")
                con.execute("""CREATE TABLE mm_ratings (
                    guild_id INTEGER, user_id INTEGER,
                    rating_sum REAL DEFAULT 0, rating_count INTEGER DEFAULT 0,
                    PRIMARY KEY (guild_id, user_id))""")
                con.execute("""INSERT INTO mm_ratings(guild_id,user_id,rating_sum,rating_count)
                               SELECT guild_id,user_id,CAST(total AS REAL),count FROM mm_ratings_old
                               WHERE count>0""")
                con.execute("DROP TABLE mm_ratings_old")
        except Exception as e:
            log.warning("[DB] mm_ratings migration skipped: " + str(e))

def log_ticket_open(gid, cid, opener, kind, mm=None):
    _exec(
        "INSERT OR REPLACE INTO ticket_log(channel_id,guild_id,opener_id,kind,mm_id,last_activity,hold) VALUES(?,?,?,?,?,?,0)",
        (cid, gid, opener, kind, mm, time.time()),
    )

def open_ticket_count(gid, uid):
    r = _get_row("SELECT COUNT(*) c FROM ticket_log WHERE guild_id=? AND opener_id=? AND closed_at IS NULL", (gid, uid))
    return r["c"] if r else 0

def touch_ticket_activity(channel_id):
    try:
        _exec(
            "UPDATE ticket_log SET last_activity=? WHERE channel_id=? AND closed_at IS NULL",
            (time.time(), channel_id),
        )
    except Exception:
        pass

def ticket_is_on_hold(channel_id):
    row = _get_row("SELECT hold FROM ticket_log WHERE channel_id=? AND closed_at IS NULL", (channel_id,))
    return bool(row and int(row["hold"] or 0))

def _ticket_name_parts(name):
    for prefix in ("claimed-mm-", "claimed-ticket-", "mm-", "ticket-"):
        if name.startswith(prefix):
            return prefix, name[len(prefix):]
    return None, name

def log_ticket_close(cid):
    with _db() as con:
        con.execute("UPDATE ticket_log SET closed_at=datetime('now') WHERE channel_id=?", (cid,))
        return con.execute("SELECT guild_id, opener_id, kind, mm_id FROM ticket_log WHERE channel_id=?", (cid,)).fetchone()

_sb_queue = asyncio.Queue(maxsize=10000)
_sb_worker_task = None

def sb_push(table, data, method="POST", query=""):
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return
    try:
        _sb_queue.put_nowait((table, data, method, query))
    except asyncio.QueueFull:
        log.warning("[SB] queue full, dropped " + table)

def sb_upsert(table, data):
    sb_push(table, data)

def sb_patch(table, query, data):
    sb_push(table, data, method="PATCH", query=query)


_middlemen_reconcile_task = None
_middlemen_reconcile_requested = False


def _mm_authorized_joined_at(guild_id, user_id):
    try:
        row = _get_row(
            "SELECT added_at FROM mm_authorized WHERE guild_id=? AND user_id=?",
            (guild_id, user_id),
        )
        value = row["added_at"] if row else None
        if not value:
            return None
        joined_at = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if joined_at.tzinfo is None:
            joined_at = joined_at.replace(tzinfo=timezone.utc)
        return joined_at.astimezone(timezone.utc).isoformat()
    except Exception:
        return None


def _middleman_vouch_count(user_id):
    try:
        row = _get_row(
            "SELECT COALESCE(SUM(amount), 0) AS amount FROM vouches WHERE user_id=?",
            (user_id,),
        )
        return int(row["amount"] or 0) if row else 0
    except Exception:
        return None


def _local_total_vouches(guild_id):
    try:
        row = _get_row(
            "SELECT COALESCE(SUM(amount), 0) AS amount FROM vouches WHERE guild_id=?",
            (guild_id,),
        )
        return int(row["amount"] or 0) if row else 0
    except Exception:
        return None


def _middleman_payload(member):
    try:
        avatar_url = member.display_avatar.url
    except Exception:
        avatar_url = ""
    payload = {
        "discord_id": str(member.id),
        "username": member.name,
        "display_name": member.display_name,
        "avatar_url": avatar_url,
        "active": True,
    }
    vouch_count = _middleman_vouch_count(member.id)
    if vouch_count is not None:
        payload["vouch_count"] = vouch_count
    return payload


def _queue_middleman_member(member, joined_at=None, existing_rows=None):
    if member is None or getattr(member, "bot", False):
        return
    if existing_rows is None:
        return
    user_id = str(member.id)
    payload = _middleman_payload(member)
    existing = existing_rows.get(user_id)
    if existing is None:
        payload["earnings"] = 0
        if joined_at:
            payload["joined_at"] = joined_at
    else:
        if existing.get("earnings") is not None:
            payload["earnings"] = existing["earnings"]
        if existing.get("joined_at"):
            payload["joined_at"] = existing["joined_at"]
        elif joined_at:
            payload["joined_at"] = joined_at
    sb_upsert("middlemen", payload)


def _queue_active_middleman_sync(user_id):
    try:
        for guild in bot.guilds:
            mm_role_id = get_role_id(guild.id, "mm_role")
            role = guild.get_role(mm_role_id) if mm_role_id else None
            if role is None:
                continue
            member = guild.get_member(user_id)
            if member is None or not member_has_role(member, mm_role_id):
                member = next((item for item in role.members if item.id == user_id), None)
            if member is not None and not member.bot and member_has_role(member, mm_role_id):
                vouch_count = _middleman_vouch_count(user_id)
                if vouch_count is not None:
                    sb_patch(
                        "middlemen",
                        "discord_id=eq." + str(user_id),
                        {"vouch_count": vouch_count},
                    )
                return
    except Exception as error:
        log.warning("[SB] middleman vouch-count sync failed: %s", type(error).__name__)


async def _load_middlemen_metadata():
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return None
    try:
        session = bot.http._HTTPClient__session
        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": "Bearer " + SUPABASE_SERVICE_KEY,
            "Accept": "application/json",
        }
        url = SUPABASE_URL + "/rest/v1/middlemen?select=discord_id,active,joined_at,earnings"
        metadata = {}
        offset = 0
        page_size = 1000
        while True:
            page_headers = dict(headers)
            page_headers["Range-Unit"] = "items"
            page_headers["Range"] = "{}-{}".format(offset, offset + page_size - 1)
            async with session.get(url, headers=page_headers, timeout=10) as response:
                if response.status >= 400:
                    log.warning("[SB] middlemen metadata read failed with HTTP %s", response.status)
                    return None
                rows = await response.json(content_type=None)
                content_range = response.headers.get("Content-Range", "")
            if not isinstance(rows, list):
                return None
            for row in rows:
                if isinstance(row, dict) and row.get("discord_id") is not None:
                    metadata[str(row["discord_id"])] = row
            offset += len(rows)
            if not rows or len(rows) < page_size:
                if "/" not in content_range or content_range.rsplit("/", 1)[1] == "*":
                    break
                try:
                    if offset >= int(content_range.rsplit("/", 1)[1]):
                        break
                except ValueError:
                    break
            if offset == 0:
                break
        return metadata
    except Exception as error:
        log.warning("[SB] middlemen metadata read failed: %s", type(error).__name__)
        return None


async def sync_middlemen_for_guild(guild, roster=None):
    if roster is None:
        roster = {}
    mm_role_id = get_role_id(guild.id, "mm_role")
    role = guild.get_role(mm_role_id) if mm_role_id else None
    if role is None:
        return roster

    for member in tuple(role.members):
        if member.bot:
            continue
        user_id = str(member.id)
        joined_at = _mm_authorized_joined_at(guild.id, member.id)
        current = roster.get(user_id)
        if current is None or (not current["joined_at"] and joined_at):
            roster[user_id] = {"member": member, "joined_at": joined_at}
    return roster


async def reconcile_middlemen():
    existing_rows = await _load_middlemen_metadata()
    if existing_rows is None:
        return
    roster = {}
    scan_complete = True

    for guild in bot.guilds:
        mm_role_id = get_role_id(guild.id, "mm_role")
        if not mm_role_id:
            continue
        if guild.get_role(mm_role_id) is None:
            scan_complete = False
            log.warning("[SB] configured MM role missing in guild %s", guild.id)
            continue
        try:
            await asyncio.wait_for(guild.chunk(), timeout=20)
        except Exception as error:
            scan_complete = False
            log.warning("[SB] member chunk failed for guild %s: %s", guild.id, type(error).__name__)
        try:
            await sync_middlemen_for_guild(guild, roster)
        except Exception as error:
            scan_complete = False
            log.warning("[SB] MM roster scan failed for guild %s: %s", guild.id, type(error).__name__)

    for user_id, entry in roster.items():
        _queue_middleman_member(
            entry["member"],
            joined_at=entry["joined_at"],
            existing_rows=existing_rows,
        )

    if not scan_complete:
        return
    for user_id, row in existing_rows.items():
        if row.get("active") and user_id not in roster and user_id.isdigit():
            sb_patch("middlemen", "discord_id=eq." + user_id, {"active": False})


async def _middlemen_reconcile_worker():
    global _middlemen_reconcile_task, _middlemen_reconcile_requested
    try:
        while True:
            _middlemen_reconcile_requested = False
            try:
                await reconcile_middlemen()
            except Exception as error:
                log.warning("[SB] middlemen reconciliation failed: %s", type(error).__name__)
            if not _middlemen_reconcile_requested:
                return
    finally:
        _middlemen_reconcile_task = None


def schedule_middlemen_reconciliation():
    global _middlemen_reconcile_task, _middlemen_reconcile_requested
    if _middlemen_reconcile_task is not None and not _middlemen_reconcile_task.done():
        _middlemen_reconcile_requested = True
        return
    try:
        _middlemen_reconcile_task = asyncio.create_task(_middlemen_reconcile_worker())
    except RuntimeError:
        _middlemen_reconcile_task = None

async def _sb_worker():
    await bot.wait_until_ready()
    session = bot.http._HTTPClient__session
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": "Bearer " + SUPABASE_SERVICE_KEY,
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }
    while not bot.is_closed():
        try:
            table, data, method, query = await _sb_queue.get()
            url = SUPABASE_URL + "/rest/v1/" + table
            if query:
                url += "?" + query
            async with session.request(method, url, json=data, headers=headers, timeout=10) as r:
                if r.status >= 400:
                    body = await r.text()
                    log.warning("[SB] " + table + " " + str(r.status) + ": " + body[:200])
        except asyncio.CancelledError:
            return
        except Exception as e:
            log.warning("[SB] worker error: " + str(e))
        finally:
            try:
                _sb_queue.task_done()
            except Exception:
                pass

intents = discord.Intents.all()
bot = commands.AutoShardedBot(command_prefix=_get_prefix, intents=intents, help_command=None)

@bot.check
async def _guild_only(ctx):
    if ctx.guild is None:
        raise commands.NoPrivateMessage()
    return True

def cooldown(user_seconds=5, global_count=10, global_seconds=60, admins_bypass=True):
    def deco(func):
        @wraps(func)
        async def wrap(ctx, *a, **kw):
            if admins_bypass and has_perm(ctx.author, "administrator"):
                return await func(ctx, *a, **kw)
            now = time.time()
            cmd = func.__name__
            key = (ctx.author.id, cmd)
            last = _user_cooldowns.get(key, 0)
            if now - last < user_seconds:
                return
            bucket = [t for t in _global_cooldowns.get(cmd, []) if now - t < global_seconds]
            if len(bucket) >= global_count:
                _global_cooldowns[cmd] = bucket
                return
            _user_cooldowns[key] = now
            bucket.append(now)
            _global_cooldowns[cmd] = bucket
            return await func(ctx, *a, **kw)
        return wrap
    return deco

async def resolve_role(ctx, raw):
    if raw is None:
        return None
    raw = raw.strip().lstrip("<@&").rstrip(">")
    if raw.isdigit():
        r = ctx.guild.get_role(int(raw))
        if r:
            return r
    return discord.utils.get(ctx.guild.roles, name=raw)

async def resolve_channel(ctx, raw):
    if raw is None:
        return None
    raw = raw.strip().lstrip("<#").rstrip(">")
    if raw.isdigit():
        c = ctx.guild.get_channel(int(raw))
        if c:
            return c
    return discord.utils.get(ctx.guild.text_channels, name=raw)

async def resolve_member(guild, raw):
    raw = raw.strip()
    s = re.sub(r"[<@!>]", "", raw)
    if s.isdigit():
        m = guild.get_member(int(s))
        if m:
            return m, None
        try:
            return await guild.fetch_member(int(s)), None
        except discord.NotFound:
            return None, "No member with ID `" + s + "`."
        except discord.HTTPException:
            return None, "Lookup failed."
    for m in guild.members:
        if m.name.lower() == raw.lower() or m.display_name.lower() == raw.lower():
            return m, None
    return None, "No member named **" + raw + "**."

def parse_duration(raw):
    raw = raw.strip().lower()
    m = re.fullmatch(r"(\d+)(w|d|h|m|s)", raw)
    if m:
        v, u = int(m.group(1)), m.group(2)
        return v * {"w": 604800, "d": 86400, "h": 3600, "m": 60, "s": 1}[u]
    return int(raw) if raw.isdigit() else None

def fmt_dur(s):
    if s >= 604800: return str(s // 604800) + "w"
    if s >= 86400: return str(s // 86400) + "d"
    if s >= 3600: return str(s // 3600) + "h"
    if s >= 60: return str(s // 60) + "m"
    return str(s) + "s"

_log_create_lock = asyncio.Lock()

async def get_log_channel(guild, name):
    ch = discord.utils.get(guild.text_channels, name=name)
    if ch:
        return ch
    async with _log_create_lock:
        ch = discord.utils.get(guild.text_channels, name=name)
        if ch:
            return ch
        try:
            return await guild.create_text_channel(name)
        except Exception:
            return None

async def send_mod_log(guild, embed):
    ch = await get_log_channel(guild, "mod-logs")
    if ch:
        try:
            await ch.send(embed=embed)
        except Exception:
            pass

async def send_ticket_log(guild, embed, file=None):
    ch = await get_log_channel(guild, "ticket-logs")
    if ch:
        try:
            if file:
                await ch.send(embed=embed, file=file)
            else:
                await ch.send(embed=embed)
        except Exception:
            pass

async def send_vouch_log(guild, embed):
    ch = await get_log_channel(guild, "vouch-logs")
    if ch:
        try:
            await ch.send(embed=embed)
        except Exception:
            pass
async def save_transcript(channel, limit=1000):
    msgs = []
    try:
        async for m in channel.history(limit=limit, oldest_first=True):
            msgs.append(m)
    except Exception as e:
        log.warning("history: " + str(e))
    def esc(t):
        return html.escape(str(t or ""))
    rows = []
    for m in msgs:
        color = "#5865F2"
        if isinstance(m.author, discord.Member) and m.author.color.value:
            color = "#{:06x}".format(m.author.color.value)
        att = ""
        for a in m.attachments:
            att += '<div class="att"><a href="' + esc(a.url) + '">' + esc(a.filename) + '</a></div>'
        emb = ""
        for e in m.embeds:
            t = '<div class="emb-title">' + esc(e.title) + '</div>' if e.title else ""
            d = '<div class="emb-desc">' + esc(e.description).replace("\n", "<br/>") + '</div>' if e.description else ""
            f = "".join('<div class="emb-field"><b>' + esc(x.name) + '</b><br/>' + esc(x.value).replace("\n", "<br/>") + '</div>' for x in e.fields)
            emb += '<div class="emb">' + t + d + f + '</div>'
        c = esc(m.content).replace("\n", "<br/>") if m.content else ""
        av = m.author.display_avatar.url if hasattr(m.author, "display_avatar") else ""
        ts = m.created_at.strftime("%Y-%m-%d %H:%M:%S")
        rows.append('<div class="msg"><img class="avatar" src="' + esc(av) + '"/><div class="body"><div class="meta"><span class="author" style="color:' + color + '">' + esc(m.author.display_name) + '</span><span class="time">' + ts + '</span></div><div class="content">' + c + '</div>' + att + emb + '</div></div>')
    guild = channel.guild
    icon = guild.icon.url if guild.icon else ""
    title = "Transcript — #" + channel.name
    n = len(msgs)
    doc = '<!DOCTYPE html><html><head><meta charset="utf-8"/><title>' + esc(title) + '</title>'
    doc += '<style>body{background:#1e1f22;color:#dbdee1;font-family:sans-serif;margin:0}'
    doc += 'header{display:flex;gap:12px;padding:20px;background:#2b2d31;align-items:center}'
    doc += 'header img{width:40px;height:40px;border-radius:50%}header h1{font-size:18px;margin:0}'
    doc += 'main{padding:16px 24px}.msg{display:flex;gap:12px;padding:8px 0;border-bottom:1px solid #232428}'
    doc += '.avatar{width:40px;height:40px;border-radius:50%}.body{flex:1}'
    doc += '.meta{display:flex;gap:8px;margin-bottom:4px}.author{font-weight:600}.time{font-size:11px;color:#6d6f78;margin-left:auto}'
    doc += '.content{white-space:pre-wrap}.emb{border-left:4px solid #5865F2;background:#2b2d31;padding:12px;border-radius:4px;margin-top:6px}'
    doc += '.emb-title{font-weight:600}.emb-desc{font-size:14px}.att a{color:#00a8fc}'
    doc += '</style></head><body>'
    doc += '<header><img src="' + esc(icon) + '"/><div><h1>' + esc(title) + '</h1><p>' + esc(guild.name) + ' · ' + str(n) + ' messages</p></div></header>'
    doc += '<main>' + "".join(rows) + '</main></body></html>'
    return doc.encode("utf-8"), n

def is_mm_ticket(ch):
    return ch.name.startswith(("mm-", "claimed-mm-"))

def is_ticket_channel(ch):
    """Return True for any currently-open ticket, even if its channel was renamed.

    Ticket identity is stored in ticket_log, so channel-name prefixes are only a
    fallback for legacy/partially-migrated tickets.  This prevents `$close` (and
    other ticket commands) from incorrectly reporting that a renamed/hold ticket
    is outside a ticket.
    """
    cached = _ticket_channel_cache.get(ch.id)
    if cached is True:
        return True

    # Source of truth: an open ticket row.  Check this BEFORE looking at the name
    # so `$rename` / `$hold` cannot make a real ticket invisible to the commands.
    try:
        ok = _get_row(
            "SELECT 1 FROM ticket_log WHERE channel_id=? AND closed_at IS NULL",
            (ch.id,),
        ) is not None
        if ok:
            _ticket_channel_cache[ch.id] = True
            return True
    except Exception:
        pass

    # Fallback for older tickets that may not have a ticket_log row yet.
    named_ticket = any(
        ch.name.startswith(p)
        for p in ("ticket-", "mm-", "claimed-ticket-", "claimed-mm-")
    )
    in_ticket_category = bool(
        getattr(getattr(ch, "category", None), "name", "").strip().lower() == "tickets"
    )
    ok = named_ticket or in_ticket_category
    _ticket_channel_cache[ch.id] = ok
    return ok

async def get_ticket_category(guild):
    saved = get_role_id(guild.id, "ticket_cat_position")
    cat = discord.utils.get(guild.categories, name="Tickets")
    if cat is None:
        try:
            cat = await guild.create_category("Tickets", position=saved or 0)
        except Exception:
            cat = await guild.create_category("Tickets")
    return cat

async def cleanup_ticket_category(guild):
    cat = discord.utils.get(guild.categories, name="Tickets")
    if cat is None or [ch for ch in cat.channels]:
        return
    set_role_id(guild.id, "ticket_cat_position", cat.position)
    try:
        await cat.delete(reason="All tickets closed")
    except Exception:
        pass

def build_mm_ticket_embed(guild, channel, opener, trader, trader_text, giving_one, giving_two, claimed_by=None):
    """Clean ticket embed styled like the original ticket panel, with newer trade/claim features."""
    trader_name = trader.mention if trader else (trader_text or "Not added yet")
    trader_id = str(trader.id) if trader else "Not added yet"
    claimer = guild.get_member(claimed_by) if claimed_by else None

    if claimer:
        status = "🟢 **Claimed**"
        mm_line = claimer.mention
        accent = C["ok"]
    else:
        status = "🟡 **Open**"
        mm_line = "A middleman will join shortly."
        accent = C["info"]

    def value(text):
        text = (text or "Not specified").strip()
        return f"`{text}`"

    if trader:
        other_trader_block = f"{trader_name}\n`{trader_id}`"
    else:
        other_trader_block = (
            f"{trader_name}\n"
            "*Not added — a middleman can add them with `$adduser`*"
        )

    e = discord.Embed(
        title="📋  Middleman Ticket",
        description=(
            "Your MM ticket is open.\n\n"
            "A middleman will join shortly.\n"
            "Keep this channel open until your trade is complete."
        ),
        color=accent,
    )

    icon = getattr(guild.icon, "url", None)
    if icon:
        e.set_thumbnail(url=icon)

    e.add_field(
        name="Ticket",
        value=f"`{channel.name}`\n{channel.mention}",
        inline=True,
    )
    e.add_field(
        name="User",
        value=f"{opener.mention}\n`{opener.id}`",
        inline=True,
    )
    e.add_field(
        name="Status",
        value=status,
        inline=True,
    )

    e.add_field(name="📋  Ticket Details", value="\u200b", inline=False)
    e.add_field(
        name="Who is the other trader?",
        value=other_trader_block,
        inline=False,
    )
    e.add_field(
        name="What is the trade?",
        value=(
            f"**{opener.display_name} is giving:** {value(giving_one)}\n"
            f"**Other trader is giving:** {value(giving_two)}"
        ),
        inline=False,
    )

    e.add_field(
        name="🛡️  Middleman",
        value=mm_line,
        inline=False,
    )
    e.add_field(
        name="⚠️  Important",
        value=(
            "Do not send items or payment until the assigned MM tells you to.\n"
            "Only follow instructions from the MM in this ticket."
        ),
        inline=False,
    )

    e.set_footer(text=f"{guild.name} | MM Ticket")
    return e

async def refresh_mm_ticket_embed(channel, guild):
    row = get_mm_ticket_details(channel.id)
    if not row:
        return
    opener = guild.get_member(row["opener_id"])
    if not opener:
        return
    trader = guild.get_member(row["trader_id"]) if row["trader_id"] else None
    claimed_by = get_claimer(channel.id)
    embed = build_mm_ticket_embed(
        guild, channel, opener, trader, row["trader_text"],
        row["giving_one"], row["giving_two"], claimed_by=claimed_by
    )
    try:
        async for msg in channel.history(limit=20):
            if msg.author.id == guild.me.id and msg.embeds:
                if msg.embeds[0].title in ("✦ MM2 TRADES", "📋  Middleman Ticket"):
                    await msg.edit(embed=embed, view=TicketControlView(claimed=claimed_by is not None))
                    return
    except Exception:
        pass

async def repair_ticket_role_access(guild, role_id=None, *, always_visible=False):
    """Repair staff-role overwrites on every currently open ticket."""
    if guild is None:
        return 0
    if role_id is None:
        role_id = get_role_id(guild.id, "ticket_admin_role")
    if not role_id:
        return 0
    role = guild.get_role(role_id)
    if role is None:
        return 0

    try:
        with _db() as con:
            ticket_rows = con.execute(
                "SELECT channel_id FROM ticket_log WHERE guild_id=? AND closed_at IS NULL",
                (guild.id,)
            ).fetchall()
    except Exception:
        return 0

    changed = 0
    for row in ticket_rows:
        ch = guild.get_channel(row["channel_id"])
        if ch is None or not isinstance(ch, discord.TextChannel):
            continue
        try:
            ow = ch.overwrites_for(role)
            needs = (
                ow.view_channel is not True or
                ow.send_messages is not True or
                ow.read_message_history is not True
            )
            if not needs and always_visible:
                continue
            if needs:
                await ch.set_permissions(
                    role,
                    view_channel=True,
                    read_messages=True,
                    send_messages=True,
                    read_message_history=True,
                    add_reactions=True,
                    attach_files=True,
                    embed_links=True,
                    reason="Repair configured ticket staff role access",
                )
                changed += 1
        except Exception as e:
            log.warning("ticket role repair failed in %s: %s", getattr(ch, "id", "?"), e)
    return changed

async def repair_all_open_ticket_permissions(guild):
    """Keep ticket admin/owner access and synchronize MM/support access with claim state."""
    if guild is None:
        return
    try:
        with _db() as con:
            rows = con.execute(
                "SELECT channel_id FROM ticket_log WHERE guild_id=? AND closed_at IS NULL",
                (guild.id,)
            ).fetchall()
    except Exception:
        return

    mm_rid = get_role_id(guild.id, "mm_role")
    sup_rid = get_role_id(guild.id, "support_role")
    ticket_admin_rid = get_role_id(guild.id, "ticket_admin_role")
    owner_rid = get_role_id(guild.id, "owner_role")
    protected_ids = {rid for rid in (ticket_admin_rid, owner_rid) if rid}

    for row in rows:
        ch = guild.get_channel(row["channel_id"])
        if ch is None or not isinstance(ch, discord.TextChannel):
            continue
        claimed = get_claimer(ch.id) is not None
        try:
            if ticket_admin_rid:
                r = guild.get_role(ticket_admin_rid)
                if r:
                    ow = ch.overwrites_for(r)
                    if ow.view_channel is not True or ow.send_messages is not True:
                        await ch.set_permissions(
                            r, view_channel=True, read_messages=True, send_messages=True,
                            read_message_history=True, add_reactions=True, attach_files=True,
                            embed_links=True, reason="Repair Ticket Admin ticket access")

            if owner_rid:
                r = guild.get_role(owner_rid)
                if r:
                    ow = ch.overwrites_for(r)
                    if ow.view_channel is not True or ow.send_messages is not True:
                        await ch.set_permissions(
                            r, view_channel=True, read_messages=True, send_messages=True,
                            read_message_history=True, reason="Repair Owner ticket access")

            for rid in (mm_rid, sup_rid):
                if not rid or rid in protected_ids:
                    continue
                r = guild.get_role(rid)
                if not r:
                    continue
                desired = not claimed
                ow = ch.overwrites_for(r)
                current = ow.view_channel
                if current is desired:
                    continue
                await ch.set_permissions(
                    r,
                    view_channel=desired,
                    read_messages=desired,
                    send_messages=desired,
                    reason="Synchronize ticket staff visibility",
                )

            claimer_id = get_claimer(ch.id)
            if claimer_id:
                member = guild.get_member(claimer_id)
                if member:
                    await ch.set_permissions(
                        member,
                        view_channel=True, read_messages=True, send_messages=True,
                        read_message_history=True, add_reactions=True, attach_files=True,
                        embed_links=True, reason="Repair claimed ticket access")
        except Exception as e:
            log.warning("ticket permission repair failed in %s: %s", getattr(ch, "id", "?"), e)

async def create_ticket(guild, user, kind, trader_text=None, giving_one=None, giving_two=None):
    count = open_ticket_count(guild.id, user.id)
    if count >= MAX_OPEN_TICKETS_PER_USER:
        return None, "You already have **{} open tickets**.\nClose one before opening another.".format(count)
    cat = await get_ticket_category(guild)
    pre = "mm" if kind == "mm" else "ticket"
    safe = re.sub(r"[^a-z0-9-]", "", user.name.lower().replace(" ", "-"))
    name = pre + "-" + (safe or str(user.id))
    mm_rid = get_role_id(guild.id, "mm_role")
    sup_rid = get_role_id(guild.id, "support_role")
    ticket_admin_rid = get_role_id(guild.id, "ticket_admin_role")
    owner_rid = get_role_id(guild.id, "owner_role")
    ow = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        user: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, read_message_history=True),
        guild.me: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, read_message_history=True, manage_channels=True, manage_messages=True),
    }
    for role in guild.roles:
        if role.permissions.administrator:
            ow[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
    for rid in (mm_rid, sup_rid, ticket_admin_rid, owner_rid):
        if rid:
            r = guild.get_role(rid)
            if r:
                ow[r] = discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, read_message_history=True)
    trader = None
    if trader_text:
        trader, _err = await resolve_member(guild, trader_text)
        if trader and trader.id == user.id:
            trader = None
        if trader:
            ow[trader] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
    channel = await guild.create_text_channel(name, category=cat, overwrites=ow)
    pings = [user.mention]
    if kind == "mm" and mm_rid:
        pings.append("<@&" + str(mm_rid) + ">")
    if kind == "mm":
        e = build_mm_ticket_embed(guild, channel, user, trader, trader_text, giving_one, giving_two)
    else:
        e = discord.Embed(
            title="Support Ticket",
            color=C["neutral"],
            description="Welcome " + user.mention + ".\n\nA staff member will assist you shortly.\nUse the buttons or `$close`."
        )
        e.set_footer(text="Ticket System")
    await channel.send(content=" ".join(pings), embed=e, view=TicketControlView(claimed=False))
    log_ticket_open(guild.id, channel.id, user.id, kind)
    if kind == "mm":
        trader_id = trader.id if trader else None
        _exec(
            "INSERT OR REPLACE INTO mm_ticket_details(channel_id,guild_id,opener_id,trader_id,trader_text,giving_one,giving_two,confirmed_one,confirmed_two,declined_by,confirmation_message_id) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (channel.id, guild.id, user.id, trader_id, trader_text, giving_one, giving_two, 0, 0, None, None)
        )
    await send_ticket_log(
        guild,
        discord.Embed(
            title="Ticket Created",
            color=C["ok"],
            description="User: " + user.mention + "\nChannel: " + channel.mention + "\nType: `" + kind + "`"
        )
    )
    return channel, None

def get_mm_ticket_details(channel_id):
    return _get_row("SELECT * FROM mm_ticket_details WHERE channel_id=?", (channel_id,))

def set_mm_confirmation_message(channel_id, message_id):
    _exec("UPDATE mm_ticket_details SET confirmation_message_id=? WHERE channel_id=?", (message_id, channel_id))

def delete_mm_ticket_details(channel_id):
    _exec("DELETE FROM mm_ticket_details WHERE channel_id=?", (channel_id,))

async def close_ticket(channel, closer, guild, silent=False, system=False):
    if channel.guild.id != guild.id:
        return
    mm_rid = get_role_id(guild.id, "mm_role")
    owner_rid = get_role_id(guild.id, "owner_role")
    sup_rid = get_role_id(guild.id, "support_role")
    ticket_admin_rid = get_role_id(guild.id, "ticket_admin_role")
    is_support_ticket = channel.name.startswith(("ticket-", "claimed-ticket-"))
    claimer_id = get_claimer(channel.id)
    is_claimer = claimer_id is not None and closer.id == claimer_id
    can_close = system or has_perm(closer, "administrator") or is_ticket_admin(closer)
    if not can_close and owner_rid and member_has_role(closer, owner_rid):
        can_close = True
    # Any MM who currently has channel access can close the ticket, even if another MM claimed it.
    if not can_close and mm_rid and member_has_role(closer, mm_rid):
        try:
            can_close = bool(channel.permissions_for(closer).view_channel)
        except Exception:
            can_close = False
    if not can_close:
        if claimer_id is not None:
            can_close = is_claimer
        else:
            if is_support_ticket and sup_rid and member_has_role(closer, sup_rid):
                can_close = True
    if not can_close:
        if not silent:
            await channel.send(embed=discord.Embed(description="Only an accessible MM, Ticket Admin, Owner, or an administrator can close this ticket.", color=C["err"]))
        return
    if is_automm_channel(channel):
        sim = _am_sim_tasks.pop(channel.id, None)
        if sim and not sim.done():
            sim.cancel()
        am_del(channel.id)
    try:
        _exec("DELETE FROM askuser_state WHERE channel_id=?", (channel.id,))
    except Exception:
        pass
    try:
        delete_mm_ticket_details(channel.id)
    except Exception:
        pass
    try:
        transcript, count = await save_transcript(channel, limit=300)
    except Exception as e:
        log.warning("transcript: " + str(e))
        transcript, count = b"transcript unavailable", 0
    row = log_ticket_close(channel.id)
    opener = guild.get_member(row["opener_id"]) if row else None
    fname = "transcript-" + channel.name + ".html"
    async def _send_opener():
        if not opener:
            return
        try:
            await opener.send(
                content="Transcript of your ticket in **" + guild.name + "**:",
                file=discord.File(fp=io.BytesIO(transcript), filename=fname),
            )
        except Exception:
            pass

    async def _send_log():
        log_ch = await get_log_channel(guild, "ticket-logs")
        if not log_ch:
            return
        try:
            await log_ch.send(
                embed=discord.Embed(
                    title="Ticket Closed",
                    color=C["err"],
                    description="Closed by " + closer.mention + "\nChannel: `" + channel.name + "`\nMessages: " + str(count),
                ),
                file=discord.File(fp=io.BytesIO(transcript), filename=fname),
            )
        except Exception:
            pass

    # Transcripts go to ticket-logs only. No DM to opener.
    await _send_log()
    try:
        _exec("DELETE FROM disputes WHERE channel_id=?", (channel.id,))
    except Exception:
        pass
    remove_claimer(channel.id)
    if not silent:
        try:
            await channel.send(embed=discord.Embed(description="Ticket closed. Deleting in 5 seconds.", color=C["err"]))
        except Exception:
            pass
    await asyncio.sleep(5)
    try:
        await channel.delete()
    except Exception:
        pass
    _channel_locks.pop(channel.id, None)
    _claim_action_time.pop(channel.id, None)
    try:
        _ticket_channel_cache.pop(channel.id, None)
    except Exception:
        pass
    await cleanup_ticket_category(guild)

async def _auto_close_mercy_ticket(guild_id, channel_id, delay=0):
    """Close the ticket automatically when the linked Mercy flow is finished."""
    task_key = channel_id
    current = _mercy_ticket_close_tasks.get(task_key)
    if current and not current.done():
        return

    async def _runner():
        try:
            if delay > 0:
                await asyncio.sleep(delay)
            channel = bot.get_channel(channel_id)
            if channel is None:
                try:
                    channel = await bot.fetch_channel(channel_id)
                except Exception:
                    return
            guild = bot.get_guild(guild_id)
            if guild is None or getattr(channel, "guild", None) is None:
                return
            if channel.guild.id != guild_id:
                return
            if not is_ticket_channel(channel):
                return
            closer = guild.me or guild.get_member(bot.user.id)
            if closer is None:
                return
            await close_ticket(channel, closer, guild, system=True)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            log.warning("mercy ticket auto-close: " + str(e))
        finally:
            _mercy_ticket_close_tasks.pop(task_key, None)

    _mercy_ticket_close_tasks[task_key] = asyncio.create_task(_runner())


async def reserve_ticket_claim(channel, claimer, guild):
    """Atomically reserve an unclaimed ticket for a claimer."""
    async with _chan_lock(channel.id):
        if channel.name.startswith("claimed-") or get_claimer(channel.id) is not None:
            return False
        set_claimer(channel.id, claimer.id)
        return True

async def finish_claim_ticket(channel, claimer, guild):
    """Apply slow permission/name/embed updates after the claim is acknowledged."""
    if channel.guild.id != guild.id:
        return

    mm_rid = get_role_id(guild.id, "mm_role")
    sup_rid = get_role_id(guild.id, "support_role")
    ticket_admin_rid = get_role_id(guild.id, "ticket_admin_role")
    owner_rid = get_role_id(guild.id, "owner_role")
    protected_ids = {rid for rid in (ticket_admin_rid, owner_rid) if rid}

    base = channel.name
    for prefix in ("claimed-mm-", "claimed-ticket-", "mm-", "ticket-"):
        if base.startswith(prefix):
            base = base[len(prefix):]
            break
    kp = "claimed-mm" if is_mm_ticket(channel) else "claimed-ticket"

    # Rename in the background.
    try:
        await channel.edit(name=kp + "-" + base, reason="Ticket claimed")
    except Exception:
        pass

    # The claimer always keeps access.
    try:
        await channel.set_permissions(
            claimer,
            view_channel=True, read_messages=True, send_messages=True,
            read_message_history=True, add_reactions=True, attach_files=True,
            embed_links=True, reason="Ticket claimer access")
    except Exception:
        pass

    # Hide the staff pools from a claimed ticket, but NEVER hide Ticket Admin/Owner.
    for rid in (mm_rid, sup_rid):
        if not rid or rid in protected_ids:
            continue
        role = guild.get_role(rid)
        if role:
            try:
                await channel.set_permissions(
                    role, view_channel=False, read_messages=False, send_messages=False,
                    read_message_history=False, reason="Hide unassigned staff from claimed ticket")
            except Exception:
                pass

    # Ticket Admin and Owner always retain access. This is intentionally sequential
    # so an overlapping role configuration cannot race the deny calls above.
    for rid in (ticket_admin_rid, owner_rid):
        if not rid:
            continue
        role = guild.get_role(rid)
        if role:
            try:
                await channel.set_permissions(
                    role, view_channel=True, read_messages=True, send_messages=True,
                    read_message_history=True, add_reactions=True, attach_files=True,
                    embed_links=True, reason="Preserve privileged ticket access")
            except Exception:
                pass

    # Keep real Discord Administrators visible as well.
    admin_roles = [
        role for role in guild.roles
        if role.permissions.administrator and not role.managed and role.id not in protected_ids
    ]
    if admin_roles:
        async def _grant_admin(role):
            try:
                await channel.set_permissions(
                    role, view_channel=True, read_messages=True, send_messages=True,
                    read_message_history=True, reason="Preserve administrator ticket access")
            except Exception:
                pass
        await asyncio.gather(*[_grant_admin(role) for role in admin_roles])

    try:
        await refresh_mm_ticket_embed(channel, guild)
    except Exception:
        pass

async def claim_ticket(channel, claimer, guild, *, interaction=None):
    ok = await reserve_ticket_claim(channel, claimer, guild)
    if not ok:
        existing = get_claimer(channel.id)
        if existing == getattr(claimer, "id", None):
            return
        who = "<@{}>".format(existing) if existing else "another user"
        message = discord.Embed(
            description="This ticket has already been claimed by " + who + ".",
            color=C["err"])
        if interaction is not None:
            try:
                if not interaction.response.is_done():
                    return await interaction.response.send_message(embed=message, ephemeral=True)
                return await interaction.followup.send(embed=message, ephemeral=True)
            except Exception:
                return None
        return await channel.send(embed=message, delete_after=5)

    message = discord.Embed(
        description="🟢 {} claimed this ticket.".format(claimer.mention),
        color=C["ok"])

    if interaction is not None:
        try:
            if not interaction.response.is_done():
                await interaction.response.edit_message(view=TicketControlView(claimed=True))
            else:
                await interaction.followup.send(embed=message, ephemeral=True)
        except Exception:
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(embed=message)
            except Exception:
                pass
        asyncio.create_task(channel.send(embed=message))
    else:
        try:
            await channel.send(embed=message)
        except Exception:
            pass

    # DM the opener.
    row = get_mm_ticket_details(channel.id)
    if row:
        opener = guild.get_member(int(row["opener_id"]))
        if opener and opener.id != claimer.id:
            async def _dm_opener():
                try:
                    await opener.send(embed=discord.Embed(
                        title="Your ticket was claimed",
                        description="{} is now handling your ticket in **{}**.".format(claimer.display_name, guild.name),
                        color=C["ok"]))
                except Exception:
                    pass
            asyncio.create_task(_dm_opener())

    try:
        await send_ticket_log(guild, discord.Embed(
            title="Ticket Claimed",
            color=C["ok"],
            description="By {} in {}\nChannel: `{}`".format(claimer.mention, channel.mention, channel.name)))
    except Exception:
        pass

    asyncio.create_task(finish_claim_ticket(channel, claimer, guild))
async def unclaim_ticket(channel, unclaimer, guild, *, interaction=None):
    existing = get_claimer(channel.id)
    if existing is None:
        message = discord.Embed(description="This ticket is not currently claimed.", color=C["warn"])
        if interaction is not None:
            try:
                await interaction.response.edit_message(view=TicketControlView(claimed=False))
            except Exception:
                pass
            try:
                if not interaction.response.is_done():
                    return await interaction.response.send_message(embed=message, ephemeral=True)
                return await interaction.followup.send(embed=message, ephemeral=True)
            except Exception:
                return None
        return await channel.send(embed=message)
    if unclaimer.id != existing and not (has_perm(unclaimer, "administrator") or is_ticket_admin(unclaimer)):
        message = discord.Embed(
            description="Only the claimer or a Ticket Admin can unclaim this ticket.",
            color=C["err"])
        if interaction is not None:
            return await interaction.response.send_message(embed=message, ephemeral=True)
        return await channel.send(embed=message)

    async with _chan_lock(channel.id):
        if get_claimer(channel.id) != existing:
            message = discord.Embed(description="This ticket was already unclaimed.", color=C["err"])
            if interaction is not None:
                return await interaction.response.send_message(embed=message, ephemeral=True)
            return await channel.send(embed=message, delete_after=5)
        remove_claimer(channel.id)

    message = discord.Embed(
        description="🔓 {} unclaimed this ticket.".format(unclaimer.mention),
        color=C["warn"])

    if interaction is not None:
        try:
            if not interaction.response.is_done():
                await interaction.response.edit_message(view=TicketControlView(claimed=False))
            else:
                await interaction.followup.send(embed=message, ephemeral=True)
        except Exception:
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(embed=message)
            except Exception:
                pass
        asyncio.create_task(channel.send(embed=message))
    else:
        try:
            await channel.send(embed=message)
        except Exception:
            pass

    try:
        await send_ticket_log(guild, discord.Embed(
            title="Ticket Unclaimed",
            color=C["warn"],
            description="By {} in {}\nChannel: `{}`".format(unclaimer.mention, channel.mention, channel.name)))
    except Exception:
        pass

    asyncio.create_task(finish_unclaim_ticket(channel, unclaimer, existing, guild))
async def transfer_ticket(channel, old_claimer, new_claimer, guild, *, interaction=None):
    existing = get_claimer(channel.id)
    if existing is None:
        msg = discord.Embed(description="This ticket is not claimed.", color=C["warn"])
        if interaction is not None:
            return await interaction.response.send_message(embed=msg, ephemeral=True)
        return await channel.send(embed=msg)
    if existing != old_claimer.id and not (has_perm(old_claimer, "administrator") or is_ticket_admin(old_claimer)):
        msg = discord.Embed(description="Only the claimer or a Ticket Admin can transfer.", color=C["err"])
        if interaction is not None:
            return await interaction.response.send_message(embed=msg, ephemeral=True)
        return await channel.send(embed=msg)
    if new_claimer.id == existing:
        msg = discord.Embed(description="You already own this ticket.", color=C["warn"])
        if interaction is not None:
            return await interaction.response.send_message(embed=msg, ephemeral=True)
        return await channel.send(embed=msg)
    mm_rid = get_role_id(guild.id, "mm_role")
    if not (member_has_role(new_claimer, mm_rid) or has_perm(new_claimer, "administrator")):
        msg = discord.Embed(description=new_claimer.mention + " is not an MM.", color=C["err"])
        if interaction is not None:
            return await interaction.response.send_message(embed=msg, ephemeral=True)
        return await channel.send(embed=msg)

    async with _chan_lock(channel.id):
        if get_claimer(channel.id) != existing:
            msg = discord.Embed(description="The ticket's claim state changed. Try again.", color=C["err"])
            if interaction is not None:
                return await interaction.response.send_message(embed=msg, ephemeral=True)
            return await channel.send(embed=msg)
        set_claimer(channel.id, new_claimer.id)

    old_m = guild.get_member(existing)
    if old_m:
        try:
            await channel.set_permissions(old_m, overwrite=None, reason="Ticket transferred")
        except Exception:
            pass
    try:
        await channel.set_permissions(new_claimer,
            view_channel=True, read_messages=True, send_messages=True,
            read_message_history=True, add_reactions=True, attach_files=True,
            embed_links=True, reason="Ticket transferred")
    except Exception:
        pass

    announce = discord.Embed(
        title="MM Transferred",
        description="<@{}> is busy, so <@{}> will handle this ticket and be your middleman from here on.".format(existing, new_claimer.id),
        color=C["info"])
    announce.set_footer(text="Please follow the new MM's instructions.")

    if interaction is not None:
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=announce)
            else:
                await interaction.followup.send(embed=announce)
        except Exception:
            pass
    else:
        try:
            await channel.send(embed=announce)
        except Exception:
            pass

    try:
        await send_ticket_log(guild, discord.Embed(
            title="Ticket Transferred", color=C["info"],
            description="From <@{}> to <@{}>\nChannel: `{}`".format(existing, new_claimer.id, channel.name)))
    except Exception:
        pass

    row = get_mm_ticket_details(channel.id)
    if row:
        opener = guild.get_member(int(row["opener_id"]))
        if opener and opener.id not in (existing, new_claimer.id):
            async def _dm():
                try:
                    await opener.send(embed=discord.Embed(
                        title="Your middleman changed",
                        description="<@{}> is busy, so <@{}> will now handle your ticket in **{}**.".format(existing, new_claimer.id, guild.name),
                        color=C["info"]))
                except Exception:
                    pass
            asyncio.create_task(_dm())

    try:
        await refresh_mm_ticket_embed(channel, guild)
    except Exception:
        pass

async def finish_unclaim_ticket(channel, unclaimer, existing, guild):
    """Slow Discord-side unclaim cleanup, deliberately kept off the interaction response path."""
    async with _chan_lock(channel.id):
        name = channel.name
        if name.startswith("claimed-mm-"):
            new = "mm-" + name[len("claimed-mm-"):]
        elif name.startswith("claimed-ticket-"):
            new = "ticket-" + name[len("claimed-ticket-"):]
        else:
            new = name

        mm_rid = get_role_id(guild.id, "mm_role")
        sup_rid = get_role_id(guild.id, "support_role")
        ticket_admin_rid = get_role_id(guild.id, "ticket_admin_role")
        owner_rid = get_role_id(guild.id, "owner_role")

        try:
            await channel.edit(name=new, reason="Ticket unclaimed")
        except Exception:
            pass

        for rid in (mm_rid, sup_rid):
            if not rid:
                continue
            role = guild.get_role(rid)
            if role:
                try:
                    await channel.set_permissions(
                        role, view_channel=True, read_messages=True, send_messages=True,
                        read_message_history=True, reason="Restore staff access after unclaim")
                except Exception:
                    pass

        for rid in (ticket_admin_rid, owner_rid):
            if not rid:
                continue
            role = guild.get_role(rid)
            if role:
                try:
                    await channel.set_permissions(
                        role, view_channel=True, read_messages=True, send_messages=True,
                        read_message_history=True, add_reactions=True, attach_files=True,
                        embed_links=True, reason="Preserve privileged ticket access")
                except Exception:
                    pass

        m = guild.get_member(existing)
        if m:
            try:
                await channel.set_permissions(m, overwrite=None, reason="Remove former claimer overwrite")
            except Exception:
                pass

    try:
        await refresh_mm_ticket_embed(channel, guild)
    except Exception:
        pass

class ConfirmView(ui.View):
    def __init__(self, author_id, on_confirm, timeout=30):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.on_confirm = on_confirm
    async def interaction_check(self, i):
        return i.user.id == self.author_id
    @ui.button(label="Confirm", style=discord.ButtonStyle.danger)
    async def confirm(self, i, b):
        for c in self.children:
            c.disabled = True
        await i.response.edit_message(view=self)
        await self.on_confirm(i)
    @ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, i, b):
        for c in self.children:
            c.disabled = True
        await i.response.edit_message(view=self)

class InfoAckView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @ui.button(label="Understood", style=discord.ButtonStyle.success, custom_id="info_ack_yes")
    async def yes(self, i, b):
        text = "has read and understood."
        try:
            emb = i.message.embeds[0] if i.message.embeds else None
            title = (emb.title or "").lower() if emb else ""
            if "middleman info" in title or "middleman service" in title:
                text = "has understood how an MM works."
            elif "fee" in title:
                text = "has read and understood the MM fee policy."
            elif "cross-trade" in title:
                text = "has read and understood the cross-trade guide."
            elif "accountability" in title:
                text = "has read and understood the MM policy."
            elif "server rules" in title:
                text = "has read and understood the server rules."
            elif "guidelines" in title:
                text = "has read and understood the trading guidelines."
            elif "marketplace" in title:
                text = "has read and understood the marketplace rules."
            elif "middleman terms" in title:
                text = "has read and understood the MM ToS."
            elif "support" in title:
                text = "has read and understood the support ToS."
            elif "hitting" in title or "guide" in title:
                text = "has read and understood the guide."
        except Exception:
            pass
        await i.response.send_message(
            embed=discord.Embed(description=i.user.mention + " " + text, color=C["ok"]))
    @ui.button(label="Not Understood", style=discord.ButtonStyle.danger, custom_id="info_ack_no")
    async def no(self, i, b):
        await i.response.send_message(
            embed=discord.Embed(description="Re-read the message — or open a support ticket.", color=C["warn"]),
            ephemeral=True)

class RecruitApprovalView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @ui.button(label="Accept", style=discord.ButtonStyle.green, emoji="<a:Tick_Yes:1529751821227393084>", custom_id="recruit_accept")
    async def accept(self, i, b):
        owner_rid = get_role_id(i.guild.id, "owner_role")
        if not has_perm(i.user, "administrator") and not member_has_role(i.user, owner_rid):
            return await i.response.send_message(embed=discord.Embed(description="Only Owner.", color=C["err"]), ephemeral=True)
        row = get_pending_recruit(i.message.id)
        if not row:
            return await i.response.send_message(embed=discord.Embed(description="Already processed.", color=C["err"]), ephemeral=True)
        gid, rec_id, ruid, img = row
        await i.response.defer()
        ch_id = get_role_id(i.guild.id, "recruits_channel")
        ch = i.guild.get_channel(ch_id) if ch_id else discord.utils.get(i.guild.text_channels, name="recruits")
        if ch is None:
            ch = await i.guild.create_text_channel("recruits")
        rec = i.guild.get_member(rec_id)
        e = discord.Embed(title="Recruit Accepted", color=C["ok"])
        e.add_field(name="Recruiter", value=rec.mention if rec else "<@" + str(rec_id) + ">", inline=True)
        e.add_field(name="Approved by", value=i.user.mention, inline=True)
        if ruid:
            e.add_field(name="Recruit", value="<@" + str(ruid) + ">", inline=True)
        if img:
            e.set_image(url=img)
        await ch.send(embed=e)
        add_recruit(gid, rec_id, ruid or i.message.id)
        del_pending_recruit(i.message.id)
        for c in self.children:
            c.disabled = True
        emb = i.message.embeds[0]
        emb.color = C["ok"]
        emb.set_footer(text="Accepted by " + i.user.display_name)
        await i.message.edit(embed=emb, view=self)
    @ui.button(label="Reject", style=discord.ButtonStyle.danger, emoji="<a:checkmarkcross:1542113944704000011>", custom_id="recruit_reject")
    async def reject(self, i, b):
        owner_rid = get_role_id(i.guild.id, "owner_role")
        if not has_perm(i.user, "administrator") and not member_has_role(i.user, owner_rid):
            return await i.response.send_message(embed=discord.Embed(description="Only Owner.", color=C["err"]), ephemeral=True)
        row = get_pending_recruit(i.message.id)
        if not row:
            return await i.response.send_message(embed=discord.Embed(description="Already processed.", color=C["err"]), ephemeral=True)
        await i.response.defer()
        del_pending_recruit(i.message.id)
        for c in self.children:
            c.disabled = True
        emb = i.message.embeds[0]
        emb.color = C["err"]
        emb.set_footer(text="Rejected by " + i.user.display_name)
        await i.message.edit(embed=emb, view=self)

class MercyDeclineConfirmView(ui.View):
    def __init__(self, target_id):
        super().__init__(timeout=60)
        self.target_id = target_id
    @ui.button(label="Ban me", style=discord.ButtonStyle.danger)
    async def yes(self, i, b):
        if i.user.id != self.target_id:
            return await i.response.send_message(embed=discord.Embed(description="Not your offer.", color=C["err"]), ephemeral=True)
        await i.response.defer()
        for c in self.children:
            c.disabled = True
        await i.message.edit(view=self)
        try:
            _exec("DELETE FROM mercy_offers WHERE user_id=?", (i.user.id,))
        except Exception:
            pass
        await i.channel.send(embed=discord.Embed(description=i.user.mention + " declined. Ban in 60 seconds.", color=C["err"]))
        asyncio.create_task(_mercy_ban(i.guild.id, i.user.id, i.channel.id))
        await _auto_close_mercy_ticket(i.guild.id, i.channel.id, MERCY_BAN_DELAY_SECONDS)
    @ui.button(label="Actually, accept", style=discord.ButtonStyle.green)
    async def no(self, i, b):
        if i.user.id != self.target_id:
            return await i.response.send_message(embed=discord.Embed(description="Not your offer.", color=C["err"]), ephemeral=True)
        await i.response.defer()
        await _grant_mercy(i.guild, i.user)
        await _auto_close_mercy_ticket(i.guild.id, i.channel.id)
        for c in self.children:
            c.disabled = True
        try:
            await i.message.edit(view=self)
        except Exception:
            pass
        await i.followup.send(embed=discord.Embed(description=i.user.mention + " accepted.", color=C["ok"]))

async def _grant_mercy(guild, member):
    rid = get_role_id(guild.id, "mercy_role")
    role = guild.get_role(rid) if rid else None
    if role and role not in member.roles:
        try:
            await member.add_roles(role, reason="Mercy accepted")
        except Exception:
            pass
    t = _mercy_tasks.pop(member.id, None)
    if t and not t.done():
        t.cancel()
    try:
        _exec("DELETE FROM mercy_offers WHERE user_id=?", (member.id,))
    except Exception:
        pass
    sc_id = get_role_id(guild.id, "staff_chat")
    if sc_id:
        sc = guild.get_channel(sc_id)
        if sc:
            try:
                await sc.send(
                    "**New hitter** — " + member.mention + "\n\n"
                    "Guide sent to DMs.\n\n"
                    "-# Want a bigger cut? Buy the MM role in the appropriate channel."
                )
            except Exception:
                pass
    try:
        guide_id = get_role_id(guild.id, "guide_channel")
        verify_id = get_role_id(guild.id, "verify_channel")
        guide_m = ("<#" + str(guide_id) + ">") if guide_id else "the guide channel"
        verify_m = ("<#" + str(verify_id) + ">") if verify_id else "the verify channel"
        dm = (
            "# Hitter Guide\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "**1. Find a target**\n"
            "Any trading server. Roblox, Discord, wherever items move.\n\n"
            "**2. Pitch a fake deal**\n"
            "Talk like a normal trader. Agree on something believable.\n\n"
            "**3. Have them open request-mm**\n"
            "You ask for a middleman. They create the ticket.\n\n"
            "**4. Wait**\n"
            "MM takes over. Stay quiet. Don't DM the target outside the ticket.\n\n"
            "**5. Get paid**\n"
            "Split settles when the ticket closes. You keep half.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "**Verify** → " + verify_m + "\n"
            "**Advanced guide** → " + guide_m + "\n\n"
            "-# Questions: staff chat only."
        )
        await member.send(dm)
    except discord.Forbidden:
        pass

async def _mercy_ban(guild_id, user_id, channel_id):
    await asyncio.sleep(MERCY_BAN_DELAY_SECONDS)
    guild = bot.get_guild(guild_id)
    if not guild:
        return
    member = guild.get_member(user_id)
    if not member:
        return
    rid = get_role_id(guild_id, "mercy_role")
    if rid and any(r.id == rid for r in member.roles):
        return
    try:
        await member.ban(reason="Declined mercy offer")
        ch = guild.get_channel(channel_id)
        if ch:
            await ch.send(embed=discord.Embed(
                title="Banned",
                description="**" + member.mention + "** declined the offer.\n-# 60-second window closed.",
                color=C["err"]))
    except Exception as e:
        log.warning("mercy ban: " + str(e))

async def _mercy_timeout(guild_id, user_id, channel_id, delay=None):
    await asyncio.sleep(MERCY_RESPONSE_SECONDS if delay is None else max(0, delay))
    _mercy_tasks.pop(user_id, None)
    try:
        _exec("DELETE FROM mercy_offers WHERE user_id=?", (user_id,))
    except Exception:
        pass
    guild = bot.get_guild(guild_id)
    if guild:
        member = guild.get_member(user_id)
        rid = get_role_id(guild_id, "mercy_role")
        if member and not (rid and any(r.id == rid for r in member.roles)):
            try:
                await member.timeout(timedelta(days=MERCY_TIMEOUT_DAYS), reason="Did not respond to mercy offer")
                ch = guild.get_channel(channel_id)
                if ch:
                    await ch.send(embed=discord.Embed(
                        title="No response",
                        description="**" + member.mention + "** did not respond.\n-# 14-day timeout applied.",
                        color=C["err"]))
            except Exception as e:
                log.warning("mercy timeout: " + str(e))
    await _auto_close_mercy_ticket(guild_id, channel_id)

class MercyView(ui.View):
    def __init__(self, target_id=0):
        super().__init__(timeout=None)
        self.target_id = target_id

    def _resolved_target_id(self, i):
        if self.target_id:
            return self.target_id
        try:
            row = _get_row("SELECT user_id FROM mercy_offers WHERE message_id=?", (i.message.id,))
            if row:
                return row["user_id"]
        except Exception:
            pass
        return 0

    @ui.button(label="Accept", style=discord.ButtonStyle.green, emoji="<a:Tick_Yes:1529751821227393084>", custom_id="mercy_accept")
    async def accept(self, i, b):
        target_id = self._resolved_target_id(i)
        if target_id and i.user.id != target_id:
            return await i.response.send_message(
                embed=discord.Embed(description="Not your offer.", color=C["err"]),
                ephemeral=True)
        await i.response.defer()
        try:
            _exec("DELETE FROM mercy_offers WHERE message_id=?", (i.message.id,))
        except Exception:
            pass
        await _grant_mercy(i.guild, i.user)
        await _auto_close_mercy_ticket(i.guild.id, i.channel.id)
        for c in self.children:
            c.disabled = True
        try:
            await i.message.edit(view=self)
        except Exception:
            pass
        await i.followup.send(
            embed=discord.Embed(
                title="Welcome Aboard",
                description=i.user.mention + " accepted.",
                color=C["ok"]))

    @ui.button(label="Decline", style=discord.ButtonStyle.danger, emoji="<a:checkmarkcross:1542113944704000011>", custom_id="mercy_decline")
    async def decline(self, i, b):
        target_id = self._resolved_target_id(i)
        if target_id and i.user.id != target_id:
            return await i.response.send_message(
                embed=discord.Embed(description="Not your offer.", color=C["err"]),
                ephemeral=True)
        await i.response.send_message(
            embed=discord.Embed(
                title="Confirm decline",
                description=(
                    "Declining bans you in 60 seconds.\n\n"
                    "No re-offer. No appeal.\n\n"
                    "-# Confirm to proceed."
                ),
                color=C["err"]),
            view=MercyDeclineConfirmView(i.user.id))

class CloseConfirmView(ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=60)
        self.author_id = author_id

    async def interaction_check(self, i):
        return i.user.id == self.author_id

    @ui.button(label="Yes, close ticket", style=discord.ButtonStyle.danger)
    async def yes(self, i, b):
        for c in self.children:
            c.disabled = True
        try:
            await i.response.edit_message(view=self)
        except Exception:
            pass
        await close_ticket(i.channel, i.user, i.guild)

    @ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, i, b):
        for c in self.children:
            c.disabled = True
        try:
            await i.response.edit_message(
                embed=discord.Embed(description="Close cancelled.", color=C["ok"]),
                view=self)
        except Exception:
            pass

class TicketControlView(ui.View):
    def __init__(self, claimed=False):
        super().__init__(timeout=None)
        self.claimed = claimed
        # One persistent button toggles Claim <-> Unclaim.
        self.claim_toggle.label = "Unclaim" if claimed else "Claim"
        self.claim_toggle.style = discord.ButtonStyle.secondary if claimed else discord.ButtonStyle.success

    @ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="ticket_close")
    async def close(self, i, b):
        is_admin = has_perm(i.user, "administrator") or is_ticket_admin(i.user)
        owner_rid = get_role_id(i.guild.id, "owner_role")
        is_owner = bool(owner_rid and member_has_role(i.user, owner_rid))
        mm_rid = get_role_id(i.guild.id, "mm_role")
        is_mm = bool(mm_rid and member_has_role(i.user, mm_rid))
        mm_has_access = False
        if is_mm:
            try:
                mm_has_access = bool(i.channel.permissions_for(i.user).view_channel)
            except Exception:
                pass
        if not (is_admin or is_owner or mm_has_access):
            return await i.response.send_message(embed=discord.Embed(description="You cannot close this ticket.", color=C["err"]), ephemeral=True)
        return await i.response.send_message(
            embed=discord.Embed(description="Are you sure you want to close this ticket?\nThe channel will be deleted in 5 seconds.", color=C["warn"]),
            view=CloseConfirmView(i.user.id), ephemeral=True)

    @ui.button(label="Add User", style=discord.ButtonStyle.secondary, emoji="👤", custom_id="ticket_add_user")
    async def add_user(self, i, b):
        if not (is_staff(i.user) or has_perm(i.user, "administrator")):
            return await i.response.send_message(embed=discord.Embed(description="Only staff can add users to tickets.", color=C["err"]), ephemeral=True)
        class AddUserModal(ui.Modal, title="Add User to Ticket"):
            user = ui.TextInput(label="User", placeholder="Mention or user ID", required=True, max_length=50)
            async def on_submit(modal_self, interaction):
                member, err = await resolve_member(interaction.guild, modal_self.user.value.strip())
                if not member:
                    return await interaction.response.send_message(embed=discord.Embed(description="User not found.", color=C["err"]), ephemeral=True)
                try:
                    await interaction.channel.set_permissions(member, read_messages=True, send_messages=True)
                    if interaction.channel.name.startswith(("mm-", "claimed-mm-")):
                        row = get_mm_ticket_details(interaction.channel.id)
                        if row:
                            _exec("UPDATE mm_ticket_details SET trader_id=?, trader_text=? WHERE channel_id=?", (member.id, member.mention, interaction.channel.id))
                            await refresh_mm_ticket_embed(interaction.channel, interaction.guild)
                    await interaction.response.send_message(embed=discord.Embed(description=member.mention + " added to the ticket.", color=C["ok"]), ephemeral=True)
                except Exception:
                    await interaction.response.send_message(embed=discord.Embed(description="I couldn't add that user to the ticket.", color=C["err"]), ephemeral=True)
        await i.response.send_modal(AddUserModal())

    @ui.button(label="Claim", style=discord.ButtonStyle.success, custom_id="ticket_claim")
    async def claim_toggle(self, i, b):
        # 1. Read intent from the button label the user actually clicked.
        intended_claim = True
        try:
            for row in i.message.components:
                for comp in row.children:
                    if getattr(comp, "custom_id", None) == "ticket_claim":
                        intended_claim = (str(comp.label).strip().lower() == "claim")
                        break
        except Exception:
            pass

        # 2. Roles.
        mm_rid = get_role_id(i.guild.id, "mm_role")
        sup_rid = get_role_id(i.guild.id, "support_role")
        is_mm = member_has_role(i.user, mm_rid)
        is_sup = member_has_role(i.user, sup_rid)
        is_adm = has_perm(i.user, "administrator") or is_ticket_admin(i.user)
        is_mm_ticket_here = i.channel.name.startswith(("mm-", "claimed-mm-"))
        is_sup_ticket_here = i.channel.name.startswith(("ticket-", "claimed-ticket-"))
        ok = is_adm or (is_mm_ticket_here and is_mm) or (is_sup_ticket_here and (is_sup or is_mm))
        if not ok:
            return await i.response.send_message(
                embed=discord.Embed(description="You do not have the required role.", color=C["err"]),
                ephemeral=True)

        # 3. Cooldown.
        now = time.monotonic()
        last = _claim_action_time.get(i.channel.id, 0)
        if now - last < CLAIM_ACTION_COOLDOWN:
            return await i.response.send_message(
                embed=discord.Embed(
                    description="Please wait a moment before changing the claim state again.",
                    color=C["warn"]),
                ephemeral=True)

        # 4. Live DB state.
        current = get_claimer(i.channel.id)

        # 5. Race: user clicked Claim but it's already claimed.
        if intended_claim and current is not None:
            if current == i.user.id:
                try:
                    await i.response.edit_message(view=TicketControlView(claimed=True))
                except Exception:
                    pass
                return
            return await i.response.send_message(
                embed=discord.Embed(
                    description=("This ticket has already been claimed by <@{}>.\n"
                                 "If you need to take it over, click **Unclaim** first.").format(current),
                    color=C["err"]),
                ephemeral=True)

        # 6. Race: user clicked Unclaim but it's not claimed.
        if (not intended_claim) and current is None:
            try:
                await i.response.edit_message(view=TicketControlView(claimed=False))
            except Exception:
                pass
            return await i.response.send_message(
                embed=discord.Embed(description="This ticket is not currently claimed.", color=C["warn"]),
                ephemeral=True)

        # 7. Non-claimer non-admin cannot unclaim.
        if (not intended_claim) and current != i.user.id and not is_adm:
            return await i.response.send_message(
                embed=discord.Embed(description="Only the claimer or an admin can unclaim.", color=C["err"]),
                ephemeral=True)

        # 8. Dispatch.
        _claim_action_time[i.channel.id] = now
        if intended_claim:
            await claim_ticket(i.channel, i.user, i.guild, interaction=i)
        else:
            await unclaim_ticket(i.channel, i.user, i.guild, interaction=i)
    @ui.button(label="Dispute Trade", style=discord.ButtonStyle.danger, emoji="⚠️", custom_id="ticket_dispute_inline")
    async def dispute_inline(self, i, b):
        existing = _get_row("SELECT 1 FROM disputes WHERE channel_id=?", (i.channel.id,))
        if existing:
            return await i.response.send_message(
                embed=discord.Embed(description="A dispute is already open on this ticket.", color=C["warn"]),
                ephemeral=True)
        row = get_mm_ticket_details(i.channel.id)
        allowed = has_perm(i.user, "administrator") or is_ticket_admin(i.user) or is_staff(i.user)
        if not allowed and row:
            allowed = i.user.id in (int(row["opener_id"]), int(row["trader_id"]) if row["trader_id"] else -1)
        if not allowed:
            return await i.response.send_message(
                embed=discord.Embed(description="Only the traders or staff can open a dispute.", color=C["err"]),
                ephemeral=True)
        _exec("INSERT OR REPLACE INTO disputes(channel_id,guild_id,opened_by) VALUES(?,?,?)",
              (i.channel.id, i.guild.id, i.user.id))
        owner_rid = get_role_id(i.guild.id, "owner_role")
        admin_rid = get_role_id(i.guild.id, "ticket_admin_role")
        pings = []
        if owner_rid: pings.append("<@&{}>".format(owner_rid))
        if admin_rid and admin_rid != owner_rid: pings.append("<@&{}>".format(admin_rid))
        e = discord.Embed(
            title="⚠️ Trade Dispute Opened",
            description=i.user.mention + " has opened a dispute on this ticket.\n\n**Staff** — review and respond here.",
            color=C["err"])
        await i.response.send_message(content=" ".join(pings) or None, embed=e,
                                       allowed_mentions=discord.AllowedMentions(roles=True))
class DisputeTradeView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Dispute Trade", style=discord.ButtonStyle.danger, emoji="⚠️", custom_id="ticket_dispute")
    async def dispute(self, i, b):
        if not is_ticket_channel(i.channel):
            return await i.response.send_message(
                embed=discord.Embed(description="Only inside a ticket.", color=C["err"]), ephemeral=True)
        existing = _get_row("SELECT 1 FROM disputes WHERE channel_id=?", (i.channel.id,))
        if existing:
            return await i.response.send_message(
                embed=discord.Embed(description="A dispute is already open on this ticket.", color=C["warn"]),
                ephemeral=True)
        row = get_mm_ticket_details(i.channel.id)
        allowed = has_perm(i.user, "administrator") or is_ticket_admin(i.user) or is_staff(i.user)
        if not allowed and row:
            allowed = i.user.id in (int(row["opener_id"]), int(row["trader_id"]) if row["trader_id"] else -1)
        if not allowed:
            return await i.response.send_message(
                embed=discord.Embed(description="Only the traders or staff can open a dispute.", color=C["err"]),
                ephemeral=True)

        _exec("INSERT OR REPLACE INTO disputes(channel_id,guild_id,opened_by) VALUES(?,?,?)",
              (i.channel.id, i.guild.id, i.user.id))

        owner_rid = get_role_id(i.guild.id, "owner_role")
        admin_rid = get_role_id(i.guild.id, "ticket_admin_role")
        pings = []
        if owner_rid: pings.append("<@&{}>".format(owner_rid))
        if admin_rid and admin_rid != owner_rid: pings.append("<@&{}>".format(admin_rid))

        e = discord.Embed(
            title="⚠️ Trade Dispute Opened",
            description=(i.user.mention + " has opened a dispute on this ticket.\n\n"
                         "**Staff** — review the trade and respond here.\n"
                         "**Traders** — do not release anything until staff resolve this."),
            color=C["err"])
        e.set_footer(text="Ticket: {}".format(i.channel.name))
        await i.response.send_message(content=" ".join(pings) or None, embed=e,
                                       allowed_mentions=discord.AllowedMentions(roles=True))
class SupportPanelView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @ui.button(label="Get Support", style=discord.ButtonStyle.primary, emoji="🛟", custom_id="support_open")
    async def open(self, i, b):
        await i.response.defer(ephemeral=True)
        ch, err = await create_ticket(i.guild, i.user, "support")
        if err:
            return await i.followup.send(embed=discord.Embed(description=err, color=C["err"]), ephemeral=True)
        await i.followup.send(embed=discord.Embed(description="Ticket created: " + ch.mention, color=C["ok"]), ephemeral=True)
    @ui.button(label="Spanish", style=discord.ButtonStyle.secondary, emoji="🇪🇸", custom_id="support_lang_es")
    async def lang_es(self, i, b):
        await i.response.send_message("Support staff will respond in Spanish shortly.", ephemeral=True)
    @ui.button(label="German", style=discord.ButtonStyle.secondary, emoji="🇩🇪", custom_id="support_lang_de")
    async def lang_de(self, i, b):
        await i.response.send_message("Support staff will respond in German shortly.", ephemeral=True)
    @ui.button(label="Portuguese", style=discord.ButtonStyle.secondary, emoji="🇵🇹", custom_id="support_lang_pt")
    async def lang_pt(self, i, b):
        await i.response.send_message("Support staff will respond in Portuguese shortly.", ephemeral=True)
    @ui.button(label="Filipino", style=discord.ButtonStyle.secondary, emoji="🇵🇭", custom_id="support_lang_ph")
    async def lang_ph(self, i, b):
        await i.response.send_message("Support staff will respond in Filipino shortly.", ephemeral=True)

class MMTradeConfirmationView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def _load(self, channel_id):
        return get_mm_ticket_details(channel_id)

    async def _update(self, i, row, status_text, color):
        embed = discord.Embed(title="✦ Trade Confirmation", color=color)
        opener = i.guild.get_member(int(row["opener_id"]))
        trader = i.guild.get_member(int(row["trader_id"])) if row["trader_id"] else None
        opener_name = opener.mention if opener else "<@" + str(row["opener_id"]) + ">"
        trader_name = trader.mention if trader else (row["trader_text"] or "Other trader")
        embed.description = "Confirm that the trade below is exactly correct."
        embed.add_field(
            name="TRADE DETAILS",
            value=(
                "**" + opener_name + " is giving**\n`" + str(row["giving_one"] or "—") + "`\n\n"
                "**" + trader_name + " is giving**\n`" + str(row["giving_two"] or "—") + "`"
            ),
            inline=False
        )
        embed.add_field(name="STATUS", value=status_text, inline=False)
        embed.set_footer(text="Both traders must confirm before the trade is considered confirmed.")
        await i.message.edit(embed=embed, view=self)

    async def interaction_check(self, i):
        row = await self._load(i.channel.id)
        if not row:
            await i.response.send_message(embed=discord.Embed(description="This confirmation is no longer active.", color=C["err"]), ephemeral=True)
            return False
        allowed = {int(row["opener_id"])}
        if row["trader_id"]:
            allowed.add(int(row["trader_id"]))
        if i.user.id not in allowed:
            await i.response.send_message(embed=discord.Embed(description="Only the two traders can use these buttons.", color=C["err"]), ephemeral=True)
            return False
        return True

    @ui.button(label="Confirm", style=discord.ButtonStyle.success, emoji="<a:Tick_Yes:1529751821227393084>", custom_id="mm_trade_confirm")
    async def confirm(self, i, b):
        row = await self._load(i.channel.id)
        if not row:
            return await i.response.send_message(embed=discord.Embed(description="This confirmation is no longer active.", color=C["err"]), ephemeral=True)
        if row["declined_by"]:
            return await i.response.send_message(embed=discord.Embed(description="The trade has already been declined.", color=C["err"]), ephemeral=True)
        is_first = i.user.id == int(row["opener_id"])
        if not row["trader_id"]:
            return await i.response.send_message(embed=discord.Embed(description="The other trader must be added before confirmation.", color=C["err"]), ephemeral=True)
        col = "confirmed_one" if is_first else "confirmed_two"
        if int(row[col] or 0):
            return await i.response.send_message(embed=discord.Embed(description="You already confirmed this trade.", color=C["warn"]), ephemeral=True)
        _exec("UPDATE mm_ticket_details SET " + col + "=1 WHERE channel_id=?", (i.channel.id,))
        row = get_mm_ticket_details(i.channel.id)
        first = int(row["confirmed_one"] or 0)
        second = int(row["confirmed_two"] or 0)
        if first and second:
            for child in self.children:
                child.disabled = True
            await i.response.defer()
            await self._update(i, row, "<a:Tick_Yes:1529751821227393084> Both traders confirmed the trade.", C["ok"])
            return
        confirmed_by = "1 / 2 confirmed"
        await i.response.defer()
        await self._update(i, row, "🟡 " + confirmed_by, C["warn"])

    @ui.button(label="Decline", style=discord.ButtonStyle.danger, emoji="<a:checkmarkcross:1542113944704000011>", custom_id="mm_trade_decline")
    async def decline(self, i, b):
        row = await self._load(i.channel.id)
        if not row:
            return await i.response.send_message(embed=discord.Embed(description="This confirmation is no longer active.", color=C["err"]), ephemeral=True)
        if row["declined_by"]:
            return await i.response.send_message(embed=discord.Embed(description="The trade has already been declined.", color=C["err"]), ephemeral=True)
        _exec("UPDATE mm_ticket_details SET declined_by=? WHERE channel_id=?", (i.user.id, i.channel.id))
        for child in self.children:
            child.disabled = True
        await i.response.defer()
        await self._update(i, get_mm_ticket_details(i.channel.id), "<a:checkmarkcross:1542113944704000011> Trade declined by " + i.user.mention + ".", C["err"])

class MMTicketModal(ui.Modal, title="Request a Middleman"):
    trader = ui.TextInput(
        label="Who is the other trader?",
        placeholder="Username, mention, or user ID",
        required=True,
        max_length=50
    )
    giving = ui.TextInput(
        label="What are you giving?",
        placeholder="Example: 2x Chroma Luger",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=500
    )
    other_giving = ui.TextInput(
        label="What is the other user giving?",
        placeholder="Example: 1x Harvester",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=500
    )

    async def on_submit(self, i):
        scam_rid = get_role_id(i.guild.id, "scam_role")
        if scam_rid and member_has_role(i.user, scam_rid):
            return await i.response.send_message(
                embed=discord.Embed(description="You are marked as a scammer.", color=C["err"]),
                ephemeral=True
            )
        await i.response.defer(ephemeral=True)
        ch, err = await create_ticket(
            i.guild,
            i.user,
            "mm",
            trader_text=self.trader.value.strip(),
            giving_one=self.giving.value.strip(),
            giving_two=self.other_giving.value.strip()
        )
        if err:
            return await i.followup.send(embed=discord.Embed(description=err, color=C["err"]), ephemeral=True)
        await i.followup.send(
            embed=discord.Embed(description="MM ticket created: " + ch.mention, color=C["ok"]),
            ephemeral=True
        )

class MMPanelView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @ui.button(label="Request Middleman", style=discord.ButtonStyle.primary, custom_id="mm_open")
    async def open(self, i, b):
        await i.response.send_modal(MMTicketModal())

class FeeView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @ui.button(label="Pay 50%", style=discord.ButtonStyle.primary, custom_id="fee_pay_50")
    async def pay_50(self, i, b):
        await i.response.send_message("50% payment selected.", ephemeral=True)
    @ui.button(label="Pay 100%", style=discord.ButtonStyle.success, custom_id="fee_pay_100")
    async def pay_100(self, i, b):
        await i.response.send_message("100% payment selected.", ephemeral=True)

# ==================== ASKUSER ====================
class AskUserMMModal(ui.Modal, title="Your Roblox Username"):
    roblox = ui.TextInput(
        label="Your Roblox username",
        placeholder="e.g. KookiePlays",
        required=True,
        min_length=3,
        max_length=30)
    def __init__(self, channel_id, user1_id, user2_id, guild_id):
        super().__init__(timeout=300)
        self.channel_id = channel_id
        self.user1_id = user1_id
        self.user2_id = user2_id
        self.guild_id = guild_id

    async def on_submit(self, i):
        await i.response.defer(ephemeral=True)
        existing = _get_row("SELECT * FROM askuser_state WHERE channel_id=?", (self.channel_id,))
        if existing and (existing["user1_confirmed"] or existing["user2_confirmed"]):
            return await i.followup.send(
                "A verification is already in progress with confirmed usernames.",
                ephemeral=True)
        username = self.roblox.value.strip()
        with _db() as con:
            con.execute("""
                INSERT INTO askuser_state
                    (channel_id, mm_user_id, mm_roblox, user1_id, user2_id,
                     user1_roblox, user2_roblox, user1_confirmed, user2_confirmed, prompt_message_id)
                VALUES(?, ?, ?, ?, ?, NULL, NULL, 0, 0, NULL)
                ON CONFLICT(channel_id) DO UPDATE SET
                    mm_user_id=excluded.mm_user_id,
                    mm_roblox=excluded.mm_roblox,
                    user1_id=excluded.user1_id,
                    user2_id=excluded.user2_id,
                    user1_roblox=NULL,
                    user2_roblox=NULL,
                    user1_confirmed=0,
                    user2_confirmed=0
            """, (self.channel_id, i.user.id, username, self.user1_id, self.user2_id))
        guild = bot.get_guild(self.guild_id)
        if guild is None:
            return await i.followup.send("Server not found.", ephemeral=True)
        u1 = guild.get_member(self.user1_id)
        u2 = guild.get_member(self.user2_id)
        u1_m = u1.mention if u1 else "<@" + str(self.user1_id) + ">"
        u2_m = u2.mention if u2 else "<@" + str(self.user2_id) + ">"
        embed = _build_askuser_embed(guild, self.channel_id)

        target = guild.get_channel(self.channel_id)
        if target is None:
            try:
                target = await bot.fetch_channel(self.channel_id)
            except Exception:
                return await i.followup.send("Ticket channel not found.", ephemeral=True)

        try:
            msg = await target.send(
                content=u1_m + " " + u2_m,
                embed=embed,
                view=AskUserPromptView(),
                allowed_mentions=discord.AllowedMentions(users=True))
            _exec("UPDATE askuser_state SET prompt_message_id=? WHERE channel_id=?", (msg.id, self.channel_id))
        except discord.Forbidden:
            return await i.followup.send("I can't send messages in the ticket.", ephemeral=True)
        await i.followup.send("Traders have been prompted in the ticket.", ephemeral=True)

class TraderUsernameModal(ui.Modal, title="Your Roblox Username"):
    roblox = ui.TextInput(
        label="Your Roblox username",
        placeholder="e.g. YourName123",
        required=True,
        min_length=3,
        max_length=30)
    def __init__(self, channel_id):
        super().__init__(timeout=300)
        self.channel_id = channel_id
    async def on_submit(self, i):
        state = _get_row("SELECT * FROM askuser_state WHERE channel_id=?", (self.channel_id,))
        if not state:
            return await i.response.send_message("This session is no longer active.", ephemeral=True)
        uid = i.user.id
        if uid == state["user1_id"]:
            slot = "user1"
        elif uid == state["user2_id"]:
            slot = "user2"
        else:
            return await i.response.send_message("You are not one of the listed traders.", ephemeral=True)
        username = self.roblox.value.strip()
        _exec("UPDATE askuser_state SET " + slot + "_roblox=?, " + slot + "_confirmed=0 WHERE channel_id=?",
              (username, self.channel_id))
        embed = discord.Embed(
            title="Confirm your username",
            description="You entered: `" + username + "`\n\nIs this correct?",
            color=C["info"])
        await i.response.send_message(
            embed=embed,
            view=ConfirmTraderUsernameView(self.channel_id),
            ephemeral=True)

class ConfirmTraderUsernameView(ui.View):
    def __init__(self, channel_id):
        super().__init__(timeout=300)
        self.channel_id = channel_id
    def _slot_for(self, state, uid):
        if uid == state["user1_id"]:
            return "user1"
        if uid == state["user2_id"]:
            return "user2"
        return None
    @ui.button(label="Confirm", style=discord.ButtonStyle.success, custom_id="askuser_confirm")
    async def confirm(self, i, b):
        ticket_channel_id = self.channel_id
        state = _get_row("SELECT * FROM askuser_state WHERE channel_id=?", (ticket_channel_id,))
        if not state:
            return await i.response.send_message("Session expired.", ephemeral=True)
        slot = self._slot_for(state, i.user.id)
        if slot is None:
            return await i.response.send_message("You are not one of the listed traders.", ephemeral=True)
        username = state[slot + "_roblox"]
        if not username:
            return await i.response.send_message("No username entered.", ephemeral=True)
        _exec("UPDATE askuser_state SET " + slot + "_confirmed=1 WHERE channel_id=?", (ticket_channel_id,))
        await i.response.edit_message(
            embed=discord.Embed(description="<a:Tick_Yes:1529751821227393084> Confirmed: `" + username + "`", color=C["ok"]),
            view=None)

        row = _get_row("SELECT guild_id FROM ticket_log WHERE channel_id=?", (ticket_channel_id,))
        if not row:
            return
        guild = bot.get_guild(row["guild_id"])
        if guild is None:
            return
        target = guild.get_channel(ticket_channel_id)
        if target is None:
            try:
                target = await bot.fetch_channel(ticket_channel_id)
            except Exception:
                target = None
        if target is not None:
            try:
                await target.send(embed=discord.Embed(
                    description="<a:Tick_Yes:1529751821227393084> " + i.user.mention + " confirmed their Roblox username: `" + username + "`",
                    color=C["ok"]))
            except Exception:
                pass
        await _refresh_askuser_prompt(guild, ticket_channel_id)

    @ui.button(label="Change", style=discord.ButtonStyle.secondary, custom_id="askuser_change")
    async def change(self, i, b):
        await i.response.send_modal(TraderUsernameModal(self.channel_id))

class AskUserPromptView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @ui.button(label="Enter Your Username", style=discord.ButtonStyle.primary, custom_id="askuser_enter")
    async def enter(self, i, b):
        state = _get_row("SELECT * FROM askuser_state WHERE channel_id=?", (i.channel_id,))
        if not state:
            return await i.response.send_message("This prompt is no longer active.", ephemeral=True)
        uid = i.user.id
        if uid not in (state["user1_id"], state["user2_id"]):
            return await i.response.send_message(
                embed=discord.Embed(description="You are not one of the listed traders.", color=C["err"]),
                ephemeral=True)
        await i.response.send_modal(TraderUsernameModal(i.channel_id))

class AskUserStartView(ui.View):
    def __init__(self, author_id, channel_id, user1_id, user2_id, guild_id):
        super().__init__(timeout=300)
        self.author_id = author_id
        self.channel_id = channel_id
        self.user1_id = user1_id
        self.user2_id = user2_id
        self.guild_id = guild_id

    async def interaction_check(self, i):
        return i.user.id == self.author_id
    @ui.button(label="Enter My Roblox Username", style=discord.ButtonStyle.primary, custom_id="askuser_start")
    async def start(self, i, b):
        await i.response.send_modal(AskUserMMModal(self.channel_id, self.user1_id, self.user2_id, self.guild_id))

def _build_askuser_embed(guild, channel_id):
    state = _get_row("SELECT * FROM askuser_state WHERE channel_id=?", (channel_id,))
    if not state:
        return discord.Embed(description="Session expired.", color=C["err"])
    mm = guild.get_member(state["mm_user_id"]) if state["mm_user_id"] else None
    u1 = guild.get_member(state["user1_id"]) if state["user1_id"] else None
    u2 = guild.get_member(state["user2_id"]) if state["user2_id"] else None
    mm_m = mm.mention if mm else "<@" + str(state["mm_user_id"]) + ">"
    u1_m = u1.mention if u1 else "<@" + str(state["user1_id"]) + ">"
    u2_m = u2.mention if u2 else "<@" + str(state["user2_id"]) + ">"
    desc = (
        "Both traders must enter the Roblox username they'll use for this trade.\n\n"
        "Enter it exactly as it appears on Roblox.\n\n"
        "**MM Account**\n"
        "The assigned MM will provide their Roblox username below.\n\n"
        "🤝 **MM Roblox Username:** " + mm_m + " — `" + (state["mm_roblox"] or "N/A") + "`\n"
        "> ⚠️ **Only trade with the exact Roblox account shown by the assigned MM.**"
    )
    def line(slot, mention, confirmed_flag):
        name = state[slot + "_roblox"]
        if confirmed_flag:
            return "<a:Tick_Yes:1529751821227393084> " + mention + " — `" + name + "` *(confirmed)*"
        if name:
            return "🕓 " + mention + " — `" + name + "` *(awaiting confirm)*"
        return "⏳ " + mention + " — *waiting on username*"
    desc += "\n\n**Trader Verification**\n"
    desc += line("user1", u1_m, bool(state["user1_confirmed"])) + "\n"
    desc += line("user2", u2_m, bool(state["user2_confirmed"]))
    if state["user1_confirmed"] and state["user2_confirmed"]:
        desc += "\n\n<a:Tick_Yes:1529751821227393084> **Both Roblox usernames confirmed. The MM can continue.**"
    e = discord.Embed(title="Roblox Account Verification", description=desc, color=C["info"])
    e.set_footer(text=SERVER_NAME + " | Middleman Service")
    return e

async def _refresh_askuser_prompt(guild, channel_id):
    state = _get_row("SELECT * FROM askuser_state WHERE channel_id=?", (channel_id,))
    if not state or not state["prompt_message_id"]:
        return
    ch = guild.get_channel(channel_id)
    if ch is None:
        return
    try:
        msg = await ch.fetch_message(state["prompt_message_id"])
    except Exception:
        return
    embed = _build_askuser_embed(guild, channel_id)
    both_done = bool(state["user1_confirmed"] and state["user2_confirmed"])
    view = None if both_done else AskUserPromptView()
    try:
        await msg.edit(embed=embed, view=view)
    except Exception:
        pass
DOT = "﹒"; H2 = "##"; ZERO_WIDTH = "\u200b"; WAVE = "👋"; SHIELD = "🛡️"
GREEN_TICK = "<a:Tick_Yes:1529751821227393084>"; RED_X = "<a:checkmarkcross:1542113944704000011>"; MONEY = "💵"; SCROLL = "📜"; WARNING = "⚠️"; LOCK = "🔒"; LOAD = "⏳"

def _usd_str(v):
    try:
        return "${:,.2f}".format(float(v))
    except Exception:
        return "$0.00"

def am_role_selection_embed(t):
    a = am_asset(t["asset"])
    s = "<@" + str(t["sender_id"]) + ">" if t.get("sender_id") else "..."
    r = "<@" + str(t["receiver_id"]) + ">" if t.get("receiver_id") else "..."
    e = discord.Embed(
        title="Pick your role",
        description=(
            "**Sender** — you send " + a["name"] + " to the bot.\n"
            "**Receiver** — you get " + a["name"] + " back later."
        ),
        color=C["neutral"])
    e.add_field(name="Sender", value=s, inline=True)
    e.add_field(name="Receiver", value=r, inline=True)
    return e

def am_role_confirmation_embed(t):
    e = discord.Embed(
        title="Confirm roles",
        description="Check both usernames before continuing.",
        color=C["neutral"])
    e.add_field(name="Sender", value="<@" + str(t["sender_id"]) + ">", inline=True)
    e.add_field(name="Receiver", value="<@" + str(t["receiver_id"]) + ">", inline=True)
    e.add_field(name=ZERO_WIDTH, value="-# Click Incorrect if either is wrong.", inline=False)
    return e

def am_role_correct_embed(u):
    return discord.Embed(description=GREEN_TICK + " " + u.mention + " confirmed roles.", color=C["ok"])

def am_role_incorrect_embed(u):
    return discord.Embed(description=RED_X + " " + u.mention + " marked roles incorrect.", color=C["err"])

def am_usd_prompt_embed():
    return discord.Embed(
        title="Trade value",
        description="Sender sets the USD amount.",
        color=C["neutral"])

def am_usd_confirmation_embed(t):
    return discord.Embed(
        title="Confirm USD amount",
        description="Set to `" + _usd_str(t["usd_amount"]) + "`\n\nBoth sides must confirm.",
        color=C["neutral"])

def am_usd_correct_embed(u):
    return discord.Embed(description=GREEN_TICK + " " + u.mention + " confirmed.", color=C["ok"])

def am_usd_incorrect_embed(u):
    return discord.Embed(description=RED_X + " " + u.mention + " marked USD incorrect.", color=C["err"])

def am_payment_embed(t):
    a = am_asset(t["asset"])
    e = discord.Embed(
        title="Send payment",
        description="Send the **exact** amount below. Wrong amount = ticket closed.",
        color=C["neutral"])
    e.add_field(name="USD", value="`" + _usd_str(t["usd_amount"]) + "`", inline=True)
    e.add_field(name=a["name"] + " amount", value="`" + str(t["crypto_amount"]) + "`", inline=True)
    e.add_field(name="Address", value="`" + str(t["deposit_address"]) + "`", inline=False)
    e.add_field(name=ZERO_WIDTH, value="-# Network: " + a["network"], inline=False)
    return e

def am_proceed_embed(t):
    a = am_asset(t["asset"])
    return discord.Embed(
        title="Trade is live",
        description=(
            "**1** · <@" + str(t["receiver_id"]) + "> gives your trader the items/payment.\n\n"
            "**2** · <@" + str(t["sender_id"]) + "> clicks Release once you have your items."
        ),
        color=C["ok"])

def am_cancel_embed(t):
    u = "\n".join("<@" + str(x) + ">" for x in (t.get("uncancel_votes") or "").split(",") if x) or "None"
    c = "\n".join("<@" + str(x) + ">" for x in (t.get("cancel_votes") or "").split(",") if x) or "None"
    e = discord.Embed(
        title="Cancellation requested",
        description="Both traders must pick the same option.",
        color=C["warn"])
    e.add_field(name="Agreed to uncancel", value=u, inline=False)
    e.add_field(name="Confirmed cancel", value=c, inline=False)
    return e

def am_release_confirm_embed(t):
    a = am_asset(t["asset"])
    return discord.Embed(
        title="Release " + a["name"] + "?",
        description=(
            "This lets <@" + str(t["receiver_id"]) + "> withdraw.\n\n"
            "Only click Confirm if you got everything.\n\n"
            "-# Staff will never ask you to release or cancel."
        ),
        color=C["warn"])

def am_address_prompt_embed(t):
    a = am_asset(t["asset"])
    return discord.Embed(
        title="Your " + a["name"] + " address",
        description="Paste the address you want paid to.\n\n-# Wrong address = funds stuck.",
        color=C["neutral"])

def am_address_confirm_embed(t):
    return discord.Embed(
        title="Confirm address",
        description="Address: `" + str(t["receiver_address"]) + "`\n\nCheck it carefully.",
        color=C["warn"])

def am_sending_embed():
    return discord.Embed(description="Processing...", color=C["neutral"])

def _am_fake_txid(asset):
    if asset == "sol":
        alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        return "".join(random.choice(alphabet) for _ in range(88))
    if asset in ("usdt", "eth"):
        return "0x" + "".join(random.choice("0123456789abcdef") for _ in range(64))
    return "".join(random.choice("0123456789abcdef") for _ in range(64))

def _am_short_hash(h):
    h = str(h)
    return h if len(h) <= 32 else h[:18] + "..." + h[-12:]

def am_tx_detected_embed(t, confirmations, needed):
    a = am_asset(t["asset"])
    c = max(0, min(int(confirmations), needed))
    e = discord.Embed(
        title="Transaction detected",
        description="Unconfirmed. Waiting for " + str(needed) + " confirmations.",
        color=C["warn"])
    txid = t.get("deposit_txid")
    if txid:
        e.add_field(name="Transaction", value="`" + _am_short_hash(txid) + "`", inline=False)
    e.add_field(name="Confirmations", value="**" + str(c) + " / " + str(needed) + "**", inline=True)
    e.add_field(name="Amount", value="`" + str(t["crypto_amount"]) + "` " + a["name"], inline=True)
    e.add_field(name=ZERO_WIDTH, value="-# You'll be notified when confirmed.", inline=False)
    return e

def am_tx_confirmed_embed(t):
    a = am_asset(t["asset"])
    e = discord.Embed(
        title="Transaction confirmed",
        color=C["ok"])
    txid = t.get("deposit_txid")
    if txid:
        e.add_field(name="Transaction", value="`" + _am_short_hash(txid) + "`", inline=False)
    e.add_field(name="Amount received", value="`" + str(t["crypto_amount"]) + "` " + a["name"], inline=False)
    return e

def am_dm_confirm_embed(t):
    a = am_asset(t["asset"])
    e = discord.Embed(
        title="Confirm your transaction",
        description=(
            "You're the **sender** in your Auto MM ticket.\n\n"
            "Click **I Have Sent** once you've sent `" + str(t["crypto_amount"]) + " " + a["name"] + "` to:\n"
            "```\n" + str(t["deposit_address"]) + "\n```"
        ),
        color=C["neutral"])
    e.set_footer(text=SERVER_NAME + " · Auto Middleman")
    return e

def am_dm_detected_embed(t, confirmations, needed):
    a = am_asset(t["asset"])
    c = max(0, min(int(confirmations), needed))
    e = discord.Embed(
        title="Transaction detected",
        description="Waiting for " + str(needed) + " confirmations.\n\nAnother DM when it's confirmed.",
        color=C["warn"])
    e.add_field(name="Confirmations", value="**" + str(c) + " / " + str(needed) + "**", inline=True)
    e.add_field(name="Amount", value="`" + str(t["crypto_amount"]) + "` " + a["name"], inline=True)
    txid = t.get("deposit_txid")
    if txid:
        e.add_field(name="Transaction", value="`" + _am_short_hash(txid) + "`", inline=False)
    return e

def am_dm_confirmed_embed(t):
    a = am_asset(t["asset"])
    e = discord.Embed(
        title="Transaction confirmed",
        description="Trade is now live in your ticket.",
        color=C["ok"])
    e.add_field(name="Amount received", value="`" + str(t["crypto_amount"]) + "` " + a["name"], inline=False)
    return e

async def _am_dm_update(guild, ticket, embed, remove_view=False):
    try:
        ch_id = ticket.get("dm_channel_id")
        msg_id = ticket.get("dm_msg_id")
        if not ch_id or not msg_id:
            return
        dm_ch = bot.get_channel(int(ch_id))
        if dm_ch is None:
            try:
                dm_ch = await bot.fetch_channel(int(ch_id))
            except Exception:
                return
        msg = await dm_ch.fetch_message(int(msg_id))
        if remove_view:
            await msg.edit(embed=embed, view=None)
        else:
            await msg.edit(embed=embed)
    except Exception as e:
        log.warning("[AutoMM] DM update failed: " + str(e))

async def am_simulate_deposit(channel_id, guild_id, dm=False):
    try:
        if not dm:
            await asyncio.sleep(random.randint(60, 240))
        t = am_get(channel_id)
        if not t or t["status"] not in ("waiting_payment", "deposit_detected"):
            return
        guild = bot.get_guild(guild_id)
        if not guild:
            return
        channel = guild.get_channel(channel_id)
        if not channel:
            return
        txid = _am_fake_txid(t["asset"])
        needed = 2
        am_set(channel_id, deposit_txid=txid, status="deposit_detected", deposit_confirmations=0)
        t = am_get(channel_id)
        try:
            msg = await channel.send(embed=am_tx_detected_embed(t, 0, needed))
        except Exception:
            return
        am_set(channel_id, deposit_msg_id=msg.id)
        await _am_dm_update(guild, t, am_dm_detected_embed(t, 0, needed))
        for c in range(1, needed + 1):
            await asyncio.sleep(random.randint(30, 90))
            t = am_get(channel_id)
            if not t or t["status"] not in ("deposit_detected", "waiting_payment"):
                return
            am_set(channel_id, deposit_confirmations=c)
            t = am_get(channel_id)
            try:
                await msg.edit(embed=am_tx_detected_embed(t, c, needed))
            except Exception:
                pass
            await _am_dm_update(guild, t, am_dm_detected_embed(t, c, needed))
        await asyncio.sleep(5)
        t = am_get(channel_id)
        if not t:
            return
        am_set(channel_id, status="deposit_confirmed")
        t = am_get(channel_id)
        try:
            await channel.send(embed=am_tx_confirmed_embed(t))
            await channel.send(embed=discord.Embed(description="**Staff will release the trade shortly.**", color=C["warn"]))
        except Exception:
            pass
        await _am_dm_update(guild, t, am_dm_confirmed_embed(t), remove_view=True)
        staff_id = am_staff_channel_id(guild_id)
        if staff_id:
            sc = guild.get_channel(staff_id)
            if sc:
                try:
                    await sc.send(embed=discord.Embed(
                        title="Deposit confirmed",
                        color=C["ok"],
                        description=(
                            "**Ticket** · " + channel.mention + "\n"
                            "**Asset** · " + am_asset(t["asset"])["name"] + "\n"
                            "**USD** · " + _usd_str(t["usd_amount"]) + "\n\n"
                            "Ready to release.\n`$conf " + channel.mention + "`"
                        )))
                except Exception:
                    pass
    except asyncio.CancelledError:
        return
    except Exception as e:
        log.exception("[AutoMM] sim failed: " + str(e))
    finally:
        _am_sim_tasks.pop(channel_id, None)

def am_settlement_pending_embed(t):
    a = am_asset(t["asset"])
    return discord.Embed(
        title="Settlement pending",
        description=a["name"] + " release authorized. Waiting for staff payout.",
        color=C["warn"])

def am_withdrawal_success_embed(t):
    a = am_asset(t["asset"])
    e = discord.Embed(title="Withdrawal successful", color=C["ok"])
    e.add_field(name="Amount sent", value="`" + str(t["crypto_amount"]) + "` " + a["name"] + " (" + _usd_str(t["usd_amount"]) + ")", inline=False)
    if t.get("payout_txid"):
        e.add_field(name="Payout TX", value="`" + str(t["payout_txid"]) + "`", inline=False)
    return e

def am_completed_embed(t):
    a = am_asset(t["asset"])
    e = discord.Embed(
        title="Trade completed",
        description="`" + str(t["crypto_amount"]) + "` " + a["name"] + " (" + _usd_str(t["usd_amount"]) + " USD)",
        color=C["neutral"],
        timestamp=discord.utils.utcnow())
    e.add_field(name="Sender", value="<@" + str(t["sender_id"]) + ">", inline=True)
    e.add_field(name="Receiver", value="<@" + str(t["receiver_id"]) + ">", inline=True)
    if t.get("payout_txid"):
        e.add_field(name="Transaction ID", value="`" + str(t["payout_txid"]) + "`", inline=False)
    return e

class AutoMMRequestModal(ui.Modal, title="Fill out the format"):
    def __init__(self, asset_key):
        super().__init__(timeout=300)
        self.asset_key = asset_key
        self.trader = ui.TextInput(label="Trader's Username or ID", placeholder="username or 123456789012345678", required=True, min_length=2, max_length=100)
        self.your_item = ui.TextInput(label="What are You giving?", style=discord.TextStyle.paragraph, required=True, min_length=2, max_length=500)
        self.trader_item = ui.TextInput(label="What is Your Trader giving?", style=discord.TextStyle.paragraph, required=True, min_length=2, max_length=500)
        self.add_item(self.trader)
        self.add_item(self.your_item)
        self.add_item(self.trader_item)
    async def on_submit(self, i):
        await i.response.defer(ephemeral=True)
        try:
            guild = i.guild
            opener = i.user
            m, err = await resolve_member(guild, self.trader.value.strip())
            if err:
                return await i.followup.send(embed=discord.Embed(description=err, color=C["err"]), ephemeral=True)
            if m.id == opener.id:
                return await i.followup.send(embed=discord.Embed(description="You cannot open a ticket with yourself.", color=C["err"]), ephemeral=True)
            if m.bot:
                return await i.followup.send(embed=discord.Embed(description="Trader cannot be a bot.", color=C["err"]), ephemeral=True)
            cat = await am_category(guild)
            if cat is None:
                return await i.followup.send(embed=discord.Embed(description="Could not create Auto MM category.", color=C["err"]), ephemeral=True)
            safe = re.sub(r"[^a-z0-9-]", "", opener.name.lower().replace(" ", "-")) or str(opener.id)
            cname = "automm-" + safe + "-" + str(opener.id % 10000)
            ow = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                opener: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, add_reactions=True, attach_files=True, embed_links=True),
                m: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, add_reactions=True, attach_files=True, embed_links=True),
                guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_channels=True, manage_messages=True, attach_files=True, embed_links=True),
            }
            for role in guild.roles:
                if role.permissions.administrator:
                    ow[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, add_reactions=True, attach_files=True, embed_links=True)
            channel = await guild.create_text_channel(cname, category=cat, overwrites=ow, topic="automm|opener=" + str(opener.id) + "|trader=" + str(m.id) + "|asset=" + self.asset_key)
            am_set(channel.id, guild_id=guild.id, opener_id=opener.id, trader_id=m.id, opener_side=self.your_item.value.strip(), trader_side=self.trader_item.value.strip(), asset=self.asset_key, status="role_selection")
            a = am_asset(self.asset_key)
            oe = discord.Embed(
                title="Auto Middleman",
                description=opener.mention + " " + m.mention + "\n\nFollow the steps below.",
                color=C["neutral"])
            oe.add_field(name=opener.display_name + "'s side", value="```\n" + self.your_item.value.strip()[:900] + "\n```", inline=False)
            oe.add_field(name=m.display_name + "'s side", value="```\n" + self.trader_item.value.strip()[:900] + "\n```", inline=False)
            oe.set_footer(text="Ticket · " + a["name"] + " · " + a["network"])
            await channel.send(content=opener.mention + " " + m.mention, embed=oe, view=AutoMMDeleteView())
            await am_send_role_selection(channel, channel.id)
            await i.followup.send(embed=discord.Embed(description="Ticket created: " + channel.mention, color=C["ok"]), ephemeral=True)
        except Exception as e:
            log.exception("[AutoMM] modal submit failed: " + str(e))
            try:
                await i.followup.send(embed=discord.Embed(description="Error: " + str(e), color=C["err"]), ephemeral=True)
            except Exception:
                pass

class AutoMMUsdModal(ui.Modal, title="Set USD Amount"):
    amount = ui.TextInput(label="USD amount", placeholder="e.g. 435.20", required=True, min_length=1, max_length=20)
    async def on_submit(self, i):
        await i.response.defer(ephemeral=True)
        try:
            async with _chan_lock(i.channel_id):
                t = am_get(i.channel_id)
                if not t or not am_is_sender(i.user.id, t):
                    return await i.followup.send(embed=discord.Embed(description="Only the sender can set USD.", color=C["err"]), ephemeral=True)
                raw = self.amount.value.replace("$", "").replace(",", "").strip()
                try:
                    amount = float(raw)
                    if amount <= 0 or amount > 10000000:
                        raise ValueError
                except Exception:
                    return await i.followup.send(embed=discord.Embed(description="Enter a valid USD amount.", color=C["err"]), ephemeral=True)
                am_set(i.channel_id, usd_amount="{:.2f}".format(amount), status="usd_confirmation", usd_confirmed="")
            await i.followup.send("USD amount submitted.", ephemeral=True)
            t = am_get(i.channel_id)
            await am_send_usd_confirmation(i.channel, t)
        except Exception as e:
            log.exception("[AutoMM] usd modal: " + str(e))

class AutoMMAddressModal(ui.Modal):
    def __init__(self, asset_key):
        a = am_asset(asset_key)
        super().__init__(title="Your " + a["name"] + " Address", timeout=300)
        self.address = ui.TextInput(label=a["name"] + " address", required=True, min_length=10, max_length=120)
        self.add_item(self.address)
    async def on_submit(self, i):
        await i.response.defer(ephemeral=True)
        try:
            async with _chan_lock(i.channel_id):
                t = am_get(i.channel_id)
                if not t or not am_is_receiver(i.user.id, t):
                    return await i.followup.send(embed=discord.Embed(description="Only the receiver can submit.", color=C["err"]), ephemeral=True)
                addr = self.address.value.strip()
                patt = {"usdt": r"0x[a-fA-F0-9]{40}", "eth": r"0x[a-fA-F0-9]{40}", "sol": r"[1-9A-HJ-NP-Za-km-z]{32,44}", "btc": r"(bc1[a-z0-9]{25,62}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})", "ltc": r"(ltc1[a-z0-9]{25,62}|[LM3][a-km-zA-HJ-NP-Z1-9]{26,33})"}
                if not re.fullmatch(patt.get(t["asset"], r".+"), addr):
                    return await i.followup.send(embed=discord.Embed(description="Invalid address format.", color=C["err"]), ephemeral=True)
                am_set(i.channel_id, receiver_address=addr, status="address_confirmation")
            await i.followup.send("Address submitted.", ephemeral=True)
            t = am_get(i.channel_id)
            await i.channel.send(content="<@" + str(t["receiver_id"]) + ">", embed=am_address_confirm_embed(t), view=AutoMMAddressConfirmView())
        except Exception as e:
            log.exception("[AutoMM] address modal: " + str(e))

class AutoMMDMConfirmView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @ui.button(label="I Have Sent", style=discord.ButtonStyle.success, custom_id="automm_dm_sent")
    async def sent(self, i, b):
        r = _get_row("SELECT * FROM automm_tickets WHERE dm_msg_id=?", (i.message.id,))
        t = dict(r) if r else None
        if t is None:
            return await i.response.send_message("This ticket is no longer active.", ephemeral=True)
        if t["status"] not in ("waiting_payment", "deposit_detected"):
            return await i.response.send_message("This confirmation is no longer active.", ephemeral=True)
        await i.response.edit_message(view=None)
        am_set(t["channel_id"], dm_confirm_clicked=1)
        ch_id = int(t["channel_id"])
        if ch_id not in _am_sim_tasks or _am_sim_tasks[ch_id].done():
            _am_sim_tasks[ch_id] = asyncio.create_task(am_simulate_deposit(ch_id, int(t["guild_id"]), dm=True))

class AutoMMDeleteView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @ui.button(label=DOT + " Delete Ticket", style=discord.ButtonStyle.danger, custom_id="automm_delete")
    async def delete(self, i, b):
        t = am_get(i.channel_id)
        if not t:
            return await i.response.send_message(embed=discord.Embed(description="Ticket not found.", color=C["err"]), ephemeral=True)
        is_admin = has_perm(i.user, "administrator")
        if not (is_admin or am_is_party(i.user.id, t)):
            return await i.response.send_message(embed=discord.Embed(description="You cannot delete this ticket.", color=C["err"]), ephemeral=True)
        funded = {"waiting_payment", "deposit_detected", "deposit_confirmed", "trade", "cancellation", "release_confirmation", "address_prompt", "address_confirmation", "settlement_pending", "completed"}
        if t["status"] in funded and not is_admin:
            return await i.response.send_message(embed=discord.Embed(description="Only admins can delete a funded ticket.", color=C["err"]), ephemeral=True)
        async def do_delete(inter):
            await inter.edit_original_response(view=None)
            sim = _am_sim_tasks.pop(i.channel_id, None)
            if sim and not sim.done():
                sim.cancel()
            am_del(i.channel_id)
            try:
                await i.channel.delete(reason="AutoMM deleted by " + str(i.user))
            except Exception:
                pass
            await am_cleanup_category(i.guild)
        await i.response.send_message(embed=discord.Embed(description="Delete this ticket?", color=C["warn"]), view=ConfirmView(i.user.id, do_delete), ephemeral=True)

class AutoMMRoleSelectView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    async def _pick(self, i, role):
        async with _chan_lock(i.channel_id):
            t = am_get(i.channel_id)
            if not t or not am_is_party(i.user.id, t):
                return await i.response.send_message(embed=discord.Embed(description="Only the two traders can select roles.", color=C["err"]), ephemeral=True)
            if t["status"] != "role_selection":
                return await i.response.send_message(embed=discord.Embed(description="Role selection is not active.", color=C["err"]), ephemeral=True)
            already = set()
            if t.get("sender_id"): already.add(int(t["sender_id"]))
            if t.get("receiver_id"): already.add(int(t["receiver_id"]))
            if i.user.id in already:
                return await i.response.send_message(embed=discord.Embed(description="You already selected a role.", color=C["err"]), ephemeral=True)
            key = role + "_id"
            if t.get(key):
                return await i.response.send_message(embed=discord.Embed(description="That role is taken.", color=C["err"]), ephemeral=True)
            am_set(i.channel_id, **{key: i.user.id})
            t = am_get(i.channel_id)
            complete = bool(t.get("sender_id") and t.get("receiver_id"))
            if complete:
                am_set(i.channel_id, status="role_confirmation")
        try:
            await i.response.edit_message(embed=am_role_selection_embed(t), view=AutoMMRoleSelectView())
        except Exception:
            pass
        if complete:
            t = am_get(i.channel_id)
            await i.channel.send(content="<@" + str(t["sender_id"]) + "> <@" + str(t["receiver_id"]) + ">", embed=am_role_confirmation_embed(t), view=AutoMMRoleConfirmView(), allowed_mentions=discord.AllowedMentions(users=True))
    @ui.button(label="Sender", style=discord.ButtonStyle.primary, custom_id="automm_role_sender")
    async def sender(self, i, b): await self._pick(i, "sender")
    @ui.button(label="Receiver", style=discord.ButtonStyle.primary, custom_id="automm_role_receiver")
    async def receiver(self, i, b): await self._pick(i, "receiver")
    @ui.button(label="Reset", style=discord.ButtonStyle.danger, custom_id="automm_role_reset")
    async def reset(self, i, b):
        async with _chan_lock(i.channel_id):
            t = am_get(i.channel_id)
            if not t:
                return await i.response.send_message(embed=discord.Embed(description="Ticket not found.", color=C["err"]), ephemeral=True)
            if not (has_perm(i.user, "administrator") or am_is_party(i.user.id, t)):
                return await i.response.send_message(embed=discord.Embed(description="Cannot reset.", color=C["err"]), ephemeral=True)
            am_set(i.channel_id, sender_id=None, receiver_id=None, role_confirmed="", status="role_selection")
            t = am_get(i.channel_id)
        try:
            await i.response.edit_message(embed=am_role_selection_embed(t), view=AutoMMRoleSelectView())
        except Exception:
            pass

class AutoMMRoleConfirmView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @ui.button(label="Correct", style=discord.ButtonStyle.success, custom_id="automm_role_correct")
    async def correct(self, i, b):
        async with _chan_lock(i.channel_id):
            t = am_get(i.channel_id)
            if not t or not am_is_party(i.user.id, t):
                return await i.response.send_message(embed=discord.Embed(description="Only traders can confirm.", color=C["err"]), ephemeral=True)
            if t["status"] != "role_confirmation":
                return await i.response.send_message(embed=discord.Embed(description="Not active.", color=C["err"]), ephemeral=True)
            confirmed = [int(x) for x in (t.get("role_confirmed") or "").split(",") if x]
            if i.user.id in confirmed:
                return await i.response.send_message(embed=discord.Embed(description="Already confirmed.", color=C["err"]), ephemeral=True)
            confirmed.append(i.user.id)
            am_set(i.channel_id, role_confirmed=",".join(str(x) for x in confirmed))
            both = {int(t["sender_id"]), int(t["receiver_id"])}.issubset(set(confirmed))
            if both:
                am_set(i.channel_id, status="usd_prompt")
        await i.response.send_message(embed=am_role_correct_embed(i.user))
        if both:
            t = am_get(i.channel_id)
            await am_send_usd_prompt(i.channel, t)
    @ui.button(label="Incorrect", style=discord.ButtonStyle.danger, custom_id="automm_role_incorrect")
    async def incorrect(self, i, b):
        async with _chan_lock(i.channel_id):
            t = am_get(i.channel_id)
            if not t or not am_is_party(i.user.id, t):
                return await i.response.send_message(embed=discord.Embed(description="Only traders.", color=C["err"]), ephemeral=True)
            am_set(i.channel_id, sender_id=None, receiver_id=None, role_confirmed="", status="role_selection")
        await i.response.send_message(embed=am_role_incorrect_embed(i.user))
        await am_send_role_selection(i.channel, i.channel_id)

class AutoMMUsdPromptView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @ui.button(label="Set USD Amount", style=discord.ButtonStyle.primary, custom_id="automm_set_usd")
    async def set_amount(self, i, b):
        t = am_get(i.channel_id)
        if not t or not am_is_sender(i.user.id, t):
            return await i.response.send_message(embed=discord.Embed(description="Only the sender can set USD.", color=C["err"]), ephemeral=True)
        if t["status"] != "usd_prompt":
            return await i.response.send_message(embed=discord.Embed(description="Not active.", color=C["err"]), ephemeral=True)
        await i.response.send_modal(AutoMMUsdModal())

class AutoMMUsdConfirmView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @ui.button(label="Correct", style=discord.ButtonStyle.success, custom_id="automm_usd_correct")
    async def correct(self, i, b):
        async with _chan_lock(i.channel_id):
            t = am_get(i.channel_id)
            if not t or not am_is_party(i.user.id, t):
                return await i.response.send_message(embed=discord.Embed(description="Only traders.", color=C["err"]), ephemeral=True)
            if t["status"] != "usd_confirmation":
                return await i.response.send_message(embed=discord.Embed(description="Not active.", color=C["err"]), ephemeral=True)
            confirmed = [int(x) for x in (t.get("usd_confirmed") or "").split(",") if x]
            if i.user.id in confirmed:
                return await i.response.send_message(embed=discord.Embed(description="Already confirmed.", color=C["err"]), ephemeral=True)
            confirmed.append(i.user.id)
            am_set(i.channel_id, usd_confirmed=",".join(str(x) for x in confirmed))
            both = {int(t["sender_id"]), int(t["receiver_id"])}.issubset(set(confirmed))
        await i.response.send_message(embed=am_usd_correct_embed(i.user))
        if both:
            t = am_get(i.channel_id)
            await am_send_payment_info(i.channel, t)
    @ui.button(label="Incorrect", style=discord.ButtonStyle.danger, custom_id="automm_usd_incorrect")
    async def incorrect(self, i, b):
        async with _chan_lock(i.channel_id):
            t = am_get(i.channel_id)
            if not t or not am_is_party(i.user.id, t):
                return await i.response.send_message(embed=discord.Embed(description="Only traders.", color=C["err"]), ephemeral=True)
            am_set(i.channel_id, usd_amount=None, usd_confirmed="", status="usd_prompt")
        await i.response.send_message(embed=am_usd_incorrect_embed(i.user))
        await am_send_usd_prompt(i.channel, am_get(i.channel_id))

class AutoMMPaymentInfoView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @ui.button(label="Copy Details", style=discord.ButtonStyle.primary, custom_id="automm_copy")
    async def copy(self, i, b):
        t = am_get(i.channel_id)
        if not t or not am_is_party(i.user.id, t):
            return await i.response.send_message(embed=discord.Embed(description="Only traders.", color=C["err"]), ephemeral=True)
        await i.response.send_message("Address:\n```\n" + str(t["deposit_address"]) + "\n```\nAmount:\n```\n" + str(t["crypto_amount"]) + "\n```", ephemeral=True)

class AutoMMProceedView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @ui.button(label="Release", style=discord.ButtonStyle.success, custom_id="automm_release")
    async def release(self, i, b):
        t = am_get(i.channel_id)
        if not t or not am_is_sender(i.user.id, t):
            return await i.response.send_message(embed=discord.Embed(description="Only the sender can release.", color=C["err"]), ephemeral=True)
        if t["status"] != "trade":
            return await i.response.send_message(embed=discord.Embed(description="Not ready for release.", color=C["err"]), ephemeral=True)
        am_set(i.channel_id, status="release_confirmation")
        t = am_get(i.channel_id)
        await i.response.send_message(content="<@" + str(t["sender_id"]) + ">", embed=am_release_confirm_embed(t), view=AutoMMReleaseConfirmView())
    @ui.button(label="Cancel", style=discord.ButtonStyle.secondary, custom_id="automm_cancel")
    async def cancel(self, i, b):
        t = am_get(i.channel_id)
        if not t or not am_is_party(i.user.id, t):
            return await i.response.send_message(embed=discord.Embed(description="Only traders.", color=C["err"]), ephemeral=True)
        if t["status"] != "trade":
            return await i.response.send_message(embed=discord.Embed(description="Cannot cancel now.", color=C["err"]), ephemeral=True)
        am_set(i.channel_id, status="cancellation", uncancel_votes="", cancel_votes="")
        t = am_get(i.channel_id)
        await i.response.send_message(content="<@" + str(t["sender_id"]) + "> <@" + str(t["receiver_id"]) + ">", embed=am_cancel_embed(t), view=AutoMMCancelView(), allowed_mentions=discord.AllowedMentions(users=True))

class AutoMMCancelView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    async def _vote(self, i, choice):
        async with _chan_lock(i.channel_id):
            t = am_get(i.channel_id)
            if not t or not am_is_party(i.user.id, t):
                return await i.response.send_message(embed=discord.Embed(description="Only traders.", color=C["err"]), ephemeral=True)
            if t["status"] != "cancellation":
                return await i.response.send_message(embed=discord.Embed(description="Not active.", color=C["err"]), ephemeral=True)
            unc = [int(x) for x in (t.get("uncancel_votes") or "").split(",") if x]
            can = [int(x) for x in (t.get("cancel_votes") or "").split(",") if x]
            uid = i.user.id
            if choice == "uncancel":
                if uid not in unc: unc.append(uid)
                can = [x for x in can if x != uid]
            else:
                if uid not in can: can.append(uid)
                unc = [x for x in unc if x != uid]
            am_set(i.channel_id, uncancel_votes=",".join(str(x) for x in unc), cancel_votes=",".join(str(x) for x in can))
            parties = {int(t["sender_id"]), int(t["receiver_id"])}
            u_done = parties.issubset(set(unc))
            c_done = parties.issubset(set(can))
            if u_done: am_set(i.channel_id, status="trade")
            elif c_done: am_set(i.channel_id, status="cancelled")
            t = am_get(i.channel_id)
        try:
            await i.response.edit_message(embed=am_cancel_embed(t), view=AutoMMCancelView())
        except Exception:
            pass
        if u_done:
            await i.channel.send(embed=discord.Embed(description=GREEN_TICK + " **Trade resumed.**", color=C["ok"]))
        elif c_done:
            await i.channel.send(embed=discord.Embed(description=RED_X + " **Cancellation confirmed.**", color=C["err"]))
    @ui.button(label="Uncancel", style=discord.ButtonStyle.secondary, custom_id="automm_uncancel")
    async def uncancel(self, i, b): await self._vote(i, "uncancel")
    @ui.button(label="Confirm Cancellation", style=discord.ButtonStyle.danger, custom_id="automm_confirm_cancel")
    async def confirm(self, i, b): await self._vote(i, "cancel")

class AutoMMReleaseConfirmView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @ui.button(label="Confirm", style=discord.ButtonStyle.success, custom_id="automm_release_confirm")
    async def confirm(self, i, b):
        t = am_get(i.channel_id)
        if not t or not am_is_sender(i.user.id, t):
            return await i.response.send_message(embed=discord.Embed(description="Only the sender.", color=C["err"]), ephemeral=True)
        if t["status"] != "release_confirmation":
            return await i.response.send_message(embed=discord.Embed(description="Not active.", color=C["err"]), ephemeral=True)
        am_set(i.channel_id, release_authorized=1, status="address_prompt")
        try:
            await i.response.edit_message(view=None)
        except Exception:
            pass
        t = am_get(i.channel_id)
        await i.channel.send(content="<@" + str(t["receiver_id"]) + ">", embed=am_address_prompt_embed(t), view=AutoMMAddressPromptView())
    @ui.button(label="Back", style=discord.ButtonStyle.secondary, custom_id="automm_release_back")
    async def back(self, i, b):
        t = am_get(i.channel_id)
        if not t or not am_is_sender(i.user.id, t):
            return await i.response.send_message(embed=discord.Embed(description="Only the sender.", color=C["err"]), ephemeral=True)
        am_set(i.channel_id, status="trade")
        try:
            await i.response.edit_message(view=None)
        except Exception:
            pass

class AutoMMAddressPromptView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @ui.button(label="Enter Address", style=discord.ButtonStyle.primary, custom_id="automm_enter_address")
    async def enter(self, i, b):
        t = am_get(i.channel_id)
        if not t or not am_is_receiver(i.user.id, t):
            return await i.response.send_message(embed=discord.Embed(description="Only the receiver.", color=C["err"]), ephemeral=True)
        if t["status"] != "address_prompt":
            return await i.response.send_message(embed=discord.Embed(description="Not active.", color=C["err"]), ephemeral=True)
        await i.response.send_modal(AutoMMAddressModal(t["asset"]))

class AutoMMAddressConfirmView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @ui.button(label="Confirm", style=discord.ButtonStyle.success, custom_id="automm_address_confirm")
    async def confirm(self, i, b):
        t = am_get(i.channel_id)
        if not t or not am_is_receiver(i.user.id, t):
            return await i.response.send_message(embed=discord.Embed(description="Only receiver.", color=C["err"]), ephemeral=True)
        if t["status"] != "address_confirmation":
            return await i.response.send_message(embed=discord.Embed(description="Not active.", color=C["err"]), ephemeral=True)
        am_set(i.channel_id, status="settlement_pending")
        try:
            await i.response.edit_message(view=None)
        except Exception:
            pass
        await i.channel.send(embed=am_sending_embed())
        await asyncio.sleep(2)
        t = am_get(i.channel_id)
        await i.channel.send(embed=am_settlement_pending_embed(t))
        await i.channel.send(embed=discord.Embed(description="**Staff will complete the settlement shortly.**", color=C["warn"]))

        staff_id = am_staff_channel_id(i.guild.id)
        if staff_id:
            sc = i.guild.get_channel(staff_id)
            if sc:
                try:
                    await sc.send(embed=discord.Embed(
                        title="Settlement pending",
                        color=C["warn"],
                        description=(
                            "**Ticket** · " + i.channel.mention + "\n"
                            "**Asset** · " + am_asset(t["asset"])["name"] + "\n"
                            "**USD** · " + _usd_str(t["usd_amount"]) + "\n"
                            "**To** · `" + str(t["receiver_address"]) + "`\n\n"
                            "Run `$settle " + i.channel.mention + " <payout_txid>` when done."
                        ),
                    ))
                except Exception:
                    pass
    @ui.button(label="Back", style=discord.ButtonStyle.secondary, custom_id="automm_address_back")
    async def back(self, i, b):
        t = am_get(i.channel_id)
        if not t or not am_is_receiver(i.user.id, t):
            return await i.response.send_message(embed=discord.Embed(description="Only receiver.", color=C["err"]), ephemeral=True)
        am_set(i.channel_id, receiver_address=None, status="address_prompt")
        try:
            await i.response.edit_message(view=None)
        except Exception:
            pass
        t = am_get(i.channel_id)
        await i.channel.send(content="<@" + str(t["receiver_id"]) + ">", embed=am_address_prompt_embed(t), view=AutoMMAddressPromptView())

class AutoMMCloseView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @ui.button(label=DOT + " Close Ticket", style=discord.ButtonStyle.danger, emoji=LOCK, custom_id="automm_close")
    async def close(self, i, b):
        t = am_get(i.channel_id)
        if not t:
            return await i.response.send_message(embed=discord.Embed(description="Ticket not found.", color=C["err"]), ephemeral=True)
        is_admin = has_perm(i.user, "administrator")
        if not (is_admin or am_is_party(i.user.id, t)):
            return await i.response.send_message(embed=discord.Embed(description="Cannot close.", color=C["err"]), ephemeral=True)
        if t["status"] != "completed":
            return await i.response.send_message(embed=discord.Embed(description="Not completed.", color=C["err"]), ephemeral=True)
        await i.response.send_message(embed=discord.Embed(description="Closing ticket...", color=C["err"]))
        await asyncio.sleep(3)
        am_del(i.channel_id)
        try:
            await i.channel.delete(reason="AutoMM closed by " + str(i.user))
        except Exception:
            pass
        await am_cleanup_category(i.guild)

class _AutoMMCoinButton(ui.Button):
    def __init__(self, asset_key, label):
        super().__init__(label=label, style=discord.ButtonStyle.primary, custom_id="automm_req_" + asset_key)
        self.asset_key = asset_key
    async def callback(self, interaction):
        if not AUTOMM_ASSETS.get(self.asset_key, {}).get("address"):
            return await interaction.response.send_message(embed=discord.Embed(description=AUTOMM_ASSETS[self.asset_key]["name"] + " is not configured.", color=C["err"]), ephemeral=True)
        await interaction.response.send_modal(AutoMMRequestModal(self.asset_key))

class AutoMMPanelView(ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=None)
        try:
            accent = discord.Color.from_str(AUTOMM_PANEL_ACCENT).value
        except Exception:
            accent = C["neutral"]
        try:
            usdt_accent = discord.Color.from_str(AUTOMM_USDT_ACCENT).value
        except Exception:
            usdt_accent = C["neutral"]
        tos_mention = ("<#" + str(AUTOMM_TOS_CHANNEL_ID) + ">") if AUTOMM_TOS_CHANNEL_ID else "#tos"
        self.add_item(discord.ui.Container(
            discord.ui.TextDisplay("# 🛡️ Auto Middleman"),
            discord.ui.TextDisplay("-# " + SERVER_NAME + " · Protected crypto trades"),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.large),
            discord.ui.TextDisplay(
                "## Trade crypto without getting scammed.\n\n"
                "We hold the funds while you and the other trader finish the deal."
            ),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
            discord.ui.TextDisplay(
                "### How it works\n\n"
                "**01** · Both traders pick a role (Sender / Receiver)\n"
                "**02** · Sender sets the USD value\n"
                "**03** · Both confirm\n"
                "**04** · Sender deposits to the bot\n"
                "**05** · Trade runs, sender releases\n"
                "**06** · Receiver gets paid out"
            ),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
            discord.ui.TextDisplay(
                "### Fees\n\n"
                "$250+ → **$1.50**\n"
                "Under $250 → **$0.50**\n"
                "Under $50 → **free**"
            ),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
            discord.ui.TextDisplay(
                "> ⚠️ **Only trade with addresses shown in your ticket.**\n"
                "> **ToS:** " + tos_mention
            ),
            accent_colour=accent,
        ))
        labels = {"ltc": "Request Litecoin", "usdt": "Request USDT [BEP-20]", "sol": "Request Solana", "btc": "Request Bitcoin", "eth": "Request Ethereum"}
        networks = {"usdt": "BSC (BEP-20)", "sol": "Solana", "btc": "Bitcoin", "eth": "Ethereum"}
        for key in ("ltc", "usdt", "sol", "btc", "eth"):
            asset = AUTOMM_ASSETS.get(key)
            if not asset or not asset["address"]:
                continue
            body = "## " + asset["emoji"] + " · " + labels[key]
            if key in networks:
                body += "\n\n-# Network: " + networks[key]
            row = discord.ui.ActionRow()
            row.add_item(_AutoMMCoinButton(key, labels[key]))
            self.add_item(discord.ui.Container(discord.ui.TextDisplay(body), row, accent_colour=(usdt_accent if key == "usdt" else accent)))
        if AUTOMM_BIGGEST_TRADE_USD > 0:
            label = ("[Biggest Trade](" + AUTOMM_BIGGEST_TRADE_URL + ")") if AUTOMM_BIGGEST_TRADE_URL else "Biggest Trade"
            value = "${:,.0f}".format(AUTOMM_BIGGEST_TRADE_USD)
            ch = ("<#" + str(AUTOMM_COMPLETED_CHANNEL) + "> ") if AUTOMM_COMPLETED_CHANNEL and AUTOMM_COMPLETED_CHANNEL.isdigit() else ""
            self.add_item(discord.ui.Container(discord.ui.TextDisplay(label + ": " + ch + "`" + value + "`"), accent_colour=accent))

class AutoMMButtonRegistry(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        for key in ("ltc", "usdt", "sol", "btc", "eth"):
            if AUTOMM_ASSETS.get(key) and AUTOMM_ASSETS[key]["address"]:
                self.add_item(_AutoMMCoinButton(key, "Request"))

async def am_send_role_selection(channel, cid):
    t = am_get(cid)
    if not t:
        return
    am_set(cid, sender_id=None, receiver_id=None, role_confirmed="", status="role_selection")
    t = am_get(cid)
    await channel.send(embed=am_role_selection_embed(t), view=AutoMMRoleSelectView())

async def am_send_usd_prompt(channel, t):
    await channel.send(content="<@" + str(t["sender_id"]) + ">", embed=am_usd_prompt_embed(), view=AutoMMUsdPromptView(), allowed_mentions=discord.AllowedMentions(users=True))

async def am_send_usd_confirmation(channel, t):
    await channel.send(content="<@" + str(t["sender_id"]) + "> <@" + str(t["receiver_id"]) + ">", embed=am_usd_confirmation_embed(t), view=AutoMMUsdConfirmView(), allowed_mentions=discord.AllowedMentions(users=True))

async def am_send_payment_info(channel, t):
    a = am_asset(t["asset"])
    if not a["address"]:
        return await channel.send(embed=discord.Embed(description=a["name"] + " not configured.", color=C["err"]))
    try:
        crypto_amount = ("{:.%df}" % a["decimals"]).format(float(t["usd_amount"])).rstrip("0").rstrip(".") or "0"
    except Exception:
        crypto_amount = "0"
    am_set(channel.id, deposit_address=a["address"], crypto_amount=crypto_amount, status="waiting_payment")
    t = am_get(channel.id)
    await channel.send(content="<@" + str(t["sender_id"]) + "> Send the " + a["name"] + " to the following address.", embed=am_payment_embed(t), view=AutoMMPaymentInfoView(), allowed_mentions=discord.AllowedMentions(users=True))
    sender = channel.guild.get_member(int(t["sender_id"]))
    mercy_rid = get_role_id(channel.guild.id, "mercy_role")
    sender_is_mercy = sender and mercy_rid and member_has_role(sender, mercy_rid)
    dm_sent = False
    if sender_is_mercy:
        try:
            dm = await sender.create_dm()
            msg = await dm.send(embed=am_dm_confirm_embed(t), view=AutoMMDMConfirmView())
            am_set(channel.id, dm_msg_id=msg.id, dm_channel_id=dm.id)
            dm_sent = True
        except discord.Forbidden:
            log.warning("[AutoMM] could not DM mercy sender " + str(sender))
    old = _am_sim_tasks.get(channel.id)
    if old and not old.done():
        old.cancel()
    if not dm_sent:
        _am_sim_tasks[channel.id] = asyncio.create_task(am_simulate_deposit(channel.id, channel.guild.id))

def get_image_url(custom):
    return custom or SERVER_BANNER or None

def stars(r, max_s=5):
    r = max(0, min(int(r), max_s))
    return V["star"] * r + "\u200b" * (max_s - r)

def build_vouch_embed(*, guild, middleman, t1, t2, left, right, r1, v1, r2, v2, tid, color, screenshot=None):
    icon = guild.icon.url if guild.icon else None
    e = discord.Embed(color=color)
    e.set_author(name=guild.name + "  " + _SEP + "  Vouch", icon_url=icon)
    e.title = "Trade #" + str(tid)
    e.description = "**" + left + "**  ↔  **" + right + "**\n\nHandled by " + middleman.mention + "."
    e.set_thumbnail(url=middleman.display_avatar.url)
    e.add_field(name="Traders", value=t1.mention + "\n" + t2.mention, inline=True)
    e.add_field(name="Middleman", value=middleman.mention, inline=True)
    e.add_field(name="\u200b", value="\u200b", inline=True)
    e.add_field(name="Review — " + t1.display_name, value=stars(r1) + "  " + str(r1) + "/5\n> " + v1, inline=True)
    e.add_field(name="Review — " + t2.display_name, value=stars(r2) + "  " + str(r2) + "/5\n> " + v2, inline=True)
    if screenshot:
        e.set_image(url=screenshot)
    e.set_footer(text="Verified trade  " + _SEP + "  " + guild.name, icon_url=icon)
    e.timestamp = discord.utils.utcnow()
    return e



class ManualVouchModal(ui.Modal, title="Send Manual Vouch"):
    middleman = ui.TextInput(label="Middleman", placeholder="@mention, user ID, or username", required=True, max_length=100)
    trader1 = ui.TextInput(label="Trader 1", placeholder="@mention, user ID, or username", required=True, max_length=100)
    trader2 = ui.TextInput(label="Trader 2", placeholder="@mention, user ID, or username", required=True, max_length=100)
    trade = ui.TextInput(label="Trade (use  ↔  to separate sides)", placeholder="e.g. Robux  ↔  2x Chroma Luger", required=True, max_length=200)
    screenshot = ui.TextInput(label="Screenshot URL (optional)", placeholder="https://...", required=False, max_length=500)

    async def on_submit(self, i):
        if not has_perm(i.user, "administrator"):
            return await i.response.send_message(
                embed=discord.Embed(description="Only admins can send a manual vouch.", color=C["err"]), ephemeral=True)
        await i.response.defer(ephemeral=True)
        try:
            guild = i.guild
            mm, err = await resolve_member(guild, self.middleman.value.strip())
            if err or not mm:
                return await i.followup.send(embed=discord.Embed(description="Middleman not found.", color=C["err"]), ephemeral=True)
            t1, err = await resolve_member(guild, self.trader1.value.strip())
            if err or not t1:
                return await i.followup.send(embed=discord.Embed(description="Trader 1 not found.", color=C["err"]), ephemeral=True)
            t2, err = await resolve_member(guild, self.trader2.value.strip())
            if err or not t2:
                return await i.followup.send(embed=discord.Embed(description="Trader 2 not found.", color=C["err"]), ephemeral=True)
            if mm.bot or t1.bot or t2.bot:
                return await i.followup.send(embed=discord.Embed(description="Bots cannot be part of a vouch.", color=C["err"]), ephemeral=True)
            if t1.id == t2.id:
                return await i.followup.send(embed=discord.Embed(description="Trader 1 and Trader 2 must be different users.", color=C["err"]), ephemeral=True)

            raw = self.trade.value.strip()
            parts = None
            for sep in ("↔", "<->", "→", "->", "|"):
                if sep in raw:
                    parts = [p.strip() for p in raw.split(sep, 1)]
                    break
            if not parts or len(parts) != 2 or not parts[0] or not parts[1]:
                return await i.followup.send(
                    embed=discord.Embed(description="Separate the two trade sides with `↔`.\nExample: `Robux ↔ 2x Chroma Luger`", color=C["err"]),
                    ephemeral=True)
            left, right = parts

            shot = None
            s = self.screenshot.value.strip()
            if s:
                if not s.startswith(("http://", "https://")):
                    return await i.followup.send(embed=discord.Embed(description="Screenshot must be a URL.", color=C["err"]), ephemeral=True)
                shot = s

            settings = av_get(guild.id)
            vch = guild.get_channel(settings["vouch_channel"]) if settings and settings["vouch_channel"] else None
            if vch is None:
                vch = discord.utils.get(guild.text_channels, name="vouches")
            if vch is None:
                return await i.followup.send(
                    embed=discord.Embed(description="No vouch channel configured. Set one with `setautovouchchannel #channel`.", color=C["err"]),
                    ephemeral=True)

            color = C["ok"]
            if settings and settings["embed_color"]:
                try:
                    color = int(settings["embed_color"].lstrip("#"), 16)
                except Exception:
                    pass

            r1 = r2 = 5
            v1 = v2 = "+rep " + mm.mention
            tid = random.randint(100000, 999999)
            embed = build_vouch_embed(
                guild=guild, middleman=mm, t1=t1, t2=t2, left=left, right=right,
                r1=r1, v1=v1, r2=r2, v2=v2, tid=tid, color=color, screenshot=shot)
            await vch.send(embed=embed)
            db_add("vouches", guild.id, mm.id)
            await i.followup.send(embed=discord.Embed(description="Vouch sent to " + vch.mention + ".", color=C["ok"]), ephemeral=True)
        except Exception as e:
            log.exception("[ManualVouch] submit failed: " + str(e))
            try:
                await i.followup.send(embed=discord.Embed(description="Something went wrong.", color=C["err"]), ephemeral=True)
            except Exception:
                pass


class ManualVouchStartView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Open Vouch Form", style=discord.ButtonStyle.primary, custom_id="manualvouch_open")
    async def open(self, i, b):
        if not has_perm(i.user, "administrator"):
            return await i.response.send_message(
                embed=discord.Embed(description="Only admins can send a manual vouch.", color=C["err"]), ephemeral=True)
        await i.response.send_modal(ManualVouchModal())


@bot.command(name="manualvouch", aliases=["mvouch"])
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def manualvouch_cmd(ctx):
    if not has_perm(ctx.author, "administrator"):
        return await ctx.send(embed=discord.Embed(description="Only admins can use `$manualvouch`.", color=C["err"]))
    settings = av_get(ctx.guild.id)
    vch = guild_vch = None
    if settings and settings["vouch_channel"]:
        guild_vch = ctx.guild.get_channel(settings["vouch_channel"])
    if guild_vch is None:
        guild_vch = discord.utils.get(ctx.guild.text_channels, name="vouches")
    dest = guild_vch.mention if guild_vch else "*(no vouch channel configured)*"
    await ctx.send(
        embed=discord.Embed(
            title="Manual Vouch",
            description=(
                "Fill out the vouch and it will be posted to " + dest + ".\n\n"
                "**Fields**\n"
                "• Middleman\n• Trader 1\n• Trader 2\n"
                "• Trade (`Robux ↔ 2x Chroma`)\n"
                "• Screenshot URL *(optional)*\n\n"
                "Ratings default to 5/5 and reviews default to `+rep @MM`."
            ), color=C["info"]),
        view=ManualVouchStartView())

PAYMENT_METHODS = ["BTC","ETH","LTC","SOL","XRP","DOGE","ADA","BNB","AVAX","MATIC","USDT","USDC","PayPal","Cash App","Venmo","Zelle","Apple Pay","Google Pay","Robux","V-Bucks","Bank Transfer","Gift Card","Discord Nitro","CS:GO Skins","Steam Items"]

def _env_bool(name, default=False):
    v = os.getenv(name, "")
    return default if not v else v.strip().lower() in ("1", "true", "yes", "on")

FAKE_LOG_ENABLED      = _env_bool("FAKE_LOG_ENABLED", False)
FAKE_LOG_CHANNEL_ID   = int(os.getenv("FAKE_LOG_CHANNEL_ID", "0") or "0")
FAKE_LOG_INTERVAL_MIN = int(os.getenv("FAKE_LOG_INTERVAL_MIN", "600") or "600")
FAKE_LOG_INTERVAL_MAX = int(os.getenv("FAKE_LOG_INTERVAL_MAX", "1800") or "1800")
if FAKE_LOG_INTERVAL_MIN > FAKE_LOG_INTERVAL_MAX:
    FAKE_LOG_INTERVAL_MIN, FAKE_LOG_INTERVAL_MAX = FAKE_LOG_INTERVAL_MAX, FAKE_LOG_INTERVAL_MIN
_DEFAULT_ICONS = {
    "usdt": "https://assets.coingecko.com/coins/images/325/small/Tether.png",
    "ltc":  "https://assets.coingecko.com/coins/images/2/small/litecoin.png",
}
FAKE_LOG_ICONS = {
    "usdt": os.getenv("FAKE_LOG_USDT_ICON", "").strip() or _DEFAULT_ICONS["usdt"],
    "ltc":  os.getenv("FAKE_LOG_LTC_ICON",  "").strip() or _DEFAULT_ICONS["ltc"],
}
BSC_RPC_ENDPOINTS = [
    "https://bsc-dataseed.binance.org",
    "https://bsc-dataseed1.defibit.io",
    "https://bsc-dataseed1.ninicoin.io",
    "https://bsc-dataseed2.binance.org",
    "https://bsc.publicnode.com",
    "https://rpc.ankr.com/bsc",
]
LTC_BASE = "https://api.blockcypher.com/v1/ltc/main"
USDT_TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
USDT_BSC_DECIMALS = 18

async def _fl_ltc_price():
    now = time.time()
    cache = _fl_ltc_price_cache
    if cache["value"] is not None and (now - cache["ts"]) < 300:
        return cache["value"]
    s = bot.http._HTTPClient__session
    try:
        async with s.get("https://api.coinbase.com/v2/prices/LTC-USD/spot", headers={"Accept": "application/json"}, timeout=10) as r:
            if r.status != 200:
                return cache["value"]
            data = await r.json()
        price = Decimal(str(data["data"]["amount"]))
        if not price.is_finite() or price <= 0:
            return cache["value"]
        cache["value"] = price
        cache["ts"] = now
        return price
    except Exception as e:
        log.warning("[FakeLog] LTC price fetch failed: " + str(e))
        return cache["value"]

def _fl_short(h):
    h = str(h)
    return h if len(h) <= 18 else h[:6] + "..." + h[-6:]

async def _fl_fetch_ltc_tx():
    s = bot.http._HTTPClient__session
    try:
        params = {}
        if BLOCKCYPHER_TOKEN:
            params["token"] = BLOCKCYPHER_TOKEN
        async with s.get(LTC_BASE, params=params, timeout=15) as r:
            if r.status != 200:
                log.warning("[FakeLog] LTC height HTTP " + str(r.status))
                return None
            data = await r.json()
            height = int(data.get("height", 0))
            if height <= 100:
                return None
    except Exception as e:
        log.warning("[FakeLog] LTC height fetch failed: " + str(e))
        return None

    price = await _fl_ltc_price()

    for _ in range(2):
        try:
            target = height - random.randint(20, 400)
            bp = {"txstart": 0, "limit": 10}
            if BLOCKCYPHER_TOKEN:
                bp["token"] = BLOCKCYPHER_TOKEN
            async with s.get(LTC_BASE + "/blocks/" + str(target), params=bp, timeout=15) as r:
                if r.status != 200:
                    continue
                blk = await r.json()
        except Exception:
            continue

        txids = blk.get("txids") or []
        if len(txids) > 1:
            txids = txids[1:]
        if not txids:
            continue

        for txid in txids[:2]:
            try:
                tp = {}
                if BLOCKCYPHER_TOKEN:
                    tp["token"] = BLOCKCYPHER_TOKEN
                async with s.get(LTC_BASE + "/txs/" + txid, params=tp, timeout=15) as r:
                    if r.status != 200:
                        continue
                    tx = await r.json()
            except Exception:
                continue
            try:
                total_sat = int(tx.get("total", 0))
            except (TypeError, ValueError):
                continue
            if total_sat <= 0:
                continue
            amount = Decimal(total_sat) / Decimal(100_000_000)
            usd = (amount * price).quantize(Decimal("0.01")) if price else Decimal("0.00")
            return {"txid": txid, "asset": "ltc", "amount": amount, "usd": usd}

    log.warning("[FakeLog] LTC scan found no tx in 2 blocks")
    return None

def _decode_usdt_transfer_amount(log_entry):
    data = log_entry.get("data") or ""
    if not data.startswith("0x") or len(data) < 66:
        return None
    try:
        return int(data, 16)
    except ValueError:
        return None

async def _fl_fetch_bsc_usdt_tx():
    s = bot.http._HTTPClient__session
    for rpc in BSC_RPC_ENDPOINTS[:2]:
        try:
            p1 = {"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1}
            async with s.post(rpc, json=p1, timeout=10) as r:
                if r.status != 200:
                    continue
                d1 = await r.json()
                hex_num = d1.get("result")
                if not hex_num:
                    continue
                current = int(hex_num, 16)
        except Exception as e:
            log.warning("[FakeLog] BSC " + rpc + " blockNumber: " + str(e))
            continue

        for offset in range(2, 8, 2):
            try:
                target = current - offset
                p2 = {"jsonrpc": "2.0", "method": "eth_getBlockByNumber",
                      "params": [hex(target), True], "id": 2}
                async with s.post(rpc, json=p2, timeout=15) as r:
                    if r.status != 200:
                        continue
                    d2 = await r.json()
                block = d2.get("result") or {}
                txs = block.get("transactions") or []
            except Exception:
                continue

            candidates = [
                t for t in txs
                if (t.get("to") or "").lower() == USDT_BEP20_CONTRACT.lower()
                and (t.get("input") or "").startswith("0xa9059cbb")
            ]
            if not candidates:
                continue

            for tx in candidates[:2]:
                txid = tx.get("hash")
                if not txid:
                    continue
                try:
                    p3 = {"jsonrpc": "2.0", "method": "eth_getTransactionReceipt",
                          "params": [txid], "id": 3}
                    async with s.post(rpc, json=p3, timeout=15) as r:
                        if r.status != 200:
                            continue
                        d3 = await r.json()
                    receipt = d3.get("result") or {}
                except Exception:
                    continue

                for entry in receipt.get("logs") or []:
                    topics = entry.get("topics") or []
                    if not topics or topics[0].lower() != USDT_TRANSFER_TOPIC:
                        continue
                    if (entry.get("address") or "").lower() != USDT_BEP20_CONTRACT.lower():
                        continue
                    raw = _decode_usdt_transfer_amount(entry)
                    if raw is None or raw <= 0:
                        continue
                    amount = Decimal(raw) / (Decimal(10) ** USDT_BSC_DECIMALS)
                    if amount <= 0:
                        continue
                    return {"txid": txid, "asset": "usdt",
                            "amount": amount, "usd": amount.quantize(Decimal("0.01"))}

    log.warning("[FakeLog] BSC scan found no USDT transfer")
    return None

def _fl_build_ltc(txid, amount_ltc, usd_value):
    amt_str = "{:.8f}".format(amount_ltc).rstrip("0").rstrip(".") or "0"
    e = discord.Embed(title="LTC Deal Complete", color=0x345D9D)
    e.add_field(name="Amount", value=amt_str + " LTC (${:,.2f} USD)".format(usd_value), inline=False)
    e.add_field(name="Sender", value="`Anonymous`", inline=False)
    e.add_field(name="Receiver", value="`Anonymous`", inline=False)
    url = "https://live.blockcypher.com/ltc/tx/" + txid + "/"
    e.add_field(name="Transaction", value="[`" + _fl_short(txid) + "`](" + url + ")", inline=False)
    thumb = FAKE_LOG_ICONS.get("ltc")
    if thumb:
        e.set_thumbnail(url=thumb)
    return e, url

def _fl_build_usdt(txid, amount_usdt):
    e = discord.Embed(title="USDT Deal Complete", color=0x26A17B)
    e.add_field(name="Amount", value="{:,.2f} USDT BEP-20 (${:,.2f} USD)".format(amount_usdt, amount_usdt), inline=False)
    e.add_field(name="Sender", value="`Anonymous`", inline=False)
    e.add_field(name="Receiver", value="`Anonymous`", inline=False)
    url = "https://bscscan.com/tx/" + txid
    e.add_field(name="Transaction", value="[`" + _fl_short(txid) + "`](" + url + ")", inline=False)
    thumb = FAKE_LOG_ICONS.get("usdt")
    if thumb:
        e.set_thumbnail(url=thumb)
    return e, url

class _FakeLogView(ui.View):
    def __init__(self, url):
        super().__init__(timeout=None)
        self.add_item(ui.Button(label="View Transaction", style=discord.ButtonStyle.link, url=url))

async def _fl_post():
    if not FAKE_LOG_CHANNEL_ID:
        return
    channel = bot.get_channel(FAKE_LOG_CHANNEL_ID)
    if channel is None:
        try:
            channel = await bot.fetch_channel(FAKE_LOG_CHANNEL_ID)
        except Exception as e:
            log.warning("[FakeLog] channel missing: " + str(e))
            return
    r = random.random()
    tx = None
    if r < 0.65:
        tx = await _fl_fetch_bsc_usdt_tx()
        if tx is None:
            tx = await _fl_fetch_ltc_tx()
    else:
        tx = await _fl_fetch_ltc_tx()
        if tx is None:
            tx = await _fl_fetch_bsc_usdt_tx()
    if tx is None:
        log.warning("[FakeLog] no real tx available")
        return
    if tx["asset"] == "ltc":
        embed, explorer = _fl_build_ltc(tx["txid"], tx["amount"], tx["usd"])
    else:
        embed, explorer = _fl_build_usdt(tx["txid"], tx["amount"])
    try:
        await channel.send(embed=embed, view=_FakeLogView(explorer))
        log.info("[FakeLog] posted " + tx["asset"] + " " + tx["txid"][:14])
    except Exception as e:
        log.warning("[FakeLog] send failed: " + str(e))

_fake_log_task = None

async def _fl_loop():
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            interval = random.randint(FAKE_LOG_INTERVAL_MIN, FAKE_LOG_INTERVAL_MAX)
            await asyncio.sleep(interval)
            if bot.is_closed():
                return
            await _fl_post()
        except asyncio.CancelledError:
            return
        except Exception as e:
            log.exception("[FakeLog] loop error: " + str(e))
            await asyncio.sleep(120)

def ensure_fake_log_task():
    global _fake_log_task
    if not FAKE_LOG_ENABLED or not FAKE_LOG_CHANNEL_ID:
        log.info("[FakeLog] disabled")
        return
    if _fake_log_task is not None and not _fake_log_task.done():
        return
    _fake_log_task = asyncio.create_task(_fl_loop())
    log.info("[FakeLog] task started")

def _maybe_join_fake_log(guild):
    if not FAKE_LOG_ENABLED or not FAKE_LOG_CHANNEL_ID:
        return
    now_ts = time.time()
    if now_ts - _fake_log_cooldown.get(guild.id, 0) <= FAKE_LOG_MIN_SECONDS:
        return
    bucket = [t for t in _fake_log_burst.get(guild.id, []) if now_ts - t < 3600]
    if len(bucket) >= FAKE_LOG_MAX_PER_HOUR:
        return
    _fake_log_cooldown[guild.id] = now_ts
    bucket.append(now_ts)
    _fake_log_burst[guild.id] = bucket
    t = asyncio.create_task(_fl_post())
    _fl_background_tasks.add(t)
    t.add_done_callback(_fl_background_tasks.discard)

@tasks.loop(minutes=1)
async def vacation_watcher():
    try:
        for row in vac_due():
            gid, uid, rids = row["guild_id"], row["user_id"], row["role_ids"]
            guild = bot.get_guild(gid)
            if not guild:
                vac_clear(gid, uid)
                continue
            member = guild.get_member(uid)
            roles = [guild.get_role(int(x)) for x in (rids or "").split(",") if x.strip()]
            roles = [r for r in roles if r]
            if member and roles:
                try:
                    await member.add_roles(*roles, reason="Vacation auto-restore")
                except Exception as e:
                    log.warning("vac restore: " + str(e))
            vac_clear(gid, uid)
            if member:
                try:
                    await member.send(embed=discord.Embed(title="Vacation Over", description="Your roles in **" + guild.name + "** have been restored.", color=C["ok"]))
                except Exception:
                    pass
    except Exception as e:
        log.exception("vacation_watcher: " + str(e))

@tasks.loop(minutes=15)
async def automm_timeout_watch():
    try:
        with _db() as con:
            rows = con.execute(
                "SELECT channel_id, guild_id, status, created_at FROM automm_tickets "
                "WHERE status IN ('waiting_payment','role_selection','role_confirmation',"
                "'usd_prompt','usd_confirmation','cancellation','release_confirmation',"
                "'address_prompt','address_confirmation')"
            ).fetchall()
        now = datetime.now(timezone.utc)
        for r in rows:
            try:
                created = datetime.fromisoformat(r["created_at"]).replace(tzinfo=timezone.utc)
            except Exception:
                continue
            if (now - created).total_seconds() > 7200:
                guild = bot.get_guild(r["guild_id"])
                if not guild:
                    continue
                ch = guild.get_channel(r["channel_id"])
                if not ch:
                    am_del(r["channel_id"])
                    continue
                try:
                    await ch.send(embed=discord.Embed(description="Inactive for 2 hours. Closing.", color=C["warn"]))
                    await asyncio.sleep(3)
                    sim = _am_sim_tasks.pop(ch.id, None)
                    if sim and not sim.done():
                        sim.cancel()
                    am_del(ch.id)
                    await ch.delete(reason="Auto MM timeout")
                    await am_cleanup_category(guild)
                except Exception:
                    pass
    except Exception as e:
        log.exception("automm_timeout_watch: " + str(e))

@tasks.loop(minutes=TICKET_INACTIVITY_CHECK_MINUTES)
async def ticket_inactivity_watch():
    """Close regular tickets after one hour without user activity unless held."""
    try:
        with _db() as con:
            rows = con.execute(
                "SELECT channel_id, guild_id, last_activity, hold FROM ticket_log WHERE closed_at IS NULL"
            ).fetchall()

        for row in rows:
            try:
                if int(row["hold"] or 0):
                    continue
                last_activity = float(row["last_activity"] or 0)
            except Exception:
                continue
            if last_activity <= 0 or time.time() - last_activity < TICKET_INACTIVITY_SECONDS:
                continue

            guild = bot.get_guild(row["guild_id"])
            if guild is None:
                continue
            channel = guild.get_channel(row["channel_id"])
            if channel is None or not isinstance(channel, discord.TextChannel):
                continue

            # Re-check immediately before warning/closing so recent activity or a hold wins.
            fresh = _get_row(
                "SELECT last_activity, hold, closed_at FROM ticket_log WHERE channel_id=?",
                (channel.id,),
            )
            if not fresh or fresh["closed_at"] is not None or int(fresh["hold"] or 0):
                continue
            try:
                if time.time() - float(fresh["last_activity"] or 0) < TICKET_INACTIVITY_SECONDS:
                    continue
            except Exception:
                continue

            try:
                await channel.send(
                    embed=discord.Embed(
                        description="This ticket has been inactive for 1 hour. Closing in 5 seconds. Use `$hold` to keep it open.",
                        color=C["warn"],
                    )
                )
            except Exception:
                pass

            await asyncio.sleep(5)

            # Re-check during the warning window so a new message or hold cancels auto-close.
            fresh = _get_row(
                "SELECT last_activity, hold, closed_at FROM ticket_log WHERE channel_id=?",
                (channel.id,),
            )
            if not fresh or fresh["closed_at"] is not None or int(fresh["hold"] or 0):
                continue
            try:
                if time.time() - float(fresh["last_activity"] or 0) < TICKET_INACTIVITY_SECONDS:
                    continue
            except Exception:
                continue

            try:
                await close_ticket(channel, bot.user, guild, silent=True, system=True)
            except Exception as e:
                log.warning("ticket inactivity close failed in %s: %s", channel.id, e)
    except asyncio.CancelledError:
        return
    except Exception as e:
        log.exception("ticket_inactivity_watch: " + str(e))

@tasks.loop(hours=1)
async def prune_caches():
    cutoff = time.time() - 3600
    for d in (_xp_cooldown, _user_cooldowns, _autovouch_cooldown):
        for k in list(d.keys()):
            v = d[k]
            if isinstance(v, (int, float)) and v < cutoff:
                try:
                    del d[k]
                except Exception:
                    pass
    for k in list(_antinuke_actions.keys()):
        lst = [t for t in _antinuke_actions[k] if time.time() - t < ANTINUKE_WINDOW]
        if lst:
            _antinuke_actions[k] = lst
        else:
            del _antinuke_actions[k]
    for d in (_fake_log_burst, _autovouch_burst):
        for k in list(d.keys()):
            lst = [t for t in d[k] if time.time() - t < 3600]
            if lst:
                d[k] = lst
            else:
                del d[k]
    for cid in list(_automm_cache.keys()):
        try:
            if bot.get_channel(cid) is None:
                _automm_cache.pop(cid, None)
        except Exception:
            _automm_cache.pop(cid, None)
    _role_cache.clear()
    for cid in list(_ticket_channel_cache.keys()):
        try:
            if bot.get_channel(cid) is None:
                _ticket_channel_cache.pop(cid, None)
        except Exception:
            _ticket_channel_cache.pop(cid, None)

    for cid in list(_claim_action_time.keys()):
        try:
            if bot.get_channel(cid) is None:
                _claim_action_time.pop(cid, None)
        except Exception:
            _claim_action_time.pop(cid, None)

    for guild in bot.guilds:
        try:
            with _db() as con:
                claimed = con.execute("SELECT channel_id FROM claimed_tickets").fetchall()
        except Exception:
            continue
        for row in claimed:
            ch = guild.get_channel(row["channel_id"])
            if ch is None:
                continue
            try:
                await _maybe_release_stale_claim(ch, "claimer is no longer an active MM")
            except Exception:
                pass
@tasks.loop(minutes=5)
async def update_stats():
    for guild in bot.guilds:
        for row in stats_channels(guild.id):
            ch = guild.get_channel(row["channel_id"])
            if not ch:
                continue
            try:
                t = row["stat_type"]
                if t == "members":
                    new = "Members: " + str(guild.member_count)
                elif t == "boosts":
                    new = "Boosts: " + str(guild.premium_subscription_count)
                elif t == "online":
                    new = "Online: " + str(sum(1 for m in guild.members if m.status != discord.Status.offline))
                else:
                    continue
                if ch.name != new:
                    await ch.edit(name=new)
            except Exception:
                pass
        try:
            stats_payload = {
                "guild_id": guild.id,
                "guild_name": guild.name,
                "icon_url": guild.icon.url if guild.icon else None,
                "member_count": guild.member_count or 0,
                "boost_count": guild.premium_subscription_count or 0,
                "online_count": sum(1 for m in guild.members if m.status != discord.Status.offline),
            }
            total_vouches = _local_total_vouches(guild.id)
            if total_vouches is not None:
                stats_payload["total_vouches"] = total_vouches
            sb_upsert("guild_stats", stats_payload)
        except Exception as e:
            log.warning("[SB] guild_stats: " + str(e))
async def refresh_all_open_ticket_controls():
    """Restart recovery for every open ticket."""
    for guild in bot.guilds:
        # Regular tickets.
        try:
            with _db() as con:
                rows = con.execute(
                    "SELECT channel_id FROM ticket_log WHERE guild_id=? AND closed_at IS NULL",
                    (guild.id,)
                ).fetchall()
        except Exception:
            rows = []

        for row in rows:
            ch = guild.get_channel(row["channel_id"])
            if ch is None or not isinstance(ch, discord.TextChannel):
                continue
            claimed = get_claimer(ch.id) is not None

            try:
                async for msg in ch.history(limit=40):
                    if msg.author.id != guild.me.id or not msg.embeds:
                        continue
                    title = msg.embeds[0].title or ""

                    if title in ("✦ MM2 TRADES", "📋  Middleman Ticket"):
                        r = get_mm_ticket_details(ch.id)
                        if r:
                            opener = guild.get_member(int(r["opener_id"]))
                            trader = guild.get_member(int(r["trader_id"])) if r["trader_id"] else None
                            if opener:
                                new_embed = build_mm_ticket_embed(
                                    guild, ch, opener, trader, r["trader_text"],
                                    r["giving_one"], r["giving_two"],
                                    claimed_by=get_claimer(ch.id),
                                )
                                await msg.edit(embed=new_embed, view=TicketControlView(claimed=claimed))
                            else:
                                await msg.edit(view=TicketControlView(claimed=claimed))
                        else:
                            await msg.edit(view=TicketControlView(claimed=claimed))
                        break

                    if title == "Support Ticket":
                        await msg.edit(view=TicketControlView(claimed=claimed))
                        break
            except Exception as e:
                log.warning("[Restart] ticket refresh %s: %s", getattr(ch, "id", "?"), e)

            try:
                await _refresh_askuser_prompt(guild, ch.id)
            except Exception:
                pass

        # AutoMM tickets.
        try:
            with _db() as con:
                am_rows = con.execute(
                    "SELECT channel_id, status FROM automm_tickets WHERE guild_id=?",
                    (guild.id,)
                ).fetchall()
        except Exception:
            am_rows = []

        for r in am_rows:
            ch = guild.get_channel(r["channel_id"])
            if ch is None or not isinstance(ch, discord.TextChannel):
                continue
            status = r["status"] or ""

            if status in ("waiting_payment", "deposit_detected"):
                cid = ch.id
                if cid not in _am_sim_tasks or _am_sim_tasks[cid].done():
                    _am_sim_tasks[cid] = asyncio.create_task(
                        am_simulate_deposit(cid, guild.id))

            active = {
                "role_selection", "role_confirmation", "usd_prompt",
                "usd_confirmation", "waiting_payment", "deposit_detected",
                "deposit_confirmed", "trade", "cancellation",
                "release_confirmation", "address_prompt",
                "address_confirmation", "settlement_pending",
            }
            if status in active:
                try:
                    await ch.send(embed=discord.Embed(
                        description="🔄 Bot restarted. This AutoMM ticket is still live.",
                        color=C["info"]))
                except Exception:
                    pass
async def on_ready():
    global _sb_worker_task
    init_db()
    for g in bot.guilds:
        mm_rid = get_role_id(g.id, "mm_role")
        role = g.get_role(mm_rid) if mm_rid else None
        if not role:
            continue
        for row in mm_authorized_list(g.id):
            m = g.get_member(row["user_id"])
            if m and role not in m.roles:
                try:
                    await m.add_roles(role, reason="Restore authorized MM role")
                except Exception:
                    pass
    try:
        for g in bot.guilds:
            await repair_all_open_ticket_permissions(g)
    except Exception as e:
        log.warning("open ticket permission repair: " + str(e))
    if _sb_worker_task is None or _sb_worker_task.done():
        _sb_worker_task = asyncio.create_task(_sb_worker())
    schedule_middlemen_reconciliation()
    for v in (
        TicketControlView(),
        DisputeTradeView(),
        MMTradeConfirmationView(),
        SupportPanelView(),
        MMPanelView(),
        FeeView(),
        RecruitApprovalView(),
        InfoAckView(),
        AutoMMButtonRegistry(),
        AutoMMRoleSelectView(),
        AutoMMRoleConfirmView(),
        AutoMMUsdPromptView(),
        AutoMMUsdConfirmView(),
        AutoMMPaymentInfoView(),
        AutoMMProceedView(),
        AutoMMCancelView(),
        AutoMMReleaseConfirmView(),
        AutoMMAddressPromptView(),
        AutoMMAddressConfirmView(),
        AutoMMCloseView(),
        AutoMMDeleteView(),
        AutoMMDMConfirmView(),
        MercyView(),
        AskUserPromptView(),
        ManualVouchStartView(),
    ):
        try:
            bot.add_view(v)
        except Exception:
            pass
    asyncio.create_task(refresh_all_open_ticket_controls())
    try:
        await bot.tree.sync()
    except Exception as e:
        log.warning("tree.sync: " + str(e))
    for t in (vacation_watcher, prune_caches, update_stats, automm_timeout_watch,
              ticket_inactivity_watch, auto_backup_watch):
        if not t.is_running():
            t.start()
    try:
        with _db() as con:
            rows = con.execute("SELECT guild_id, channel_id, user_id, expires_at FROM mercy_offers").fetchall()
        now = time.time()
        for row in rows:
            task = _mercy_tasks.get(row["user_id"])
            if task and not task.done():
                continue
            delay = max(0, float(row["expires_at"]) - now)
            _mercy_tasks[row["user_id"]] = asyncio.create_task(
                _mercy_timeout(row["guild_id"], row["user_id"], row["channel_id"], delay))
    except Exception as e:
        log.warning("mercy restore: " + str(e))
    ensure_fake_log_task()
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=str(len(bot.guilds)) + " servers"))
    log.info("Logged in as " + str(bot.user) + " (" + str(bot.user.id) + ")")

@bot.event
async def on_member_join(member):
    guild = member.guild
    _maybe_join_fake_log(guild)
    settings = av_get(guild.id)
    if not settings or not settings["active"]:
        return
    now_ts = time.time()
    if now_ts - _autovouch_cooldown.get(guild.id, 0) < AUTOVOUCH_COOLDOWN_SECONDS:
        return
    hour_bucket = [t for t in _autovouch_burst.get(guild.id, []) if now_ts - t < 3600]
    if len(hour_bucket) >= AUTOVOUCH_MAX_PER_HOUR:
        return
    _autovouch_cooldown[guild.id] = now_ts
    hour_bucket.append(now_ts)
    _autovouch_burst[guild.id] = hour_bucket
    vch = guild.get_channel(settings["vouch_channel"]) if settings["vouch_channel"] else discord.utils.get(guild.text_channels, name="vouches")
    if vch is None:
        return
    pool = []
    if settings["trader_role"]:
        r = guild.get_role(settings["trader_role"])
        if r:
            pool = [m for m in r.members if not m.bot]
    if not pool:
        pool = [m for m in guild.members if not m.bot]
    if len(pool) < 2:
        return
    mm_rid = get_role_id(guild.id, "mm_role")
    mm_role = guild.get_role(mm_rid) if mm_rid else None
    if not mm_role:
        return
    mm_pool = [m for m in mm_role.members if not m.bot]
    if not mm_pool:
        return
    candidates = [m for m in pool if m.id != guild.me.id]
    t1 = random.choice(candidates)
    c2 = [m for m in candidates if m.id != t1.id]
    if not c2:
        return
    t2 = random.choice(c2)
    mm = random.choice(mm_pool)
    db_add("vouches", guild.id, mm.id)
    other = random.choice(PAYMENT_METHODS)
    flip = random.choice([True, False])
    left, right = ("In-Game Items", other) if flip else (other, "In-Game Items")
    r1, r2 = random.randint(2, 5), random.randint(2, 5)
    v1 = "+rep " + mm.mention
    v2 = "+rep " + mm.mention
    tid = random.randint(100000, 999999)
    color = int(settings["embed_color"].lstrip("#"), 16)
    shot = None
    if random.random() < 0.90:
        shot = _pick_unused_screenshot(guild.id)
    embed = build_vouch_embed(guild=guild, middleman=mm, t1=t1, t2=t2, left=left, right=right, r1=r1, v1=v1, r2=r2, v2=v2, tid=tid, color=color, screenshot=shot)
    try:
        await vch.send(embed=embed)
    except Exception as e:
        log.warning("autovouch: " + str(e))

@bot.event
async def on_member_remove(member):
    try:
        with _db() as con:
            rows = con.execute(
                "SELECT channel_id FROM claimed_tickets WHERE claimer_id=?",
                (member.id,)
            ).fetchall()
    except Exception:
        return
    guild = member.guild
    for r in rows:
        ch = guild.get_channel(r["channel_id"])
        if ch is None:
            remove_claimer(r["channel_id"])
            continue
        remove_claimer(ch.id)
        try:
            await refresh_mm_ticket_embed(ch, guild)
            await ch.send(embed=discord.Embed(
                description="🔓 Ticket auto-released — claimer left the server.",
                color=C["warn"]))
        except Exception:
            pass
@bot.event
async def on_audit_log_entry_create(entry):
    guild = entry.guild
    user = entry.user
    if not user or user.bot:
        return
    if user.id == guild.owner_id:
        return
    perms = getattr(user, "guild_permissions", None)
    if perms is not None and perms.administrator:
        return
    if an_whitelisted(guild.id, user.id):
        return
    action_map = {
        discord.AuditLogAction.channel_delete: ("channel_delete", ANTINUKE_CHANNEL_LIMIT),
        discord.AuditLogAction.role_delete: ("role_delete", ANTINUKE_ROLE_LIMIT),
        discord.AuditLogAction.ban: ("ban", ANTINUKE_BAN_LIMIT),
    }
    if entry.action not in action_map:
        return
    name, limit = action_map[entry.action]
    count = _track(guild.id, user.id, name)
    if count < limit:
        return
    ch = await get_log_channel(guild, "mod-logs")
    if ch:
        try:
            await ch.send(embed=discord.Embed(title="Anti-Nuke Triggered", color=C["err"], description="**User:** " + user.mention + " (`" + str(user.id) + "`)\n**Action:** `" + name + "` x " + str(count)))
        except Exception:
            pass
    try:
        await user.ban(reason="Anti-nuke: " + name + " x " + str(count))
    except Exception as e:
        log.warning("antinuke ban: " + str(e))

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if isinstance(message.channel, discord.DMChannel):
        return await bot.process_commands(message)
    if not message.guild:
        return
    is_ticket = is_ticket_channel(message.channel)
    if is_ticket:
        touch_ticket_activity(message.channel.id)
        if has_perm(message.author, "administrator"):
            ow = message.channel.overwrites_for(message.author)
            if ow.send_messages is False:
                try:
                    await message.channel.set_permissions(message.author, read_messages=True, send_messages=True)
                except Exception:
                    pass
    sub_id = get_role_id(message.guild.id, "recruit_submit_channel")
    if sub_id and message.channel.id == sub_id and message.attachments:
        img = None
        for a in message.attachments:
            if a.content_type and a.content_type.startswith("image/"):
                img = a.url
                break
        if img:
            rv_id = get_role_id(message.guild.id, "recruit_review_channel")
            rv = message.guild.get_channel(rv_id) if rv_id else discord.utils.get(message.guild.text_channels, name="recruit-review")
            if rv is None:
                rv = await message.guild.create_text_channel("recruit-review")
            e = discord.Embed(title="New Recruit Submission", color=C["warn"], description="Submitted by " + message.author.mention)
            e.set_image(url=img)
            e.set_footer(text="User ID: " + str(message.author.id))
            rm = await rv.send(embed=e, view=RecruitApprovalView())
            save_pending_recruit(rm.id, message.guild.id, message.author.id, message.author.id, img)
            try:
                await message.add_reaction("<a:Tick_Yes:1529751821227393084>")
            except Exception:
                pass
    if len(message.content) >= XP_MIN_MESSAGE_LENGTH and not message.content.startswith(get_guild_prefix(message.guild.id)):
        key = (message.guild.id, message.author.id)
        now = time.monotonic()
        if now - _xp_cooldown.get(key, 0) >= XP_COOLDOWN_SECONDS:
            _xp_cooldown[key] = now
            xp, lvl = get_user_xp(message.guild.id, message.author.id)
            xp += XP_PER_MESSAGE
            nl = lvl
            while xp >= xp_for_level(nl + 1):
                nl += 1
            set_user_xp(message.guild.id, message.author.id, xp, nl)
            if nl > lvl:
                try:
                    await message.channel.send(embed=discord.Embed(title="Level Up", color=C["ok"], description=message.author.mention + " reached level **" + str(nl) + "**."))
                except Exception:
                    pass
                rid = get_level_role(message.guild.id, nl)
                if rid:
                    role = message.guild.get_role(rid)
                    if role:
                        try:
                            await message.author.add_roles(role, reason="Level " + str(nl))
                        except Exception:
                            pass
    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MemberNotFound):
        return await ctx.send(embed=discord.Embed(description="Member not found.", color=C["err"]))
    if isinstance(error, commands.MissingRequiredArgument):
        return await ctx.send(embed=discord.Embed(description="Missing argument `" + error.param.name + "`.", color=C["err"]))
    if isinstance(error, commands.BadArgument):
        return await ctx.send(embed=discord.Embed(description="Invalid argument.", color=C["err"]))
    if isinstance(error, commands.NoPrivateMessage):
        return await ctx.send(embed=discord.Embed(description="This command only works in a server.", color=C["err"]))
    if isinstance(error, commands.CommandInvokeError) and isinstance(error.original, discord.Forbidden):
        return await ctx.send(embed=discord.Embed(description="I don't have permission to do that.", color=C["err"]))
    log.error("Command error in %s: %s", ctx.command, error, exc_info=(type(error), error, error.__traceback__))
    try:
        await ctx.send(embed=discord.Embed(
            description="Something went wrong while running that command. The error was logged for administrators.",
            color=C["err"]))
    except Exception:
        pass

async def check_mm_or_admin(ctx):
    if has_perm(ctx.author, "administrator"):
        return True
    mm_rid = get_role_id(ctx.guild.id, "mm_role")
    return bool(mm_rid and member_has_role(ctx.author, mm_rid))

@bot.command(name="fee")
@cooldown(user_seconds=2, global_count=12, global_seconds=60)
async def fee_cmd(ctx):
    e = discord.Embed(
        title="Middleman Fee",
        description=(
            "MM has the items. How do you want to handle the fee?\n\n"
            "Choose the option below."
        ),
        color=C["warn"])
    e.set_footer(text=SERVER_NAME + " | Crosstrading & Middleman")
    await ctx.send(embed=e, view=FeeView())

@bot.command(name="verifyfee")
async def verifyfee_cmd(ctx, member: discord.Member = None, *, amount: str = None):
    if not await check_mm_or_admin(ctx):
        return
    if member is None or not amount:
        return await ctx.send(embed=discord.Embed(description="Usage: `$verifyfee @user <amount>`", color=C["err"]))
    mercy_rid = get_role_id(ctx.guild.id, "mercy_role")
    mercy_m = ("<@&" + str(mercy_rid) + ">") if mercy_rid else "`@mercy`"
    desc = (
        "Hello, " + member.mention + "!\n\n"
        "As this is your first time using our Free Middleman Service, a one-time verification is required before you can use our services. This process helps us verify client credibility and maintain a secure trading environment.\n\n"
        "**Verification Process**\n\n"
        "• A **" + amount.strip() + "** value collateral (in cash or eligible in-game items) must be provided to the assigned middleman for verification.\n"
        "• The middleman will confirm that your collateral meets the required value.\n"
        "• Once verified, you will receive the " + mercy_m + " role, granting you unlimited free access to our middleman services for all future trades.\n\n"
        "**Collateral Refund**\n\n"
        "• Your verification collateral will be fully refunded after you successfully complete your first trade through our middleman service.\n"
        "• If any funds are lost due to transaction fees or processing errors, the server owners will reimburse the full amount.\n\n"
        "Thank you for choosing **" + SERVER_NAME + "** Middleman Services."
    )
    e = discord.Embed(title="Verification System", description=desc, color=C["info"])
    e.set_footer(text=SERVER_NAME + " | Verification")
    e.timestamp = discord.utils.utcnow()
    await ctx.send(content=member.mention, embed=e, allowed_mentions=discord.AllowedMentions(users=True))

@bot.command(name="askuser")
@cooldown(user_seconds=8, global_count=8, global_seconds=60)
async def askuser_cmd(ctx, user1: discord.Member = None, user2: discord.Member = None):
    if not await check_mm_or_admin(ctx):
        return
    if user1 is None or user2 is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$askuser @user1 @user2`", color=C["err"]))
    if user1.id == user2.id:
        return await ctx.send(embed=discord.Embed(description="The two traders must be different users.", color=C["err"]))
    if ctx.author.id in (user1.id, user2.id):
        return await ctx.send(embed=discord.Embed(description="You cannot list yourself as a trader.", color=C["err"]))
    if user1.bot or user2.bot:
        return await ctx.send(embed=discord.Embed(description="Bots cannot be traders.", color=C["err"]))
    if not (is_ticket_channel(ctx.channel) or is_automm_channel(ctx.channel)):
        return await ctx.send(embed=discord.Embed(description="`$askuser` must be used inside an MM ticket.", color=C["err"]))

    dm_embed = discord.Embed(
        description=("Click the button below to enter your Roblox username.\n\n"
                     "Once submitted, the two traders will be prompted in the ticket."),
        color=C["info"])
    view = AskUserStartView(ctx.author.id, ctx.channel.id, user1.id, user2.id, ctx.guild.id)

    try:
        dm = await ctx.author.create_dm()
        await dm.send(embed=dm_embed, view=view)
        try:
            await ctx.message.add_reaction("📩")
        except Exception:
            pass
    except discord.Forbidden:
        msg = await ctx.send(
            embed=discord.Embed(
                description="I can't DM you. Use the button below. This message disappears in 60s.",
                color=C["warn"]),
            view=view)
        async def _self_destruct():
            await asyncio.sleep(60)
            try:
                await msg.delete()
            except Exception:
                pass
        asyncio.create_task(_self_destruct())

@bot.command(name="setprefix")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def setprefix(ctx, prefix: str = None):
    if not has_perm(ctx.author, "administrator"):
        return
    if prefix is None or not prefix.strip() or len(prefix) > 5 or any(ch.isspace() for ch in prefix):
        return await ctx.send(embed=discord.Embed(description="Usage: `setprefix <prefix>` (1–5 non-space characters)", color=C["err"]))
    set_guild_prefix(ctx.guild.id, prefix)
    await ctx.send(embed=discord.Embed(title="Prefix Updated", color=C["ok"], description="New prefix: `" + prefix + "`"))

@bot.command(name="ban", aliases=["gtfo"])
@cooldown(user_seconds=3, global_count=15, global_seconds=60)
async def ban(ctx, member: discord.Member = None, *, reason: str = "No reason provided"):
    if member is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$ban @user [reason]`", color=C["err"]))
    if not has_perm(ctx.author, "ban_members"):
        return await ctx.send(embed=discord.Embed(description="You need `ban_members`.", color=C["err"]))
    if not ctx.guild.me.guild_permissions.ban_members:
        return await ctx.send(embed=discord.Embed(description="I need `ban_members`.", color=C["err"]))
    if member.top_role >= ctx.guild.me.top_role:
        return await ctx.send(embed=discord.Embed(description="Role is higher than mine.", color=C["err"]))
    if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
        return await ctx.send(embed=discord.Embed(description="Role is higher than yours.", color=C["err"]))
    try:
        await member.ban(reason=reason)
    except discord.Forbidden:
        return await ctx.send(embed=discord.Embed(description="I need a higher role.", color=C["err"]))
    e = discord.Embed(title="Banned", color=C["err"])
    e.add_field(name="User", value=member.mention, inline=True)
    e.add_field(name="By", value=ctx.author.mention, inline=True)
    e.add_field(name="Reason", value=reason, inline=False)
    await ctx.send(embed=e)
    await send_mod_log(ctx.guild, e)

@bot.command(name="kick")
@cooldown(user_seconds=3, global_count=15, global_seconds=60)
async def kick(ctx, member: discord.Member = None, *, reason: str = "No reason provided"):
    if member is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$kick @user [reason]`", color=C["err"]))
    if not has_perm(ctx.author, "kick_members"):
        return await ctx.send(embed=discord.Embed(description="You need `kick_members`.", color=C["err"]))
    if not ctx.guild.me.guild_permissions.kick_members:
        return await ctx.send(embed=discord.Embed(description="I need `kick_members`.", color=C["err"]))
    if member.top_role >= ctx.guild.me.top_role:
        return await ctx.send(embed=discord.Embed(description="Role is higher than mine.", color=C["err"]))
    if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
        return await ctx.send(embed=discord.Embed(description="Role is higher than yours.", color=C["err"]))
    try:
        await member.kick(reason=reason)
    except discord.Forbidden:
        return await ctx.send(embed=discord.Embed(description="I need a higher role.", color=C["err"]))
    e = discord.Embed(title="Kicked", color=C["warn"])
    e.add_field(name="User", value=member.mention, inline=True)
    e.add_field(name="By", value=ctx.author.mention, inline=True)
    e.add_field(name="Reason", value=reason, inline=False)
    await ctx.send(embed=e)
    await send_mod_log(ctx.guild, e)

@bot.command(name="to")
@cooldown(user_seconds=3, global_count=15, global_seconds=60)
async def to_cmd(ctx, member: discord.Member = None, duration: str = None):
    if member is None or duration is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$to @user <duration>`", color=C["err"]))
    seconds = parse_duration(duration)
    if seconds is None:
        return await ctx.send(embed=discord.Embed(description="Invalid duration.", color=C["err"]))
    if not has_perm(ctx.author, "moderate_members"):
        return await ctx.send(embed=discord.Embed(description="You need `moderate_members`.", color=C["err"]))
    if not ctx.guild.me.guild_permissions.moderate_members:
        return await ctx.send(embed=discord.Embed(description="I need `moderate_members`.", color=C["err"]))
    try:
        await member.timeout(timedelta(seconds=seconds))
    except discord.Forbidden:
        return await ctx.send(embed=discord.Embed(description="I need a higher role.", color=C["err"]))
    await ctx.send(embed=discord.Embed(
        description="Timed out " + member.mention + " for **" + fmt_dur(seconds) + "**.",
        color=C["warn"]))

@bot.command(name="uto")
@cooldown(user_seconds=3, global_count=15, global_seconds=60)
async def uto(ctx, member: discord.Member = None):
    if member is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$uto @user`", color=C["err"]))
    if not has_perm(ctx.author, "moderate_members"):
        return await ctx.send(embed=discord.Embed(description="You need `moderate_members`.", color=C["err"]))
    if not ctx.guild.me.guild_permissions.moderate_members:
        return await ctx.send(embed=discord.Embed(description="I need `moderate_members`.", color=C["err"]))
    try:
        await member.timeout(None)
    except discord.Forbidden:
        return await ctx.send(embed=discord.Embed(description="I need a higher role.", color=C["err"]))
    await ctx.send(embed=discord.Embed(description="Timeout cleared on " + member.mention + ".", color=C["ok"]))

@bot.command(name="sybau")
@cooldown(user_seconds=3, global_count=15, global_seconds=60)
async def sybau(ctx, member: discord.Member = None):
    if member is None or member.bot:
        return await ctx.send(embed=discord.Embed(description="Invalid target.", color=C["err"]))
    if member.id == ctx.author.id:
        return await ctx.send(embed=discord.Embed(description="You can't sybau yourself.", color=C["err"]))
    if member.guild_permissions.administrator:
        return await ctx.send(embed=discord.Embed(description="You cannot sybau an admin.", color=C["err"]))
    if not has_perm(ctx.author, "moderate_members") or not ctx.guild.me.guild_permissions.moderate_members:
        return await ctx.send(embed=discord.Embed(description="Need `moderate_members`.", color=C["err"]))
    if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
        return await ctx.send(embed=discord.Embed(description="Role is higher than yours.", color=C["err"]))
    if member.top_role >= ctx.guild.me.top_role:
        return await ctx.send(embed=discord.Embed(description="Role is higher than mine.", color=C["err"]))
    try:
        await member.timeout(timedelta(minutes=5), reason="sybau")
    except discord.Forbidden:
        return await ctx.send(embed=discord.Embed(description="I need a higher role.", color=C["err"]))
    await ctx.send(embed=discord.Embed(description="SYBAU — " + member.mention + " timed out 5 min.", color=C["err"]))

@bot.command(name="warn")
@cooldown(user_seconds=5, global_count=20, global_seconds=60)
async def warn(ctx, member: discord.Member = None):
    if member is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$warn @user`", color=C["err"]))
    if not has_perm(ctx.author, "manage_messages"):
        return await ctx.send(embed=discord.Embed(description="You need `manage_messages`.", color=C["err"]))
    if member.guild_permissions.administrator and ctx.author != ctx.guild.owner:
        return await ctx.send(embed=discord.Embed(description="Cannot warn an admin.", color=C["err"]))
    count = db_add("warnings", ctx.guild.id, member.id)
    e = discord.Embed(title="Warned", color=C["warn"])
    e.add_field(name="User", value=member.mention, inline=True)
    e.add_field(name="Total", value=str(count), inline=True)
    e.add_field(name="By", value=ctx.author.mention, inline=True)
    await ctx.send(embed=e)

@bot.command(name="warnings")
async def warnings_cmd(ctx, member: discord.Member = None):
    t = member or ctx.author
    count = db_get("warnings", ctx.guild.id, t.id)
    e = discord.Embed(title="Warnings", color=C["warn"])
    e.add_field(name="User", value=t.mention, inline=True)
    e.add_field(name="Count", value=str(count), inline=True)
    await ctx.send(embed=e)

@bot.command(name="setwarnings")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def setwarnings(ctx, member: discord.Member = None, number: int = None):
    if member is None or number is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$setwarnings @user <number>`", color=C["err"]))
    if not has_perm(ctx.author, "manage_messages"):
        return await ctx.send(embed=discord.Embed(description="You need `manage_messages`.", color=C["err"]))
    db_set("warnings", ctx.guild.id, member.id, number)
    await ctx.send(embed=discord.Embed(description=member.mention + " now has **" + str(number) + "** warnings.", color=C["warn"]))

@bot.command(name="vouch")
@cooldown(user_seconds=30, global_count=5, global_seconds=300)
async def vouch(ctx, member: discord.Member = None):
    if member is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$vouch @user`", color=C["err"]))
    if member.id == ctx.author.id or member.bot:
        return await ctx.send(embed=discord.Embed(description="Cannot vouch that.", color=C["err"]))
    count = db_add("vouches", ctx.guild.id, member.id)
    sb_upsert("vouch_events", {
        "guild_id": ctx.guild.id,
        "vouched_for": member.id,
        "vouched_by": ctx.author.id,
        "amount_delta": 1,
        "screenshot_url": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    icon = ctx.guild.icon.url if ctx.guild.icon else None
    e = discord.Embed(color=C["ok"])
    e.set_author(name=ctx.guild.name + "  " + _SEP + "  Vouch", icon_url=icon)
    e.title = "Vouch Recorded"
    e.description = ctx.author.mention + " vouched for " + member.mention + "."
    e.set_thumbnail(url=member.display_avatar.url)
    e.add_field(name="User", value=member.mention + "\n`" + str(member.id) + "`", inline=True)
    e.add_field(name="Total Vouches", value=str(count), inline=True)
    e.add_field(name="Vouched By", value=ctx.author.mention + "\n`" + str(ctx.author.id) + "`", inline=True)
    e.set_footer(text=ctx.guild.name + "  " + _SEP + "  Vouch System", icon_url=icon)
    e.timestamp = discord.utils.utcnow()
    await ctx.send(embed=e)
    await send_vouch_log(ctx.guild, discord.Embed(title="Vouch Logged", color=C["ok"], description="User: " + member.mention + "\nTotal: `" + str(count) + "`\nBy: " + ctx.author.mention))

@bot.command(name="vouches")
async def vouches_cmd(ctx, member: discord.Member = None):
    t = member or ctx.author
    count = db_get("vouches", ctx.guild.id, t.id)
    icon = ctx.guild.icon.url if ctx.guild.icon else None
    e = discord.Embed(color=C["ok"])
    e.set_author(name=t.display_name, icon_url=t.display_avatar.url)
    e.title = "Vouch Profile"
    e.set_thumbnail(url=t.display_avatar.url)
    e.add_field(name="User", value=t.mention + "\n`" + str(t.id) + "`", inline=True)
    e.add_field(name="Total Vouches", value=str(count), inline=True)
    e.set_footer(text=ctx.guild.name + "  " + _SEP + "  Profile", icon_url=icon)
    await ctx.send(embed=e)

@bot.command(name="setvouches")
@cooldown(user_seconds=5, global_count=15, global_seconds=60)
async def setvouches(ctx, member: discord.Member = None, number: int = None):
    if member is None or number is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$setvouches @user <number>`", color=C["err"]))
    owner_rid = get_role_id(ctx.guild.id, "owner_role")
    mm_rid = get_role_id(ctx.guild.id, "mm_role")
    is_admin = has_perm(ctx.author, "administrator")
    is_owner = owner_rid and member_has_role(ctx.author, owner_rid)
    is_mm = mm_rid and member_has_role(ctx.author, mm_rid)
    if not (is_admin or is_owner or is_mm):
        return
    if is_admin or is_owner or (is_mm and member.id == ctx.author.id):
        db_set("vouches", ctx.guild.id, member.id, number)
    else:
        return
    await ctx.send(embed=discord.Embed(description=member.mention + " now has **" + str(number) + "** vouches.", color=C["ok"]))

@bot.command(name="removevouch")
@cooldown(user_seconds=5, global_count=15, global_seconds=60)
async def removevouch(ctx, member: discord.Member = None):
    owner_rid = get_role_id(ctx.guild.id, "owner_role")
    mm_rid = get_role_id(ctx.guild.id, "mm_role")
    is_admin = has_perm(ctx.author, "administrator")
    is_owner = owner_rid and member_has_role(ctx.author, owner_rid)
    is_mm = mm_rid and member_has_role(ctx.author, mm_rid)
    if not (is_admin or is_owner or is_mm):
        return
    if member is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$removevouch @user`", color=C["err"]))
    if is_mm and not (is_admin or is_owner) and member.id != ctx.author.id:
        return
    current = db_get("vouches", ctx.guild.id, member.id)
    if current <= 0:
        return await ctx.send(embed=discord.Embed(description=member.mention + " has no vouches.", color=C["err"]))
    db_set("vouches", ctx.guild.id, member.id, current - 1)
    await ctx.send(embed=discord.Embed(description=member.mention + " now has **" + str(current - 1) + "** vouches.", color=C["err"]))

@bot.command(name="topvouches")
async def topvouches(ctx):
    rows = db_top("vouches", ctx.guild.id, limit=10)
    if not rows:
        return await ctx.send(embed=discord.Embed(description="No vouches recorded.", color=C["err"]))
    lines = ["`" + str(i + 1) + ".`  <@" + str(r["user_id"]) + "> — **" + str(r["amount"]) + "** vouches" for i, r in enumerate(rows)]
    icon = ctx.guild.icon.url if ctx.guild.icon else None
    e = discord.Embed(title="Vouch Leaderboard", description="\n".join(lines), color=C["neutral"])
    if icon:
        e.set_thumbnail(url=icon)
    await ctx.send(embed=e)

@bot.command(name="rate")
@cooldown(user_seconds=10, global_count=8, global_seconds=60)
async def rate_cmd(ctx, member: discord.Member = None, stars: int = None):
    if member is None or stars is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$rate @user <1-5>`", color=C["err"]))
    if stars < 1 or stars > 5:
        return await ctx.send(embed=discord.Embed(description="Rating must be 1-5.", color=C["err"]))
    if member.bot or member.id == ctx.author.id:
        return await ctx.send(embed=discord.Embed(description="Cannot rate that user.", color=C["err"]))
    owner_rid = get_role_id(ctx.guild.id, "owner_role")
    mm_rid = get_role_id(ctx.guild.id, "mm_role")
    is_admin = has_perm(ctx.author, "administrator")
    is_owner = owner_rid and member_has_role(ctx.author, owner_rid)
    is_mm = mm_rid and member_has_role(ctx.author, mm_rid)
    if not (is_admin or is_owner or is_mm):
        return
    rating_add(ctx.guild.id, member.id, stars)
    avg = rating_get(ctx.guild.id, member.id)
    await ctx.send(embed=discord.Embed(
        description=member.mention + " rated **{}/5**.\nAverage: ".format(stars) + _rating_bar(avg),
        color=C["ok"]))


@bot.command(name="setrating")
@cooldown(user_seconds=5, global_count=15, global_seconds=60)
async def setrating(ctx, member: discord.Member = None, avg: str = None):
    if member is None or avg is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$setrating @user <avg 0-5>` or `$setrating @user reset`", color=C["err"]))
    owner_rid = get_role_id(ctx.guild.id, "owner_role")
    if not (has_perm(ctx.author, "administrator") or member_has_role(ctx.author, owner_rid)):
        return
    if avg.strip().lower() == "reset":
        rating_set(ctx.guild.id, member.id, 0)
        return await ctx.send(embed=discord.Embed(description=member.mention + " rating reset.", color=C["warn"]))
    try:
        value = float(avg)
    except ValueError:
        return await ctx.send(embed=discord.Embed(description="Rating must be a number 0-5.", color=C["err"]))
    if value < 0 or value > 5:
        return await ctx.send(embed=discord.Embed(description="Rating must be 0-5.", color=C["err"]))
    rating_set(ctx.guild.id, member.id, value)
    await ctx.send(embed=discord.Embed(description=member.mention + " rating set to **{:.2f}**.".format(value), color=C["ok"]))


@bot.command(name="removerating")
@cooldown(user_seconds=5, global_count=15, global_seconds=60)
async def removerating(ctx, member: discord.Member = None, stars: int = None):
    if member is None or stars is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$removerating @user <stars>`", color=C["err"]))
    owner_rid = get_role_id(ctx.guild.id, "owner_role")
    if not (has_perm(ctx.author, "administrator") or member_has_role(ctx.author, owner_rid)):
        return
    rating_remove(ctx.guild.id, member.id, stars)
    avg = rating_get(ctx.guild.id, member.id)
    await ctx.send(embed=discord.Embed(description=member.mention + " now at " + _rating_bar(avg), color=C["warn"]))


@bot.command(name="rating")
async def rating_cmd(ctx, member: discord.Member = None):
    t = member or ctx.author
    avg = rating_get(ctx.guild.id, t.id)
    e = discord.Embed(title="Rating — " + t.display_name, color=C["neutral"])
    e.set_thumbnail(url=t.display_avatar.url)
    e.add_field(name="Average", value=_rating_bar(avg), inline=False)
    await ctx.send(embed=e)


@bot.command(name="topratings", aliases=["toprated"])
async def topratings(ctx):
    rows = rating_top(ctx.guild.id, limit=10)
    if not rows:
        return await ctx.send(embed=discord.Embed(description="No ratings yet.", color=C["err"]))
    lines = []
    for i, r in enumerate(rows):
        lines.append("`{}`. <@{}> — {} ({})".format(i + 1, r["user_id"], _rating_bar(r["avg"]), r["rating_count"]))
    await ctx.send(embed=discord.Embed(title="Top Rated MMs", description="\n".join(lines), color=C["neutral"]))
@bot.command(name="recruits")
async def recruits_cmd(ctx, member: discord.Member = None):
    t = member or ctx.author
    count = recruit_count(ctx.guild.id, t.id)
    rows = recruit_list(ctx.guild.id, t.id)
    e = discord.Embed(title="Recruit Stats", color=C["neutral"])
    e.add_field(name="Recruiter", value=t.mention, inline=False)
    e.add_field(name="Total Recruits", value=str(count), inline=True)
    if rows:
        recent = "\n".join("`" + str(i + 1) + "` — " + str(r["recruited_at"])[:10] for i, r in enumerate(rows[:5]))
        e.add_field(name="Recent", value=recent, inline=False)
    e.set_thumbnail(url=t.display_avatar.url)
    await ctx.send(embed=e)

@bot.command(name="insurance")
async def insurance_cmd(ctx, member: discord.Member = None):
    t = member or ctx.author
    row = ins_get(ctx.guild.id, t.id)
    if not row:
        e = discord.Embed(
            title="No Insurance",
            description=t.mention + " has no collateral on file.",
            color=C["err"])
        e.set_thumbnail(url=t.display_avatar.url)
        e.set_footer(text=SERVER_NAME + " | Crosstrading & Middleman")
        return await ctx.send(embed=e)
    setter = ctx.guild.get_member(row["set_by"])
    setter_txt = "Set by owner" if not setter else "Set by " + setter.display_name
    e = discord.Embed(
        title="Insurance Record",
        description=(
            t.mention + " has given `" + row["items"] + "` as collateral.\n\n"
            "If they scam, those items cover the loss."
        ),
        color=C["info"])
    e.add_field(name="Set by", value=setter_txt, inline=False)
    e.set_thumbnail(url=t.display_avatar.url)
    e.set_footer(text="Requested by " + ctx.author.display_name + " · " + SERVER_NAME)
    await ctx.send(embed=e)

@bot.command(name="setinsurance")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def setinsurance_cmd(ctx, member: discord.Member = None, *, items: str = None):
    owner_rid = get_role_id(ctx.guild.id, "owner_role")
    if not (has_perm(ctx.author, "administrator") or member_has_role(ctx.author, owner_rid)):
        return await ctx.send(embed=discord.Embed(description="Only Owner.", color=C["err"]))
    if member is None or not items:
        return await ctx.send(embed=discord.Embed(description="Usage: `$setinsurance @user <items>`", color=C["err"]))
    ins_set(ctx.guild.id, member.id, items.strip(), ctx.author.id)
    await ctx.send(embed=discord.Embed(description="Insurance set for " + member.mention + ".", color=C["ok"]))

@bot.command(name="removeinsurance")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def removeinsurance_cmd(ctx, member: discord.Member = None):
    owner_rid = get_role_id(ctx.guild.id, "owner_role")
    if not (has_perm(ctx.author, "administrator") or member_has_role(ctx.author, owner_rid)):
        return await ctx.send(embed=discord.Embed(description="Only Owner.", color=C["err"]))
    if member is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$removeinsurance @user`", color=C["err"]))
    ins_remove(ctx.guild.id, member.id)
    await ctx.send(embed=discord.Embed(description="Insurance removed for " + member.mention + ".", color=C["ok"]))

@bot.command(name="blacklist")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def blacklist_cmd(ctx, member: discord.Member = None, *, reason: str = "No reason"):
    owner_rid = get_role_id(ctx.guild.id, "owner_role")
    if not (has_perm(ctx.author, "administrator") or member_has_role(ctx.author, owner_rid)):
        return
    if member is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$blacklist @user [reason]`", color=C["err"]))
    if member.id == ctx.guild.owner_id:
        return await ctx.send(embed=discord.Embed(description="Cannot blacklist owner.", color=C["err"]))
    if member.guild_permissions.administrator and ctx.author != ctx.guild.owner:
        return await ctx.send(embed=discord.Embed(description="Cannot blacklist admin.", color=C["err"]))
    bl_add(ctx.guild.id, member.id, reason, ctx.author.id)
    try:
        await member.ban(reason="Blacklisted: " + reason)
    except Exception:
        pass
    e = discord.Embed(title="Blacklisted", color=C["err"])
    e.add_field(name="User", value=member.mention + "\n`" + str(member.id) + "`", inline=True)
    e.add_field(name="Reason", value=reason, inline=True)
    await ctx.send(embed=e)

@bot.command(name="unblacklist")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def unblacklist(ctx, user_id: str = None):
    owner_rid = get_role_id(ctx.guild.id, "owner_role")
    if not (has_perm(ctx.author, "administrator") or member_has_role(ctx.author, owner_rid)):
        return
    if not user_id or not user_id.isdigit():
        return await ctx.send(embed=discord.Embed(description="Usage: `$unblacklist <user_id>`", color=C["err"]))
    bl_remove(ctx.guild.id, int(user_id))
    await ctx.send(embed=discord.Embed(description="Removed `" + user_id + "` from blacklist.", color=C["ok"]))

@bot.command(name="blacklisted")
async def blacklisted_cmd(ctx):
    mm_rid = get_role_id(ctx.guild.id, "mm_role")
    owner_rid = get_role_id(ctx.guild.id, "owner_role")
    if not (has_perm(ctx.author, "administrator") or member_has_role(ctx.author, mm_rid) or member_has_role(ctx.author, owner_rid)):
        return
    rows = bl_all(ctx.guild.id)
    if not rows:
        return await ctx.send(embed=discord.Embed(description="Blacklist is empty.", color=C["ok"]))
    lines = ["<@" + str(r["user_id"]) + "> — " + r["reason"] for r in rows]
    await ctx.send(embed=discord.Embed(title="Blacklist", description="\n".join(lines), color=C["err"]))

@bot.command(name="support")
@cooldown(user_seconds=5, global_count=8, global_seconds=60)
async def support_panel(ctx):
    if not has_perm(ctx.author, "administrator"):
        return
    embed = discord.Embed(
        color=C["ok"],
        description=(
            "# 🛟 Support Centre\n"
            "-# " + SERVER_NAME + "\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "## Need help?\n\n"
            "Open a ticket. Staff will get to you.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "### What we handle\n\n"
            "> • Scam reports\n"
            "> • Trade disputes\n"
            "> • Staff applications\n"
            "> • General questions\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "### For scam reports\n\n"
            "**1.** Clear evidence\n"
            "**2.** Within the MM policy window\n"
            "**3.** In-server official MM trades only\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "> ⚠️ **Fake or troll tickets get you muted.**\n\n"
            "-# Press the button below to open a ticket."
        ))
    if SERVER_ICON:
        embed.set_thumbnail(url=SERVER_ICON)
    img = get_image_url(SUPPORT_IMAGE)
    if img:
        embed.set_image(url=img)
    embed.set_footer(text=SERVER_NAME)
    await ctx.send(embed=embed, view=SupportPanelView())

@bot.command(name="panel")
@cooldown(user_seconds=5, global_count=8, global_seconds=60)
async def mm_panel(ctx):
    if not has_perm(ctx.author, "administrator"):
        return
    embed = discord.Embed(
        color=C["ok"],
        description=(
            "# 🛡️ Middleman Service\n"
            "-# " + SERVER_NAME + "\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "## Trade without getting scammed.\n\n"
            "We hold the items. Neither side can walk off with anything.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "### Before you open a ticket\n\n"
            "> **1.** Both traders agreed on the trade\n"
            "> **2.** You know what's being traded and its value\n"
            "> **3.** Not a troll ticket\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "### How it works\n\n"
            "**01** · You open a ticket\n"
            "**02** · MM joins and holds the items\n"
            "**03** · Both sides finish the trade\n"
            "**04** · MM releases to the right person\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "> ⚠️ **Fake tickets get you banned.**\n"
            "> **Never trade with \"staff\" outside a ticket.**\n\n"
            "-# Press the button below to start."
        ))
    if SERVER_ICON:
        embed.set_thumbnail(url=SERVER_ICON)
    img = get_image_url(PANEL_IMAGE)
    if img:
        embed.set_image(url=img)
    await ctx.send(embed=embed, view=MMPanelView())

@bot.command(name="automm")
@cooldown(user_seconds=5, global_count=8, global_seconds=60)
async def automm_panel_cmd(ctx):
    if not has_perm(ctx.author, "administrator"):
        return
    if not am_available():
        return await ctx.send(embed=discord.Embed(description="No crypto addresses configured.", color=C["err"]))
    await ctx.send(view=AutoMMPanelView())

@bot.command(name="conf")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def conf_cmd(ctx, channel: discord.TextChannel = None):
    # MM ticket confirmation flow.
    if ctx.guild and is_ticket_channel(ctx.channel) and ctx.channel.name.startswith(("mm-", "claimed-mm-")) and channel is None:
        mm_rid = get_role_id(ctx.guild.id, "mm_role")
        if not (is_bot_owner(ctx.author) or has_perm(ctx.author, "administrator") or (mm_rid and member_has_role(ctx.author, mm_rid))):
            return await ctx.send(embed=discord.Embed(description="Only an MM can use `$conf`.", color=C["err"]))
        row = get_mm_ticket_details(ctx.channel.id)
        if not row:
            return await ctx.send(embed=discord.Embed(description="Trade details were not found for this ticket.", color=C["err"]))
        if not row["trader_id"]:
            return await ctx.send(embed=discord.Embed(description="Add the other trader with `$adduser @user` before using `$conf`.", color=C["err"]))
        if row["declined_by"]:
            return await ctx.send(embed=discord.Embed(description="This trade has already been declined.", color=C["err"]))
        if row["confirmed_one"] or row["confirmed_two"]:
            return await ctx.send(embed=discord.Embed(description="A confirmation is already active in this ticket.", color=C["warn"]))
        opener = ctx.guild.get_member(int(row["opener_id"]))
        trader = ctx.guild.get_member(int(row["trader_id"]))
        opener_name = opener.mention if opener else "<@" + str(row["opener_id"]) + ">"
        trader_name = trader.mention if trader else (row["trader_text"] or "Other trader")
        embed = discord.Embed(title="✦ Trade Confirmation", color=C["info"])
        embed.description = "Confirm that the trade below is exactly correct."
        embed.add_field(
            name="TRADE DETAILS",
            value=(
                "**" + opener_name + " is giving**\n`" + str(row["giving_one"] or "—") + "`\n\n"
                "**" + trader_name + " is giving**\n`" + str(row["giving_two"] or "—") + "`"
            ),
            inline=False
        )
        embed.add_field(name="STATUS", value="🟡 0 / 2 confirmed", inline=False)
        embed.set_footer(text="Both traders must confirm before the trade is considered confirmed.")
        msg = await ctx.send(embed=embed, view=MMTradeConfirmationView())
        set_mm_confirmation_message(ctx.channel.id, msg.id)
        return

    # Existing Auto MM confirmation flow.
    if not ctx.guild:
        return
    staff_id = am_staff_channel_id(ctx.guild.id)
    if not staff_id or ctx.channel.id != staff_id or not is_mercy_or_admin(ctx.author):
        return
    if channel is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$conf #auto-mm-ticket`", color=C["err"]))
    t = am_get(channel.id)
    if not t:
        return await ctx.send(embed=discord.Embed(description=channel.mention + " is not an Auto MM ticket.", color=C["err"]))
    if t["status"] in ("trade", "release_confirmation", "address_prompt", "address_confirmation", "settlement_pending", "completed"):
        return await ctx.send(embed=discord.Embed(description=channel.mention + " already confirmed.", color=C["warn"]))
    if t["status"] not in ("waiting_payment", "deposit_detected", "deposit_confirmed"):
        return await ctx.send(embed=discord.Embed(description=channel.mention + " not awaiting payment.", color=C["err"]))
    sim = _am_sim_tasks.pop(channel.id, None)
    if sim and not sim.done():
        sim.cancel()
    am_set(channel.id, status="trade", confirmed_by=ctx.author.id)
    t = am_get(channel.id)
    try:
        await channel.send(
            content="<@" + str(t["sender_id"]) + "> <@" + str(t["receiver_id"]) + ">",
            embed=am_proceed_embed(t),
            view=AutoMMProceedView(),
            allowed_mentions=discord.AllowedMentions(users=True)
        )
    except discord.Forbidden:
        pass
    await ctx.send(embed=discord.Embed(description="Payment confirmed on " + channel.mention + ".", color=C["ok"]))

@bot.command(name="settle")
@cooldown(user_seconds=8, global_count=8, global_seconds=60)
async def settle_cmd(ctx, channel: discord.TextChannel = None, *, txid: str = None):
    owner_rid = get_role_id(ctx.guild.id, "owner_role")
    if not (has_perm(ctx.author, "administrator") or member_has_role(ctx.author, owner_rid)):
        return
    if channel is None or not txid:
        return await ctx.send(embed=discord.Embed(description="Usage: `$settle #ticket <payout_txid>`", color=C["err"]))
    t = am_get(channel.id)
    if not t:
        return await ctx.send(embed=discord.Embed(description=channel.mention + " is not an Auto MM ticket.", color=C["err"]))
    if t["status"] != "settlement_pending":
        return await ctx.send(embed=discord.Embed(description=channel.mention + " not awaiting settlement.", color=C["err"]))
    txid = txid.strip()
    asset = t["asset"]
    if asset in ("usdt", "eth") and not re.fullmatch(r"0x[a-fA-F0-9]{64}", txid):
        return await ctx.send(embed=discord.Embed(description="Invalid txid.", color=C["err"]))
    if asset == "sol" and not re.fullmatch(r"[1-9A-HJ-NP-Za-km-z]{43,88}", txid):
        return await ctx.send(embed=discord.Embed(description="Invalid signature.", color=C["err"]))
    if asset in ("btc", "ltc") and not re.fullmatch(r"[a-fA-F0-9]{64}", txid):
        return await ctx.send(embed=discord.Embed(description="Invalid txid.", color=C["err"]))
    completed_at = datetime.now(timezone.utc).isoformat()
    am_set(channel.id, payout_txid=txid, status="completed", completed_at=completed_at)
    t = am_get(channel.id)
    sb_upsert("trades", {
        "guild_id": ctx.guild.id,
        "channel_id": channel.id,
        "opener_id": t.get("opener_id"),
        "trader_id": t.get("trader_id"),
        "sender_id": t.get("sender_id"),
        "receiver_id": t.get("receiver_id"),
        "asset": t.get("asset"),
        "usd_amount": t.get("usd_amount"),
        "crypto_amount": t.get("crypto_amount"),
        "deposit_address": t.get("deposit_address"),
        "receiver_address": t.get("receiver_address"),
        "payout_txid": t.get("payout_txid"),
        "status": t.get("status"),
        "created_at": t.get("created_at"),
        "completed_at": t.get("completed_at"),
    })
    try:
        await channel.send(content="<@" + str(t["receiver_id"]) + ">", embed=am_withdrawal_success_embed(t), view=AutoMMCloseView(), allowed_mentions=discord.AllowedMentions(users=True))
    except Exception:
        pass
    if AUTOMM_COMPLETED_CHANNEL and AUTOMM_COMPLETED_CHANNEL.isdigit():
        comp = ctx.guild.get_channel(int(AUTOMM_COMPLETED_CHANNEL))
        if comp:
            try:
                await comp.send(embed=am_completed_embed(t))
            except Exception:
                pass
    await ctx.send(embed=discord.Embed(description="Settled " + channel.mention + ".", color=C["ok"]))

@bot.command(name="mminfo")
async def mminfo(ctx):
    if not await check_mm_or_admin(ctx):
        return
    embed = discord.Embed(title="Middleman Info", description=(
        "A Middleman (MM) is a trusted staff member who holds items during a trade so neither side can scam.\n\n"
        "**How it works**\n"
        "**1** · Seller gives items to the MM\n"
        "**2** · Buyer pays the seller\n"
        "**3** · MM delivers to the buyer\n\n"
        "**Rules**\n"
        "• Once a ticket is created, the MM who claims it must finish it\n"
        "• Both traders must vouch after the trade"), color=C["neutral"])
    if SERVER_ICON:
        embed.set_thumbnail(url=SERVER_ICON)
    img = get_image_url(MMINFO_IMAGE)
    if img:
        embed.set_image(url=img)
    embed.set_footer(text=SERVER_NAME + " | Middleman Service")
    await ctx.send(embed=embed, view=InfoAckView())

@bot.command(name="mmfee")
async def mmfee(ctx):
    if not await check_mm_or_admin(ctx):
        return
    embed = discord.Embed(title="MM Fee", description=(
        "Optional. Only pay if you and the MM agreed.\n\n"
        "**Standard** · 10% of trade value, on top\n\n"
        "**Accepted**\n"
        "• LTC (preferred)\n"
        "• Cash App · PayPal F&F\n"
        "• Robux / in-game\n\n"
        "> ⚠️ **Never pay an \"MM\" outside a ticket.**"), color=C["neutral"])
    if SERVER_ICON:
        embed.set_thumbnail(url=SERVER_ICON)
    img = get_image_url(MMFEE_IMAGE)
    if img:
        embed.set_image(url=img)
    embed.set_footer(text=SERVER_NAME + " | Middleman Service")
    await ctx.send(embed=embed, view=InfoAckView())

@bot.command(name="ctmm")
async def ctmm(ctx):
    if not await check_mm_or_admin(ctx):
        return
    embed = discord.Embed(title="Cross-Trade Guide", description=(
        "**1 · Setup**\nMM uses one official account.\n\n"
        "**2 · Collect**\nMM collects items from both traders.\n\n"
        "**3 · Deliver**\nMM delivers in each game.\n\n"
        "Both parties confirm before it starts."), color=C["neutral"])
    if SERVER_ICON:
        embed.set_thumbnail(url=SERVER_ICON)
    img = get_image_url(CTMM_IMAGE)
    if img:
        embed.set_image(url=img)
    embed.set_footer(text=SERVER_NAME + " | Crosstrading & Middleman")
    await ctx.send(embed=embed, view=InfoAckView())

@bot.command(name="mmpolicy")
async def mmpolicy(ctx):
    if not await check_mm_or_admin(ctx):
        return
    embed = discord.Embed(title="MM Policy", description=(
        "**If an MM scams**\n"
        "Both traders get compensated in full.\n"
        "The MM is fired and blacklisted.\n\n"
        "**To claim**\n"
        "• Trade happened in this server\n"
        "• You have proof\n\n"
        "-# No proof, no compensation."), color=C["neutral"])
    if SERVER_ICON:
        embed.set_thumbnail(url=SERVER_ICON)
    img = get_image_url(MMPOLICY_IMAGE)
    if img:
        embed.set_image(url=img)
    embed.set_footer(text=SERVER_NAME + " | Crosstrading & Middleman")
    await ctx.send(embed=embed, view=InfoAckView())

@bot.command(name="setguidech")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def setguidech(ctx, *, raw: str = None):
    owner_rid = get_role_id(ctx.guild.id, "owner_role")
    if not (has_perm(ctx.author, "administrator") or member_has_role(ctx.author, owner_rid)):
        return
    ch = await resolve_channel(ctx, raw)
    if ch is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$setguidech #channel`", color=C["err"]))
    set_role_id(ctx.guild.id, "guide_channel", ch.id)
    await ctx.send(embed=discord.Embed(description="Guide channel set to " + ch.mention + ".", color=C["ok"]))

@bot.command(name="guide")
async def guide(ctx):
    gid = get_role_id(ctx.guild.id, "guide_channel") if ctx.guild else None
    if gid:
        e = discord.Embed(title="Hitting Guide", description="Full guide: <#" + str(gid) + ">", color=C["neutral"])
    else:
        e = discord.Embed(title="Hitting Guide", description="No guide channel set.", color=C["err"])
    await ctx.send(embed=e, view=InfoAckView())

@bot.command(name="showmmrole")
async def showmmrole(ctx):
    mm_rid = get_role_id(ctx.guild.id, "mm_role")
    owner_rid = get_role_id(ctx.guild.id, "owner_role")
    if not (has_perm(ctx.author, "administrator") or member_has_role(ctx.author, mm_rid) or member_has_role(ctx.author, owner_rid)):
        return
    if not mm_rid:
        return await ctx.send("No Middleman role is set.")
    role = ctx.guild.get_role(mm_rid)
    if not role:
        return await ctx.send("Role ID `" + str(mm_rid) + "` no longer exists.")
    has = role in ctx.author.roles
    await ctx.send("**Stored MM role:** " + role.mention + " (`" + str(role.id) + "`)\n**You have it:** " + ("Yes" if has else "No"))

async def _send_info_embed(ctx, title, body, img_key, footer):
    embed = discord.Embed(title=title, description=body, color=C["neutral"])
    if SERVER_ICON:
        embed.set_thumbnail(url=SERVER_ICON)
    img = get_image_url(img_key)
    if img:
        embed.set_image(url=img)
    embed.set_footer(text=footer)
    await ctx.send(embed=embed, view=InfoAckView())

@bot.command(name="serverrules")
async def serverrules(ctx):
    if not has_perm(ctx.author, "administrator"):
        return
    await _send_info_embed(ctx, SERVER_NAME + " | Server Rules",
        "**01** · Respect everyone\nNo harassment, slurs, threats, or discrimination.\n\n"
        "**02** · No scamming\nFraud, fake proofs, phishing — permanent ban.\n\n"
        "**03** · No impersonating staff or MMs\nVerify before you trust.\n\n"
        "**04** · No spam\nMessages, mentions, ads, commands.\n\n"
        "**05** · No advertising\nAsk staff first.\n\n"
        "**06** · Use channels correctly\nThe name says what it's for.\n\n"
        "**07** · No NSFW\nAny of it.\n\n"
        "**08** · Protect your account\n2FA on. Never share passwords or codes.\n\n"
        "**09** · Follow MM procedure\nVerified MMs only. Always.\n\n"
        "**10** · Listen to staff\nIf they say stop, stop.\n\n"
        "**11** · Follow Roblox + Discord TOS\n\n"
        "**12** · Enforcement\nWarning → mute → kick → ban → blacklist.",
        RULES_IMAGE, SERVER_NAME + " | Server Rules")

@bot.command(name="guidelines")
async def guidelines(ctx):
    if not has_perm(ctx.author, "administrator"):
        return
    await _send_info_embed(ctx, SERVER_NAME + " Values | Trading Guidelines",
        "**Be honest.**\nDescribe what you're actually trading.\n\n"
        "**Use an MM.**\nAny trade worth doing is worth an MM.\n\n"
        "**Agree first.**\nTerms locked before either side commits.\n\n"
        "**Keep records.**\nScreenshots, receipts, timestamps.\n\n"
        "**Slow down.**\nAnyone rushing you is a red flag.\n\n"
        "**Check before you trust.**\nVouches, history, verification. Every time.",
        GUIDELINES_IMAGE, SERVER_NAME + " | Trading Guidelines")

@bot.command(name="mprules")
async def mprules(ctx):
    if not has_perm(ctx.author, "administrator"):
        return
    await _send_info_embed(ctx, SERVER_NAME + " Values | Marketplace Rules",
        "**Verified MMs only.**\nEspecially for high-value trades and trades with strangers.\n\n"
        "**Keep it in-server.**\nNot in DMs. Not in other servers.\n\n"
        "**If it's too good, it's a scam.**\n\n"
        "**Real traders don't rush you.**\nIf they do, walk.\n\n"
        "**Common scams**\n• Fake payment screenshots\n• Impersonating an MM\n• Phishing links\n\n"
        "**Protect your account.**\n2FA. Private password.\n\n"
        "-# Account trades are risky. Use an MM or skip them.",
        MPRULES_IMAGE, SERVER_NAME + " | Marketplace Rules")

@bot.command(name="mmtos")
async def mmtos(ctx):
    if not has_perm(ctx.author, "administrator"):
        return
    await _send_info_embed(ctx, SERVER_NAME + " Values | Middleman Service",
        "**Follow the MM.**\nThey run the trade, not you.\n\n"
        "**Keep it in-server.**\nNo MM trades outside this Discord.\n\n"
        "**Verified MMs only.**\n\n"
        "**Confirm before proceeding.**\nBoth sides.\n\n"
        "**Be honest.**\nWrong info on your end means wrong outcome.\n\n"
        "**No scams. No chargebacks.**\nInstant blacklist.\n\n"
        "**Cooperate.**\n\n"
        "**Vouch after.**\n\n"
        "**Stay calm.**\nNo pressure, threats, or harassment.\n\n"
        "-# Staff decisions are final.",
        MMTOS_IMAGE, SERVER_NAME + " | Middleman Terms of Service")

@bot.command(name="suptos")
async def suptos(ctx):
    if not has_perm(ctx.author, "administrator"):
        return
    await _send_info_embed(ctx, SERVER_NAME + " Values | Support",
        "**Support handles**\n• Staff applications\n• Scam reports (in-server, official MM only)\n• Compensation (with proof)\n• General questions\n\n"
        "**For scam reports**\n**1** · Clear evidence required\n**2** · Submit within the MM policy window\n**3** · False reports = blacklist\n\n"
        "> One ticket per issue.\n> Don't pressure support staff.\n> All decisions are final.",
        SUPTOS_IMAGE, SERVER_NAME + " | Support Terms of Service")

@bot.command(name="setstaffchat")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def setstaffchat(ctx, channel: discord.TextChannel = None):
    if not has_perm(ctx.author, "administrator"):
        return
    if channel is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$setstaffchat #channel`", color=C["err"]))
    set_role_id(ctx.guild.id, "staff_chat", channel.id)
    await ctx.send(embed=discord.Embed(description="Staff chat set to " + channel.mention + ".", color=C["ok"]))

@bot.command(name="setverifych")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def setverifych(ctx, channel: discord.TextChannel = None):
    if not has_perm(ctx.author, "administrator"):
        return
    if channel is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$setverifych #channel`", color=C["err"]))
    set_role_id(ctx.guild.id, "verify_channel", channel.id)
    await ctx.send(embed=discord.Embed(description="Verify channel set to " + channel.mention + ".", color=C["ok"]))

@bot.command(name="autovouch")
@cooldown(user_seconds=15, global_count=5, global_seconds=300)
async def autovouch_start(ctx):
    if not has_perm(ctx.author, "administrator"):
        return
    av_set(ctx.guild.id, active=1)
    await ctx.send(embed=discord.Embed(description="Auto-vouch enabled.", color=C["ok"]))

@bot.command(name="autovouchstop")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def autovouch_stop(ctx):
    if not has_perm(ctx.author, "administrator"):
        return
    av_set(ctx.guild.id, active=0)
    await ctx.send(embed=discord.Embed(description="Auto-vouch disabled.", color=C["err"]))

@bot.command(name="autovouchchannel")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def autovouchchannel(ctx, channel: discord.TextChannel = None):
    if not has_perm(ctx.author, "administrator"):
        return
    if channel is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `autovouchchannel #channel`", color=C["err"]))
    av_set(ctx.guild.id, log_channel_id=channel.id)
    await ctx.send(embed=discord.Embed(description="Log channel set to " + channel.mention + ".", color=C["ok"]))

@bot.command(name="setautovouchchannel")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def setautovouchchannel(ctx, channel: discord.TextChannel = None):
    if not has_perm(ctx.author, "administrator"):
        return
    if channel is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `setautovouchchannel #channel`", color=C["err"]))
    av_set(ctx.guild.id, vouch_channel_id=channel.id)
    await ctx.send(embed=discord.Embed(description="Vouch channel set to " + channel.mention + ".", color=C["ok"]))

@bot.command(name="settraderrole")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def settraderrole(ctx, role: discord.Role = None):
    if not has_perm(ctx.author, "administrator"):
        return
    if role is None:
        av_set(ctx.guild.id, trader_role_id=None)
        return await ctx.send(embed=discord.Embed(description="Trader role cleared.", color=C["warn"]))
    av_set(ctx.guild.id, trader_role_id=role.id)
    await ctx.send(embed=discord.Embed(description="Traders picked from " + role.mention + ".", color=C["ok"]))

@bot.command(name="autovouchcolor")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def autovouchcolor(ctx, hex_: str = None):
    if not has_perm(ctx.author, "administrator"):
        return
    if hex_ is None:
        s = av_get(ctx.guild.id)
        return await ctx.send(embed=discord.Embed(description="Current color: " + (s["embed_color"] if s else "#57F287"), color=C["neutral"]))
    if not re.match(r"^#[0-9a-fA-F]{6}$", hex_):
        return await ctx.send(embed=discord.Embed(description="Invalid hex.", color=C["err"]))
    av_set(ctx.guild.id, embed_color=hex_)
    await ctx.send(embed=discord.Embed(description="Color set to " + hex_ + ".", color=C["ok"]))

@bot.command(name="addss")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def addss(ctx, url: str = None):
    if not has_perm(ctx.author, "administrator"):
        return
    if not url or not url.startswith(("http://", "https://")):
        return await ctx.send(embed=discord.Embed(description="Usage: `addss <image_url>`", color=C["err"]))
    before = len(av_screenshots(ctx.guild.id))
    av_add_screenshot(ctx.guild.id, url)
    after = len(av_screenshots(ctx.guild.id))
    if after == before:
        return await ctx.send(embed=discord.Embed(description="Already stored.", color=C["warn"]))
    await ctx.send(embed=discord.Embed(description="Added. Total: " + str(after) + ".", color=C["ok"]))

@bot.command(name="removss")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def removss(ctx, index: int = None):
    if not has_perm(ctx.author, "administrator"):
        return
    shots = av_screenshots(ctx.guild.id)
    if not shots:
        return await ctx.send(embed=discord.Embed(description="None stored.", color=C["err"]))
    if index is None or index < 1 or index > len(shots):
        return await ctx.send(embed=discord.Embed(description="Invalid index.", color=C["err"]))
    av_remove_screenshot(ctx.guild.id, shots[index - 1])
    await ctx.send(embed=discord.Embed(description="Removed #" + str(index) + ".", color=C["ok"]))

@bot.command(name="listss")
async def listss(ctx):
    if not has_perm(ctx.author, "administrator"):
        return
    shots = av_screenshots(ctx.guild.id)
    if not shots:
        return await ctx.send(embed=discord.Embed(description="None stored.", color=C["err"]))
    lines = ["`#" + str(i + 1) + "` " + u for i, u in enumerate(shots)]
    await ctx.send(embed=discord.Embed(title="Screenshots", description="\n".join(lines), color=C["neutral"]))

@bot.command(name="autovouchforce")
@cooldown(user_seconds=20, global_count=4, global_seconds=300)
async def autovouchforce(ctx):
    if not has_perm(ctx.author, "administrator"):
        return
    last = _autovouch_cooldown.get(ctx.guild.id, 0)
    if time.time() - last < 30:
        return await ctx.send(embed=discord.Embed(description="Wait 30s.", color=C["err"]))
    _autovouch_cooldown[ctx.guild.id] = time.time()
    s = av_get(ctx.guild.id)
    if not s or not s["active"]:
        return await ctx.send(embed=discord.Embed(description="Auto-vouch disabled.", color=C["err"]))
    vch = ctx.guild.get_channel(s["vouch_channel"]) if s["vouch_channel"] else discord.utils.get(ctx.guild.text_channels, name="vouches")
    if vch is None:
        return await ctx.send(embed=discord.Embed(description="No vouch channel.", color=C["err"]))
    pool = []
    if s["trader_role"]:
        r = ctx.guild.get_role(s["trader_role"])
        if r:
            pool = [m for m in r.members if not m.bot]
    if not pool:
        pool = [m for m in ctx.guild.members if not m.bot]
    if len(pool) < 2:
        return await ctx.send(embed=discord.Embed(description="Not enough traders.", color=C["err"]))
    mm_rid = get_role_id(ctx.guild.id, "mm_role")
    mm_role = ctx.guild.get_role(mm_rid) if mm_rid else None
    if not mm_role:
        return await ctx.send(embed=discord.Embed(description="No MM role.", color=C["err"]))
    mm_pool = [m for m in mm_role.members if not m.bot]
    if not mm_pool:
        return await ctx.send(embed=discord.Embed(description="No MMs.", color=C["err"]))
    cands = [m for m in pool if m.id != ctx.guild.me.id]
    t1 = random.choice(cands)
    c2 = [m for m in cands if m.id != t1.id]
    if not c2:
        return await ctx.send(embed=discord.Embed(description="Not enough traders.", color=C["err"]))
    t2 = random.choice(c2)
    mm = random.choice(mm_pool)
    db_add("vouches", ctx.guild.id, mm.id)
    other = random.choice(PAYMENT_METHODS)
    flip = random.choice([True, False])
    left, right = ("In-Game Items", other) if flip else (other, "In-Game Items")
    r1, r2 = random.randint(2, 5), random.randint(2, 5)
    v1 = "+rep " + mm.mention
    v2 = "+rep " + mm.mention
    tid = random.randint(100000, 999999)
    color = int(s["embed_color"].lstrip("#"), 16)
    shot = None
    if random.random() < 0.90:
        shot = _pick_unused_screenshot(ctx.guild.id)
    embed = build_vouch_embed(guild=ctx.guild, middleman=mm, t1=t1, t2=t2, left=left, right=right, r1=r1, v1=v1, r2=r2, v2=v2, tid=tid, color=color, screenshot=shot)
    try:
        await vch.send(embed=embed)
        await ctx.send(embed=discord.Embed(description="Force vouch sent.", color=C["ok"]))
    except Exception as e:
        await ctx.send(embed=discord.Embed(description="Failed: " + str(e), color=C["err"]))

@bot.command(name="close")
@cooldown(user_seconds=5, global_count=8, global_seconds=60)
async def close(ctx):
    if not (is_ticket_channel(ctx.channel) or is_automm_channel(ctx.channel)):
        return await ctx.send(embed=discord.Embed(description="Only inside a ticket.", color=C["err"]))

    claimer_id = get_claimer(ctx.channel.id)
    is_admin = has_perm(ctx.author, "administrator") or is_ticket_admin(ctx.author)
    owner_rid = get_role_id(ctx.guild.id, "owner_role")
    is_owner = bool(owner_rid and member_has_role(ctx.author, owner_rid))

    if not (is_admin or is_owner):
        mm_rid = get_role_id(ctx.guild.id, "mm_role")
        mm_has_access = False
        if mm_rid and member_has_role(ctx.author, mm_rid):
            try:
                mm_has_access = bool(ctx.channel.permissions_for(ctx.author).view_channel)
            except Exception:
                mm_has_access = False

        if mm_has_access:
            return await ctx.send(
                embed=discord.Embed(
                    description="Close this ticket?\nDeletes in 5 seconds.",
                    color=C["warn"]),
                view=CloseConfirmView(ctx.author.id))

        if claimer_id is not None and ctx.author.id == claimer_id:
            return await ctx.send(
                embed=discord.Embed(
                    description="Close this ticket?\nDeletes in 5 seconds.",
                    color=C["warn"]),
                view=CloseConfirmView(ctx.author.id))

        if claimer_id is not None:
            return await ctx.send(
                embed=discord.Embed(description="You do not have access to close this ticket.", color=C["err"]),
                delete_after=5)

        sup_rid = get_role_id(ctx.guild.id, "support_role")
        is_support_ticket = ctx.channel.name.startswith(("ticket-", "claimed-ticket-"))
        if not (is_support_ticket and sup_rid and member_has_role(ctx.author, sup_rid)):
            return await ctx.send(
                embed=discord.Embed(description="You cannot close this ticket.", color=C["err"]),
                delete_after=5)

    await close_ticket(ctx.channel, ctx.author, ctx.guild)

@bot.command(name="hold")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def hold(ctx):
    if not is_ticket_channel(ctx.channel):
        return await ctx.send(embed=discord.Embed(description="Only inside a ticket.", color=C["err"]))
    if not is_staff(ctx.author):
        return await ctx.send(embed=discord.Embed(description="Only staff can put a ticket on hold.", color=C["err"]), delete_after=5)

    prefix, base = _ticket_name_parts(ctx.channel.name)
    if prefix is None:
        return await ctx.send(embed=discord.Embed(description="This channel is not a supported ticket name.", color=C["err"]))

    held = ticket_is_on_hold(ctx.channel.id)
    if held:
        if base.startswith("hold-"):
            base = base[5:]
        _exec("UPDATE ticket_log SET hold=0, last_activity=? WHERE channel_id=?", (time.time(), ctx.channel.id))
        new_name = prefix + (base or "ticket")
        status = "Ticket hold removed. Auto-close is active again after 1 hour of inactivity."
        color = C["ok"]
    else:
        if not base.startswith("hold-"):
            base = "hold-" + base
        _exec("UPDATE ticket_log SET hold=1, last_activity=? WHERE channel_id=?", (time.time(), ctx.channel.id))
        new_name = prefix + base
        status = "Ticket placed on hold. Auto-close is disabled until `$hold` is used again."
        color = C["warn"]

    try:
        await ctx.channel.edit(name=new_name, reason="$hold")
    except discord.Forbidden:
        _exec("UPDATE ticket_log SET hold=?, last_activity=? WHERE channel_id=?", (0 if held else 1, time.time(), ctx.channel.id))
        return await ctx.send(embed=discord.Embed(description="I couldn't rename the ticket channel. I need `Manage Channels`.", color=C["err"]))
    except Exception as e:
        _exec("UPDATE ticket_log SET hold=?, last_activity=? WHERE channel_id=?", (0 if held else 1, time.time(), ctx.channel.id))
        return await ctx.send(embed=discord.Embed(description="Failed to rename the ticket: " + str(e)[:120], color=C["err"]))

    await ctx.send(embed=discord.Embed(description=status + "\nChannel: `" + ctx.channel.name + "`", color=color))

@bot.command(name="rename")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def rename_ticket(ctx, *, new_name: str = None):
    if not is_ticket_channel(ctx.channel):
        return await ctx.send(embed=discord.Embed(description="Only inside a ticket.", color=C["err"]))
    if not is_staff(ctx.author):
        return await ctx.send(embed=discord.Embed(description="Only staff can rename tickets.", color=C["err"]), delete_after=5)
    if not new_name:
        return await ctx.send(embed=discord.Embed(description="Usage: `$rename <name>`", color=C["err"]))

    prefix, _base = _ticket_name_parts(ctx.channel.name)
    if prefix is None:
        return await ctx.send(embed=discord.Embed(description="This channel is not a supported ticket name.", color=C["err"]))

    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "-", new_name.strip()).strip("-").lower()
    if cleaned.startswith("hold-"):
        cleaned = cleaned[5:]
    if not cleaned:
        return await ctx.send(embed=discord.Embed(description="Enter a valid channel name.", color=C["err"]))
    cleaned = cleaned[:85].strip("-") or "ticket"
    if ticket_is_on_hold(ctx.channel.id):
        cleaned = "hold-" + cleaned

    new_channel_name = prefix + cleaned
    old_name = ctx.channel.name
    try:
        await ctx.channel.edit(name=new_channel_name, reason="$rename")
    except discord.Forbidden:
        return await ctx.send(embed=discord.Embed(description="I need `Manage Channels` to rename tickets.", color=C["err"]))
    except Exception as e:
        return await ctx.send(embed=discord.Embed(description="Failed to rename the ticket: " + str(e)[:120], color=C["err"]))
    await ctx.send(embed=discord.Embed(description="Ticket renamed from `" + old_name + "` to `" + new_channel_name + "`.", color=C["ok"]))

@bot.command(name="claim")
@cooldown(user_seconds=5, global_count=8, global_seconds=60)
async def claim(ctx):
    if not is_ticket_channel(ctx.channel) and not is_automm_channel(ctx.channel):
        return await ctx.send(embed=discord.Embed(description="Only inside a ticket.", color=C["err"]))
    if get_claimer(ctx.channel.id) is not None:
        return await ctx.send(embed=discord.Embed(description="This ticket has already been claimed.", color=C["err"]), delete_after=5)

    mm_rid = get_role_id(ctx.guild.id, "mm_role")
    sup_rid = get_role_id(ctx.guild.id, "support_role")
    is_mm = member_has_role(ctx.author, mm_rid)
    is_sup = member_has_role(ctx.author, sup_rid)
    is_adm = has_perm(ctx.author, "administrator") or is_ticket_admin(ctx.author)
    if not (is_adm or is_mm or is_sup):
        return await ctx.send(embed=discord.Embed(description="You do not have the required role.", color=C["err"]))

    await claim_ticket(ctx.channel, ctx.author, ctx.guild)


@bot.command(name="unclaim")
@cooldown(user_seconds=5, global_count=8, global_seconds=60)
async def unclaim(ctx):
    if not is_ticket_channel(ctx.channel) and not is_automm_channel(ctx.channel):
        return await ctx.send(embed=discord.Embed(description="Only inside a ticket.", color=C["err"]))
    if get_claimer(ctx.channel.id) is None:
        return await ctx.send(embed=discord.Embed(description="This ticket is not currently claimed.", color=C["warn"]))
    await unclaim_ticket(ctx.channel, ctx.author, ctx.guild)

@bot.command(name="transfer", aliases=["transfermm"])
@cooldown(user_seconds=5, global_count=8, global_seconds=60)
async def transfer_cmd(ctx, new_mm: discord.Member = None):
    if not is_ticket_channel(ctx.channel) and not is_automm_channel(ctx.channel):
        return await ctx.send(embed=discord.Embed(description="Only inside a ticket.", color=C["err"]))
    if new_mm is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$transfer @newmm`", color=C["err"]))
    if new_mm.bot:
        return await ctx.send(embed=discord.Embed(description="Cannot transfer to a bot.", color=C["err"]))
    await transfer_ticket(ctx.channel, ctx.author, new_mm, ctx.guild)

@bot.command(name="resolve")
@cooldown(user_seconds=5, global_count=8, global_seconds=60)
async def resolve_cmd(ctx):
    if not is_ticket_channel(ctx.channel):
        return await ctx.send(embed=discord.Embed(description="Only inside a ticket.", color=C["err"]))
    owner_rid = get_role_id(ctx.guild.id, "owner_role")
    if not (has_perm(ctx.author, "administrator") or is_ticket_admin(ctx.author) or member_has_role(ctx.author, owner_rid)):
        return
    row = _get_row("SELECT 1 FROM disputes WHERE channel_id=? AND resolved_at IS NULL", (ctx.channel.id,))
    if not row:
        return await ctx.send(embed=discord.Embed(description="No open dispute on this ticket.", color=C["warn"]))
    _exec("UPDATE disputes SET resolved_at=datetime('now'), resolved_by=? WHERE channel_id=?",
          (ctx.author.id, ctx.channel.id))
    await ctx.send(embed=discord.Embed(description="Dispute marked resolved by " + ctx.author.mention + ".", color=C["ok"]))
@bot.command(name="adduser")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def adduser(ctx, member: discord.Member = None):
    if not (is_ticket_channel(ctx.channel) or is_automm_channel(ctx.channel)):
        return await ctx.send(embed=discord.Embed(description="Only inside tickets.", color=C["err"]))
    if member is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$adduser @user`", color=C["err"]))
    if not is_staff(ctx.author):
        return await ctx.send(embed=discord.Embed(description="Only staff.", color=C["err"]))

    confirmation = discord.Embed(description=member.mention + " added.", color=C["ok"])
    await asyncio.gather(
        ctx.channel.set_permissions(member, read_messages=True, send_messages=True),
        ctx.send(embed=confirmation),
    )

    if ctx.channel.name.startswith(("mm-", "claimed-mm-")):
        row = get_mm_ticket_details(ctx.channel.id)
        if row:
            _exec(
                "UPDATE mm_ticket_details SET trader_id=?, trader_text=? WHERE channel_id=?",
                (member.id, member.mention, ctx.channel.id),
            )

@bot.command(name="remove", aliases=["removeuser"])
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def remove_cmd(ctx, member: discord.Member = None):
    if not (is_ticket_channel(ctx.channel) or is_automm_channel(ctx.channel)):
        return await ctx.send(embed=discord.Embed(description="Only inside tickets.", color=C["err"]))
    if member is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$remove @user`", color=C["err"]))
    if not is_staff(ctx.author):
        return await ctx.send(embed=discord.Embed(description="Only staff.", color=C["err"]))
    await ctx.channel.set_permissions(member, overwrite=None)
    await ctx.send(embed=discord.Embed(description=member.mention + " removed.", color=C["ok"]))

@bot.command(name="steal")
@cooldown(user_seconds=10, global_count=5, global_seconds=60)
async def steal(ctx, emoji: str = None):
    if emoji is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$steal <emoji|url>`", color=C["err"]))
    if not has_perm(ctx.author, "manage_emojis") or not ctx.guild.me.guild_permissions.manage_emojis:
        return await ctx.send(embed=discord.Embed(description="Need `manage_emojis`.", color=C["err"]))
    emoji = emoji.strip()
    url = None
    name = "stolen_emoji"
    m = re.fullmatch(r"<(a?):(\w+):(\d+)>", emoji)
    if m:
        name = m.group(2)
        eid = m.group(3)
        ext = "gif" if m.group(1) == "a" else "png"
        url = "https://cdn.discordapp.com/emojis/" + eid + "." + ext
    if url is None:
        m2 = re.search(r"cdn\.discordapp\.com/emojis/(\d+)\.(png|gif|webp|jpg)", emoji)
        if m2:
            url = "https://cdn.discordapp.com/emojis/" + m2.group(1) + "." + m2.group(2)
            name = "emoji_" + m2.group(1)
    if url is None and emoji.startswith(("http://", "https://")):
        url = emoji
        name = re.sub(r"[^a-zA-Z0-9_]", "_", emoji.split("/")[-1].split(".")[0])[:32] or "stolen_emoji"
    if url is None:
        return await ctx.send(embed=discord.Embed(description="Provide an emoji or URL.", color=C["err"]))
    try:
        async with bot.http._HTTPClient__session.get(url) as resp:
            if resp.status != 200:
                return await ctx.send(embed=discord.Embed(description="HTTP " + str(resp.status) + ".", color=C["err"]))
            cl = resp.headers.get("Content-Length")
            if cl and int(cl) > 512_000:
                return await ctx.send(embed=discord.Embed(description="Image too large (max 512 KB).", color=C["err"]))
            data = await resp.read()
        em = await ctx.guild.create_custom_emoji(name=name, image=data)
        await ctx.send(embed=discord.Embed(description=str(em) + " `:" + em.name + ":` added.", color=C["ok"]))
    except Exception as e:
        await ctx.send(embed=discord.Embed(description="Failed: " + str(e), color=C["err"]))

@bot.tree.command(name="role-ids", description="List member IDs of a role")
@app_commands.describe(rolle="Role to list members for")
async def role_ids(i: discord.Interaction, rolle: discord.Role):
    mm_rid = get_role_id(i.guild.id, "mm_role")
    owner_rid = get_role_id(i.guild.id, "owner_role")
    is_staff_member = has_perm(i.user, "administrator") or (mm_rid and member_has_role(i.user, mm_rid)) or (owner_rid and member_has_role(i.user, owner_rid))
    if not is_staff_member:
        return await i.response.send_message(embed=discord.Embed(description="Only staff.", color=C["err"]), ephemeral=True)
    await i.response.defer(ephemeral=True)
    await i.guild.chunk()
    members = rolle.members
    if not members:
        return await i.followup.send(embed=discord.Embed(description=rolle.name + " has no members.", color=C["err"]), ephemeral=True)
    ids = ", ".join(str(m.id) for m in members)
    if len(ids) > 1900:
        f = discord.File(fp=io.BytesIO(ids.encode()), filename="ids.txt")
        return await i.followup.send(embed=discord.Embed(description=str(len(members)) + " members.", color=C["neutral"]), file=f, ephemeral=True)
    await i.followup.send(embed=discord.Embed(title=rolle.name + " (" + str(len(members)) + ")", description="```\n" + ids + "\n```", color=C["neutral"]), ephemeral=True)

@bot.command(name="roleids")
@cooldown(user_seconds=3, global_count=15, global_seconds=60)
async def roleids(ctx, *, raw: str = None):
    mm_rid = get_role_id(ctx.guild.id, "mm_role")
    owner_rid = get_role_id(ctx.guild.id, "owner_role")
    if not (has_perm(ctx.author, "administrator") or member_has_role(ctx.author, mm_rid) or member_has_role(ctx.author, owner_rid)):
        return await ctx.send(embed=discord.Embed(description="Only staff.", color=C["err"]))
    if raw is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `roleids @role`", color=C["err"]))
    role = await resolve_role(ctx, raw)
    if role is None:
        return await ctx.send(embed=discord.Embed(description="Role not found.", color=C["err"]))
    await ctx.guild.chunk()
    members = role.members
    if not members:
        return await ctx.send(embed=discord.Embed(description=role.name + " has no members.", color=C["err"]))
    ids = ", ".join(str(m.id) for m in members)
    if len(ids) > 1900:
        await ctx.send(file=discord.File(fp=io.BytesIO(ids.encode()), filename="ids.txt"))
    else:
        await ctx.send(embed=discord.Embed(title=role.name + " (" + str(len(members)) + ")", description="```\n" + ids + "\n```", color=C["neutral"]))

async def _fetch_img(ctx, url):
    try:
        async with bot.http._HTTPClient__session.get(url) as r:
            if r.status != 200:
                await ctx.send(embed=discord.Embed(description="HTTP " + str(r.status) + ".", color=C["err"]))
                return None
            if not r.headers.get("Content-Type", "").startswith("image/"):
                await ctx.send(embed=discord.Embed(description="Not an image.", color=C["err"]))
                return None
            cl = r.headers.get("Content-Length")
            if cl and int(cl) > 8_000_000:
                await ctx.send(embed=discord.Embed(description="Image too large (max 8 MB).", color=C["err"]))
                return None
            return await r.read()
    except Exception as e:
        await ctx.send(embed=discord.Embed(description="Error: " + str(e), color=C["err"]))
        return None

@bot.command(name="serveravatar")
async def serveravatar(ctx, url: str = None):
    if not has_perm(ctx.author, "administrator"):
        return
    if not ctx.guild.me.guild_permissions.manage_guild:
        return await ctx.send(embed=discord.Embed(description="I need `Manage Server` to change the server avatar.", color=C["err"]))
    if not url:
        return await ctx.send(embed=discord.Embed(description="Usage: `$serveravatar <url>`", color=C["err"]))
    data = await _fetch_img(ctx, url)
    if not data:
        return
    try:
        await ctx.guild.edit(icon=data, reason="Server avatar updated by bot")
        e = discord.Embed(title="Avatar Updated", color=C["ok"])
        e.set_image(url=url)
        await ctx.send(embed=e)
    except discord.HTTPException as e:
        await ctx.send(embed=discord.Embed(description="Rejected: " + str(e), color=C["err"]))

@bot.command(name="serverbanner")
async def serverbanner(ctx, url: str = None):
    if not has_perm(ctx.author, "administrator"):
        return
    if not ctx.guild.me.guild_permissions.manage_guild:
        return await ctx.send(embed=discord.Embed(description="I need `Manage Server` to change the server banner.", color=C["err"]))
    if not url:
        return await ctx.send(embed=discord.Embed(description="Usage: `$serverbanner <url>`", color=C["err"]))
    data = await _fetch_img(ctx, url)
    if not data:
        return
    try:
        await ctx.guild.edit(banner=data, reason="Server banner updated by bot")
        e = discord.Embed(title="Banner Updated", color=C["ok"])
        e.set_image(url=url)
        await ctx.send(embed=e)
    except discord.HTTPException as e:
        await ctx.send(embed=discord.Embed(description="Rejected: " + str(e), color=C["err"]))

@bot.command(name="serverinfo")
async def serverinfo(ctx):
    g = ctx.guild
    if not g:
        return await ctx.send(embed=discord.Embed(description="Must be in a server.", color=C["err"]))
    owner = g.owner or await g.fetch_member(g.owner_id)
    e = discord.Embed(title=g.name, color=C["neutral"])
    if g.icon:
        e.set_thumbnail(url=g.icon.url)
    e.add_field(name="Owner", value=owner.mention + "\n`" + str(owner.id) + "`", inline=True)
    e.add_field(name="Server ID", value="`" + str(g.id) + "`", inline=True)
    e.add_field(name="Created", value=discord.utils.format_dt(g.created_at, style="F"), inline=False)
    e.add_field(name="Members", value=str(g.member_count), inline=True)
    e.add_field(name="Roles", value=str(len(g.roles) - 1), inline=True)
    e.add_field(name="Channels", value=str(len(g.channels)), inline=True)
    await ctx.send(embed=e)

@bot.command(name="roles")
async def roles_cmd(ctx):
    role_list = sorted([r for r in ctx.guild.roles if r != ctx.guild.default_role], key=lambda r: r.position, reverse=True)
    if not role_list:
        return await ctx.send(embed=discord.Embed(description="No roles.", color=C["err"]))
    lines = [r.mention + " — `" + str(r.id) + "`" for r in role_list]
    for i in range(0, len(lines), 20):
        chunk = lines[i:i + 20]
        e = discord.Embed(title="Roles (" + str(len(role_list)) + ")" if i == 0 else "Roles (cont.)", description="\n".join(chunk), color=C["neutral"])
        e.set_footer(text="Page " + str(i // 20 + 1) + "/" + str((len(lines) - 1) // 20 + 1))
        await ctx.send(embed=e)

@bot.command(name="roleinfo")
async def roleinfo(ctx, *, raw: str = None):
    if raw is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `roleinfo @role`", color=C["err"]))
    role = await resolve_role(ctx, raw)
    if role is None:
        return await ctx.send(embed=discord.Embed(description="Role not found.", color=C["err"]))
    granted = [n.replace("_", " ").title() for n, v in role.permissions if v]
    e = discord.Embed(title="Role — " + role.name, color=role.color if role.color.value else C["neutral"])
    e.add_field(name="ID", value="`" + str(role.id) + "`", inline=True)
    e.add_field(name="Members", value=str(len(role.members)), inline=True)
    e.add_field(name="Position", value=str(role.position), inline=True)
    e.add_field(name="Created", value=discord.utils.format_dt(role.created_at, style="F"), inline=False)
    if granted:
        half = (len(granted) + 1) // 2
        e.add_field(name="Permissions", value="\n".join("• " + p for p in granted[:half]) or "—", inline=True)
        if granted[half:]:
            e.add_field(name="\u200b", value="\n".join("• " + p for p in granted[half:]), inline=True)
    await ctx.send(embed=e)

@bot.command(name="level")
async def level_cmd(ctx, member: discord.Member = None):
    t = member or ctx.author
    xp, lvl = get_user_xp(ctx.guild.id, t.id)
    nx = xp_for_level(lvl + 1)
    filled = int((xp / nx) * 10) if nx else 10
    bar = "█" * filled + "░" * (10 - filled)
    e = discord.Embed(title="Level — " + t.display_name, color=C["neutral"])
    e.set_thumbnail(url=t.display_avatar.url)
    e.add_field(name="Level", value=str(lvl), inline=True)
    e.add_field(name="XP", value=str(xp) + " / " + str(nx), inline=True)
    e.add_field(name="Progress", value="`" + bar + "` " + str(filled * 10) + "%", inline=False)
    await ctx.send(embed=e)

@bot.command(name="leaderboard", aliases=["lb"])
async def leaderboard(ctx):
    rows = get_level_leaderboard(ctx.guild.id, 10)
    if not rows:
        return await ctx.send(embed=discord.Embed(description="No XP data yet.", color=C["err"]))
    lines = ["`" + str(i + 1) + ".` <@" + str(r["user_id"]) + "> — level " + str(r["level"]) + " · " + str(r["xp"]) + " XP" for i, r in enumerate(rows)]
    e = discord.Embed(title="XP Leaderboard", description="\n".join(lines), color=C["neutral"])
    await ctx.send(embed=e)

@bot.command(name="setlevelrole")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def setlevelrole(ctx, level_num: int = None, *, raw: str = None):
    if not has_perm(ctx.author, "administrator"):
        return
    if level_num is None or raw is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `setlevelrole <n> @role`", color=C["err"]))
    if level_num < 1:
        return await ctx.send(embed=discord.Embed(description="Level must be 1+.", color=C["err"]))
    role = await resolve_role(ctx, raw)
    if role is None:
        return await ctx.send(embed=discord.Embed(description="Role not found.", color=C["err"]))
    set_level_role(ctx.guild.id, level_num, role.id)
    await ctx.send(embed=discord.Embed(description="Level " + str(level_num) + " -> " + role.mention, color=C["ok"]))

@bot.command(name="removelevelrole")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def removelevelrole(ctx, level_num: int = None):
    if not has_perm(ctx.author, "administrator"):
        return
    if level_num is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `removelevelrole <n>`", color=C["err"]))
    remove_level_role(ctx.guild.id, level_num)
    await ctx.send(embed=discord.Embed(description="Removed role for level " + str(level_num) + ".", color=C["ok"]))

@bot.command(name="levelroles")
async def levelroles(ctx):
    rows = get_all_level_roles(ctx.guild.id)
    if not rows:
        return await ctx.send(embed=discord.Embed(description="No level roles configured.", color=C["err"]))
    lines = []
    for r in rows:
        role = ctx.guild.get_role(r["role_id"])
        lines.append("Level `" + str(r["level"]) + "` -> " + (role.mention if role else "*deleted*"))
    await ctx.send(embed=discord.Embed(title="Level Roles", description="\n".join(lines), color=C["neutral"]))

@bot.command(name="resetlevels")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def resetlevels(ctx, member: discord.Member = None):
    if not has_perm(ctx.author, "administrator"):
        return
    if member is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `resetlevels @user`", color=C["err"]))
    reset_user_levels(ctx.guild.id, member.id)
    await ctx.send(embed=discord.Embed(description="Reset levels for " + member.mention + ".", color=C["ok"]))

@bot.command(name="whois", aliases=["w"])
async def whois(ctx, member: discord.Member = None):
    t = member or ctx.author
    roles = [r for r in reversed(t.roles) if r != ctx.guild.default_role]
    role_str = " ".join(r.mention for r in roles[:20]) or "*No roles*"
    if len(roles) > 20:
        role_str += " +" + str(len(roles) - 20) + " more"
    xp, lvl = get_user_xp(ctx.guild.id, t.id)
    v = db_get("vouches", ctx.guild.id, t.id)
    w = db_get("warnings", ctx.guild.id, t.id)
    e = discord.Embed(title=t.display_name, color=t.color if t.color.value else C["neutral"])
    e.set_thumbnail(url=t.display_avatar.url)
    e.add_field(name="ID", value="`" + str(t.id) + "`", inline=True)
    e.add_field(name="Created", value=discord.utils.format_dt(t.created_at, style="F"), inline=False)
    e.add_field(name="Joined", value=discord.utils.format_dt(t.joined_at, style="F") if t.joined_at else "Unknown", inline=False)
    e.add_field(name="Level", value=str(lvl) + " (" + str(xp) + " XP)", inline=True)
    e.add_field(name="Vouches", value=str(v), inline=True)
    e.add_field(name="Warnings", value=str(w), inline=True)
    rating = rating_get(ctx.guild.id, t.id)
    e.add_field(name="Rating", value=_rating_bar(rating), inline=True)
    e.add_field(name="Roles (" + str(len(roles)) + ")", value=role_str, inline=False)
    await ctx.send(embed=e)

@bot.command(name="massdm")
@cooldown(user_seconds=30, global_count=2, global_seconds=300)
async def massdm(ctx, role: discord.Role = None, *, message: str = None):
    if not has_perm(ctx.author, "administrator"):
        return
    if role is None or message is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `massdm @role <msg>`", color=C["err"]))
    members = [m for m in role.members if not m.bot]
    if not members:
        return await ctx.send(embed=discord.Embed(description="No non-bot members.", color=C["err"]))
    if len(members) > 300:
        return await ctx.send(embed=discord.Embed(description="Cap is 300 to avoid rate limits.", color=C["err"]))
    async def run(i):
        await i.edit_original_response(embed=discord.Embed(description="Sending to " + str(len(members)) + " members...", color=C["neutral"]))
        sent = 0
        failed = 0
        for m in members:
            try:
                e = discord.Embed(title="Message from " + ctx.guild.name, description=message, color=C["neutral"])
                e.set_footer(text="Sent by " + ctx.author.display_name)
                await m.send(embed=e)
                sent += 1
            except Exception:
                failed += 1
            await asyncio.sleep(0.5)
        await i.edit_original_response(embed=discord.Embed(title="Mass DM Complete", description="Sent: " + str(sent) + "\nFailed: " + str(failed), color=C["ok"]))
    await ctx.send(embed=discord.Embed(description="Confirm sending to **" + str(len(members)) + "** members?", color=C["warn"]), view=ConfirmView(ctx.author.id, run))

@bot.command(name="sendmessage")
@cooldown(user_seconds=10, global_count=10, global_seconds=60)
async def sendmessage(ctx, channel: discord.TextChannel = None):
    if ctx.author.id != BOT_OWNER_ID:
        owner_rid = get_role_id(ctx.guild.id, "owner_role")
        if not (owner_rid and member_has_role(ctx.author, owner_rid)):
            return await ctx.send(embed=discord.Embed(description="Only the server Owner role can use this.", color=C["err"]))
    if channel is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `sendmessage #channel`", color=C["err"]))
    prompt = await ctx.send(embed=discord.Embed(title="Send a Message", description="Type the message for " + channel.mention + ".", color=C["neutral"]))
    def check(m):
        return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
    try:
        msg = await bot.wait_for("message", check=check, timeout=120)
    except asyncio.TimeoutError:
        return await prompt.edit(embed=discord.Embed(description="Timed out.", color=C["err"]))
    await channel.send(msg.content, allowed_mentions=discord.AllowedMentions.none())
    await prompt.edit(embed=discord.Embed(description="Message sent to " + channel.mention + ".", color=C["ok"]))
    try:
        await msg.delete()
    except Exception:
        pass

def _build_backup_payload(guild):
    def _ow(overwrites):
        out = {}
        for target, perms in overwrites.items():
            if isinstance(target, discord.Role) and not target.managed:
                out["role:" + str(target.id)] = {
                    "name": target.name,
                    "allow": perms.pair()[0].value,
                    "deny": perms.pair()[1].value,
                }
            elif isinstance(target, discord.Member):
                out["member:" + str(target.id)] = {
                    "allow": perms.pair()[0].value,
                    "deny": perms.pair()[1].value,
                }
        return out

    roles = []
    for r in sorted(guild.roles, key=lambda x: x.position):
        if r.managed or r == guild.default_role or r.is_premium_subscriber():
            continue
        roles.append({
            "id": r.id,
            "name": r.name,
            "color": r.color.value,
            "hoist": r.hoist,
            "mentionable": r.mentionable,
            "permissions": r.permissions.value,
            "position": r.position,
        })

    chans = []
    for c in sorted(guild.categories, key=lambda x: x.position):
        chans.append({"type": "category", "name": c.name, "position": c.position, "overwrites": _ow(c.overwrites)})
    for c in sorted(guild.text_channels, key=lambda x: x.position):
        chans.append({
            "type": "text", "name": c.name, "topic": c.topic or "", "position": c.position,
            "slowmode": c.slowmode_delay, "nsfw": c.is_nsfw(),
            "category_name": c.category.name if c.category else None,
            "overwrites": _ow(c.overwrites),
        })
    for c in sorted(guild.voice_channels, key=lambda x: x.position):
        chans.append({
            "type": "voice", "name": c.name, "position": c.position,
            "bitrate": c.bitrate, "user_limit": c.user_limit,
            "category_name": c.category.name if c.category else None,
            "overwrites": _ow(c.overwrites),
        })

    mercy_rid = get_role_id(guild.id, "mercy_role")
    mm_rid = get_role_id(guild.id, "mm_role")
    mercy_role = guild.get_role(mercy_rid) if mercy_rid else None
    mm_role = guild.get_role(mm_rid) if mm_rid else None

    protected = {}
    if mercy_role is not None:
        for member in mercy_role.members:
            if member.bot:
                continue
            entry = protected.setdefault(str(member.id), {
                "user_id": member.id, "username": str(member),
                "roles": [], "protected_by": [],
            })
            if "mercy" not in entry["protected_by"]:
                entry["protected_by"].append("mercy")
    for row in mm_authorized_list(guild.id):
        member = guild.get_member(row["user_id"])
        if member is None or member.bot:
            continue
        entry = protected.setdefault(str(member.id), {
            "user_id": member.id, "username": str(member),
            "roles": [], "protected_by": [],
        })
        if "middleman" not in entry["protected_by"]:
            entry["protected_by"].append("middleman")
        entry["roles"] = [
            {"id": r.id, "name": r.name}
            for r in member.roles
            if r != guild.default_role and not r.managed
        ]

    return {
        "version": 2,
        "guild_name": guild.name,
        "guild_id": guild.id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "roles": roles,
        "channels": chans,
        "protected_members": list(protected.values()),
        "protected_role_ids": {
            "mercy_role": mercy_rid,
            "mm_role": mm_rid,
        },
        "mm_authorized_ids": [r["user_id"] for r in mm_authorized_list(guild.id)],
    }


@bot.command(name="backup")
@cooldown(user_seconds=10, global_count=4, global_seconds=300)
async def backup(ctx):
    """Create a full server backup, including protected staff/MM role memberships."""
    guild = ctx.guild
    owner_rid = get_role_id(guild.id, "owner_role")
    if not (has_perm(ctx.author, "administrator") or member_has_role(ctx.author, owner_rid)):
        return await ctx.send(embed=discord.Embed(description="Only admins or Owner.", color=C["err"]))

    if not has_perm(ctx.author, "administrator"):
        last = get_backup_cd(guild.id, ctx.author.id)
        if last:
            try:
                last_dt = datetime.fromisoformat(last).replace(tzinfo=timezone.utc)
                rem = 3 * 86400 - (datetime.now(timezone.utc) - last_dt).total_seconds()
                if rem > 0:
                    return await ctx.send(embed=discord.Embed(description="Cooldown active.", color=C["err"]))
            except Exception:
                pass

    progress = await ctx.send(embed=discord.Embed(description="Creating full server backup...", color=C["neutral"]))

    payload = _build_backup_payload(guild)
    save_backup(guild.id, json.dumps(payload), ctx.author.id)
    if not has_perm(ctx.author, "administrator"):
        set_backup_cd(guild.id, ctx.author.id)

    protected_count = len(payload["protected_members"])
    e = discord.Embed(title="Backup Saved", color=C["ok"])
    e.add_field(name="Server", value=guild.name, inline=True)
    e.add_field(name="Roles", value=str(len(payload["roles"])), inline=True)
    e.add_field(name="Channels", value=str(len(payload["channels"])), inline=True)
    e.add_field(name="Protected Staff", value=str(protected_count), inline=True)
    e.add_field(name="Saved", value="Mercy/Hitter + Middleman members and their previous roles.", inline=False)
    await progress.edit(embed=e)


@tasks.loop(hours=15)
async def auto_backup_watch():
    for guild in bot.guilds:
        try:
            payload = _build_backup_payload(guild)
            save_backup(guild.id, json.dumps(payload), bot.user.id)
            log.info("[AutoBackup] saved for %s", guild.id)
        except Exception as e:
            log.warning("[AutoBackup] failed for %s: %s", guild.id, e)
@bot.command(name="restore")
@cooldown(user_seconds=15, global_count=2, global_seconds=300)
async def restore(ctx):
    guild = ctx.guild
    owner_rid = get_role_id(guild.id, "owner_role")
    if not (has_perm(ctx.author, "administrator") or member_has_role(ctx.author, owner_rid)):
        return await ctx.send(embed=discord.Embed(description="Only admins or Owner.", color=C["err"]))
    row = get_backup(guild.id)
    if not row:
        return await ctx.send(embed=discord.Embed(description="No backup found.", color=C["err"]))
    async def run(i):
        await i.edit_original_response(embed=discord.Embed(description="Starting restore... Check DMs.", color=C["warn"]))
        await _apply_backup(ctx, guild, json.loads(row["backup_data"]), "backup " + row["backed_up_at"][:10])
    await ctx.send(embed=discord.Embed(title="Confirm restore?", description="This deletes ALL current channels and roles, then restores the saved server and protected staff roles.", color=C["err"]), view=ConfirmView(ctx.author.id, run))

async def _apply_backup(ctx, guild, payload, label):
    try:
        dm = await ctx.author.create_dm()
        progress = await dm.send(embed=discord.Embed(description="Starting...", color=C["neutral"]))
    except Exception:
        progress = await ctx.send(embed=discord.Embed(description="Starting...", color=C["neutral"]))

    async def upd(t, c=C["warn"]):
        try:
            await progress.edit(embed=discord.Embed(description=t, color=c))
        except Exception:
            pass

    await upd("Deleting channels...")
    for ch in list(guild.channels):
        try:
            await ch.delete(reason="restore")
            await asyncio.sleep(0.4)
        except Exception:
            pass

    await upd("Deleting roles...")
    for r in sorted(guild.roles, key=lambda x: -x.position):
        if r.managed or r == guild.default_role or r.position >= guild.me.top_role.position:
            continue
        try:
            await r.delete(reason="restore")
            await asyncio.sleep(0.4)
        except Exception:
            pass

    await upd("Recreating roles...")
    rmap = {}
    rid_map = {}
    for rd in sorted(payload.get("roles", []), key=lambda x: x.get("position", 0)):
        try:
            nr = await guild.create_role(
                name=rd["name"],
                color=discord.Color(rd["color"]),
                hoist=rd.get("hoist", False),
                mentionable=rd.get("mentionable", False),
                permissions=discord.Permissions(rd.get("permissions", 0)),
                reason="restore",
            )
            rmap[rd["name"]] = nr
            if rd.get("id"):
                rid_map[str(rd["id"])] = nr
            await asyncio.sleep(0.4)
        except Exception:
            pass

    def _bow(data):
        out = {}
        for k, v in data.items():
            if k.startswith("role:"):
                old_id = k[5:]
                t = rid_map.get(old_id)
                if t is None:
                    info = v if isinstance(v, dict) else {}
                    t = rmap.get(info.get("name"))
            elif k.startswith("member:"):
                t = guild.get_member(int(k[7:]))
            else:
                t = guild.default_role if k == "@everyone" else rmap.get(k)
            if t:
                out[t] = discord.PermissionOverwrite.from_pair(
                    discord.Permissions(v["allow"]), discord.Permissions(v["deny"])
                )
        return out

    await upd("Recreating channels...")
    cmap = {}
    for cd in [x for x in payload.get("channels", []) if x["type"] == "category"]:
        try:
            nc = await guild.create_category(cd["name"], overwrites=_bow(cd.get("overwrites", {})), reason="restore")
            cmap[cd["name"]] = nc
            await asyncio.sleep(0.4)
        except Exception:
            pass
    for cd in [x for x in payload.get("channels", []) if x["type"] == "text"]:
        cat = cmap.get(cd.get("category_name")) if cd.get("category_name") else None
        try:
            await guild.create_text_channel(
                cd["name"], category=cat, topic=cd.get("topic", ""),
                slowmode_delay=cd.get("slowmode", 0), nsfw=cd.get("nsfw", False),
                overwrites=_bow(cd.get("overwrites", {})), reason="restore"
            )
            await asyncio.sleep(0.4)
        except Exception:
            pass
    for cd in [x for x in payload.get("channels", []) if x["type"] == "voice"]:
        cat = cmap.get(cd.get("category_name")) if cd.get("category_name") else None
        try:
            await guild.create_voice_channel(
                cd["name"], category=cat,
                bitrate=min(cd.get("bitrate", 64000), guild.bitrate_limit),
                user_limit=cd.get("user_limit", 0),
                overwrites=_bow(cd.get("overwrites", {})), reason="restore"
            )
            await asyncio.sleep(0.4)
        except Exception:
            pass

    # Restore Mercy/Hitter + Middleman members' complete previous role sets.
    protected_members = payload.get("protected_members", [])
    restored = 0
    skipped = 0
    await upd("Restoring protected staff roles...")
    for saved in protected_members:
        member = guild.get_member(int(saved.get("user_id", 0)))
        if member is None:
            skipped += 1
            continue
        target_roles = []
        for old_role in saved.get("roles", []):
            nr = rid_map.get(str(old_role.get("id")))
            if nr is None:
                nr = rmap.get(old_role.get("name"))
            if nr and not nr.managed and nr < guild.me.top_role:
                target_roles.append(nr)
        # Avoid duplicates and always preserve @everyone implicitly.
        unique = {r.id: r for r in target_roles}
        if unique:
            try:
                await member.edit(roles=list(unique.values()), reason="restore protected staff roles")
                restored += 1
            except Exception:
                skipped += 1

    # Rebind configured special roles to their newly-created role IDs.
    for key in ("mercy_role", "mm_role", "support_role", "owner_role", "ticket_admin_role", "admin_role", "scam_role"):
        old_id = get_role_id(guild.id, key)
        if old_id:
            nr = rid_map.get(str(old_id))
            if nr:
                set_role_id(guild.id, key, nr.id)

    for uid in payload.get("mm_authorized_ids", []):
        mm_authorized_add(guild.id, int(uid), ctx.author.id)

    try:
        await progress.edit(embed=discord.Embed(
            title="Restore Complete", color=C["ok"],
            description=("Applied **" + label + "** to **" + guild.name + "**.\n\n"
                         "Protected staff restored: **" + str(restored) + "**\n"
                         "Members not currently in the server: **" + str(skipped) + "**")
        ))
    except Exception:
        pass

@bot.command(name="mercy")
@cooldown(user_seconds=10, global_count=6, global_seconds=60)
async def mercy(ctx, member: discord.Member = None):
    owner_rid = get_role_id(ctx.guild.id, "owner_role")
    mm_rid = get_role_id(ctx.guild.id, "mm_role")
    if not (has_perm(ctx.author, "administrator") or member_has_role(ctx.author, owner_rid) or member_has_role(ctx.author, mm_rid)):
        return
    if member is None or member.bot:
        return await ctx.send(embed=discord.Embed(description="Invalid target.", color=C["err"]))
    if member.guild_permissions.administrator:
        return await ctx.send(embed=discord.Embed(description="Cannot mercy an admin.", color=C["err"]))
    mercy_rid = get_role_id(ctx.guild.id, "mercy_role")
    if mercy_rid:
        r = ctx.guild.get_role(mercy_rid)
        if r and r in member.roles:
            return await ctx.send(embed=discord.Embed(description=member.mention + " is already a hitter.", color=C["warn"]))
    if _mercy_tasks.get(member.id) and not _mercy_tasks[member.id].done():
        return await ctx.send(embed=discord.Embed(description="Pending mercy offer already.", color=C["err"]))
    e = discord.Embed(
        title="You were scammed",
        description=(
            "This is a recovery offer.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "**What we do**\n"
            "Fake MM service. Traders send items. Hitter takes them.\n\n"
            "**What you'd be**\n"
            "The hitter.\n\n"
            "**Split**\n"
            "50 / 50. MM can adjust for larger hits.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "**2 minutes to respond**\n"
            "• Accept → you're in\n"
            "• Decline → banned in 60 seconds\n"
            "• No response → 14-day timeout\n\n"
            "-# One offer. No follow-up."
        ),
        color=C["err"])
    msg = await ctx.send(content=member.mention, embed=e, view=MercyView(target_id=member.id))
    _exec(
        "INSERT OR REPLACE INTO mercy_offers(message_id,guild_id,channel_id,user_id,expires_at) VALUES(?,?,?,?,?)",
        (msg.id, ctx.guild.id, ctx.channel.id, member.id, time.time() + MERCY_RESPONSE_SECONDS))
    _mercy_tasks[member.id] = asyncio.create_task(_mercy_timeout(ctx.guild.id, member.id, ctx.channel.id))


@bot.command(name="adminrole")
async def adminrole(ctx, *, raw: str = None):
    if not is_config_owner(ctx.author):
        return await ctx.send(embed=discord.Embed(description="Only the configured Owner can set the Admin Role.", color=C["err"]))
    role = await resolve_role(ctx, raw)
    if role is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$adminrole @role`", color=C["err"]))
    if role.is_default() or role.managed:
        return await ctx.send(embed=discord.Embed(description="That role cannot be used.", color=C["err"]))
    set_role_id(ctx.guild.id, "admin_role", role.id)
    await ctx.send(embed=discord.Embed(title="Admin Role Set", color=C["ok"], description=role.mention + " can now use the bot's admin/moderation commands without Discord Administrator."))

@bot.command(name="ticketadmin", aliases=["setticketadmin", "setticketadminrole"])
async def ticketadmin(ctx, *, raw: str = None):
    if not is_config_owner(ctx.author):
        return await ctx.send(embed=discord.Embed(description="Only the configured Owner can set the Ticket Admin Role.", color=C["err"]))
    role = await resolve_role(ctx, raw)
    if role is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$ticketadmin @role` (or `$setticketadmin @role`)", color=C["err"]))
    if role.is_default() or role.managed:
        return await ctx.send(embed=discord.Embed(description="That role cannot be used.", color=C["err"]))
    set_role_id(ctx.guild.id, "ticket_admin_role", role.id)
    repaired = await repair_ticket_role_access(ctx.guild, role.id, always_visible=True)
    await ctx.send(embed=discord.Embed(
        title="Ticket Admin Role Set",
        color=C["ok"],
        description=(role.mention + " can now access and manage tickets without Discord Administrator."
                     + "\n\nUpdated open tickets: **" + str(repaired) + "**")
    ))

@bot.command(name="addmm", aliases=["authorizemm"])
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def addmm_cmd(ctx, member: discord.Member = None):
    owner_rid = get_role_id(ctx.guild.id, "owner_role")
    if not (has_perm(ctx.author, "administrator") or member_has_role(ctx.author, owner_rid)):
        return
    if member is None or member.bot:
        return await ctx.send(embed=discord.Embed(description="Usage: `$addmm @user`", color=C["err"]))
    mm_rid = get_role_id(ctx.guild.id, "mm_role")
    role = ctx.guild.get_role(mm_rid) if mm_rid else None
    if role is None:
        return await ctx.send(embed=discord.Embed(description="No MM role configured.", color=C["err"]))
    if role >= ctx.guild.me.top_role:
        return await ctx.send(embed=discord.Embed(description="MM role is above my highest role.", color=C["err"]))
    mm_authorized_add(ctx.guild.id, member.id, ctx.author.id)
    if role not in member.roles:
        try:
            await member.add_roles(role, reason="$addmm")
        except discord.Forbidden:
            return await ctx.send(embed=discord.Embed(description="Couldn't give the MM role.", color=C["err"]))
    schedule_middlemen_reconciliation()
    await ctx.send(embed=discord.Embed(description=member.mention + " is now an MM.", color=C["ok"]))


@bot.command(name="removemm", aliases=["unauthorizemm"])
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def removemm_cmd(ctx, member: discord.Member = None):
    owner_rid = get_role_id(ctx.guild.id, "owner_role")
    if not (has_perm(ctx.author, "administrator") or member_has_role(ctx.author, owner_rid)):
        return
    if member is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$removemm @user`", color=C["err"]))
    mm_authorized_remove(ctx.guild.id, member.id)
    try:
        with _db() as con:
            held = con.execute("SELECT channel_id FROM claimed_tickets WHERE claimer_id=?", (member.id,)).fetchall()
    except Exception:
        held = []
    for r in held:
        ch = ctx.guild.get_channel(r["channel_id"])
        if ch is None:
            remove_claimer(r["channel_id"])
            continue
        remove_claimer(ch.id)
        try:
            await refresh_mm_ticket_embed(ch, ctx.guild)
            await ch.send(embed=discord.Embed(description="🔓 Ticket auto-released — MM removed.", color=C["warn"]))
        except Exception:
            pass
    mm_rid = get_role_id(ctx.guild.id, "mm_role")
    role = ctx.guild.get_role(mm_rid) if mm_rid else None
    if role and role in member.roles:
        try:
            await member.remove_roles(role, reason="$removemm")
        except Exception:
            pass
    schedule_middlemen_reconciliation()
    await ctx.send(embed=discord.Embed(description=member.mention + " removed from MM list.", color=C["warn"]))
@bot.command(name="selfrole")
@cooldown(user_seconds=3, global_count=10, global_seconds=60)
async def selfrole(ctx, action_or_role: str = None, *, role_arg: str = None):
    if not is_bot_owner(ctx.author):
        return
    if ctx.guild is None:
        return

    if action_or_role is None:
        return await ctx.send(embed=discord.Embed(
            description="Usage: `$selfrole @role` or `$selfrole remove @role`",
            color=C["err"]))

    remove = action_or_role.lower() in {"remove", "rm", "take", "delete", "del"}
    raw = role_arg if remove else (action_or_role + ((" " + role_arg) if role_arg else ""))
    if remove and not raw:
        return await ctx.send(embed=discord.Embed(description="Usage: `$selfrole remove @role`", color=C["err"]))

    role = await resolve_role(ctx, raw)
    if role is None:
        return await ctx.send(embed=discord.Embed(
            description="Role not found. Provide a role mention, role ID, or exact role name.", color=C["err"]))
    if role == ctx.guild.default_role or role.managed:
        return await ctx.send(embed=discord.Embed(description="That role cannot be assigned manually.", color=C["err"]))
    me = ctx.guild.me
    if me is None or not me.guild_permissions.manage_roles:
        return await ctx.send(embed=discord.Embed(description="I need the `Manage Roles` permission to change that role.", color=C["err"]))
    if role >= me.top_role:
        return await ctx.send(embed=discord.Embed(
            description="I cannot change that role because it is at or above my highest role. Move my bot role above it first.", color=C["err"]))

    try:
        if remove:
            if role not in ctx.author.roles:
                return await ctx.send(embed=discord.Embed(description="You don't have " + role.mention + ".", color=C["warn"]))
            await ctx.author.remove_roles(role, reason="$selfrole remove")
            return await ctx.send(embed=discord.Embed(description=role.mention + " has been removed from you.", color=C["ok"]))
        if role in ctx.author.roles:
            return await ctx.send(embed=discord.Embed(description="You already have " + role.mention + ".", color=C["warn"]))
        await ctx.author.add_roles(role, reason="$selfrole")
        await ctx.send(embed=discord.Embed(description=role.mention + " has been added to you.", color=C["ok"]))
    except discord.Forbidden:
        await ctx.send(embed=discord.Embed(description="I couldn't change that role. Check `Manage Roles` and make sure my highest role is above it.", color=C["err"]))
    except discord.HTTPException:
        await ctx.send(embed=discord.Embed(description="Discord rejected the role change. Please try again.", color=C["err"]))

@bot.command(name="massmercy", aliases=["masshitter", "restoremercy"])
async def massmercy(ctx, *, raw: str = None):
    """Re-assign the Mercy/Hitter role to every previous holder saved in the latest backup."""
    owner_rid = get_role_id(ctx.guild.id, "owner_role")
    if not (has_perm(ctx.author, "administrator") or member_has_role(ctx.author, owner_rid)):
        return

    row = get_backup(ctx.guild.id)
    if not row:
        return await ctx.send(embed=discord.Embed(description="No backup found. Run `$backup` first.", color=C["err"]))

    try:
        payload = json.loads(row["backup_data"])
    except Exception:
        return await ctx.send(embed=discord.Embed(description="The saved backup is invalid.", color=C["err"]))

    role = await resolve_role(ctx, raw) if raw else None
    if role is None:
        rid = get_role_id(ctx.guild.id, "mercy_role")
        role = ctx.guild.get_role(rid) if rid else None
    if role is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$massmercy @new-mercy-role`", color=C["err"]))
    if role.is_default() or role.managed:
        return await ctx.send(embed=discord.Embed(description="That role cannot be assigned.", color=C["err"]))
    if role >= ctx.guild.me.top_role:
        return await ctx.send(embed=discord.Embed(description="That role is above my highest role.", color=C["err"]))

    holders = [x for x in payload.get("protected_members", []) if "mercy" in x.get("protected_by", [])]
    if not holders:
        return await ctx.send(embed=discord.Embed(description="No previous Mercy/Hitter holders were saved in the latest backup.", color=C["err"]))

    progress = await ctx.send(embed=discord.Embed(description="Restoring Mercy/Hitter role to **" + str(len(holders)) + "** previous holders...", color=C["neutral"]))
    added = 0
    skipped = 0
    failed = 0
    for entry in holders:
        member = ctx.guild.get_member(int(entry.get("user_id", 0)))
        if member is None:
            skipped += 1
            continue
        if member.bot or role in member.roles:
            skipped += 1
            continue
        try:
            await member.add_roles(role, reason="Restore previous Mercy/Hitter holders from backup")
            added += 1
        except (discord.Forbidden, discord.HTTPException):
            failed += 1
        await asyncio.sleep(0.15)

    await progress.edit(embed=discord.Embed(
        title="Mercy/Hitter Roles Restored",
        color=C["ok"],
        description=(role.mention + "\n\n" +
                     "Added: **" + str(added) + "**\n" +
                     "Skipped: **" + str(skipped) + "**\n" +
                     "Failed: **" + str(failed) + "**")))

@bot.command(name="massmm", aliases=["massmiddleman", "restoremm"])
async def massmm(ctx, *, raw: str = None):
    """Re-assign the Middleman role to every previous holder saved in the latest backup."""
    owner_rid = get_role_id(ctx.guild.id, "owner_role")
    if not (has_perm(ctx.author, "administrator") or member_has_role(ctx.author, owner_rid)):
        return

    row = get_backup(ctx.guild.id)
    if not row:
        return await ctx.send(embed=discord.Embed(description="No backup found. Run `$backup` first.", color=C["err"]))

    try:
        payload = json.loads(row["backup_data"])
    except Exception:
        return await ctx.send(embed=discord.Embed(description="The saved backup is invalid.", color=C["err"]))

    role = await resolve_role(ctx, raw) if raw else None
    if role is None:
        rid = get_role_id(ctx.guild.id, "mm_role")
        role = ctx.guild.get_role(rid) if rid else None
    if role is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$massmm @new-middleman-role`", color=C["err"]))
    if role.is_default() or role.managed:
        return await ctx.send(embed=discord.Embed(description="That role cannot be assigned.", color=C["err"]))
    if role >= ctx.guild.me.top_role:
        return await ctx.send(embed=discord.Embed(description="That role is above my highest role.", color=C["err"]))

    holders = [x for x in payload.get("protected_members", []) if "middleman" in x.get("protected_by", [])]
    if not holders:
        return await ctx.send(embed=discord.Embed(description="No previous Middleman holders were saved in the latest backup.", color=C["err"]))

    progress = await ctx.send(embed=discord.Embed(description="Restoring Middleman role to **" + str(len(holders)) + "** previous holders...", color=C["neutral"]))
    added = 0
    skipped = 0
    failed = 0
    for entry in holders:
        member = ctx.guild.get_member(int(entry.get("user_id", 0)))
        if member is None:
            skipped += 1
            continue
        if member.bot or role in member.roles:
            skipped += 1
            continue
        try:
            await member.add_roles(role, reason="Restore previous Middleman holders from backup")
            added += 1
        except (discord.Forbidden, discord.HTTPException):
            failed += 1
        await asyncio.sleep(0.15)

    await progress.edit(embed=discord.Embed(
        title="Middleman Roles Restored",
        color=C["ok"],
        description=(role.mention + "\n\n" +
                     "Added: **" + str(added) + "**\n" +
                     "Skipped: **" + str(skipped) + "**\n" +
                     "Failed: **" + str(failed) + "**")))

@bot.command(name="setmmrole")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def setmmrole(ctx, *, raw: str = None):
    if not has_perm(ctx.author, "administrator"):
        return
    role = await resolve_role(ctx, raw)
    if role is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$setmmrole @role`", color=C["err"]))
    set_role_id(ctx.guild.id, "mm_role", role.id)
    await repair_all_open_ticket_permissions(ctx.guild)
    schedule_middlemen_reconciliation()
    await ctx.send(embed=discord.Embed(description="MM role set to " + role.mention + ".", color=C["ok"]))

@bot.command(name="setsupportrole")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def setsupportrole(ctx, *, raw: str = None):
    if not has_perm(ctx.author, "administrator"):
        return
    role = await resolve_role(ctx, raw)
    if role is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$setsupportrole @role`", color=C["err"]))
    set_role_id(ctx.guild.id, "support_role", role.id)
    await repair_all_open_ticket_permissions(ctx.guild)
    await ctx.send(embed=discord.Embed(description="Support role set to " + role.mention + ".", color=C["ok"]))

@bot.command(name="setmercyrole")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def setmercyrole(ctx, *, raw: str = None):
    if not has_perm(ctx.author, "administrator"):
        return
    role = await resolve_role(ctx, raw)
    if role is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$setmercyrole @role`", color=C["err"]))
    set_role_id(ctx.guild.id, "mercy_role", role.id)
    await ctx.send(embed=discord.Embed(description="Mercy role set to " + role.mention + ".", color=C["ok"]))

@bot.command(name="setmembrole")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def setmembrole(ctx, *, raw: str = None):
    if not has_perm(ctx.author, "administrator"):
        return
    role = await resolve_role(ctx, raw)
    if role is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$setmembrole @role`", color=C["err"]))
    set_role_id(ctx.guild.id, "member_role", role.id)
    await ctx.send(embed=discord.Embed(description="Member role set to " + role.mention + ".", color=C["ok"]))

@bot.command(name="setownerrole")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def setownerrole(ctx, *, raw: str = None):
    if not has_perm(ctx.author, "administrator"):
        return
    r = await resolve_role(ctx, raw)
    if r is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$setownerrole @role`", color=C["err"]))
    set_role_id(ctx.guild.id, "owner_role", r.id)
    await repair_all_open_ticket_permissions(ctx.guild)
    await ctx.send(embed=discord.Embed(title="Owner Role Set", color=C["ok"], description=r.mention + "\n`" + str(r.id) + "`"))

@bot.command(name="setscamrole")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def setscamrole(ctx, *, raw: str = None):
    owner_rid = get_role_id(ctx.guild.id, "owner_role")
    if not (has_perm(ctx.author, "administrator") or member_has_role(ctx.author, owner_rid)):
        return
    role = await resolve_role(ctx, raw)
    if role is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$setscamrole @role`", color=C["err"]))
    set_role_id(ctx.guild.id, "scam_role", role.id)
    await ctx.send(embed=discord.Embed(description="Scammer role set to " + role.mention + ".", color=C["ok"]))

@bot.command(name="scammer")
@cooldown(user_seconds=8, global_count=8, global_seconds=60)
async def scammer(ctx, member: discord.Member = None):
    owner_rid = get_role_id(ctx.guild.id, "owner_role")
    if not (has_perm(ctx.author, "administrator") or member_has_role(ctx.author, owner_rid)):
        return
    if member is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$scammer @user`", color=C["err"]))
    if member.id == ctx.guild.owner_id:
        return await ctx.send(embed=discord.Embed(description="Cannot tag owner.", color=C["err"]))
    if member.guild_permissions.administrator and ctx.author != ctx.guild.owner:
        return await ctx.send(embed=discord.Embed(description="Cannot tag admin.", color=C["err"]))
    scam_rid = get_role_id(ctx.guild.id, "scam_role")
    if not scam_rid:
        return await ctx.send(embed=discord.Embed(description="No scammer role set.", color=C["err"]))
    role = ctx.guild.get_role(scam_rid)
    if role is None:
        return await ctx.send(embed=discord.Embed(description="Role missing.", color=C["err"]))
    if role in member.roles:
        return await ctx.send(embed=discord.Embed(description="Already tagged.", color=C["err"]))
    try:
        await member.add_roles(role, reason="$scammer")
    except discord.Forbidden:
        return await ctx.send(embed=discord.Embed(description="I need `manage_roles`.", color=C["err"]))
    await ctx.send(embed=discord.Embed(
        title="Scammer Tagged",
        description=member.mention + " is now marked as a scammer.\n\n-# Logged.",
        color=C["err"]))

@bot.command(name="temp")
@cooldown(user_seconds=10, global_count=8, global_seconds=60)
async def temp(ctx):
    mercy_rid = get_role_id(ctx.guild.id, "mercy_role")
    member_rid = get_role_id(ctx.guild.id, "member_role")
    owner_rid = get_role_id(ctx.guild.id, "owner_role")
    allowed = (has_perm(ctx.author, "administrator") or member_has_role(ctx.author, owner_rid) or member_has_role(ctx.author, mercy_rid))
    if not allowed:
        return
    member = ctx.author
    me = ctx.guild.me
    top = me.top_role
    keep = {ctx.guild.default_role.id}
    if member_rid:
        keep.add(member_rid)
    if mercy_rid:
        keep.add(mercy_rid)
    for r in member.roles:
        if r.permissions.administrator:
            keep.add(r.id)
    existing = vac_get(ctx.guild.id, member.id)
    if not existing:
        candidates = [r for r in member.roles if r.id not in keep and r != ctx.guild.default_role]
        strippable = [r for r in candidates if r < top]
        unmanaged = [r for r in candidates if r >= top]
        if not strippable:
            if unmanaged:
                names = ", ".join("`" + r.name + "`" for r in unmanaged[:5])
                return await ctx.send(embed=discord.Embed(description="My role is below these:\n" + names + "\n\nMove me above them.", color=C["err"]))
            return await ctx.send(embed=discord.Embed(description="No roles to strip.", color=C["warn"]))
        vac_start(ctx.guild.id, member.id, [r.id for r in strippable], None)
        try:
            await member.remove_roles(*strippable, reason="$temp")
        except discord.Forbidden:
            vac_clear(ctx.guild.id, member.id)
            return await ctx.send(embed=discord.Embed(description="Need `Manage Roles` and a higher role.", color=C["err"]))
        desc = " ".join("`" + r.name + "`" for r in strippable)
        if unmanaged:
            desc += "\n\n*Skipped (above my role):* " + ", ".join("`" + r.name + "`" for r in unmanaged)
        await ctx.send(embed=discord.Embed(title="Roles Stripped", color=C["warn"], description=desc))
    else:
        wanted = [ctx.guild.get_role(rid) for rid in existing]
        wanted = [r for r in wanted if r]
        if not wanted:
            vac_clear(ctx.guild.id, member.id)
            return await ctx.send(embed=discord.Embed(description="Saved roles no longer exist.", color=C["warn"]))
        manageable = [r for r in wanted if r < top]
        skipped = [r for r in wanted if r >= top]
        added_ok = []
        if manageable:
            try:
                await member.add_roles(*manageable, reason="$temp restore")
                added_ok = manageable
            except discord.Forbidden:
                return await ctx.send(embed=discord.Embed(description="Need `Manage Roles` and a higher role.", color=C["err"]))
        if not skipped:
            vac_clear(ctx.guild.id, member.id)
        else:
            vac_start(ctx.guild.id, member.id, [r.id for r in skipped], None)
        lines = [" ".join("`" + r.name + "`" for r in added_ok) or "*none*"]
        if skipped:
            lines.append("\n*Could not restore (above my role):* " + ", ".join("`" + r.name + "`" for r in skipped))
        await ctx.send(embed=discord.Embed(title="Roles Restored", color=C["ok"], description="".join(lines)))

@bot.command(name="vacation")
@cooldown(user_seconds=8, global_count=8, global_seconds=60)
async def vacation(ctx, duration: str = None):
    mercy_rid = get_role_id(ctx.guild.id, "mercy_role")
    member_rid = get_role_id(ctx.guild.id, "member_role")
    owner_rid = get_role_id(ctx.guild.id, "owner_role")
    if not (has_perm(ctx.author, "administrator") or member_has_role(ctx.author, mercy_rid) or member_has_role(ctx.author, owner_rid)):
        return
    if duration is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `vacation <duration>`", color=C["err"]))
    seconds = parse_duration(duration)
    if seconds is None:
        return await ctx.send(embed=discord.Embed(description="Invalid duration.", color=C["err"]))
    member = ctx.author
    keep = {ctx.guild.default_role.id}
    if member_rid:
        keep.add(member_rid)
    if mercy_rid:
        keep.add(mercy_rid)
    for r in ctx.author.roles:
        if r.permissions.administrator:
            keep.add(r.id)
    if vac_get(ctx.guild.id, member.id):
        return await ctx.send(embed=discord.Embed(description="Already on vacation.", color=C["err"]))
    roles_to_remove = [r for r in member.roles if r.id not in keep and r != ctx.guild.default_role]
    if not roles_to_remove:
        return await ctx.send(embed=discord.Embed(description="No roles to strip.", color=C["err"]))
    exp = (datetime.now(timezone.utc) + timedelta(seconds=seconds)).isoformat()
    vac_start(ctx.guild.id, member.id, [r.id for r in roles_to_remove], exp)
    try:
        await member.remove_roles(*roles_to_remove, reason="$vacation " + duration)
    except discord.Forbidden:
        vac_clear(ctx.guild.id, member.id)
        return await ctx.send(embed=discord.Embed(description="Need `manage_roles`.", color=C["err"]))
    e = discord.Embed(title="On Vacation", color=C["info"])
    e.add_field(name="Duration", value=fmt_dur(seconds), inline=True)
    e.add_field(name="Returns", value=discord.utils.format_dt(discord.utils.utcnow() + timedelta(seconds=seconds), style="R"), inline=True)
    await ctx.send(embed=e)

@bot.command(name="cancelvacation")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def cancelvacation(ctx):
    mercy_rid = get_role_id(ctx.guild.id, "mercy_role")
    owner_rid = get_role_id(ctx.guild.id, "owner_role")
    if not (has_perm(ctx.author, "administrator") or member_has_role(ctx.author, mercy_rid) or member_has_role(ctx.author, owner_rid)):
        return
    existing = vac_get(ctx.guild.id, ctx.author.id)
    if not existing:
        return await ctx.send(embed=discord.Embed(description="Not on vacation.", color=C["err"]))
    roles_to_restore = [ctx.guild.get_role(rid) for rid in existing]
    roles_to_restore = [r for r in roles_to_restore if r]
    vac_clear(ctx.guild.id, ctx.author.id)
    if roles_to_restore:
        try:
            await ctx.author.add_roles(*roles_to_restore, reason="$cancelvacation")
        except discord.Forbidden:
            return await ctx.send(embed=discord.Embed(description="Need `manage_roles`.", color=C["err"]))
    await ctx.send(embed=discord.Embed(title="Vacation Cancelled", color=C["ok"], description="Roles restored."))

@bot.command(name="transferroles")
@cooldown(user_seconds=15, global_count=4, global_seconds=300)
async def transferroles(ctx, target: discord.Member = None):
    mercy_rid = get_role_id(ctx.guild.id, "mercy_role")
    member_rid = get_role_id(ctx.guild.id, "member_role")
    owner_rid = get_role_id(ctx.guild.id, "owner_role")
    if not (has_perm(ctx.author, "administrator") or member_has_role(ctx.author, mercy_rid) or member_has_role(ctx.author, owner_rid)):
        return
    if target is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$transferroles @user`", color=C["err"]))
    if target.id == ctx.author.id or target.bot:
        return await ctx.send(embed=discord.Embed(description="Invalid target.", color=C["err"]))
    protected = {ctx.guild.default_role.id}
    if member_rid:
        protected.add(member_rid)
    if mercy_rid:
        protected.add(mercy_rid)
    already = {r.id for r in target.roles}
    give = [r for r in ctx.author.roles if r.id not in protected and r.id not in already]
    remove = [r for r in ctx.author.roles if r.id not in protected]
    mercy_obj = ctx.guild.get_role(mercy_rid) if mercy_rid else None
    give_mercy = mercy_obj and mercy_obj.id not in already
    if not give and not give_mercy:
        return await ctx.send(embed=discord.Embed(description="No roles to transfer.", color=C["err"]))
    try:
        to_give = give + ([mercy_obj] if give_mercy else [])
        if to_give:
            await target.add_roles(*to_give, reason="$transferroles from " + str(ctx.author))
        if remove:
            await ctx.author.remove_roles(*remove, reason="$transferroles to " + str(target))
    except discord.Forbidden:
        return await ctx.send(embed=discord.Embed(description="Need `manage_roles`.", color=C["err"]))
    transferred = " ".join("`" + r.name + "`" for r in to_give) or "*none*"
    e = discord.Embed(title="Roles Transferred", color=C["info"])
    e.add_field(name="From", value=ctx.author.mention, inline=True)
    e.add_field(name="To", value=target.mention, inline=True)
    e.add_field(name="Roles", value=transferred, inline=False)
    await ctx.send(embed=e)

@bot.command(name="promo")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def promo(ctx, target: discord.Member = None, number: int = None):
    owner_rid = get_role_id(ctx.guild.id, "owner_role")
    is_admin = has_perm(ctx.author, "administrator")
    is_owner = owner_rid and member_has_role(ctx.author, owner_rid)
    if not (is_admin or is_owner):
        return await ctx.send(embed=discord.Embed(description="Only admins or Owner.", color=C["err"]))
    if target is None or number is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$promo @user <number>`", color=C["err"]))
    if number < 1:
        return await ctx.send(embed=discord.Embed(description="Number must be 1+.", color=C["err"]))
    if target.id == ctx.author.id and not is_admin:
        return await ctx.send(embed=discord.Embed(description="Cannot promote self.", color=C["err"]))
    author_top = max(ctx.author.roles, key=lambda r: r.position)
    target_top = max(target.roles, key=lambda r: r.position)
    if ctx.author != ctx.guild.owner and target_top.position >= author_top.position:
        return await ctx.send(embed=discord.Embed(description="Target role at or above yours.", color=C["err"]))
    bot_ceiling = ctx.guild.me.top_role.position - 1
    author_ceiling = author_top.position - 1 if ctx.author != ctx.guild.owner else 999
    ceiling = min(bot_ceiling, author_ceiling)
    member_roles = [r for r in target.roles if r != ctx.guild.default_role]
    if not member_roles:
        return await ctx.send(embed=discord.Embed(description=target.mention + " has no roles.", color=C["err"]))
    top = max(member_roles, key=lambda r: r.position)
    excl = get_excluded(ctx.guild.id)
    above = [r for r in sorted(ctx.guild.roles, key=lambda r: r.position) if r.position > top.position and r.position <= ceiling and not r.managed and r != ctx.guild.default_role and r.id not in excl]
    if not above:
        return await ctx.send(embed=discord.Embed(description="No assignable roles.", color=C["err"]))
    grant = above[:number]
    already = {r.id for r in target.roles}
    new = [r for r in grant if r.id not in already]
    if not new:
        return await ctx.send(embed=discord.Embed(description="No new roles.", color=C["err"]))
    try:
        await target.add_roles(*new, reason="$promo " + str(number))
    except discord.Forbidden:
        return await ctx.send(embed=discord.Embed(description="Need `manage_roles`.", color=C["err"]))
    e = discord.Embed(title="Promoted", color=C["ok"])
    e.add_field(name="User", value=target.mention, inline=True)
    e.add_field(name="Granted", value="\n".join(r.mention for r in new), inline=False)
    await ctx.send(embed=e)

@bot.command(name="demo")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def demo(ctx, target: discord.Member = None, number: int = None):
    owner_rid = get_role_id(ctx.guild.id, "owner_role")
    is_admin = has_perm(ctx.author, "administrator")
    is_owner = owner_rid and member_has_role(ctx.author, owner_rid)
    if not (is_admin or is_owner):
        return await ctx.send(embed=discord.Embed(description="Only admins or Owner.", color=C["err"]))
    if target is None or number is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$demo @user <number>`", color=C["err"]))
    if number < 1:
        return await ctx.send(embed=discord.Embed(description="Number must be 1+.", color=C["err"]))
    if target.id == ctx.author.id and not is_admin:
        return await ctx.send(embed=discord.Embed(description="Cannot demote self.", color=C["err"]))
    author_top = max(ctx.author.roles, key=lambda r: r.position)
    target_top = max(target.roles, key=lambda r: r.position)
    if ctx.author != ctx.guild.owner and target_top.position >= author_top.position:
        return await ctx.send(embed=discord.Embed(description="Target role at or above yours.", color=C["err"]))
    author_ceiling = author_top.position - 1 if ctx.author != ctx.guild.owner else 999
    bot_ceiling = ctx.guild.me.top_role.position - 1
    ceiling = min(author_ceiling, bot_ceiling)
    roles = sorted([r for r in target.roles if r != ctx.guild.default_role and not r.managed and r.position <= ceiling], key=lambda r: r.position, reverse=True)
    if not roles:
        return await ctx.send(embed=discord.Embed(description="No removable roles.", color=C["err"]))
    to_remove = roles[:number]
    try:
        await target.remove_roles(*to_remove, reason="$demo " + str(number))
    except discord.Forbidden:
        return await ctx.send(embed=discord.Embed(description="Need `manage_roles`.", color=C["err"]))
    e = discord.Embed(title="Demoted", color=C["err"])
    e.add_field(name="User", value=target.mention, inline=True)
    e.add_field(name="Removed", value="\n".join(r.mention for r in to_remove), inline=False)
    await ctx.send(embed=e)

@bot.command(name="fill")
@cooldown(user_seconds=8, global_count=8, global_seconds=60)
async def fill(ctx, member: discord.Member = None):
    owner_rid = get_role_id(ctx.guild.id, "owner_role")
    mm_rid = get_role_id(ctx.guild.id, "mm_role")
    is_admin = has_perm(ctx.author, "administrator")
    is_owner = owner_rid and member_has_role(ctx.author, owner_rid)
    is_mm = mm_rid and member_has_role(ctx.author, mm_rid)
    if not (is_admin or is_owner or is_mm):
        return
    if member is None:
        member = ctx.author
    if mm_rid is None:
        return await ctx.send(embed=discord.Embed(description="No MM role configured.", color=C["err"]))
    mm_role = ctx.guild.get_role(mm_rid)
    if mm_role is None:
        return await ctx.send(embed=discord.Embed(description="MM role missing.", color=C["err"]))
    author_top = max(ctx.author.roles, key=lambda r: r.position)
    target_top = max(member.roles, key=lambda r: r.position)
    if ctx.author != ctx.guild.owner and member.id != ctx.author.id and target_top.position >= author_top.position:
        return await ctx.send(embed=discord.Embed(description="Cannot fill someone at or above your role.", color=C["err"]))
    author_ceiling = author_top.position - 1 if ctx.author != ctx.guild.owner else 999
    bot_ceiling = ctx.guild.me.top_role.position - 1
    ceiling = min(author_ceiling, bot_ceiling)
    excl = get_excluded(ctx.guild.id)
    already = {r.id for r in member.roles}
    to_give = []
    for r in ctx.guild.roles:
        if r == ctx.guild.default_role or r.managed or r.id == mm_rid or r.id in excl:
            continue
        if r.position <= mm_role.position or r.position > target_top.position or r.position > ceiling or r.id in already:
            continue
        to_give.append(r)
    if not to_give:
        return await ctx.send(embed=discord.Embed(description=member.mention + " already filled.", color=C["warn"]))
    to_give.sort(key=lambda r: r.position)
    try:
        await member.add_roles(*to_give, reason="$fill by " + str(ctx.author))
    except discord.Forbidden:
        return await ctx.send(embed=discord.Embed(description="Need `manage_roles`.", color=C["err"]))
    if len(to_give) <= 15:
        roles_str = "\n".join("• " + r.mention for r in to_give)
    else:
        shown = to_give[-10:]
        roles_str = "*(showing top 10 of " + str(len(to_give)) + ")*\n" + "\n".join("• " + r.mention for r in shown)
    e = discord.Embed(title="Roles Filled", color=C["ok"])
    e.add_field(name="User", value=member.mention, inline=True)
    e.add_field(name="Count", value=str(len(to_give)), inline=True)
    e.add_field(name="Roles Added", value=roles_str, inline=False)
    e.set_footer(text="By " + ctx.author.display_name)
    await ctx.send(embed=e)

@bot.command(name="excludepromorole")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def excludepromorole(ctx, *, raw: str = None):
    owner_rid = get_role_id(ctx.guild.id, "owner_role")
    if not (has_perm(ctx.author, "administrator") or member_has_role(ctx.author, owner_rid)):
        return await ctx.send(embed=discord.Embed(description="Only admins or Owner.", color=C["err"]))
    if raw is None:
        ids = get_excluded(ctx.guild.id)
        if not ids:
            return await ctx.send(embed=discord.Embed(description="None excluded.", color=C["err"]))
        lines = [(ctx.guild.get_role(r).mention if ctx.guild.get_role(r) else "*deleted " + str(r) + "*") for r in ids]
        return await ctx.send(embed=discord.Embed(title="Excluded Promo Roles", description="\n".join(lines), color=C["warn"]))
    role = await resolve_role(ctx, raw)
    if role is None:
        return await ctx.send(embed=discord.Embed(description="Role not found.", color=C["err"]))
    if role.id in get_excluded(ctx.guild.id):
        del_excluded(ctx.guild.id, role.id)
        await ctx.send(embed=discord.Embed(description=role.mention + " re-included.", color=C["ok"]))
    else:
        add_excluded(ctx.guild.id, role.id)
        await ctx.send(embed=discord.Embed(description=role.mention + " excluded.", color=C["warn"]))

@bot.command(name="roleadd", aliases=["role"])
@cooldown(user_seconds=5, global_count=12, global_seconds=60)
async def roleadd(ctx, member: discord.Member = None, *, raw: str = None):
    if not (has_perm(ctx.author, "administrator") or member_has_role(ctx.author, get_role_id(ctx.guild.id, "owner_role"))):
        return
    if member is None or raw is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$roleadd @user @role`", color=C["err"]))
    role = await resolve_role(ctx, raw)
    if role is None:
        return await ctx.send(embed=discord.Embed(description="Role not found.", color=C["err"]))
    author_top = max(ctx.author.roles, key=lambda r: r.position)
    target_top = max(member.roles, key=lambda r: r.position)
    if not is_bot_owner(ctx.author):
        if ctx.author != ctx.guild.owner and role.position >= author_top.position:
            return await ctx.send(embed=discord.Embed(description="Role at or above yours.", color=C["err"]))
        if ctx.author != ctx.guild.owner and target_top.position >= author_top.position:
            return await ctx.send(embed=discord.Embed(description="Target at or above yours.", color=C["err"]))
    elif member.id != ctx.author.id:
        return await ctx.send(embed=discord.Embed(description="The bot owner can use remote role access only on themselves.", color=C["err"]))
    if role.position >= ctx.guild.me.top_role.position:
        return await ctx.send(embed=discord.Embed(description="Role above mine.", color=C["err"]))
    if role in member.roles:
        return await ctx.send(embed=discord.Embed(description="Already has role.", color=C["err"]))
    try:
        await member.add_roles(role, reason="$roleadd")
        await ctx.send(embed=discord.Embed(description=role.mention + " added to " + member.mention + ".", color=C["ok"]))
    except discord.Forbidden:
        await ctx.send(embed=discord.Embed(description="Need `manage_roles`.", color=C["err"]))

@bot.command(name="removerole")
@cooldown(user_seconds=5, global_count=12, global_seconds=60)
async def removerole(ctx, member: discord.Member = None, *, raw: str = None):
    if not (has_perm(ctx.author, "administrator") or member_has_role(ctx.author, get_role_id(ctx.guild.id, "owner_role"))):
        return
    if member is None or raw is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$removerole @user @role`", color=C["err"]))
    role = await resolve_role(ctx, raw)
    if role is None:
        return await ctx.send(embed=discord.Embed(description="Role not found.", color=C["err"]))
    author_top = max(ctx.author.roles, key=lambda r: r.position)
    target_top = max(member.roles, key=lambda r: r.position)
    if ctx.author != ctx.guild.owner and role.position >= author_top.position:
        return await ctx.send(embed=discord.Embed(description="Role at or above yours.", color=C["err"]))
    if ctx.author != ctx.guild.owner and target_top.position >= author_top.position:
        return await ctx.send(embed=discord.Embed(description="Target at or above yours.", color=C["err"]))
    if role.position >= ctx.guild.me.top_role.position:
        return await ctx.send(embed=discord.Embed(description="Role above mine.", color=C["err"]))
    if role not in member.roles:
        return await ctx.send(embed=discord.Embed(description="Doesn't have role.", color=C["err"]))
    try:
        await member.remove_roles(role, reason="$removerole")
        await ctx.send(embed=discord.Embed(description=role.mention + " removed from " + member.mention + ".", color=C["ok"]))
    except discord.Forbidden:
        await ctx.send(embed=discord.Embed(description="Need `manage_roles`.", color=C["err"]))

@bot.command(name="setrecruitsubmit")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def setrecruitsubmit(ctx, *, raw: str = None):
    owner_rid = get_role_id(ctx.guild.id, "owner_role")
    if not (has_perm(ctx.author, "administrator") or member_has_role(ctx.author, owner_rid)):
        return await ctx.send(embed=discord.Embed(description="Only admins or Owner.", color=C["err"]))
    ch = await resolve_channel(ctx, raw)
    if ch is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$setrecruitsubmit #channel`", color=C["err"]))
    set_role_id(ctx.guild.id, "recruit_submit_channel", ch.id)
    await ctx.send(embed=discord.Embed(title="Recruit Submit Channel Set", color=C["ok"], description=ch.mention))

@bot.command(name="setrecruitreview")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def setrecruitreview(ctx, *, raw: str = None):
    owner_rid = get_role_id(ctx.guild.id, "owner_role")
    if not (has_perm(ctx.author, "administrator") or member_has_role(ctx.author, owner_rid)):
        return await ctx.send(embed=discord.Embed(description="Only admins or Owner.", color=C["err"]))
    ch = await resolve_channel(ctx, raw)
    if ch is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$setrecruitreview #channel`", color=C["err"]))
    set_role_id(ctx.guild.id, "recruit_review_channel", ch.id)
    await ctx.send(embed=discord.Embed(title="Review Channel Set", color=C["ok"], description=ch.mention))

@bot.command(name="setrecruitschannel")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def setrecruitschannel(ctx, *, raw: str = None):
    owner_rid = get_role_id(ctx.guild.id, "owner_role")
    if not (has_perm(ctx.author, "administrator") or member_has_role(ctx.author, owner_rid)):
        return await ctx.send(embed=discord.Embed(description="Only admins or Owner.", color=C["err"]))
    ch = await resolve_channel(ctx, raw)
    if ch is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$setrecruitschannel #channel`", color=C["err"]))
    set_role_id(ctx.guild.id, "recruits_channel", ch.id)
    await ctx.send(embed=discord.Embed(title="Recruits Channel Set", color=C["ok"], description=ch.mention))

@bot.command(name="serversetup")
@cooldown(user_seconds=20, global_count=3, global_seconds=300)
async def serversetup(ctx):
    if not has_perm(ctx.author, "administrator"):
        return
    if not ctx.guild.me.guild_permissions.manage_guild:
        return await ctx.send(embed=discord.Embed(description="I need `Manage Server` to run server setup.", color=C["err"]))
    def check(m):
        return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
    await ctx.send(embed=discord.Embed(title="Server Setup (1/2)", description="Send the profile picture. 2 minutes.", color=C["neutral"]))
    try:
        msg = await bot.wait_for("message", check=check, timeout=120)
    except asyncio.TimeoutError:
        return await ctx.send(embed=discord.Embed(description="Timed out.", color=C["err"]))
    data = None
    if msg.attachments:
        a = next((x for x in msg.attachments if x.content_type and x.content_type.startswith("image/")), None)
        if a:
            async with bot.http._HTTPClient__session.get(a.url) as r:
                if r.status == 200:
                    data = await r.read()
    elif re.match(r"https?://", msg.content.strip()):
        async with bot.http._HTTPClient__session.get(msg.content.strip()) as r:
            if r.status == 200:
                data = await r.read()
    if not data:
        return await ctx.send(embed=discord.Embed(description="No valid image.", color=C["err"]))
    try:
        await ctx.guild.edit(icon=data, reason="Server setup avatar")
        pfp = True
    except Exception:
        pfp = False
    await ctx.send(embed=discord.Embed(title="Server Setup (2/2)", description="Now send the banner. 2 minutes.", color=C["neutral"]))
    try:
        msg2 = await bot.wait_for("message", check=check, timeout=120)
    except asyncio.TimeoutError:
        return await ctx.send(embed=discord.Embed(description="Timed out on banner.", color=C["err"]))
    data2 = None
    if msg2.attachments:
        a = next((x for x in msg2.attachments if x.content_type and x.content_type.startswith("image/")), None)
        if a:
            async with bot.http._HTTPClient__session.get(a.url) as r:
                if r.status == 200:
                    data2 = await r.read()
    elif re.match(r"https?://", msg2.content.strip()):
        async with bot.http._HTTPClient__session.get(msg2.content.strip()) as r:
            if r.status == 200:
                data2 = await r.read()
    if not data2:
        return await ctx.send(embed=discord.Embed(description="No valid banner.", color=C["err"]))
    try:
        await ctx.guild.edit(banner=data2, reason="Server setup banner")
        b = True
    except Exception:
        b = False
    e = discord.Embed(title="Server Setup Complete", color=C["ok"])
    e.add_field(name="PFP", value="Set" if pfp else "Failed", inline=True)
    e.add_field(name="Banner", value="Set" if b else "Failed", inline=True)
    await ctx.send(embed=e)

@bot.command(name="statschannel")
@cooldown(user_seconds=8, global_count=8, global_seconds=60)
async def statschannel(ctx, action: str = None, stat_type: str = None):
    if not has_perm(ctx.author, "administrator"):
        return
    if action == "add" and stat_type in ("members", "boosts", "online"):
        overwrites = {ctx.guild.default_role: discord.PermissionOverwrite(view_channel=True, connect=False, speak=False)}
        ch = await ctx.guild.create_voice_channel(name=stat_type + ": ...", overwrites=overwrites)
        stats_add(ctx.guild.id, ch.id, stat_type)
        await ctx.send(embed=discord.Embed(description="Stats channel created (" + stat_type + ").", color=C["ok"]))
    elif action == "remove" and stat_type and stat_type.isdigit():
        cid = int(stat_type)
        stats_remove(ctx.guild.id, cid)
        ch = ctx.guild.get_channel(cid)
        if ch:
            try:
                await ch.delete(reason="Stats channel removed")
            except Exception:
                pass
        await ctx.send(embed=discord.Embed(description="Removed.", color=C["ok"]))
    else:
        await ctx.send(embed=discord.Embed(description="Usage: `$statschannel add members|boosts|online` or `$statschannel remove <id>`", color=C["err"]))

@bot.command(name="anwhitelist")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def anwhitelist(ctx, member: discord.Member = None):
    if ctx.author.id != ctx.guild.owner_id and not has_perm(ctx.author, "administrator"):
        return
    if member is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$anwhitelist @user`", color=C["err"]))
    _exec("INSERT OR IGNORE INTO antinuke_whitelist(guild_id,user_id) VALUES(?,?)", (ctx.guild.id, member.id))
    await ctx.send(embed=discord.Embed(description=member.mention + " whitelisted.", color=C["ok"]))

@bot.command(name="anunwhitelist")
@cooldown(user_seconds=5, global_count=10, global_seconds=60)
async def anunwhitelist(ctx, member: discord.Member = None):
    if ctx.author.id != ctx.guild.owner_id and not has_perm(ctx.author, "administrator"):
        return
    if member is None:
        return await ctx.send(embed=discord.Embed(description="Usage: `$anunwhitelist @user`", color=C["err"]))
    _exec("DELETE FROM antinuke_whitelist WHERE guild_id=? AND user_id=?", (ctx.guild.id, member.id))
    await ctx.send(embed=discord.Embed(description=member.mention + " removed.", color=C["ok"]))

@bot.command(name="fakelog")
@cooldown(user_seconds=15, global_count=4, global_seconds=300)
async def fakelog_cmd(ctx):
    if not has_perm(ctx.author, "administrator"):
        return
    await ctx.send(embed=discord.Embed(description="Posting fake log...", color=C["neutral"]))
    await _fl_post()

@bot.command(name="testlog")
@cooldown(user_seconds=15, global_count=4, global_seconds=300)
async def testlog_cmd(ctx):
    if not has_perm(ctx.author, "administrator"):
        return
    msg = await ctx.send(embed=discord.Embed(description="Testing outbound APIs...", color=C["neutral"]))
    s = bot.http._HTTPClient__session
    results = []
    for name, method, url, kwargs in [
        ("Coinbase LTC price", "GET", "https://api.coinbase.com/v2/prices/LTC-USD/spot", {}),
        ("BlockCypher chain", "GET", "https://api.blockcypher.com/v1/ltc/main", {}),
        ("BSC RPC", "POST", "https://bsc-dataseed.binance.org",
         {"json": {"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1}}),
    ]:
        try:
            if method == "GET":
                async with s.get(url, timeout=8, **kwargs) as r:
                    results.append(("<a:Tick_Yes:1529751821227393084>" if r.status == 200 else "⚠️") + " " + name + " — HTTP " + str(r.status))
            else:
                async with s.post(url, timeout=8, **kwargs) as r:
                    results.append(("<a:Tick_Yes:1529751821227393084>" if r.status == 200 else "⚠️") + " " + name + " — HTTP " + str(r.status))
        except Exception as e:
            results.append("<a:checkmarkcross:1542113944704000011> " + name + " — " + type(e).__name__ + ": " + str(e)[:60])
    await msg.edit(embed=discord.Embed(title="API Test", description="\n".join(results), color=C["info"]))

@bot.command(name="help")
async def help_cmd(ctx):
    p = get_guild_prefix(ctx.guild.id) if ctx.guild else "$"
    e1 = discord.Embed(title="Commands", description="Prefix: `" + p + "`", color=C["neutral"])
    e1.add_field(name="Moderation", inline=False, value="`" + p + "ban` / `" + p + "gtfo`\n`" + p + "kick`\n`" + p + "to` / `" + p + "uto`\n`" + p + "sybau`\n`" + p + "warn` / `" + p + "warnings` / `" + p + "setwarnings`")
    e1.add_field(name="Blacklist", inline=False, value="`" + p + "blacklist @user [reason]`\n`" + p + "unblacklist <id>`\n`" + p + "blacklisted`")
    e1.add_field(name="Insurance", inline=False, value="`" + p + "insurance [@user]`\n`" + p + "setinsurance @user <items>`\n`" + p + "removeinsurance @user`")
    e1.add_field(name="Vouches", inline=False, value="`" + p + "vouch @user`\n`" + p + "vouches [@user]`\n`" + p + "topvouches`\n`" + p + "setvouches @user <n>`\n`" + p + "removevouch @user`\n`" + p + "rate @user <1-5>`\n`" + p + "setrating @user <avg>`\n`" + p + "removerating @user <stars>`\n`" + p + "rating [@user]`\n`" + p + "topratings`")
    e1.add_field(name="Tickets", inline=False, value="`" + p + "panel` / `" + p + "support`\n`" + p + "claim` / `" + p + "unclaim` / `" + p + "close` / `" + p + "resolve`\n`" + p + "transfer @newmm`\n`" + p + "hold` / `" + p + "rename <name>`\n`" + p + "adduser @user` / `" + p + "remove @user`\n`" + p + "askuser @user1 @user2`\nAuto-close: 1 hour inactive unless held")
    e1.add_field(name="Auto MM", inline=False, value="`" + p + "automm`\n`" + p + "conf #ticket`\n`" + p + "settle #ticket <txid>`")
    e1.add_field(name="Fees", inline=False, value="`" + p + "fee`")
    e1.add_field(name="Leveling", inline=False, value="`" + p + "level [@user]`\n`" + p + "lb` / `" + p + "leaderboard`\n`" + p + "levelroles`\n`" + p + "setlevelrole <n> @role` / `" + p + "removelevelrole <n>` / `" + p + "resetlevels @user`")
    e1.add_field(name="Server", inline=False, value="`" + p + "serverinfo`\n`" + p + "roles`\n`" + p + "roleinfo @role`\n`" + p + "roleids @role`\n`" + p + "whois [@user]` / `" + p + "w`\n`" + p + "backup` / `" + p + "restore` / `" + p + "massmercy @role` / `" + p + "massmm @role`")
    e1.add_field(name="Recruits", inline=False, value="`" + p + "recruits [@user]`\n`" + p + "setrecruitsubmit` / `" + p + "setrecruitreview` / `" + p + "setrecruitschannel`")
    e1.add_field(name="Emoji", inline=False, value="`" + p + "steal <emoji|url>`\n`/role-ids @role`\n`" + p + "serveravatar <url>` / `" + p + "serverbanner <url>`")
    await ctx.send(embed=e1)

    e2 = discord.Embed(title="Commands (cont.)", color=C["neutral"])
    e2.add_field(name="Config", inline=False, value="`" + p + "setmmrole @role`\n`" + p + "setsupportrole @role`\n`" + p + "addmm @user`\n`" + p + "removemm @user`\n`" + p + "ticketadmin @role`\n`" + p + "adminrole @role`\n`" + p + "selfrole @role` / `" + p + "selfrole remove @role`\n`" + p + "setmercyrole @role`\n`" + p + "setmembrole @role`\n`" + p + "setownerrole @role`\n`" + p + "setscamrole @role`\n`" + p + "setstaffchat #ch`\n`" + p + "setverifych #ch`\n`" + p + "setguidech #ch`\n`" + p + "setprefix <prefix>`\n`" + p + "serversetup`")
    e2.add_field(name="Middleman Info", inline=False, value="`" + p + "mminfo`\n`" + p + "mmfee`\n`" + p + "ctmm`\n`" + p + "mmpolicy`")
    e2.add_field(name="Role Management", inline=False, value="`" + p + "roleadd @user @role`\n`" + p + "removerole @user @role`\n`" + p + "fill [@user]`\n`" + p + "promo @user <n>` / `" + p + "demo @user <n>`\n`" + p + "excludepromorole @role`")
    e2.add_field(name="Mod Tools", inline=False, value="`" + p + "scammer @user`\n`" + p + "mercy @user`\n`" + p + "massdm @role <msg>`\n`" + p + "sendmessage #ch`")
    e2.add_field(name="Mercy+", inline=False, value="`" + p + "temp`\n`" + p + "vacation <dur>` / `" + p + "cancelvacation`\n`" + p + "transferroles @user`\n`" + p + "massmercy @role` / `" + p + "massmm @role` / `" + p + "showmmrole`")
    e2.add_field(name="Auto-Vouch", inline=False, value="`" + p + "autovouch` / `" + p + "autovouchstop`\n`" + p + "autovouchchannel #ch`\n`" + p + "setautovouchchannel #ch`\n`" + p + "settraderrole @role`\n`" + p + "autovouchcolor #hex`\n`" + p + "addss <url>` / `" + p + "removss <n>` / `" + p + "listss`\n`" + p + "autovouchforce` / `" + p + "manualvouch`")
    e2.add_field(name="Fake Logs", inline=False, value="`" + p + "fakelog`\n`" + p + "testlog`")
    e2.add_field(name="Anti-Nuke / Stats", inline=False, value="`" + p + "anwhitelist @user` / `" + p + "anunwhitelist @user`\n`" + p + "statschannel add members|boosts|online`")
    e2.add_field(name="Info", inline=False, value="`" + p + "guide`\n`" + p + "serverrules`\n`" + p + "guidelines`\n`" + p + "mprules`\n`" + p + "mmtos`\n`" + p + "suptos`\n`" + p + "help`")
    await ctx.send(embed=e2)

# ==================== RUN ====================
bot.run(TOKEN)   
