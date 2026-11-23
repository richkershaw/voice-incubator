"""The tone once a wake word has been checked (tones.wake(), settings.json
``wake_chime`` and its sound and loudness): the settings, an area's own, the
tones themselves, and the chime's place in the call's one stream."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import numpy as np
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


def test_its_sound_and_loudness_the_whole_home_s_and_an_area_s_own():
    settings: dict = {}
    # A short note, as loud as the call's sounds, unless another.
    assert areas.whole_wake_chime_sound(settings) == "note"
    assert areas.whole_wake_chime_level(settings) == "normal"
    assert areas.effective(settings, "kitchen")["wake_chime_sound"] == "note"
    assert areas.effective(settings, "kitchen")["wake_chime_level"] == "normal"
    settings["wake_chime_sound"] = "ping"
    settings["wake_chime_level"] = "loudest"
    assert areas.whole_wake_chime_sound(settings) == "ping"
    assert areas.effective(settings, "kitchen")["wake_chime_sound"] == "ping"
    assert areas.effective(settings, "kitchen")["wake_chime_level"] == "loudest"
    # An area's own, from its page: the whole home's for the rest.
    own = areas.put(settings, "kitchen", {"wake_chime_sound": "ding_dong", "wake_chime_level": "loud"}, {}, [])
    assert (own["wake_chime_sound"], own["wake_chime_level"]) == ("ding_dong", "loud")
    assert areas.effective(settings, "kitchen")["wake_chime_sound"] == "ding_dong"
    assert areas.effective(settings, "kitchen")["wake_chime_level"] == "loud"
    assert areas.effective(settings, "office")["wake_chime_sound"] == "ping"  # the whole home's
    assert areas.effective(settings, "office")["wake_chime_level"] == "loudest"
    # Back to the whole home's.
    areas.put(settings, "kitchen", {"wake_chime_sound": None, "wake_chime_level": None}, {}, [])
    assert areas.effective(settings, "kitchen")["wake_chime_sound"] == "ping"
    for bad in ({"wake_chime_sound": "gong"}, {"wake_chime_level": "loudestest"}):
        with pytest.raises(ConfigError):
            areas.put(settings, "kitchen", bad, {}, [])


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


def loudness(pcm: bytes) -> float:
    """Where it sounds, as instruments.leveled measures it: dB of full scale."""
    x = np.frombuffer(pcm, dtype="<i2").astype(float) / 32767
    sounding = x[np.abs(x) > 0.003]
    return 20 * np.log10(np.sqrt(np.mean(sounding**2)))


@pytest.mark.parametrize("sound", sorted(tones.WAKE_NOTES))
def test_each_tone_is_short(sound):
    # It plays over the start of the command: a quarter of a second or less.
    for level in tones.WAKE_LEVELS:
        assert 0 < len(tones.wake(sound, level)) <= 0.25 * 32000


@pytest.mark.parametrize("sound", sorted(tones.WAKE_NOTES))
def test_each_level_is_as_loud_as_it_says(sound):
    def peak(pcm: bytes) -> float:
        return abs(np.frombuffer(pcm, dtype="<i2")).max() / 32767

    normal = tones.wake(sound, "normal")
    loud = tones.wake(sound, "loud")
    loudest = tones.wake(sound, "loudest")
    # Within a dB of the level it names: the room and the 16-bit samples
    # move what is measured a little.
    assert -19.8 <= loudness(normal) <= -18.2  # as the call's sounds
    assert -15.8 <= loudness(loud) <= -14.2  # about a timer's ring
    assert -12.8 <= loudness(loudest) <= -11.2
    assert loudness(normal) < loudness(loud) < loudness(loudest)
    assert peak(loud) <= 0.9 and peak(loudest) <= 0.9 and peak(normal) <= 0.7
    assert peak(loud) < peak(loudest)


def test_the_note_has_a_short_room_after_it():
    # The room follows the note, quieter than it, and has died away by the
    # chime's quarter of a second: the command is heard from the same speaker.
    x = np.frombuffer(tones.wake("note"), dtype="<i2").astype(float) / 32767
    note = np.sqrt(np.mean(x[int(0.02 * 16000) : int(0.14 * 16000)] ** 2))
    room = np.sqrt(np.mean(x[int(0.18 * 16000) :] ** 2))
    assert 0.002 < room < 0.2 * note
    assert abs(x[-1]) < 0.002


def test_a_tone_or_level_it_does_not_know_is_the_default():
    assert tones.wake("gong", "normal") == tones.WAKE
    assert tones.wake("note", "quietest") == tones.WAKE


class Wake:
    """Stands in for the app: who asks, and what it plays."""

    _wake_chime = server.VoiceIncubatorApp._wake_chime
    _cues = server.VoiceIncubatorApp._cues

    def __init__(self, *, wake_chime: bool = True, sounds: bool = True, night: bool = False,
                 wake_chime_sound: str = "note", wake_chime_level: str = "normal"):
        self.options = SimpleNamespace(drain_timeout=5.0)
        self.satellite_ = SimpleNamespace(
            settings={
                "sounds": sounds, "wake_chime": wake_chime, "instrument": None, "pitch": None,
                "wake_chime_sound": wake_chime_sound, "wake_chime_level": wake_chime_level,
            },
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
    # The area's or the home's own tone, and how loud.
    assert played(wake_chime_sound="ping", wake_chime_level="loudest") == tones.wake("ping", "loudest")
    assert played(wake_chime_sound="ding_dong", wake_chime_level="loud") == tones.wake("ding_dong", "loud")
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
