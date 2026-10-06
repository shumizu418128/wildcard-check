<script lang="ts">
	import { goto } from '$app/navigation'
	import { getContext, onMount } from 'svelte'
	import ReviewStep from '$lib/components/review-step.svelte'
	import VideoPreview from '$lib/components/video-preview.svelte'
	import { ReviewSession, reviewSessionKey } from '$lib/session.svelte'

	const session = getContext<ReviewSession>(reviewSessionKey)

	onMount(() => {
		if (session.phase !== 'work' || session.source !== 'file') void goto('/')
	})
</script>

{#if session.phase === 'work' && session.abortMessage === ''}
	<VideoPreview {session} />
	<ReviewStep {session} />
{/if}
