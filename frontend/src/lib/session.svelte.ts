import { goto } from '$app/navigation'
import {
	plainPledgesFor,
	reviewPledgesFor,
	watchPledgesFor,
	watchesVideo,
} from '$lib/catalog'
import { categories, sheet, type CategoryId, type RuleStatus, type SourceKind } from '$lib/sheet'
import { fetchYoutubeTitle, titleMatches } from '$lib/title-format'
import { ensureDebugMode } from '$lib/debug'
import {
	isNonPublicUrlCode,
	isShortsUrl,
	premiereUnavailableCode,
	shortsUrlCode,
} from '$lib/youtube'

export const reviewSessionKey = 'review-session'

type Phase = 'intake' | 'work' | 'result'

type AbortKind = 'shorts' | 'visibility' | 'title'

type RuleResult = {
	id: string
	status: RuleStatus
}

type ReviewResource = {
	id: string
	category?: string
	source?: SourceKind
	status: 'running' | 'done'
	rules: RuleResult[]
	raw_url?: string
	youtube_url?: string
	agreements?: string[]
}

const isCategoryId = (value: unknown): value is CategoryId =>
	typeof value === 'string' && categories.some((category) => category.id === value)

const readErrorDetail = async (response: Response) => {
	try {
		const payload = (await response.json()) as { detail?: unknown }
		return typeof payload.detail === 'string' ? payload.detail : ''
	} catch {
		return ''
	}
}

export class ReviewSession {
	phase = $state<Phase>('intake')
	category = $state<CategoryId | ''>('')
	source = $state<SourceKind>('file')
	youtubeUrl = $state('')
	rawUrl = $state('')
	pledgeIndex = $state(0)
	pledgeStep = $state<'plain' | 'watch' | 'review'>('plain')
	autoCursor = $state(-1)
	plainAutoSeen = $state(false)
	watchAutoSeen = $state(false)
	agreed = $state(false)
	rules = $state<RuleResult[]>([])
	jobDone = $state(false)
	error = $state('')
	abortMessage = $state('')
	abortKind = $state<AbortKind | ''>('')
	abortTitle = $state('')
	premierePending = $state(false)
	submitting = $state(false)
	advancing = $state(false)
	localVideoUrl = $state('')
	jobId = ''
	watchId = 0

	releaseLocalVideo = () => {
		if (this.localVideoUrl === '') return
		URL.revokeObjectURL(this.localVideoUrl)
		this.localVideoUrl = ''
	}

	currentRuleId = () => {
		if (this.category === '') return ''
		if (this.autoCursor >= 0) return this.activeFixes()[this.autoCursor]?.id ?? ''
		return this.pledgeList()[this.pledgeIndex]?.id ?? ''
	}

	reviewPath = () => (this.source === 'youtube' ? `/review/${this.jobId}` : '/review/file')

	finishPath = () => (this.source === 'youtube' ? `/finish/${this.jobId}` : '/finish/file')

	// 自動判定で指摘したルールは指摘カードで同意済みなので、視聴後の誓約には出さない
	reviewPledges = () => {
		if (this.category === '') return []
		return reviewPledgesFor(
			this.category,
			this.rules.filter((rule) => rule.status !== 'fix').map((rule) => rule.id),
			this.source,
		)
	}

	pledgeList = () => {
		if (this.category === '') return []
		if (this.pledgeStep === 'review') return this.reviewPledges()
		if (this.pledgeStep === 'watch') return watchPledgesFor(this.category, this.source)
		return plainPledgesFor(this.category, this.source)
	}

	plainFixes = () => this.autoFixes().filter((rule) => !watchesVideo(rule.id))

	watchFixes = () => this.autoFixes().filter((rule) => watchesVideo(rule.id))

	activeFixes = () => (this.pledgeStep === 'watch' ? this.watchFixes() : this.plainFixes())

