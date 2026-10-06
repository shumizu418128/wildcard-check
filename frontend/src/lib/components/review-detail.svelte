<script lang="ts">
	import { ruleDetail, type Verdict } from '$lib/catalog'
	import { sheet } from '$lib/sheet'
	import FixText from '$lib/components/fix-text.svelte'
	import FormatCompare from '$lib/components/format-compare.svelte'
	import RuleLines from '$lib/components/rule-lines.svelte'
	import SameTakeCompare from '$lib/components/same-take-compare.svelte'
	import VisibilityCompare from '$lib/components/visibility-compare.svelte'

	let {
		id,
		lines,
		notes = [],
		videoTitle = '',
		reviewId = '',
		videoUrl = '',
	}: {
		id: string
		lines: Verdict[]
		notes?: string[]
		videoTitle?: string
		reviewId?: string
		videoUrl?: string
	} = $props()
</script>

<div class="mt-6">
	{#if id === 'TITLE-FORMAT' && videoTitle !== ''}
		<p class="text-[16px] leading-6 text-muted">{sheet.foundTitle}</p>
		<p class="mt-2 text-[24px] leading-8 font-semibold wrap-break-word" data-testid="found-title">
			{videoTitle}
		</p>
	{/if}
	<h2 class="eyebrow {id === 'TITLE-FORMAT' && videoTitle !== '' ? 'mt-8' : ''}">{sheet.autoHeading}</h2>
	<div class="mt-2 rounded-lg bg-[#fff1f0] p-4 text-destructive">
		<div class="flex items-start gap-2">
			<p class="w-8 shrink-0 text-[16px] leading-6">×</p>
			<div class="min-w-0">
				<FixText {...ruleDetail(id)} flush />
			</div>
		</div>
	</div>
	{#if id === 'GEN-YOUTUBE'}
		<FormatCompare />
	{/if}
	{#if id === 'GEN-VISIBILITY'}
		<VisibilityCompare />
	{/if}
	{#if id === 'INTRO-SAME-TAKE'}
		<SameTakeCompare {reviewId} {videoUrl} />
	{/if}
</div>
{#if lines.length > 0 || notes.length > 0}
	<section class="mt-8 border-t border-line pt-6">
		<h2 class="eyebrow">{sheet.ruleHeading}</h2>
		<RuleLines {lines} {notes} />
	</section>
{/if}
