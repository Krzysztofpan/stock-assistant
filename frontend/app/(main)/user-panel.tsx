"use client"

import { useCurrentUser } from "@/hooks/queries/use-current-user"
import { signOut } from "@/services/stockAssistantService/auth-actions"

export function UserPanel() {
  const { data, isLoading, isError } = useCurrentUser()

  if (isLoading) {
    return <p className="text-neutral-600">Loading user...</p>
  }

  if (isError || !data) {
    return <p className="text-red-600">Failed to load user</p>
  }

  return (
    <div className="flex flex-col gap-4">
      <p>
        Signed in as
        {" "}
        <strong>{data.user.name}</strong>
        {" "}
        (
        {data.user.email}
        )
      </p>
      <form action={signOut}>
        <button
          type="submit"
          className="rounded border border-neutral-300 px-4 py-2"
        >
          Sign out
        </button>
      </form>
    </div>
  )
}
