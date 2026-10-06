<script lang="ts">
	import { Label as LabelPrimitive } from "bits-ui";

	let {
		ref = $bindable(null),
		class: className,
		...restProps
	}: LabelPrimitive.RootProps = $props();

	const labelClass =
		'flex items-center gap-2 text-[16px] leading-6 font-medium select-none group-data-[disabled=true]:pointer-events-none group-data-[disabled=true]:opacity-50 peer-disabled:cursor-not-allowed peer-disabled:opacity-50'
</script>

<LabelPrimitive.Root
	bind:ref
	data-slot="label"
	class={className ? `${labelClass} ${className}` : labelClass}
	{...restProps}
/>
