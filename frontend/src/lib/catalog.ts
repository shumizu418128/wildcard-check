import { editionYear } from '$lib/title-format'
import type { CategoryId, SourceKind } from '$lib/sheet'

export type Verdict =
	| { ok: true; text: string }
	| { ok: false; text: string; outcome: string; detail: string }

export type Pledge = {
	id: string
	title: string
	lead?: string
	lines: Verdict[]
	notes: string[]
}

type FixText = {
	lead: string
	samples: string[]
}

type CatalogItem = {
	id: string
	title: string
	ruleTitle?: string
	lead?: string
	lines: Verdict[]
	notes: string[]
	fix?: FixText
	categories?: readonly CategoryId[]
	sources?: readonly SourceKind[]
	watchesVideo?: boolean
	pledge?: boolean
}

type RuleCopy = {
	title: string
	fix: FixText
	lines?: Verdict[]
	notes?: string[]
}

const yes = (text: string): Verdict => ({ ok: true, text })
const no = (text: string, outcome: string, detail = ''): Verdict => ({
	ok: false,
	text,
	outcome,
	detail,
})

const introQuote =
	'My name is [ARTIST NAME], and this is my [CATEGORY] wildcard for the GBB2026 World League.'

const shortYear = String(editionYear % 100).padStart(2, '0')
const titleForms = [
	`[ARTIST NAME] – GBB${shortYear}: World League [CATEGORY] Wildcard`,
	`Grand Beatbox Battle ${editionYear}: World League [CATEGORY] Wildcard`,
]

const lengthRange: Record<CategoryId, string> = {
	solo: '1:50–2:10',
	tag: '1:50–2:10',
	crew: '2:50–3:10',
	loopstation: '3:00–3:30',
}

const timeLines = (category: CategoryId): Verdict[] => [
	yes(`Within ${lengthRange[category]}, not counting intro and outro.`),
	no(
		'Under or over that range.',
		'Rank drop',
		'One place per full second. Not a disqualification.',
	),
]

const sessionRecordingCategories: CategoryId[] = ['loopstation', 'tag', 'crew']
const sessionRecordingText = 'A screen recording of the session.'

