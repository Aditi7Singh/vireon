import { chromium, FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  console.log('🔧 Global setup: Setting up test environment...');
  // Ensure env var is set for all tests
  process.env.NEXT_PUBLIC_E2E_BYPASS_AUTH = '1';
  console.log('✅ E2E bypass auth enabled for tests');
}

export default globalSetup;
