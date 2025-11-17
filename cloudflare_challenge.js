/**
 * Cloudflare Challenge Solver Demo (Node.js)
 * Solves Cloudflare Challenge (5-second shield) using CapSolver API
 * 
 * Requirements:
 * - Static or Sticky proxy (MANDATORY - rotating proxies won't work)
 * - TLS fingerprinting, matching headers, header order, and User-Agent
 * - Chrome User-Agent recommended
 * 
 * Returns: cf_clearance cookie and token
 */

const axios = require('axios');

// ============== CONFIGURATION ==============
const CAPSOLVER_API_KEY = 'YOUR_API_KEY_HERE';
const WEBSITE_URL = 'https://www.example.com';
const PROXY = 'http://user:pass@host:port';
const USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36';
const HTML_CONTENT = '';
// ============================================

async function createTask(apiKey, taskData) {
  const response = await axios.post('https://api.capsolver.com/createTask', {
    clientKey: apiKey,
    task: taskData
  });
  return response.data;
}

async function getTaskResult(apiKey, taskId) {
  const response = await axios.post('https://api.capsolver.com/getTaskResult', {
    clientKey: apiKey,
    taskId: taskId
  });
  return response.data;
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function solveCloudflareChallenge(apiKey, websiteUrl, proxy, userAgent = null, html = null) {
  console.log('='.repeat(70));
  console.log('Cloudflare Challenge Solver (Node.js with tls-client)');
  console.log('='.repeat(70));

  if (!apiKey || apiKey === 'YOUR_API_KEY_HERE') {
    throw new Error('Please set your CapSolver API key');
  }

  if (!websiteUrl || websiteUrl === 'https://www.example.com') {
    throw new Error('Please set the target website URL');
  }

  if (!proxy || proxy === 'http://user:pass@host:port') {
    throw new Error('Proxy is MANDATORY for Cloudflare Challenge. Use Static or Sticky proxy.');
  }

  const taskData = {
    type: 'AntiCloudflareTask',
    websiteURL: websiteUrl,
    proxy: proxy
  };

  if (userAgent) {
    taskData.userAgent = userAgent;
  }

  if (html) {
    taskData.html = html;
  }

  console.log('\n[1/3] Creating task...');
  console.log(`  Website: ${websiteUrl}`);
  console.log(`  Proxy: ${proxy.length > 30 ? proxy.substring(0, 30) + '...' : proxy}`);
  console.log(`  User-Agent: ${userAgent ? 'Custom' : 'Default'}`);
  console.log(`  HTML provided: ${html ? 'Yes' : 'No'}`);

  const createResult = await createTask(apiKey, taskData);

  if (createResult.errorId !== 0) {
    throw new Error(`Failed to create task: ${createResult.errorDescription || 'Unknown error'}`);
  }

  const taskId = createResult.taskId;
  console.log(`  ✓ Task created: ${taskId}`);

  console.log('\n[2/3] Waiting for solution...');
  console.log('  This may take 2-20 seconds depending on the website and proxy...');

  const maxAttempts = 60;
  let attempt = 0;

  while (attempt < maxAttempts) {
    await sleep(2000);
    attempt++;

    const result = await getTaskResult(apiKey, taskId);
    const status = result.status;

    if (status === 'ready') {
      console.log(`  ✓ Solution received after ${attempt * 2} seconds!`);
      return result.solution;
    } else if (status === 'failed') {
      const errorDesc = result.errorDescription || 'Unknown error';
      throw new Error(`Task failed: ${errorDesc}`);
    } else if (status === 'processing') {
      if (attempt % 5 === 0) {
        console.log(`  ... Processing (attempt ${attempt}/${maxAttempts})`);
      }
    }
  }

  throw new Error('Timeout: Failed to get solution within maximum time');
}

function printImportantNotes() {
  console.log('\n' + '='.repeat(70));
  console.log('IMPORTANT: Using cf_clearance Cookie');
  console.log('='.repeat(70));
  console.log(`
⚠️  CRITICAL REQUIREMENTS for using the cf_clearance cookie:

1. TLS Fingerprinting:
   - Use TLS client libraries (tls-client, curl-impersonate, etc.)
   - Match Chrome browser TLS fingerprint
   - Standard HTTP libraries will likely fail

2. HTTP Headers:
   - Use realistic browser headers
   - Match the User-Agent returned by CapSolver (EXACT match)
   - Include common headers: Accept, Accept-Language, Accept-Encoding, etc.

3. Header Order:
   - Headers must be sent in browser-like order
   - Cloudflare checks header ordering
   - Use libraries that preserve header order

4. User-Agent Matching:
   - MUST use the EXACT User-Agent returned in solution
   - Don't modify or use a different User-Agent
   - Case-sensitive match required

5. Cookie Format:
   - Send as: Cookie: cf_clearance=VALUE
   - Include other cookies if present
   - Maintain cookie throughout session

Recommended Libraries:
  Node.js: tls-client, node-curl-impersonate
  Python: curl_cffi, tls-client
  Go: http2, cycletls

Without proper TLS fingerprinting and header matching,
the cf_clearance cookie will be rejected by Cloudflare.
`);
}

async function main() {
  try {
    const solution = await solveCloudflareChallenge(
      CAPSOLVER_API_KEY,
      WEBSITE_URL,
      PROXY,
      USER_AGENT,
      HTML_CONTENT || null
    );

    console.log('\n' + '='.repeat(70));
    console.log('SOLUTION DETAILS');
    console.log('='.repeat(70));

    const cfClearance = solution.cookies?.cf_clearance;
    const token = solution.token;
    const userAgent = solution.userAgent;

    console.log('\ncf_clearance cookie:');
    console.log(`  ${cfClearance}`);

    console.log('\nToken:');
    console.log(`  ${token}`);

    console.log('\nUser-Agent:');
    console.log(`  ${userAgent}`);

    printImportantNotes();

    console.log('\n' + '='.repeat(70));
    console.log('COMPLETE');
    console.log('='.repeat(70));

  } catch (error) {
    console.error(`\n✗ Error: ${error.message}`);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = { solveCloudflareChallenge };
