import './style.css'
import { createIcons, BrainCircuit, ShieldCheck, Link, CheckCircle2, AlertCircle } from 'lucide'
import confetti from 'canvas-confetti'

// Initialize Lucide icons
const icons = {
  BrainCircuit,
  ShieldCheck,
  Link,
  CheckCircle2,
  AlertCircle
}

function updateIcons() {
  createIcons({ icons })
}

updateIcons()

// Point to Render backend when deployed, otherwise localhost
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://localhost:8000'
  : 'https://zk-oracle-backend.onrender.com' // Placeholder for Render deployment

const runBtn = document.querySelector('#runBtn')
const assetInput = document.querySelector('#assetInput')
console.log('DOM Elements check:', { runBtn, assetInput })

if (!runBtn) console.error('Error: runBtn not found')
if (!assetInput) console.error('Error: assetInput not found')
const statusContainer = document.querySelector('#statusContainer')
const progressBar = document.querySelector('#progressBar')
const statusMsg = document.querySelector('#statusMsg')
const percentageText = document.querySelector('#percentageText')
const terminalLogs = document.querySelector('#terminalLogs')
const resultArea = document.querySelector('#resultArea')
const steps = [
  document.querySelector('#step1'),
  document.querySelector('#step2'),
  document.querySelector('#step3')
]

let pollInterval = null
let lastLogCount = 0

async function startPipeline() {
  console.log('startPipeline called')
  const asset = assetInput.value.trim()
  console.log('Asset value:', asset)
  if (!asset) return

  // Reset UI
  runBtn.disabled = true
  statusContainer.style.display = 'block'
  resultArea.innerHTML = ''
  terminalLogs.innerHTML = '<div class="log-line system">Starting new pipeline...</div>'
  lastLogCount = 0
  steps.forEach(s => s.classList.remove('active', 'completed'))
  progressBar.style.width = '0%'
  percentageText.textContent = '0%'
  
  try {
    const response = await fetch(`${API_BASE}/analyze/${asset}`, { method: 'POST' })
    const data = await response.json()
    
    if (response.ok) {
      pollStatus(asset)
    } else {
      showError(data.detail || 'Failed to start pipeline')
    }
  } catch (err) {
    console.error('Failed to start pipeline. Error:', err)
    showError(`Could not connect to the ZK-Oracle Backend. Error: ${err.message || err}`)
  }
}

function pollStatus(asset) {
  if (pollInterval) clearInterval(pollInterval)
  
  pollInterval = setInterval(async () => {
    try {
      const response = await fetch(`${API_BASE}/status/${asset}`)
      const data = await response.json()
      
      updateUI(data)
      
      if (data.status === 'completed' || data.status === 'failed') {
        clearInterval(pollInterval)
        runBtn.disabled = false
        if (data.status === 'completed') {
          confetti({
            particleCount: 100,
            spread: 70,
            origin: { y: 0.6 },
            colors: ['#7c4dff', '#00e5ff', '#00e676']
          })
          showResult(data)
        } else {
           showError(data.error || 'Pipeline failed during execution')
        }
      }
    } catch (err) {
      console.error('Polling error:', err)
    }
  }, 1000)
}

function updateUI(data) {
  statusMsg.textContent = data.message
  progressBar.style.width = `${data.progress}%`
  percentageText.textContent = `${data.progress}%`
  
  // Render new logs
  if (data.logs && data.logs.length > lastLogCount) {
    for (let i = lastLogCount; i < data.logs.length; i++) {
        const line = document.createElement('div')
        line.className = 'log-line'
        if (data.logs[i].includes('✅') || data.logs[i].includes('confirmed')) line.classList.add('success')
        if (data.logs[i].includes('❌') || data.logs[i].includes('ERROR')) line.classList.add('error')
        if (data.logs[i].includes('Initializing') || data.logs[i].includes('complete')) line.classList.add('system')
        
        line.textContent = `> ${data.logs[i]}`
        terminalLogs.appendChild(line)
    }
    lastLogCount = data.logs.length
    terminalLogs.scrollTop = terminalLogs.scrollHeight
  }

  // Step logic
  if (data.status === 'analyzing') {
    steps[0].classList.add('active')
  } else if (data.status === 'proving') {
// ...
    steps[0].classList.remove('active')
    steps[0].classList.add('completed')
    steps[1].classList.add('active')
  } else if (data.status === 'submitting') {
    steps[1].classList.remove('active')
    steps[1].classList.add('completed')
    steps[2].classList.add('active')
  } else if (data.status === 'completed') {
    steps[2].classList.remove('active')
    steps[2].classList.add('completed')
  }
}

