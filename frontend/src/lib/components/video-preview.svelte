<script lang="ts">
	import { watchesVideo } from '$lib/catalog'
	import { isDebugYoutubeUrl } from '$lib/debug'
	import { sheet } from '$lib/sheet'
	import type { ReviewSession } from '$lib/session.svelte'
	import { youtubeEmbedUrl } from '$lib/youtube'

	let { session, showSubmitted = false }: { session: ReviewSession; showSubmitted?: boolean } =
		$props()
	let frame = $state<HTMLIFrameElement | null>(null)
	let clip = $state<HTMLVideoElement | null>(null)

	const fileUrl = () => session.localVideoUrl

	const useMockEmbed = () =>
		fileUrl() === '' && session.source === 'youtube' && isDebugYoutubeUrl(session.youtubeUrl)

	const embedUrl = () => {
		if (fileUrl() !== '' || session.source !== 'youtube' || useMockEmbed()) return ''
		const origin = typeof window === 'undefined' ? '' : window.location.origin
		return youtubeEmbedUrl(session.youtubeUrl, origin)
	}

	const hasSubmittedVideo = () => fileUrl() !== '' || useMockEmbed() || embedUrl() !== ''

	const visible = () => {
		if (!hasSubmittedVideo()) return false
		// 待機画面では、今のルールが動画を見るかどうかに関係なく提出動画を出す
		if (showSubmitted) return true
		return watchesVideo(session.currentRuleId())
	}

	const pauseEmbed = (player: HTMLIFrameElement | null) => {
		player?.contentWindow?.postMessage(
			JSON.stringify({ event: 'command', func: 'pauseVideo', args: '' }),
			'https://www.youtube-nocookie.com',
		)
	}

	$effect(() => {
		const showing = visible()
		const player = frame
		const node = clip
		if (showing) return
		node?.pause()
		pauseEmbed(player)
	})
</script>

<figure
	class:mt-8={visible()}
	class:hidden={!visible()}
	class="overflow-hidden rounded-lg border border-line"
	data-testid="video-preview"
>
	{#if useMockEmbed()}
		<div
			class="flex aspect-video w-full items-center justify-center bg-[#d9d2c8]"
			data-testid="video-preview-mock"
			role="img"
			aria-label={sheet.previewTitle}
		>
			<span class="text-[16px] leading-6 text-muted">Mock video</span>
		</div>
	{:else if embedUrl()}
		<iframe
			bind:this={frame}
			class="block aspect-video w-full"
			src={embedUrl()}
			title={sheet.previewTitle}
			allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
			allowfullscreen
			referrerpolicy="strict-origin-when-cross-origin"
		></iframe>
	{:else if fileUrl()}
		<!-- 提出ファイルに字幕は付かない -->
		<!-- svelte-ignore a11y_media_has_caption -->
		<video
			bind:this={clip}
			class="block aspect-video w-full bg-ink object-contain"
			src={fileUrl()}
			aria-label={sheet.previewTitle}
			controls
			playsinline
			preload="metadata"
		></video>
	{/if}
</figure>
