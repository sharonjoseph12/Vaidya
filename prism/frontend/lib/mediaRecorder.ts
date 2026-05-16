/**
 * Utilities for finding the best supported MediaRecorder MIME types.
 */

export function pickAudioMimeType(): string | undefined {
  if (typeof MediaRecorder === "undefined") return undefined;
  const types = ["audio/webm", "audio/mp4", "audio/ogg"];
  for (const t of types) {
    if (MediaRecorder.isTypeSupported(t)) return t;
  }
  return undefined;
}

export function pickVideoMimeType(): string | undefined {
  if (typeof MediaRecorder === "undefined") return undefined;
  const types = [
    "video/webm;codecs=vp9",
    "video/webm;codecs=vp8",
    "video/webm",
    "video/mp4",
  ];
  for (const t of types) {
    if (MediaRecorder.isTypeSupported(t)) return t;
  }
  return undefined;
}
