// Optional acceptance harness. Requires Playwright and Chrome; no paid calls without --live.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
(async () => {
  const live = process.argv.includes('--live');
  const browser = await chromium.launch({channel:'chrome',headless:true});
  const page = await browser.newPage({viewport:{width:1360,height:1000}});
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.goto('http://127.0.0.1:8000');
  if(live){
    await page.locator('#mode').selectOption('live');
    await page.locator('#company').fill(process.env.DEMO_COMPANY || 'https://www.lightdash.com');
    await page.locator('#confirm-live').check();
  }
  const response = page.waitForResponse(r => r.url().endsWith('/api/analyze') && r.request().method()==='POST', {timeout:210000});
  await page.getByRole('button',{name:'Analyze company'}).click();
  const res = await response;
  const report = await res.json();
  fs.mkdirSync('.local',{recursive:true});
  if(res.status()!==200){
    fs.writeFileSync('.local/browser-'+(live?'live':'offline')+'-failure.json',JSON.stringify(report,null,2));
    throw new Error('Analyze failed: '+JSON.stringify(report));
  }
  await page.locator('#results').waitFor({state:'visible'});
  assert.equal(report.analysis.sections.length,9);
  assert.ok(report.evidence.length>0);
  assert.ok((await page.locator('#memo-content').textContent()).includes('investment research memo'));
  if(!live){
    for(const [role,value] of Object.entries({prior_revenue:'C4',current_revenue:'C5',gross_profit:'C6',cash:'C7',monthly_net_burn:'C8'}))
      await page.locator('#input-'+role).selectOption(value);
    await page.getByText('Optional valuation sensitivities — analyst assumptions',{exact:true}).click();
    await page.locator('#bear').fill('2'); await page.locator('#base').fill('3'); await page.locator('#bull').fill('4');
    await page.locator('#confirm-finance').check();
    const financeResponse=page.waitForResponse(r=>r.url().endsWith('/api/financials'));
    await page.getByRole('button',{name:'Calculate reviewed inputs'}).click();
    const fr=await financeResponse; assert.equal(fr.status(),200);
    const updated=await fr.json();
    assert.equal(updated.financials.calculations.length,6);
    await page.locator('#financial-results').getByText('50 percent',{exact:true}).waitFor();
    const downloadPromise=page.waitForEvent('download');
    await page.getByRole('link',{name:'Download memo (.md)'}).click();
    const download=await downloadPromise; await download.saveAs('.local/browser-offline-memo.md');
    assert.ok(fs.readFileSync('.local/browser-offline-memo.md','utf8').includes('ASSUMPTION'));
    await page.locator('#financials').scrollIntoViewIfNeeded();
    await page.screenshot({path:'.local/browser-financials.png'});
    await page.locator('#company').fill('Lumen Sparse');
    const sparseResponse=page.waitForResponse(r=>r.url().endsWith('/api/analyze'));
    await page.getByRole('button',{name:'Analyze company'}).click();
    const sparse=await (await sparseResponse).json();
    assert.equal(sparse.financials.status,'unavailable');
    await page.locator('#financial-form').waitFor({state:'hidden'});
    assert.equal(sparse.usage.model_calls,0);
  }else{
    assert.equal(report.mode,'live');
    assert.equal(report.usage.searches,3);
    assert.equal(report.usage.model_calls,2);
    fs.writeFileSync('.local/browser-live-report.json',JSON.stringify(report,null,2));
  }
  await page.evaluate(()=>window.scrollTo(0,0));
  await page.screenshot({path:'.local/browser-'+(live?'live':'offline')+'.png'});
  assert.deepEqual(errors,[]);
  console.log(JSON.stringify({passed:true,mode:live?'live':'offline',company:report.company,claims:report.evidence.length,usage:report.usage,browser_errors:errors},null,2));
  await browser.close();
})().catch(e=>{console.error(e.message);process.exit(1);});
