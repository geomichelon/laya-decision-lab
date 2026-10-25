'use strict';
const $ = id => document.getElementById(id);
const names = {billing:'Billing',technical:'Technical',sales:'Sales',other:'Other'};
let config, busy=false, lastResult=null, evaluation=null, modelState='connecting', poll;
const percent = n => `${(n*100).toFixed(1)}%`;
function error(message){$('error').textContent=message;$('error').hidden=!message;}
function controls(){
 const waiting=busy||modelState==='loading'||modelState==='connecting';
 $('analyze').disabled=waiting||!$('ticket').value.trim();$('evaluate').disabled=waiting;
 for(const id of ['ticket','sample','model','threshold'])$(id).disabled=busy;
}
function invalidate(){lastResult=null;$('result').hidden=true;$('empty-result').hidden=false;$('timing').textContent='Ready when you are';$('characters').textContent=`${$('ticket').value.length.toLocaleString()} / 2,000`;controls();}
function loadSample(id){const s=config.samples.find(x=>x.id===id);if(!s)return;$('ticket').value=s.text;$('model').value=s.language==='pt'?'multilingual':'typed-decisions';invalidate();error('');}
async function request(path,body){const response=await fetch(path,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{});const data=await response.json();if(!response.ok){throw new Error(typeof data.detail==='string'?data.detail:'The request was rejected. Check the ticket text and try again.');}return data;}
async function status(){try{const s=await request('/api/status');modelState=s.state;$('state-dot').classList.toggle('ready',s.state==='ready');$('machine-state').textContent=({idle:'Local engine available',loading:'Preparing the checkpoint…',analyzing:'Analyzing on this Mac…',ready:'Local model ready',error:'Model needs attention'})[s.state];$('machine-detail').textContent=[s.model,s.device?.toUpperCase()].filter(Boolean).join(' · ')||'First use downloads the model weights';$('version').textContent=`Laya ${s.version} · real local inference`;if(!busy){$('run-state').textContent=s.error||(s.state==='loading'?'Downloading or loading model weights. Please keep this window open.':'Choose a ticket and analyze. English and Portuguese use separate checkpoints.');}controls();}catch{modelState='error';$('machine-state').textContent='Local server unavailable';$('state-dot').classList.remove('ready');$('run-state').textContent='Start the local server, then reload this page.';$('analyze').disabled=true;$('evaluate').disabled=true;}}
function element(tag,text,cls){const el=document.createElement(tag);if(text!==undefined)el.textContent=text;if(cls)el.className=cls;return el;}
function resultReady(result){modelState='ready';$('state-dot').classList.add('ready');$('machine-state').textContent='Local model ready';$('machine-detail').textContent=`${result.model} · ${result.device.toUpperCase()}`;}
function render(result){
 resultReady(result);
 const a=result.answers;$('empty-result').hidden=true;$('result').hidden=false;
 $('department').textContent=names[a.department.choice]||a.department.choice;
 $('timing').textContent=`${result.inference_ms.toFixed(0)} ms · inference`;
 $('department-bars').replaceChildren();
 for(const [key,value] of Object.entries(a.department.probabilities)){
  const col=element('div'),track=element('div',undefined,'track'),bar=element('span');bar.style.width=`${value*100}%`;track.append(bar);col.append(track,element('span',names[key]||key),element('b',percent(value)));$('department-bars').append(col);
 }
 const levels=['Low','Medium','High'];const probabilities=Object.entries(a.urgency.probabilities);const top=probabilities.reduce((best,p)=>p[1]>best[1]?p:best)[0];
 $('urgency').textContent=levels[Number(top)]||top;$('urgency-score').textContent=`Expected score ${a.urgency.score.toFixed(2)} / 2`;
 $('urgency-bars').replaceChildren(...levels.map((x,i)=>element('div',`${x} ${Math.round((a.urgency.probabilities[String(i)]||0)*100)}%`,String(i)===top?'selected':'')));
 $('churn').textContent=percent(a.churn_risk.noul);$('churn-bar').style.width=`${a.churn_risk.noul*100}%`;
 const review=result.policy.outcome==='human_review';$('policy').classList.toggle('review',review);$('policy-outcome').textContent=review?'Human review':`Suggested route → ${names[a.department.choice]||a.department.choice}`;
 $('policy-reason').textContent=result.policy.reasons.join(' ');$('confidence').textContent=`Lowest confidence: ${percent(result.policy.minimum_confidence)} · threshold ${Math.round(result.policy.threshold*100)}%`;
 $('receipt').textContent=`${result.model} · ${result.device.toUpperCase()}${result.cpu_fallback_count?' · CPU fallback observed':''}`;
}
function download(value,name){const url=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:'application/json'}));const a=element('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
$('ticket').addEventListener('input',()=>{$('sample').value='';invalidate();});
$('model').addEventListener('change',invalidate);
$('threshold').addEventListener('input',()=>{$('threshold-value').textContent=`${$('threshold').value}%`;invalidate();});
$('sample').addEventListener('change',e=>loadSample(e.target.value));
$('analyze').addEventListener('click',async()=>{
 if(busy)return;busy=true;controls();error('');invalidate();
 const body={text:$('ticket').value,model:$('model').value,threshold:Number($('threshold').value)/100};
 const start=performance.now();const timer=setInterval(()=>{$('run-state').textContent=`${modelState==='loading'?'Preparing model':'Analyzing'} · ${((performance.now()-start)/1000).toFixed(1)} s elapsed`;},100);
 try{const result=await request('/api/analyze',body);lastResult={input:body,...result};render(result);$('run-state').textContent=`Completed in ${(result.total_ms/1000).toFixed(2)} s on the server.${result.loaded_this_request?' Includes checkpoint loading.':''}`;}
 catch(e){error(e.message);$('run-state').textContent='No result was produced. You can retry.';}
 finally{clearInterval(timer);busy=false;controls();}
});
$('export').addEventListener('click',()=>lastResult&&download(lastResult,'laya-decision.json'));
for(const tab of document.querySelectorAll('.tab'))tab.addEventListener('click',()=>{
 for(const t of document.querySelectorAll('.tab')){t.classList.toggle('active',t===tab);if(t===tab)t.setAttribute('aria-current','page');else t.removeAttribute('aria-current');}
 for(const section of document.querySelectorAll('.panel'))section.hidden=section.id!==tab.dataset.panel;
});
function updateMetrics(){
 const rows=evaluation.rows,n=rows.length;if(!n)return;
 const times=rows.map(r=>r.result.inference_ms).sort((a,b)=>a-b);
 const accuracy=key=>rows.filter(r=>(key==='laya'?r.result.answers.department.choice:r.result.baseline.department)===r.expected.department).length/n;
 const metrics={completed:n,failed:evaluation.failures.length,department_accuracy:accuracy('laya'),rules_accuracy:accuracy('rules'),churn_accuracy:rows.filter(r=>(r.result.answers.churn_risk.noul>=.5)===r.expected.churn_risk).length/n,urgency_mae:rows.reduce((sum,r)=>sum+Math.abs(r.result.answers.urgency.score-r.expected.urgency),0)/n,p50_ms:times[Math.ceil(n*.5)-1],p95_ms:times[Math.ceil(n*.95)-1],review_rate:rows.filter(r=>r.result.policy.outcome==='human_review').length/n};
 evaluation.metrics=metrics;
 const pairs=[[percent(metrics.department_accuracy),'Laya · department agreement'],[percent(metrics.rules_accuracy),'Rules · department agreement'],[`${metrics.p95_ms.toFixed(0)} ms`,`p95 · ${n} completed samples`],[percent(metrics.review_rate),'Suggested human review']];
 $('metrics').replaceChildren(...pairs.map(([v,label])=>{const div=element('div',undefined,'metric');div.append(element('strong',v),element('span',label));return div;}));
}
$('evaluate').addEventListener('click',async()=>{
 if(busy)return;busy=true;controls();error('');$('export-evaluation').disabled=true;
 evaluation={description:'Visible synthetic demonstration samples; not a held-out benchmark. No model calibration performed.',threshold:Number($('threshold').value)/100,rows:[],failures:[]};
 $('evaluation-rows').replaceChildren();$('metrics').replaceChildren();
 for(const [index,sample] of config.samples.entries()){
  $('evaluation-progress').textContent=`Analyzing ${index+1} / ${config.samples.length}: ${sample.title}…`;
  const row=element('tr');row.append(element('td',sample.title),element('td',names[sample.expected.department]));$('evaluation-rows').append(row);
  try{
   const result=await request('/api/analyze',{text:sample.text,model:sample.language==='pt'?'multilingual':'typed-decisions',threshold:evaluation.threshold});
   resultReady(result);evaluation.rows.push({id:sample.id,text:sample.text,expected:sample.expected,result});
   const actual=result.answers.department.choice,rules=result.baseline.department;
   row.append(element('td',names[actual]||actual,actual===sample.expected.department?'pass':'fail'),element('td',names[rules],rules===sample.expected.department?'pass':'fail'),element('td',`${result.inference_ms.toFixed(0)} ms`),element('td',result.policy.outcome==='human_review'?'Human review':'Suggested route'));
   updateMetrics();
  }catch(e){evaluation.failures.push({id:sample.id,error:e.message});const td=element('td',e.message,'fail');td.colSpan=4;row.append(td);}
 }
 $('evaluation-progress').textContent=`Completed ${evaluation.rows.length} / ${config.samples.length} · ${evaluation.failures.length} failures. Metrics use completed samples only. No external actions executed.`;
 if(evaluation.rows.length)updateMetrics();$('export-evaluation').disabled=false;busy=false;controls();
});
$('export-evaluation').addEventListener('click',()=>evaluation&&download(evaluation,'laya-evaluation.json'));
$('present').addEventListener('click',async()=>{if(document.fullscreenElement){await document.exitFullscreen();return;}document.body.classList.toggle('presenting');if(document.body.classList.contains('presenting')){try{await document.documentElement.requestFullscreen();}catch{}}});
document.addEventListener('fullscreenchange',()=>{document.body.classList.toggle('presenting',!!document.fullscreenElement);$('present').textContent=document.fullscreenElement?'⛶ Exit':'⛶ Present';});
(async()=>{try{config=await request('/api/config');for(const s of config.samples)$('sample').append(Object.assign(element('option',`${s.title} · ${s.language.toUpperCase()}`),{value:s.id}));$('schema-code').textContent=JSON.stringify(config.questions,null,2);$('sample').value='duplicate';loadSample('duplicate');await status();poll=setInterval(status,2000);}catch(e){error(e.message);}})();
window.addEventListener('pagehide',()=>clearInterval(poll));
