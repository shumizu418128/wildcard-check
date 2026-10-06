<script lang="ts">
	import { getContext, onMount } from 'svelte'
	import StartForm from '$lib/components/start-form.svelte'
	import { sheet } from '$lib/sheet'
	import { ReviewSession, reviewSessionKey } from '$lib/session.svelte'

	const session = getContext<ReviewSession>(reviewSessionKey)

	onMount(() => {
		if (session.phase !== 'intake') session.returnToIntake()
	})
</script>

<h1 class="mt-4 text-[32px] leading-10 font-semibold sm:text-[40px] sm:leading-12">{sheet.title}</h1>
<StartForm {session} />
