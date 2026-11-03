const fs = require('fs');
const vm = require('vm');
const assert = require('assert/strict');
const path = require('path');
const handlers = {actions: [], texts: [], start: null};
const rows = [], transcript = [], requests = [];
const keyboard = rows => ({rows, resize(){return this}, oneTime(){return this}});
class Telegraf {
  start(fn){handlers.start=fn;}
  action(pattern,fn){handlers.actions.push([pattern,fn]);}
  on(type,fn){if(type==='text') handlers.texts.push(fn);}
}
const sheets = {spreadsheets:{
  get:async()=>({data:{sheets:[{properties:{title:'Demo Project',sheetId:1}}]}}),
  values:{
    append:async req=>{requests.push(req);rows.push(...req.requestBody.values);return {data:{updates:{updatedRange:`'Demo Project'!A${rows.length+1}:F${rows.length+1}`}}}},
    get:async()=>({data:{values:rows}})
  }
}};
const extracted={type:'Расход',category:'Расходы с НДС',amount:10000,amount1:12000,date:'2026-10-01',comment:'Demo materials'};
const mocks={
  telegraf:{Telegraf,Markup:{keyboard,inlineKeyboard:keyboard,button:{callback:(text,data)=>({text,data})}}},
  googleapis:{google:{auth:{GoogleAuth:class{async getClient(){return {demo:true}}}},sheets:()=>sheets}},
  dotenv:{config(){}},fs:{},path,
  'node-fetch':async()=>({json:async()=>({choices:[{message:{content:JSON.stringify(extracted)}}]})})
};
const sandbox={require:n=>{if(!(n in mocks))throw Error('Unexpected dependency: '+n);return mocks[n]},
  process:{env:{BOT_PASSWORD:'local-demo',BOT_TOKEN:'DEMO',SHEET_ID:'DEMO',DEEPSEEK_API_KEY:'DEMO'}},
  console:{log(){},error(...a){throw Error(a.join(' '))}},
  module:{exports:{}},setTimeout,clearTimeout,AbortController,Date};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'prototype-index.cjs'),'utf8'),sandbox);
function ctx(text=''){return {chat:{id:1},message:{text,message_id:1},reply:async(text,options)=>{transcript.push({from:'bot',text,options:options?JSON.parse(JSON.stringify(options)):null})},deleteMessage:async()=>{}};}
async function message(text){transcript.push({from:'user',text});for(const fn of handlers.texts)await fn(ctx(text));}
async function action(value){const c=ctx();for(const [p,fn] of handlers.actions){if(typeof p==='string'?p===value:(c.match=value.match(p))) {await fn(c);return;}}throw Error('Missing action '+value);}
function frame(title,note){return {title,note,transcript:structuredClone(transcript),rows:structuredClone(rows)}}
(async()=>{
  await message('local-demo'); transcript.length=0;
  await message('📂 Demo Project');
  const frames=[frame('1. Choose a project','The prototype offers manual income, expense and AI text input.')];
  await action('input:ai');
  await message('Расход: 10000 без НДС, категория Расходы с НДС, дата 2026-10-01, комментарий Demo materials');
  assert.equal(rows.length,0,'No row may be written before confirmation');
  frames.push(frame('2. Review the parsed entry','Fixed AI response in this offline demo; no model quality claim.'));
  await action('keep_last');
  assert.equal(rows.length,1);assert.deepEqual(Array.from(rows[0],String),['2026-10-01','Расходы с НДС','10000','12000','2000','Demo materials']);
  frames.push(frame('3. Confirm and save','The original handler appends the confirmed row to the mocked Sheets API.'));
  await action('preview');
  assert.ok(transcript.at(-1).text.includes('10000'));
  frames.push(frame('4. Inspect the result','The prototype reads the last entries back from the same mock sheet.'));
  fs.writeFileSync(path.join(__dirname,'../evidence/ai-run.json'),JSON.stringify({source:'https://github.com/islamwers/tgbot_salary',mode:'Offline harness: original handlers; Telegram, DeepSeek and Google Sheets are mocked. All entries are fictional. Existing prototype uses a fixed 20% tax calculation; this is not tax guidance.',checks:{noWriteBeforeConfirmation:true,singleConfirmedRow:true,readBackMatches:true},frames,requests},null,2));
  console.log('PASS: original handlers executed; no write before confirmation; one confirmed sample row; read-back matched.');
})();
