// Render an HTML infographic to PNG at 1080x1080.
// Usage: node cap_infographic.js <input.html> <output.png> [width] [height]
// Defaults: 1080x1080. Pass width=1080 height=1350 for portrait (carousel slides).
const puppeteer = require('./node_modules/puppeteer');
const path = require('path');

(async () => {
  const htmlPath = process.argv[2];
  const outPath = process.argv[3];
  const width = parseInt(process.argv[4] || '1080', 10);
  const height = parseInt(process.argv[5] || '1080', 10);

  if (!htmlPath || !outPath) {
    console.error('usage: node cap_infographic.js <in.html> <out.png> [width] [height]');
    process.exit(1);
  }

  const browser = await puppeteer.launch({
    headless: 'shell',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--font-render-hinting=none',
      '--disable-gpu',
    ],
  });

  const page = await browser.newPage();
  await page.setViewport({ width, height, deviceScaleFactor: 2 });
  await page.goto('file:///' + path.resolve(htmlPath).replace(/\\/g, '/'), {
    waitUntil: 'networkidle0',
    timeout: 35000,
  });

  try { await page.evaluate(() => document.fonts.ready); } catch (e) {}
  await new Promise(r => setTimeout(r, 800));

  await page.screenshot({
    path: outPath,
    type: 'png',
    clip: { x: 0, y: 0, width, height },
  });

  await browser.close();
  console.log('saved', outPath);
})().catch(e => {
  console.error('FATAL', e.message);
  process.exit(1);
});
