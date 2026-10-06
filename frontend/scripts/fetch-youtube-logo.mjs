import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const out = path.join(__dirname, '../static/logos/youtube.png')
const url =
	'https://static.vecteezy.com/system/resources/thumbnails/018/930/572/small/youtube-logo-youtube-icon-transparent-free-png.png'

const res = await fetch(url, {
	headers: {
		'User-Agent':
			'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
		Accept: 'image/png,image/*;q=0.8',
		Referer: 'https://www.vecteezy.com/',
	},
})

console.log('status', res.status, res.headers.get('content-type'))
const buf = Buffer.from(await res.arrayBuffer())
fs.writeFileSync(out, buf)
console.log('wrote', out, 'len', buf.length, 'head', buf.subarray(0, 8).toString('hex'))
