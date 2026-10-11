import { ALL_FORMATS, AudioBufferSink, BlobSource, Input } from 'mediabunny'
import {
	introAudioSeconds,
	introFrameSeconds,
	routineFrameSeconds,
	wavSampleRate,
} from '$lib/clip-times'
import { closeVideo, jpegFromVideo, openVideo, seekVideo } from '$lib/video-frame'
import { encodeWav, resampleMono } from '$lib/wav'

export type ReviewClipFiles = {
	introAudio: Blob
	introFrame: Blob
	routineFrame: Blob
}

const mergeFloats = (chunks: Float32Array[]) => {
	const length = chunks.reduce((sum, chunk) => sum + chunk.length, 0)
	const merged = new Float32Array(length)
	let offset = 0
	for (const chunk of chunks) {
		merged.set(chunk, offset)
		offset += chunk.length
	}
	return merged
}

const monoFromBuffer = (buffer: AudioBuffer) => {
	const channels = buffer.numberOfChannels
	const mono = new Float32Array(buffer.length)
	for (let channel = 0; channel < channels; channel += 1) {
		const data = buffer.getChannelData(channel)
		for (let index = 0; index < buffer.length; index += 1) {
			mono[index] += data[index] / channels
		}
	}
	return mono
}

const wavFromSamples = (samples: Float32Array, fromRate: number, seconds: number) => {
	const resampled = resampleMono(samples, fromRate, wavSampleRate)
	const limit = wavSampleRate * seconds
	return encodeWav(resampled.subarray(0, limit), wavSampleRate)
}

/** ファイル全体は読まず、冒頭の音声パケットだけをデコードする。 */
const introWav = async (file: File, seconds: number) => {
	const input = new Input({ source: new BlobSource(file), formats: ALL_FORMATS })
	try {
		const track = await input.getPrimaryAudioTrack()
		if (!track || !(await track.canDecode())) throw new Error('audio')
		const chunks: Float32Array[] = []
		let rate = 0
		for await (const { buffer } of new AudioBufferSink(track).buffers(0, seconds)) {
			rate = buffer.sampleRate
			chunks.push(monoFromBuffer(buffer))
		}
		const merged = mergeFloats(chunks)
		if (merged.length === 0) throw new Error('audio')
		return wavFromSamples(merged, rate, seconds)
	} finally {
		input.dispose()
	}
}

export const extractReviewClips = async (file: File): Promise<ReviewClipFiles> => {
	const introAudio = await introWav(file, introAudioSeconds)
	const url = URL.createObjectURL(file)
	let video: HTMLVideoElement | null = null
	try {
		const opened = await openVideo(url)
		video = opened
		await seekVideo(opened, introFrameSeconds)
		const introFrame = await jpegFromVideo(opened)
		await seekVideo(opened, routineFrameSeconds)
		const routineFrame = await jpegFromVideo(opened)
		return { introAudio, introFrame, routineFrame }
	} finally {
		if (video) closeVideo(video)
		URL.revokeObjectURL(url)
	}
}
