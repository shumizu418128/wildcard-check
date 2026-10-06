<script lang="ts">
	import { sheet } from '$lib/sheet'
</script>

<div
	class="mt-6 flex flex-col items-center gap-8 sm:flex-row sm:items-end sm:justify-center"
	data-testid="visibility-compare"
	aria-label={sheet.visibilityCompareLabel}
>
	<figure class="flex w-40 flex-col items-center gap-2">
		<div
			class="flex h-24 w-full items-center justify-center rounded-lg border-2 border-destructive bg-[#fff1f0]"
		>
			<svg
				class="size-10 text-destructive"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				stroke-linecap="round"
				stroke-linejoin="round"
				aria-hidden="true"
			>
				<rect width="18" height="11" x="3" y="11" rx="2" ry="2" />
				<path d="M7 11V7a5 5 0 0 1 10 0v4" />
			</svg>
		</div>
		<figcaption class="text-center text-[12px] leading-4 font-semibold text-destructive">
			× {sheet.visibilityLocked}
		</figcaption>
	</figure>
	<figure class="flex w-40 flex-col items-center gap-2">
		<div
			class="flex h-24 w-full items-center justify-center rounded-lg border-2 border-ok bg-[#eaf6ee]"
		>
			<svg
				class="size-10 text-ok"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				stroke-linecap="round"
				stroke-linejoin="round"
				aria-hidden="true"
			>
				<circle cx="12" cy="12" r="10" />
				<path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20" />
				<path d="M2 12h20" />
			</svg>
		</div>
		<figcaption class="text-center text-[12px] leading-4 font-semibold text-ok">
			〇 {sheet.visibilityPublic}
		</figcaption>
	</figure>
</div>
