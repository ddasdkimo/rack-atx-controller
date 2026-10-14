// Optional browser validation: install Playwright or supply it via NODE_PATH.
const {chromium}=require('playwright');
const fs=require('node:fs');
const assert=require('node:assert/strict');
(async()=>{
  const browser=await chromium.launch({channel:'chrome',headless:true});
  const page=await browser.newPage({viewport:{width:1120,height:950},deviceScaleFactor:1});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(process.env.VIEWER_URL||'http://127.0.0.1:8766',{waitUntil:'networkidle'});
  const frame=page.frames().find(f=>f.parentFrame());
  assert(frame,'Viewer frame exists');
  await frame.waitForFunction(()=>!!window.rackViewer,{timeout:30000});
  const counts=await frame.evaluate(()=>window.rackViewer.hardwareCounts);
  assert.deepEqual(counts,{photorelays:20,isolatedSupplies:10,shiftRegisters:3,hostPorts:10,simulatedHosts:2});
  fs.mkdirSync('artifacts/local',{recursive:true});
  await page.screenshot({path:'artifacts/local/overview.png',fullPage:true});
  for(const view of ['controller','pc1','pc2']){
    await frame.locator('[data-view="'+view+'"]').click();
    await frame.waitForFunction(v=>window.rackViewer.getState().view===v,view);
    await page.screenshot({path:'artifacts/local/'+view+'.png',fullPage:true});
  }
  for(const signal of ['power','reset','pled','hdd','reference','all']){
    await frame.locator('[data-signal]').selectOption(signal);
    assert.equal(await frame.evaluate(()=>window.rackViewer.getState().signal),signal);
  }
  await frame.locator('[data-host]').selectOption('0');
  await frame.locator('[data-view="overview"]').click();
  const canvas=frame.locator('.rack-space canvas');
  const bounds=await canvas.boundingBox();
  const before=await frame.evaluate(()=>window.rackViewer.getCamera());
  await page.mouse.move(bounds.x+bounds.width/2,bounds.y+bounds.height/2);
  await page.mouse.down();await page.mouse.move(bounds.x+bounds.width/2+45,bounds.y+bounds.height/2+15,{steps:4});await page.mouse.up();
  assert.notEqual((await frame.evaluate(()=>window.rackViewer.getCamera())).yaw,before.yaw);
  await frame.locator('[data-shell]').check();assert.equal(await frame.evaluate(()=>window.rackViewer.getState().shell),true);
  await frame.locator('[data-shell]').uncheck();
  await frame.locator('[data-view="overview"]').click();
  await page.emulateMedia({colorScheme:'dark'});
  await page.screenshot({path:'artifacts/local/dark.png',fullPage:true});
  await page.emulateMedia({colorScheme:'light'});
  for(const width of [736,390,320]){
    await page.setViewportSize({width,height:900});
    await frame.waitForTimeout(150);
    assert.equal(await frame.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1),true,'No horizontal overflow at '+width);
    await page.screenshot({path:'artifacts/local/mobile-'+width+'.png',fullPage:true});
  }
  await page.setViewportSize({width:1120,height:900});
  await frame.locator('[data-costs]').scrollIntoViewIfNeeded();
  await page.waitForTimeout(200);
  const comparison=await frame.locator('[data-costs]').innerText();
  for(const amount of ['$148.18','$225.11–$247.02','$274.87','$372.90–$392.35']) assert(comparison.includes(amount),'Comparison includes '+amount);
  assert.match(await frame.locator('[data-pcb-cost-note]').innerText(), /另剩 3 片裸板/);
  await page.screenshot({path:'artifacts/local/costs.png'});
  await page.setViewportSize({width:390,height:900});
  await frame.locator('[data-costs]').scrollIntoViewIfNeeded();
  await page.waitForTimeout(200);
  await page.screenshot({path:'artifacts/local/costs-mobile.png'});
  assert.deepEqual(errors,[]);
  console.log(JSON.stringify({status:'pass',hardwareCounts:counts,views:4,signals:6,mobileWidths:[736,390,320],errors},null,2));
  await browser.close();
})().catch(e=>{console.error(e);process.exit(1);});
