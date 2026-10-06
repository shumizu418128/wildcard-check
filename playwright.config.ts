import { defineConfig, devices } from '@playwright/test'

const e2eApiPort = 8001
const e2eWebPort = 5174

export default defineConfig({
	testDir: './e2e',
	timeout: 60000,
	workers: 1,
	use: {
		baseURL: `http://127.0.0.1:${e2eWebPort}`,
		...devices['Desktop Chrome'],
	},
	webServer: [
		{
			command: `python -m uvicorn app.main:app --host 127.0.0.1 --port ${e2eApiPort}`,
			cwd: './backend',
			url: `http://127.0.0.1:${e2eApiPort}/api/health`,
			env: { ...process.env },
			reuseExistingServer: false,
			timeout: 60000,
		},
		{
			command: `npm run dev -- --host 127.0.0.1 --port ${e2eWebPort} --strictPort`,
			cwd: './frontend',
			url: `http://127.0.0.1:${e2eWebPort}`,
			env: { ...process.env, API_PROXY_TARGET: `http://127.0.0.1:${e2eApiPort}` },
			reuseExistingServer: false,
			timeout: 120000,
		},
	],
})
