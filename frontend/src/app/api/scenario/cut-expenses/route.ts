import { NextRequest, NextResponse } from 'next/server';

interface CutExpensesScenarioRequest {
  category: string;
  reductionPercent: number;
  currentRunway: number;
  currentBurn: number;
  currentMrr: number;
}

// Default category burn rates (in %, relative to total burn)
const CATEGORY_BURN_RATIOS: Record<string, number> = {
  aws: 0.25, // 25% of burn is infrastructure
  payroll: 0.5, // 50% of burn is payroll
  saas: 0.1, // 10% of burn is SaaS tools
  marketing: 0.15, // 15% of burn is marketing
  all: 1.0, // All burn
};

export async function POST(request: NextRequest) {
  try {
    const body: CutExpensesScenarioRequest = await request.json();

    // Get the category's percentage of total burn
    const categoryRatio = CATEGORY_BURN_RATIOS[body.category] || 1.0;
    const categoryBurn = body.currentBurn * categoryRatio;

    // Calculate savings
    const monthlySavings = (categoryBurn * body.reductionPercent) / 100;
    const newMonthlyBurn = body.currentBurn - monthlySavings;

    // Calculate new runway
    const cashAvailable = body.currentRunway * body.currentBurn;
    const newRunway = newMonthlyBurn > 0 ? cashAvailable / newMonthlyBurn : 999;

    // Calculate zero date
    const today = new Date();
    const monthsUntilZero = Math.min(newRunway, 120); // Cap at 10 years
    const zeroDate = new Date(today);
    zeroDate.setMonth(zeroDate.getMonth() + Math.floor(monthsUntilZero));
    zeroDate.setDate(today.getDate() + Math.round((monthsUntilZero % 1) * 30));

    return NextResponse.json({
      currentRunway: body.currentRunway,
      newRunway,
      runwayDelta: newRunway - body.currentRunway,
      monthlyBurnDelta: -monthlySavings,
      monthlySavings,
      zeroDate: zeroDate.toLocaleDateString('en-US', {
        weekday: 'long',
        month: 'long',
        day: 'numeric',
        year: 'numeric',
      }),
    });
  } catch (error) {
    console.error('Scenario calculation error:', error);
    return NextResponse.json({ error: 'Failed to calculate scenario' }, { status: 500 });
  }
}
