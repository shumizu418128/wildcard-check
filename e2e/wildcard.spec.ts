import { expect, test, type Locator, type Page } from '@playwright/test'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const fixture = path.join(path.dirname(fileURLToPath(import.meta.url)), 'fixtures', 'clip.mp4')
const rawLink = 'https://example.com/raw'

const fillRaw = async (page: Page) => {
	await page.getByRole('textbox', { name: 'Raw file link' }).fill(rawLink)
}

const passingSoloTitle = 'Name - GBB26: World League Solo Wildcard'
const passingTagTitle = 'Name - GBB26: World League Tag Team Wildcard'

const stubYoutubeTitle = async (page: Page, title: string) => {
	await page.route('https://www.youtube.com/oembed*', async (route) => {
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ title }),
		})
	})
}

const previewOn = [
	'Record the video and audio together',
	'Stick to the allowed audio processing',
	'Performance length',
	'Record the intro in the same take',
	'Intro in the same take',
	'Keep your face recognizable',
	'Keep every member on screen',
	'Intro at the start',
]

const previewOff = [
	'You only get one submission',
	'Age restriction',
	'Video call if you win',
	'Video title',
	'Publish it as a normal video',
]

// A passed raw-link check is confirmed after the video. Hide the preview there too.
const hidesPreview = (heading: string) =>
	previewOff.includes(heading) || heading === 'Add your raw files with a public link'

const expectCloseAtTopRight = async (dialog: Locator) => {
	const close = dialog.getByRole('button', { name: 'Close' })
	await expect(close).toBeVisible()
	const closeBox = await close.boundingBox()
	const dialogBox = await dialog.boundingBox()
	expect(closeBox).not.toBeNull()
	expect(dialogBox).not.toBeNull()
	if (closeBox === null || dialogBox === null) return
	const rightGap = dialogBox.x + dialogBox.width - (closeBox.x + closeBox.width)
	const topGap = closeBox.y - dialogBox.y
	expect(rightGap).toBeGreaterThanOrEqual(8)
	expect(rightGap).toBeLessThanOrEqual(24)
	expect(topGap).toBeGreaterThanOrEqual(8)
	expect(topGap).toBeLessThanOrEqual(24)
}

const expectPreviewFor = async (page: Page, heading: string) => {
	const preview = page.getByTestId('video-preview')
	if (previewOn.includes(heading)) await expect(preview).toBeVisible()
	if (hidesPreview(heading)) await expect(preview).toBeHidden()
}

const notePreviewOrder = (heading: string, started: { value: boolean }) => {
	if (previewOff.includes(heading)) expect(started.value, heading).toBe(false)
	if (previewOn.includes(heading)) started.value = true
}

const banned = [
	'完了',
	'合格',
	'準備でき',
	'通過しました',
	'このまま提出',
	'All set',
	'Success',
	'Congratulations',
]

const open = async (page: Page) => {
	await page.goto('/')
	await page.waitForFunction(() => {
		const select = document.querySelector('select')
		return select !== null && Object.getOwnPropertySymbols(select).length > 0
	})
}

const chooseSolo = async (page: Page) => {
	await page.getByLabel('Category').selectOption('solo')
}

const stepMark = async (page: Page) =>
	page.evaluate(() => {
		if (document.querySelector('[data-testid="outcome"]')) return 'outcome'
		if (document.querySelector('[data-testid="please-wait"]')) return 'wait'
		return document.querySelector('h1')?.textContent?.trim() ?? ''
	})

const agreeAndLeave = async (page: Page) => {
	const before = await stepMark(page)
	await page.getByRole('checkbox').check()
	await page.getByRole('button', { name: 'Next', exact: true }).click()
	await expect.poll(async () => stepMark(page), { timeout: 20000 }).not.toBe(before)
}

const pollUntilLeft = async (page: Page) => {
	await expect
		.poll(
			async () => {
				if (!(await page.getByTestId('please-wait').isVisible())) return 'left'
				const waitButton = page.getByRole('button', { name: 'Next', exact: true })
				if (await waitButton.isEnabled()) await waitButton.click()
				return 'waiting'
			},
			{ timeout: 20000 },
		)
		.toBe('left')
}

