import { maxFrameBytes } from '$lib/clip-times'

const maxFrameEdge = 1280

const even = (value: number) => Math.max(2, Math.round(value / 2) * 2)

export const openVideo = (url: string) =>
	new Promise<HTMLVideoElement>((resolve, reject) => {
		const video = document.createElement('video')
		video.preload = 'auto'
		video.playsInline = true
		video.muted = true
		video.src = url
		video.style.position = 'fixed'
		video.style.width = '8px'
		video.style.height = '8px'
		video.style.opacity = '0'
		video.style.pointerEvents = 'none'
		document.body.append(video)
		const onReady = () => {
			video.removeEventListener('error', onError)
			resolve(video)
		}
		const onError = () => {
			video.removeEventListener('loadedmetadata', onReady)
			video.remove()
			reject(new Error('video'))
		}
		video.addEventListener('loadedmetadata', onReady, { once: true })
		video.addEventListener('error', onError, { once: true })
	})

export const closeVideo = (video: HTMLVideoElement) => {
	video.pause()
	video.removeAttribute('src')
	video.load()
	video.remove()
}

export const seekVideo = (video: HTMLVideoElement, seconds: number) =>
	new Promise<void>((resolve, reject) => {
		const duration = Number.isFinite(video.duration) ? video.duration : seconds
		const target = Math.min(seconds, Math.max(duration - 0.05, 0))
		if (Math.abs(video.currentTime - target) < 0.01) {
			resolve()
			return
		}
		const onSeeked = () => {
			video.removeEventListener('error', onError)
			resolve()
		}
		const onError = () => {
			video.removeEventListener('seeked', onSeeked)
			reject(new Error('video'))
		}
		video.addEventListener('seeked', onSeeked, { once: true })
		video.addEventListener('error', onError, { once: true })
		video.currentTime = target
	})

export const jpegFromVideo = (video: HTMLVideoElement) =>
	new Promise<Blob>((resolve, reject) => {
		const sourceWidth = video.videoWidth
		const sourceHeight = video.videoHeight
		if (sourceWidth === 0 || sourceHeight === 0) {
			reject(new Error('video'))
			return
		}
		const scale = Math.min(1, maxFrameEdge / Math.max(sourceWidth, sourceHeight))
		const canvas = document.createElement('canvas')
		canvas.width = even(sourceWidth * scale)
		canvas.height = even(sourceHeight * scale)
		const context = canvas.getContext('2d')
		if (!context) {
			reject(new Error('canvas'))
			return
		}
		context.drawImage(video, 0, 0, canvas.width, canvas.height)
		const encode = (step: number) => {
			const quality = 0.8 - step * 0.1
			canvas.toBlob(
				(blob) => {
					if (!blob) {
						reject(new Error('jpeg'))
						return
					}
					if (blob.size > maxFrameBytes && step < 3) {
						encode(step + 1)
						return
					}
					if (blob.size > maxFrameBytes) {
						reject(new Error('jpeg'))
						return
					}
					resolve(blob)
				},
				'image/jpeg',
				quality,
			)
		}
		encode(0)
	})

export const blobToDataUrl = (blob: Blob) =>
	new Promise<string>((resolve, reject) => {
		const reader = new FileReader()
		reader.addEventListener('load', () => {
			if (typeof reader.result === 'string') resolve(reader.result)
			else reject(new Error('jpeg'))
		})
		reader.addEventListener('error', () => reject(new Error('jpeg')))
		reader.readAsDataURL(blob)
	})
