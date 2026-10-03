import http from "http";
const evalJson = {"metrics":{"SPLIT_INVOICE":{"precision":0.727,"recall":0.889},"STATISTICAL_ANOMALY":{"precision":0.385,"recall":0.833},"WRONG_TAX_RATE":{"precision":0.9,"recall":0.9},"AMOUNT_MISMATCH":{"precision":1.0,"recall":0.9},"ROUNDING_DIFF":{"precision":0.875,"recall":0.933},"MISSING_IN_BOOKS":{"precision":1.0,"recall":1.0},"MISSING_IN_GSTR2B":{"precision":0.933,"recall":1.0},"PAYMENT_180_DAY_RISK":{"precision":1.0,"recall":0.875},"UNMATCHED_RECEIPT":{"precision":0.8,"recall":1.0},"UPI_MDR_ADJUSTED":{"precision":1.0,"recall":0.95},"DUPLICATE_INVOICE":{"precision":1.0,"recall":0.875},"SUPPLIER_GSTIN_CANCELLED":{"precision":0.316,"recall":1.0},"UNMATCHED_PAYMENT":{"precision":1.0,"recall":1.0},"CIRCULAR_TRADING":{"precision":0.438,"recall":1.0},"PERIOD_CUTOFF":{"precision":0.12,"recall":1.0},"WRONG_TAX_TYPE":{"precision":1.0,"recall":1.0}}};
const q1 = {id:1,rule_id:"R-MATCH-01",issue_type:"MISSING_IN_GSTR2B",bucket:"AT_RISK",severity:"HIGH",title:"Invoice not in GSTR-2B",plain_reason:"Zenith Traders has not reported this invoice, so the tax credit cannot be claimed yet.",amount_at_stake:180000,priority_score:270000,confidence:1,deadline:"2026-10-20",days_left:2,recommended_action:"CHASE_SUPPLIER",entity:{type:"purchase_invoice",id:412,invoice_no:"INV/25-26/0045",invoice_date:"2026-09-12",supplier_id:9,supplier_name:"Zenith Traders"},evidence:[{label:"Books tax",value:"180000.00",source:"purchase_books#412"}],status:"OPEN",explanation:null,draft:null};
const q64 = {id:64,rule_id:"R-TAX-02",issue_type:"WRONG_TAX_RATE",bucket:"NEEDS_FIX",severity:"LOW",title:"charged less than expected; supplier may owe the difference",plain_reason:"This invoice is dated unknown, but charges 0.0% instead of 5.0%. Ask for a credit note for \u20B90.00.",amount_at_stake:0,priority_score:0,confidence:0.95,deadline:null,days_left:null,recommended_action:"INVESTIGATE",entity:{type:"purchase_invoice",id:460,invoice_no:null,invoice_date:null,supplier_id:9,supplier_name:null},evidence:[{label:"charged_rate",value:"0.0",source:"supplier_invoices/books"},{label:"expected_rate",value:"5.0",source:"rate_table"}],status:"OPEN",explanation:null,draft:null};
const q2 = {...q1,id:2,issue_type:"PAYMENT_180_DAY_RISK",title:"Pay supplier before the 180-day limit",amount_at_stake:92000,priority_score:115000,deadline:"2026-10-29",days_left:11,recommended_action:"PAY_NOW",entity:{...q1.entity,id:300,invoice_no:"APX/118",supplier_name:"Apex Packaging",invoice_date:"2026-05-02"}};
let queue = [q64, q1, q2];
const summary = {safe_to_claim:4260000,at_risk:680000,needs_fix:120000,status_breakdown:{matched:350,matched_adjusted:20,discrepant:30,unmatched:15,duplicate:5},liability:{output_tax:5000000,itc_claim_now:4260000,itc_if_all_recovered:5060000,net_payable_now:740000,net_payable_if_recovered:0,cash_impact_of_issues:740000},top5_queue:[q1]};
const send = (res, code, body) => { res.writeHead(code, {"Content-Type":"application/json","Access-Control-Allow-Origin":"*","Access-Control-Allow-Methods":"*","Access-Control-Allow-Headers":"*"}); res.end(JSON.stringify(body)); };
http.createServer((req, res) => {
  const u = new URL(req.url, "http://x"); const p = u.pathname.replace(/^\/api/, "");
  if (req.method === "OPTIONS") return send(res, 204, {});
  if (p === "/health") return send(res, 200, {status:"ok",as_of_date:"2026-10-18",period:"2026-09",llm_provider:"none"});
  if (p === "/summary") return send(res, 200, summary);
  if (p === "/queue") return send(res, 200, queue);
  let m = p.match(/^\/queue\/(\d+)$/);
  if (m && req.method === "PATCH") { let b=""; req.on("data",c=>b+=c); req.on("end",()=>{ const s=JSON.parse(b).status; queue=queue.map(i=>i.id==m[1]?{...i,status:s}:i); send(res,200,{ok:true}); }); return; }
  if (m) return send(res, 200, queue.find(i=>i.id==m[1]));
  m = p.match(/^\/queue\/(\d+)\/explain$/); if (m) return send(res, 200, {explanation:"Zenith Traders has not filed this invoice yet, so \u20B91,80,000 of credit is stuck. Chase them before 20 Oct."});
  m = p.match(/^\/queue\/(\d+)\/draft$/); if (m) return send(res, 200, {draft:{subject:"Invoice INV/25-26/0045 not showing in GSTR-2B",body:"Hello,\n\nInvoice INV/25-26/0045 dated 12 Sep 2026 for \u20B91,80,000 tax is not reflecting in our GSTR-2B. Please file by 20 Oct 2026.\n\nThank you"}});
  if (p === "/audit") return send(res, 200, [{id:1,ts:"2026-10-18T10:00:00",actor:"system",action:"RUN_STARTED",entity_type:"recon_run",entity_id:1}]);
  if (p === "/audit/verify") return send(res, 200, {valid:true,broken_at_id:null});
  if (p === "/evaluation") return send(res, 200, evalJson);
  send(res, 404, {error:{code:"not_found",message:p}});
}).listen(8000, () => console.log("mock on 8000"));