function parseAnalysis(text) {
  const sections = { SENTIMENT: '', NEWS: '', TECHNICALS: '', CONCLUSION: '' };
  
  if (!text) return sections;

  const parts = text.split(/\[(SENTIMENT|NEWS|TECHNICALS|CONCLUSION)\]/);
  if (parts.length > 1) {
    for (let i = 1; i < parts.length; i += 2) {
      const tag = parts[i];
      const content = parts[i+1] ? parts[i+1].trim() : '';
      if (content) sections[tag] = content;
    }
  } else {
    sections['CONCLUSION'] = text;
  }
  
  return sections;
}

function showResult(data) {
  const report = data.report
  resultArea.innerHTML = `
    <div class="result-card">
      <h2 style="margin-bottom: 1rem">Verified Oracle Report</h2>
      <div class="report-grid">
        <div class="info-item">
          <div class="info-label">Asset</div>
          <div class="info-value">${report.asset.toUpperCase()}</div>
        </div>
        <div class="info-item">
          <div class="info-label">Price</div>
          <div class="info-value">$${report.price_usd.toLocaleString()}</div>
        </div>
        <div class="info-item">
          <div class="info-label">7D Moving Avg</div>
          <div class="info-value">$${report.moving_average.toLocaleString()}</div>
        </div>
        <div class="info-item">
          <div class="info-label">Status</div>
          <div class="info-value" style="color: var(--success)">✓ SECURE</div>
        </div>
      </div>
      
      <div class="info-label" style="margin-top: 2rem;">Detailed AI Analysis</div>
      ${renderAnalysisBoxes(report.analysis)}
      
      <a href="#" class="tx-link">
        View On-Chain Receipt: ${data.tx_hash.substring(0, 10)}...${data.tx_hash.substring(data.tx_hash.length - 8)}
      </a>
    </div>
  `
}

function renderAnalysisBoxes(analysisText) {
  const parsed = parseAnalysis(analysisText);
  const hasSections = Object.values(parsed).some(s => s.trim().length > 0);
  
  if (!hasSections) {
    return `<div class="analysis-text">${analysisText}</div>`;
  }
  
  const formatContent = (text) => {
    if (!text) return '';
    // Replace URLs with <a> tags
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    return text.trim()
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(urlRegex, (url) => `<a href="${url}" target="_blank" class="news-link">${url}</a>`)
      .replace(/\n\s*[\*\-]\s+/g, '<br>• ') // Convert bullet points (* or -)
      .replace(/\n(\d+)\.\s+/g, '<br>$1. ') // Handle numbered lists
      .replace(/\n/g, '<br>');
  };
  
  return `
    <div class="analysis-grid">
      ${parsed.SENTIMENT.trim() ? `
        <div class="analysis-box sentiment-box">
          <div class="box-header">Sentiment</div>
          <div class="box-content">${formatContent(parsed.SENTIMENT)}</div>
        </div>
      ` : ''}
      ${parsed.NEWS.trim() ? `
        <div class="analysis-box news-box">
          <div class="box-header">News</div>
          <div class="box-content">${formatContent(parsed.NEWS)}</div>
        </div>
      ` : ''}
      ${parsed.TECHNICALS.trim() ? `
        <div class="analysis-box technicals-box">
          <div class="box-header">Price & Technicals</div>
          <div class="box-content">${formatContent(parsed.TECHNICALS)}</div>
        </div>
      ` : ''}
      ${parsed.CONCLUSION.trim() ? `
        <div class="analysis-box conclusion-box">
          <div class="box-header">Overall Conclusion</div>
          <div class="box-content">${formatContent(parsed.CONCLUSION)}</div>
        </div>
      ` : ''}
    </div>
  `;
}

function showError(msg) {
  runBtn.disabled = false
  statusMsg.innerHTML = `<span style="color: var(--error)">${msg}</span>`
  clearInterval(pollInterval)
}

runBtn.addEventListener('click', startPipeline)
assetInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') startPipeline()
})
