import { SignUpForm } from "./sign-up-form"

export default function SignUpPage() {
  return (
    <div className="flex flex-col gap-6 items-center">
      <h1 className="text-2xl font-semibold">Sign up</h1>
      <SignUpForm />
    </div>
  )
}
