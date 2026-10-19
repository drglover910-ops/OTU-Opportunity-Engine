# Heart CPU speech — v0.19.12

Owner chose A / Heart. Default read-aloud now uses the private CPU service when configured. Existing device speech remains selectable under Isis’s voice and is used if synthesis fails. Static samples remain examples rather than a claim that every response was already generated. No GPU setting, paid API, account token, writing-model limit or subscription is added.

## Runtime and controls

Build downloads fixed public ONNX/voice assets using scripts/fetch_voice_model.py and verifies pinned SHA256 digests. Model files remain outside source Git. A separate voice_worker.py child process uses CPUExecutionProvider only, one ONNX thread, telemetry disabled, and receives only text plus an opaque output ID. No Gmail, Contra, HF credentials or database objects enter that process. Output/audio and errors never print private text.

Parent CPUVoice accepts at most 280 characters per job, one queued renderer and at most four pending/running jobs; a worker render times out after 45 seconds. Browser splits into <=181-character segments and prefetches at most the next one. A completed segment is generated only once per exact workspace/opportunity/chat and model/voice/text key. Temporary cache is on local disk, not the mounted business database. Age/space cleanup occurs on requests: entries older than 30 minutes are eligible; cache is trimmed below 48 completed records / 16 MiB as requests arrive. Cache is ephemeral and is not a backup or a source of durable business records. No arbitrary filename/path or voice may be supplied to the API.

Play and speed controls do not require new writing-model calls. Speed uses the audio player's preserved-pitch playback rate, not another synthesis. Stop/navigation/microphone interrupt playback and ignore late results. Already queued bounded CPU work may finish; stopping audio is not a promise that every started computation was canceled. Failed jobs do not auto-retry or call a paid provider. A player blocked by Safari autoplay shows Play Heart for a second explicit tap. First audio preparation may take several seconds; this is not a real-time/streaming-latency guarantee.

## Licensing / ownership

Base Kokoro weights and stock Heart voice are licensed technology, not exclusively trained/owned OTU assets: https://huggingface.co/hexgrad/Kokoro-82M . The ONNX and packaged voices are from https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.1 ; checksums are pinned in cpu_voice.py and the build script. kokoro-onnx / ONNX Runtime use MIT licenses. Phonemizer and eSpeak NG are GPL components. Their runtime lives in the separate speech process, with its source shipped, and installed packages retain their license files. Keep copyright/license notices and applicable source obligations when distributing containers or desktop builds. Private hosted operation is not a full corporate distribution/commercial-rights clearance or exclusive voice ownership claim. Review the exact complete runtime and voice chain before customer distribution.

## Validation boundaries

Unit fixtures cover real WAV delivery, scope isolation, serialization, cache reuse, request/voice bounds and no automatic retry after failure. Browser tests use synthetic WAV generation, exercising actual playback, speed, pause/resume, replay, navigation and device fallback. The deployment check separately generates a short non-private script on the actual Space CPU and verifies WAV delivery and identical cache ID on replay. No paid inference or external applications are used. Subjective listening and actual iPad audio/autoplay behavior remain owner checks.
