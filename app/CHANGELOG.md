# Changelog

Fork builds are numbered upstream's release with a build number after it:
`0.3.5.42`. The number before the build is upstream's release; the build
number only rises, so Home Assistant sees each as a newer version. The stamp
commit's message names the commit.

## 0.3.5

- **It brings upstream 0.3.5**: each person's own conversation
  agent and answer voice (contributed from this fork), announcements that
  need an area, a floor or a whole-house word, replies at 48 kHz on firmware
  that takes them, the chosen text-to-speech voice on satellites without a
  media player, satellites dialled at their last address after a restart,
  and Settings as a page of its own with the app's version shown.
- **The optional wake-word chime is still here**, which this fork has and
  upstream doesn't yet: a short tone once the wake word is checked, in
  Settings > Responses or for one area on its page. Now with a choice of
  tone (a note, a ding-dong, dong-ding, stairs, or a ping), of loudness (as
  the call's own sounds, louder, or loudest), a small room's reflections
  after each tone, and a Try button.

## 0.3.3

- **The app calls itself Voice Incubator (richkershaw's fork)**, in the app
  store, the repository list and its sidebar panel, so it is told apart from
  upstream's app when both repositories are added. Its slug is unchanged
  (`voice_incubator`), so its data and configuration stay where they are.
- **An optional chime when the wake word is heard.** Turn it on in Settings >
  Responses, or for one area on its page: a short tone once the app has
  checked the wake word, for a satellite whose ring isn't in sight. A false
  wake word stays silent, the button stays silent, and night mode keeps it
  quiet with the rest of the sounds.
- **It brings upstream 0.3.1, 0.3.2 and 0.3.3's fixes**: Silero VAD 3.4.1 for
  CPUs without AVX2 (enrolling and ending a command no longer crash on older
  x86 boxes), alarm times as speech-to-text writes them ("5.50", "5-0-1",
  "7 a.m."), Home Assistant devices with three-part identifiers, free text
  keeping its last words, small boxes no longer running out of memory
  building the home's sentences, enrolling surviving a cut-off audio frame,
  satellites staying connected when a weak Wi-Fi link loses their mDNS
  record, Home Assistant starting after the app being waited for, the app as
  its own conversation agent no longer asking itself forever, the integration
  from the Marketplace, a device heard only in its area saying it can only be
  controlled from there, sentence triggers winning over an area's own
  commands as good as them, and English's "change the lights to blue" and
  "what's the time".

## 0.3.2

- **A typed Try goes to the home's conversation agent.** A typed sentence has
  no speaker to identify, so a one-person home is no longer taken to be them
  for the fallback: the trace shows the agent Settings picked, as a real call
  from someone unknown would. Commands typed there still see the only person
  ("add to my list").
- **Test it can take a person's part.** Pick one there and the sentence is
  heard as if their voice were recognized: their own conversation agent, and
  what "my" means. Nobody known, the default, is a guest.

## 0.3.1

- **Each person can have their own conversation agent, and a voice for its
  answers.** On the People page, a person picks an agent -- or keeps the
  home's from Settings -- and the voice its answers are said in. What no
  command, skill or step understood goes to the agent of the person
  speaking. Each agent keeps its own conversation in an area, so two agents
  in one room are never sent each other's conversation id, and a follow-up
  answer goes back to the agent that asked.
- **The People page says when one person and no enrolled voice mean every
  request is theirs**, with a link to enrol them or to add someone else.

## 0.3.0

- **The app's language is picked on its Configuration tab, and it has no
  default.** Updated from 0.2, the app won't start until one is picked.
  German, Spanish, French, Italian, Dutch, Polish, Russian and Ukrainian
  now have English's commands, versions, slots, lists and actions, alarms
  and reminders on the calendar, and two commands said together. The
  language's speech model is downloaded at the first start. Piper's voices
  are the language's, and GLiNER is English only.
- **Wake word training is installed from the Wake words page.** TensorFlow
  is no longer in the image (3.0 GB down to 1.1 GB on amd64), and the
  training kit no longer has to be copied in by hand. Install downloads
  about 1.2 GB on amd64 and 900 MB on aarch64, and takes about 4 GB in the
  data folder. Remove frees it again. Updates keep it, and backups leave it
  out.
- **A training voice that won't download fails the training.** It used to
  wait without saying anything, trying again every 30 s; now the training
  stops after three tries and says why.
- **Wake words are trained with the new libritts_r voice.** It has 904
  speakers where the old one had 2306, with other ids. A saved speaker it
  no longer has speaks with the voice's default.
- **A command said right after the wake word isn't missed.** Silero now
  starts listening on the quiet before the wake word. Started on "okay",
  it scored a plainly said command 0.36, under the 0.5 that starts it,
  and the call ended "no speech was heard".
- **Adding from the library is quick.** The library's sentences are
  embedded in the background after the first build (100 s once on an HA
  Green), so adding 12 commands no longer takes 23 s. The Add buttons say
  "Adding…" until the commands are recognized.
- **The app's logo reads in dark mode too.** The Supervisor shows one logo
  for both themes, and its dark gray wordmark all but disappeared on a dark
  card; it is blue now.

## 0.2.1

- **Wake words are verified on the AEC capture.** The VPE's AGC capture
  sometimes sits about 35 dB down, and near misses ("okay natalie") got
  through on it. The command is still heard on the AGC capture; a call
  without AEC audio is verified as before, and `--wake-capture agc` puts it
  back for every call.
- **The second opinion doesn't overturn a near miss.** A wake word Kaldi
  refused is no longer accepted on the ratio when it sounds more like one of
  37 of "okay nabu"'s confusables ("okay natalie", "okay taboo" with a long
  last vowel) than like it. The call's trace says which.
- **Sentence triggers are known by their sentence.** An automation with no
  description is known to the fallback by its first sentence, each slot by
  its name ("how is the sport game going in city"), not its name: GLiNER
  scored "Game info" 0.27 for "how's the basketball game going in New
  Orleans?", too unsure to run it, and the sentence 0.96. Hints say it the
  same way.

## 0.2.0

- **Voice Labs is Voice Incubator.** As a Home Assistant app it is a new
  one (slug `voice_incubator`): what Voice Labs kept doesn't come along by
  itself. Everything new since Voice Labs is in the source's
  [changelog](https://github.com/OHF-Voice/voice-incubator/blob/v0.2.0/CHANGELOG.md#020).
