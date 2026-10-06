import { fetchYoutubeTitle, isYoutubeUrl, titleMatches } from './title-format.ts'

const assertOk = (value: boolean, message: string) => {
	if (!value) throw new Error(message)
}

const titles = () => {
	assertOk(titleMatches('Pepouni – GBB26: World League Solo Wildcard', 'solo'), 'solo short')
	assertOk(titleMatches('Grand Beatbox Battle 2026: World League Solo Wildcard', 'solo'), 'solo long')
	assertOk(titleMatches('Name – GBB26: World League Loopstation Wildcard', 'loopstation'), 'loopstation')
	assertOk(titleMatches('Name – GBB26: World League Loop Station Wildcard', 'loopstation'), 'loop station')
	assertOk(titleMatches('Name – GBB26: World League Tag Team Wildcard', 'tag'), 'tag team')
	assertOk(titleMatches('Name – GBB26: World League Tag-Team Wildcard', 'tag'), 'tag-team')
	assertOk(titleMatches('Name – GBB26: World League Crew Wildcard', 'crew'), 'crew')
	assertOk(titleMatches('name | gbb26 world league solo wildcard', 'solo'), 'case')
	assertOk(!titleMatches('Pepouni – GBB26: World League Solo', 'solo'), 'missing wildcard')
	assertOk(!titleMatches('Pepouni – GBB: World League Solo Wildcard', 'solo'), 'missing year')
	assertOk(!titleMatches('2026 World League Solo Wildcard', 'solo'), 'missing battle')
	assertOk(!titleMatches('Pepouni – GBB25: World League Solo Wildcard', 'solo'), 'old year')
	assertOk(!titleMatches('Pepouni – GBB26: World League Loopstation Wildcard', 'solo'), 'wrong category')
	assertOk(!titleMatches('', 'solo'), 'empty')
	assertOk(!titleMatches("Don't screw this – GBB26 Wildcard", 'crew'), 'screw')
	assertOk(!titleMatches('Name – GBB26: World League Tag Wildcard', 'tag'), 'tag alone')
	assertOk(!titleMatches('Name – GBB26: World League Loop Wildcard', 'loopstation'), 'loop alone')
	assertOk(!titleMatches('Pepouni – GBB126: World League Solo Wildcard', 'solo'), '126')
	assertOk(!titleMatches('Pepouni – GBB20260: World League Solo Wildcard', 'solo'), '20260')
	assertOk(titleMatches('Pepouni – GBB2026: World League Solo Wildcard', 'solo'), '2026')
	assertOk(titleMatches('Name – GBB27: World League Solo Wildcard', 'solo', 2027), '2027 short')
	assertOk(titleMatches('Grand Beatbox Battle 2027: World League Solo Wildcard', 'solo', 2027), '2027 long')
	assertOk(!titleMatches('Name – GBB26: World League Solo Wildcard', 'solo', 2027), '2026 in 2027')
}

const urls = async () => {
	assertOk(!isYoutubeUrl('https://example.com/watch?v=abcdefghijk'), 'example host')
	assertOk(isYoutubeUrl('https://www.youtube.com/watch?v=abcdefghijk'), 'youtube host')
	assertOk(isYoutubeUrl('https://youtu.be/abcdefghijk'), 'youtu.be')
	const original = globalThis.fetch
	try {
		let called = false
		globalThis.fetch = async () => {
			called = true
			return new Response('{}')
		}
		assertOk((await fetchYoutubeTitle('https://example.com/watch?v=abcdefghijk')) === '', 'skip fetch')
		assertOk(!called, 'fetch was called')

		globalThis.fetch = async () =>
			new Response(JSON.stringify({ title: 'Pepouni &amp; Co – GBB26: World League Solo Wildcard' }), {
				status: 200,
			})
		assertOk(
			(await fetchYoutubeTitle('https://www.youtube.com/watch?v=abcdefghijk')) ===
				'Pepouni & Co – GBB26: World League Solo Wildcard',
			'oembed title',
		)

		globalThis.fetch = async () => {
			throw new Error('down')
		}
		assertOk((await fetchYoutubeTitle('https://youtu.be/abcdefghijk')) === '', 'oembed down')

		const { setDebugEnabled } = await import('./debug.ts')
		setDebugEnabled(true)
		called = false
		globalThis.fetch = async () => {
			called = true
			return new Response('{}')
		}
		assertOk(
			(await fetchYoutubeTitle('https://www.youtube.com/watch?v=SHORT-VIDEO', 'solo')) ===
				'Debug – GBB26: World League Solo Wildcard',
			'debug title',
		)
		assertOk(!called, 'debug skipped oembed')
		setDebugEnabled(false)
	} finally {
		globalThis.fetch = original
	}
}

titles()
await urls()
