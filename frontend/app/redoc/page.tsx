import { redirect } from "next/navigation";

export default function RedocRedirectPage() {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  redirect(`${apiBaseUrl}/api/v1/redoc`);
}