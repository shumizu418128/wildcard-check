import { encodeWav, resampleMono } from './wav.ts'

const assertOk = (value: boolean, message: string) => {
	if (!value) throw new Error(message)
}

const wav = encodeWav(new Float32Array([0, 0.5, -1]), 16000)
const bytes = new Uint8Array(await wav.arrayBuffer())
assertOk(bytes.length === 44 + 6, 'wav size')
assertOk(String.fromCharCode(...bytes.slice(0, 4)) === 'RIFF', 'riff')
assertOk(String.fromCharCode(...bytes.slice(8, 12)) === 'WAVE', 'wave')
assertOk(wav.type === 'audio/wav', 'type')

const same = resampleMono(new Float32Array([0.25, -0.25]), 16000, 16000)
assertOk(same.length === 2 && same[0] === 0.25, 'same rate')
const stretched = resampleMono(new Float32Array([0, 1]), 8000, 16000)
assertOk(stretched.length === 4, 'double rate')

console.log('wav ok')
