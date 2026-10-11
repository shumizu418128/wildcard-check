export const resampleMono = (input: Float32Array, fromRate: number, toRate: number) => {
	if (fromRate === toRate || input.length === 0) return input
	const length = Math.max(1, Math.round((input.length * toRate) / fromRate))
	const output = new Float32Array(length)
	const last = input.length - 1
	for (let index = 0; index < length; index += 1) {
		const position = (index * fromRate) / toRate
		const left = Math.min(Math.floor(position), last)
		const right = Math.min(left + 1, last)
		const mix = position - left
		output[index] = input[left] * (1 - mix) + input[right] * mix
	}
	return output
}

export const encodeWav = (samples: Float32Array, sampleRate: number) => {
	const bytes = new ArrayBuffer(44 + samples.length * 2)
	const view = new DataView(bytes)
	const write = (offset: number, text: string) => {
		for (let index = 0; index < text.length; index += 1) {
			view.setUint8(offset + index, text.charCodeAt(index))
		}
	}
	write(0, 'RIFF')
	view.setUint32(4, 36 + samples.length * 2, true)
	write(8, 'WAVE')
	write(12, 'fmt ')
	view.setUint32(16, 16, true)
	view.setUint16(20, 1, true)
	view.setUint16(22, 1, true)
	view.setUint32(24, sampleRate, true)
	view.setUint32(28, sampleRate * 2, true)
	view.setUint16(32, 2, true)
	view.setUint16(34, 16, true)
	write(36, 'data')
	view.setUint32(40, samples.length * 2, true)
	let offset = 44
	for (let index = 0; index < samples.length; index += 1) {
		const sample = Math.max(-1, Math.min(1, samples[index] ?? 0))
		view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true)
		offset += 2
	}
	return new Blob([bytes], { type: 'audio/wav' })
}
