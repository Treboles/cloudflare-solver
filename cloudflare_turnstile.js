const axios = require('axios');

const CAPSOLVER_API_KEY = 'YOUR_API_KEY_HERE';
const WEBSITE_URL = 'https://www.example.com';
const WEBSITE_KEY = '0x4XXXXXXXXXXXXXXXXX';
const METADATA_ACTION = '';
const METADATA_CDATA = '';

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

async function solveTurnstile(apiKey, websiteUrl, websiteKey, metadataAction = null, metadataCdata = null) {
  console.log('='.repeat(70));
  console.log('Cloudflare Turnstile Solver (Node.js)');
  console.log('='.repeat(70));

  if (!apiKey || apiKey === 'YOUR_API_KEY_HERE') {
    throw new Error('Please set your CapSolver API key');
  }

  if (!websiteUrl || websiteUrl === 'https://www.example.com') {
    throw new Error('Please set the target website URL');
  }

  if (!websiteKey || websiteKey === '0x4XXXXXXXXXXXXXXXXX') {
    throw new Error('Please set the Turnstile website key (sitekey)');
  }

  const taskData = {
    type: 'AntiTurnstileTaskProxyLess',
    websiteURL: websiteUrl,
    websiteKey: websiteKey
  };

  const metadata = {};
  if (metadataAction) metadata.action = metadataAction;
  if (metadataCdata) metadata.cdata = metadataCdata;
  if (Object.keys(metadata).length > 0) taskData.metadata = metadata;

  console.log('\n[1/2] Creating task...');
  console.log(`  Website: ${websiteUrl}`);
  console.log(`  Website Key: ${websiteKey}`);
  console.log('  Proxy: Not required (ProxyLess)');

  const createResult = await createTask(apiKey, taskData);
  if (createResult.errorId !== 0) {
    throw new Error(`Failed to create task: ${createResult.errorDescription || 'Unknown error'}`);
  }

  const taskId = createResult.taskId;
  console.log(`  ✓ Task created: ${taskId}`);

  console.log('\n[2/2] Waiting for solution...');
  const maxAttempts = 40;
  let attempt = 0;

  while (attempt < maxAttempts) {
    await sleep(1000);
    attempt++;

    const result = await getTaskResult(apiKey, taskId);
    if (result.status === 'ready') {
      console.log(`  ✓ Solution received after ${attempt} seconds!`);
      return result.solution;
    } else if (result.status === 'failed') {
      throw new Error(`Task failed: ${result.errorDescription || 'Unknown error'}`);
    }
  }

  throw new Error('Timeout');
}

async function main() {
  try {
    if (WEBSITE_KEY === '0x4XXXXXXXXXXXXXXXXX') {
      console.log('\nPlease set the WEBSITE_KEY and run again.');
      console.log('Find it in: <div class=\"cf-turnstile\" data-sitekey=\"0x4...\"></div>');
      process.exit(1);
    }

    const solution = await solveTurnstile(CAPSOLVER_API_KEY, WEBSITE_URL, WEBSITE_KEY, METADATA_ACTION || null, METADATA_CDATA || null);

    console.log('\n' + '='.repeat(70));
    console.log('SOLUTION DETAILS');
    console.log('='.repeat(70));
    console.log('\nTurnstile Token:');
    console.log(`  ${solution.token}`);
    console.log('\nUser-Agent:');
    console.log(`  ${solution.userAgent}`);
    console.log('\n' + '='.repeat(70));
    console.log('COMPLETE');
    console.log('='.repeat(70));
    console.log('\nUse in form: cf-turnstile-response=' + solution.token);

  } catch (error) {
    console.error(`\n✗ Error: ${error.message}`);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = { solveTurnstile };
