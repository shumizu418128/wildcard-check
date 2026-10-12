<script lang="ts">
	import { sheet } from '$lib/sheet'
	import type { ReviewSession } from '$lib/session.svelte'
	import VideoPreview from '$lib/components/video-preview.svelte'

	let { session }: { session: ReviewSession } = $props()

	const pollMs = 2000
	let elapsed = $state(0)

	const elapsedLabel = () => {
		const minutes = Math.floor(elapsed / 60)
		const seconds = String(elapsed % 60).padStart(2, '0')
		return `${minutes}:${seconds}`
	}

	$effect(() => {
		const startedAt = Date.now()
		const tick = setInterval(() => {
			elapsed = Math.floor((Date.now() - startedAt) / 1000)
		}, 1000)
		const poll = setInterval(() => {
			void session.pollReview()
		}, pollMs)
		return () => {
			clearInterval(tick)
			clearInterval(poll)
		}
	})
</script>

<div class="mt-8" data-testid="please-wait" aria-busy="true">
	<div class="flex items-center gap-4 text-ink">
		<span class="wait-spinner" data-testid="wait-spinner" aria-hidden="true"></span>
		<p class="text-[24px] leading-8" aria-live="polite">{sheet.pleaseWait}</p>
	</div>
	<p class="mt-2 text-[16px] leading-6 text-muted">{sheet.pleaseWaitHint}</p>
	<p class="mt-2 text-[16px] leading-6 text-muted tabular-nums" data-testid="wait-elapsed">
		{sheet.waitElapsed}
		<span class="font-semibold text-ink">{elapsedLabel()}</span>
	</p>
	<VideoPreview {session} showSubmitted />
</div>
