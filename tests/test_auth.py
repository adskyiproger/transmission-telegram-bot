from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from lib import auth


def make_update(user_id: int):
    user = SimpleNamespace(id=user_id, language_code="en")
    return SimpleNamespace(effective_user=user)


@pytest.mark.asyncio
async def test_restricted_denies_access_when_admin_is_not_configured(monkeypatch):
    monkeypatch.setattr(auth.bot_config, "get", lambda path, default=None: default)
    context = SimpleNamespace(bot=SimpleNamespace(send_message=AsyncMock()))
    wrapped = AsyncMock()

    await auth.restricted(wrapped)(make_update(42), context)

    wrapped.assert_not_awaited()
    context.bot.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_restricted_allows_configured_admin(monkeypatch):
    values = {"bot.super_user": 42, "bot.allowed_users": []}
    monkeypatch.setattr(
        auth.bot_config, "get", lambda path, default=None: values.get(path, default)
    )
    context = SimpleNamespace(bot=SimpleNamespace(send_message=AsyncMock()))
    wrapped = AsyncMock()

    await auth.restricted(wrapped)(make_update(42), context)

    wrapped.assert_awaited_once()
    context.bot.send_message.assert_not_awaited()
