import type { ReactNode } from "react";
import SideBar from "./Sidebar";

interface AppLayoutProps {
    children: ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
    return (
        <div className="flex min-h-screen bg-app-bg">
            <SideBar />
            <div className="ml-70 flex min-h-screen min-w-0 flex-1 flex-col lg:ml-70">
                {children}
            </div>
        </div>
    );
}
