<script lang="ts">
	import { sheet } from '$lib/sheet'
	import type { ReviewSession } from '$lib/session.svelte'
	import DialogClose from '$lib/components/dialog-close.svelte'
	import { Label } from '$lib/components/ui/label'
	import BusyButton from '$lib/components/busy-button.svelte'

	let { session }: { session: ReviewSession } = $props()
	let dialog = $state<HTMLDialogElement | null>(null)
	let files = $state<FileList | undefined>(undefined)

	$effect(() => {
		const node = dialog
		const open = session.premierePending
		if (!node) return
		if (open && !node.open) {
			files = undefined
			node.showModal()
		}
		if (!open && node.open) node.close()
	})

	const dismiss = () => {
		files = undefined
		session.dismissPremiere()
	}

	const continueWithFile = () => {
		const file = files?.item(0)
		if (!file) return
		void session.continueWithPremiereFile(file)
	}
</script>

<dialog
	bind:this={dialog}
	class="m-auto w-[min(512px,calc(100%-48px))] rounded-lg border border-ink bg-background text-foreground backdrop:bg-ink/40"
	aria-modal="true"
	aria-labelledby="premiere-title"
	aria-describedby="premiere-body"
	oncancel={(event) => {
		event.preventDefault()
		dismiss()
	}}
>
	{#if session.premierePending}
		<div class="flex justify-end px-4 pt-4">
			<DialogClose label={sheet.close} onclick={dismiss} />
		</div>
		<div class="px-8 pt-4 pb-8" id="premiere-body">
			<h2 id="premiere-title" class="text-[24px] leading-8">{sheet.premiereTitle}</h2>

			<div class="mt-6">
				<h3 class="eyebrow">{sheet.autoHeading}</h3>
				<div class="mt-2 rounded-lg bg-soft p-4 text-[#9A6700]">
					<div class="flex items-start gap-2">
						<p class="w-8 shrink-0 text-[16px] leading-6 font-semibold">!</p>
						<p class="min-w-0 text-[16px] leading-6">{sheet.premiereNotice}</p>
					</div>
				</div>
			</div>

			<div class="mt-6">
				<Label class="eyebrow" for="premiere-youtube-url">{sheet.urlLabel}</Label>
				<div
					id="premiere-youtube-url"
					class="field-shell mt-2 gap-2 text-muted"
					aria-readonly="true"
				>
					<svg
						class="size-4 shrink-0"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						stroke-linecap="round"
						stroke-linejoin="round"
						aria-hidden="true"
					>
						<rect width="18" height="11" x="3" y="11" rx="2" ry="2"></rect>
						<path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
					</svg>
					<span class="truncate">{session.youtubeUrl}</span>
				</div>
			</div>

			<div class="mt-6">
				<Label for="premiere-video-file" class="eyebrow eyebrow-required">{sheet.fileLabel}</Label>
				<div class="field-file relative mt-2">
					<div
						class="field-shell pointer-events-none justify-between border-2 border-primary"
					>
						<span class="truncate">{files?.item(0)?.name ?? sheet.fileChoose}</span>
						<span class="shrink-0 text-primary" aria-hidden="true">↑</span>
					</div>
					<input
						id="premiere-video-file"
						class="absolute inset-0 h-12 cursor-pointer opacity-0"
						type="file"
						accept=".mp4,.mov,.webm,video/mp4,video/quicktime,video/webm"
						required
						bind:files
					/>
				</div>
				<p class="mt-2 text-[14px] leading-6 text-muted">{sheet.premiereHint}</p>
			</div>

			{#if session.preparing}
				<p class="mt-4 text-[16px] leading-6 text-muted" data-testid="preparing-clips">
					{sheet.preparingClips}
				</p>
			{/if}

			{#if session.error}
				<p class="mt-4 text-[16px] leading-6 text-destructive" role="alert">{session.error}</p>
			{/if}

			<div class="mt-8 flex flex-wrap gap-4">
				<button type="button" class="btn-secondary" onclick={dismiss}>{sheet.back}</button>
				<BusyButton
					type="button"
					class="btn-primary min-w-0 flex-1 sm:flex-none"
					busy={session.submitting}
					disabled={!files?.item(0)}
					onclick={continueWithFile}
				>
					{sheet.premiereContinue}
				</BusyButton>
			</div>
		</div>
	{/if}
</dialog>
