import { MainSidebar } from "@/components/main/sidebar/MainSidebar"
import MobileNavbarTrigger from "@/components/main/sidebar/MobileNavbarTrigger"
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar"
import { ReactNode } from "react"

const MainViewLayout = ({ children }: { children: ReactNode }) => {
  return (
    <SidebarProvider>
      <MainSidebar />
      <SidebarInset className="flex flex-col md:block">
        <MobileNavbarTrigger />
        <div className="w-full px-4 lg:mx-auto max-w-3xl">
          {children}
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}

export default MainViewLayout
