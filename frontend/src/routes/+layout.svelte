<script lang="ts">
	import './layout.css'
	import { setContext } from 'svelte'
	import favicon from '$lib/assets/favicon.svg'
	import { rules } from '$lib/catalog'
	import EndReviewDialog from '$lib/components/end-review-dialog.svelte'
	import PremiereFileDialog from '$lib/components/premiere-file-dialog.svelte'
	import { editionLabel, sheet } from '$lib/sheet'
	import { ReviewSession, reviewSessionKey } from '$lib/session.svelte'

	let { children } = $props()
	const session = new ReviewSession()
	setContext(reviewSessionKey, session)

	const workHeading = () => {
		if (session.autoCursor >= 0) {
			const rule = session.activeFixes()[session.autoCursor]
			return rules[rule?.id ?? '']?.title ?? ''
		}
		return session.pledgeList()[session.pledgeIndex]?.title ?? ''
	}

	const documentTitle = $derived.by(() => {
		if (session.phase === 'intake') return sheet.title
		if (session.phase === 'result') return `${sheet.resultLead} — ${sheet.title}`
		const heading = workHeading()
		if (heading !== '') return `${heading} — ${sheet.title}`
		if (!session.jobDone) return `${sheet.pleaseWait} — ${sheet.title}`
		return sheet.title
	})

	const warnBeforeLeave = (event: BeforeUnloadEvent) => {
		if (session.phase !== 'work') return
		event.preventDefault()
	}
</script>

<svelte:window onbeforeunload={warnBeforeLeave} />

<svelte:head>
	<link rel="icon" href={favicon} />
	<title>{documentTitle}</title>
</svelte:head>

<div class="min-h-screen bg-background">
	<header class="flex items-center bg-ink px-4 py-4 text-white sm:px-8">
		<p class="text-[16px] leading-6 font-semibold">{editionLabel}</p>
	</header>
	<main class="mx-auto flex w-full max-w-160 flex-col px-4 py-8 sm:px-8 sm:py-12">
		{@render children()}
	</main>
</div>
<EndReviewDialog {session} />
<PremiereFileDialog {session} />
