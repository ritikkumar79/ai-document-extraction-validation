let allDocuments = [];

function escapeHtml(v){return String(v ?? "").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]));}
function prettyType(v){return String(v || "").replaceAll("_"," ").replace(/\b\w/g,c=>c.toUpperCase());}
function statusClass(v){return String(v || "").toLowerCase().replaceAll(" ","_");}

function renderDocuments(list){
  const tbody=document.getElementById("documentsBody");
  const empty=document.getElementById("tableEmpty");
  if(!list.length){tbody.innerHTML="";empty.classList.remove("hidden");return;}
  empty.classList.add("hidden");
  tbody.innerHTML=list.map(d=>`<tr>
    <td><a class="doc-link" href="/result/${encodeURIComponent(d.document_name)}"><span class="file-icon">${String(d.document_name).toLowerCase().endsWith(".pdf")?"PDF":"IMG"}</span><span><strong>${escapeHtml(d.document_name)}</strong><small>Stored result</small></span></a></td>
    <td><span class="type-pill">${escapeHtml(prettyType(d.document_type))}</span></td>
    <td><span class="status ${statusClass(d.processing_status)}">${escapeHtml(d.processing_status)}</span></td>
    <td>${d.processed_at ? escapeHtml(new Date(d.processed_at).toLocaleString()) : "—"}</td>
    <td>${escapeHtml(d.processing_time_ms ?? "—")} ms</td>
    <td><a class="view-link" href="/result/${encodeURIComponent(d.document_name)}">View result <span>→</span></a></td>
  </tr>`).join("");
}

function updateMetrics(list){
  const passed=list.filter(d=>String(d.processing_status).toUpperCase()==="PASS").length;
  const failed=list.filter(d=>String(d.processing_status).toUpperCase()!=="PASS").length;
  document.getElementById("totalDocs").textContent=list.length;
  document.getElementById("passedDocs").textContent=passed;
  document.getElementById("failedDocs").textContent=failed;
  document.getElementById("latestTime").textContent=list[0]?.processed_at ? new Date(list[0].processed_at).toLocaleDateString([], {day:"2-digit",month:"short"}) : "—";
}

async function loadDocuments(){
  const tbody=document.getElementById("documentsBody");
  tbody.innerHTML='<tr><td colspan="6"><div class="table-loading"><div class="spinner small"></div>Loading processed documents…</div></td></tr>';
  try{
    const res=await fetch("/api/v1/documents");
    const data=await res.json();
    if(!res.ok) throw new Error("Unable to load documents");
    allDocuments=Array.isArray(data.documents)?data.documents:[];
    updateMetrics(allDocuments); renderDocuments(allDocuments);
  }catch(e){
    document.getElementById("documentsBody").innerHTML='<tr><td colspan="6"><div class="table-error">API unavailable. Please refresh and try again.</div></td></tr>';
    document.getElementById("tableEmpty").classList.add("hidden");
  }
}

async function processDocument(){
  const file=document.getElementById("file").files[0];
  const type=document.getElementById("documentType").value;
  const msg=document.getElementById("message");
  const btn=document.getElementById("processBtn");
  if(!file){showMessage("Please choose a PDF, JPG or PNG file.","error");document.getElementById("dropzone").classList.add("invalid");return;}
  document.getElementById("dropzone").classList.remove("invalid");
  const fd=new FormData();fd.append("file",file);fd.append("document_type",type);
  btn.disabled=true;btn.innerHTML='<span>Processing document…</span><b class="spin">◌</b>';msg.textContent="";msg.className="message";
  try{
    const res=await fetch("/api/v1/documents/process",{method:"POST",body:fd});
    const data=await res.json();
    if(!res.ok) throw new Error(data.detail?.error?.message || data.detail?.message || "Processing failed");
    showMessage("Document processed successfully. Opening the result…","success");
    await loadDocuments();
    setTimeout(()=>location.href="/result/"+encodeURIComponent(data.document_name),250);
  }catch(e){showMessage(e.message,"error");}
  finally{btn.disabled=false;btn.innerHTML='<span>Process document</span><b>→</b>';}
}

function showMessage(text,type){const el=document.getElementById("message");el.className="message "+type;el.textContent=text;}
function setupUpload(){
  const input=document.getElementById("file"),zone=document.getElementById("dropzone"),name=document.getElementById("fileName");
  if(!input||!zone)return;
  input.addEventListener("change",()=>{if(input.files[0]){name.textContent=input.files[0].name;zone.classList.add("selected");}});
  ["dragenter","dragover"].forEach(evt=>zone.addEventListener(evt,e=>{e.preventDefault();zone.classList.add("dragging");}));
  ["dragleave","drop"].forEach(evt=>zone.addEventListener(evt,e=>{e.preventDefault();zone.classList.remove("dragging");}));
  zone.addEventListener("drop",e=>{const file=e.dataTransfer.files[0];if(!file)return;try{const dt=new DataTransfer();dt.items.add(file);input.files=dt.files;input.dispatchEvent(new Event("change"));}catch(_){name.textContent=file.name;}});
}
function setupSearch(){const input=document.getElementById("searchInput");if(!input)return;input.addEventListener("input",()=>{const q=input.value.trim().toLowerCase();renderDocuments(allDocuments.filter(d=>`${d.document_name} ${d.document_type} ${d.processing_status}`.toLowerCase().includes(q)));});}
async function checkHealth(){
  try{const r=await fetch("/api/v1/health");const ok=r.ok;const el=document.getElementById("health");el.innerHTML=`<span class="status-dot"></span><span>${ok?"API operational":"API error"}</span>`;el.className="api-status "+(ok?"ok":"bad");document.getElementById("sideHealth").textContent=ok?"Operational":"Unavailable";document.getElementById("sideHealthDot").className="service-dot "+(ok?"ok":"bad");}
  catch(e){const el=document.getElementById("health");el.innerHTML='<span class="status-dot"></span><span>API unavailable</span>';el.className="api-status bad";document.getElementById("sideHealth").textContent="Unavailable";document.getElementById("sideHealthDot").className="service-dot bad";}
}
function setupMenu(){const btn=document.getElementById("menuBtn"),side=document.getElementById("sidebar");if(!btn||!side)return;btn.addEventListener("click",()=>side.classList.toggle("open"));side.querySelectorAll("a").forEach(a=>a.addEventListener("click",()=>side.classList.remove("open")));}

document.addEventListener("DOMContentLoaded",()=>{setupUpload();setupSearch();setupMenu();loadDocuments();checkHealth();});
