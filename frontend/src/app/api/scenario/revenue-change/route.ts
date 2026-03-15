import { NextRequest, NextResponse } from 'next/server';

interface RevenueChangeScenarioRequest {
  mrrDelta: number;
  probability: number;
  currentRunway: number;
  currentBurn: number;
  currentMrr: number;
}

export async function POST(request: NextRequest) {
  try {
    const body: RevenueChangeScenarioRequest = await request.json();

    // Calculate expected MRR change (accounting for probability)
    const expectedMrrDelta = (body.mrrDelta * body.probability) / 100;

    // MRR delta reduces burn by same amount (for revenue increase) or increases burn (for revenue decrease)
    const burnChange = -expectedMrrDelta;
    const newMonthlyBurn = body.currentBurn + burnChange;

    // Calculate new runway
    const cashAvailable = body.currentRunway * body.currentBurn;
    const newRunway = newMonthlyBurn > 0 ? cashAvailable / newMonthlyBurn : 999;

    // Calculate break-even MRR if needed
    const breakEvenMrr = newMonthlyBurn - body.currentMrr;

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
      monthlyBurnDelta: burnChange,
      breakEvenMrr: Math.max(0, breakEvenMrr),
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
