<script lang="ts">
	import {
		keepVideoPledge,
		plainPledgesFor,
		pledgesFor,
		rules,
		watchesVideo,
		watchPledgesFor,
	} from '$lib/catalog'
	import { sheet, submissionUrl } from '$lib/sheet'
	import type { ReviewSession } from '$lib/session.svelte'
	import DialogClose from '$lib/components/dialog-close.svelte'
	import RuleLines from '$lib/components/rule-lines.svelte'

	let { session }: { session: ReviewSession } = $props()
	let finalOpen = $state(false)
	let confirmText = $state('')
	let dialog = $state<HTMLDialogElement | null>(null)

	$effect(() => {
		const node = dialog
		const open = finalOpen
		if (!node) return
		if (open && !node.open) node.showModal()
		if (!open && node.open) node.close()
	})

	const lettersOnly = (value: string) => value.toUpperCase().replace(/[^A-Z ]/g, '')

	const closeFinal = () => {
		finalOpen = false
		confirmText = ''
	}

	const onConfirmBeforeInput = (event: Event) => {
		if (!(event instanceof InputEvent) || event.data === null) return
		if (event.inputType !== 'insertText' || event.data.length !== 1) return
		if (!/^[A-Za-z ]$/.test(event.data)) event.preventDefault()
	}

	const onConfirmInput = (event: Event) => {
		const input = event.currentTarget
		if (!(input instanceof HTMLInputElement)) return
		const cursor = input.selectionStart ?? input.value.length
		const sanitized = lettersOnly(input.value)
		const nextCursor = lettersOnly(input.value.slice(0, cursor)).length
		confirmText = sanitized
		input.value = sanitized
		input.setSelectionRange(nextCursor, nextCursor)
	}

	const autoRules = () => [
		...session.rules.filter((rule) => rule.status === 'fix' && !watchesVideo(rule.id)),
		...session.rules.filter((rule) => rule.status === 'fix' && watchesVideo(rule.id)),
	]
	const shorts = () => session.rules.some((rule) => rule.id === 'NO-SHORT' && rule.status === 'fix')
	const nonPublic = () =>
		session.rules.some((rule) => rule.id === 'GEN-VISIBILITY' && rule.status === 'fix')
	// /review と同じ順。冒頭の誓約、動画を見ない合格、視聴前の誓約、視聴後の項目。
	const noted = () => {
		if (!session.category) return []
		const category = session.category
		const rows: { id: string; title: string }[] = []
		const seen = new Set<string>()
		const add = (id: string, title: string) => {
			if (title === '' || seen.has(id)) return
			seen.add(id)
			rows.push({ id, title })
		}
		const pledgeById = new Map(
			pledgesFor(category, session.source).map((pledge) => [pledge.id, pledge]),
		)

		for (const pledge of plainPledgesFor(category, session.source)) add(pledge.id, pledge.title)
		for (const rule of session.rules) {
			if (watchesVideo(rule.id) || rule.status !== 'clear') continue
			add(rule.id, rules[rule.id]?.title ?? '')
		}
		for (const pledge of watchPledgesFor(category, session.source)) add(pledge.id, pledge.title)
		for (const rule of session.rules) {
			if (!watchesVideo(rule.id)) continue
			const pledge = pledgeById.get(rule.id)
			if (pledge) {
				add(pledge.id, pledge.title)
				continue
			}
			if (rule.status === 'clear') add(rule.id, rules[rule.id]?.title ?? '')
		}
		for (const pledge of pledgesFor(category, session.source)) add(pledge.id, pledge.title)
		return rows
	}
	const openRows = () => {
		if (session.source !== 'file') return [] as { id: string; title: string }[]
		return [
			{ id: 'FILE-POST', title: sheet.filePost },
			{ id: 'FILE-RESUBMIT', title: sheet.fileResubmit },
		]
	}
	const passed = () => session.source !== 'file' && !shorts() && !nonPublic()
	const showLead = () => passed() || session.source === 'file'
</script>

