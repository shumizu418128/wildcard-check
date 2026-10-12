import { youtubeVideoId } from './youtube.ts'

export const debugShortVideoId = 'SHORT-VIDEO'
export const debugPrivateVideoId = 'PRIVATE-VID'

const fixtureIds = new Set([debugShortVideoId, debugPrivateVideoId])

const categoryWord: Record<string, string> = {
	solo: 'Solo',
	loopstation: 'Loopstation',
	tag: 'Tag Team',
	crew: 'Crew',
}

let debugEnabled = false
let debugResolved = false

export const setDebugEnabled = (value: boolean) => {
	debugEnabled = value
	debugResolved = true
}

export const ensureDebugMode = async () => {
	if (debugResolved) return
	try {
		const response = await fetch('/api/health')
		if (!response.ok) {
			setDebugEnabled(false)
			return
		}
		const payload: unknown = await response.json()
		const enabled =
			typeof payload === 'object' &&
			payload !== null &&
			'debug' in payload &&
			payload.debug === true
		setDebugEnabled(enabled)
	} catch {
		setDebugEnabled(false)
	}
}

export const isDebugYoutubeUrl = (url: string) => {
	if (!debugEnabled) return false
	return fixtureIds.has(youtubeVideoId(url))
}

/** title-format.editionYear と同じ年。循環参照を避けるためここでも持つ。 */
const mockEditionYear = 2026

export const mockDebugTitle = (category: string) => {
	const word = categoryWord[category]
	if (word === undefined) return ''
	const shortYear = String(mockEditionYear % 100).padStart(2, '0')
	return `Debug – GBB${shortYear}: World League ${word} Wildcard`
}
