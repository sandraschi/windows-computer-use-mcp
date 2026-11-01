import { expect, test } from "@playwright/test";

test.describe("Dashboard", () => {
	test("loads with KPIs", async ({ page }) => {
		await page.goto("/");
		await expect(
			page.getByRole("heading", { name: "Automation Dashboard" }),
		).toBeVisible();
		const cards = page.locator('[data-testid^="kpi-"]');
		const count = await cards.count();
		expect(count).toBeGreaterThanOrEqual(4);
	});

	test("shows automation KPIs after loading", async ({ page }) => {
		await page.goto("/");
		await expect(page.getByText(/Windows open|Tools ready/)).toBeVisible({
			timeout: 10000,
		});
	});
});
