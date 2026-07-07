import { UserPanel } from "./user-panel"

export default function Home() {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold">Stock Assistant</h1>
      <UserPanel />
    </div>
  )
}