<div data-testid="outcome">
	{#if showLead()}
		<h1 class="mt-4 text-[28px] leading-9 font-semibold sm:text-[32px] sm:leading-10">
			{sheet.resultLead}
		</h1>
	{/if}
	{#if session.source === 'file'}
		<p class="mt-4 text-[16px] leading-6 text-muted">{sheet.fileBody}</p>
	{/if}

	{#if autoRules().length > 0}
		<section class="mt-12">
			<h2 class="eyebrow">{sheet.autoHeading}</h2>
			<div class="mt-4 flex flex-col gap-4">
				{#each autoRules() as rule (rule.id)}
					<article class="rounded-lg bg-[#fff1f0] p-4">
						<h3 class="text-[24px] leading-8">
							<span class="text-destructive">×</span>
							{rules[rule.id]?.title ?? ''}
						</h3>
						<p class="mt-4 text-[16px] leading-6">{sheet.autoOwnRisk}</p>
					</article>
				{/each}
			</div>
		</section>
	{/if}

	<section class="mt-12">
		{#if openRows().length > 0}
			<h2 class="eyebrow">{sheet.openHeading}</h2>
			<ul class="mt-4 flex flex-col gap-2">
				{#each openRows() as pledge (pledge.id)}
					<li
						class="flex items-center gap-4 rounded-lg bg-soft px-4 py-6"
						data-testid="open-step"
					>
						<span class="h-8 w-1 shrink-0 rounded-sm bg-muted" aria-hidden="true"></span>
						<span class="min-w-0 flex-1 text-[20px] leading-7 font-semibold">{pledge.title}</span>
						<span
							class="shrink-0 font-mono text-[12px] leading-4 tracking-[0.04em] text-muted uppercase"
							>{sheet.pledgeOpen}</span
						>
					</li>
				{/each}
			</ul>
			<h2 class="eyebrow mt-12">{sheet.pledgeHeading}</h2>
		{:else}
			<h2 class="eyebrow">{sheet.pledgeHeading}</h2>
		{/if}
		<ul class="mt-4 border-t border-line" data-testid="agreed-list">
			{#each noted() as pledge (pledge.id)}
				<li class="flex items-center gap-4 border-b border-line py-4">
					<span class="h-6 w-1 shrink-0 rounded-sm bg-primary" aria-hidden="true"></span>
					<span class="min-w-0 flex-1 text-[16px] leading-6">{pledge.title}</span>
					<span
						class="shrink-0 font-mono text-[12px] leading-4 tracking-[0.04em] text-primary-ink uppercase"
						>{sheet.pledgeNoted}</span
					>
				</li>
			{/each}
		</ul>
	</section>

	<div class="mt-12 flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:gap-4">
		<button type="button" class="btn-secondary w-full sm:w-auto" onclick={session.retry}>
			{sheet.again}
		</button>
		{#if passed() && !finalOpen}
			<button type="button" class="btn-primary w-full sm:w-auto" onclick={() => (finalOpen = true)}>
				{sheet.next}
			</button>
		{/if}
	</div>
	{#if passed()}
		<dialog
			bind:this={dialog}
			class="m-auto max-h-[calc(100%-48px)] w-[min(640px,calc(100%-48px))] overflow-hidden rounded-lg border border-ink bg-background text-foreground open:flex open:flex-col backdrop:bg-ink/40"
			aria-labelledby="keep-video-title"
			closedby="none"
			oncancel={(event) => {
				event.preventDefault()
			}}
		>
			<div class="flex shrink-0 justify-end px-4 pt-4">
				<DialogClose label={sheet.close} onclick={closeFinal} />
			</div>
			<div class="min-h-0 overflow-y-auto px-8 pt-4 pb-8">
				<label id="keep-video-title" for="keep-video" class="text-[16px] leading-6">
					{sheet.finalReviewLead}
				</label>
				<p class="mt-4 text-[16px] leading-6 font-bold">{sheet.keepVideoPhrase}</p>
				<input
					id="keep-video"
					class="field-input mt-4"
					type="text"
					placeholder="I WILL ..."
					value={confirmText}
					maxlength={sheet.keepVideoPhrase.length}
					autocomplete="off"
					autocapitalize="characters"
					spellcheck="false"
					onbeforeinput={onConfirmBeforeInput}
					oninput={onConfirmInput}
				/>
				{#if confirmText === sheet.keepVideoPhrase}
					<section class="mt-8 pt-8">
						<h2 class="text-[24px] leading-8">{keepVideoPledge.title}</h2>
						<RuleLines lines={keepVideoPledge.lines} notes={keepVideoPledge.notes} expanded />
					</section>
				{/if}
				<div class="mt-8 flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center sm:gap-4">
					<button type="button" class="btn-secondary w-full sm:w-auto" onclick={closeFinal}>
						{sheet.back}
					</button>
					{#if confirmText === sheet.keepVideoPhrase}
						{#if submissionUrl}
							<a
								class="btn-primary w-full sm:w-auto"
								href={submissionUrl}
								target="_blank"
								rel="noopener noreferrer"
							>
								{sheet.continueSubmission}
								<span class="sr-only"> (opens in a new tab)</span>
							</a>
						{:else}
							<button type="button" class="btn-primary w-full opacity-50 sm:w-auto" disabled>
								{sheet.continueSubmission}
							</button>
							<p class="text-[16px] leading-6">{sheet.submissionMissing}</p>
						{/if}
					{/if}
				</div>
			</div>
		</dialog>
	{/if}
</div>
