import { spawn } from 'child_process';
import fs from 'fs';

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function run() {
  console.log('[+] Spawning headless Google Chrome navigating to http://localhost:8504...');
  const chrome = spawn('google-chrome', [
    '--headless=new',
    '--remote-debugging-port=9222',
    '--disable-gpu',
    '--no-sandbox',
    '--window-size=1280,1000',
    'http://localhost:8504'
  ], { stdio: 'ignore' });

  // Wait for Chrome CDP port to be open
  let pageWsUrl = null;
  for (let i = 0; i < 30; i++) {
    await sleep(500);
    try {
      const res = await fetch('http://127.0.0.1:9222/json/list');
      if (res.ok) {
        const pages = await res.json();
        const p = pages.find(item => item.type === 'page');
        if (p && p.webSocketDebuggerUrl) {
          pageWsUrl = p.webSocketDebuggerUrl;
          console.log('[+] Found page WebSocket:', pageWsUrl);
          break;
        }
      }
    } catch (e) {}
  }

  if (!pageWsUrl) {
    console.error('[-] Failed to find page target.');
    chrome.kill();
    process.exit(1);
  }

  const pageWs = new WebSocket(pageWsUrl);
  await new Promise((res, rej) => {
    pageWs.onopen = res;
    pageWs.onerror = rej;
  });

  let pMsgId = 1;
  const pPending = new Map();
  pageWs.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.id && pPending.has(data.id)) {
      const { resolve, reject } = pPending.get(data.id);
      pPending.delete(data.id);
      if (data.error) reject(data.error);
      else resolve(data.result);
    }
  };

  function sendPage(method, params = {}) {
    const id = pMsgId++;
    return new Promise((resolve, reject) => {
      pPending.set(id, { resolve, reject });
      pageWs.send(JSON.stringify({ id, method, params }));
    });
  }

  try {
    await sendPage('Page.enable');
    await sendPage('Runtime.enable');
    await sendPage('Emulation.setDeviceMetricsOverride', {
      width: 1280,
      height: 1500,
      deviceScaleFactor: 2,
      mobile: false
    });

    console.log('[+] Polling for Streamlit buttons to be ready in DOM...');
    let ready = false;
    for (let i = 0; i < 40; i++) {
      await sleep(1000);
      try {
        const res = await sendPage('Runtime.evaluate', {
          expression: `(() => Array.from(document.querySelectorAll('button')).some(b => (b.innerText || b.textContent).includes('تطابق لفظي')))()`
        });
        if (res && res.result && res.result.value) {
          ready = true;
          console.log('[+] Streamlit is fully loaded and interactive!');
          break;
        }
      } catch (e) {
        // ignore and retry
      }
    }

    if (!ready) throw new Error('Streamlit buttons never appeared!');

    await sleep(2000);

    console.log('[+] Clicking authentic hadith sample button (تطابق لفظي مباشر)...');
    await sendPage('Runtime.evaluate', {
      expression: `
        (() => {
          const buttons = Array.from(document.querySelectorAll('button'));
          const btn = buttons.find(b => (b.innerText || b.textContent).includes('تطابق لفظي'));
          if (btn) btn.click();
        })()
      `
    });

    console.log('[+] Waiting for verification result to appear with full Evidence Card...');
    let verifiedReady = false;
    for (let i = 0; i < 40; i++) {
      await sleep(1000);
      try {
        const res = await sendPage('Runtime.evaluate', {
          expression: `(() => {
            const body = document.body.innerText;
            const hasEvidenceCard = body.includes('بطاقة الإسناد المعتمدة') && body.includes('المصدر المعتمد');
            const hasVerdict = body.includes('تم التحقق');
            const isStillSpinning = body.includes('جارٍ المعالجة الدلالية');
            return hasEvidenceCard && hasVerdict && !isStillSpinning;
          })()`
        });
        if (res && res.result && res.result.value) {
          verifiedReady = true;
          console.log('[+] Verification result rendered with complete Evidence Card!');
          break;
        }
      } catch (e) {}
    }

    if (!verifiedReady) throw new Error('Verification result never finished processing!');

    await sleep(2500);

    // Scroll down to display the Evidence Card prominently
    console.log('[+] Scrolling to center the Evidence Card...');
    await sendPage('Runtime.evaluate', {
      expression: `(() => {
        const cardTitle = Array.from(document.querySelectorAll('h1, h2, h3, div')).find(el => el.innerText && el.innerText.includes('بطاقة الإسناد المعتمدة'));
        if (cardTitle) {
          cardTitle.scrollIntoView({ behavior: 'instant', block: 'start' });
          window.scrollBy(0, -50); // slight top margin for aesthetic framing
        } else {
          window.scrollTo(0, 380);
        }
      })()`
    });

    await sleep(1500);

    console.log('[+] Capturing verified UI screenshot (Evidence Card)...');
    const verifiedShot = await sendPage('Page.captureScreenshot', {
      format: 'png',
      captureBeyondViewport: false
    });
    fs.writeFileSync('streamlit_ui_verified.png', Buffer.from(verifiedShot.data, 'base64'));
    console.log('[+] Saved streamlit_ui_verified.png (' + fs.statSync('streamlit_ui_verified.png').size + ' bytes)');

    // Scroll back to top before clicking refused hadith
    await sendPage('Runtime.evaluate', { expression: `window.scrollTo(0, 0);` });
    await sleep(1000);

    // Now test refused hadith
    console.log('[+] Clicking on sample refused hadith button (الرفض الذكي لمكذوب)...');
    await sendPage('Runtime.evaluate', {
      expression: `
        (() => {
          const buttons = Array.from(document.querySelectorAll('button'));
          const btn = buttons.find(b => (b.innerText || b.textContent).includes('الرفض الذكي'));
          if (btn) btn.click();
        })()
      `
    });

    console.log('[+] Waiting for refusal result with custom card...');
    let refusedReady = false;
    for (let i = 0; i < 40; i++) {
      await sleep(1000);
      try {
        const res = await sendPage('Runtime.evaluate', {
          expression: `(() => {
            const body = document.body.innerText;
            const hasRefusalBadge = body.includes('غير مثبت في مصادر السنة');
            const hasRefusalMessage = body.includes('لم يتم العثور على أصل مطابق');
            const isStillSpinning = body.includes('جارٍ المعالجة الدلالية');
            return hasRefusalBadge && hasRefusalMessage && !isStillSpinning;
          })()`
        });
        if (res && res.result && res.result.value) {
          refusedReady = true;
          console.log('[+] Refusal alert rendered with clean spacing!');
          break;
        }
      } catch (e) {}
    }

    if (!refusedReady) throw new Error('Refusal alert never rendered!');

    await sleep(2500);

    // Scroll to center the refusal state and button
    console.log('[+] Scrolling to frame the Smart Refusal container...');
    await sendPage('Runtime.evaluate', {
      expression: `(() => {
        window.scrollTo(0, 220);
      })()`
    });

    await sleep(1500);

    console.log('[+] Capturing smart refusal UI screenshot...');
    const refusedShot = await sendPage('Page.captureScreenshot', {
      format: 'png',
      captureBeyondViewport: false
    });
    fs.writeFileSync('streamlit_ui_refused.png', Buffer.from(refusedShot.data, 'base64'));
    console.log('[+] Saved streamlit_ui_refused.png (' + fs.statSync('streamlit_ui_refused.png').size + ' bytes)');

    pageWs.close();
    chrome.kill();
    console.log('✅ Screenshots captured successfully!');
  } catch (err) {
    console.error('[-] Error during screenshot capture:', err);
    chrome.kill();
    process.exit(1);
  }
}

run();
