<script lang="ts">
	let {
		lead = '',
		samples = [],
		flush = false,
	}: {
		lead?: string
		samples?: string[]
		flush?: boolean
	} = $props()

	const top = $derived(flush ? '' : 'mt-6')
</script>

{#if lead}
	<p class="{top} text-[16px] leading-6">{lead}</p>
{/if}
{#each samples as sample, index (index)}
	<p class="text-[16px] leading-6 {index === 0 && !lead ? top : 'mt-2'}">{sample}</p>
{/each}
