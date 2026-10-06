<script lang="ts">
	let { label, onclick }: { label: string; onclick: () => void } = $props()
</script>

<button
	type="button"
	class="flex size-8 items-center justify-center rounded-lg text-[16px] leading-4 font-semibold text-ink hover:bg-line"
	aria-label={label}
	{onclick}
>
	<span aria-hidden="true">×</span>
</button>
