<script lang="ts">
	import type { Snippet } from 'svelte'

	let {
		busy = false,
		disabled = false,
		type = 'button',
		class: className = '',
		onclick,
		children,
	}: {
		busy?: boolean
		disabled?: boolean
		type?: 'button' | 'submit'
		class?: string
		onclick?: () => void
		children: Snippet
	} = $props()
</script>

<button
	{type}
	class={className}
	class:btn-busy={busy}
	disabled={disabled || busy}
	aria-busy={busy}
	{onclick}
>
	{#if busy}
		<span class="btn-spinner" aria-hidden="true"></span>
	{/if}
	{@render children()}
</button>
