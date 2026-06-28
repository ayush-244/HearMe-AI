"use client"

import { UserSidebar } from "@/components/layouts/user-sidebar"
import { DeveloperSidebar } from "@/components/layouts/developer-sidebar"
import { Header } from "@/components/layout/header"
import { PageContainer } from "@/components/layout/page-container"

export function UserLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <UserSidebar />
      <DeveloperSidebar />
      <div className="flex min-h-screen flex-col">
        <Header />
        <PageContainer>{children}</PageContainer>
      </div>
    </>
  )
}
