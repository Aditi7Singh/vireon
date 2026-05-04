import { redirect } from "next/navigation";

export default function RedocRedirectPage() {
  const rawApiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_API_URL || "https://vireon-sq3h.onrender.com";
  const apiBaseUrl = rawApiBaseUrl.replace(/\/$/, "").endsWith("/api/v1")
    ? rawApiBaseUrl.replace(/\/$/, "")
    : `${rawApiBaseUrl.replace(/\/$/, "")}/api/v1`;
  redirect(`${apiBaseUrl}/redoc`);
}