const catalog: CatalogItem[] = [
	{
		id: 'SUB-ONCE',
		title: 'You only get one submission',
		pledge: true,
		lines: [
			yes('Never delete the video after submit.'),
			no(
				'Delete and replace the video.',
				'Not accepted',
				'Only the first video counts. You lose your Wildcard.',
			),
		],
		notes: [],
	},
	{
		id: 'SUB-RAW',
		title: 'Add your raw files with a public link',
		sources: ['youtube'],
		pledge: true,
		fix: {
			lead: "This link didn't open. Use a public link that doesn't ask for access.",
			samples: [],
		},
		lines: [
			yes('Raw audio on a public link.'),
			yes('Raw video with camera audio on a public link.'),
			no('A link that asks for access.', 'Not accepted'),
			no('A link that expires.', 'Not accepted'),
		],
		notes: ['Keep the link until 2026-09-24.'],
	},
	{
		id: 'ADMIN-AGE',
		title: 'Age restriction',
		pledge: true,
		lines: [
			yes('Age 16 or older at the event.'),
			yes('Under 18 and you win: a parent comes with you.'),
			no('Under 16.', "Can't enter"),
			no(
				'Under 18, you win, and no parent comes.',
				'Disqualified',
				'The next eligible wildcard takes the spot.',
			),
		],
		notes: ["The organizer won't cover the guardian's cost."],
	},
	{
		id: 'ADMIN-CALL',
		title: 'Video call if you win',
		lead: 'If you win, join the official video call. The email names the window.',
		pledge: true,
		lines: [
			yes('You join the call yourself.'),
			yes('If a sound engineer worked on your wildcard, they must join this call too.'),
			no('Miss it with under 24 hours notice.', 'Disqualified', 'No exceptions.'),
			no('More than 10 minutes late.', 'Disqualified', 'No exceptions.'),
			no('Someone else joins for you.', 'Disqualified', 'No exceptions.'),
		],
		notes: [],
	},
	{
		id: 'SYNC-LIVE',
		title: 'Record the video and audio together',
		pledge: true,
		watchesVideo: true,
		lines: [
			yes('Video and audio from the same recording.'),
			no('Lip-sync.', 'Disqualified', "If the recording can't be verified."),
			no(
				'Audio recorded apart and laid over the video.',
				'Disqualified',
				"If the recording can't be verified.",
			),
		],
		notes: [],
	},
	{
		id: 'AUDIO-PROCESS',
		title: 'Stick to the allowed audio processing',
		pledge: true,
		watchesVideo: true,
		lines: [
			yes('Compression, EQ, and reverb.'),
			yes('Same processing on the whole recording, after you record.'),
			no('Different processing on kick and snare.', 'Red card', 'Immediate. You are out.'),
			no('Distortion, delay, or time/frequency warp.', 'Red card', 'Immediate. You are out.'),
		],
		notes: [],
	},
	{
		id: 'TIME-PENALTY',
		title: 'Performance length',
		pledge: true,
		watchesVideo: true,
		lines: [],
		notes: [],
	},
	{
		id: 'INTRO-SAME-TAKE',
		title: 'Record the intro in the same take',
		ruleTitle: 'Intro in the same take',
		pledge: true,
		watchesVideo: true,
		fix: { lead: 'Record the intro in the same take as the routine.', samples: [] },
		lines: [
			yes('Intro and routine share place and take.'),
			no('A separately recorded intro.', 'Disqualified', 'After an investigation.'),
		],
		notes: [],
	},
	{
		id: 'TEAM-VIS',
		title: 'Keep every member on screen',
		pledge: true,
		watchesVideo: true,
		categories: ['tag', 'crew'],
		lines: [
			yes('Every member stays on screen for the whole video.'),
			no(
				'Someone leaves the frame.',
				'Can be disqualified',
				'The rules forbid it. No automatic penalty named.',
			),
		],
		notes: [],
	},
	{
		id: 'VIS-FACE',
		title: 'Keep your face recognizable',
		pledge: true,
		watchesVideo: true,
		categories: ['solo', 'loopstation'],
		lines: [
			yes('Your face is clearly visible.'),
			no(
				'Face hidden by mask, darkness, or overexposure.',
				'Can be disqualified',
				'The rules forbid it. No automatic penalty named.',
			),
		],
		notes: [],
	},
	{
		id: 'NO-SHORT',
		title: 'Publish it as a normal video',
		fix: {
			lead: 'Shorts are not allowed. Use a normal video URL.',
			samples: [],
		},
		lines: [
			yes('A normal YouTube video.'),
			no('A YouTube Short.', 'Not accepted', 'Shorts are not allowed.'),
		],
		notes: [],
	},
	{
		id: 'GEN-VISIBILITY',
		title: 'Make the video public',
		fix: {
			lead: 'Private and unlisted videos are not allowed. Use a public URL.',
			samples: [],
		},
		lines: [
			yes('A public YouTube video.'),
			no('Private or unlisted.', 'Not accepted', 'Only public videos are allowed.'),
		],
		notes: [],
	},
	{
		id: 'TITLE-FORMAT',
		title: 'Video title',
		fix: { lead: "This title doesn't match. Use one of these.", samples: titleForms },
		lines: [
			yes(titleForms[0]),
			yes(titleForms[1]),
			no(
				'A different title.',
				'Can be disqualified',
				'The rules require this naming. No separate penalty named.',
			),
		],
		notes: [],
	},
	{
		id: 'INTRO-REQUIRED',
		title: 'Intro at the start',
		watchesVideo: true,
		fix: { lead: 'Say this at the start.', samples: [introQuote] },
		lines: [
			yes('The intro is at the start of the video.'),
			no(
				'The intro is missing from the start.',
				'Warning',
				'After an investigation. Not an immediate disqualification.',
			),
		],
		notes: [introQuote],
	},
]

