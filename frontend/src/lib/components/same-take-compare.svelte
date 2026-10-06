<script lang="ts">
	import { sheet } from '$lib/sheet'

	let { reviewId = '', videoUrl = '' }: { reviewId?: string; videoUrl?: string } = $props()

	type Part = 'intro' | 'routine'

	const placeholders: Record<Part, string> = {
		intro: '/placeholders/same-take-intro.svg',
		routine: '/placeholders/same-take-routine.svg',
	}
	// バックエンドの INTRO-SAME-TAKE と同じ秒数
	const partSeconds: Record<Part, number> = { intro: 2, routine: 60 }

	let captured = $state<Partial<Record<Part, string>>>({})
	let failed = $state<Partial<Record<Part, boolean>>>({})

	const captureFrame = (url: string, seconds: number) =>
		new Promise<string>((resolve, reject) => {
			const video = document.createElement('video')
			video.muted = true
			video.preload = 'auto'
			video.addEventListener(
				'loadedmetadata',
				() => {
					video.currentTime = Math.min(seconds, Math.max(video.duration - 0.1, 0))
				},
				{ once: true },
			)
			video.addEventListener(
				'seeked',
				() => {
					const canvas = document.createElement('canvas')
					canvas.width = video.videoWidth
					canvas.height = video.videoHeight
					const context = canvas.getContext('2d')
					if (!context) {
						reject(new Error('canvas'))
						return
					}
					context.drawImage(video, 0, 0)
					resolve(canvas.toDataURL('image/jpeg', 0.8))
					video.removeAttribute('src')
					video.load()
				},
				{ once: true },
			)
			video.addEventListener('error', () => reject(new Error('video')), { once: true })
			video.src = url
		})

	$effect(() => {
		captured = {}
		failed = {}
		const url = videoUrl
		if (reviewId !== '' || url === '') return
		let active = true
		void (async () => {
			for (const part of ['intro', 'routine'] as const) {
				try {
					const image = await captureFrame(url, partSeconds[part])
					if (active) captured = { ...captured, [part]: image }
				} catch {
					if (active) failed = { ...failed, [part]: true }
				}
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
