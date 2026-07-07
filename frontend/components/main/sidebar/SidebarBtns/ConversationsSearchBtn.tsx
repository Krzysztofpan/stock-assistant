import SidebarBtn from "@/components/utlis/SidebarBtn"
import { Search } from "lucide-react"

const ConversationsSearchBtn = ({ onClick }: { onClick: () => void }) => {
  return (
    <SidebarBtn label="Search Conversations" icon={<Search />} onClick={onClick} />
  )
}

export default ConversationsSearchBtn
