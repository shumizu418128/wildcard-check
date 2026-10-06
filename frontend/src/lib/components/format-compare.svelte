<script lang="ts">
	import { sheet } from '$lib/sheet'

	const shortsLogo = '/logos/youtube-shorts.png'
	const youtubeLogo = '/logos/youtube.png'
</script>

<div
	class="mt-6 flex flex-col items-center gap-8 sm:flex-row sm:items-end sm:justify-center"
	data-testid="format-compare"
	aria-label={sheet.formatCompareLabel}
>
	<figure class="flex w-40 flex-col items-center gap-2">
		<div
			class="flex h-24 w-full items-center justify-center rounded-lg border-2 border-destructive bg-[#fff1f0] px-4"
		>
			<img
				src={shortsLogo}
				alt=""
				class="max-h-16 w-auto max-w-full object-contain"
				width="160"
				height="64"
			/>
		</div>
		<figcaption class="text-[12px] leading-4 font-semibold text-destructive">
			× {sheet.formatShort}
		</figcaption>
	</figure>
	<figure class="flex w-40 flex-col items-center gap-2">
		<div
			class="flex h-24 w-full items-center justify-center rounded-lg border-2 border-ok bg-[#eaf6ee] px-4"
		>
			<img
				src={youtubeLogo}
				alt=""
				class="max-h-16 w-auto max-w-full object-contain"
				width="64"
				height="64"
			/>
		</div>
		<figcaption class="text-[12px] leading-4 font-semibold text-ok">
			〇 {sheet.formatNormal}
		</figcaption>
	</figure>
</div>