const walkPledges = async (page: Page, rawLinkExpected = '') => {
	let sawIntroPledge = false
	let sawRawPledge = false
	const previewStarted = { value: false }
	for (let step = 0; step < 24; step += 1) {
		if (await page.getByTestId('outcome').isVisible()) break
		await expect
			.poll(
				async () => {
					if (await page.getByTestId('outcome').isVisible()) return 'outcome'
					if (await page.getByTestId('please-wait').isVisible()) return 'wait'
					const next = page.getByRole('button', { name: 'Next', exact: true })
					if (await next.isVisible()) return 'next'
					return ''
				},
				{ timeout: 20000 },
			)
			.not.toBe('')
		if (await page.getByTestId('outcome').isVisible()) break
		if (await page.getByTestId('please-wait').isVisible()) {
			await pollUntilLeft(page)
			continue
		}
		const heading = (await page.getByRole('heading').first().innerText()).trim()
		notePreviewOrder(heading, previewStarted)
		if (heading === 'Add your raw files with a public link') {
			sawRawPledge = true
			await expect(page.getByTestId('found-raw')).toHaveText(rawLinkExpected)
		}
		if (heading === 'Record the intro in the same take') {
			sawIntroPledge = true
			await expect(page.getByText('Automatic review')).toHaveCount(0)
			await expect(page.getByTestId('same-take-compare')).toBeVisible()
			await expect(page.getByText('Intro and routine share place and take.')).toBeVisible()
		}
		if (heading === 'Record the video and audio together') {
			const preview = page.getByTestId('video-preview')
			const video = preview.locator('video')
			const frame = preview.locator('iframe')
			if ((await video.count()) > 0) await expect(video).toHaveAttribute('src', /^blob:/)
			if ((await frame.count()) > 0) {
				await expect(frame).toHaveAttribute(
					'src',
					/https:\/\/www\.youtube-nocookie\.com\/embed\/abcdefghijk\?/,
				)
			}
		}
		await expectPreviewFor(page, heading)
		await expect(page.getByText("This isn't checked automatically")).toHaveCount(0)
		await expect(page.getByText('Needs attention')).toHaveCount(0)
		await agreeAndLeave(page)
	}
	expect(sawIntroPledge).toBe(true)
	expect(sawRawPledge).toBe(rawLinkExpected !== '')
}

const expectNoBannedWords = async (page: Page, expectRawPledge = true) => {
	const text = await page.getByTestId('outcome').innerText()
	for (const word of banned) {
		expect(text, word).not.toContain(word)
	}
	for (const code of ['INTRO-SAME-TAKE', 'SYNC-LIVE', 'NO-SHORT', 'TITLE-FORMAT']) {
		expect(text, code).not.toContain(code)
	}
	expect(text).not.toContain('For reference')
	expect(text).not.toContain("isn't checked automatically")
	expect(text).not.toContain('Needs attention')
	expect(text).toContain('What you agreed to')
	const titles = [
		'Intro at the start',
		'Record the intro in the same take',
		'Keep your face recognizable',
	]
	if (expectRawPledge) titles.push('Add your raw files with a public link')
	for (const title of titles) {
		expect(text, title).toContain(title)
	}
	if (!expectRawPledge) expect(text).not.toContain('Add your raw files with a public link')
}

