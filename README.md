# Cents — Custom Tonality System for Dorico

Cent-accurate microtonal accidentals for Steinberg Dorico Pro 6. Every accidental is a familiar natural / sharp / flat glyph paired with a small signed cent label (e.g., `Sharp +14` displays C♯ with `+14` above the staff and plays back 14 cents sharp of C♯).

## Requirements

**Dorico Pro 6.0 or later.** This library will not load on Dorico 5, Dorico Elements, or Dorico SE. See the [Compatibility](#compatibility) section below for details.

## Package Contents

- `cents.doricolib` — the tonality system library (597 accidentals, ~1.2 MB)
- `README.md` — this file
- `LICENSE` — MIT license

## Install (Recommended): Library Manager

Library Manager is the primary install path. It scopes the library to a single project, is recoverable on failure, and was the path validated on Dorico Pro 6.2.2 during development.

1. Open the Dorico project where you want to use cent-accurate accidentals.
2. Go to **Library → Library Manager**.
3. In the left pane, click **Import**.
4. Select `cents.doricolib` from this download.
5. Confirm import. The library is now scoped to this project only.
6. Save the project to persist the library reference.

If the import fails, no system files are touched — close Library Manager and try the [DefaultLibraryAdditions path](#install-power-user-defaultlibraryadditions) below, or see [Troubleshooting](#troubleshooting).

## Install (Power User): DefaultLibraryAdditions

> **Warning:** Files dropped into `DefaultLibraryAdditions/` are loaded by Dorico at startup. If Dorico fails to launch after installing here, **remove if Dorico fails to launch** — delete `cents.doricolib` from the folder below and Dorico will recover on the next start. Library Manager (above) is safer because it scopes per-project.

**macOS:**
```
~/Library/Application Support/Steinberg/Dorico 6/DefaultLibraryAdditions/
```

**Windows:**
```
%APPDATA%\Steinberg\Dorico 6\DefaultLibraryAdditions\
```

1. Quit Dorico.
2. Drop `cents.doricolib` into the path for your OS above.
3. Re-launch Dorico. The library loads globally for every project.
4. If Dorico fails to launch, delete the file from this folder and Dorico will recover.

## Your First Cent-Accurate Note

Cent-accurate accidentals will not appear in the panel until the flow is in an open (atonal) key signature. Skipping this step is the #1 silent failure for any custom tonality system in Dorico.

1. **Set the flow to an open key signature.** With the caret active in Write mode, press **Shift+K** to open the key signatures popover, type `open`, and press Enter. (You can also use **Write → Create Key Signature → Open/Atonal**.)
2. **Apply the cents tonality system to the player.** Go to **Setup mode → Players panel**. Click the player you want to write microtonal music for. In the right-hand properties panel, set **Tonality System** to `cents`.
3. **Open the Accidentals panel.** Return to **Write mode**. Open the right-hand panel **Key Signatures, Tonality Systems, and Accidentals**. You should see all 597 accidentals listed.
4. **Search for a cent value.** Type `+14` into the panel search to filter. You should see three matches — `Sharp +14`, `Flat +14`, `Natural +14`.
5. **Apply the accidental.** With a note selected, click `Sharp +14`. The note now displays a sharp glyph with `+14` floating above the staff, and plays back 14 cents sharp of the written pitch.
6. **Verify with a tuner.** Play the note back via HALion or NotePerformer (see [Playback compatibility](#troubleshooting) below). A reference tuner should read 14 cents sharp of the natural pitch (validated to ±1¢ on Dorico Pro 6.2.2 macOS during development).

If the panel is empty, the open key signature step (#1) was skipped — go back and apply Shift+K → "open".

## Naming Convention

Every accidental name follows the pattern `<Base> <signed-cents>`, where the base is one of `Sharp`, `Flat`, or `Natural` and the cents value is signed (always with `+` or `-`).

| Name | Glyph | Cents from natural | Notes |
|------|-------|--------------------|-------|
| `Sharp` | ♯ | +100¢ | zero-deviation; standard sharp |
| `Flat` | ♭ | -100¢ | zero-deviation; standard flat |
| `Natural` | ♮ | 0¢ | zero-deviation; standard natural |
| `Sharp +14` | ♯ + `+14` | +114¢ | sharp 14¢ further sharp |
| `Flat -50` | ♭ + `-50` | -150¢ | flat 50¢ further flat |
| `Natural -7` | `-7` only | -7¢ | natural-base shows cents only |
| `Sharp -50` | ♯ + `-50` | +50¢ | enharmonic equivalent of `Natural +50` |

Search ergonomics validated at the 597-entry scale: `+14` returns 3 matches, `Sharp -` returns 99 matches, `Flat +50` returns 1 match, `Natural` returns 199 matches.

## Troubleshooting

### The Accidentals panel is empty / the cents accidentals don't appear

This is the #1 silent failure. The cents tonality system only displays accidentals when the flow is in an **open (atonal) key signature**. To fix:

1. In Write mode, with the caret active, press **Shift+K**.
2. Type `open` and press Enter.
3. The key signature is now open/atonal, and the 597 accidentals will appear in the panel.

If the panel still shows the standard 12-EDO accidentals only, confirm the player has `cents` set as its Tonality System in Setup mode (see [Your First Cent-Accurate Note](#your-first-cent-accurate-note) step 2).

### Playback is in 12-EDO instead of cent-accurate

Dorico itself plays back at the labeled cent value (validated to ±1¢ in HALion on Dorico Pro 6.2.2). If you hear 12-EDO playback, the cause is almost always the playback instrument:

| Instrument | Microtonal playback | Notes |
|------------|---------------------|-------|
| **HALion** (Dorico's bundled sampler) | Yes — confirmed in Phase 3 validation | Default; recommended |
| **NotePerformer** | Yes — supports per-note pitch bends | Confirmed compatible |
| **Kontakt** | Caveat | Requires per-instrument microtonal support; Kontakt's host-pitch-bend MIDI semantics vary by library. Test before relying on. |
| **SWAM** instruments | Caveat | Some SWAM instruments respond to per-note pitch deviations, others quantize to 12-EDO. Test before relying on. |
| **Falcon** (UVI) | Caveat | Microtonal support is patch-dependent. Test before relying on. |

If your VST quantizes to 12-EDO regardless of Dorico's pitch instruction, that is a VST limit, not a library limit. Switch to HALion or NotePerformer for verified cent-accurate output.

### Cent labels render in the wrong font / look weird

Cent labels use the `font.defaulttext` font style, which inherits from your project's default text font. If you have overridden `font.defaulttext` to a non-monospaced or unusual font, cent labels (e.g., `+14`) may render with poor kerning or unexpected weight. To fix, either revert the project default text font or override `font.defaulttext` to a clean sans-serif (Academico Bold or the Dorico default).

### Re-importing the library duplicated entries / I want a clean install

Re-imports do not duplicate. Every accidental's `entityID` is derived deterministically (`uuid5(PROJECT_NAMESPACE, key)`), so a re-import of the same `cents.doricolib` updates existing entries in place rather than appending duplicates. If you want a clean state, remove the library via Library Manager and re-import.

## Compatibility

| Dorico Edition | Will the file load? | Notes |
|----------------|---------------------|-------|
| Dorico Pro 6.0–6.2.x | **Yes** (target) | Validated on Dorico Pro 6.2.2 macOS |
| Dorico Pro 5.x | **No** | Library format changed between Dorico 5 and 6 |
| Dorico Pro 4.x and below | **No** | Older library format |
| Dorico Elements 6.x | **Partial** | Library import may succeed, but tonality-system editing requires Pro |
| Dorico SE 6.x | **No** | SE lacks Library Manager and tonality-system support |

This library is built against `fileVersion 1.1450` (Dorico Pro 6.x). It will not be back-ported to Dorico 5.

## License

MIT License. See [LICENSE](LICENSE) for the full text.

Copyright (c) 2026 Taylor Brook.
