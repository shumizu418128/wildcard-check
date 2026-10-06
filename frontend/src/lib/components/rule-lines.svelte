<script lang="ts">
	import type { Verdict } from '$lib/catalog'

	let {
		lines,
		notes = [],
		expanded = false,
	}: { lines: Verdict[]; notes?: string[]; expanded?: boolean } = $props()
	let open = $state<Record<number, boolean>>({})
	let seen = ''

	const lineKey = $derived(lines.map((line) => line.text).join('|'))

	$effect(() => {
		if (seen === lineKey) return
		seen = lineKey
		open = {}
	})

	const toggle = (index: number) => {
		open = { ...open, [index]: !open[index] }
	}
</script>

{#if lines.length > 0}
	<ul class="mt-6 flex flex-col gap-2">
		{#each lines as line, index (index)}
			<li>
				{#if line.ok}
					<div
						class="flex items-start gap-2 rounded-lg bg-[#eaf6ee] px-4 py-4 text-[16px] leading-6 text-ok"
					>
						<p class="w-8 shrink-0">〇</p>
						<p>{line.text}</p>
					</div>
				{:else}
					<div
						class="rounded-lg bg-[#fff1f0] px-4 py-4 text-[16px] leading-6 text-destructive"
					>
						<div class="flex items-start gap-2">
							<p class="w-8 shrink-0">×</p>
							<div class="min-w-0">
								<p>{line.text}</p>
								{#if expanded}
									<div class="mt-2 border-t border-destructive pt-2">
										<p>{line.outcome}</p>
										{#if line.detail}
											<p class="mt-2">{line.detail}</p>
										{/if}
									</div>
								{:else}
									<button
										type="button"
										class="mt-2 inline-flex h-8 cursor-pointer items-center rounded-sm bg-destructive px-4 text-[16px] leading-6 text-white hover:bg-destructive/80"
										aria-expanded={Boolean(open[index])}
										onclick={() => toggle(index)}
									>
										penalty ›
									</button>
									{#if open[index]}
										<div class="mt-2 border-t border-destructive pt-2">
											<p>{line.outcome}</p>
											{#if line.detail}
												<p class="mt-2">{line.detail}</p>
											{/if}
										</div>
									{/if}
								{/if}
							</div>
						</div>
					</div>
				{/if}
			</li>
		{/each}
	</ul>
{/if}
{#if notes.length > 0}
	<div class="mt-6">
		{#each notes as note, index (index)}
			<p class="text-[16px] leading-6 text-muted {index > 0 ? 'mt-2' : ''}">{note}</p>
		{/each}
	</div>
{/if}
