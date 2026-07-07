import { SidebarTrigger } from "@/components/ui/sidebar"

const MobileNavbarTrigger = () => {
  return (
    <header className="space-x-1 sticky top-0 z-50 flex h-12 shrink-0 items-center px-2 md:hidden bg-muted">
      <SidebarTrigger className="scale-x-125 scale-y-110" />
      <span className="font-semibold">Stock Asisstant</span>
    </header>
  )
}

export default MobileNavbarTrigger
