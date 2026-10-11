export const introAudioSeconds = 30
export const introFrameSeconds = 2
export const routineFrameSeconds = 60
export const wavSampleRate = 16000
export const maxFrameBytes = 1024 * 1024
// ストリーム録音が無音のときだけ、このサイズ以下はデコードに切り替える
export const decodeFallbackBytes = 32 * 1024 * 1024
