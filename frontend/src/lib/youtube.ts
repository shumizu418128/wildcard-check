const shortsUrlPattern =
	/(?:^|\/\/)(?:[\w.-]+\.)?(?:youtube\.com|youtube-nocookie\.com)\/shorts(?:\/|[?#]|$)/i

const videoIdPattern = /^[A-Za-z0-9_-]{11}$/

const pathMarkers = new Set(['embed', 'shorts', 'live', 'v'])

/** `detail` when the video is private or unlisted. */
export const privateUrlCode = 'private_url'
export const unlistedUrlCode = 'unlisted_url'

export const nonPublicUrlCodes = new Set([privateUrlCode, unlistedUrlCode])

export const isShortsUrl = (value: string) => shortsUrlPattern.test(value.trim())

export const isNonPublicUrlCode = (detail: string) => nonPublicUrlCodes.has(detail)

const isYoutubeHost = (hostname: string) => {
	const host = hostname.toLowerCase().replace(/^www\./, '')
	if (host === 'youtu.be' || host === 'youtube.com' || host === 'youtube-nocookie.com') return true
	if (host === 'm.youtube.com' || host === 'music.youtube.com') return true
	return host.endsWith('.youtube.com') || host.endsWith('.youtube-nocookie.com')
}

export const youtubeVideoId = (value: string) => {
	let url: URL
	try {
		url = new URL(value.trim())
	} catch {
		return ''
	}
	if (!isYoutubeHost(url.hostname)) return ''
	const host = url.hostname.toLowerCase().replace(/^www\./, '')
	if (host === 'youtu.be') {
		const id = url.pathname.split('/').filter(Boolean)[0] ?? ''
		return videoIdPattern.test(id) ? id : ''
	}
	const fromQuery = url.searchParams.get('v') ?? ''
	if (videoIdPattern.test(fromQuery)) return fromQuery
	const parts = url.pathname.split('/').filter(Boolean)
	const markerAt = parts.findIndex((part) => pathMarkers.has(part))
	const id = markerAt >= 0 ? (parts[markerAt + 1] ?? '') : ''
	return videoIdPattern.test(id) ? id : ''
}

export const youtubeEmbedUrl = (value: string, origin = '') => {
	const id = youtubeVideoId(value)
	if (id === '') return ''
	const url = new URL(`https://www.youtube-nocookie.com/embed/${id}`)
	url.searchParams.set('enablejsapi', '1')
	if (origin !== '') url.searchParams.set('origin', origin)
	return url.toString()
}
