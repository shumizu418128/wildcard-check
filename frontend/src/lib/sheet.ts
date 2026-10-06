/**
 * Screen labels. submissionUrl is the Swissbeatbox submission page.
 * While it is empty, the submission button stays disabled.
 * The on-screen edition is 2027. GBB2026 / GBB26 / 2026-09-24 in the review text are placeholders.
 */
export const submissionUrl = 'https://example.com'

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
	leadFile: 'File upload is for review only.',
	leadYoutube: 'If clear, continue to Swissbeatbox.',
	category: 'Category',
	categoryPlaceholder: 'Choose a category',
	sourceKind: 'Source',
	sourceFile: 'File',
	sourceYoutube: 'YouTube URL',
	fileLabel: 'Video file',
	fileChoose: 'Choose a file',
	urlLabel: 'YouTube URL',
	urlPlaceholder: 'https://www.youtube.com/watch?v=',
	rawLabel: 'Raw file link',
	rawPlaceholder: 'https://',
	start: 'Start the review',
	agree: 'I read this. My submission follows it.',
	back: 'Go back',
	close: 'Close',
	next: 'Next',
	pleaseWait: 'Please wait a moment.',
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
	streamError: 'The review was interrupted. Start again.',
	shortsUrlError: 'Shorts are not allowed. Use a normal video URL.',
	titleUrlError: "This title doesn't match. Use one of these.",
	visibilityUrlError: 'Private and unlisted videos are not allowed. Use a public URL.',
	premiereTitle: 'Upload the video file',
	premiereNotice:
		'This premiere is not available yet. Submit the same video file so the review can continue.',
	premiereHint: 'The review continues with this file instead of the YouTube URL.',
	premiereContinue: 'Continue with this file',
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
