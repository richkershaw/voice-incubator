"""The tone once a wake word has been checked (tones.WAKE, settings.json
``wake_chime``): the setting, its area's own, and its place in the call's one
stream."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest
from adapt_ctc.config import ConfigError

from voice_incubator import areas, server, tones
from voice_incubator.server import PRESS_TO_TALK
from voice_incubator.protocol import Message


class Recorder:
    """Stands in for the app: records what Cues sends."""

    def __init__(self):
        self.options = SimpleNamespace(drain_timeout=5.0)
        self.sent: list[Message] = []

    async def _send(self, session, msg_type, payload=b""):
        self.sent.append(msg_type)


def _session():
    return SimpleNamespace(drained=asyncio.Event(), output_rate=server.SAMPLE_RATE)


def test_off_unless_turned_on_and_an_area_may_have_its_own():
    settings: dict = {}
    assert areas.whole_wake_chime(settings) is False
    assert areas.effective(settings, "kitchen")["wake_chime"] is False
    settings["wake_chime"] = True
    assert areas.whole_wake_chime(settings) is True
    assert areas.effective(settings, "kitchen")["wake_chime"] is True
    assert areas.put(settings, "kitchen", {"wake_chime": False}, {}, []) == {"wake_chime": False}
    assert areas.effective(settings, "kitchen")["wake_chime"] is False
    assert areas.effective(settings, "office")["wake_chime"] is True  # the whole home's
    with pytest.raises(ConfigError):
        areas.put(settings, "kitchen", {"wake_chime": "yes"}, {}, [])


def test_the_tone_and_the_heard_sound_are_one_stream():
    # The tone opens the call's stream; the sounds and the reply follow it in
    # it, and its one end closes them all.
    async def scenario():
        app, session = Recorder(), _session()
        cues = server.Cues(app, session)
        await cues.play(tones.WAKE)
        await cues.play(b"\x01\x00" * 1600)  # what "heard" would be
        assert app.sent and set(app.sent) == {Message.AUDIO_OUT}
        stopping = asyncio.ensure_future(cues.stop(close=True))
        while Message.AUDIO_OUT_END not in app.sent:
            await asyncio.sleep(0.01)
        session.drained.set()
        await asyncio.wait_for(stopping, 1)
        assert app.sent.count(Message.AUDIO_OUT_END) == 1
        assert app.sent[-1] == Message.AUDIO_OUT_END

    asyncio.run(scenario())


def test_the_tone_is_short():
    # It plays over the start of the command: a fifth of a second or less.
    assert 0 < len(tones.WAKE) <= 0.2 * 32000


class Wake:
    """Stands in for the app: who asks, and what it plays."""

    _wake_chime = server.VoiceIncubatorApp._wake_chime
    _cues = server.VoiceIncubatorApp._cues

    def __init__(self, *, wake_chime: bool = True, sounds: bool = True, night: bool = False):
        self.options = SimpleNamespace(drain_timeout=5.0)
        self.satellite_ = SimpleNamespace(
            settings={"sounds": sounds, "wake_chime": wake_chime, "instrument": None, "pitch": None},
            night=night,
        )
        self.played: list[bytes] = []

    def satellite(self, key):
        return self.satellite_

    async def _send(self, session, msg_type, payload=b""):
        if msg_type == Message.AUDIO_OUT:
            self.played.append(payload)


def played(wake_word: str = "okay_nabu", finished: bool = False, **settings) -> bytes:
    """What the app plays for a call whose wake word it has just checked."""

    async def scenario():
        app = Wake(**settings)
        call = server.Call(preroll_bytes=0, wake_word=wake_word)
        call.finished = finished
        session = SimpleNamespace(
            call=call, satellite="kitchen", drained=asyncio.Event(), output_rate=server.SAMPLE_RATE
        )
        await app._wake_chime(session, call)
        return b"".join(app.played)

    return asyncio.run(scenario())


def test_what_says_the_wake_word_was_heard():
    assert played() == tones.WAKE
    # Not for the button: it is not a wake word.
    assert played(PRESS_TO_TALK) == b""
    # Turned off, no sounds at all, or at night.
    assert played(wake_chime=False) == b""
    assert played(sounds=False) == b""
    assert played(night=True) == b""
    # The command ended first: the "heard" sound says so instead.
    assert played(finished=True) == b""
    # A call that is no longer this satellite's.
    async def gone():
        app = Wake()
        call = server.Call(preroll_bytes=0, wake_word="okay_nabu")
        session = SimpleNamespace(
            call=None, satellite="kitchen", drained=asyncio.Event(), output_rate=server.SAMPLE_RATE
        )
        await app._wake_chime(session, call)
        return b"".join(app.played)

    assert asyncio.run(gone()) == b""
