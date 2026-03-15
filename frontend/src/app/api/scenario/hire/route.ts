import { NextRequest, NextResponse } from 'next/server';

interface HireScenarioRequest {
  numEngineers: number;
  avgSalary: number;
  currentRunway: number;
  currentBurn: number;
  currentMrr: number;
}

export async function POST(request: NextRequest) {
  try {
    const body: HireScenarioRequest = await request.json();

    // Calculate new burn rate
    const addedAnnualBurn = body.numEngineers * body.avgSalary;
    const addedMonthlyBurn = addedAnnualBurn / 12;
    const newMonthlyBurn = body.currentBurn + addedMonthlyBurn;

    // Calculate new runway
    const cashAvailable = body.currentRunway * body.currentBurn;
    const newRunway = cashAvailable / newMonthlyBurn;

    // Calculate break-even MRR needed
    const breakEvenMrr = newMonthlyBurn - body.currentMrr;

    // Calculate zero date
    const today = new Date();
    const monthsUntilZero = newRunway;
    const zeroDate = new Date(today);
    zeroDate.setMonth(zeroDate.getMonth() + Math.floor(monthsUntilZero));
    zeroDate.setDate(today.getDate() + Math.round((monthsUntilZero % 1) * 30));

    return NextResponse.json({
      currentRunway: body.currentRunway,
      newRunway,
      runwayDelta: newRunway - body.currentRunway,
      monthlyBurnDelta: addedMonthlyBurn,
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