	start = async (file: File | null, options?: { premiereFile?: boolean }) => {
		if (this.submitting || this.category === '') return
		const premiereFile = options?.premiereFile === true
		const source: SourceKind = premiereFile ? 'youtube' : this.source
		const youtubeUrl = this.youtubeUrl.trim()
		const rawUrl = this.source === 'youtube' || premiereFile ? this.rawUrl.trim() : ''
		if (!premiereFile && source === 'file' && !file) return
		if (source === 'youtube' && (youtubeUrl === '' || rawUrl === '')) return
		if (premiereFile && !file) return

		this.submitting = true
		this.error = ''
		this.abortMessage = ''
		this.abortKind = ''
		this.abortTitle = ''
		if (!premiereFile) this.premierePending = false
		this.pledgeIndex = 0
		this.pledgeStep = 'plain'
		this.autoCursor = -1
		this.plainAutoSeen = false
		this.watchAutoSeen = false
		this.agreed = false
		this.rules = []
		this.jobDone = false
		this.jobId = ''
		this.advancing = false

		const body = new FormData()
		body.set('category', this.category)
		body.set('source', source)
		if (source === 'youtube') {
			body.set('youtube_url', youtubeUrl)
			body.set('raw_url', rawUrl)
		}
		if (file) body.set('file', file)

		try {
			if (source === 'youtube' && !premiereFile && isShortsUrl(youtubeUrl)) {
				this.abortReview(sheet.shortsUrlError, 'shorts')
				return
			}
			if (source === 'youtube' && !premiereFile) {
				await ensureDebugMode()
				const foundTitle = await fetchYoutubeTitle(youtubeUrl, this.category)
				if (!titleMatches(foundTitle, this.category)) {
					this.abortReview(sheet.titleUrlError, 'title', foundTitle)
					return
				}
			}
			this.releaseLocalVideo()
			if (file) this.localVideoUrl = URL.createObjectURL(file)
			this.stopWatch()
			const response = await fetch('/api/reviews', { method: 'POST', body })
			if (!response.ok) {
				const detail = await readErrorDetail(response)
				if (detail === shortsUrlCode) {
					this.abortReview(sheet.shortsUrlError, 'shorts')
					return
				}
				if (isNonPublicUrlCode(detail)) {
					this.abortReview(sheet.visibilityUrlError, 'visibility')
					return
				}
				if (detail === premiereUnavailableCode) {
					this.premierePending = true
					return
				}
				throw new Error('start')
			}
			this.premierePending = false
			// プレミア追加提出後はファイル審査として進める
			if (premiereFile) this.source = 'file'
			const payload = (await response.json()) as ReviewResource
			this.takeRawUrl(payload)
			this.jobId = payload.id
			this.phase = 'work'
			this.applyReview(payload)
			if (this.phase === 'work') await goto(this.reviewPath())
		} catch {
			this.releaseLocalVideo()
			this.error = sheet.startError
		} finally {
			this.submitting = false
		}
	}

	dismissPremiere = () => {
		this.premierePending = false
		this.error = ''
		this.submitting = false
	}

	continueWithPremiereFile = async (file: File) => {
		if (!file || this.submitting) return
		await this.start(file, { premiereFile: true })
	}

	stopWatch = () => {
		this.watchId += 1
	}

	autoFixes = () =>
		this.rules.filter(
			(rule) =>
				rule.id !== 'NO-SHORT' &&
				rule.id !== 'GEN-VISIBILITY' &&
				rule.status === 'fix',
		)

	abortReview = (message: string, kind: AbortKind = 'shorts', foundTitle = '') => {
		this.stopWatch()
		this.abortMessage = message
		this.abortKind = kind
		this.abortTitle = foundTitle
		this.autoCursor = -1
		this.agreed = false
	}

	confirmAbort = () => {
		if (this.abortMessage === '') return
		const working = this.phase === 'work'
		this.returnToIntake()
		if (working) void goto('/')
	}

	haltForShorts = () => {
		const shorts = this.rules.some((rule) => rule.id === 'NO-SHORT' && rule.status === 'fix')
		if (!shorts) return false
		this.abortReview(sheet.shortsUrlError, 'shorts')
		return true
	}

	haltForVisibility = () => {
		const blocked = this.rules.some((rule) => rule.id === 'GEN-VISIBILITY' && rule.status === 'fix')
		if (!blocked) return false
		this.abortReview(sheet.visibilityUrlError, 'visibility')
		return true
	}

	takeRawUrl = (payload: ReviewResource) => {
		if (typeof payload.raw_url === 'string') this.rawUrl = payload.raw_url
	}

