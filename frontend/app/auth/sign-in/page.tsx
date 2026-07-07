import { SignInForm } from "./sign-in-form"

export default function SignInPage() {
  return (
    <div className="flex flex-col gap-6 items-center w-full">
      <h1 className="text-2xl font-semibold">Sign in</h1>
      <SignInForm />
    </div>
  )
}