const toPledge = (item: CatalogItem): Pledge => ({
	id: item.id,
	title: item.title,
	...(item.lead === undefined ? {} : { lead: item.lead }),
	lines: item.lines,
	notes: item.notes,
})

const pledgeById = (id: string): Pledge => {
	const item = catalog.find((entry) => entry.id === id && entry.pledge === true)
	if (item === undefined) throw new Error(id)
	return toPledge(item)
}

export const keepVideoPledge = pledgeById('SUB-ONCE')

const appliesTo = (item: CatalogItem, category: CategoryId) =>
	item.categories === undefined || item.categories.includes(category)

const appliesToSource = (item: CatalogItem, source: SourceKind) =>
	item.sources === undefined || item.sources.includes(source)

export const pledgesFor = (category: CategoryId, source: SourceKind): Pledge[] =>
	catalog
		.filter(
			(item) =>
				item.pledge === true && appliesTo(item, category) && appliesToSource(item, source),
		)
		.map((item) => {
			const pledge = toPledge(item)
			if (pledge.id === 'TIME-PENALTY') return { ...pledge, lines: timeLines(category) }
			if (pledge.id === 'SUB-RAW' && sessionRecordingCategories.includes(category)) {
				const video = pledge.lines.findIndex((line) =>
					line.text.startsWith('Raw video with camera audio'),
				)
				const lines = [...pledge.lines]
				lines.splice(video + 1, 0, yes(sessionRecordingText))
				return { ...pledge, lines }
			}
			return pledge
		})

const emptyLines: FixText = { lead: '', samples: [] }

const toRule = (item: CatalogItem & { fix: FixText }): RuleCopy => {
	const rule: RuleCopy = {
		title: item.ruleTitle ?? item.title,
		fix: item.fix,
	}
	if (item.pledge === true) return rule
	rule.lines = item.lines
	if (item.notes.length > 0) rule.notes = item.notes
	return rule
}

export const rules: Record<string, RuleCopy> = Object.fromEntries(
	catalog.flatMap((item) => {
		if (item.fix === undefined) return []
		const rule = toRule({ ...item, fix: item.fix })
		return [[item.id, rule] as const]
	}),
)

export const ruleLinesFor = (
	category: CategoryId | '',
	id: string,
	source: SourceKind = 'youtube',
) => {
	if (category !== '') {
		const pledge = pledgesFor(category, source).find((item) => item.id === id)
		if (pledge) return { lines: pledge.lines, notes: pledge.notes }
	}
	const copy = rules[id]
	return { lines: copy?.lines ?? [], notes: copy?.notes ?? [] }
}

export const ruleDetail = (id: string): FixText => rules[id]?.fix ?? emptyLines

const watchIds = new Set(catalog.filter((item) => item.watchesVideo === true).map((item) => item.id))

export const watchesVideo = (id: string) => watchIds.has(id)

const openingPledges = (category: CategoryId, source: SourceKind) =>
	pledgesFor(category, source).filter((pledge) => rules[pledge.id] === undefined)

export const plainPledgesFor = (category: CategoryId, source: SourceKind): Pledge[] =>
	openingPledges(category, source).filter((pledge) => !watchesVideo(pledge.id))

export const watchPledgesFor = (category: CategoryId, source: SourceKind): Pledge[] =>
	openingPledges(category, source).filter((pledge) => watchesVideo(pledge.id))

export const reviewPledgesFor = (
	category: CategoryId,
	ruleIds: readonly string[],
	source: SourceKind,
): Pledge[] => {
	const byId = new Map(pledgesFor(category, source).map((pledge) => [pledge.id, pledge]))
	return ruleIds.flatMap((id) => {
		const pledge = byId.get(id)
		return pledge ? [pledge] : []
	})
}
