const {chromium,expect}=require('@playwright/test');const fs=require('fs');
(async()=>{
 const out=require('path').resolve(process.env.EVIDENCE_DIR || require('path').join(__dirname,'../evidence'));fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch();const page=await browser.newPage({viewport:{width:1440,height:1080}});const errors=[];page.on('pageerror',e=>errors.push(String(e)));
 try{
 await page.goto(process.env.BASE_URL || 'http://127.0.0.1:8765/');await expect(page.getByRole('button',{name:'Analyze ticket'})).toBeEnabled({timeout:120000});
 await page.getByRole('button',{name:'Analyze ticket'}).click();await expect(page.locator('#result')).toBeVisible({timeout:60000});await expect(page.locator('#department')).toHaveText('Billing');await expect(page.locator('#policy-outcome')).toHaveText('Human review');
 await page.screenshot({path:out+'/live-desktop.png',fullPage:true});
 const decisionDownload=page.waitForEvent('download');await page.getByRole('button',{name:'Export JSON'}).click();await(await decisionDownload).saveAs(out+'/live-result.json');
 await page.locator('#threshold').fill('20');await expect(page.locator('#result')).toBeHidden();
 await page.locator('#threshold').fill('80');
 await page.getByRole('button',{name:'Decision schema'}).click();await expect(page.locator('#schema-code')).toContainText('churn_risk');
 await page.getByRole('button',{name:'Evaluate samples'}).click();await page.getByRole('button',{name:'Run 8 samples'}).click();
 await expect(page.locator('#evaluation-progress')).toContainText('Completed 8 / 8',{timeout:240000});
 await expect(page.locator('#evaluation-progress')).toContainText('0 failures');await expect(page.locator('#evaluation-rows tr')).toHaveCount(8);
 await expect(page.locator('#machine-state')).toHaveText('Local model ready');
 await page.screenshot({path:out+'/evaluation-desktop.png',fullPage:true});
 const evaluationDownload=page.waitForEvent('download');await page.getByRole('button',{name:'Export evaluation'}).click();await(await evaluationDownload).saveAs(out+'/evaluation.json');
 await page.getByRole('button',{name:'Live demo'}).click();await page.locator('#sample').selectOption('pt-billing');await expect(page.locator('#model')).toHaveValue('multilingual');
 await page.getByRole('button',{name:'Analyze ticket'}).click();await expect(page.locator('#result')).toBeVisible({timeout:60000});
 await page.setViewportSize({width:390,height:844});await page.screenshot({path:out+'/live-mobile.png',fullPage:true});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.locator('#ticket').fill('');await expect(page.locator('#result')).toBeHidden();await expect(page.getByRole('button',{name:'Analyze ticket'})).toBeDisabled();
 expect(errors).toEqual([]);fs.writeFileSync(out+'/browser-check.json',JSON.stringify({passed:true,realInference:true,viewports:[1440,390],checks:['real ticket','JSON export','stale result invalidation','schema','8-sample evaluation','Portuguese','mobile overflow','empty input'],errors},null,2));
 console.log(JSON.stringify(JSON.parse(fs.readFileSync(out+'/evaluation.json')).metrics));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
