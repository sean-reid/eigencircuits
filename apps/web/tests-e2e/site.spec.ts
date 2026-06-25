import { expect, test } from '@playwright/test';

const SHOTS = 'tests-e2e/__screens__';

test('archive landing lists the math subjects', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /Mathematics/ })).toBeVisible();
  await expect(page.getByText('Number Theory')).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/01-archive.png`, fullPage: true });
});

test('subject listing paginates recent submissions', async ({ page }) => {
  await page.goto('/list/math.NT/recent');
  await expect(page.getByRole('heading', { name: 'Number Theory' })).toBeVisible();
  await expect(page.getByText(/Total of \d+ entries/)).toBeVisible();
  await expect(page.locator('text=/eiGen:\\d{4}\\.\\d{5}/').first()).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/02-listing.png`, fullPage: true });
});

test('abstract page shows metadata, then full text renders', async ({ page }) => {
  await page.goto('/list/math.NT/recent');
  await page.locator('a[href^="/abs/"]').first().click();
  await expect(page).toHaveURL(/\/abs\//);
  await expect(page.getByText('Abstract:')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Submission history' })).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/03-abstract.png`, fullPage: true });

  await page.locator('a[href^="/html/"]').first().click();
  await expect(page).toHaveURL(/\/html\//);
  await expect(page.locator('.paper .title')).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/04-fulltext.png`, fullPage: true });
});

test('search box finds papers by keyword', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('searchbox').fill('cohomology');
  await page.getByRole('button', { name: 'Search' }).click();
  await expect(page).toHaveURL(/\/search\?q=cohomology/);
  await expect(page.getByRole('heading', { name: /results? for/ })).toBeVisible();
  await expect(page.locator('a[href^="/abs/"]').first()).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/06-search.png`, fullPage: true });
});

test('search box jumps to an article by id', async ({ page }) => {
  await page.goto('/list/math.NT/recent');
  const href = (await page.locator('a[href^="/abs/"]').first().getAttribute('href'))!;
  const id = href.split('/')[2]!;
  await page.getByRole('searchbox').fill(id);
  await page.getByRole('button', { name: 'Search' }).click();
  await expect(page).toHaveURL(new RegExp(`/abs/${id.replace('.', '\\.')}`));
  await expect(page.getByText('Abstract:')).toBeVisible();
});

test('View PDF compiles the paper and hands off a PDF', async ({ page }) => {
  test.setTimeout(180_000); // first compile downloads the engine + packages
  // Record when a PDF blob is created (the handoff to the native viewer). This
  // is deterministic, unlike the subsequent navigation, which headless Chromium
  // turns into a download rather than a URL change.
  await page.addInitScript(() => {
    const w = window as unknown as { __pdfReady?: boolean };
    w.__pdfReady = false;
    const orig = URL.createObjectURL.bind(URL);
    URL.createObjectURL = (obj: Blob | MediaSource) => {
      if (obj instanceof Blob && obj.type === 'application/pdf') w.__pdfReady = true;
      return orig(obj);
    };
  });
  await page.goto('/list/math.NT/recent');
  await page.locator('a[href^="/pdf/"]').first().click();
  await expect(page).toHaveURL(/\/pdf\//);
  await expect(page.getByText(/Compiling with pdfTeX/)).toBeVisible();
  // The self-hosted TeX Live mirror means the compile needs no external service.
  await expect
    .poll(() => page.evaluate(() => (window as unknown as { __pdfReady?: boolean }).__pdfReady), {
      timeout: 150_000,
    })
    .toBe(true);
});

test('mobile archive layout', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /Mathematics/ })).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/05-mobile-archive.png`, fullPage: true });
});

test('mobile full-text view does not overflow horizontally', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/list/math.NT/recent');
  await page.locator('a[href^="/html/"]').first().click();
  await expect(page.locator('.paper .title')).toBeVisible();
  // Wide display equations must scroll within their box, not stretch the page.
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow).toBeLessThanOrEqual(1);
  await page.screenshot({ path: `${SHOTS}/08-mobile-html.png`, fullPage: true });
});
