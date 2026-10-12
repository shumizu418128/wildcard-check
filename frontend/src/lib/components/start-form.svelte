<script lang="ts">
	import { untrack } from 'svelte'
	import { categories, sheet, type CategoryId, type SourceKind } from '$lib/sheet'
	import type { ReviewSession } from '$lib/session.svelte'
	import BusyButton from '$lib/components/busy-button.svelte'
	import { Label } from '$lib/components/ui/label'

	let { session }: { session: ReviewSession } = $props()
	let files = $state<FileList | undefined>(undefined)
	let category = $state<CategoryId | ''>(untrack(() => session.category))
	let source = $state<SourceKind>(untrack(() => session.source))
	let youtubeUrl = $state(untrack(() => session.youtubeUrl))
	let rawUrl = $state(untrack(() => session.rawUrl))

	const onSubmit = (event: SubmitEvent) => {
		event.preventDefault()
		session.category = category
		session.source = source
		session.youtubeUrl = youtubeUrl
		session.rawUrl = source === 'youtube' ? rawUrl : ''
		void session.start(files?.item(0) ?? null)
	}

	const applyCategory = (event: Event) => {
		const target = event.currentTarget as HTMLSelectElement
		category = target.value as CategoryId | ''
	}

	const sourceCard = (active: boolean) =>
		active ? 'border-ink bg-ink text-white' : 'border-line bg-surface text-ink'
	const sourceLead = (active: boolean) => (active ? 'text-white/70' : 'text-muted')
	const sourceIcon = (active: boolean) => (active ? 'text-white' : 'text-ink')
</script>

<form onsubmit={onSubmit} class="mt-8 flex flex-col gap-8">
	<div>
		<Label for="category" class="eyebrow eyebrow-required">{sheet.category}</Label>
		<select
			id="category"
			class="field-input mt-2"
			required
			onchange={applyCategory}
			onchangecapture={applyCategory}
		>
			<option value="" selected={category === ''}>{sheet.categoryPlaceholder}</option>
			{#each categories as item (item.id)}
				<option value={item.id} selected={category === item.id}>{item.label}</option>
			{/each}
		</select>
	</div>

	<div>
		<Label class="eyebrow" id="source-label">{sheet.sourceKind}</Label>
		<div class="mt-2 grid gap-2 sm:grid-cols-2" role="group" aria-labelledby="source-label">
			<button
				type="button"
				aria-pressed={source === 'file'}
				class="flex min-h-28 flex-col justify-center gap-2 rounded-lg border-2 px-4 py-4 text-left transition-colors {sourceCard(
					source === 'file',
				)}"
				onclick={() => {
					source = 'file'
				}}
			>
				<svg
					class="size-8 {sourceIcon(source === 'file')}"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					stroke-linecap="round"
					stroke-linejoin="round"
					aria-hidden="true"
				>
					<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
				</svg>
				<span class="text-[16px] leading-6 font-semibold">{sheet.sourceFile}</span>
				<span class="text-[12px] leading-4 font-normal {sourceLead(source === 'file')}">
					{sheet.leadFile}
				</span>
			</button>
			<button
				type="button"
				aria-pressed={source === 'youtube'}
				class="flex min-h-28 flex-col justify-center gap-2 rounded-lg border-2 px-4 py-4 text-left transition-colors {sourceCard(
					source === 'youtube',
				)}"
				onclick={() => {
					source = 'youtube'
				}}
			>
				<svg
					class="size-8 {sourceIcon(source === 'youtube')}"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					stroke-linecap="round"
					stroke-linejoin="round"
					aria-hidden="true"
				>
					<circle cx="12" cy="12" r="9" />
					<path d="M10 9.5v5l4.5-2.5z" fill="currentColor" stroke="none" />
				</svg>
				<span class="text-[16px] leading-6 font-semibold">{sheet.sourceYoutube}</span>
				<span class="text-[12px] leading-4 font-normal {sourceLead(source === 'youtube')}">
					{sheet.leadYoutube}
				</span>
			</button>
		</div>
	</div>

	{#if source === 'file'}
		<div>
			<Label for="video-file" class="eyebrow eyebrow-required">{sheet.fileLabel}</Label>
			<div class="field-file relative mt-2">
				<div class="field-shell pointer-events-none justify-between">
					<span class="truncate">{files?.item(0)?.name ?? sheet.fileChoose}</span>
					<svg
						class="size-6 shrink-0 text-primary"
						xmlns="http://www.w3.org/2000/svg"
						viewBox="0 -960 960 960"
						fill="currentColor"
						aria-hidden="true"
					>
						<path
							d="M440-320v-326L336-542l-56-58 200-200 200 200-56 58-104-104v326h-80ZM240-160q-33 0-56.5-23.5T160-240v-120h80v120h480v-120h80v120q0 33-23.5 56.5T720-160H240Z"
						/>
					</svg>
				</div>
				<input
					id="video-file"
					class="absolute inset-0 h-12 cursor-pointer opacity-0"
					type="file"
					accept=".mp4,.mov,.webm,video/mp4,video/quicktime,video/webm"
					required
					bind:files
				/>
			</div>
		</div>
	{:else}
		<div>
			<Label for="youtube-url" class="eyebrow eyebrow-required">{sheet.urlLabel}</Label>
			<input
				id="youtube-url"
				class="field-input mt-2"
				type="url"
				placeholder={sheet.urlPlaceholder}
				required
				bind:value={youtubeUrl}
			/>
		</div>
		<div>
			<Label for="raw-url" class="eyebrow eyebrow-required">{sheet.rawLabel}</Label>
			<input
				id="raw-url"
				class="field-input mt-2"
				type="url"
				placeholder={sheet.rawPlaceholder}
				required
				bind:value={rawUrl}
			/>
		</div>
	{/if}

	{#if session.preparing}
		<p class="text-[16px] leading-6 text-muted" data-testid="preparing-clips">{sheet.preparingClips}</p>
	{/if}

	{#if session.error}
		<p class="text-[16px] leading-6 text-destructive" role="alert">{session.error}</p>
	{/if}

	<BusyButton type="submit" class="btn-primary w-full sm:w-auto" busy={session.submitting}>
		{sheet.start}
	</BusyButton>
</form>
