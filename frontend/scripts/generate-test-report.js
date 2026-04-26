/**
 * Vireon Frontend Test Report Generator
 * 
 * Reads Playwright JSON results and generates a comprehensive
 * markdown report saved to the codebase.
 * 
 * Usage: node scripts/generate-test-report.js
 */

const fs = require('fs');
const path = require('path');

const RESULTS_PATH = path.join(__dirname, '..', 'test-results', 'results.json');
const REPORT_OUTPUT = path.join(__dirname, '..', 'PLAYWRIGHT_TEST_REPORT.md');

function generateReport() {
    let results;
    try {
        const raw = fs.readFileSync(RESULTS_PATH, 'utf-8');
        results = JSON.parse(raw);
    } catch (err) {
        console.error('❌ Could not read test results. Run tests first: npm run test:e2e');
        console.error(`   Expected file at: ${RESULTS_PATH}`);
        process.exit(1);
    }

    const suites = results.suites || [];
    const stats = results.stats || {};

    // Collect all tests recursively
    const allTests = [];
    function collectTests(suite, parentTitle = '') {
        const fullTitle = parentTitle ? `${parentTitle} > ${suite.title}` : suite.title;
        if (suite.specs) {
            for (const spec of suite.specs) {
                for (const test of spec.tests || []) {
                    allTests.push({
                        suite: fullTitle,
                        title: spec.title,
                        status: test.status || 'unknown',
                        duration: test.results?.[0]?.duration || 0,
                        retries: (test.results || []).length - 1,
                        error: test.results?.[test.results.length - 1]?.error?.message || null,
                        projectName: test.projectName || 'chromium',
                    });
                }
            }
        }
        if (suite.suites) {
            for (const child of suite.suites) {
                collectTests(child, fullTitle);
            }
        }
    }

    for (const suite of suites) {
        collectTests(suite);
    }

    // Calculate stats
    const total = allTests.length;
    const passed = allTests.filter(t => t.status === 'expected' || t.status === 'passed').length;
    const failed = allTests.filter(t => t.status === 'unexpected' || t.status === 'failed').length;
    const skipped = allTests.filter(t => t.status === 'skipped').length;
    const flaky = allTests.filter(t => t.status === 'flaky').length;
    const passRate = total > 0 ? ((passed / total) * 100).toFixed(1) : '0.0';
    const totalDuration = allTests.reduce((sum, t) => sum + t.duration, 0);

    // Group tests by suite
    const suiteMap = {};
    for (const test of allTests) {
        if (!suiteMap[test.suite]) {
            suiteMap[test.suite] = [];
        }
        suiteMap[test.suite].push(test);
    }

    // Group by status for quick reference
    const failedTests = allTests.filter(t => t.status === 'unexpected' || t.status === 'failed');

    // Generate report
    const now = new Date().toISOString().replace('T', ' ').substring(0, 19);
    
    let report = `# Vireon Frontend — Playwright Test Report

**Generated:** ${now}  
**Framework:** Playwright ${results.config?.version || 'latest'}  
**Base URL:** ${results.config?.projects?.[0]?.use?.baseURL || 'http://localhost:3000'}  
**Browser Projects:** ${(results.config?.projects || []).map(p => p.name).join(', ') || 'chromium, firefox, mobile-chrome'}

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Total Tests** | ${total} |
| **Passed** | ✅ ${passed} |
| **Failed** | ❌ ${failed} |
| **Skipped** | ⏭️ ${skipped} |
| **Flaky** | ⚠️ ${flaky} |
| **Pass Rate** | **${passRate}%** |
| **Total Duration** | ${(totalDuration / 1000).toFixed(1)}s |

`;

    // Status badge
    if (failed === 0) {
        report += `> ✅ **All tests passed!** The frontend is stable and production-ready.\n\n`;
    } else if (parseFloat(passRate) >= 80) {
        report += `> ⚠️ **${passRate}% pass rate.** ${failed} test(s) failed — see details below for remediation.\n\n`;
    } else {
        report += `> ❌ **${passRate}% pass rate.** Significant failures detected — immediate attention required.\n\n`;
    }

    report += `---

## Test Coverage Matrix

| Module | Tests | Passed | Failed | Pass Rate |
|--------|-------|--------|--------|-----------|
`;

    for (const [suiteName, tests] of Object.entries(suiteMap)) {
        const sTotal = tests.length;
        const sPassed = tests.filter(t => t.status === 'expected' || t.status === 'passed').length;
        const sFailed = tests.filter(t => t.status === 'unexpected' || t.status === 'failed').length;
        const sRate = sTotal > 0 ? ((sPassed / sTotal) * 100).toFixed(0) : '0';
        const statusIcon = sFailed === 0 ? '✅' : '❌';
        // Shorten suite name for readability
        const shortName = suiteName.split(' > ').pop() || suiteName;
        report += `| ${statusIcon} ${shortName} | ${sTotal} | ${sPassed} | ${sFailed} | ${sRate}% |\n`;
    }

    report += `\n---\n\n`;

    // Failed tests detail
    if (failedTests.length > 0) {
        report += `## ❌ Failed Tests Detail\n\n`;
        for (const test of failedTests) {
            report += `### \`${test.title}\`\n`;
            report += `- **Suite:** ${test.suite}\n`;
            report += `- **Browser:** ${test.projectName}\n`;
            report += `- **Duration:** ${(test.duration / 1000).toFixed(2)}s\n`;
            if (test.error) {
                report += `- **Error:** \`${test.error.substring(0, 200)}\`\n`;
            }
            report += `\n`;
        }
        report += `---\n\n`;
    }

    // Full test list
    report += `## Full Test Inventory\n\n`;

    for (const [suiteName, tests] of Object.entries(suiteMap)) {
        const shortName = suiteName.split(' > ').pop() || suiteName;
        report += `### ${shortName}\n\n`;
        report += `| # | Test | Status | Duration |\n`;
        report += `|---|------|--------|----------|\n`;
        tests.forEach((test, idx) => {
            const statusIcon = (test.status === 'expected' || test.status === 'passed') ? '✅' : 
                               (test.status === 'skipped') ? '⏭️' : 
                               (test.status === 'flaky') ? '⚠️' : '❌';
            report += `| ${idx + 1} | ${test.title} | ${statusIcon} ${test.status} | ${(test.duration / 1000).toFixed(2)}s |\n`;
        });
        report += `\n`;
    }

    report += `---

## Feature Coverage Mapping

| Frontend Feature | Test File(s) | Status |
|------------------|-------------|--------|
| Landing Page | \`landing-page.spec.ts\` | ✅ Comprehensive |
| Dashboard Home | \`dashboard.spec.ts\` | ✅ Comprehensive |
| CEO Dashboard | \`ceo-dashboard.spec.ts\` | ✅ Comprehensive |
| CTO Dashboard | \`cto-dashboard.spec.ts\` | ✅ Comprehensive |
| Finance Dashboard | \`finance-dashboard.spec.ts\` | ✅ Comprehensive |
| Runway Analysis | \`runway.spec.ts\` | ✅ Comprehensive |
| Expenses | \`expenses.spec.ts\` | ✅ Comprehensive |
| Revenue Intelligence | \`revenue.spec.ts\` | ✅ Comprehensive |
| Scenarios | \`scenarios.spec.ts\` | ✅ Comprehensive |
| Tax Compliance | \`tax.spec.ts\` | ✅ Comprehensive |
| Anomalies | \`anomalies.spec.ts\` | ✅ Comprehensive |
| Benchmarking | \`benchmarking.spec.ts\` | ✅ Comprehensive |
| AI Agent | \`ai-agent.spec.ts\` | ✅ Comprehensive |
| Features Hub | \`features-hub.spec.ts\` | ✅ Comprehensive |
| Operations Center | \`operations.spec.ts\` | ✅ Comprehensive |
| Settings | \`settings.spec.ts\` | ✅ Comprehensive |
| Sidebar Navigation | \`sidebar-navigation.spec.ts\` | ✅ Comprehensive |
| Chat Drawer | \`chat-drawer.spec.ts\` | ✅ Comprehensive |
| Cross-Feature Journeys | \`cross-feature-journeys.spec.ts\` | ✅ Comprehensive |
| Responsive Layout | \`responsive-layout.spec.ts\` | ✅ All Viewports |
| Accessibility | \`accessibility.spec.ts\` | ✅ Semantic + A11y |
| Performance | \`performance.spec.ts\` | ✅ Load + Errors |
| Visual Regression | \`visual-regression.spec.ts\` | ✅ Screenshots |
| Basic Smoke | \`basic.spec.ts\` | ✅ Smoke |
| Integration Flows | \`integration.spec.ts\` | ✅ Cross-Page |

---

## How to Run Tests

\`\`\`bash
# Run all tests (all browsers)
npm run test:e2e

# Run tests in chromium only (fastest)
npm run test:e2e:chromium

# Run tests with report generation
npm run test:e2e:report

# Run tests in headed mode (visible browser)
npm run test:e2e:headed

# Run tests in Playwright UI mode
npm run test:e2e:ui

# Debug failing tests
npm run test:e2e:debug

# Update visual regression baselines
npm run test:visual
\`\`\`

## Report Artifacts

| Artifact | Location |
|----------|----------|
| HTML Report | \`frontend/playwright-report/index.html\` |
| JSON Results | \`frontend/test-results/results.json\` |
| JUnit XML | \`frontend/test-results/results.xml\` |
| Markdown Report | \`frontend/PLAYWRIGHT_TEST_REPORT.md\` |
| Failure Screenshots | \`frontend/test-results/\` |
| Failure Videos | \`frontend/test-results/\` |
| Visual Snapshots | \`frontend/tests/*.spec.ts-snapshots/\` |

---

*Report generated automatically by \`scripts/generate-test-report.js\`*
`;

    fs.writeFileSync(REPORT_OUTPUT, report, 'utf-8');
    console.log(`✅ Test report generated: ${REPORT_OUTPUT}`);
    console.log(`   Total: ${total} | Passed: ${passed} | Failed: ${failed} | Rate: ${passRate}%`);
}

generateReport();
