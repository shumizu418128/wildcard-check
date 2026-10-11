<script lang="ts">
	import { tick, type Snippet } from 'svelte'
	import { ruleLinesFor, rules } from '$lib/catalog'
	import { categoryLabel, sheet } from '$lib/sheet'
	import type { ReviewSession } from '$lib/session.svelte'
	import BusyButton from '$lib/components/busy-button.svelte'
	import ReviewDetail from '$lib/components/review-detail.svelte'
	import RuleLines from '$lib/components/rule-lines.svelte'
	import SameTakeCompare from '$lib/components/same-take-compare.svelte'
	import { Label } from '$lib/components/ui/label'

	let { session }: { session: ReviewSession } = $props()
	let agreed = $state(false)
	let headingEl = $state<HTMLHeadingElement | null>(null)

	const pledgeList = () => session.pledgeList()
	const pledge = () => pledgeList()[session.pledgeIndex]
	const autoError = () => {
		if (session.autoCursor < 0) return undefined
		return session.activeFixes()[session.autoCursor]
	}
	$effect(() => {
		void session.pledgeIndex
		void session.autoCursor
		void session.pledgeStep
		agreed = false
		void tick().then(() => {
			headingEl?.focus()
		})
	})
	const frameReviewId = () => (session.source === 'youtube' ? session.jobId : '')
	const agreeAndNext = () => {
		if (session.advancing) return
		session.agreed = true
		void session.acknowledge()
	}
	const goBack = () => {
		if (session.advancing) return
		session.back()
		agreed = false
	}
</script>

{#snippet stepFrame(title: string, body: Snippet, testId?: string)}
	<article class="mt-8" data-testid={testId}>
		{#if session.category}
			<p class="text-[16px] leading-6 font-medium text-ink">{categoryLabel(session.category)}</p>
		{/if}
		<h1
			bind:this={headingEl}
			tabindex="-1"
			class="mt-2 text-[28px] leading-9 font-semibold outline-none sm:text-[32px] sm:leading-10"
		>
			{title}
		</h1>
		{@render body()}
		<div class="mt-8 flex items-center gap-4">
			<input
				id="agree"
				type="checkbox"
				class="size-6 shrink-0 accent-[#cc4800]"
				bind:checked={agreed}
			/>
			<Label for="agree">{sheet.agree}</Label>
		</div>
		<div class="mt-8 flex flex-col gap-2 sm:flex-row sm:gap-4">
			<button type="button" class="btn-secondary w-full sm:w-auto" disabled={session.advancing} onclick={goBack}>
				{sheet.back}
			</button>
			<BusyButton
				class="btn-primary w-full sm:w-auto"
				disabled={!agreed}
				busy={session.advancing}
				onclick={agreeAndNext}
			>
				{sheet.next}
			</BusyButton>
		</div>
	</article>
{/snippet}

{#if session.autoCursor >= 0}
	{@const rule = autoError()}
	{#if rule}
		{@const detail = ruleLinesFor(session.category, rule.id, session.source)}
		{#snippet body()}
			<ReviewDetail
				id={rule.id}
				lines={detail.lines}
				notes={detail.notes}
				reviewId={frameReviewId()}
				videoUrl={session.localVideoUrl}
				rawUrl={session.rawUrl}
			/>
		{/snippet}
		{@render stepFrame(rules[rule.id]?.title ?? '', body, 'auto-error')}
	{/if}
{:else if pledge()}
	{@const current = pledge()}
	{@const rule = session.rules.find((item) => item.id === current.id)}
	{#snippet body()}
		{#if current.id === 'SUB-RAW' && session.rawUrl !== ''}
			<p class="mt-6 text-[16px] leading-6 text-muted">{sheet.foundRaw}</p>
			<p class="mt-2 text-[24px] leading-8 font-semibold break-all" data-testid="found-raw">
				{session.rawUrl}
			</p>
		{/if}
		{#if current.lead}
			<p class="mt-6 text-[16px] leading-6 text-muted">{current.lead}</p>
		{/if}
		{#if session.pledgeStep === 'review' && rule && rule.status === 'fix'}
			<ReviewDetail
				id={rule.id}
				lines={current.lines}
				notes={current.notes}
				reviewId={frameReviewId()}
				videoUrl={session.localVideoUrl}
			/>
		{:else}
			{#if current.id === 'INTRO-SAME-TAKE'}
				<SameTakeCompare reviewId={frameReviewId()} videoUrl={session.localVideoUrl} />
			{/if}
			<RuleLines lines={current.lines} notes={current.notes} />
		{/if}
	{/snippet}
	{@render stepFrame(current.title, body)}
{:else if !session.jobDone}
	<p class="mt-8 text-[24px] leading-8" data-testid="please-wait" aria-live="polite">
		{sheet.pleaseWait}
	</p>
	<BusyButton
		class="btn-primary mt-8 w-full sm:w-auto"
		busy={session.advancing}
		onclick={() => {
			void session.pollReview()
		}}
	>
		{sheet.next}
	</BusyButton>
{/if}

{#if session.error}
	<p class="mt-6 text-[16px] leading-6 text-destructive" role="alert">{session.error}</p>
{/if}
