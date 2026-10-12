/**
 * Screen labels. submissionUrlFor builds the Swissbeatbox Google Form with review id.
 * While reviewId is empty, the submission button stays disabled.
 * The on-screen edition is 2027. GBB2026 / GBB26 / 2026-09-24 in the review text are placeholders.
 */
export const submissionUrlFor = (reviewId: string) =>
	`https://docs.google.com/forms/d/e/1FAIpQLSfHGZgoIkOHUwHnWeZTcNUU8b9OmQf3bq0SAEjiQomzWmemGg/viewform?usp=pp_url&entry.707071559=${encodeURIComponent(reviewId)}`

export const editionLabel = 'GBB2026-v0.1'

export const categories = [
	{ id: 'solo', label: 'Solo' },
	{ id: 'loopstation', label: 'Loopstation' },
	{ id: 'tag', label: 'Tag Team' },
	{ id: 'crew', label: 'Crew' },
] as const

export type CategoryId = (typeof categories)[number]['id']

export const categoryLabel = (id: CategoryId) =>
	categories.find((category) => category.id === id)?.label ?? id

export type SourceKind = 'file' | 'youtube'
export type RuleStatus = 'clear' | 'fix'

export const sheet = {
	title: 'Review before you submit',
	category: 'Category',
	categoryPlaceholder: 'Choose a category',
	fileLabel: 'Video file',
	fileChoose: 'Choose a file',
	fileHint: 'MP4, MOV, or WebM. The file is only used for the review.',
	urlLabel: 'YouTube URL',
	urlOptional: '(optional)',
	urlHint: 'Add it to also review the title and visibility on YouTube.',
	urlPlaceholder: 'https://www.youtube.com/watch?v=',
	rawLabel: 'Raw file link',
	rawPlaceholder: 'https://',
	start: 'Start the review',
	agree: 'I read this. My submission follows it.',
	back: 'Go back',
	close: 'Close',
	next: 'Next',
	pleaseWait: 'Please wait a moment.',
	pleaseWaitHint: 'This may take a few minutes.',
	waitElapsed: 'Waiting',
	fileBody: 'Post as a normal YouTube video, then review that URL here.',
	filePost: 'Post it on YouTube',
	fileResubmit: 'Submit the link here again',
	resultLead: "This isn't finished yet.",
	finalReviewLead: 'Type this line to continue.',
	keepVideoPhrase: 'I WILL NOT DELETE MY WILDCARD',
	continueSubmission: 'Continue',
	submissionMissing: "The submission link isn't set.",
	autoHeading: 'Automatic review',
	foundTitle: 'Title on YouTube',
	foundRaw: 'Raw file link you submitted',
	autoOwnRisk: 'The system found a problem. You reviewed this yourself.',
	ruleHeading: 'The rule',
	pledgeHeading: 'What you agreed to',
	openHeading: 'Still open',
	pledgeNoted: 'Agreed',
	pledgeOpen: 'Not yet',
	startError: "Couldn't start the review. Fix your input and try again.",
	rateLimitError: 'Too many reviews in a row. Wait 10 seconds and try again.',
	streamError: 'The review was interrupted. Start again.',
	shortsUrlError: 'Shorts are not allowed. Use a normal video URL.',
	titleUrlError: "This title doesn't match. Use one of these.",
	visibilityUrlError: 'Private and unlisted videos are not allowed. Use a public URL.',
	previewTitle: 'Submitted video',
	endReview: 'End the review',
	again: 'go back to top',
	formatCompareLabel: 'Short versus normal video',
	formatShort: 'Short',
	formatNormal: 'Normal',
	visibilityCompareLabel: 'Private or unlisted versus public',
	visibilityLocked: 'Private / Unlisted',
	visibilityPublic: 'Public',
	sameTakeCompareLabel: 'Intro and routine frames',
	sameTakeIntro: 'Intro',
	sameTakeRoutine: 'Routine',
	sameTakeHint: 'Same place: keep. Different place: fix before submit.',
}
