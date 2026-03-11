"use client";

import { Card, Grid, Text, Metric, AreaChart, Title, BadgeDelta, Flex, ProgressBar } from "@tremor/react";
import { TrendingUp, TrendingDown, DollarSign, Calendar, Users, Zap } from "lucide-react";

const chartdata = [
    { date: "Jan 24", Revenue: 21000, Expenses: 18000 },
    { date: "Feb 24", Revenue: 23500, Expenses: 19500 },
    { date: "Mar 24", Revenue: 27000, Expenses: 22000 },
    { date: "Apr 24", Revenue: 31000, Expenses: 24000 },
    { date: "May 24", Revenue: 38000, Expenses: 28000 },
    { date: "Jun 24", Revenue: 45000, Expenses: 32000 },
];

const categories = [
    {
        title: "Cash Balance",
        metric: "$1.4M",
        delta: "+12.5%",
        deltaType: "moderateIncrease",
        icon: DollarSign,
    },
    {
        title: "Monthly Burn",
        metric: "$64K",
        delta: "-4.2%",
        deltaType: "moderateDecrease",
        icon: Zap,
    },
    {
        title: "Runway",
        metric: "22.4 Mo",
        delta: "+2.1%",
        deltaType: "moderateIncrease",
        icon: Calendar,
    },
    {
        title: "Headcount",
        metric: "14",
        delta: "0%",
        deltaType: "unchanged",
        icon: Users,
    },
];

export default function DashboardPage() {
    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-50">Financial Intelligence</h1>
                <p className="text-zinc-500">Real-time metrics from ERPNext Math Engine</p>
            </div>

            <Grid numItemsSm={2} numItemsLg={4} className="gap-6">
                {categories.map((item) => (
                    <Card key={item.title} decoration="top" decorationColor="blue">
                        <Flex alignItems="start">
                            <div className="space-y-2">
                                <Text>{item.title}</Text>
                                <Metric>{item.metric}</Metric>
                            </div>
                            <BadgeDelta deltaType={item.deltaType as any}>{item.delta}</BadgeDelta>
                        </Flex>
                    </Card>
                ))}
            </Grid>

            <div className="mt-8">
                <Card>
                    <Title>Revenue vs. Expenses (Last 6 Months)</Title>
                    <Text>Comparison of monthly subscription revenue and operating expenses.</Text>
                    <AreaChart
                        className="mt-4 h-80"
                        data={chartdata}
                        index="date"
                        categories={["Revenue", "Expenses"]}
                        colors={["blue", "rose"]}
                        valueFormatter={(number: number) => `$ ${Intl.NumberFormat("us").format(number).toString()}`}
                    />
                </Card>
            </div>

            <Grid numItemsSm={1} numItemsLg={2} className="gap-6 mt-8">
                <Card>
                    <Title>Runway Progress</Title>
                    <Flex className="mt-4">
                        <Text>Target: 24 Months</Text>
                        <Text>92%</Text>
                    </Flex>
                    <ProgressBar value={92} color="teal" className="mt-3" />
                    <div className="mt-6">
                        <Text className="italic text-zinc-500">
                            "Based on current burn, you are 2 months away from your 24-month safety target."
                        </Text>
                    </div>
                </Card>
                <Card>
                    <Title>Top Cost Drivers</Title>
                    <div className="mt-4 space-y-4">
                        <Flex>
                            <Text>Cloud Infrastructure</Text>
                            <Text className="font-medium">$24,200</Text>
                        </Flex>
                        <Flex>
                            <Text>Payroll & Benefits</Text>
                            <Text className="font-medium">$32,000</Text>
                        </Flex>
                        <Flex>
                            <Text>Marketing Spend</Text>
                            <Text className="font-medium">$8,400</Text>
                        </Flex>
                    </div>
                </Card>
            </Grid>
        </div>
    );
}
