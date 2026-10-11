<script lang="ts">
	import { ruleLinesFor, rules } from '$lib/catalog'
	import { sheet } from '$lib/sheet'
	import type { ReviewSession } from '$lib/session.svelte'
	import ReviewDetail from '$lib/components/review-detail.svelte'
	import DialogClose from '$lib/components/dialog-close.svelte'

	let { session }: { session: ReviewSession } = $props()
	let dialog = $state<HTMLDialogElement | null>(null)

	$effect(() => {
		const node = dialog
		const open = session.abortMessage !== ''
		if (!node) return
		if (open && !node.open) node.showModal()
		if (!open && node.open) node.close()
	})

	const end = () => {
		session.confirmAbort()
	}

	const abortRuleIds = {
		shorts: 'NO-SHORT',
		visibility: 'GEN-VISIBILITY',
		title: 'TITLE-FORMAT',
	} as const
	const abortRuleId = $derived(
		session.abortKind === '' ? 'NO-SHORT' : abortRuleIds[session.abortKind],
	)
	const abortRule = $derived(ruleLinesFor(session.category, abortRuleId, session.source))
</script>

<dialog
	bind:this={dialog}
	class="m-auto w-[min(512px,calc(100%-48px))] rounded-lg border border-ink bg-background text-foreground backdrop:bg-ink/40"
	role="alertdialog"
	aria-modal="true"
	aria-labelledby="abort-title"
	aria-describedby="abort-body"
	oncancel={(event) => {
		event.preventDefault()
		end()
	}}
>
	{#if session.abortMessage !== ''}
		<div class="flex justify-end px-4 pt-4">
			<DialogClose label={sheet.close} onclick={end} />
		</div>
		<div class="px-8 pt-4 pb-8">
			<h2 id="abort-title" class="text-[24px] leading-8">{rules[abortRuleId].title}</h2>
			<div id="abort-body">
				<ReviewDetail
					id={abortRuleId}
					lines={abortRule.lines}
					notes={abortRule.notes}
					videoTitle={session.abortTitle}
				/>
			</div>
			<button type="button" class="btn-primary mt-8 w-full sm:w-auto" onclick={end}>
				{sheet.endReview}
			</button>
		</div>
	{/if}
</dialog>
