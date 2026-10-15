const fs=require('node:fs');
const path=require('node:path');
const {chromium}=require('C:/Users/21045/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const base='D:/MicroDuckResearch/ti/outputs/microduck_reproduction/all_work_reports_20261015';
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true,args:['--disable-gpu','--no-first-run']});
 const results=[];
 for(let n=1;n<=16;n++){
  const p=await browser.newPage({viewport:{width:1400,height:1000}}),errors=[];
  p.on('pageerror',e=>errors.push(e.message));
  const file=`reports/${String(n).padStart(2,'0')}_report.html`;
  await p.goto('file:///'+base+'/'+file,{waitUntil:'load'});
  const check=await p.evaluate(()=>({title:document.querySelector('h1').innerText,lastHeading:[...document.querySelectorAll('h2')].at(-1).innerText,overflow:document.documentElement.scrollWidth>innerWidth,images:document.images.length,missingImages:[...document.images].filter(i=>i.complete&&i.naturalWidth===0).length}));
  if(check.lastHeading!=='这项工作的价值'||check.overflow||check.missingImages||errors.length)throw Error(JSON.stringify({n,check,errors}));
  await p.screenshot({path:path.join(base,'qa',`report_${n.toString().padStart(2,'0')}.png`)});results.push({file,...check,errors});await p.close();
 }
 const p=await browser.newPage({viewport:{width:1400,height:1000}}),errors=[];p.on('pageerror',e=>errors.push(e.message));
 await p.goto('file:///'+base+'/index.html',{waitUntil:'load'});
 const atlasAll=await p.locator('.chart:not(.hidden)').count();
 await p.selectOption('#work','16');const atlas16=await p.locator('.chart:not(.hidden)').count();
 await p.screenshot({path:path.join(base,'qa','atlas.png')});
 if(atlasAll!==192||atlas16===0)throw Error('atlas filter failed');
 await p.goto('file:///'+base+'/data_explorer.html',{waitUntil:'load'});
 await p.selectOption('#w','8');
 const pulseCurves=await p.locator('#curve option').count();
 const pulseRows=await p.locator('#rows tbody tr').count();
 await p.screenshot({path:path.join(base,'qa','explorer_pulse.png')});
 if(pulseCurves!==20||pulseRows!==41)throw Error(JSON.stringify({pulseCurves,pulseRows}));
 await p.selectOption('#w','16');await p.selectOption('#metric','recorded:mean_joint_limit_steps');
 const metricsDrawn=await p.locator('#plot circle').count();
 if(metricsDrawn!==900||errors.length)throw Error(JSON.stringify({metricsDrawn,errors}));
 await p.screenshot({path:path.join(base,'qa','explorer_dose.png')});
 results.push({atlasAll,atlas16,pulseCurves,pulseRows,metricsDrawn,errors});
 fs.writeFileSync(path.join(base,'qa','browser_QA.json'),JSON.stringify({complete:true,results},null,2));
 await browser.close();console.log(JSON.stringify({reports:16,atlasAll,atlas16,pulseCurves,metricsDrawn,errors}));
})().catch(e=>{console.error(e);process.exit(1)});
