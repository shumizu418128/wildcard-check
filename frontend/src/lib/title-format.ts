import { isDebugYoutubeUrl, mockDebugTitle } from './debug.ts'

// 画面のタイトル例は catalog.ts がこの年から作る。
export const editionYear = 2026

const categoryPatterns: Record<string, RegExp> = {
	solo: /\bsolo\b/i,
	loopstation: /\bloop[\s-]*station\b/i,
	tag: /\btag[\s-]*team\b/i,
	crew: /\bcrew\b/i,
}

const battleShort = /gbb/i
const battleLong = /grand\s+beatbox\s+battle/i
const wildcardWord = /wildcard/i

const namedEntities: Record<string, string> = {
	amp: '&',
	lt: '<',
	gt: '>',
	quot: '"',
	apos: "'",
	nbsp: '\u00a0',
}

const characterFromCode = (code: number, entity: string) => {
	if (!Number.isInteger(code) || code < 0 || code > 0x10ffff) return entity
	return String.fromCodePoint(code)
}

const unescapeHtml = (value: string) =>
	value.replace(/&(#x[0-9a-f]+|#\d+|[a-z]+);/gi, (entity, body: string) => {
		const token = body.toLowerCase()
		if (token.startsWith('#x')) return characterFromCode(Number.parseInt(token.slice(2), 16), entity)
		if (token.startsWith('#')) return characterFromCode(Number.parseInt(token.slice(1), 10), entity)
		return namedEntities[token] ?? entity
	})

const yearPattern = (year: number) => {
	const short = String(year % 100).padStart(2, '0')
	// 2026 も 26 も通す。126 や 20260 のような別の数には当てない。
	return new RegExp(`(?<!\\d)(?:${year}|${short})(?!\\d)`)
}

export const isYoutubeUrl = (value: string) => {
	let url: URL
	try {
		url = new URL(value.trim())
	} catch {
		return false
	}
	if (url.protocol !== 'http:' && url.protocol !== 'https:') return false
	let host = url.hostname.toLowerCase().replace(/\.+$/, '')
	if (host.startsWith('www.')) host = host.slice(4)
	if (host === 'youtu.be' || host === 'youtube.com' || host === 'youtube-nocookie.com') return true
	return host.endsWith('.youtube.com') || host.endsWith('.youtube-nocookie.com')
}

export const titleMatches = (title: string, category: string, year = editionYear) => {
	const pattern = categoryPatterns[category]
	if (title.trim() === '' || pattern === undefined) return false
	if (!pattern.test(title)) return false
	if (!wildcardWord.test(title)) return false
	if (!battleShort.test(title) && !battleLong.test(title)) return false
	return yearPattern(year).test(title)
}

export const fetchYoutubeTitle = async (url: string, category = '') => {
	if (!isYoutubeUrl(url)) return ''
	if (isDebugYoutubeUrl(url)) return mockDebugTitle(category)
	const query = new URLSearchParams({ url, format: 'json' })
	try {
		const response = await fetch(`https://www.youtube.com/oembed?${query}`, {
			signal: AbortSignal.timeout(5000),
		})
		if (!response.ok) return ''
		const payload: unknown = await response.json()
		if (typeof payload !== 'object' || payload === null || !('title' in payload)) return ''
		const title = payload.title
		if (typeof title !== 'string') return ''
		return unescapeHtml(title).trim()
	} catch {
		return ''
	}
}
