<script lang="ts">
	import { untrack } from 'svelte'
	import { categories, sheet, type CategoryId } from '$lib/sheet'
	import type { ReviewSession } from '$lib/session.svelte'
	import BusyButton from '$lib/components/busy-button.svelte'
	import { Label } from '$lib/components/ui/label'

	let { session }: { session: ReviewSession } = $props()
	let files = $state<FileList | undefined>(undefined)
	let category = $state<CategoryId | ''>(untrack(() => session.category))
	let youtubeUrl = $state(untrack(() => session.youtubeUrl))
	let rawUrl = $state(untrack(() => session.rawUrl))

	const hasYoutubeUrl = $derived(youtubeUrl.trim() !== '')

	const onSubmit = (event: SubmitEvent) => {
		event.preventDefault()
		session.category = category
		session.source = hasYoutubeUrl ? 'youtube' : 'file'
		session.youtubeUrl = youtubeUrl
		session.rawUrl = hasYoutubeUrl ? rawUrl : ''
		void session.start(files?.item(0) ?? null)
	}

	const applyCategory = (event: Event) => {
		const target = event.currentTarget as HTMLSelectElement
		category = target.value as CategoryId | ''
	}
</script>

<form onsubmit={onSubmit} class="mt-8 flex flex-col gap-8">
	<div>
		<Label for="category" class="eyebrow eyebrow-required">{sheet.category}</Label>
		<select
			id="category"
			class="field-input mt-2"
			required
			onchange={applyCategory}
		>
			<option value="" selected={category === ''}>{sheet.categoryPlaceholder}</option>
			{#each categories as item (item.id)}
				<option value={item.id} selected={category === item.id}>{item.label}</option>
			{/each}
		</select>
	</div>

	<div>
		<Label for="video-file" class="eyebrow eyebrow-required">{sheet.fileLabel}</Label>
		<div class="field-file relative mt-2">
			<div class="field-drop pointer-events-none">
				<svg
					class="size-8 shrink-0 text-primary"
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 -960 960 960"
					fill="currentColor"
					aria-hidden="true"
				>
					<path
						d="M440-320v-326L336-542l-56-58 200-200 200 200-56 58-104-104v326h-80ZM240-160q-33 0-56.5-23.5T160-240v-120h80v120h480v-120h80v120q0 33-23.5 56.5T720-160H240Z"
					/>
				</svg>
				<span class="max-w-full truncate font-semibold">
					{files?.item(0)?.name ?? sheet.fileChoose}
				</span>
				<span class="text-[12px] leading-4 text-muted">{sheet.fileHint}</span>
			</div>
			<input
				id="video-file"
				class="absolute inset-0 h-full w-full cursor-pointer opacity-0"
				type="file"
				accept=".mp4,.mov,.webm,video/mp4,video/quicktime,video/webm"
				required
				bind:files
			/>
		</div>
	</div>

	<div>
		<Label for="youtube-url" class="eyebrow">{sheet.urlLabel} {sheet.urlOptional}</Label>
		<input
			id="youtube-url"
			class="field-input mt-2"
			type="url"
			placeholder={sheet.urlPlaceholder}
			aria-describedby="youtube-url-hint"
			bind:value={youtubeUrl}
		/>
		<p id="youtube-url-hint" class="mt-2 text-[12px] leading-4 text-muted">{sheet.urlHint}</p>
	</div>

	{#if hasYoutubeUrl}
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

	{#if session.error}
		<p class="text-[16px] leading-6 text-destructive" role="alert">{session.error}</p>
	{/if}

	<BusyButton type="submit" class="btn-primary w-full sm:w-auto" busy={session.submitting}>
		{sheet.start}
	</BusyButton>
</form>
