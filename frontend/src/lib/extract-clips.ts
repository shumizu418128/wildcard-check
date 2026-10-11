import {
	decodeFallbackBytes,
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

const monoFromBuffer = (buffer: AudioBuffer, frames: number) => {
	const channels = buffer.numberOfChannels
	const mono = new Float32Array(frames)
	for (let index = 0; index < frames; index += 1) {
		let sum = 0
		for (let channel = 0; channel < channels; channel += 1) {
			sum += buffer.getChannelData(channel)[index] ?? 0
		}
		mono[index] = sum / channels
	}
	return mono
}

const wavFromSamples = (samples: Float32Array, fromRate: number, seconds: number) => {
	const resampled = resampleMono(samples, fromRate, wavSampleRate)
	const limit = wavSampleRate * seconds
	return encodeWav(resampled.subarray(0, limit), wavSampleRate)
}

const recordIntroWav = async (video: HTMLVideoElement, seconds: number) => {
	const context = new AudioContext()
	await context.resume()
	const inputRate = context.sampleRate
	const source = context.createMediaElementSource(video)
	const processor = context.createScriptProcessor(4096, 2, 1)
	const silent = context.createGain()
	silent.gain.value = 0
	const chunks: Float32Array[] = []
	let recording = true
	processor.onaudioprocess = (event) => {
		if (!recording) return
		const left = event.inputBuffer.getChannelData(0)
		const right =
			event.inputBuffer.numberOfChannels > 1 ? event.inputBuffer.getChannelData(1) : left
		const mono = new Float32Array(left.length)
		for (let index = 0; index < left.length; index += 1) {
			mono[index] = ((left[index] ?? 0) + (right[index] ?? 0)) / 2
		}
		chunks.push(mono)
	}
	source.connect(processor)
	processor.connect(silent)
	silent.connect(context.destination)
	try {
		video.muted = false
		video.volume = 0
		await seekVideo(video, 0)
		await video.play()
		await new Promise<void>((resolve, reject) => {
			const stop = () => {
				window.clearInterval(timer)
				window.clearTimeout(limit)
				video.removeEventListener('ended', stop)
				video.removeEventListener('error', onError)
				resolve()
			}
			const onError = () => {
				window.clearInterval(timer)
				window.clearTimeout(limit)
				reject(new Error('video'))
			}
			const timer = window.setInterval(() => {
				if (video.ended || video.currentTime >= seconds) stop()
			}, 100)
			const limit = window.setTimeout(stop, (seconds + 8) * 1000)
			video.addEventListener('ended', stop, { once: true })
			video.addEventListener('error', onError, { once: true })
		})
	} finally {
		recording = false
		video.pause()
		processor.disconnect()
		source.disconnect()
		silent.disconnect()
		await context.close()
	}
	const merged = mergeFloats(chunks)
	if (merged.length === 0) throw new Error('audio')
	return wavFromSamples(merged, inputRate, seconds)
}

const decodeIntroWav = async (file: File, seconds: number) => {
	const context = new AudioContext()
	try {
		await context.resume()
		const decoded = await context.decodeAudioData(await file.arrayBuffer())
		const frames = Math.min(decoded.length, Math.floor(seconds * decoded.sampleRate))
		if (frames === 0) throw new Error('audio')
		return wavFromSamples(monoFromBuffer(decoded, frames), decoded.sampleRate, seconds)
	} finally {
		await context.close()
	}
}

const introWav = async (file: File, video: HTMLVideoElement) => {
	try {
		return await recordIntroWav(video, introAudioSeconds)
	} catch (error) {
		// MediaElementSource が無音になるブラウザがある。大きなファイルは全読みしない。
		if (file.size > decodeFallbackBytes) throw error
		return decodeIntroWav(file, introAudioSeconds)
	}
}

export const extractReviewClips = async (file: File): Promise<ReviewClipFiles> => {
	const url = URL.createObjectURL(file)
	let video: HTMLVideoElement | null = null
	try {
		const opened = await openVideo(url)
		video = opened
		await seekVideo(opened, introFrameSeconds)
		const introFrame = await jpegFromVideo(opened)
		await seekVideo(opened, routineFrameSeconds)
		const routineFrame = await jpegFromVideo(opened)
		const introAudio = await introWav(file, opened)
		return { introAudio, introFrame, routineFrame }
	} finally {
		if (video) closeVideo(video)
		URL.revokeObjectURL(url)
	}
}
