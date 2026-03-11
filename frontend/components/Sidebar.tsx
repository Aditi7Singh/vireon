"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const Sidebar = () => {
    const pathname = usePathname();

    const menuItems = [
        { name: "Dashboard", path: "/dashboard", icon: "📊" },
        { name: "Scenarios", path: "/scenarios", icon: "🔮" },
        { name: "AI Agent", path: "/agent", icon: "🤖" },
        { name: "Anomalies", path: "/anomalies", icon: "⚠️" },
        { name: "Settings", path: "/settings", icon: "⚙️" },
    ];

    return (
        <div className="flex h-screen w-64 flex-col bg-zinc-950 text-zinc-400">
            <div className="flex px-6 py-8">
                <h1 className="text-xl font-bold tracking-tighter text-white">Agentic CFO</h1>
            </div>
            <nav className="flex-1 space-y-1 px-4">
                {menuItems.map((item) => {
                    const isActive = pathname === item.path;
                    return (
                        <Link
                            key={item.name}
                            href={item.path}
                            className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${isActive
                                    ? "bg-zinc-800 text-white"
                                    : "hover:bg-zinc-900 hover:text-white"
                                }`}
                        >
                            <span>{item.icon}</span>
                            {item.name}
                        </Link>
                    );
                })}
            </nav>
            <div className="p-4">
                <div className="rounded-xl bg-zinc-900 p-4 text-xs">
                    <p className="font-semibold text-white">Project Phase 2</p>
                    <p className="mt-1">ERPNext Integration Active</p>
                </div>
            </div>
        </div>
    );
};

export default Sidebar;
