"use client"

import Link from "next/link"
import { startTransition, useActionState } from "react"
import { zodResolver } from "@hookform/resolvers/zod"
import { FormProvider, useForm } from "react-hook-form"

import AuthFormField from "@/components/auth/AuthFormInput"
import { signIn } from "@/services/stockAssistantService/auth-actions"
import { signInFormSchema, SignInFormType } from "@/services/stockAssistantService/schemas"

export function SignInForm() {
  const [state, formAction, isPending] = useActionState(signIn, {})
  const form = useForm<SignInFormType>({
    resolver: zodResolver(signInFormSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  })

  const onSubmit = (data: SignInFormType) => {
    const formData = new FormData()

    formData.set("email", data.email)
    formData.set("password", data.password)
    startTransition(() => {
      formAction(formData)
    })
  }

  return (
    <FormProvider {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} noValidate className="flex w-full max-w-sm flex-col gap-4 md:gap-6">
        <AuthFormField name="email" label="email" inputType="email" autoComplete="email" />
        <AuthFormField name="password" label="password" inputType="password" autoComplete="current-password" />

        {state.error
          ? (
              <p className="text-sm text-red-600" role="alert">
                {state.error}
              </p>
            )
          : null}

        <button type="submit" disabled={isPending} className="cursor-pointer rounded bg-neutral-900 px-4 py-2 text-white hover:bg-neutral-800 disabled:opacity-50">
          {isPending ? "Signing in..." : "Sign in"}
        </button>

        <p className="text-sm text-neutral-600 text-center">
          No account?
          {" "}
          <Link href="/auth/sign-up" className="underline">
            Sign up
          </Link>
        </p>
      </form>
    </FormProvider>
  )
}
