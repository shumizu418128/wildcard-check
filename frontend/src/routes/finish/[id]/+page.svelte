<script lang="ts">
	import { page } from '$app/state'
	import { getContext, onMount } from 'svelte'
	import ResultView from '$lib/components/result-view.svelte'
	import { ReviewSession, reviewSessionKey } from '$lib/session.svelte'

	const session = getContext<ReviewSession>(reviewSessionKey)

	onMount(() => {
		const id = page.params.id ?? ''
		if (session.phase === 'result' && session.jobId === id) return
		void session.resume(id)
	})
</script>

{#if session.phase === 'result'}
	<ResultView {session} />
{/if}
