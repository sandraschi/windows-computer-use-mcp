import { expect, test } from "@playwright/test";

const BE = "http://127.0.0.1:10789";

test.describe("REST API", () => {
	test("GET /api/v1/health returns 200", async ({ request }) => {
		const res = await request.get(`${BE}/api/v1/health`);
		expect(res.status()).toBe(200);
		const body = await res.json();
		expect(body).toHaveProperty("status");
	});

	test("GET /api/v1/diagnostics returns system info", async ({ request }) => {
		const res = await request.get(`${BE}/api/v1/diagnostics`);
		expect(res.status()).toBe(200);
		const body = await res.json();
		expect(body).toHaveProperty("backend");
		expect(body).toHaveProperty("system");
	});

	test("GET /api/v1/system/info returns metrics", async ({ request }) => {
		const res = await request.get(`${BE}/api/v1/system/info`);
		expect(res.status()).toBe(200);
		const body = await res.json();
		expect(body).toHaveProperty("cpu_percent");
	});

	test("POST to nonexistent endpoint returns 404", async ({ request }) => {
		const res = await request.post(`${BE}/api/v1/nonexistent`, { data: {} });
		expect(res.status()).toBe(404);
	});
});
