<script lang="ts">
	import { goto } from '$app/navigation'
	import { getContext, onMount } from 'svelte'
	import ResultView from '$lib/components/result-view.svelte'
	import { ReviewSession, reviewSessionKey } from '$lib/session.svelte'

	const session = getContext<ReviewSession>(reviewSessionKey)

	onMount(() => {
		if (session.phase !== 'result' || session.source !== 'file') void goto('/')
	})
</script>

{#if session.phase === 'result'}
	<ResultView {session} />
{/if}
