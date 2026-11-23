# Home Assistant App: Voice Incubator (richkershaw's fork)

![Supports aarch64 Architecture][aarch64-shield] ![Supports amd64 Architecture][amd64-shield]

Home Assistant app for voice satellites with commands you make yourself,
recognized on this machine: [Voice Incubator](https://github.com/richkershaw/voice-incubator),
built from this fork's source by `.github/workflows/app.yml`.

## Installing it from this fork

This repository is its own app repository: add
`https://github.com/richkershaw/voice-incubator` in **Settings > Apps > Install
app > ⋮ > Repositories**, then install **Voice Incubator (richkershaw's fork)**
and start it. It pulls `ghcr.io/richkershaw/voice-incubator-app`, which
`.github/workflows/app.yml` builds from this folder for amd64 and aarch64: by
hand, or on a published release whose tag is the number before the commit.
Make the package public once in the fork's package settings, or Home Assistant
can't pull it.

Its version is upstream's release with a build number after it (`0.3.5.42`),
written to `config.yaml` by `.github/workflows/version.yml` after each push:
Home Assistant offers an update when it is newer, and the build number only
rises. The stamp commit's message names the commit. Build the image once the
"App version" run has finished.

To build it on the Home Assistant machine instead, write the source tarball,
copy this folder into the host's `addons` share as `voice_incubator`, remove
`image:` from `config.yaml` (or Home Assistant pulls the published one), then
check for updates and install it from **Local apps**:

```bash
scripts/app_source.sh app
```

[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
