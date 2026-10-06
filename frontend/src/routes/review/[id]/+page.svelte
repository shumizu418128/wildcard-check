<script lang="ts">
	import { page } from '$app/state'
	import { getContext, onMount } from 'svelte'
	import ReviewStep from '$lib/components/review-step.svelte'
	import VideoPreview from '$lib/components/video-preview.svelte'
	import { ReviewSession, reviewSessionKey } from '$lib/session.svelte'

	const session = getContext<ReviewSession>(reviewSessionKey)

	onMount(() => {
		const id = page.params.id ?? ''
		if (session.phase === 'work' && session.jobId === id) return
		void session.resume(id)
	})
</script>

{#if session.phase === 'work' && session.abortMessage === ''}
	<VideoPreview {session} />
	<ReviewStep {session} />
{/if}