test('a file stops at the pre-review and does not offer submission', async ({ page }) => {
	await open(page)
	await page.screenshot({ path: 'e2e/artifacts/intake.png', fullPage: true })
	await chooseSolo(page)
	await expect(page.getByRole('textbox', { name: 'Raw file link' })).toHaveCount(0)
	await page.getByLabel('Video file').setInputFiles(fixture)
	await page.getByRole('button', { name: 'Start the review' }).click()
	await expect(page).toHaveURL(/\/review\/file$/)
	await expect(page.getByRole('heading', { name: 'You only get one submission' })).toBeVisible()
	await expect(page.getByText('Solo', { exact: true })).toBeVisible()
	await expect(page.getByTestId('video-preview')).toBeHidden()
	await expect(page.getByText('Received')).toHaveCount(0)
	await expect(page.getByText('SYNC-LIVE')).toHaveCount(0)
	await page.screenshot({ path: 'e2e/artifacts/pledge.png', fullPage: true })
	await walkPledges(page)
	await expect(page).toHaveURL(/\/finish\/file$/)
	await expect(page.getByRole('heading', { name: "This isn't finished yet." })).toBeVisible()
	await expect(
		page.getByText('Post as a normal YouTube video, then review that URL here.'),
	).toBeVisible()
	const agreed = page.locator('section').filter({
		has: page.getByRole('heading', { name: 'What you agreed to' }),
	})
	const post = agreed.getByRole('listitem').filter({ hasText: 'Post it on YouTube' })
	const resubmit = agreed.getByRole('listitem').filter({ hasText: 'Submit the link here again' })
	await expect(post).toContainText('Not yet')
	await expect(post).not.toContainText('Agreed')
	await expect(resubmit).toContainText('Not yet')
	await expect(resubmit).not.toContainText('Agreed')
	await expect(page.getByRole('heading', { name: 'Still open' })).toBeVisible()
	await expect(page.getByTestId('open-step')).toHaveCount(2)
	await expect(page.getByRole('link', { name: 'Continue' })).toHaveCount(0)
	await expect(page.getByRole('button', { name: 'Next', exact: true })).toHaveCount(0)
	await expect(page.getByRole('button', { name: 'go back to top' })).toBeVisible()
	await expect(page.getByRole('heading', { name: 'final review' })).toHaveCount(0)
	await expectNoBannedWords(page, false)
	await page.screenshot({ path: 'e2e/artifacts/file-end.png', fullPage: true })
})

