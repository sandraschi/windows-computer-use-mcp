import { expect, test } from "@playwright/test";

const PAGES = [
	{ route: "/", heading: "Automation Dashboard" },
	{ route: "/targets", heading: "Automation Targets" },
	{ route: "/tools", heading: "Tools" },
	{ route: "/elements", heading: "Element Inspector" },
	{ route: "/windows", heading: "Window Manager" },
	{ route: "/crawler", heading: "App Crawler" },
	{ route: "/chat", heading: "Chat" },
	{ route: "/logging", heading: "Logs" },
	{ route: "/settings", heading: "Settings" },
	{ route: "/help", heading: "Help" },
];

test.describe("Navigation", () => {
	for (const { route, heading } of PAGES) {
		test(`${route} loads with heading`, async ({ page }) => {
			await page.goto(route);
			await expect(page.getByRole("heading", { name: heading })).toBeVisible({ timeout: 10000 });
		});
	}

	test("sidebar links navigate to each page", async ({ page }) => {
		await page.goto("/");
		for (const { route } of PAGES.slice(1)) {
			const link = page.locator(`nav a[href="${route}"]`);
			await expect(link).toBeAttached();
			await link.click();
			await expect(page).toHaveURL(route);
		}
	});
});
