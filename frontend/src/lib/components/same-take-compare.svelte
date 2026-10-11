<script lang="ts">
	import { introFrameSeconds, routineFrameSeconds } from '$lib/clip-times'
	import { sheet } from '$lib/sheet'
	import { blobToDataUrl, closeVideo, jpegFromVideo, openVideo, seekVideo } from '$lib/video-frame'

	let { reviewId = '', videoUrl = '' }: { reviewId?: string; videoUrl?: string } = $props()

	type Part = 'intro' | 'routine'

	const placeholders: Record<Part, string> = {
		intro: '/placeholders/same-take-intro.svg',
		routine: '/placeholders/same-take-routine.svg',
	}
	// バックエンドの INTRO-SAME-TAKE と同じ秒数
	const partSeconds: Record<Part, number> = {
		intro: introFrameSeconds,
		routine: routineFrameSeconds,
	}

	let captured = $state<Partial<Record<Part, string>>>({})
	let failed = $state<Partial<Record<Part, boolean>>>({})

	$effect(() => {
		captured = {}
		failed = {}
		const url = videoUrl
		if (reviewId !== '' || url === '') return
		let active = true
		let video: HTMLVideoElement | null = null
		void (async () => {
			try {
				const opened = await openVideo(url)
				video = opened
				for (const part of ['intro', 'routine'] as const) {
					try {
						await seekVideo(opened, partSeconds[part])
						const image = await blobToDataUrl(await jpegFromVideo(opened))
						if (active) captured = { ...captured, [part]: image }
					} catch {
						if (active) failed = { ...failed, [part]: true }
					}
				}
			} catch {
				if (active) failed = { intro: true, routine: true }
			} finally {
				if (video) closeVideo(video)
			}
		})()
		return () => {
			active = false
		}
	})

	const frameSrc = (part: Part) => {
		if (failed[part]) return placeholders[part]
		if (reviewId !== '') return `/api/reviews/${encodeURIComponent(reviewId)}/frames/${part}`
		return captured[part] ?? placeholders[part]
	}

	const markFailed = (part: Part) => {
		failed = { ...failed, [part]: true }
	}
</script>

{#snippet frame(part: Part, alt: string)}
	<figure class="flex flex-col items-center gap-2">
		<div class="h-24 w-32 overflow-hidden rounded-lg border-2 border-line bg-[#d9d2c8]">
			<img
				src={frameSrc(part)}
				{alt}
				class="h-full w-full object-cover"
				width="128"
				height="96"
				data-testid="same-take-{part}"
				onerror={() => markFailed(part)}
			/>
		</div>
	</figure>
{/snippet}

<div
	class="mt-6 flex flex-col items-center gap-4"
	data-testid="same-take-compare"
	aria-label={sheet.sameTakeCompareLabel}
>
	<div class="flex items-center justify-center gap-4">
		{@render frame('intro', sheet.sameTakeIntro)}
		<span class="text-[20px] leading-6 text-ok" aria-hidden="true">↔</span>
		{@render frame('routine', sheet.sameTakeRoutine)}
	</div>
	<p class="text-center text-[12px] leading-4 text-muted">{sheet.sameTakeHint}</p>
</div>