	applyReview = (payload: ReviewResource) => {
		if (payload.status !== 'done') return
		this.rules = payload.rules
		this.jobDone = true
		if (this.haltForShorts()) return
		if (this.haltForVisibility()) return
		this.continueFromPledge()
	}

	// YouTube のときだけ Next のたびに同意を保存し、/review/:id と /finish/:id の復帰に使う。
	// ファイルは復帰できないので送らない。
	recordAgreement = async (key: string) => {
		if (this.jobId === '' || key === '') return false
		if (this.source !== 'youtube') return true
		try {
			const response = await fetch(`/api/reviews/${this.jobId}/agreements`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ rule_id: key }),
			})
			if (response.ok) return true
		} catch {
			// 下でまとめてエラー表示する
		}
		this.error = sheet.streamError
		return false
	}

	resume = async (id: string) => {
		const watchId = this.watchId
		let payload: ReviewResource | null = null
		try {
			const response = await fetch(`/api/reviews/${encodeURIComponent(id)}`)
			if (response.ok) payload = (await response.json()) as ReviewResource
		} catch {
			payload = null
		}
		if (watchId !== this.watchId) return
		if (!payload || payload.source !== 'youtube' || !isCategoryId(payload.category)) {
			this.returnToIntake()
			await goto('/', { replaceState: true })
			return
		}
		this.returnToIntake()
		this.category = payload.category
		this.source = 'youtube'
		this.youtubeUrl = payload.youtube_url ?? ''
		this.takeRawUrl(payload)
		this.jobId = payload.id
		this.phase = 'work'
		this.applyReview(payload)
		const agreed = new Set(payload.agreements ?? [])
		const limit = agreed.size + 1
		for (let step = 0; step < limit; step += 1) {
			if (this.phase !== 'work' || this.abortMessage !== '') break
			const key = this.currentRuleId()
			if (key === '' || !agreed.has(key)) break
			this.advanceAfterAgreement()
		}
		// 結果画面へは enterResult が遷移する
		if (this.abortMessage !== '' || this.phase !== 'work') return
		const path = this.reviewPath()
		if (window.location.pathname !== path) await goto(path, { replaceState: true })
	}

	refreshReview = async () => {
		if (this.jobDone) return true
		const id = this.jobId
		if (id === '') return false
		const watchId = this.watchId
		try {
			const response = await fetch(`/api/reviews/${id}`)
			if (watchId !== this.watchId) return false
			if (!response.ok) {
				this.error = sheet.streamError
				return false
			}
			const payload = (await response.json()) as ReviewResource
			if (watchId !== this.watchId) return false
			this.takeRawUrl(payload)
			this.applyReview(payload)
			return this.abortMessage === ''
		} catch {
			if (watchId !== this.watchId) return false
			this.error = sheet.streamError
			return false
		}
	}

	acknowledge = async () => {
		if (this.abortMessage !== '' || !this.agreed || !this.category || this.advancing) return
		this.advancing = true
		const watchId = this.watchId
		const key = this.currentRuleId()
		this.agreed = false
		this.error = ''
		try {
			const saved = await this.recordAgreement(key)
			if (watchId !== this.watchId || !saved) return
			const refreshed = await this.refreshReview()
			if (watchId !== this.watchId || !refreshed) return
			this.advanceAfterAgreement()
		} finally {
			if (watchId === this.watchId) this.advancing = false
		}
	}

	pollReview = async () => {
		if (this.advancing || this.jobDone || this.jobId === '') return
		this.advancing = true
		const watchId = this.watchId
		this.error = ''
		try {
			await this.refreshReview()
		} finally {
			if (watchId === this.watchId) this.advancing = false
		}
	}

	advanceAfterAgreement = () => {
		if (this.autoCursor >= 0) {
			this.autoCursor += 1
			if (this.autoCursor < this.activeFixes().length) return
			this.autoCursor = -1
			if (this.pledgeStep === 'plain') {
				this.plainAutoSeen = true
				this.enterWatch()
				return
			}
			this.watchAutoSeen = true
			this.enterReviewOrResult()
			return
		}
		this.pledgeIndex += 1
		this.continueFromPledge()
	}

	// YouTube は結果が出るまでプレビューへ進まない。
	awaitsPlainResults = () => this.source === 'youtube'

	continueFromPledge = () => {
		if (!this.category || this.phase === 'result' || this.abortMessage !== '' || this.autoCursor >= 0) return
		const list = this.pledgeList()
		if (this.pledgeIndex < list.length) return
		if (this.pledgeStep === 'plain') {
			if (!this.jobDone && this.awaitsPlainResults()) return
			if (!this.plainAutoSeen) {
				if (!this.jobDone) {
					this.plainAutoSeen = true
				} else if (this.plainFixes().length > 0) {
					this.autoCursor = 0
					this.agreed = false
					return
				} else {
					this.plainAutoSeen = true
				}
			}
			this.enterWatch()
			return
		}
		if (this.pledgeStep === 'watch') {
			if (!this.jobDone) return
			if (!this.watchAutoSeen) {
				if (this.watchFixes().length > 0) {
					this.autoCursor = 0
					this.agreed = false
					return
				}
				this.watchAutoSeen = true
			}
			this.enterReviewOrResult()
			return
		}
		this.enterResult()
	}

	enterWatch = () => {
		if (!this.category) return
		this.pledgeStep = 'watch'
		this.pledgeIndex = 0
		this.autoCursor = -1
		this.agreed = false
		if (watchPledgesFor(this.category, this.source).length > 0) return
		this.continueFromPledge()
	}

	enterReviewOrResult = () => {
		if (!this.category) return
		if (this.reviewPledges().length === 0) {
			this.enterResult()
			return
		}
		this.pledgeStep = 'review'
		this.pledgeIndex = 0
		this.autoCursor = -1
		this.agreed = false
	}

	back = () => {
		if (!this.category) return
		this.agreed = false
		if (this.autoCursor > 0) {
			this.autoCursor -= 1
			return
		}
		if (this.autoCursor === 0) {
			this.autoCursor = -1
			const list = this.pledgeList()
			if (list.length > 0) {
				this.pledgeIndex = list.length - 1
				return
			}
		} else if (this.pledgeIndex > 0) {
			this.pledgeIndex -= 1
			return
		}
		if (this.pledgeStep === 'review') {
			this.rewindToWatch()
			return
		}
		if (this.pledgeStep === 'watch') {
			this.rewindToPlain()
			return
		}
		this.returnToIntake()
		void goto('/')
	}

	rewindToWatch = () => {
		if (!this.category) return
		const watch = watchPledgesFor(this.category, this.source)
		const fixes = this.watchFixes()
		this.pledgeStep = 'watch'
		this.autoCursor = -1
		if (fixes.length > 0) {
			this.watchAutoSeen = false
			this.autoCursor = fixes.length - 1
			this.pledgeIndex = watch.length
			return
		}
		if (watch.length > 0) {
			this.pledgeIndex = watch.length - 1
			return
		}
		this.rewindToPlain()
	}

	rewindToPlain = () => {
		if (!this.category) return
		const plain = plainPledgesFor(this.category, this.source)
		const fixes = this.jobDone ? this.plainFixes() : []
		this.pledgeStep = 'plain'
		this.autoCursor = -1
		if (fixes.length > 0) {
			this.plainAutoSeen = false
			this.autoCursor = fixes.length - 1
			this.pledgeIndex = plain.length
			return
		}
		if (plain.length > 0) {
			this.pledgeIndex = plain.length - 1
			return
		}
		this.returnToIntake()
		void goto('/')
	}

	returnToIntake = () => {
		this.stopWatch()
		this.releaseLocalVideo()
		this.phase = 'intake'
		this.pledgeIndex = 0
		this.pledgeStep = 'plain'
		this.autoCursor = -1
		this.plainAutoSeen = false
		this.watchAutoSeen = false
		this.agreed = false
		this.rules = []
		this.jobDone = false
		this.jobId = ''
		this.advancing = false
		this.error = ''
		this.abortMessage = ''
		this.abortKind = ''
		this.abortTitle = ''
		this.premierePending = false
		this.submitting = false
	}

	enterResult = () => {
		if (this.phase === 'result') return
		this.releaseLocalVideo()
		this.phase = 'result'
		void goto(this.finishPath(), { replaceState: true })
	}

	retry = () => {
		this.returnToIntake()
		void goto('/')
	}
}