test('YouTube continues to the Swissbeatbox submission page', async ({ page }) => {
	await open(page)
	await chooseSolo(page)
	await page.getByLabel('Video file').setInputFiles(fixture)
	await page.getByRole('textbox', { name: 'YouTube URL' }).fill('https://www.youtube.com/watch?v=abcdefghijk')
	await fillRaw(page)
	await stubYoutubeTitle(page, passingSoloTitle)
	await page.getByRole('button', { name: 'Start the review' }).click()
	await expect(page).toHaveURL(/\/review\/[^/]+$/)
	await expect(page).not.toHaveURL(/\/review\/file$/)
	await expect(page.getByRole('heading', { name: 'You only get one submission' })).toBeVisible()
	await expect(page.getByText('Solo', { exact: true })).toBeVisible()
	await expect(page.getByTestId('video-preview')).toBeHidden()
	await walkPledges(page, rawLink)
	await expect(page).toHaveURL(/\/finish\/[^/]+$/)
	await expect(page).not.toHaveURL(/\/finish\/file$/)
	await expect(page.getByTestId('outcome')).toBeVisible()
	await expect(page.getByRole('heading', { name: "This isn't finished yet." })).toBeVisible()
	await expect(
		page.getByText("This counts as a Wildcard only after you submit it to Swissbeatbox."),
	).toHaveCount(0)
	await expect(page.getByRole('link', { name: 'Continue' })).toHaveCount(0)
	await page.getByRole('button', { name: 'Next', exact: true }).click()
	const dialog = page.getByRole('dialog')
	await expect(dialog).toBeVisible()
	const line = dialog.getByLabel('Type this line to continue.')
	await line.fill('i will n0t delete my wildcard!')
	await expect(line).toHaveValue('I WILL NT DELETE MY WILDCARD')
	await expect(dialog.getByRole('link', { name: 'Continue' })).toHaveCount(0)
	await expect(dialog.getByRole('heading', { name: 'You only get one submission' })).toHaveCount(0)
	await line.fill('i will not delete my wildcard')
	await expect(line).toHaveValue('I WILL NOT DELETE MY WILDCARD')
	await expect(dialog.getByRole('heading', { name: 'You only get one submission' })).toBeVisible()
	await expect(dialog.getByText('Delete and replace the video.')).toBeVisible()
	await expect(
		dialog.getByText('Only the first video counts. You lose your Wildcard.'),
	).toBeVisible()
	const reviewId = page.url().match(/\/finish\/([^/?#]+)/)?.[1]
	expect(reviewId).toBeTruthy()
	await expect(dialog.getByRole('link', { name: 'Continue' })).toHaveAttribute(
		'href',
		`https://docs.google.com/forms/d/e/1FAIpQLSfHGZgoIkOHUwHnWeZTcNUU8b9OmQf3bq0SAEjiQomzWmemGg/viewform?usp=pp_url&entry.707071559=${reviewId}`,
	)
	await expect(page.getByText('Shorts are not allowed.')).toHaveCount(0)
	await expect(page.getByRole('heading', { name: 'Automatic review' })).toHaveCount(0)
	const agreed = page.locator('section').filter({
		has: page.getByRole('heading', { name: 'What you agreed to' }),
	})
	await expect(agreed.getByText('Publish it as a normal video')).toBeVisible()
	await expect(agreed.getByText('Video title')).toHaveCount(0)
	await expect(agreed.getByText('Post it on YouTube')).toHaveCount(0)
	await expect(agreed.getByText('Submit the link here again')).toHaveCount(0)
	await expectNoBannedWords(page)
	await page.screenshot({ path: 'e2e/artifacts/youtube-end.png', fullPage: true })
	const backdrop = await page.evaluate(() => document.elementFromPoint(8, 8)?.tagName ?? '')
	expect(backdrop).toBe('DIALOG')
	await page.mouse.click(8, 8)
	await expect(dialog).toBeVisible()
	await expectCloseAtTopRight(dialog)
	await dialog.getByRole('button', { name: 'Go back' }).click()
	await expect(dialog).toBeHidden()
	await expect(page).toHaveURL(/\/finish\/[^/]+$/)
	await expect(page.getByRole('button', { name: 'Next', exact: true })).toBeVisible()
	await page.getByRole('button', { name: 'go back to top' }).click()
	await expect(page).toHaveURL(/\/$/)
	await expect(page.getByRole('heading', { name: 'Review before you submit' })).toBeVisible()
	await expect(page.getByRole('textbox', { name: 'YouTube URL' })).toHaveValue(
		'https://www.youtube.com/watch?v=abcdefghijk',
	)
})

const doneReview = {
	id: 'job-fix',
	status: 'done',
	rules: [
		{ id: 'NO-SHORT', status: 'clear' },
		{ id: 'SUB-RAW', status: 'clear' },
		{ id: 'INTRO-REQUIRED', status: 'clear' },
		{ id: 'INTRO-SAME-TAKE', status: 'clear' },
	],
}

const runningReview = {
	id: 'job-wait',
	status: 'running',
	rules: [],
}

const fulfillReview = async (page: Page, body: object) => {
	await page.route('**/api/reviews**', async (route) => {
		await route.fulfill({
			status: route.request().method() === 'POST' ? 201 : 200,
			contentType: 'application/json',
			body: JSON.stringify(body),
		})
	})
}

const startYoutube = async (page: Page) => {
	await stubYoutubeTitle(page, passingSoloTitle)
	await open(page)
	await chooseSolo(page)
	await page.getByLabel('Video file').setInputFiles(fixture)
	await page.getByRole('textbox', { name: 'YouTube URL' }).fill('https://www.youtube.com/watch?v=abcdefghijk')
	await fillRaw(page)
	await page.getByRole('button', { name: 'Start the review' }).click()
	await expect(page).toHaveURL(/\/review\/[^/]+$/)
}

test('a title that does not match ends the review', async ({ page }) => {
	await stubYoutubeTitle(page, 'Placeholder video title')
	await open(page)
	await chooseSolo(page)
	await page.getByLabel('Video file').setInputFiles(fixture)
	await page.getByRole('textbox', { name: 'YouTube URL' }).fill('https://www.youtube.com/watch?v=abcdefghijk')
	await fillRaw(page)
	await page.getByRole('button', { name: 'Start the review' }).click()
	// タイトルは誓約へ進んだあと裏で確かめる
	await expect(page).toHaveURL(/\/review\/[^/]+$/)
	const dialog = page.getByRole('alertdialog')
	await expect(dialog).toBeVisible()
	await expect(dialog.getByRole('heading', { name: 'Video title' })).toBeVisible()
	await expect(dialog.getByTestId('found-title')).toHaveText('Placeholder video title')
	await expect(dialog.getByText("This title doesn't match. Use one of these.")).toBeVisible()
	await expect(dialog.getByText('A different title.')).toBeVisible()
	await expect(dialog.getByRole('checkbox')).toHaveCount(0)
	await expect(page.getByRole('heading', { name: 'You only get one submission' })).toHaveCount(0)
	await expectCloseAtTopRight(dialog)
	await dialog.getByRole('button', { name: 'End the review' }).click()
	await expect(dialog).toBeHidden()
	await expect(page).toHaveURL(/\/$/)
	await expect(page.getByRole('textbox', { name: 'YouTube URL' })).toHaveValue(
		'https://www.youtube.com/watch?v=abcdefghijk',
	)
	await expect(page.getByLabel('Category')).toHaveValue('solo')
})

test('a failed same-take review lists the result and the rule apart', async ({ page }) => {
	const sameTake = {
		...doneReview,
		id: 'job-same-take',
		rules: doneReview.rules.map((rule) => ({
			...rule,
			status: rule.id === 'INTRO-SAME-TAKE' ? ('fix' as const) : ('clear' as const),
		})),
	}
	await fulfillReview(page, sameTake)
	await startYoutube(page)

	const headings: string[] = []
	const previewStarted = { value: false }
	for (let step = 0; step < 20; step += 1) {
		await expect
			.poll(async () => {
				if (await page.getByTestId('outcome').isVisible()) return 'outcome'
				if (await page.getByRole('checkbox').isVisible()) return 'agree'
				return ''
			})
			.not.toBe('')
		if (await page.getByTestId('outcome').isVisible()) break
		const heading = (await page.getByRole('heading').first().innerText()).trim()
		headings.push(heading)
		notePreviewOrder(heading, previewStarted)
		await expectPreviewFor(page, heading)
		if (heading === 'Intro in the same take') {
			const card = page.locator('article').filter({ has: page.getByRole('heading', { name: heading }) })
			await expect(card.getByRole('heading', { name: 'Automatic review' })).toBeVisible()
			await expect(card.getByRole('heading', { name: 'The rule', exact: true })).toBeVisible()
			await expect(card.getByText('Record the intro in the same take as the routine.')).toBeVisible()
			await expect(card.getByTestId('same-take-compare')).toBeVisible()
			await expect(card.getByText('Intro and routine share place and take.')).toBeVisible()
			await expect(card.getByText('A separately recorded intro.')).toBeVisible()
		}
		await agreeAndLeave(page)
	}

	expect(headings.filter((heading) => heading === 'Intro in the same take')).toHaveLength(1)
	expect(headings).not.toContain('Record the intro in the same take')
	const automatic = page.locator('section').filter({
		has: page.getByRole('heading', { name: 'Automatic review', exact: true }),
	})
	await expect(automatic.getByRole('heading', { name: 'Intro in the same take' })).toBeVisible()
	await expect(automatic.getByRole('heading', { name: 'The rule', exact: true })).toHaveCount(0)
	await expect(automatic.getByText('A separately recorded intro.')).toHaveCount(0)
	await expect(
		automatic.getByText('The system found a problem. You reviewed this yourself.'),
	).toBeVisible()
})

test('a team visibility pledge appears once without an automatic review', async ({ page }) => {
	await fulfillReview(page, { ...doneReview, id: 'job-team-vis' })
	await open(page)
	await page.getByLabel('Category').selectOption('tag')
	await page.getByLabel('Video file').setInputFiles(fixture)
	await page.getByRole('textbox', { name: 'YouTube URL' }).fill('https://www.youtube.com/watch?v=abcdefghijk')
	await fillRaw(page)
	await stubYoutubeTitle(page, passingTagTitle)
	await page.getByRole('button', { name: 'Start the review' }).click()
	await expect(page).toHaveURL(/\/review\/[^/]+$/)

	const headings: string[] = []
	for (let step = 0; step < 20; step += 1) {
		await expect
			.poll(async () => {
				if (await page.getByTestId('outcome').isVisible()) return 'outcome'
				if (await page.getByRole('checkbox').isVisible()) return 'agree'
				return ''
			})
			.not.toBe('')
		if (await page.getByTestId('outcome').isVisible()) break
		const heading = (await page.getByRole('heading').first().innerText()).trim()
		headings.push(heading)
		if (heading === 'Keep every member on screen') {
			const card = page.locator('article').filter({
				has: page.getByRole('heading', { name: heading }),
			})
			await expect(card.getByRole('heading', { name: 'Automatic review' })).toHaveCount(0)
			await expect(card.getByText('Every member stays on screen for the whole video.')).toBeVisible()
		}
		await agreeAndLeave(page)
	}

	expect(headings.filter((heading) => heading === 'Keep every member on screen')).toHaveLength(1)
	expect(headings).not.toContain('Keep your face recognizable')
	await expect(page.getByRole('heading', { name: 'Automatic review', exact: true })).toHaveCount(0)
	const agreed = page.locator('section').filter({
		has: page.getByRole('heading', { name: 'What you agreed to' }),
	})
	await expect(agreed.getByText('Keep every member on screen')).toHaveCount(1)
})

test('an unfinished review can ask you to wait partway through', async ({ page }) => {
	await fulfillReview(page, runningReview)
	await startYoutube(page)
	await expect(page.getByRole('heading', { name: 'You only get one submission' })).toBeVisible()
	await expect(page.getByTestId('please-wait')).toHaveCount(0)

	for (let step = 0; step < 12; step += 1) {
		if (await page.getByTestId('please-wait').isVisible()) break
		await expect(page.getByRole('heading', { name: 'Record the video and audio together' })).toHaveCount(0)
		await expect(page.getByRole('heading', { name: 'Record the intro in the same take' })).toHaveCount(0)
		await agreeAndLeave(page)
	}

	await expect(page.getByTestId('please-wait')).toBeVisible()
	await expect(page.getByText('Please wait a moment.')).toBeVisible()
	await expect(page.getByText('This may take a few minutes.')).toBeVisible()
	await expect(page.getByTestId('wait-spinner')).toBeVisible()
	const waitingPreview = page.getByTestId('please-wait').getByTestId('video-preview')
	await expect(waitingPreview).toBeVisible()
	await expect(waitingPreview.locator('video')).toHaveAttribute('src', /^blob:/)
	await expect(page.getByRole('button', { name: 'Still reviewing' })).toHaveCount(0)
	await expect(page.getByRole('button', { name: 'Next', exact: true })).toHaveCount(0)
	await expect(page.getByTestId('wait-elapsed')).toContainText('0:0')
	await expect(page.getByTestId('wait-elapsed')).not.toContainText('0:00')
	await expect(page.getByTestId('auto-error')).toHaveCount(0)
	await expect(page).toHaveURL(/\/review\/[^/]+$/)
	await expect(page.getByTestId('outcome')).toHaveCount(0)
})

test('the wait screen moves on by itself when the review is ready', async ({ page }) => {
	let ready = false
	await page.route('**/api/reviews**', async (route) => {
		const request = route.request()
		if (request.url().endsWith('/agreements')) {
			await route.fulfill({ status: 204 })
			return
		}
		await route.fulfill({
			status: request.method() === 'POST' ? 201 : 200,
			contentType: 'application/json',
			body: JSON.stringify(ready ? { ...doneReview, id: 'job-wait' } : runningReview),
		})
	})
	await startYoutube(page)

	for (let step = 0; step < 12; step += 1) {
		if (await page.getByTestId('please-wait').isVisible()) break
		await agreeAndLeave(page)
	}
	await expect(page.getByTestId('please-wait')).toBeVisible()
	await expect(page.getByTestId('wait-spinner')).toBeVisible()
	await expect(page.getByTestId('please-wait').getByTestId('video-preview')).toBeVisible()

	ready = true
	await expect(page.getByTestId('please-wait')).toHaveCount(0, { timeout: 8000 })
	await expect(page.getByRole('checkbox')).toBeVisible()
})

const fulfillResumable = async (page: Page) => {
	const agreements: string[] = []
	await page.route('**/api/reviews**', async (route) => {
		const request = route.request()
		if (request.url().endsWith('/agreements')) {
			const body = request.postDataJSON() as { rule_id: string }
			if (!agreements.includes(body.rule_id)) agreements.push(body.rule_id)
			await route.fulfill({ status: 204 })
			return
		}
		const id = new URL(request.url()).pathname.split('/').at(-1)
		await route.fulfill({
			status: request.method() === 'POST' ? 201 : 200,
			contentType: 'application/json',
			body: JSON.stringify({
				...doneReview,
				id,
				category: 'solo',
				source: 'youtube',
				youtube_url: 'https://www.youtube.com/watch?v=abcdefghijk',
				raw_url: rawLink,
				agreements,
			}),
		})
	})
	return agreements
}

test('a YouTube review resumes from the same step after a reload', async ({ page }) => {
	const agreements = await fulfillResumable(page)
	page.on('dialog', (dialog) => void dialog.accept())
	await startYoutube(page)
	const id = new URL(page.url()).pathname.split('/').at(-1) ?? ''
	await agreeAndLeave(page)
	await agreeAndLeave(page)
	await expect.poll(() => agreements.length).toBe(2)
	const heading = await stepMark(page)

	await page.reload()
	await expect(page).toHaveURL(`/review/${id}`)
	await expect(page.getByRole('heading', { name: heading, exact: true })).toBeVisible()

	for (let step = 0; step < 24; step += 1) {
		if (await page.getByTestId('outcome').isVisible()) break
		await agreeAndLeave(page)
	}
	await expect(page).toHaveURL(`/finish/${id}`)

	await page.reload()
	await expect(page).toHaveURL(`/finish/${id}`)
	await expect(page.getByTestId('outcome')).toBeVisible()
})

test('a YouTube review opens the pledges before the upload finishes', async ({ page }) => {
	const agreed: string[] = []
	let release = () => {}
	const held = new Promise<void>((resolve) => {
		release = resolve
	})
	let postedId = ''
	await page.route('**/api/reviews**', async (route) => {
		const request = route.request()
		if (request.url().endsWith('/agreements')) {
			agreed.push(request.url())
			await route.fulfill({ status: 204 })
			return
		}
		if (request.method() === 'POST') {
			postedId = /name="id"\r\n\r\n([^\r]+)\r\n/.exec(request.postData() ?? '')?.[1] ?? ''
			await held
		}
		await route.fulfill({
			status: request.method() === 'POST' ? 201 : 200,
			contentType: 'application/json',
			body: JSON.stringify({ ...runningReview, id: postedId }),
		})
	})
	await startYoutube(page)
	const id = new URL(page.url()).pathname.split('/').at(-1) ?? ''
	await expect(page.getByRole('heading', { name: 'You only get one submission' })).toBeVisible()
	await agreeAndLeave(page)
	expect(agreed).toHaveLength(0)

	await expect.poll(() => postedId).toBe(id)
	release()
	await expect.poll(() => agreed).toEqual([expect.stringContaining(`/api/reviews/${id}/agreements`)])
})

test('a YouTube review sends clips cut from the file', async ({ page }) => {
	let posted = ''
	await page.route('**/api/reviews', async (route) => {
		if (route.request().method() !== 'POST') {
			await route.continue()
			return
		}
		posted = route.request().postDataBuffer()?.toString('utf8') ?? ''
		await route.fulfill({
			status: 201,
			contentType: 'application/json',
			body: JSON.stringify({
				id: 'job-youtube-file',
				source: 'youtube',
				status: 'done',
				rules: [
					{ id: 'INTRO-REQUIRED', status: 'clear' },
					{ id: 'INTRO-SAME-TAKE', status: 'clear' },
				],
			}),
		})
	})
	await startYoutube(page)
	const id = new URL(page.url()).pathname.split('/').at(-1) ?? ''
	await expect(page.getByRole('heading', { name: 'You only get one submission' })).toBeVisible()
	await expect.poll(() => posted).not.toBe('')
	// 動画本体ではなく、切り出した素材と URL を一度に送る
	expect(posted).toContain(`name="id"\r\n\r\n${id}\r\n`)
	expect(posted).toMatch(/name="source"\r\n\r\nyoutube\r\n/)
	expect(posted).toContain('abcdefghijk')
	expect(posted).toContain(rawLink)
	for (const name of ['intro_audio', 'intro_frame', 'routine_frame']) {
		expect(posted).toContain(`name="${name}"`)
	}
})

test('the file is required and the raw link appears only with a YouTube URL', async ({ page }) => {
	await open(page)
	await chooseSolo(page)
	await expect(page.getByRole('button', { name: 'File', exact: true })).toHaveCount(0)
	await expect(page.getByLabel('Video file')).toHaveAttribute('required', '')
	await expect(page.getByRole('textbox', { name: 'YouTube URL' })).not.toHaveAttribute('required')
	await expect(page.getByRole('textbox', { name: 'Raw file link' })).toHaveCount(0)
	await page.getByRole('textbox', { name: 'YouTube URL' }).fill('https://www.youtube.com/watch?v=abcdefghijk')
	await expect(page.getByRole('textbox', { name: 'Raw file link' })).toHaveAttribute('required', '')
	await page.getByRole('button', { name: 'Start the review' }).click()
	await expect(page).toHaveURL(/\/$/)
})

test('a Shorts URL is excluded before the review starts', async ({ page }) => {
	await open(page)
	await chooseSolo(page)
	await page.getByLabel('Video file').setInputFiles(fixture)
	await page.getByRole('textbox', { name: 'YouTube URL' }).fill('https://www.youtube.com/shorts/abcdefghijk')
	await fillRaw(page)
	await page.getByRole('button', { name: 'Start the review' }).click()
	const dialog = page.getByRole('alertdialog')
	await expect(dialog).toBeVisible()
	await expect(dialog.getByText('Shorts are not allowed. Use a normal video URL.')).toBeVisible()
	await expect(dialog.getByTestId('format-compare')).toBeVisible()
	await expect(page).toHaveURL(/\/$/)
	await expect(page.getByRole('heading', { name: 'Record the video and audio together' })).toHaveCount(0)
	await page.screenshot({ path: 'e2e/artifacts/shorts-end.png', fullPage: true })
	await expectCloseAtTopRight(dialog)
	await dialog.getByRole('button', { name: 'End the review' }).click()
	await expect(dialog).toBeHidden()
	await expect(page.getByRole('textbox', { name: 'YouTube URL' })).toHaveValue(
		'https://www.youtube.com/shorts/abcdefghijk',
	)
	await expect(page.getByLabel('Category')).toHaveValue('solo')
})

test('a Shorts result ends the review', async ({ page }) => {
	const shortsReview = {
		...doneReview,
		id: 'job-shorts',
		rules: doneReview.rules.map((rule) =>
			rule.id === 'NO-SHORT' ? { ...rule, status: 'fix' as const } : rule,
		),
	}
	await fulfillReview(page, shortsReview)
	await startYoutube(page)
	const dialog = page.getByRole('alertdialog')
	await expect(dialog).toBeVisible()
	await expect(dialog.getByRole('heading', { name: 'Publish it as a normal video' })).toBeVisible()
	await expect(dialog.getByText('Shorts are not allowed. Use a normal video URL.')).toBeVisible()
	await expect(dialog.getByTestId('format-compare')).toBeVisible()
	await expect(page.getByTestId('auto-error')).toHaveCount(0)
	await expect(page.getByRole('heading', { name: 'Video title' })).toHaveCount(0)
	await expect(page.getByTestId('outcome')).toHaveCount(0)
	await expectCloseAtTopRight(dialog)
	await dialog.getByRole('button', { name: 'Close' }).click()
	await expect(page).toHaveURL(/\/$/)
	await expect(dialog).toBeHidden()
	await expect(page.getByRole('heading', { name: 'Review before you submit' })).toBeVisible()
})
