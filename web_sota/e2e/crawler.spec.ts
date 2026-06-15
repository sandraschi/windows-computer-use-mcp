import { expect, test } from "@playwright/test";

test.describe("Crawler page", () => {
	test.beforeEach(async ({ page }) => {
		await page.goto("/crawler");
	});

	test("shows crawl form", async ({ page }) => {
		await expect(page.getByRole("heading", { name: "App Crawler" })).toBeVisible();
		await expect(page.getByText("Window title")).toBeVisible();
		await expect(page.getByRole("button", { name: /crawl|start/i })).toBeAttached();
	});

	test("reports section is accessible", async ({ page }) => {
		const reportsTab = page.getByRole("tab", { name: /reports/i });
		await expect(reportsTab).toBeVisible();
	});
});
